"""
NCP Projects API — All Project-Related Functional Flow Tests

Covers 3 API groups in a single file:

  ── PROJECT APIs (F01–F06) ─────────────────────────────────────
  Step 1  CREATE project  → GET all (verify count+1, in list) → GET specific (verify fields)
  Step 2  UPDATE project  → GET specific (verify name changed)
  Step 3  DELETE project  → GET all (verify gone, count back to baseline)
  Step 4  ARCHIVE project → GET specific (verify is_archived=true)
  Step 5  UNARCHIVE project → GET specific (verify is_archived=false)
  Step 6  DOWNLOAD project  → verify ZIP contains project.json

  ── PROJECT MEMBER APIs (M01–M03) ──────────────────────────────
  Step 1  ADD member      → verify in member list + verify by GET specific
  Step 2  ADD AS ADMIN    → verify admin promotion via GET specific
  Step 3  DELETE member   → verify member gone from list

  ── PINNED PROJECT APIs (P01–P02) ──────────────────────────────
  Step 1  PIN project    → verify project appears in pinned list
  Step 2  UNPIN project  → verify project removed from pinned list

  ── USER PREFERENCES APIs (UP01–UP02) ──────────────────────────
  Step 1  CREATE preferences → GET verify (notifications match)
  Step 2  UPDATE preferences → GET verify (notifications updated)
"""

import pytest
import logging
import time
import json
import zipfile
import io

from api_client import (
    create_project,
    get_projects,
    get_project,
    update_project,
    delete_project,
    archive_project,
    unarchive_project,
    download_project,
    list_members,
    add_member,
    get_member,
    delete_member,
    add_member_as_admin,
    get_pinned_projects,
    pin_project,
    unpin_project,
    get_user_preferences,
    create_user_preferences,
    update_user_preferences,
    safe_json,
)
from config import TEST_MEMBER_USERNAME, NCP_USERNAME, TEST_USER_PREF_USER_ID

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
# PROJECT API TESTS  (F01 – F06)
# ════════════════════════════════════════════════════════════════

