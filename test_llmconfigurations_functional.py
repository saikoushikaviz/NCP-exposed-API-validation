"""
NCP LLM Configurations API — Functional Flow Tests

Covers LLM Config APIs (LC01–LC05):
  Step 1  CREATE   → POST   /api/v1/llm-configs
  Step 2  LIST     → GET    /api/v1/llm-configs
  Step 3  READ     → GET    /api/v1/llm-configs/{config_id}
  Step 4  UPDATE   → PUT    /api/v1/llm-configs/{config_id}
  Step 5  DELETE   → DELETE /api/v1/llm-configs/{config_id}
"""

import pytest
import logging
import json
import time

from api_client import (
    create_llm_config,
    get_all_llm_configs,
    get_llm_config,
    update_llm_config,
    delete_llm_config,
    safe_json,
)

logger = logging.getLogger(__name__)


# ── Shared Helper (same pattern as data connectors) ─────────────

def _flow(collector, step, description, resp, method, endpoint, expected=(200,), prefix=""):
    data   = safe_json(resp)
    passed = resp.status_code in expected

    pretty = json.dumps(data, indent=2, default=str) if data is not None \
             else f"(status {resp.status_code}, no body)"

    logger.info("[%s%02d] %s %s → %s\n%s", prefix, step, method, endpoint, resp.status_code, pretty)

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
# LLM CONFIGURATIONS API TESTS
# ════════════════════════════════════════════════════════════════

class TestLLMConfigsFunctionalFlow:

    @pytest.fixture(scope="class")
    def base_payload(self):
        """Baseline payload for LLM config creation — mirrors Swagger example."""
        return {
            "model_name":   f"auto-test-model-{int(time.time())}",
            "description":  "Created by automated functional flow",
            "url":          "https://10.1.1.1",
            "username":     "check",
            "password":     "abc123",
            "api_key":      "123abc",
            "is_default":   False,
            "status":       "Inactive",
        }

    # ── Step 1: CREATE LLM CONFIG ──────────────────────────────
    def test_lc01_create_llm_config(self, ncp_token, report_collector, flow_state, base_payload):
        resp = create_llm_config(base_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 1,
            "CREATE LLM Config",
            resp, "POST", "/api/v1/llm-configs", (200, 201), prefix="LC"
        )
        assert passed, f"CREATE failed: expected 200/201, got {code}"

        # Extract config_id from response — field is 'id' per Swagger response body
        config_id = data.get("id") or data.get("config_id")

        # Fallback: scan list if response body didn't include id
        if not config_id:
            all_resp = get_all_llm_configs(ncp_token)
            all_data = safe_json(all_resp)
            if isinstance(all_data, list):
                for c in all_data:
                    if c.get("model_name") == base_payload["model_name"]:
                        config_id = c.get("id")
                        break

        if config_id:
            logger.info("[LC01] LLM Config created with id=%s", config_id)
        else:
            logger.warning("[LC01] Could not resolve config_id — downstream steps may fail")
            config_id = "unknown_id"

        flow_state["llm_config_id"] = config_id

    # ── Step 2: LIST LLM CONFIGS ───────────────────────────────
    def test_lc02_list_llm_configs(self, ncp_token, report_collector):
        resp = get_all_llm_configs(ncp_token)
        passed, data, code = _flow(
            report_collector, 2,
            "LIST LLM Configs",
            resp, "GET", "/api/v1/llm-configs", (200,), prefix="LC"
        )
        assert passed, f"LIST failed: expected 200, got {code}"

        # Verify response is a list
        assert isinstance(data, list), f"Expected list response, got: {type(data)}"
        logger.info("[LC02] Total LLM configs returned: %d", len(data))

    # ── Step 3: READ LLM CONFIG ────────────────────────────────
    def test_lc03_read_llm_config(self, ncp_token, report_collector, flow_state):
        config_id = flow_state.get("llm_config_id")

        resp = get_llm_config(config_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 3,
            f"READ LLM Config id={config_id}",
            resp, "GET", f"/api/v1/llm-configs/{config_id}", (200,), prefix="LC"
        )
        assert passed, f"READ failed: expected 200, got {code}"

        # Confirm we got the right record back
        assert data.get("id") == config_id or str(data.get("id")) == str(config_id), \
            f"Returned config id mismatch: expected {config_id}, got {data.get('id')}"

    # ── Step 4: UPDATE LLM CONFIG ──────────────────────────────
    def test_lc04_update_llm_config(self, ncp_token, report_collector, flow_state, base_payload):
        config_id = flow_state.get("llm_config_id")

        update_payload = base_payload.copy()
        update_payload["description"] = "Updated description by automated functional flow"
        update_payload["status"]      = "Inactive"   # keep inactive so it stays safe to delete

        resp = update_llm_config(config_id, update_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 4,
            f"UPDATE LLM Config id={config_id}",
            resp, "PUT", f"/api/v1/llm-configs/{config_id}", (200,), prefix="LC"
        )
        assert passed, f"UPDATE failed: expected 200, got {code}"

    # ── Step 5: DELETE LLM CONFIG ──────────────────────────────
    def test_lc05_delete_llm_config(self, ncp_token, report_collector, flow_state):
        config_id = flow_state.get("llm_config_id")

        resp = delete_llm_config(config_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 5,
            f"DELETE LLM Config id={config_id}",
            resp, "DELETE", f"/api/v1/llm-configs/{config_id}", (200, 204), prefix="LC"
        )
        assert passed, f"DELETE failed: expected 200/204, got {code}"

        logger.info("[LC05] LLM Config id=%s deleted successfully", config_id)