"""
NCP Organization API — Functional Flow Tests

Covers the Organization endpoints (OR01 – ...). This suite groups all 7
Organization APIs together; steps are added as each endpoint spec is provided.

  ── OR01: LIST ORGANIZATIONS ────────────────────────────────────
  Step 1  GET /api/v1/organizations
          → list all organizations. Verify 200, the body is a JSON array, each
            organization carries the expected schema keys, "usernames" is a
            list, and the seeded 'default' org is present. The default org's id
            is captured on the class so later steps can reuse it.

  ── OR02: CREATE ORGANIZATION ───────────────────────────────────
  Step 2  POST /api/v1/organizations
          body: {name, description, usernames}
          → create a new organization. Verify 201, an id is returned, name +
            description echoed, is_active true. The new org's id is captured on
            the class so later steps (get / update / delete) can reuse it.

  ── OR03: UPDATE ORGANIZATION ───────────────────────────────────
  Step 3  PUT /api/v1/organizations/{org_id}
          body: {name, description, is_active}
          → update the org created in OR02. Verify 200, id unchanged, and the
            edited fields (name / description / is_active) echoed back.

  ── OR04: ASSIGN USERS TO ORGANIZATION ──────────────────────────
  Step 4  PATCH /api/v1/organizations/{org_id}/users
          body: {usernames}
          → assign users to the OR02-created org (replaces their current org
            assignment). Verify 200, "assigned" contains the requested
            usernames and "not_found" is empty (they exist).

  ── OR05: LIST ORGANIZATION USERS ───────────────────────────────
  Step 5  GET /api/v1/organizations/{org_id}/users
          → list users assigned to an org (read-only; uses the OR02-created
            org, else the config org id). Verify 200, the body is a JSON array
            and each user carries the expected schema keys.

  ── OR06: DEACTIVATE ORGANIZATION ───────────────────────────────
  Step 6  PATCH /api/v1/organizations/{org_id}/deactivate
          → soft-delete (deactivate) the OR02-created org. Verify 200 and a
            'detail' message confirming deactivation.

  ── OR07: DELETE ORGANIZATION ───────────────────────────────────
  Step 7  DELETE /api/v1/organizations/{org_id}
          → hard-delete the OR02-created org. Precondition: the endpoint 400s
            while users are attached, so this step FIRST reassigns the org's
            users back to the default org, THEN deletes. Verify 200 and that
            the org no longer appears in the list.

Flow (create → configure → teardown):
  OR01 list → OR02 create → OR03 update → OR04 assign users →
  OR05 list users → OR06 deactivate → OR07 reassign-to-default + delete

Test data:
  known org  : default  (expected in the returned list)
  create org : name=Microsoft-<ts>, description=Test
  update org : name=XBOX-<ts>, description=test-123, is_active=true
  assign     : usernames=[john]  (moved onto the disposable created org)
"""

import time
import pytest
import logging
import json

# Unique per-run suffix so create/update use fresh names (the API rejects
# duplicate org names with 400), keeping the suite re-runnable.
RUN_SUFFIX = str(int(time.time()))

