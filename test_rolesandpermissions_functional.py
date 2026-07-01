"""
NCP Roles and Permissions API — Functional Flow Tests

Covers all 9 Roles & Permissions endpoints (RP01–RP09):

  Step 1  LIST ALL ROLES        → GET    /api/v1/roles_and_permissions
  Step 2  CREATE ROLE           → POST   /api/v1/roles_and_permissions
  Step 3  GET ROLE              → GET    /api/v1/roles_and_permissions/{role_id}
  Step 4  UPDATE ROLE           → PUT    /api/v1/roles_and_permissions/{role_id}
  Step 5   GET CUSTOM AGENTS          → GET    /api/v1/roles_and_permissions/custom_agents
  Step 6   GET ROLE BY USERNAME       → GET    /api/v1/roles_and_permissions/get_role_by_username/{username}
  Step 7   GET USERS BY ROLE          → GET    /api/v1/roles_and_permissions/get_users_by_role/{role_id}
  Step 8   REASSIGN USERS             → POST   /api/v1/roles_and_permissions/reassign_users/
  Step 9   DELETE ROLE                → DELETE /api/v1/roles_and_permissions/{role_id}
  Step 10  GET LLMs BY ROLE           → GET    /api/v1/roles_and_permissions/llms/{role_id}
  Step 11  GET DATA CONNECTORS BY ROLE→ GET    /api/v1/roles_and_permissions/data_connectors/{role_id}
  Step 12  GET FILES BY ROLE          → GET    /api/v1/roles_and_permissions/files/{role_id}
  Step 13  GET DEVICES BY ROLE        → GET    /api/v1/roles_and_permissions/devices/{role_id}
  Step 14  GET CUSTOM AGENTS BY ROLE  → GET    /api/v1/roles_and_permissions/custom_agents/{role_id}

Flow strategy:
  - CREATE a fresh role at Step 2; steps 3/4/9 use its role_id.
  - DELETE the same role at Step 9 — fully self-contained, no pre-existing data needed.
  - Steps 5–8 use stable system data (custom_agents list, superadmin user).
  - Steps 7, 10–14 use TEST_ROLE_ID=19 (stable existing role with assigned resources).
  - Step 8 (reassign_users) is known to return 405 in the current API version;
    the test accepts 200/405 and logs accordingly so the suite does not block.
"""

import pytest
import logging
import json
import time

from api_client import (
    get_all_roles,
    create_role,
    get_role,
    update_role,
    delete_role,
    get_custom_agents,
    reassign_users,
    get_role_by_username,
    get_users_by_role,
    get_llms_by_role,
    get_data_connectors_by_role,
    get_files_by_role,
    get_devices_by_role,
    get_custom_agents_by_role,
    safe_json,
)
from config import (
    TEST_ROLE_ID,
    TEST_ROLE_USERNAME,
    TEST_REASSIGN_TO_ROLE_ID,
)

logger = logging.getLogger(__name__)


# ── Shared helper (same pattern as other functional test files) ─

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
# ROLES AND PERMISSIONS FUNCTIONAL FLOW
# ════════════════════════════════════════════════════════════════

