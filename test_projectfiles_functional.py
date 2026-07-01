"""
NCP Project Files API — Functional Flow Tests

Covers 4 Project Files endpoints (PF01–PF03):

  ── PF01: LIST & GET METADATA ───────────────────────────────────
  Step 1  GET /api/v1/projects/{project_id}/files
          → verify 200, non-empty list, target file present
  Step 2  GET /api/v1/projects/{project_id}/files/{file_id}
          → verify 200, id matches, key fields present

  ── PF02: UPDATE FILE METADATA ──────────────────────────────────
  Step 3  PUT /api/v1/projects/{project_id}/files/{file_id}
          → change uploader_username to "koushik"
          → verify 200 and updated field in response
  Step 4  GET /api/v1/projects/{project_id}/files/{file_id}
          → confirm uploader_username reflects the update

  ── PF03: DOWNLOAD FILE ─────────────────────────────────────────
  Step 5  GET /api/v1/projects/{project_id}/files/{file_id}/download
          → verify 200 and non-empty content returned

Test data:
  project_id : 229
  file_id    : 6   (Outdated_APIs.docx)
  uploader_username updated to: "koushik"

Note: DELETE file endpoint is intentionally excluded from this suite.
"""

import pytest
import logging
import json

from api_client import (
    list_project_files,
    get_project_file,
    update_project_file,
    download_project_file,
    safe_json,
)
from config import (
    TEST_PROJECT_FILES_PROJECT_ID,
    TEST_PROJECT_FILE_ID,
)

logger = logging.getLogger(__name__)

_UPLOADER_A = "koushik"
_UPLOADER_B = "superadmin"


# ── Shared Helper ───────────────────────────────────────────────

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
# PROJECT FILES FUNCTIONAL FLOW  (PF01 – PF03)
# ════════════════════════════════════════════════════════════════

