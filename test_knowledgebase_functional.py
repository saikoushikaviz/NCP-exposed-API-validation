"""
NCP Knowledge Base API — Functional Flow Tests

Covers all 4 Knowledge Base endpoints (KB01–KB04):

  Step 1  UPLOAD FILE          → POST /api/v1/knowledge_base/upload
  Step 2  GET FILES            → GET  /api/v1/knowledge_base/files/{username}
  Step 3  UPDATE FILE DESC     → PUT  /api/v1/knowledge_base/files/{username}/{id}
  Step 4  DELETE FILE          → DELETE /api/v1/knowledge_base/files/{username}/{id}

Flow strategy:
  - UPLOAD the real 'api_validation_check.docx' file at Step 1.
  - GET at Step 2 confirms the file appears in the list and extracts the file id.
  - UPDATE at Step 3 modifies the file description.
  - DELETE at Step 4 cleans up — fully self-contained.

File used: api_validation_check.docx (must be in the same folder as test files)
Username:  superadmin (NCP_USERNAME from config)
"""

import os
import pytest
import logging
import json

from api_client import (
    upload_knowledge_base_file,
    get_knowledge_base_files,
    update_knowledge_base_file,
    delete_knowledge_base_file,
    safe_json,
)
from config import NCP_USERNAME

logger = logging.getLogger(__name__)

# File to upload — must be in the same directory as the test files
UPLOAD_FILENAME = "api_validation_check.docx"
UPLOAD_FILEPATH = os.path.join(os.path.dirname(__file__), UPLOAD_FILENAME)


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
# KNOWLEDGE BASE FUNCTIONAL FLOW
# ════════════════════════════════════════════════════════════════

