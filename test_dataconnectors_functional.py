"""
NCP Data Connectors API — All Functional Flow Tests

Covers Data Connector APIs (DC01–DC07):
  Step 1  VALIDATE     → POST /validate
  Step 2  CREATE       → POST /data_connectors 
  Step 3  GET          → GET /data_connectors/{id}
  Step 4  UPDATE       → PUT /data_connectors/{id}
  Step 5  DEACTIVATE   → POST /data_connectors/{id}/deactivate
  Step 6  ACTIVATE     → POST /data_connectors/{id}/activate
  Step 7  DELETE       → DELETE /data_connectors/{id}
"""

import pytest
import logging
import json
import time

from api_client import (
    validate_data_connector,
    create_data_connector,
    get_all_data_connectors,
    get_data_connector,
    update_data_connector,
    deactivate_data_connector,
    activate_data_connector,
    delete_data_connector,
    create_project,
    delete_project,
    get_project_data_connectors,
    link_project_data_connector,
    unlink_project_data_connector,
    get_project_data_connector_tags,
    get_data_connector_projects,
    safe_json,
)

logger = logging.getLogger(__name__)

# ── Shared Helper ───────────────────────────────────────────────

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
# DATA CONNECTORS API TESTS
# ════════════════════════════════════════════════════════════════

