"""
NCP LDAP Configurations API — Functional Flow Tests

Covers all 5 LDAP Config endpoints (LC01–LC05):

  Step 1  LIST ALL   → GET    /api/v1/ldap-configs
  Step 2  CREATE     → POST   /api/v1/ldap-configs
  Step 3  GET        → GET    /api/v1/ldap-configs/{config_id}
  Step 4  UPDATE     → PUT    /api/v1/ldap-configs/{config_id}
  Step 5  DELETE     → DELETE /api/v1/ldap-configs/{config_id}

Flow strategy:
  - CREATE a fresh LDAP config at Step 2.
  - Steps 3 and 4 validate read and update on that same config.
  - DELETE at Step 5 cleans up — fully self-contained.
  - Post-delete GET confirms the config no longer exists (expects 404/422).

Request body fields (per Swagger):
  host, port (int, default 389), base_dn, admin_cn, admin_password, ou

Response body fields (per Swagger):
  id, host, port, base_dn, admin_cn, ou  (admin_password is NOT returned)
"""

import pytest
import logging
import json
import time

from api_client import (
    get_all_ldap_configs,
    create_ldap_config,
    get_ldap_config,
    update_ldap_config,
    delete_ldap_config,
    safe_json,
)

logger = logging.getLogger(__name__)


# ── Shared helper (same pattern used across all functional flows) ─

def _flow(collector, step, description, resp, method, endpoint,
          expected=(200,), prefix=""):
    data   = safe_json(resp)
    passed = resp.status_code in expected

    pretty = json.dumps(data, indent=2, default=str) if data is not None \
             else f"(status {resp.status_code}, no body)"

    logger.info(
        "[%s%02d] %s %s → %s\n%s",
        prefix, step, method, endpoint, resp.status_code, pretty,
    )

    collector.add_flow(
        step             = step,
        description      = description,
        api_method       = method,
        endpoint         = endpoint,
        expected_status  = "/".join(str(c) for c in expected),
        actual_status    = resp.status_code,
        response_summary = pretty,
        passed           = passed,
    )
    return passed, data, resp.status_code


# ════════════════════════════════════════════════════════════════
# LDAP CONFIGURATIONS FUNCTIONAL FLOW
# ════════════════════════════════════════════════════════════════

