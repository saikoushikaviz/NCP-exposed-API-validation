"""
NCP Admin Files API — Functional Flow Tests

Covers 4 Admin Files endpoints (AF01–AF05):

  ── AF01: LIST ADMIN FILES ──────────────────────────────────────
  Step 1  GET /api/v1/admin/files?role_id=19
          → verify 200, non-empty list, target file present

  ── AF02: GET ADMIN FILE METADATA ───────────────────────────────
  Step 2  GET /api/v1/admin/files/{file_id}
          → verify 200, file_id matches, key fields present

  ── AF03: UPDATE ADMIN FILE ─────────────────────────────────────
  Step 3  PATCH /api/v1/admin/files/{file_id}
          → GET current metadata, send full body with updated description
          → verify 200 and updated field in response

  ── AF04: VERIFY UPDATE ─────────────────────────────────────────
  Step 4  GET /api/v1/admin/files/{file_id}
          → confirm description reflects the update

  ── AF05: DOWNLOAD ADMIN FILE ───────────────────────────────────
  Step 5  GET /api/v1/admin/files/{file_id}/download
          → verify 200 and Content-Disposition header present

Test data:
  file_id  : 1   (api_validation_check.docx)
  role_id  : 19  (query param for list)
  description updated to: "Updated by automated functional flow"

Note: DELETE admin file endpoint is intentionally excluded from this suite.
"""

import pytest
import logging
import json
import time

from api_client import (
    list_admin_files,
    get_admin_file,
    update_admin_file,
    download_admin_file,
    safe_json,
)
from config import (
    TEST_ADMIN_FILE_ID,
    TEST_ADMIN_FILES_ROLE_ID,
)

logger = logging.getLogger(__name__)


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
# ADMIN FILES FUNCTIONAL FLOW  (AF01 – AF05)
# ════════════════════════════════════════════════════════════════