class TestRolesAndPermissionsFunctionalFlow:

    # ── Base payload for role creation ─────────────────────────
    @pytest.fixture(scope="class")
    def base_payload(self):
        """Minimal but complete payload for role creation, per Swagger schema."""
        return {
            "role_name":         f"Auto-Role-{int(time.time())}",
            "description":       "Created by automated functional flow",
            "created_by":        "superadmin",
            "can_submit_agent":  False,
            "options": [
                {
                    "entity_name": "auto-test-entity",
                    "entity_type": "LLMs",
                    "entity_id":   0,
                }
            ],
            "nav_permission":    {},
            "action_permission": {},
            "is_editable":       True,
        }

    # ── Step 1: LIST ALL ROLES ─────────────────────────────────
    def test_rp01_list_all_roles(self, ncp_token, report_collector):
        resp = get_all_roles(ncp_token)
        passed, data, code = _flow(
            report_collector, 1,
            "LIST all roles",
            resp, "GET", "/api/v1/roles_and_permissions", (200,), prefix="RP",
        )
        assert passed, f"LIST roles failed: expected 200, got {code}"
        assert isinstance(data, list), \
            f"Expected list response for all roles, got: {type(data)}"
        logger.info("[RP01] Total roles returned: %d", len(data))

    # ── Step 2: CREATE ROLE ────────────────────────────────────
    def test_rp02_create_role(self, ncp_token, report_collector,
                              flow_state, base_payload):
        resp = create_role(base_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 2,
            "CREATE new role",
            resp, "POST", "/api/v1/roles_and_permissions", (200, 201), prefix="RP",
        )
        assert passed, f"CREATE role failed: expected 200/201, got {code}"

        # Extract role_id — Swagger shows field is 'role_id'
        role_id = data.get("role_id") or data.get("id")

        # Fallback: scan list if body did not include id
        if not role_id:
            all_resp = get_all_roles(ncp_token)
            all_data = safe_json(all_resp)
            if isinstance(all_data, list):
                for r in all_data:
                    if r.get("role_name") == base_payload["role_name"]:
                        role_id = r.get("role_id") or r.get("id")
                        break

        if role_id:
            logger.info("[RP02] Role created with role_id=%s", role_id)
        else:
            logger.warning("[RP02] Could not resolve role_id — downstream steps may fail")
            role_id = "unknown_id"

        flow_state["role_id"]   = role_id
        flow_state["role_name"] = base_payload["role_name"]

    # ── Step 3: GET ROLE ───────────────────────────────────────
    def test_rp03_get_role(self, ncp_token, report_collector, flow_state):
        role_id = flow_state.get("role_id")

        resp = get_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 3,
            f"GET role id={role_id}",
            resp, "GET", f"/api/v1/roles_and_permissions/{role_id}", (200,), prefix="RP",
        )
        assert passed, f"GET role failed: expected 200, got {code}"

        # Confirm the correct record was returned
        returned_id = data.get("role_id") or data.get("id")
        assert str(returned_id) == str(role_id), \
            f"Returned role_id mismatch: expected {role_id}, got {returned_id}"

    # ── Step 4: UPDATE ROLE ────────────────────────────────────
    def test_rp04_update_role(self, ncp_token, report_collector,
                              flow_state, base_payload):
        role_id = flow_state.get("role_id")

        update_payload = base_payload.copy()
        update_payload["description"]      = "Updated description by automated functional flow"
        update_payload["can_submit_agent"] = True

        resp = update_role(role_id, update_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 4,
            f"UPDATE role id={role_id}",
            resp, "PUT", f"/api/v1/roles_and_permissions/{role_id}", (200,), prefix="RP",
        )
        assert passed, f"UPDATE role failed: expected 200, got {code}"

    # ── Step 5: GET CUSTOM AGENTS ──────────────────────────────
    def test_rp05_get_custom_agents(self, ncp_token, report_collector):
        resp = get_custom_agents(ncp_token)
        passed, data, code = _flow(
            report_collector, 5,
            "GET all custom agents",
            resp, "GET", "/api/v1/roles_and_permissions/custom_agents", (200,), prefix="RP",
        )
        assert passed, f"GET custom agents failed: expected 200, got {code}"

    # ── Step 6: GET ROLE BY USERNAME ───────────────────────────
    def test_rp06_get_role_by_username(self, ncp_token, report_collector):
        username = TEST_ROLE_USERNAME  # "superadmin"

        resp = get_role_by_username(username, ncp_token)
        passed, data, code = _flow(
            report_collector, 6,
            f"GET role for username={username}",
            resp, "GET",
            f"/api/v1/roles_and_permissions/get_role_by_username/{username}",
            (200,), prefix="RP",
        )
        assert passed, f"GET role by username failed: expected 200, got {code}"

    # ── Step 7: GET USERS BY ROLE ──────────────────────────────
    def test_rp07_get_users_by_role(self, ncp_token, report_collector):
        role_id = TEST_ROLE_ID  # stable existing role_id=1

        resp = get_users_by_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 7,
            f"GET users for role_id={role_id}",
            resp, "GET",
            f"/api/v1/roles_and_permissions/get_users_by_role/{role_id}",
            (200,), prefix="RP",
        )
        assert passed, f"GET users by role failed: expected 200, got {code}"

    # ── Step 8: REASSIGN USERS ─────────────────────────────────
    def test_rp08_reassign_users(self, ncp_token, report_collector):
        """
        POST /api/v1/roles_and_permissions/reassign_users/?to_role_id=<id>
        Body: list of entity objects to reassign.

        NOTE: Swagger itself returns 405 (Method Not Allowed) for this endpoint.
        The test accepts both 200 (success) and 405 (known API limitation) so the
        suite remains non-blocking. A 405 result is logged as a known issue.
        """
        to_role_id = TEST_REASSIGN_TO_ROLE_ID  # 2

        body_payload = [
            {
                "entity_name": "superadmin",
                "entity_type": "LLMs",
                "entity_id":   5,
            }
        ]

        resp = reassign_users(to_role_id, body_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 8,
            f"REASSIGN users to role_id={to_role_id}",
            resp, "POST",
            f"/api/v1/roles_and_permissions/reassign_users/?to_role_id={to_role_id}",
            (200, 204), prefix="RP",
        )

        '''if code == 405:
            logger.warning(
                "[RP08] REASSIGN returned 405 — known API limitation (observed in Swagger too). "
                "Marking as acceptable."
            )'''
        assert passed, f"REASSIGN users failed: expected 200 got {code}"

    # ── Step 10: GET LLMs BY ROLE ──────────────────────────────
    def test_rp10_get_llms_by_role(self, ncp_token, report_collector):
        role_id = TEST_ROLE_ID  # 19

        resp = get_llms_by_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 10,
            f"GET LLMs assigned to role_id={role_id}",
            resp, "GET",
            f"/api/v1/roles_and_permissions/llms/{role_id}",
            (200,), prefix="RP",
        )
        assert passed, f"GET LLMs by role failed: expected 200, got {code}"
        logger.info("[RP10] LLMs for role_id=%s: %s",
                    role_id, data if isinstance(data, list) else data)

    # ── Step 11: GET DATA CONNECTORS BY ROLE ──────────────────
    def test_rp11_get_data_connectors_by_role(self, ncp_token, report_collector):
        role_id = TEST_ROLE_ID  # 19

        resp = get_data_connectors_by_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 11,
            f"GET data connectors assigned to role_id={role_id}",
            resp, "GET",
            f"/api/v1/roles_and_permissions/data_connectors/{role_id}",
            (200,), prefix="RP",
        )
        assert passed, f"GET data connectors by role failed: expected 200, got {code}"
        logger.info("[RP11] Data connectors for role_id=%s: %s",
                    role_id, data if isinstance(data, list) else data)

    # ── Step 12: GET FILES BY ROLE ─────────────────────────────
    def test_rp12_get_files_by_role(self, ncp_token, report_collector):
        role_id = TEST_ROLE_ID  # 19

        resp = get_files_by_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 12,
            f"GET files assigned to role_id={role_id}",
            resp, "GET",
            f"/api/v1/roles_and_permissions/files/{role_id}",
            (200,), prefix="RP",
        )
        assert passed, f"GET files by role failed: expected 200, got {code}"
        logger.info("[RP12] Files for role_id=%s: %s",
                    role_id, data if isinstance(data, list) else data)

    # ── Step 13: GET DEVICES BY ROLE ───────────────────────────
    def test_rp13_get_devices_by_role(self, ncp_token, report_collector):
        role_id = TEST_ROLE_ID  # 19

        resp = get_devices_by_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 13,
            f"GET devices assigned to role_id={role_id}",
            resp, "GET",
            f"/api/v1/roles_and_permissions/devices/{role_id}",
            (200,), prefix="RP",
        )
        assert passed, f"GET devices by role failed: expected 200, got {code}"
        logger.info("[RP13] Devices for role_id=%s: %s",
                    role_id, data if isinstance(data, list) else data)

    # ── Step 14: GET CUSTOM AGENTS BY ROLE ────────────────────
    def test_rp14_get_custom_agents_by_role(self, ncp_token, report_collector):
        role_id = TEST_ROLE_ID  # 19

        resp = get_custom_agents_by_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 14,
            f"GET custom agents assigned to role_id={role_id}",
            resp, "GET",
            f"/api/v1/roles_and_permissions/custom_agents/{role_id}",
            (200,), prefix="RP",
        )
        assert passed, f"GET custom agents by role failed: expected 200, got {code}"
        logger.info("[RP14] Custom agents for role_id=%s: %s",
                    role_id, data if isinstance(data, list) else data)

    # ── Step 9: DELETE ROLE ────────────────────────────────────
    def test_rp09_delete_role(self, ncp_token, report_collector, flow_state):
        """Delete the role created in Step 2 — keeps the suite self-contained."""
        role_id = flow_state.get("role_id")

        resp = delete_role(role_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 9,
            f"DELETE role id={role_id}",
            resp, "DELETE",
            f"/api/v1/roles_and_permissions/{role_id}",
            (200, 204), prefix="RP",
        )
        assert passed, f"DELETE role failed: expected 200/204, got {code}"

        # Confirm deletion by verifying role no longer exists
        verify_resp = get_role(role_id, ncp_token)
        verify_code = verify_resp.status_code
        assert verify_code in (404, 422), (
            f"Role id={role_id} still exists after DELETE (GET returned {verify_code})"
        )
        logger.info(
            "[RP09] Role id=%s confirmed deleted (GET returned %s)", role_id, verify_code
        )