"""
NCP Exports API — Functional Flow Tests

Covers the Exports endpoints (EX01 – ...). This suite groups all 8 Exports
APIs together; steps are added as each endpoint spec is provided.

  ── EX01: LIST EXPORTS ──────────────────────────────────────────
  Step 1  GET /api/v1/projects/{project_id}/exports
              ?username=&export_format=&status=&conversation_id=
          → verify 200, list response, every returned export matches
            the applied filters

  ── EX02: GET EXPORT METADATA ───────────────────────────────────
  Step 2  GET /api/v1/projects/{project_id}/exports/{export_id}
          → verify 200, export_id and project_id match, key fields present

  ── EX03: DOWNLOAD EXPORT ───────────────────────────────────────
  Step 3  GET /api/v1/projects/{project_id}/exports/{export_id}/download
          → verify 200, Content-Disposition header present, bytes received

  ── EX04: PREVIEW EXPORT ────────────────────────────────────────
  Step 4  GET /api/v1/projects/{project_id}/exports/{export_id}/preview
          → verify 200, columns + rows present, row width matches columns

  ── EX05: LIST CONVERSATION EXPORTS ─────────────────────────────
  Step 5  GET /api/v1/conversations/{conversation_id}/exports
          → verify 200, list response, every export belongs to the
            requested conversation, target export_id present

  ── EX06: DOWNLOAD USER EXPORT ──────────────────────────────────
  Step 6  GET /api/v1/exports/{export_id}/download   (no project scope)
          → verify 200, Content-Disposition header present, bytes received

  ── EX07: PREVIEW USER EXPORT ───────────────────────────────────
  Step 7  GET /api/v1/exports/{export_id}/preview   (no project scope)
          → verify 200, columns + rows present, row width matches columns

  ── EX08: DELETE EXPORT ─────────────────────────────────────────
  Step 8  DELETE /api/v1/projects/{project_id}/exports/{export_id}
          → verify 200 and "deleted" confirmation, then GET the export
            and confirm it is no longer retrievable (404)

          NOTE: destructive — removes the file + DB record. Targets
          TEST_EXPORT_DELETE_ID (a disposable export), NOT TEST_EXPORT_ID,
          so the read/download/preview steps stay re-runnable.

Test data (from List Exports sample response, project_id=2):
  project_id      : 2
  username        : superadmin
  export_format   : csv
  status          : completed
  conversation_id : 31
  export_id       : 6
"""

import pytest
import logging
import json