class TestAdminFilesFunctionalFlow:

    # ── Step 1: LIST ADMIN FILES ───────────────────────────────
    def test_af01_list_admin_files(self, ncp_token, report_collector):
        role_id = TEST_ADMIN_FILES_ROLE_ID
        file_id = TEST_ADMIN_FILE_ID

        resp = list_admin_files(role_id=role_id, token=ncp_token)
        data = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[AF01] GET /api/v1/admin/files?role_id=%s → %s\n%s",
            role_id, resp.status_code, pretty,
        )

        files = data if isinstance(data, list) else data.get("data", []) if data else []
        ids_in_list  = [f.get("file_id") or f.get("id") for f in files]
        target_found = file_id in ids_in_list

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  role_id       : {role_id}\n"
            f"\nResult:\n"
            f"  Files returned: {len(files)}\n"
            f"  Looking for id: {file_id}\n"
            f"  Found in list : {'YES (PASS)' if target_found else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"GET list admin files role_id={role_id} — verify non-empty, file_id={file_id} present",
            api_method       = "GET",
            endpoint         = f"/api/v1/admin/files?role_id={role_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and target_found,
        )

        assert passed,       f"LIST admin files failed: expected 200, got {resp.status_code}"
        assert len(files) > 0, "LIST returned empty admin file list"
        assert target_found, f"file_id={file_id} not found in list response"
        logger.info("[AF01] %d file(s) returned, file_id=%s confirmed present", len(files), file_id)

    # ── Step 2: GET ADMIN FILE METADATA ───────────────────────
    def test_af02_get_admin_file(self, ncp_token, report_collector):
        file_id = TEST_ADMIN_FILE_ID

        resp = get_admin_file(file_id, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[AF02] GET /api/v1/admin/files/%s → %s\n%s",
            file_id, resp.status_code, pretty,
        )

        returned_id   = data.get("file_id") or data.get("id") if data else None
        file_name     = data.get("filename") or data.get("file_name", "N/A") if data else "N/A"
        uploader      = data.get("uploader_username", "N/A") if data else "N/A"
        id_match      = str(returned_id) == str(file_id)
        has_file_name = bool(file_name and file_name != "N/A")

        summary = (
            f"Status             : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  file_id          : {file_id}\n"
            f"\nMetadata Returned:\n"
            f"  file_id          : {returned_id} {'✓' if id_match else '✗'}\n"
            f"  filename         : {file_name} {'✓' if has_file_name else '✗'}\n"
            f"  uploader_username: {uploader}\n"
            f"  access_level     : {data.get('access_level', 'N/A') if data else 'N/A'}\n"
            f"  active_status    : {data.get('active_status', 'N/A') if data else 'N/A'}\n"
            f"\nField Checks:\n"
            f"  id matches       : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  filename present : {'YES (PASS)' if has_file_name else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"GET admin file metadata file_id={file_id} — verify id and filename",
            api_method       = "GET",
            endpoint         = f"/api/v1/admin/files/{file_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and has_file_name,
        )

        assert passed,       f"GET admin file failed: expected 200, got {resp.status_code}"
        assert id_match,     f"Returned file_id mismatch: expected {file_id}, got {returned_id}"
        assert has_file_name, "GET admin file response missing filename"
        logger.info("[AF02] file_id=%s metadata verified — filename=%s, uploader=%s",
                    file_id, file_name, uploader)

    # ── Step 3: UPDATE ADMIN FILE + VERIFY ────────────────────
    def test_af03_update_and_verify(self, ncp_token, report_collector):
        file_id = TEST_ADMIN_FILE_ID

        # GET current metadata — needed for full PATCH body and to compute new value
        current_resp = get_admin_file(file_id, ncp_token)
        current_data = safe_json(current_resp)
        assert current_resp.status_code == 200 and current_data, \
            f"Could not GET admin file before update: {current_resp.status_code}"

        current_desc = current_data.get("description") or ""

        # Always toggle so the change is visible regardless of previous state
        desc_a = "Automated test — description update A"
        desc_b = "Automated test — description update B"
        new_description = desc_b if current_desc == desc_a else desc_a

        logger.info(
            "[AF03] Before update: description='%s' → will change to='%s'",
            current_desc, new_description,
        )

        payload = {
            "filename":          current_data.get("filename") or current_data.get("file_name", ""),
            "source":            current_data.get("source", "File"),
            "description":       new_description,
            "uploaded_at":       current_data.get("uploaded_at", ""),
            "storage_path":      current_data.get("storage_path", ""),
            "uploader_username": current_data.get("uploader_username", ""),
            "access_level":      current_data.get("access_level", "everyone"),
            "tags":              current_data.get("tags", []),
            "organization_id":   current_data.get("organization_id", 1),
        }

        # ── PATCH ──
        resp = update_admin_file(file_id, payload, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[AF03] PATCH /api/v1/admin/files/%s → %s\n%s",
                    file_id, resp.status_code, pretty)

        updated_desc  = data.get("description") if data else None
        field_updated = updated_desc == new_description

        patch_summary = (
            f"Status              : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  file_id           : {file_id}\n"
            f"  Payload sent      :\n{json.dumps(payload, indent=4)}\n"
            f"\nBefore / After:\n"
            f"  description BEFORE: {current_desc}\n"
            f"  description AFTER : {updated_desc} "
            f"{'✓' if field_updated else '✗'}\n"
            f"  Changed           : {'YES — visible difference (PASS)' if field_updated else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = f"PATCH admin file_id={file_id} — toggle description (before: '{current_desc}' → after: '{new_description}')",
            api_method       = "PATCH",
            endpoint         = f"/api/v1/admin/files/{file_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = patch_summary,
            passed           = passed and field_updated,
        )

        assert passed,        f"UPDATE admin file failed: expected 200, got {resp.status_code}"
        assert field_updated, (
            f"description not updated: expected '{new_description}', got '{updated_desc}'"
        )

        # ── GET verify (within same test) ──
        verify_resp = get_admin_file(file_id, ncp_token)
        verify_data = safe_json(verify_resp)
        verify_passed = verify_resp.status_code == 200
        verify_pretty = json.dumps(verify_data, indent=2, default=str)

        logger.info("[AF03] GET verify /api/v1/admin/files/%s → %s\n%s",
                    file_id, verify_resp.status_code, verify_pretty)

        persisted_desc = verify_data.get("description") if verify_data else None
        verified       = persisted_desc == new_description

        verify_summary = (
            f"Status              : {verify_resp.status_code} ({'PASS' if verify_passed else 'FAIL'})\n"
            f"\nVerification (GET after PATCH):\n"
            f"  Expected description : {new_description}\n"
            f"  Stored description   : {persisted_desc} "
            f"{'✓' if verified else '✗'}\n"
            f"  Update persisted     : {'YES (PASS)' if verified else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{verify_pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = f"GET admin file_id={file_id} after PATCH — confirm description='{new_description}' persisted",
            api_method       = "GET",
            endpoint         = f"/api/v1/admin/files/{file_id}",
            expected_status  = "200",
            actual_status    = verify_resp.status_code,
            response_summary = verify_summary,
            passed           = verify_passed and verified,
        )

        assert verify_passed, f"GET verify failed: expected 200, got {verify_resp.status_code}"
        assert verified, (
            f"Update not persisted: expected '{new_description}', got '{persisted_desc}'"
        )
        logger.info("[AF03] file_id=%s — description changed from '%s' to '%s' and verified",
                    file_id, current_desc, persisted_desc)

    # ── Step 4: DOWNLOAD ADMIN FILE ────────────────────────────
    def test_af04_download_admin_file(self, ncp_token, report_collector):
        file_id = TEST_ADMIN_FILE_ID

        resp = download_admin_file(file_id, ncp_token)
        passed = resp.status_code == 200

        content_type  = resp.headers.get("Content-Type", "N/A")
        content_disp  = resp.headers.get("Content-Disposition", "N/A")
        content_len   = resp.headers.get("Content-Length", "N/A")
        content_bytes = resp.content
        has_disp      = content_disp != "N/A"

        logger.info(
            "[AF04] GET /api/v1/admin/files/%s/download → %s "
            "(Content-Type=%s, bytes=%d)",
            file_id, resp.status_code, content_type, len(content_bytes),
        )

        summary = (
            f"Status               : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  file_id            : {file_id}\n"
            f"\nDownload Result:\n"
            f"  Content-Type       : {content_type}\n"
            f"  Content-Length     : {content_len}\n"
            f"  Content-Disposition: {content_disp} {'✓' if has_disp else '✗'}\n"
            f"  Bytes received     : {len(content_bytes)}\n"
        )

        report_collector.add_flow(
            step             = 4,
            description      = f"GET download admin file_id={file_id} — verify 200 and Content-Disposition header",
            api_method       = "GET",
            endpoint         = f"/api/v1/admin/files/{file_id}/download",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_disp,
        )

        assert passed,   f"DOWNLOAD admin file failed: expected 200, got {resp.status_code}"
        assert has_disp, "DOWNLOAD response missing Content-Disposition header"
        logger.info(
            "[AF04] file_id=%s downloaded — %d bytes, Content-Disposition=%s",
            file_id, len(content_bytes), content_disp,
        )