class TestProjectFunctionalFlow:

    # ── Step 1: CREATE & VERIFY ────────────────────────────────
    def test_f01_create_and_verify(self, ncp_token, report_collector, flow_state,
                                   _test_project_tracker):
        # --- baseline count (silent, setup only) ---
        all_projects = safe_json(get_projects(ncp_token))
        baseline = len(all_projects if isinstance(all_projects, list)
                       else all_projects.get("data", []))
        flow_state["baseline_count"] = baseline
        logger.info("[F01] Baseline count: %d", baseline)

        # --- CREATE ---
        name    = f"Flow-Test-{int(time.time())}"
        payload = {"name": name, "description": "Created by functional flow test",
                   "org_id": 0, "username": "superadmin"}
        resp = create_project(payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 1, "CREATE project",
            resp, "POST", "/api/v1/projects", (200, 201), prefix="F",
        )
        assert passed, f"CREATE failed: expected 200/201, got {code}"

        project_id = data.get("project_id")
        flow_state["created_id"]   = project_id
        flow_state["created_name"] = name
        if project_id:
            _test_project_tracker.append(project_id)

        # --- GET all → verify count +1 and project in list ---
        all_resp = get_projects(ncp_token)
        passed_all, all_data, all_code = _flow(
            report_collector, 1,
            f"GET all projects — verify count +1 and project_id={project_id} in list",
            all_resp, "GET", "/api/v1/projects", prefix="F",
        )
        assert passed_all, f"GET all projects failed: expected 200, got {all_code}"
        projects2   = all_data if isinstance(all_data, list) else all_data.get("data", [])
        ids_in_list = [p.get("project_id") for p in projects2]
        assert len(projects2) == baseline + 1, f"Expected count {baseline + 1}, got {len(projects2)}"
        assert project_id in ids_in_list, f"project_id={project_id} not found in list"

        # --- GET specific → verify fields ---
        get_resp = get_project(project_id, ncp_token)
        passed_get, get_data, get_code = _flow(
            report_collector, 1,
            f"GET specific project id={project_id} — verify project_id and name",
            get_resp, "GET", f"/api/v1/projects/{project_id}", prefix="F",
        )
        assert passed_get, f"GET specific failed: expected 200, got {get_code}"
        assert get_data.get("project_id") == project_id
        assert get_data.get("name")       == name
        logger.info("[F01] project_id=%s name='%s' verified", project_id, name)

    # ── Step 2: UPDATE & VERIFY ────────────────────────────────
    def test_f02_update_and_verify(self, ncp_token, report_collector, flow_state):
        project_id   = flow_state.get("created_id")
        updated_name = f"Flow-Updated-{int(time.time())}"
        payload      = {"name": updated_name, "description": "Updated by flow test", "org_id": 0}

        resp = update_project(project_id, payload, ncp_token)
        passed, data, code = _flow(
            report_collector, 2,
            f"UPDATE project id={project_id} — change name",
            resp, "PUT", f"/api/v1/projects/{project_id}", prefix="F",
        )
        assert passed, f"UPDATE failed: expected 200, got {code}"
        flow_state["updated_name"] = updated_name

        get_resp = get_project(project_id, ncp_token)
        passed_get, get_data, get_code = _flow(
            report_collector, 2,
            f"GET specific project id={project_id} — verify name update reflected",
            get_resp, "GET", f"/api/v1/projects/{project_id}", prefix="F",
        )
        assert passed_get, f"GET specific failed: expected 200, got {get_code}"
        assert get_data.get("name") == updated_name, \
            f"Update not reflected. Expected '{updated_name}', got '{get_data.get('name')}'"
        logger.info("[F02] project_id=%s name updated to '%s' and verified", project_id, updated_name)

    # ── Step 3: DELETE & VERIFY ────────────────────────────────
    def test_f03_delete_and_verify(self, ncp_token, report_collector, flow_state):
        project_id = flow_state.get("created_id")

        resp = delete_project(project_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 3,
            f"DELETE project id={project_id}",
            resp, "DELETE", f"/api/v1/projects/{project_id}", (200, 204), prefix="F",
        )
        assert passed, f"DELETE failed: expected 200/204, got {code}"

        all_resp = get_projects(ncp_token)
        passed_all, all_data, all_code = _flow(
            report_collector, 3,
            f"GET all projects — verify project_id={project_id} gone, count back to baseline",
            all_resp, "GET", "/api/v1/projects", prefix="F",
        )
        assert passed_all, f"GET all projects failed: expected 200, got {all_code}"
        projects = all_data if isinstance(all_data, list) else all_data.get("data", [])
        ids      = [p.get("project_id") for p in projects]
        assert project_id not in ids, f"Deleted project_id={project_id} still appears in list"
        assert len(projects) == flow_state["baseline_count"], \
            f"Expected count back to {flow_state['baseline_count']}, got {len(projects)}"
        logger.info("[F03] project_id=%s deleted and confirmed gone. Count=%d",
                    project_id, len(projects))

    # ── Step 4: ARCHIVE & VERIFY ───────────────────────────────
    def test_f04_archive_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = archive_project(baseline_project_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 4,
            f"ARCHIVE project id={baseline_project_id}",
            resp, "POST", f"/api/v1/projects/{baseline_project_id}/archive", (200, 204), prefix="F",
        )
        assert passed, f"ARCHIVE failed: expected 200/204, got {code}"

        get_resp = get_project(baseline_project_id, ncp_token)
        passed_get, get_data, get_code = _flow(
            report_collector, 4,
            f"GET specific project id={baseline_project_id} — verify is_archived=true",
            get_resp, "GET", f"/api/v1/projects/{baseline_project_id}", prefix="F",
        )
        assert passed_get, f"GET specific failed: expected 200, got {get_code}"
        assert get_data.get("is_archived") is True, \
            f"Expected is_archived=true, got {get_data.get('is_archived')}"
        logger.info("[F04] project_id=%s is_archived=True confirmed", baseline_project_id)

    # ── Step 5: UNARCHIVE & VERIFY ─────────────────────────────
    def test_f05_unarchive_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = unarchive_project(baseline_project_id, ncp_token)
        passed, data, code = _flow(
            report_collector, 5,
            f"UNARCHIVE project id={baseline_project_id}",
            resp, "POST", f"/api/v1/projects/{baseline_project_id}/unarchive", (200, 204), prefix="F",
        )
        assert passed, f"UNARCHIVE failed: expected 200/204, got {code}"

        get_resp = get_project(baseline_project_id, ncp_token)
        passed_get, get_data, get_code = _flow(
            report_collector, 5,
            f"GET specific project id={baseline_project_id} — verify is_archived=false",
            get_resp, "GET", f"/api/v1/projects/{baseline_project_id}", prefix="F",
        )
        assert passed_get, f"GET specific failed: expected 200, got {get_code}"
        assert get_data.get("is_archived") is False, \
            f"Expected is_archived=false, got {get_data.get('is_archived')}"
        logger.info("[F05] project_id=%s is_archived=False confirmed", baseline_project_id)

    # ── Step 6: DOWNLOAD & VERIFY ──────────────────────────────
    def test_f06_download_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = download_project(baseline_project_id, ncp_token)

        passed_status    = resp.status_code == 200
        content_type     = resp.headers.get("Content-Type", "(not set)")
        details          = [f"Content-Type: {content_type}"]
        zip_valid        = False
        has_project_json = False
        zip_names        = []

        if passed_status:
            try:
                zip_bytes = resp.content
                zf        = zipfile.ZipFile(io.BytesIO(zip_bytes))
                zip_valid = True
                zip_names = zf.namelist()
                details.append(f"ZIP contents: {zip_names}")
                has_project_json = "project.json" in zip_names
                if has_project_json:
                    inner = json.loads(zf.read("project.json"))
                    details.append("project.json:\n" + json.dumps(inner, indent=2, default=str))
                zip_path = f"project_{baseline_project_id}_export.zip"
                with open(zip_path, "wb") as f:
                    f.write(zip_bytes)
                details.append(f"Saved to: {zip_path}")
                logger.info("[F06] ZIP saved to disk: %s", zip_path)
            except Exception as exc:
                details.append(f"ZIP parse error: {exc}")

        passed  = passed_status and zip_valid and has_project_json
        summary = "\n".join(details)

        report_collector.add_flow(
            step             = 6,
            description      = f"DOWNLOAD project id={baseline_project_id} — verify ZIP contains project.json",
            api_method       = "GET",
            endpoint         = f"/api/v1/projects/{baseline_project_id}/download",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed,
        )
        logger.info("[F06] Download project_id=%s → %s\n%s",
                    baseline_project_id, resp.status_code, summary)
        assert passed_status,    f"Expected 200, got {resp.status_code}"
        assert zip_valid,        "Response is not a valid ZIP file"
        assert has_project_json, f"project.json not found in ZIP. Contents: {zip_names}"