class TestKnowledgeBaseFunctionalFlow:

    # ── Step 1: UPLOAD FILE ────────────────────────────────────
    def test_kb01_upload_file(self, ncp_token, report_collector, flow_state):
        # Guard: confirm the file actually exists before attempting upload
        assert os.path.isfile(UPLOAD_FILEPATH), (
            f"Upload file not found at: {UPLOAD_FILEPATH}\n"
            f"Place '{UPLOAD_FILENAME}' in the same folder as the test files."
        )

        resp = upload_knowledge_base_file(UPLOAD_FILEPATH, ncp_token)
        passed, data, code = _flow(
            report_collector, 1,
            f"UPLOAD file '{UPLOAD_FILENAME}' to knowledge base",
            resp, "POST", "/api/v1/knowledge_base/upload", (200, 201), prefix="KB",
        )
        assert passed, f"UPLOAD failed: expected 200/201, got {code}"

        # Try to get file id directly from upload response
        file_id = (
            data.get("id")
            or data.get("file_id")
            or data.get("kb_file_id")
        )

        if file_id:
            logger.info("[KB01] File uploaded successfully with id=%s", file_id)
        else:
            logger.info(
                "[KB01] id not in upload response — will resolve via GET FILES in KB02"
            )

        # Store whatever we have; KB02 will resolve if still None
        flow_state["kb_file_id"] = file_id
        flow_state["kb_username"] = NCP_USERNAME

    # ── Step 2: GET FILES ──────────────────────────────────────
    def test_kb02_get_files(self, ncp_token, report_collector, flow_state):
        username = flow_state.get("kb_username", NCP_USERNAME)

        resp = get_knowledge_base_files(username, ncp_token)
        passed, data, code = _flow(
            report_collector, 2,
            f"GET knowledge base files for username='{username}'",
            resp, "GET", f"/api/v1/knowledge_base/files/{username}", (200,), prefix="KB",
        )
        assert passed, f"GET FILES failed: expected 200, got {code}"

        # Response should be a list
        assert isinstance(data, list), \
            f"Expected list response for GET FILES, got: {type(data)}"
        logger.info("[KB02] Total files returned for '%s': %d", username, len(data))

        # If KB01 did not return a file id, resolve it here by matching filename
        if not flow_state.get("kb_file_id"):
            for f in data:
                fname = f.get("filename") or f.get("file_name") or f.get("name") or ""
                if UPLOAD_FILENAME in fname:
                    file_id = f.get("id") or f.get("file_id") or f.get("kb_file_id")
                    flow_state["kb_file_id"] = file_id
                    logger.info(
                        "[KB02] Resolved file id=%s by matching filename '%s'",
                        file_id, UPLOAD_FILENAME,
                    )
                    break

        assert flow_state.get("kb_file_id"), (
            f"Could not resolve file id for '{UPLOAD_FILENAME}' from GET FILES response. "
            f"Files returned: {data}"
        )

        # Confirm uploaded file appears in the list
        all_names = [
            f.get("filename") or f.get("file_name") or f.get("name") or ""
            for f in data
        ]
        assert any(UPLOAD_FILENAME in n for n in all_names), (
            f"Uploaded file '{UPLOAD_FILENAME}' not found in GET FILES response. "
            f"Files present: {all_names}"
        )

    # ── Step 3: UPDATE FILE DESCRIPTION ───────────────────────
    def test_kb03_update_file_description(self, ncp_token, report_collector, flow_state):
        username = flow_state.get("kb_username", NCP_USERNAME)
        file_id  = flow_state.get("kb_file_id")

        assert file_id, "File ID is missing from flow_state — upload might have failed"

        update_payload = {
            "description": "Updated by automated functional flow test"
        }

        # 🔹 Step 1: Update description
        resp = update_knowledge_base_file(username, file_id, update_payload, ncp_token)

        passed, data, code = _flow(
            report_collector, 3,
            f"UPDATE file description for id={file_id}, username='{username}'",
            resp, "PUT",
            f"/api/v1/knowledge_base/files/{username}/{file_id}",
            (200,), prefix="KB",
        )

        assert passed, f"UPDATE FILE DESCRIPTION failed: expected 200, got {code}"

        # 🔹 Step 2: Optional direct response validation
        if data and isinstance(data, dict) and data.get("description"):
            assert data.get("description") == update_payload["description"], (
                f"Description mismatch in response: "
                f"expected '{update_payload['description']}', got '{data.get('description')}'"
            )
            logger.info("[KB03] UPDATE response confirmed — description: %s", data.get("description"))

        # 🔹 Step 3: Re-fetch using GET API (STRONG VALIDATION)
        get_resp = get_knowledge_base_files(username, ncp_token)
        get_data = safe_json(get_resp)
        passed_get = get_resp.status_code == 200
        get_pretty = json.dumps(get_data, indent=2, default=str) if get_data is not None \
                     else f"(status {get_resp.status_code}, no body)"

        logger.info(
            "[KB03] GET /api/v1/knowledge_base/files/%s → %s\n%s",
            username, get_resp.status_code, get_pretty,
        )

        assert isinstance(get_data, list), "GET FILES response is not a list"

        # Find updated file
        updated_file = None
        for f in get_data:
            fid = f.get("id") or f.get("file_id") or f.get("kb_file_id")
            if str(fid) == str(file_id):
                updated_file = f
                break

        desc_verified = (
            updated_file is not None
            and updated_file.get("description") == update_payload["description"]
        )

        get_summary = (
            f"Status              : {get_resp.status_code} ({'PASS' if passed_get else 'FAIL'})\n"
            f"Looking for file id : {file_id}\n"
            f"Expected description: {update_payload['description']}\n"
            f"Stored  description : {updated_file.get('description') if updated_file else '(file not found)'}\n"
            f"Description match   : {'YES — description verified (PASS)' if desc_verified else 'NO — mismatch or file missing (FAIL)'}\n"
            f"Full Response       :\n{get_pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = f"GET files for username='{username}' — verify description updated for id={file_id}",
            api_method       = "GET",
            endpoint         = f"/api/v1/knowledge_base/files/{username}",
            expected_status  = "200",
            actual_status    = get_resp.status_code,
            response_summary = get_summary,
            passed           = passed_get and desc_verified,
        )

        assert updated_file, f"File id={file_id} not found after update"
        assert desc_verified, (
            f"Description NOT updated in system. "
            f"Expected: '{update_payload['description']}', "
            f"Got: '{updated_file.get('description')}'"
        )
        logger.info("[KB03] VERIFIED via GET — description successfully updated")
    # ── Step 4: DELETE FILE ────────────────────────────────────
    def test_kb04_delete_file(self, ncp_token, report_collector, flow_state):
        username = flow_state.get("kb_username", NCP_USERNAME)
        file_id  = flow_state.get("kb_file_id")

        resp = delete_knowledge_base_file(username, file_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 4,
            f"DELETE file id={file_id} for username='{username}'",
            resp, "DELETE",
            f"/api/v1/knowledge_base/files/{username}/{file_id}",
            (200, 204), prefix="KB",
        )
        assert passed, f"DELETE FILE failed: expected 200/204, got {code}"

        # Post-delete verification — confirm the file is no longer in the list
        all_resp = get_knowledge_base_files(username, ncp_token)
        all_data = safe_json(all_resp)
        passed_all = all_resp.status_code == 200
        all_pretty = json.dumps(all_data, indent=2, default=str) if all_data is not None \
                     else f"(status {all_resp.status_code}, no body)"

        logger.info(
            "[KB04] GET /api/v1/knowledge_base/files/%s → %s\n%s",
            username, all_resp.status_code, all_pretty,
        )

        if isinstance(all_data, list):
            remaining_ids = [
                str(f.get("id") or f.get("file_id") or f.get("kb_file_id") or "")
                for f in all_data
            ]
            removed = str(file_id) not in remaining_ids

            verify_summary = (
                f"Status              : {all_resp.status_code} ({'PASS' if passed_all else 'FAIL'})\n"
                f"Checking file id    : {file_id}\n"
                f"Removed from list   : {'YES — file confirmed absent (PASS)' if removed else 'NO — file still present (FAIL)'}\n"
                f"Verification        : {'file id=' + str(file_id) + ' is NOT in GET FILES — delete confirmed.' if removed else 'file id=' + str(file_id) + ' is STILL in GET FILES — delete may have failed.'}\n"
                f"Remaining files     : {len(all_data)}\n"
                f"Full Response       :\n{all_pretty}"
            )

            report_collector.add_flow(
                step             = 4,
                description      = f"GET files for username='{username}' — verify file id={file_id} is removed after DELETE",
                api_method       = "GET",
                endpoint         = f"/api/v1/knowledge_base/files/{username}",
                expected_status  = "200",
                actual_status    = all_resp.status_code,
                response_summary = verify_summary,
                passed           = passed_all and removed,
            )

            assert removed, (
                f"File id={file_id} still appears in GET FILES after DELETE. "
                f"Remaining ids: {remaining_ids}"
            )
            logger.info(
                "[KB04] File id=%s confirmed absent after DELETE. Remaining files: %d",
                file_id, len(all_data),
            )
        else:
            logger.warning(
                "[KB04] Could not verify post-delete state — "
                "GET FILES returned unexpected type: %s", type(all_data)
            )