from api_client import (
    list_organizations,
    create_organization,
    update_organization,
    assign_users_to_organization,
    get_organization_users,
    deactivate_organization,
    delete_organization,
    safe_json,
)
from config import (
    TEST_ORG_NAME,
    TEST_ORG_ID,
    DEFAULT_ORG_ID,
    TEST_ORG_CREATE_NAME,
    TEST_ORG_CREATE_DESCRIPTION,
    TEST_ORG_CREATE_USERNAMES,
    TEST_ORG_UPDATE_NAME,
    TEST_ORG_UPDATE_DESCRIPTION,
    TEST_ORG_UPDATE_IS_ACTIVE,
    TEST_ORG_ASSIGN_USERNAMES,
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
# ORGANIZATION FUNCTIONAL FLOW  (OR01 – ...)
# ════════════════════════════════════════════════════════════════

class TestOrganizationsFunctionalFlow:

    # Captured at runtime: known_org_id = the seeded 'default' org (OR01,
    # informational only); created_org_id = the org OR02 creates.
    #
    # IMPORTANT: mutating steps (update / delete) operate ONLY on
    # created_org_id and must NEVER fall back to the default org — clobbering
    # the seeded 'default' (id 1) is destructive. Those steps skip if OR02 did
    # not create an org. TEST_ORG_ID is a read-only fallback only.
    known_org_id   = None
    created_org_id = None

    @classmethod
    def _read_org_id(cls):
        """org id for READ-ONLY steps: the OR02-created org, else the config
        fallback (safe to read the default org)."""
        return cls.created_org_id if cls.created_org_id is not None else TEST_ORG_ID

    # ── Step 1: LIST ORGANIZATIONS ─────────────────────────────
    def test_or01_list_organizations(self, ncp_token, report_collector):
        resp = list_organizations(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        # Endpoint returns a bare JSON array of organizations.
        orgs = data if isinstance(data, list) else []
        is_list = isinstance(data, list)

        required_keys = ("id", "name", "description", "is_active",
                         "created_at", "user", "usernames")
        schema_ok = is_list and all(
            isinstance(o, dict) and all(k in o for k in required_keys)
            for o in orgs
        )
        usernames_ok = is_list and all(
            isinstance(o, dict) and isinstance(o.get("usernames"), list)
            for o in orgs
        )

        org_names   = [o.get("name") for o in orgs if isinstance(o, dict)]
        default_found = TEST_ORG_NAME in org_names

        # Capture the default org's id for later id-based steps.
        for o in orgs:
            if isinstance(o, dict) and o.get("name") == TEST_ORG_NAME:
                TestOrganizationsFunctionalFlow.known_org_id = o.get("id")
                break

        logger.info(
            "[OR01] GET /api/v1/organizations → %s (orgs=%d)",
            resp.status_code, len(orgs),
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  orgs returned   : {len(orgs)}\n"
            f"  body is a list  : {'YES (PASS)' if is_list else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  usernames lists : {'YES (PASS)' if usernames_ok else 'NO (FAIL)'}\n"
            f"  '{TEST_ORG_NAME}' present: {'YES (PASS)' if default_found else 'NO (FAIL)'}\n"
            f"\nOrg names       :\n  {org_names}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = (
                "GET list organizations — verify 200, body is a JSON array, each org "
                f"carries the schema keys, usernames is a list, '{TEST_ORG_NAME}' present"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/organizations",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and is_list and schema_ok and usernames_ok and default_found,
        )

        assert passed,       f"LIST organizations failed: expected 200, got {resp.status_code}"
        assert is_list,      "Response body is not a JSON array"
        assert schema_ok,    f"One or more organizations missing required keys {required_keys}"
        assert usernames_ok, "One or more organizations have a non-list 'usernames'"
        assert default_found, f"Known org '{TEST_ORG_NAME}' not present in the list"
        logger.info(
            "[OR01] %d organization(s) returned — '%s' present (id=%s)",
            len(orgs), TEST_ORG_NAME, TestOrganizationsFunctionalFlow.known_org_id,
        )

    # ── Step 2: CREATE ORGANIZATION ────────────────────────────
    def test_or02_create_organization(self, ncp_token, report_collector):
        # Unique name per run — the API rejects duplicate org names (400).
        name        = f"{TEST_ORG_CREATE_NAME}-{RUN_SUFFIX}"
        description = TEST_ORG_CREATE_DESCRIPTION
        usernames   = TEST_ORG_CREATE_USERNAMES

        resp = create_organization(
            name        = name,
            description = description,
            usernames   = usernames,
            token       = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 201
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[OR02] POST /api/v1/organizations → %s\n%s",
            resp.status_code, pretty,
        )

        org_id      = data.get("id") if isinstance(data, dict) else None
        name_match  = isinstance(data, dict) and data.get("name") == name
        desc_match  = isinstance(data, dict) and data.get("description") == description
        is_active   = isinstance(data, dict) and data.get("is_active") is True
        has_id      = org_id is not None

        # Capture for later steps regardless of the assertions below.
        if has_id:
            TestOrganizationsFunctionalFlow.created_org_id = org_id

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  name         : {name}\n"
            f"  description  : {description}\n"
            f"  usernames    : {usernames}\n"
            f"\nResult:\n"
            f"  id           : {org_id} {'✓' if has_id else '✗'}\n"
            f"  name match   : {'YES' if name_match else 'NO'}\n"
            f"  desc match   : {'YES' if desc_match else 'NO'}\n"
            f"  is_active    : {data.get('is_active') if isinstance(data, dict) else None} {'✓' if is_active else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = (
                f"POST create organization '{name}' — verify 201, id returned, name + "
                f"description echoed, is_active true"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/organizations",
            expected_status  = "201",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_id and name_match and desc_match and is_active,
        )

        assert passed,     f"CREATE organization failed: expected 201, got {resp.status_code}"
        assert has_id,     "Response missing 'id'"
        assert name_match, f"name mismatch: expected {name!r}, got {data.get('name')!r}"
        assert desc_match, f"description mismatch: expected {description!r}, got {data.get('description')!r}"
        assert is_active,  f"Expected is_active true, got {data.get('is_active')!r}"
        logger.info("[OR02] organization created — id=%s name=%r", org_id, name)

    # ── Step 3: UPDATE ORGANIZATION ────────────────────────────
    def test_or03_update_organization(self, ncp_token, report_collector):
        # Operate ONLY on the org OR02 created — never fall back to the
        # default org (mutating id 1 would clobber the seeded organization).
        org_id = TestOrganizationsFunctionalFlow.created_org_id
        if org_id is None:
            pytest.skip("OR02 did not create an org (no id captured) — "
                        "skipping update to avoid mutating a real/default org")

        new_name    = f"{TEST_ORG_UPDATE_NAME}-{RUN_SUFFIX}"
        new_desc    = TEST_ORG_UPDATE_DESCRIPTION
        is_active   = TEST_ORG_UPDATE_IS_ACTIVE

        resp = update_organization(
            org_id      = org_id,
            name        = new_name,
            description = new_desc,
            is_active   = is_active,
            token       = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[OR03] PUT /api/v1/organizations/%s → %s\n%s",
            org_id, resp.status_code, pretty,
        )

        # id path param may echo back as int; compare leniently.
        id_match       = isinstance(data, dict) and str(data.get("id")) == str(org_id)
        name_match     = isinstance(data, dict) and data.get("name") == new_name
        desc_match     = isinstance(data, dict) and data.get("description") == new_desc
        active_match   = isinstance(data, dict) and data.get("is_active") == is_active

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest (PUT):\n"
            f"  org_id       : {org_id}\n"
            f"  name         : {new_name}\n"
            f"  description  : {new_desc}\n"
            f"  is_active    : {is_active}\n"
            f"\nResult:\n"
            f"  id match     : {'YES' if id_match else 'NO'}\n"
            f"  name updated : {'YES' if name_match else 'NO'} (got {data.get('name') if isinstance(data, dict) else None!r})\n"
            f"  desc updated : {'YES' if desc_match else 'NO'}\n"
            f"  is_active    : {'YES' if active_match else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = (
                f"PUT update organization {org_id} (name/description/is_active) — verify 200, "
                f"id unchanged, edited fields echoed with new values"
            ),
            api_method       = "PUT",
            endpoint         = "/api/v1/organizations/{org_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and name_match and desc_match and active_match,
        )

        assert passed,       f"UPDATE organization failed: expected 200, got {resp.status_code}"
        assert id_match,     f"id changed: expected {org_id}, got {data.get('id')}"
        assert name_match,   f"name not updated: expected {new_name!r}, got {data.get('name')!r}"
        assert desc_match,   f"description not updated: expected {new_desc!r}, got {data.get('description')!r}"
        assert active_match, f"is_active mismatch: expected {is_active}, got {data.get('is_active')}"
        logger.info("[OR03] organization %s updated — name=%r", org_id, new_name)

    # ── Step 4: ASSIGN USERS TO ORGANIZATION ───────────────────
    def test_or04_assign_users_to_organization(self, ncp_token, report_collector):
        # Operate ONLY on the org OR02 created — assigning to the default org
        # would move real users off it (this endpoint replaces their org).
        org_id = TestOrganizationsFunctionalFlow.created_org_id
        if org_id is None:
            pytest.skip("OR02 did not create an org (no id captured) — "
                        "skipping user-assign to avoid mutating a real/default org")

        usernames = TEST_ORG_ASSIGN_USERNAMES

        resp = assign_users_to_organization(org_id, usernames, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[OR04] PATCH /api/v1/organizations/%s/users → %s\n%s",
            org_id, resp.status_code, pretty,
        )

        assigned  = data.get("assigned") if isinstance(data, dict) else None
        not_found = data.get("not_found") if isinstance(data, dict) else None

        keys_ok       = isinstance(assigned, list) and isinstance(not_found, list)
        all_assigned  = keys_ok and all(u in assigned for u in usernames)
        none_missing  = keys_ok and len(not_found) == 0

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  org_id       : {org_id}\n"
            f"  usernames    : {usernames}\n"
            f"\nResult:\n"
            f"  assigned     : {assigned}\n"
            f"  not_found    : {not_found}\n"
            f"  all assigned : {'YES' if all_assigned else 'NO'}\n"
            f"  none missing : {'YES' if none_missing else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 4,
            description      = (
                f"PATCH assign users {usernames} to organization {org_id} — verify 200, "
                f"'assigned' contains the requested usernames, 'not_found' is empty"
            ),
            api_method       = "PATCH",
            endpoint         = "/api/v1/organizations/{org_id}/users",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and keys_ok and all_assigned and none_missing,
        )

        assert passed,       f"ASSIGN users failed: expected 200, got {resp.status_code}"
        assert keys_ok,      "Response missing 'assigned'/'not_found' lists"
        assert all_assigned, f"Not all requested users assigned: requested={usernames}, assigned={assigned}"
        assert none_missing, f"Some users not found: {not_found}"
        logger.info("[OR04] users %s assigned to organization %s", assigned, org_id)

    # ── Step 5: LIST ORGANIZATION USERS ────────────────────────
    def test_or05_get_organization_users(self, ncp_token, report_collector):
        org_id = self._read_org_id()

        resp = get_organization_users(org_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        # Endpoint returns a bare JSON array of users.
        users = data if isinstance(data, list) else []
        is_list = isinstance(data, list)

        required_keys = ("id", "username", "firstname", "lastname", "email")
        schema_ok = is_list and all(
            isinstance(u, dict) and all(k in u for k in required_keys)
            for u in users
        )

        usernames = [u.get("username") for u in users if isinstance(u, dict)]

        logger.info(
            "[OR05] GET /api/v1/organizations/%s/users → %s (users=%d)",
            org_id, resp.status_code, len(users),
        )

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  org_id       : {org_id}\n"
            f"\nResult:\n"
            f"  users returned: {len(users)}\n"
            f"  body is a list: {'YES (PASS)' if is_list else 'NO (FAIL)'}\n"
            f"  schema keys ok: {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  usernames    : {usernames}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 5,
            description      = (
                f"GET organization {org_id} users — verify 200, body is a JSON array, "
                f"each user carries the expected schema keys"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/organizations/{org_id}/users",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and is_list and schema_ok,
        )

        assert passed,    f"LIST organization users failed: expected 200, got {resp.status_code}"
        assert is_list,   "Response body is not a JSON array"
        assert schema_ok, f"One or more users missing required keys {required_keys}"
        logger.info("[OR05] %d user(s) in organization %s", len(users), org_id)

    # ── Step 6: DEACTIVATE ORGANIZATION ────────────────────────
    def test_or06_deactivate_organization(self, ncp_token, report_collector):
        # Operate ONLY on the org OR02 created — deactivating the default org
        # would soft-delete the seeded organization.
        org_id = TestOrganizationsFunctionalFlow.created_org_id
        if org_id is None:
            pytest.skip("OR02 did not create an org (no id captured) — "
                        "skipping deactivate to avoid mutating a real/default org")

        resp = deactivate_organization(org_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[OR06] PATCH /api/v1/organizations/%s/deactivate → %s\n%s",
            org_id, resp.status_code, pretty,
        )

        detail        = data.get("detail") if isinstance(data, dict) else None
        has_detail    = bool(detail)
        confirms      = has_detail and "deactivat" in str(detail).lower()

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  org_id       : {org_id}\n"
            f"\nResult:\n"
            f"  detail       : {detail}\n"
            f"  confirms deactivation: {'YES (PASS)' if confirms else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 6,
            description      = (
                f"PATCH deactivate organization {org_id} — verify 200 and a 'detail' "
                f"message confirming deactivation"
            ),
            api_method       = "PATCH",
            endpoint         = "/api/v1/organizations/{org_id}/deactivate",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and confirms,
        )

        assert passed,   f"DEACTIVATE organization failed: expected 200, got {resp.status_code}"
        assert confirms, f"Expected a deactivation 'detail' message, got {detail!r}"
        logger.info("[OR06] organization %s deactivated", org_id)

    # ── Step 7: DELETE ORGANIZATION (reassign users first) ─────
    def test_or07_delete_organization(self, ncp_token, report_collector):
        # Operate ONLY on the org OR02 created.
        org_id = TestOrganizationsFunctionalFlow.created_org_id
        if org_id is None:
            pytest.skip("OR02 did not create an org (no id captured) — "
                        "skipping delete to avoid mutating a real/default org")

        # Precondition: hard-delete fails while users are attached. Reassign
        # any users on this org back to the DEFAULT org first.
        users_resp = get_organization_users(org_id, token=ncp_token)
        users_data = safe_json(users_resp)
        current_users = (
            [u.get("username") for u in users_data if isinstance(u, dict) and u.get("username")]
            if isinstance(users_data, list) else []
        )

        reassigned = []
        if current_users:
            r = assign_users_to_organization(DEFAULT_ORG_ID, current_users, token=ncp_token)
            rd = safe_json(r)
            reassigned = rd.get("assigned", []) if isinstance(rd, dict) else []
            logger.info(
                "[OR07] reassigned %s from org %s → default org %s (status %s)",
                current_users, org_id, DEFAULT_ORG_ID, r.status_code,
            )

        resp = delete_organization(org_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code in (200, 204)
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[OR07] DELETE /api/v1/organizations/%s → %s\n%s",
            org_id, resp.status_code, pretty,
        )

        # Confirm the org is gone from the list (soft verification).
        gone = None
        try:
            list_resp = list_organizations(ncp_token)
            list_data = safe_json(list_resp)
            ids = [o.get("id") for o in list_data if isinstance(o, dict)] \
                  if isinstance(list_data, list) else []
            gone = org_id not in ids
        except Exception as exc:  # pragma: no cover - verification best-effort
            logger.warning("[OR07] post-delete list check failed: %s", exc)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  org_id       : {org_id}\n"
            f"\nPre-delete reassign:\n"
            f"  users on org : {current_users}\n"
            f"  reassigned → default ({DEFAULT_ORG_ID}): {reassigned}\n"
            f"\nResult:\n"
            f"  delete status: {resp.status_code}\n"
            f"  org gone from list: {gone}\n"
            f"\nDelete Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 7,
            description      = (
                f"DELETE organization {org_id} — reassign attached users to the default "
                f"org first, then hard-delete; verify 200 and the org is gone"
            ),
            api_method       = "DELETE",
            endpoint         = "/api/v1/organizations/{org_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and (gone is True or gone is None),
        )

        assert passed, (
            f"DELETE organization failed: expected 200/204, got {resp.status_code} "
            f"(body: {data!r})"
        )
        if gone is False:
            raise AssertionError(f"Organization {org_id} still present after delete")
        logger.info("[OR07] organization %s deleted (gone=%s)", org_id, gone)