# ════════════════════════════════════════════════════════════════
# PROJECT MEMBER API TESTS  (M01 – M03)
# ════════════════════════════════════════════════════════════════

MEMBER = TEST_MEMBER_USERNAME


class TestProjectMembersFunctionalFlow:

    # ── Step 1: ADD MEMBER & VERIFY ────────────────────────────
    def test_m01_add_member_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = add_member(baseline_project_id, MEMBER, ncp_token)
        passed, data, code = _flow(
            report_collector, 1,
            f"ADD member '{MEMBER}' to project id={baseline_project_id}",
            resp, "POST",
            f"/api/v1/project_members/projects/{baseline_project_id}/members",
            (200, 201), prefix="M",
        )
        assert passed, f"ADD member failed: expected 200/201, got {code}"

        list_resp = list_members(baseline_project_id, ncp_token)
        passed_list, list_data, list_code = _flow(
            report_collector, 1,
            f"GET list members — verify '{MEMBER}' appears in project id={baseline_project_id}",
            list_resp, "GET",
            f"/api/v1/project_members/projects/{baseline_project_id}/members",
            prefix="M",
        )
        assert passed_list, f"LIST members failed: expected 200, got {list_code}"
        members   = list_data if isinstance(list_data, list) else list_data.get("data", [])
        usernames = [m.get("username") for m in members]
        assert MEMBER in usernames, f"Member '{MEMBER}' not found in list. Got: {usernames}"
        logger.info("[M01] Member '%s' confirmed in list", MEMBER)

        get_resp = get_member(baseline_project_id, MEMBER, ncp_token)
        passed_get, get_data, get_code = _flow(
            report_collector, 1,
            f"GET specific member '{MEMBER}' — verify username and project_id",
            get_resp, "GET",
            f"/api/v1/project_members/projects/{baseline_project_id}/members/{MEMBER}",
            prefix="M",
        )
        assert passed_get, f"GET member failed: expected 200, got {get_code}"
        assert get_data.get("username") == MEMBER, \
            f"GET specific returned wrong username: {get_data.get('username')}"
        logger.info("[M01] GET specific member confirmed: %s", get_data)

    # ── Step 2: ADD AS ADMIN & VERIFY ──────────────────────────
    def test_m02_add_as_admin_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = add_member_as_admin(baseline_project_id, MEMBER, ncp_token)
        passed, data, code = _flow(
            report_collector, 2,
            f"ADD '{MEMBER}' AS ADMIN in project id={baseline_project_id}",
            resp, "POST",
            f"/api/v1/project_members/projects/{baseline_project_id}/members/{MEMBER}/admin",
            (200, 201), prefix="M",
        )
        assert passed, f"ADD AS ADMIN failed: expected 200/201, got {code}"

        get_resp = get_member(baseline_project_id, MEMBER, ncp_token)
        passed_get, get_data, get_code = _flow(
            report_collector, 2,
            f"GET specific member '{MEMBER}' — verify admin promotion reflected",
            get_resp, "GET",
            f"/api/v1/project_members/projects/{baseline_project_id}/members/{MEMBER}",
            prefix="M",
        )
        assert passed_get, f"GET member failed: expected 200, got {get_code}"
        is_admin = (
            get_data.get("is_admin")
            or get_data.get("role") in ("admin", "Admin", "ADMIN")
            or get_data.get("admin") is True
        )
        assert is_admin, f"Expected admin status for '{MEMBER}', got: {get_data}"
        logger.info("[M02] Admin promotion verified for '%s'", MEMBER)

    # ── Step 3: DELETE MEMBER & VERIFY ─────────────────────────
    def test_m03_delete_member_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = delete_member(baseline_project_id, MEMBER, ncp_token)
        passed, data, code = _flow(
            report_collector, 3,
            f"DELETE member '{MEMBER}' from project id={baseline_project_id}",
            resp, "DELETE",
            f"/api/v1/project_members/projects/{baseline_project_id}/members/{MEMBER}",
            (200, 204), prefix="M",
        )
        assert passed, f"DELETE member failed: expected 200/204, got {code}"

        list_resp = list_members(baseline_project_id, ncp_token)
        passed_list, list_data, list_code = _flow(
            report_collector, 3,
            f"GET list members — verify '{MEMBER}' is removed from project id={baseline_project_id}",
            list_resp, "GET",
            f"/api/v1/project_members/projects/{baseline_project_id}/members",
            prefix="M",
        )
        assert passed_list, f"LIST members failed: expected 200, got {list_code}"
        members   = list_data if isinstance(list_data, list) else list_data.get("data", [])
        usernames = [m.get("username") for m in members]
        assert MEMBER not in usernames, f"Deleted member '{MEMBER}' still appears in member list"
        logger.info("[M03] Member '%s' confirmed removed from project", MEMBER)