class TestLDAPConfigsFunctionalFlow:

    # ── Base payload for LDAP config creation ──────────────────
    @pytest.fixture(scope="class")
    def base_payload(self):
        """
        Mirrors the Swagger example exactly.
        Uses dummy/test values — the API accepts any string for host/dn fields.
        """
        # Real, reachable LDAP/AD server on the target box. Create AND update
        # actually bind to this server, so these must be valid credentials.
        return {
            "host":           "10.4.5.236",
            "port":           636,
            "base_dn":        "dc=aviz,dc=networks",
            "admin_cn":       "Administrator",
            "admin_password": "Admin@1234",
            "ou":             "aviz_eng",
            "auth_type":      "AD",
        }

    # ── Step 1: LIST ALL LDAP CONFIGS ──────────────────────────
    def test_ldap01_list_all_configs(self, ncp_token, report_collector):
        resp = get_all_ldap_configs(ncp_token)
        passed, data, code = _flow(
            report_collector, 1,
            "LIST all LDAP configs",
            resp, "GET", "/api/v1/ldap-configs", (200,), prefix="LDAP",
        )
        assert passed, f"LIST LDAP configs failed: expected 200, got {code}"

        # Response should be a list (empty list is also valid)
        assert isinstance(data, list), \
            f"Expected list response for all LDAP configs, got: {type(data)}"
        logger.info("[LDAP01] Total LDAP configs returned: %d", len(data))

    # ── Step 2: CREATE LDAP CONFIG ─────────────────────────────
    def test_ldap02_create_config(self, ncp_token, report_collector,
                                  flow_state, base_payload):
        # Only ONE LDAP config is allowed globally; a pre-existing one makes
        # create 400 ("already exists. Please remove it first"). Remove any
        # existing config so this create exercises a real 200/201.
        existing = safe_json(get_all_ldap_configs(ncp_token))
        if isinstance(existing, list):
            for c in existing:
                cid = c.get("id") or c.get("config_id")
                if cid:
                    d = delete_ldap_config(cid, ncp_token)
                    logger.info(
                        "[LDAP02] removed pre-existing LDAP config id=%s → %s",
                        cid, d.status_code,
                    )

        resp = create_ldap_config(base_payload, ncp_token)
        # The API validates by actually binding to the LDAP server. With no
        # reachable LDAP server it returns 500 "Failed to connect...". That's an
        # external dependency, not a test defect — skip (set base_payload to a
        # real reachable LDAP server to exercise the full CRUD flow).
        body = safe_json(resp)
        if resp.status_code >= 500 and "connect" in str(body).lower():
            flow_state["ldap_config_id"] = None
            pytest.skip(
                "LDAP server unreachable (external dependency) — create returned "
                f"{resp.status_code}: {body}. Point base_payload at a real LDAP server."
            )

        passed, data, code = _flow(
            report_collector, 2,
            "CREATE LDAP config",
            resp, "POST", "/api/v1/ldap-configs", (200, 201), prefix="LDAP",
        )
        assert passed, f"CREATE LDAP config failed: expected 200/201, got {code}"

        # Swagger response body uses 'id' as the key
        config_id = data.get("id") or data.get("config_id")

        # Fallback: scan list if response body did not include id
        if not config_id:
            all_resp = get_all_ldap_configs(ncp_token)
            all_data = safe_json(all_resp)
            if isinstance(all_data, list):
                for c in all_data:
                    if c.get("host") == base_payload["host"]:
                        config_id = c.get("id") or c.get("config_id")
                        break

        if config_id:
            logger.info("[LDAP02] LDAP config created with id=%s", config_id)
        else:
            logger.warning(
                "[LDAP02] Could not resolve config_id — downstream steps may fail"
            )
            config_id = "unknown_id"

        flow_state["ldap_config_id"] = config_id

    # ── Step 3: GET LDAP CONFIG ────────────────────────────────
    def test_ldap03_get_config(self, ncp_token, report_collector, flow_state,
                               base_payload):
        config_id = flow_state.get("ldap_config_id")
        if not config_id or config_id == "unknown_id":
            pytest.skip("No LDAP config created in LDAP02 (server unreachable) — skipping GET")

        resp = get_ldap_config(config_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 3,
            f"GET LDAP config id={config_id}",
            resp, "GET", f"/api/v1/ldap-configs/{config_id}", (200,), prefix="LDAP",
        )
        assert passed, f"GET LDAP config failed: expected 200, got {code}"

        # Confirm the correct record was returned
        returned_id = data.get("id") or data.get("config_id")
        assert str(returned_id) == str(config_id), \
            f"Returned config id mismatch: expected {config_id}, got {returned_id}"

        # Confirm host matches what we created
        assert data.get("host") == base_payload["host"], \
            f"Unexpected host in response: {data.get('host')}"

        # Confirm admin_password is NOT returned (security check)
        assert "admin_password" not in data, \
            "Security issue: admin_password should not be returned in GET response"

    # ── Step 4: UPDATE LDAP CONFIG ─────────────────────────────
    def test_ldap04_update_config(self, ncp_token, report_collector,
                                  flow_state, base_payload):
        config_id = flow_state.get("ldap_config_id")
        if not config_id or config_id == "unknown_id":
            pytest.skip("No LDAP config created in LDAP02 (server unreachable) — skipping UPDATE")

        # UPDATE also binds to the LDAP server, so the connection fields must
        # stay valid/reachable. Keep the real host/port/creds and change only a
        # non-connection field (ou) so the update is real yet still binds.
        update_payload = base_payload.copy()
        update_payload["ou"] = "aviz_eng_updated"

        resp = update_ldap_config(config_id, update_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 4,
            f"UPDATE LDAP config id={config_id}",
            resp, "PUT", f"/api/v1/ldap-configs/{config_id}", (200,), prefix="LDAP",
        )
        assert passed, f"UPDATE LDAP config failed: expected 200, got {code}"

        # Verify the update was applied if the response returns the record
        if data and data.get("ou"):
            assert data.get("ou") == "aviz_eng_updated", \
                f"Update not reflected in response: ou={data.get('ou')}"
            logger.info("[LDAP04] UPDATE confirmed — ou now: %s", data.get("ou"))

    # ── Step 5: DELETE LDAP CONFIG ─────────────────────────────
    def test_ldap05_delete_config(self, ncp_token, report_collector, flow_state):
        """Delete the config created in Step 2 — fully self-contained cleanup."""
        config_id = flow_state.get("ldap_config_id")
        if not config_id or config_id == "unknown_id":
            pytest.skip("No LDAP config created in LDAP02 (server unreachable) — skipping DELETE")

        resp = delete_ldap_config(config_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 5,
            f"DELETE LDAP config id={config_id}",
            resp, "DELETE", f"/api/v1/ldap-configs/{config_id}",
            (200, 204), prefix="LDAP",
        )
        assert passed, f"DELETE LDAP config failed: expected 200/204, got {code}"

        # Post-delete verification — confirm the deleted config is no longer
        # present in the full list returned by GET ALL.
        all_resp = get_all_ldap_configs(ncp_token)
        all_data = safe_json(all_resp)
        assert isinstance(all_data, list), \
            f"GET ALL after DELETE returned unexpected type: {type(all_data)}"

        remaining_ids = [
            str(c.get("id") or c.get("config_id", ""))
            for c in all_data
        ]
        assert str(config_id) not in remaining_ids, (
            f"LDAP config id={config_id} still appears in GET ALL after DELETE. "
            f"Remaining ids: {remaining_ids}"
        )
        logger.info(
            "[LDAP05] LDAP config id=%s confirmed absent from GET ALL after DELETE. "
            "Remaining configs: %d",
            config_id, len(all_data),
        )