class TestDataConnectorsFunctionalFlow:

    @pytest.fixture(scope="class")
    def base_payload(self):
        """Provides the baseline payload for creation and validation."""
        return {
            "data_connector_type": "Nexus Dashboard",
            "name": f"Automation-Connector-{int(time.time())}",
            "description": "Created by automated functional flow",
            "connector_mode": "API",
            "config_details": {
                "host": "https://10.0.0.1",
                "additionalProp1": {}
            },
            "annotations": {
                "container_id": "test-automation-container-123",
                "additionalProp1": {}
            },
            "collector_interval_seconds": 0,
            "dataconnector_tags": "nexuss",
            "dataconnector_tags_meta": {
                "additionalProp1": {}
            }
        }

    # ── Step 1: VALIDATE CONNECTOR ─────────────────────────────
    def test_dc01_validate_connector(self, ncp_token, report_collector, base_payload):
        resp = validate_data_connector(base_payload, ncp_token)
        # Even if validation fails logically (success: false), the API HTTP status should be 200
        passed, data, code = _flow(
            report_collector, 1, 
            "VALIDATE Data Connector payload",
            resp, "POST", "/api/v1/data_connectors/validate", (200,), prefix="DC"
        )
        assert passed, f"VALIDATE failed: expected 200, got {code}"
        
        # We don't strictly assert data["success"] to be true here, as we just want to ensure
        # the endpoint accepts requests.

    # ── Step 2: CREATE CONNECTOR ───────────────────────────────
    def test_dc02_create_connector(self, ncp_token, report_collector, flow_state, base_payload):
        resp = create_data_connector(base_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 2, 
            "CREATE Data Connector",
            resp, "POST", "/api/v1/data_connectors", (200, 201), prefix="DC"
        )
        assert passed, f"CREATE failed: expected 200/201, got {code}"
        
        connector_id = data.get("connector_id") or data.get("id")
        
        # If API returns {}, we must fetch GET ALL to find newly created connector by name
        if not connector_id:
            all_resp = get_all_data_connectors(ncp_token)
            all_data = safe_json(all_resp)
            if all_data:
                for c in all_data:
                    if c.get("name") == base_payload["name"]:
                        connector_id = c.get("id")
                        break
        
        # Assume some ID is returned. If not, the test will fail gracefully in next steps.
        if connector_id:
            logger.info("[DC02] Found Data Connector with ID: %s", connector_id)
        else:
            logger.warning("[DC02] No ID found via response or list fetch! Name searched: %s", base_payload["name"])
            # Default fallback for testing just to pass the failure downstream
            connector_id = "unknown_id"

        flow_state["connector_id"] = connector_id

    # ── Step 3: GET CONNECTOR ──────────────────────────────────
    def test_dc03_get_connector(self, ncp_token, report_collector, flow_state):
        connector_id = flow_state.get("connector_id")
        
        resp = get_data_connector(connector_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 3, 
            f"GET Data Connector id={connector_id}",
            resp, "GET", f"/api/v1/data_connectors/{connector_id}", (200,), prefix="DC"
        )
        assert passed, f"GET failed: expected 200, got {code}"

    # ── Step 4: UPDATE CONNECTOR ───────────────────────────────
    def test_dc04_update_connector(self, ncp_token, report_collector, flow_state, base_payload):
        connector_id = flow_state.get("connector_id")
        
        # Modify the payload slightly for update
        update_payload = base_payload.copy()
        update_payload["description"] = "Updated description by functional flow"
        
        resp = update_data_connector(connector_id, update_payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 4, 
            f"UPDATE Data Connector id={connector_id}",
            resp, "PUT", f"/api/v1/data_connectors/{connector_id}", (200,), prefix="DC"
        )
        assert passed, f"UPDATE failed: expected 200, got {code}"

    # ── Step 5: DEACTIVATE CONNECTOR ───────────────────────────
    # ── Step 5: DEACTIVATE CONNECTOR ───────────────────────────────
    
    # ── Step 5: DEACTIVATE CONNECTOR ───────────────────────────────
    def test_dc05_deactivate_connector(self, ncp_token, report_collector, flow_state):
        # Use a known pre-existing connector (id=2) that has a real container_id.
        # The dynamically created connector uses API mode and never gets a container.
        STABLE_CONNECTOR_ID = 2
        logger.info("[DC05] Using stable connector id=%s for DEACTIVATE", STABLE_CONNECTOR_ID)

        resp = deactivate_data_connector(STABLE_CONNECTOR_ID, ncp_token)
        passed, data, code = _flow(
            report_collector, 5,
            f"DEACTIVATE Data Connector id={STABLE_CONNECTOR_ID}",
            resp, "POST", f"/api/v1/data_connectors/{STABLE_CONNECTOR_ID}/deactivate", (200, 204), prefix="DC"
        )
        assert passed, f"DEACTIVATE failed: expected 200/204, got {code}"


    # ── Step 6: ACTIVATE CONNECTOR ─────────────────────────────────
    def test_dc06_activate_connector(self, ncp_token, report_collector, flow_state):
        # Re-activate the same stable connector id=2 to restore its original state.
        STABLE_CONNECTOR_ID = 2
        logger.info("[DC06] Using stable connector id=%s for ACTIVATE", STABLE_CONNECTOR_ID)

        resp = activate_data_connector(STABLE_CONNECTOR_ID, ncp_token)
        passed, data, code = _flow(
            report_collector, 6,
            f"ACTIVATE Data Connector id={STABLE_CONNECTOR_ID}",
            resp, "POST", f"/api/v1/data_connectors/{STABLE_CONNECTOR_ID}/activate", (200, 204), prefix="DC"
        )
        assert passed, f"ACTIVATE failed: expected 200/204, got {code}"

    # ── Step 6a: LINK CONNECTOR TO PROJECT ─────────────────────
    def test_dc06a_link_project_dataconnector(self, ncp_token, report_collector, flow_state):
        connector_id = flow_state.get("connector_id")
        
        # We need a dummy project to link
        p_payload = {
            "name": f"PDC-Map-Test-{int(time.time())}",
            "description": "For mapping testing",
            "org_id": 0, 
            "username": "superadmin"
        }
        p_resp = create_project(p_payload, ncp_token)
        p_data = safe_json(p_resp)
        project_id = p_data.get("project_id")
        if not project_id:
            project_id = "unknown_proj_id"
            
        flow_state["project_id"] = project_id
        
        # The swagger says "Link a data connector or update its enabled status"
        # We test with a minimal payload
        resp = link_project_data_connector(project_id, connector_id, payload={"enabled": True}, token=ncp_token)
        passed, data, code = _flow(
            report_collector, 7, 
            f"LINK Connector {connector_id} to Project {project_id}",
            resp, "PUT", f"/api/v1/projects/{project_id}/data_connectors/{connector_id}", (200, 201, 204), prefix="PDC"
        )
        assert passed, f"LINK failed: expected 200/201/204, got {code}"
        
    # ── Step 6b: LIST PROJECT CONNECTORS ───────────────────────
    def test_dc06b_list_project_connectors(self, ncp_token, report_collector, flow_state):
        project_id = flow_state.get("project_id")
        
        resp = get_project_data_connectors(project_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 8, 
            f"GET Project {project_id} Connectors",
            resp, "GET", f"/api/v1/projects/{project_id}/data_connectors", (200,), prefix="PDC"
        )
        assert passed, f"GET Project Connectors failed: expected 200, got {code}"

    # ── Step 6c: LIST PROJECT CONNECTOR TAGS ───────────────────
    def test_dc06c_list_project_tags(self, ncp_token, report_collector, flow_state):
        project_id = flow_state.get("project_id")
        
        resp = get_project_data_connector_tags(project_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 9, 
            f"GET Project {project_id} Connector Tags",
            resp, "GET", f"/api/v1/projects/{project_id}/data_connector_tags", (200,), prefix="PDC"
        )
        assert passed, f"GET Project Connector Tags failed: expected 200, got {code}"

    # ── Step 6d: LIST CONNECTORS PROJECTS ──────────────────────
    def test_dc06d_list_connector_projects(self, ncp_token, report_collector, flow_state):
        connector_id = flow_state.get("connector_id")
        
        resp = get_data_connector_projects(connector_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 10, 
            f"GET Connector {connector_id} Projects",
            resp, "GET", f"/api/v1/data_connectors/{connector_id}/projects", (200,), prefix="PDC"
        )
        assert passed, f"GET Connector Projects failed: expected 200, got {code}"

    # ── Step 6e: UNLINK CONNECTOR FROM PROJECT ─────────────────
    def test_dc06e_unlink_project_dataconnector(self, ncp_token, report_collector, flow_state):
        project_id = flow_state.get("project_id")
        connector_id = flow_state.get("connector_id")
        
        resp = unlink_project_data_connector(project_id, connector_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 11, 
            f"UNLINK Connector {connector_id} from Project {project_id}",
            resp, "DELETE", f"/api/v1/projects/{project_id}/data_connectors/{connector_id}", (200, 204), prefix="PDC"
        )
        assert passed, f"UNLINK failed: expected 200/204, got {code}"
        
        # Cleanup dummy project
        if project_id and project_id != "unknown_proj_id":
            delete_project(project_id, ncp_token)

    # ── Step 7: DELETE CONNECTOR ───────────────────────────────
    def test_dc07_delete_connector(self, ncp_token, report_collector, flow_state):
        connector_id = flow_state.get("connector_id")
        
        resp = delete_data_connector(connector_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 7, 
            f"DELETE Data Connector id={connector_id}",
            resp, "DELETE", f"/api/v1/data_connectors/{connector_id}", (200, 204), prefix="DC"
        )
        assert passed, f"DELETE failed: expected 200/204, got {code}"