from api_client import (
    list_exports,
    get_export,
    download_export,
    preview_export,
    list_conversation_exports,
    download_user_export,
    preview_user_export,
    delete_export,
    safe_json,
)
from config import (
    TEST_EXPORTS_PROJECT_ID,
    TEST_EXPORTS_USERNAME,
    TEST_EXPORT_FORMAT,
    TEST_EXPORT_STATUS,
    TEST_EXPORT_CONVERSATION_ID,
    TEST_EXPORT_ID,
    TEST_EXPORT_DELETE_ID,
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
# EXPORTS FUNCTIONAL FLOW  (EX01 – ...)
# ════════════════════════════════════════════════════════════════

class TestExportsFunctionalFlow:

    # ── Step 1: LIST EXPORTS ───────────────────────────────────
    def test_ex01_list_exports(self, ncp_token, report_collector):
        project_id      = TEST_EXPORTS_PROJECT_ID
        username        = TEST_EXPORTS_USERNAME
        export_format   = TEST_EXPORT_FORMAT
        status          = TEST_EXPORT_STATUS
        conversation_id = TEST_EXPORT_CONVERSATION_ID

        resp = list_exports(
            project_id      = project_id,
            username        = username,
            export_format   = export_format,
            status          = status,
            conversation_id = conversation_id,
            token           = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[EX01] GET /api/v1/projects/%s/exports"
            "?username=%s&export_format=%s&status=%s&conversation_id=%s → %s\n%s",
            project_id, username, export_format, status, conversation_id,
            resp.status_code, pretty,
        )

        exports = data if isinstance(data, list) \
                  else data.get("data", []) if data else []

        # Every returned export must respect the applied filters
        filters_ok = all(
            e.get("export_format") == export_format
            and e.get("status") == status
            and e.get("conversation_id") == conversation_id
            and e.get("requested_by") == username
            for e in exports
        )
        ids_in_list  = [e.get("export_id") for e in exports]
        target_found = TEST_EXPORT_ID in ids_in_list

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest Filters:\n"
            f"  project_id      : {project_id}\n"
            f"  username        : {username}\n"
            f"  export_format   : {export_format}\n"
            f"  status          : {status}\n"
            f"  conversation_id : {conversation_id}\n"
            f"\nResult:\n"
            f"  Exports returned: {len(exports)}\n"
            f"  Filters honored : {'YES (PASS)' if filters_ok else 'NO (FAIL)'}\n"
            f"  export_id {TEST_EXPORT_ID} present: {'YES' if target_found else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = (
                f"GET list exports project_id={project_id} "
                f"(username={username}, export_format={export_format}, "
                f"status={status}, conversation_id={conversation_id}) "
                f"— verify 200 and filters honored"
            ),
            api_method       = "GET",
            endpoint         = (
                f"/api/v1/projects/{project_id}/exports"
                f"?username={username}&export_format={export_format}"
                f"&status={status}&conversation_id={conversation_id}"
            ),
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and filters_ok,
        )

        assert passed, f"LIST exports failed: expected 200, got {resp.status_code}"
        assert isinstance(exports, list), "LIST exports did not return a list"
        assert filters_ok, "One or more returned exports do not match the applied filters"
        logger.info(
            "[EX01] %d export(s) returned for project_id=%s — filters honored",
            len(exports), project_id,
        )

    # ── Step 2: GET EXPORT METADATA ────────────────────────────
    def test_ex02_get_export_metadata(self, ncp_token, report_collector):
        project_id = TEST_EXPORTS_PROJECT_ID
        export_id  = TEST_EXPORT_ID

        resp = get_export(project_id, export_id, ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[EX02] GET /api/v1/projects/%s/exports/%s → %s\n%s",
            project_id, export_id, resp.status_code, pretty,
        )

        returned_id      = data.get("export_id") if data else None
        returned_project = data.get("project_id") if data else None
        filename         = data.get("filename", "N/A") if data else "N/A"
        export_format    = data.get("export_format", "N/A") if data else "N/A"
        status           = data.get("status", "N/A") if data else "N/A"

        id_match      = str(returned_id) == str(export_id)
        project_match = str(returned_project) == str(project_id)
        has_filename  = bool(filename and filename != "N/A")

        summary = (
            f"Status             : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id       : {project_id}\n"
            f"  export_id        : {export_id}\n"
            f"\nMetadata Returned:\n"
            f"  export_id        : {returned_id} {'✓' if id_match else '✗'}\n"
            f"  project_id       : {returned_project} {'✓' if project_match else '✗'}\n"
            f"  filename         : {filename} {'✓' if has_filename else '✗'}\n"
            f"  export_format    : {export_format}\n"
            f"  status           : {status}\n"
            f"  conversation_id  : {data.get('conversation_id', 'N/A') if data else 'N/A'}\n"
            f"  file_size_bytes  : {data.get('file_size_bytes', 'N/A') if data else 'N/A'}\n"
            f"  download_count   : {data.get('download_count', 'N/A') if data else 'N/A'}\n"
            f"\nField Checks:\n"
            f"  export_id matches : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  project_id matches: {'YES (PASS)' if project_match else 'NO (FAIL)'}\n"
            f"  filename present  : {'YES (PASS)' if has_filename else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = (
                f"GET export metadata project_id={project_id} export_id={export_id} "
                f"— verify export_id/project_id match and filename present"
            ),
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{project_id}/exports/{export_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and project_match and has_filename,
        )

        assert passed,        f"GET export failed: expected 200, got {resp.status_code}"
        assert id_match,      f"Returned export_id mismatch: expected {export_id}, got {returned_id}"
        assert project_match, f"Returned project_id mismatch: expected {project_id}, got {returned_project}"
        assert has_filename,  "GET export response missing filename"
        logger.info(
            "[EX02] export_id=%s metadata verified — filename=%s, status=%s",
            export_id, filename, status,
        )

    # ── Step 3: DOWNLOAD EXPORT ────────────────────────────────
    def test_ex03_download_export(self, ncp_token, report_collector):
        project_id = TEST_EXPORTS_PROJECT_ID
        export_id  = TEST_EXPORT_ID

        resp = download_export(project_id, export_id, ncp_token)
        passed = resp.status_code == 200

        content_type  = resp.headers.get("Content-Type", "N/A")
        content_disp  = resp.headers.get("Content-Disposition", "N/A")
        content_len   = resp.headers.get("Content-Length", "N/A")
        content_bytes = resp.content
        has_disp      = content_disp != "N/A"
        has_bytes     = len(content_bytes) > 0

        logger.info(
            "[EX03] GET /api/v1/projects/%s/exports/%s/download → %s "
            "(Content-Type=%s, bytes=%d)",
            project_id, export_id, resp.status_code, content_type, len(content_bytes),
        )

        summary = (
            f"Status               : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id         : {project_id}\n"
            f"  export_id          : {export_id}\n"
            f"\nDownload Result:\n"
            f"  Content-Type       : {content_type}\n"
            f"  Content-Length     : {content_len}\n"
            f"  Content-Disposition: {content_disp} {'✓' if has_disp else '✗'}\n"
            f"  Bytes received     : {len(content_bytes)} {'✓' if has_bytes else '✗'}\n"
        )

        report_collector.add_flow(
            step             = 3,
            description      = (
                f"GET download export project_id={project_id} export_id={export_id} "
                f"— verify 200, Content-Disposition header and bytes received"
            ),
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{project_id}/exports/{export_id}/download",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_disp and has_bytes,
        )

        assert passed,    f"DOWNLOAD export failed: expected 200, got {resp.status_code}"
        assert has_disp,  "DOWNLOAD response missing Content-Disposition header"
        assert has_bytes, "DOWNLOAD response body was empty"
        logger.info(
            "[EX03] export_id=%s downloaded — %d bytes, Content-Disposition=%s",
            export_id, len(content_bytes), content_disp,
        )

    # ── Step 4: PREVIEW EXPORT ─────────────────────────────────
    def test_ex04_preview_export(self, ncp_token, report_collector):
        project_id = TEST_EXPORTS_PROJECT_ID
        export_id  = TEST_EXPORT_ID

        resp = preview_export(project_id, export_id, ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[EX04] GET /api/v1/projects/%s/exports/%s/preview → %s\n%s",
            project_id, export_id, resp.status_code, pretty,
        )

        columns       = data.get("columns", []) if data else []
        rows          = data.get("rows", []) if data else []
        total_rows    = data.get("total_rows", "N/A") if data else "N/A"
        total_columns = data.get("total_columns", "N/A") if data else "N/A"
        filename      = data.get("filename", "N/A") if data else "N/A"
        export_format = data.get("export_format", "N/A") if data else "N/A"

        has_columns    = isinstance(columns, list) and len(columns) > 0
        rows_is_list   = isinstance(rows, list)
        # Every previewed row should have the same width as the columns header
        width_matches  = rows_is_list and all(
            isinstance(r, list) and len(r) == len(columns) for r in rows
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id      : {project_id}\n"
            f"  export_id       : {export_id}\n"
            f"\nPreview Returned:\n"
            f"  filename        : {filename}\n"
            f"  export_format   : {export_format}\n"
            f"  columns         : {len(columns)} {'✓' if has_columns else '✗'}\n"
            f"  rows            : {len(rows) if rows_is_list else 'N/A'} {'✓' if rows_is_list else '✗'}\n"
            f"  total_rows      : {total_rows}\n"
            f"  total_columns   : {total_columns}\n"
            f"  truncated_columns: {data.get('truncated_columns', 'N/A') if data else 'N/A'}\n"
            f"\nField Checks:\n"
            f"  columns present : {'YES (PASS)' if has_columns else 'NO (FAIL)'}\n"
            f"  rows is list    : {'YES (PASS)' if rows_is_list else 'NO (FAIL)'}\n"
            f"  row width==cols : {'YES (PASS)' if width_matches else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 4,
            description      = (
                f"GET preview export project_id={project_id} export_id={export_id} "
                f"— verify 200, columns + rows present, row width matches columns"
            ),
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{project_id}/exports/{export_id}/preview",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_columns and rows_is_list and width_matches,
        )

        assert passed,        f"PREVIEW export failed: expected 200, got {resp.status_code}"
        assert has_columns,   "PREVIEW response missing/empty 'columns'"
        assert rows_is_list,  "PREVIEW response 'rows' is not a list"
        assert width_matches, "One or more preview rows do not match the column count"
        logger.info(
            "[EX04] export_id=%s preview verified — %d columns, %d rows (total_rows=%s)",
            export_id, len(columns), len(rows), total_rows,
        )

    # ── Step 5: LIST CONVERSATION EXPORTS ──────────────────────
    def test_ex05_list_conversation_exports(self, ncp_token, report_collector):
        conversation_id = TEST_EXPORT_CONVERSATION_ID

        resp = list_conversation_exports(conversation_id, ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[EX05] GET /api/v1/conversations/%s/exports → %s\n%s",
            conversation_id, resp.status_code, pretty,
        )

        exports = data if isinstance(data, list) \
                  else data.get("data", []) if data else []

        # Every returned export must belong to the requested conversation
        conversation_ok = all(
            e.get("conversation_id") == conversation_id for e in exports
        )
        ids_in_list  = [e.get("export_id") for e in exports]
        target_found = TEST_EXPORT_ID in ids_in_list

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  conversation_id : {conversation_id}\n"
            f"\nResult:\n"
            f"  Exports returned: {len(exports)}\n"
            f"  All match conv. : {'YES (PASS)' if conversation_ok else 'NO (FAIL)'}\n"
            f"  export_id {TEST_EXPORT_ID} present: {'YES' if target_found else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 5,
            description      = (
                f"GET list conversation exports conversation_id={conversation_id} "
                f"— verify 200 and every export belongs to the conversation"
            ),
            api_method       = "GET",
            endpoint         = f"/api/v1/conversations/{conversation_id}/exports",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and conversation_ok,
        )

        assert passed,           f"LIST conversation exports failed: expected 200, got {resp.status_code}"
        assert isinstance(exports, list), "LIST conversation exports did not return a list"
        assert conversation_ok,  "One or more exports do not belong to the requested conversation"
        logger.info(
            "[EX05] %d export(s) returned for conversation_id=%s — all match",
            len(exports), conversation_id,
        )

    # ── Step 6: DOWNLOAD USER EXPORT (no project scope) ────────
    def test_ex06_download_user_export(self, ncp_token, report_collector):
        export_id = TEST_EXPORT_ID

        resp = download_user_export(export_id, ncp_token)
        passed = resp.status_code == 200

        content_type  = resp.headers.get("Content-Type", "N/A")
        content_disp  = resp.headers.get("Content-Disposition", "N/A")
        content_len   = resp.headers.get("Content-Length", "N/A")
        content_bytes = resp.content
        has_disp      = content_disp != "N/A"
        has_bytes     = len(content_bytes) > 0

        logger.info(
            "[EX06] GET /api/v1/exports/%s/download → %s "
            "(Content-Type=%s, bytes=%d)",
            export_id, resp.status_code, content_type, len(content_bytes),
        )

        summary = (
            f"Status               : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  export_id          : {export_id}\n"
            f"\nDownload Result:\n"
            f"  Content-Type       : {content_type}\n"
            f"  Content-Length     : {content_len}\n"
            f"  Content-Disposition: {content_disp} {'✓' if has_disp else '✗'}\n"
            f"  Bytes received     : {len(content_bytes)} {'✓' if has_bytes else '✗'}\n"
        )

        report_collector.add_flow(
            step             = 6,
            description      = (
                f"GET download user export export_id={export_id} (no project scope) "
                f"— verify 200, Content-Disposition header and bytes received"
            ),
            api_method       = "GET",
            endpoint         = f"/api/v1/exports/{export_id}/download",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_disp and has_bytes,
        )

        assert passed,    f"DOWNLOAD user export failed: expected 200, got {resp.status_code}"
        assert has_disp,  "DOWNLOAD user export response missing Content-Disposition header"
        assert has_bytes, "DOWNLOAD user export response body was empty"
        logger.info(
            "[EX06] export_id=%s downloaded — %d bytes, Content-Disposition=%s",
            export_id, len(content_bytes), content_disp,
        )

    # ── Step 7: PREVIEW USER EXPORT (no project scope) ─────────
    def test_ex07_preview_user_export(self, ncp_token, report_collector):
        export_id = TEST_EXPORT_ID

        resp = preview_user_export(export_id, ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[EX07] GET /api/v1/exports/%s/preview → %s\n%s",
            export_id, resp.status_code, pretty,
        )

        columns       = data.get("columns", []) if data else []
        rows          = data.get("rows", []) if data else []
        total_rows    = data.get("total_rows", "N/A") if data else "N/A"
        total_columns = data.get("total_columns", "N/A") if data else "N/A"
        filename      = data.get("filename", "N/A") if data else "N/A"
        export_format = data.get("export_format", "N/A") if data else "N/A"

        has_columns   = isinstance(columns, list) and len(columns) > 0
        rows_is_list  = isinstance(rows, list)
        width_matches = rows_is_list and all(
            isinstance(r, list) and len(r) == len(columns) for r in rows
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  export_id       : {export_id}\n"
            f"\nPreview Returned:\n"
            f"  filename        : {filename}\n"
            f"  export_format   : {export_format}\n"
            f"  columns         : {len(columns)} {'✓' if has_columns else '✗'}\n"
            f"  rows            : {len(rows) if rows_is_list else 'N/A'} {'✓' if rows_is_list else '✗'}\n"
            f"  total_rows      : {total_rows}\n"
            f"  total_columns   : {total_columns}\n"
            f"  truncated_columns: {data.get('truncated_columns', 'N/A') if data else 'N/A'}\n"
            f"\nField Checks:\n"
            f"  columns present : {'YES (PASS)' if has_columns else 'NO (FAIL)'}\n"
            f"  rows is list    : {'YES (PASS)' if rows_is_list else 'NO (FAIL)'}\n"
            f"  row width==cols : {'YES (PASS)' if width_matches else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 7,
            description      = (
                f"GET preview user export export_id={export_id} (no project scope) "
                f"— verify 200, columns + rows present, row width matches columns"
            ),
            api_method       = "GET",
            endpoint         = f"/api/v1/exports/{export_id}/preview",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_columns and rows_is_list and width_matches,
        )

        assert passed,        f"PREVIEW user export failed: expected 200, got {resp.status_code}"
        assert has_columns,   "PREVIEW user export response missing/empty 'columns'"
        assert rows_is_list,  "PREVIEW user export response 'rows' is not a list"
        assert width_matches, "One or more preview rows do not match the column count"
        logger.info(
            "[EX07] export_id=%s preview verified — %d columns, %d rows (total_rows=%s)",
            export_id, len(columns), len(rows), total_rows,
        )

    # ── Step 8: DELETE EXPORT (destructive) ────────────────────
    def test_ex08_delete_export(self, ncp_token, report_collector):
        project_id = TEST_EXPORTS_PROJECT_ID
        export_id  = TEST_EXPORT_DELETE_ID

        # ── DELETE ──
        resp = delete_export(project_id, export_id, ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[EX08] DELETE /api/v1/projects/%s/exports/%s → %s\n%s",
            project_id, export_id, resp.status_code, pretty,
        )

        detail        = data.get("detail", "") if isinstance(data, dict) else str(data or "")
        confirmed_msg = "delet" in str(detail).lower()

        # ── VERIFY gone (GET should no longer find it) ──
        verify_resp   = get_export(project_id, export_id, ncp_token)
        verify_data   = safe_json(verify_resp)
        gone          = verify_resp.status_code in (404, 410)
        verify_pretty = json.dumps(verify_data, indent=2, default=str)

        logger.info(
            "[EX08] GET verify /api/v1/projects/%s/exports/%s → %s (expect 404/410)\n%s",
            project_id, export_id, verify_resp.status_code, verify_pretty,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id      : {project_id}\n"
            f"  export_id       : {export_id} (TEST_EXPORT_DELETE_ID — disposable)\n"
            f"\nDelete Result:\n"
            f"  detail          : {detail}\n"
            f"  confirmed msg   : {'YES (PASS)' if confirmed_msg else 'NO (FAIL)'}\n"
            f"\nDeletion Verified (GET after DELETE):\n"
            f"  GET status      : {verify_resp.status_code}\n"
            f"  no longer found : {'YES (PASS)' if gone else 'NO (FAIL)'}\n"
            f"\nDelete Response :\n{pretty}\n"
            f"\nVerify Response :\n{verify_pretty}"
        )

        report_collector.add_flow(
            step             = 8,
            description      = (
                f"DELETE export project_id={project_id} export_id={export_id} "
                f"— verify 200 + confirmation, then GET confirms it is gone (404)"
            ),
            api_method       = "DELETE",
            endpoint         = f"/api/v1/projects/{project_id}/exports/{export_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and confirmed_msg and gone,
        )

        assert passed,        f"DELETE export failed: expected 200, got {resp.status_code}"
        assert confirmed_msg, f"DELETE response did not confirm deletion: {detail!r}"
        assert gone, (
            f"Export still retrievable after delete: GET returned {verify_resp.status_code}"
        )
        logger.info(
            "[EX08] export_id=%s deleted and verified gone (GET → %s)",
            export_id, verify_resp.status_code,
        )