# ════════════════════════════════════════════════════════════════
# PINNED PROJECT API TESTS  (P01 – P02)
# ════════════════════════════════════════════════════════════════

class TestPinnedProjectsFunctionalFlow:

    # ── Step 1: PIN & VERIFY ───────────────────────────────────
    def test_p01_pin_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = pin_project(baseline_project_id, ncp_token)
        passed = resp.status_code in (200, 201, 204)
        pin_summary = (
            f"Status: {resp.status_code}\n"
            f"Result: Project id={baseline_project_id} pinned successfully"
            if passed else
            f"Status: {resp.status_code}\n"
            f"Result: PIN failed — {safe_json(resp)}"
        )
        logger.info("[P01] PUT /api/v1/user/pinned/projects/%s → %s", baseline_project_id, resp.status_code)
        report_collector.add_flow(
            step             = 1,
            description      = f"PIN project id={baseline_project_id}",
            api_method       = "PUT",
            endpoint         = f"/api/v1/user/pinned/projects/{baseline_project_id}",
            expected_status  = "200/201/204",
            actual_status    = resp.status_code,
            response_summary = pin_summary,
            passed           = passed,
        )
        assert passed, f"PIN project failed: expected 200/201/204, got {resp.status_code}"

        list_resp = get_pinned_projects(ncp_token)
        passed_list, list_data, list_code = _flow(
            report_collector, 1,
            f"GET pinned projects — verify project id={baseline_project_id} is pinned",
            list_resp, "GET", "/api/v1/user/pinned/projects", prefix="P",
        )
        assert passed_list, f"GET pinned projects failed: expected 200, got {list_code}"
        pinned  = list_data if isinstance(list_data, list) else list_data.get("data", [])
        pin_ids = [p.get("project_id") for p in pinned]
        assert baseline_project_id in pin_ids, \
            f"project_id={baseline_project_id} not found in pinned list. Got: {pin_ids}"
        logger.info("[P01] project_id=%s confirmed in pinned list", baseline_project_id)

    # ── Step 2: UNPIN & VERIFY ─────────────────────────────────
    def test_p02_unpin_and_verify(self, ncp_token, report_collector, baseline_project_id):
        resp = unpin_project(baseline_project_id, ncp_token)
        passed = resp.status_code in (200, 204)
        unpin_summary = (
            f"Status: {resp.status_code}\n"
            f"Result: Project id={baseline_project_id} unpinned successfully"
            if passed else
            f"Status: {resp.status_code}\n"
            f"Result: UNPIN failed — {safe_json(resp)}"
        )
        logger.info("[P02] DELETE /api/v1/user/pinned/projects/%s → %s", baseline_project_id, resp.status_code)
        report_collector.add_flow(
            step             = 2,
            description      = f"UNPIN project id={baseline_project_id}",
            api_method       = "DELETE",
            endpoint         = f"/api/v1/user/pinned/projects/{baseline_project_id}",
            expected_status  = "200/204",
            actual_status    = resp.status_code,
            response_summary = unpin_summary,
            passed           = passed,
        )
        assert passed, f"UNPIN project failed: expected 200/204, got {resp.status_code}"

        list_resp = get_pinned_projects(ncp_token)
        list_data = safe_json(list_resp)
        pinned    = list_data if isinstance(list_data, list) else list_data.get("data", [])
        pin_ids   = [p.get("project_id") for p in pinned]
        verified  = baseline_project_id not in pin_ids

        get_summary = (
            f"Status: {list_resp.status_code}\n"
            f"Total pinned projects: {len(pinned)}\n"
            f"project_id={baseline_project_id} in list: {baseline_project_id in pin_ids}\n"
            f"Verification: {'PASS — project successfully removed from pinned list' if verified else 'FAIL — project still in pinned list'}\n"
            f"Current pinned list:\n{json.dumps(pinned, indent=2, default=str)}"
        )
        logger.info("[P02] GET pinned projects → %s\n%s", list_resp.status_code, get_summary)
        report_collector.add_flow(
            step             = 2,
            description      = f"GET pinned projects — verify project id={baseline_project_id} is removed",
            api_method       = "GET",
            endpoint         = "/api/v1/user/pinned/projects",
            expected_status  = "200",
            actual_status    = list_resp.status_code,
            response_summary = get_summary,
            passed           = list_resp.status_code == 200 and verified,
        )
        assert list_resp.status_code == 200, f"GET pinned projects failed: {list_resp.status_code}"
        assert verified, f"project_id={baseline_project_id} still appears in pinned list after unpin"
        logger.info("[P02] project_id=%s confirmed removed from pinned list", baseline_project_id)