class TestProjectFilesFunctionalFlow:

    # ── Step 1: LIST FILES ─────────────────────────────────────
    def test_pf01_list_project_files(self, ncp_token, report_collector):
        project_id = TEST_PROJECT_FILES_PROJECT_ID
        file_id    = TEST_PROJECT_FILE_ID

        resp = list_project_files(project_id, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[PF01] GET /api/v1/projects/%s/files → %s\n%s",
            project_id, resp.status_code, pretty,
        )

        files = data if isinstance(data, list) else data.get("data", []) if data else []
        ids_in_list = [f.get("file_id") or f.get("id") for f in files]
        target_found = file_id in ids_in_list

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id    : {project_id}\n"
            f"\nResult:\n"
            f"  Files returned: {len(files)}\n"
            f"  Looking for id: {file_id}\n"
            f"  Found in list : {'YES (PASS)' if target_found else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"GET list files for project_id={project_id} — verify non-empty, file_id={file_id} present",
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{project_id}/files",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and target_found,
        )

        assert passed,       f"LIST project files failed: expected 200, got {resp.status_code}"
        assert len(files) > 0, "LIST returned empty file list"
        assert target_found, f"file_id={file_id} not found in list response"
        logger.info("[PF01] %d file(s) returned, file_id=%s confirmed present", len(files), file_id)

    # ── Step 2: GET FILE METADATA ──────────────────────────────
    def test_pf02_get_file_metadata(self, ncp_token, report_collector):
        project_id = TEST_PROJECT_FILES_PROJECT_ID
        file_id    = TEST_PROJECT_FILE_ID

        resp = get_project_file(project_id, file_id, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[PF02] GET /api/v1/projects/%s/files/%s → %s\n%s",
            project_id, file_id, resp.status_code, pretty,
        )

        returned_id    = data.get("file_id") or data.get("id") if data else None
        file_name      = data.get("filename") or data.get("file_name", "N/A") if data else "N/A"
        uploader       = data.get("uploader_username", "N/A") if data else "N/A"
        id_match       = str(returned_id) == str(file_id)
        has_file_name  = bool(file_name and file_name != "N/A")

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id      : {project_id}\n"
            f"  file_id         : {file_id}\n"
            f"\nMetadata Returned:\n"
            f"  id              : {returned_id} {'✓' if id_match else '✗'}\n"
            f"  filename        : {file_name} {'✓' if has_file_name else '✗'}\n"
            f"  uploader_username: {uploader}\n"
            f"  project_id      : {data.get('project_id', 'N/A') if data else 'N/A'}\n"
            f"\nField Checks:\n"
            f"  id matches      : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  file_name present: {'YES (PASS)' if has_file_name else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"GET file metadata project_id={project_id} file_id={file_id} — verify id and file_name",
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{project_id}/files/{file_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and has_file_name,
        )

        assert passed,      f"GET file metadata failed: expected 200, got {resp.status_code}"
        assert id_match,    f"Returned id mismatch: expected {file_id}, got {returned_id}"
        assert has_file_name, "GET file metadata response missing file_name"
        logger.info("[PF02] file_id=%s metadata verified — file_name=%s, uploader=%s",
                    file_id, file_name, uploader)

    # ── Step 3: UPDATE FILE METADATA + VERIFY ─────────────────
    def test_pf03_update_and_verify(self, ncp_token, report_collector):
        project_id = TEST_PROJECT_FILES_PROJECT_ID
        file_id    = TEST_PROJECT_FILE_ID

        # GET current metadata — needed for full PUT body and to compute new value
        current_resp = get_project_file(project_id, file_id, ncp_token)
        current_data = safe_json(current_resp)
        assert current_resp.status_code == 200 and current_data, \
            f"Could not GET file metadata before update: {current_resp.status_code}"

        current_uploader = current_data.get("uploader_username", "")

        # Always toggle so the change is visible regardless of previous state
        new_uploader = _UPLOADER_B if current_uploader == _UPLOADER_A else _UPLOADER_A

        logger.info(
            "[PF03] Before update: uploader_username='%s' → will change to='%s'",
            current_uploader, new_uploader,
        )

        payload = {
            "project_id":        project_id,
            "filename":          current_data.get("filename") or current_data.get("file_name"),
            "storage_path":      current_data.get("storage_path", ""),
            "uploader_username": new_uploader,
        }

        # ── PUT ──
        resp = update_project_file(project_id, file_id, payload, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[PF03] PUT /api/v1/projects/%s/files/%s → %s\n%s",
                    project_id, file_id, resp.status_code, pretty)

        updated_uploader = data.get("uploader_username") if data else None
        field_updated    = updated_uploader == new_uploader

        put_summary = (
            f"Status              : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id        : {project_id}\n"
            f"  file_id           : {file_id}\n"
            f"  Payload sent      :\n{json.dumps(payload, indent=4)}\n"
            f"\nBefore / After:\n"
            f"  uploader BEFORE   : {current_uploader}\n"
            f"  uploader AFTER    : {updated_uploader} "
            f"{'✓' if field_updated else '✗'}\n"
            f"  Changed           : {'YES — visible difference (PASS)' if field_updated else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = f"PUT file_id={file_id} — toggle uploader_username ('{current_uploader}' → '{new_uploader}')",
            api_method       = "PUT",
            endpoint         = f"/api/v1/projects/{project_id}/files/{file_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = put_summary,
            passed           = passed and field_updated,
        )

        assert passed,        f"UPDATE file metadata failed: expected 200, got {resp.status_code}"
        assert field_updated, (
            f"uploader_username not updated: expected '{new_uploader}', got '{updated_uploader}'"
        )

        # ── GET verify (within same test) ──
        verify_resp = get_project_file(project_id, file_id, ncp_token)
        verify_data = safe_json(verify_resp)
        verify_passed = verify_resp.status_code == 200
        verify_pretty = json.dumps(verify_data, indent=2, default=str)

        logger.info("[PF03] GET verify /api/v1/projects/%s/files/%s → %s\n%s",
                    project_id, file_id, verify_resp.status_code, verify_pretty)

        persisted_uploader = verify_data.get("uploader_username") if verify_data else None
        verified           = persisted_uploader == new_uploader

        verify_summary = (
            f"Status              : {verify_resp.status_code} ({'PASS' if verify_passed else 'FAIL'})\n"
            f"\nVerification (GET after PUT):\n"
            f"  Expected uploader_username : {new_uploader}\n"
            f"  Stored uploader_username   : {persisted_uploader} "
            f"{'✓' if verified else '✗'}\n"
            f"  Update persisted           : {'YES (PASS)' if verified else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{verify_pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = f"GET file_id={file_id} after PUT — confirm uploader_username='{new_uploader}' persisted",
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{project_id}/files/{file_id}",
            expected_status  = "200",
            actual_status    = verify_resp.status_code,
            response_summary = verify_summary,
            passed           = verify_passed and verified,
        )

        assert verify_passed, f"GET verify failed: expected 200, got {verify_resp.status_code}"
        assert verified, (
            f"Update not persisted: expected uploader_username='{new_uploader}', "
            f"got '{persisted_uploader}'"
        )
        logger.info("[PF03] file_id=%s — uploader changed from '%s' to '%s' and verified",
                    file_id, current_uploader, persisted_uploader)

    # ── Step 4: DOWNLOAD FILE ──────────────────────────────────
    def test_pf04_download_file(self, ncp_token, report_collector):
        project_id = TEST_PROJECT_FILES_PROJECT_ID
        file_id    = TEST_PROJECT_FILE_ID

        resp = download_project_file(project_id, file_id, ncp_token)
        passed = resp.status_code == 200

        content_type   = resp.headers.get("Content-Type", "N/A")
        content_length = resp.headers.get("Content-Length", "N/A")
        content_disp   = resp.headers.get("Content-Disposition", "N/A")

        content_bytes = resp.content
        has_content   = len(content_bytes) > 0

        logger.info(
            "[PF04] GET /api/v1/projects/%s/files/%s/download → %s "
            "(Content-Type=%s, bytes=%d)",
            project_id, file_id, resp.status_code, content_type, len(content_bytes),
        )

        summary = (
            f"Status              : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id        : {project_id}\n"
            f"  file_id           : {file_id}\n"
            f"\nDownload Result:\n"
            f"  Content-Type      : {content_type}\n"
            f"  Content-Length    : {content_length}\n"
            f"  Content-Disposition: {content_disp}\n"
            f"  Bytes received    : {len(content_bytes)}\n"
            f"  Has content       : {'YES (PASS)' if has_content else 'NO — empty body (FAIL)'}\n"
        )

        report_collector.add_flow(
            step             = 4,
            description      = f"GET download file_id={file_id} — verify 200 and non-empty content",
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{project_id}/files/{file_id}/download",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_content,
        )

        assert passed,      f"DOWNLOAD file failed: expected 200, got {resp.status_code}"
        assert has_content, "DOWNLOAD returned empty response body"
        logger.info(
            "[PF04] file_id=%s downloaded successfully — %d bytes, Content-Type=%s",
            file_id, len(content_bytes), content_type,
        )