# ════════════════════════════════════════════════════════════════
# USER PREFERENCES API TESTS  (UP01 – UP02)
# ════════════════════════════════════════════════════════════════

USER_ID             = TEST_USER_PREF_USER_ID
NOTIF_CREATE        = ["automated-test-notification"]
NOTIF_UPDATE        = ["automated-test-notification-updated"]


class TestUserPreferencesFunctionalFlow:

    # ── Step 1: CREATE & VERIFY ────────────────────────────────
    def test_up01_create_and_verify(self, ncp_token, report_collector):

        # --- POST create user preferences ---
        resp = create_user_preferences(USER_ID, NOTIF_CREATE, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code in (200, 201, 400)
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[UP01] POST /api/v1/user_preferences → %s\n%s", resp.status_code, pretty)

        if resp.status_code in (200, 201):
            result_msg = "User preferences created successfully."
        elif resp.status_code == 400:
            reason = data.get("message") or data.get("detail") or "Already exists"
            result_msg = f"Preferences already exist for user_id={USER_ID} — API responded as expected.\nServer message: \"{reason}\""
        else:
            result_msg = "Unexpected response."

        create_summary = (
            f"Status        : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"Payload sent  : {{\"user_id\": \"{USER_ID}\", \"notifications\": {NOTIF_CREATE}}}\n"
            f"Result        : {result_msg}\n"
            f"Full Response :\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"POST create user preferences for user_id={USER_ID} — 200/201=created, 400=already exists (both valid)",
            api_method       = "POST",
            endpoint         = "/api/v1/user_preferences",
            expected_status  = "200/201/400",
            actual_status    = resp.status_code,
            response_summary = create_summary,
            passed           = passed,
        )
        assert passed, f"CREATE user preferences failed: expected 200/201/400, got {resp.status_code}"

        # --- PUT to set known state (NOTIF_CREATE) so GET verification is meaningful ---
        # (needed because POST returns 400 when prefs already exist from a prior run)
        set_resp = update_user_preferences(USER_ID, NOTIF_CREATE, ncp_token)
        set_data = safe_json(set_resp)
        passed_set = set_resp.status_code == 200
        set_pretty = json.dumps(set_data, indent=2, default=str)

        logger.info("[UP01] PUT /api/v1/user_preferences/%s (set known state) → %s\n%s",
                    USER_ID, set_resp.status_code, set_pretty)

        set_summary = (
            f"Status        : {set_resp.status_code} ({'PASS' if passed_set else 'FAIL'})\n"
            f"Payload sent  : {{\"notifications\": {NOTIF_CREATE}}}\n"
            f"Result        : {'Preferences set to known state for verification.' if passed_set else 'Failed to set known state.'}\n"
            f"Full Response :\n{set_pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"PUT set user preferences to known state — user_id={USER_ID}, notifications={NOTIF_CREATE}",
            api_method       = "PUT",
            endpoint         = f"/api/v1/user_preferences/{USER_ID}",
            expected_status  = "200",
            actual_status    = set_resp.status_code,
            response_summary = set_summary,
            passed           = passed_set,
        )
        assert passed_set, f"SET known state failed: expected 200, got {set_resp.status_code}"

        # --- GET → verify notifications match NOTIF_CREATE ---
        get_resp = get_user_preferences(USER_ID, ncp_token)
        get_data = safe_json(get_resp)
        passed_get = get_resp.status_code == 200
        get_pretty = json.dumps(get_data, indent=2, default=str)

        logger.info("[UP01] GET /api/v1/user_preferences?user_id=%s → %s\n%s",
                    USER_ID, get_resp.status_code, get_pretty)

        stored_notifs  = get_data.get("notifications", [])
        notif_verified = stored_notifs == NOTIF_CREATE

        get_summary = (
            f"Status               : {get_resp.status_code} ({'PASS' if passed_get else 'FAIL'})\n"
            f"user_id              : {get_data.get('user_id', 'N/A')}\n"
            f"Expected notifications: {NOTIF_CREATE}\n"
            f"Stored  notifications: {stored_notifs}\n"
            f"Notifications match  : {'YES — preferences verified (PASS)' if notif_verified else 'NO — mismatch (FAIL)'}\n"
            f"Full Response        :\n{get_pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"GET user preferences for user_id={USER_ID} — verify notifications={NOTIF_CREATE}",
            api_method       = "GET",
            endpoint         = f"/api/v1/user_preferences?user_id={USER_ID}",
            expected_status  = "200",
            actual_status    = get_resp.status_code,
            response_summary = get_summary,
            passed           = passed_get and notif_verified,
        )
        assert passed_get, f"GET user preferences failed: expected 200, got {get_resp.status_code}"
        assert notif_verified, f"Mismatch. Expected {NOTIF_CREATE}, got {stored_notifs}"
        logger.info("[UP01] Verified: user_id=%s notifications=%s", USER_ID, stored_notifs)

    # ── Step 2: UPDATE & VERIFY ────────────────────────────────
    def test_up02_update_and_verify(self, ncp_token, report_collector):

        # --- PUT update user preferences ---
        resp = update_user_preferences(USER_ID, NOTIF_UPDATE, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[UP02] PUT /api/v1/user_preferences/%s → %s\n%s",
                    USER_ID, resp.status_code, pretty)

        update_summary = (
            f"Status        : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"Payload sent  : {{\"notifications\": {NOTIF_UPDATE}}}\n"
            f"Result        : {'User preferences updated successfully.' if passed else 'Update failed.'}\n"
            f"Full Response :\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"PUT update user preferences for user_id={USER_ID}",
            api_method       = "PUT",
            endpoint         = f"/api/v1/user_preferences/{USER_ID}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = update_summary,
            passed           = passed,
        )
        assert passed, f"UPDATE user preferences failed: expected 200, got {resp.status_code}"

        # --- GET → verify notifications reflect the update ---
        get_resp = get_user_preferences(USER_ID, ncp_token)
        get_data = safe_json(get_resp)
        passed_get = get_resp.status_code == 200
        get_pretty = json.dumps(get_data, indent=2, default=str)

        logger.info("[UP02] GET /api/v1/user_preferences?user_id=%s → %s\n%s",
                    USER_ID, get_resp.status_code, get_pretty)

        stored_notifs  = get_data.get("notifications", [])
        notif_verified = stored_notifs == NOTIF_UPDATE

        get_summary = (
            f"Status              : {get_resp.status_code} ({'PASS' if passed_get else 'FAIL'})\n"
            f"user_id             : {get_data.get('user_id', 'N/A')}\n"
            f"Expected notifications: {NOTIF_UPDATE}\n"
            f"Stored  notifications: {stored_notifs}\n"
            f"Notifications match : {'YES — update reflected correctly (PASS)' if notif_verified else 'NO — update not reflected (FAIL)'}\n"
            f"Full Response       :\n{get_pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"GET user preferences for user_id={USER_ID} — verify notifications reflect update",
            api_method       = "GET",
            endpoint         = f"/api/v1/user_preferences?user_id={USER_ID}",
            expected_status  = "200",
            actual_status    = get_resp.status_code,
            response_summary = get_summary,
            passed           = passed_get and notif_verified,
        )
        assert passed_get, f"GET user preferences failed: expected 200, got {get_resp.status_code}"
        assert notif_verified, \
            f"Update not reflected. Expected {NOTIF_UPDATE}, got {stored_notifs}"
        logger.info("[UP02] Update verified: user_id=%s notifications=%s",
                    USER_ID, stored_notifs)
