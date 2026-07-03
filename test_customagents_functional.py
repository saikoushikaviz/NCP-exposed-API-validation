"""
NCP Custom Agents API — Functional Flow Tests

Covers the Custom Agents endpoints (CA01 – ...). This suite groups all 19
Custom Agents APIs together; steps are added as each endpoint spec is provided.

  ── CA01: ONBOARD CUSTOM AGENT ──────────────────────────────────
  Step 1  POST /api/v1/custom_agents/onboard   (multipart/form-data)
          file: .ncp package (tar.gz); optional ?update=<agent_name>
          → onboard a custom agent from a .ncp package (admin-only). Agents
            go directly to ACTIVE status. Verify 200, a success message,
            agent_id returned, agent_name echoed, and status == "ACTIVE".
            The agent_id / agent_name are captured on the class so later
            steps can reuse them.

  ── CA02: LIST CUSTOM AGENTS ────────────────────────────────────
  Step 2  GET /api/v1/custom_agents/list
          → list all custom agents (admin-only). Verify 200, "agents" list +
            "total" present, total matches count, each agent carries the
            expected schema keys, and (if CA01 ran) the onboarded agent is in
            the list.

  ── CA03: LIST BACKGROUND-ELIGIBLE AGENTS ───────────────────────
  Step 3  GET /api/v1/custom_agents/background-eligible
          → list custom agents eligible for background scheduling (every
            active agent). Verify 200, "agents" list + "total" present, total
            matches count, schema keys present, and every returned agent has
            status == "ACTIVE".

  ── CA04: GET CUSTOM AGENT ──────────────────────────────────────
  Step 4  GET /api/v1/custom_agents/{agent_name}
          → get details of a single custom agent (admin-only). Verify 200, the
            returned name matches the requested agent, and the payload carries
            the expected schema keys.

  ── CA05: DISABLE CUSTOM AGENT ──────────────────────────────────
  Step 5  POST /api/v1/custom_agents/{agent_name}/disable
          → disable a custom agent (admin-only); disabled agents are not
            loaded into the orchestrator. Verify 200, agent_name matches,
            status == "DISABLED", and a message is returned.

  ── CA06: ENABLE CUSTOM AGENT ───────────────────────────────────
  Step 6  POST /api/v1/custom_agents/{agent_name}/enable
          → enable a disabled custom agent (admin-only). Runs after CA05 so it
            re-activates the agent. Verify 200, agent_name matches, status ==
            "ACTIVE", and a message is returned.

  ── CA07: ENABLE CUSTOM AGENT BACKGROUND ────────────────────────
  Step 7  POST /api/v1/custom_agents/{agent_name}/enable-background
          → allow a custom agent to be scheduled as a background job (admin-
            only). Verify 200, agent_name matches, supports_background is true,
            and a message is returned.

  ── CA08: DISABLE CUSTOM AGENT BACKGROUND ───────────────────────
  Step 8  POST /api/v1/custom_agents/{agent_name}/disable-background
          → revoke a custom agent's background-scheduling eligibility (admin-
            only). Runs after CA07. Verify 200, agent_name matches,
            supports_background is false, and a message is returned.

  ── CA09: ADMIN LIST CUSTOM AGENTS ──────────────────────────────
  Step 9  GET /api/v1/custom_agents/admin/list
          → list all custom agents for admin (ACTIVE / PENDING / REJECTED).
            Verify 200, "agents" list + "total" present, total matches count,
            each agent carries the admin schema keys (incl. assigned_roles as
            a list, status_changed_by/at, submitted_at).

  ── CA10: GET MY CUSTOM AGENTS ──────────────────────────────────
  Step 10 GET /api/v1/custom_agents/user/my-agent
          → custom agents submitted by the authenticated user. Verify 200,
            "agents" list + "total" present, total matches count, schema keys
            present, and every returned agent was submitted_by the caller.

  ── CA11: SUBMIT CUSTOM AGENT ───────────────────────────────────
  Step 11 POST /api/v1/custom_agents/user/submit   (multipart/form-data)
          file: .ncp package (tar.gz)
          → upload/submit a new custom agent (role-aware). Admin → auto-ACTIVE,
            regular user → PENDING. Verify 200, a success message, agent_id
            returned, agent_name echoed, and status is ACTIVE or PENDING.

  ── CA12: UPDATE CUSTOM AGENT (NEW VERSION) ─────────────────────
  Step 12 POST /api/v1/custom_agents/{agent_id}/version   (multipart/form-data)
          file: .ncp package (tar.gz)
          → upload a new version of an existing agent. Verify 200, agent_id
            matches, agent_name echoed, a version string is returned, and
            status is ACTIVE or PENDING.

  ── CA13: APPROVE CUSTOM AGENT ──────────────────────────────────
  Step 13 POST /api/v1/custom_agents/{agent_id}/approve
          → approve a custom agent (admin-only); extracts it to the runtime
            directory. Verify 200, agent_name matches, status == "ACTIVE",
            and a message is returned.

  ── CA14: DECLINE CUSTOM AGENT ──────────────────────────────────
  Step 14 POST /api/v1/custom_agents/{agent_id}/decline
          body: {feedback}
          → decline a custom agent (admin-only) with feedback. Verify 200,
            agent_name matches, status == "REJECTED", and a message is returned.

  ── CA15: FEEDBACK CUSTOM AGENT ─────────────────────────────────
  Step 15 POST /api/v1/custom_agents/{agent_id}/feedback
          body: {message, feedback_type}
          → submit feedback for a custom agent (admin-only). Verify 200,
            agent_name matches, and a confirmation message is returned.

  ── CA16: DOWNLOAD CUSTOM AGENT ─────────────────────────────────
  Step 16 GET /api/v1/custom_agents/{agent_id}/download
          → download the agent's .ncp package (admin and owner). Verify 200,
            a Content-Disposition attachment header with a .ncp filename, and
            non-empty package bytes received.

  ── CA17: CAN SUBMIT CUSTOM AGENT ───────────────────────────────
  Step 17 GET /api/v1/custom_agents/user/can-submit-agent
          → whether the caller can submit a new agent. Verify 200,
            "submitAgent" present as a bool matching the expected value for
            the test role (admin → true).

  ── CA18: REMOVE (DELETE) CUSTOM AGENT ──────────────────────────
  Step 18 DELETE /api/v1/custom_agents/{agent_name}
          → remove a custom agent (admin-only). Verify 200, agent_name matches,
            and a removal-confirmation message is returned.

  ── CA19: REMOVE (DELETE) USER CUSTOM AGENT ─────────────────────
  Step 19 DELETE /api/v1/custom_agents/user/{agent_name}?allow_force_delete=
          → remove a custom agent (user-scoped, force-delete). Since CA18
            already deleted the shared agent, this step FIRST re-onboards it as
            setup, then force-deletes. Verify 200, agent_name matches, and a
            removal-confirmation message is returned.

File used:
  calculator-agent.ncp  (must be in the same folder as the test files)
"""

import os
import pytest
import logging
import json

from api_client import (
    onboard_custom_agent,
    list_custom_agents,
    list_background_eligible_agents,
    get_custom_agent,
    disable_custom_agent,
    enable_custom_agent,
    enable_custom_agent_background,
    disable_custom_agent_background,
    admin_list_custom_agents,
    get_my_custom_agents,
    submit_custom_agent,
    update_custom_agent_version,
    approve_custom_agent,
    decline_custom_agent,
    submit_custom_agent_feedback,
    download_custom_agent,
    can_submit_custom_agent,
    remove_custom_agent,
    remove_user_custom_agent,
    safe_json,
)
from config import (
    TEST_CA_PACKAGE_FILENAME,
    TEST_CA_AGENT_NAME,
    TEST_CA_AGENT_ID,
    TEST_CA_VERSION_SUBDIR,
    TEST_CA_DECLINE_FEEDBACK,
    TEST_CA_FEEDBACK_MESSAGE,
    TEST_CA_FEEDBACK_TYPE,
    TEST_CA_CAN_SUBMIT_EXPECTED,
    TEST_CA_ALLOW_FORCE_DELETE,
    NCP_USERNAME,
)

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(__file__)

# Base .ncp package (older version) — used by CA01 onboard + CA11 submit.
# Must be in the same directory as the test files.
ONBOARD_PACKAGE_PATH = os.path.join(_HERE, TEST_CA_PACKAGE_FILENAME)

# Bumped-version .ncp package — used by CA12 (version upload). Same filename
# (the platform keys on the agent name inside the package, so it must NOT be
# renamed) but a HIGHER version in its toml. Kept in a separate subfolder so it
# can coexist with the base package that shares its name.
VERSION_PACKAGE_PATH = os.path.join(_HERE, TEST_CA_VERSION_SUBDIR, TEST_CA_PACKAGE_FILENAME)


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
# CUSTOM AGENTS FUNCTIONAL FLOW  (CA01 – ...)
# ════════════════════════════════════════════════════════════════

class TestCustomAgentsFunctionalFlow:

    # Captured at runtime by CA01 (onboard) so later steps
    # (get / update / delete / ...) can operate on a real agent.
    created_agent_id   = None
    created_agent_name = None

    @classmethod
    def _target_agent_name(cls):
        """agent_name to operate on: the one CA01 onboarded, else the config default."""
        return cls.created_agent_name or TEST_CA_AGENT_NAME

    @classmethod
    def _target_agent_id(cls):
        """agent_id to operate on: the one CA01/CA02 captured, else the config fallback."""
        return cls.created_agent_id if cls.created_agent_id is not None else TEST_CA_AGENT_ID

    # ── Step 1: ONBOARD CUSTOM AGENT ───────────────────────────
    def test_ca01_onboard_custom_agent(self, ncp_token, report_collector):
        # Guard: confirm the .ncp package exists before attempting upload.
        assert os.path.isfile(ONBOARD_PACKAGE_PATH), (
            f"Onboard package not found at: {ONBOARD_PACKAGE_PATH}\n"
            f"Place '{TEST_CA_PACKAGE_FILENAME}' in the same folder as the test files."
        )

        # Note: if the agent already exists, re-run with update=TEST_CA_AGENT_NAME
        # to update it in place instead of failing on a duplicate name.
        resp = onboard_custom_agent(ONBOARD_PACKAGE_PATH, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA01] POST /api/v1/custom_agents/onboard → %s\n%s",
            resp.status_code, pretty,
        )

        agent_id   = data.get("agent_id") if isinstance(data, dict) else None
        agent_name = data.get("agent_name") if isinstance(data, dict) else None
        status     = data.get("status") if isinstance(data, dict) else None
        message    = data.get("message") if isinstance(data, dict) else None

        # Capture for later steps regardless of the assertions below.
        if agent_id is not None:
            TestCustomAgentsFunctionalFlow.created_agent_id = agent_id
        if agent_name:
            TestCustomAgentsFunctionalFlow.created_agent_name = agent_name

        has_agent_id  = agent_id is not None
        name_match    = agent_name == TEST_CA_AGENT_NAME
        status_active = status == "ACTIVE"
        has_message   = bool(message)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  file         : {TEST_CA_PACKAGE_FILENAME}\n"
            f"\nResult:\n"
            f"  message      : {message}\n"
            f"  agent_id     : {agent_id} {'✓' if has_agent_id else '✗'}\n"
            f"  agent_name   : {agent_name} {'✓' if name_match else '✗'}\n"
            f"  status       : {status} {'✓ (ACTIVE)' if status_active else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = (
                f"POST onboard custom agent from '{TEST_CA_PACKAGE_FILENAME}' — verify 200, "
                f"success message, agent_id returned, agent_name='{TEST_CA_AGENT_NAME}', "
                f"status='ACTIVE'"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/onboard",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_agent_id and name_match and status_active and has_message,
        )

        assert passed,        f"ONBOARD custom agent failed: expected 200, got {resp.status_code}"
        assert has_agent_id,  "Response missing 'agent_id'"
        assert name_match,    f"agent_name mismatch: expected {TEST_CA_AGENT_NAME!r}, got {agent_name!r}"
        assert status_active, f"Expected status='ACTIVE', got {status!r}"
        assert has_message,   "Response missing 'message'"
        logger.info(
            "[CA01] custom agent onboarded — agent_id=%s name=%r status=%s",
            agent_id, agent_name, status,
        )

    # ── Step 2: LIST CUSTOM AGENTS ─────────────────────────────
    def test_ca02_list_custom_agents(self, ncp_token, report_collector):
        resp = list_custom_agents(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        agents = data.get("agents", []) if isinstance(data, dict) else []
        total  = data.get("total") if isinstance(data, dict) else None

        agents_is_list = isinstance(agents, list)
        total_matches  = total == len(agents) if agents_is_list else False

        required_keys = (
            "agent_id", "name", "description", "status", "version",
            "submitted_by", "created_at", "updated_at", "supports_background",
        )
        schema_ok = agents_is_list and all(
            isinstance(a, dict) and all(k in a for k in required_keys)
            for a in agents
        )

        # If CA01 ran, its agent should be listed. Also backfill the class
        # agent_id from the catalog when running CA02 without CA01.
        agent_names = [a.get("name") for a in agents if isinstance(a, dict)]
        target_found = TEST_CA_AGENT_NAME in agent_names
        if TestCustomAgentsFunctionalFlow.created_agent_id is None:
            for a in agents:
                if isinstance(a, dict) and a.get("name") == TEST_CA_AGENT_NAME:
                    TestCustomAgentsFunctionalFlow.created_agent_id   = a.get("agent_id")
                    TestCustomAgentsFunctionalFlow.created_agent_name = a.get("name")
                    break

        logger.info(
            "[CA02] GET /api/v1/custom_agents/list → %s (agents=%d, total=%s)",
            resp.status_code, len(agents), total,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  agents returned : {len(agents)}\n"
            f"  total field     : {total}\n"
            f"  total==count    : {'YES (PASS)' if total_matches else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  '{TEST_CA_AGENT_NAME}' present: "
            f"{'YES (PASS)' if target_found else 'NO'}\n"
            f"\nAgent names     :\n  {agent_names}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = (
                "GET list custom agents — verify 200, agents+total present, total "
                "matches count, each agent carries the expected schema keys"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/custom_agents/list",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and agents_is_list and total_matches and schema_ok,
        )

        assert passed,        f"LIST custom agents failed: expected 200, got {resp.status_code}"
        assert agents_is_list, "Response 'agents' is missing or not a list"
        assert total_matches, f"'total' ({total}) does not match agent count ({len(agents)})"
        assert schema_ok,     f"One or more agents missing required keys {required_keys}"
        logger.info(
            "[CA02] %d custom agent(s) returned — total=%s", len(agents), total,
        )

    # ── Step 3: LIST BACKGROUND-ELIGIBLE AGENTS ────────────────
    def test_ca03_list_background_eligible_agents(self, ncp_token, report_collector):
        resp = list_background_eligible_agents(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        agents = data.get("agents", []) if isinstance(data, dict) else []
        total  = data.get("total") if isinstance(data, dict) else None

        agents_is_list = isinstance(agents, list)
        total_matches  = total == len(agents) if agents_is_list else False

        required_keys = (
            "agent_id", "name", "description", "status", "version",
            "submitted_by", "created_at", "updated_at", "supports_background",
        )
        schema_ok = agents_is_list and all(
            isinstance(a, dict) and all(k in a for k in required_keys)
            for a in agents
        )

        # Eligibility == active: every returned agent must be ACTIVE.
        all_active = agents_is_list and all(
            isinstance(a, dict) and a.get("status") == "ACTIVE" for a in agents
        )

        agent_names = [a.get("name") for a in agents if isinstance(a, dict)]

        logger.info(
            "[CA03] GET /api/v1/custom_agents/background-eligible → %s (agents=%d, total=%s)",
            resp.status_code, len(agents), total,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  agents returned : {len(agents)}\n"
            f"  total field     : {total}\n"
            f"  total==count    : {'YES (PASS)' if total_matches else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  all ACTIVE      : {'YES (PASS)' if all_active else 'NO (FAIL)'}\n"
            f"\nAgent names     :\n  {agent_names}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = (
                "GET background-eligible custom agents — verify 200, agents+total "
                "present, total matches count, schema keys present, all agents ACTIVE"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/custom_agents/background-eligible",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and agents_is_list and total_matches and schema_ok and all_active,
        )

        assert passed,        f"LIST background-eligible failed: expected 200, got {resp.status_code}"
        assert agents_is_list, "Response 'agents' is missing or not a list"
        assert total_matches, f"'total' ({total}) does not match agent count ({len(agents)})"
        assert schema_ok,     f"One or more agents missing required keys {required_keys}"
        assert all_active,    "One or more background-eligible agents are not ACTIVE"
        logger.info(
            "[CA03] %d background-eligible agent(s) — all ACTIVE", len(agents),
        )

    # ── Step 4: GET CUSTOM AGENT ───────────────────────────────
    def test_ca04_get_custom_agent(self, ncp_token, report_collector):
        agent_name = self._target_agent_name()

        resp = get_custom_agent(agent_name, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA04] GET /api/v1/custom_agents/%s → %s\n%s",
            agent_name, resp.status_code, pretty,
        )

        name_match = isinstance(data, dict) and data.get("name") == agent_name

        required_keys = (
            "agent_id", "name", "description", "status", "version",
            "submitted_by", "created_at", "updated_at", "supports_background",
        )
        schema_ok = isinstance(data, dict) and all(k in data for k in required_keys)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name   : {agent_name}\n"
            f"\nResult:\n"
            f"  name match   : {'YES (PASS)' if name_match else 'NO (FAIL)'}\n"
            f"  schema keys  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  agent_id     : {data.get('agent_id') if isinstance(data, dict) else None}\n"
            f"  status       : {data.get('status') if isinstance(data, dict) else None}\n"
            f"  version      : {data.get('version') if isinstance(data, dict) else None}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 4,
            description      = (
                f"GET custom agent '{agent_name}' — verify 200, returned name matches "
                f"the requested agent, and payload carries the expected schema keys"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/custom_agents/{agent_name}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and schema_ok,
        )

        assert passed,     f"GET custom agent failed: expected 200, got {resp.status_code}"
        assert name_match, f"Returned name mismatch: expected {agent_name!r}, got {data.get('name')!r}"
        assert schema_ok,  f"Agent payload missing required keys {required_keys}"
        logger.info(
            "[CA04] fetched custom agent %r — status=%s",
            agent_name, data.get("status"),
        )

    # ── Step 5: DISABLE CUSTOM AGENT ───────────────────────────
    def test_ca05_disable_custom_agent(self, ncp_token, report_collector):
        agent_name = self._target_agent_name()

        resp = disable_custom_agent(agent_name, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA05] POST /api/v1/custom_agents/%s/disable → %s\n%s",
            agent_name, resp.status_code, pretty,
        )

        name_match       = isinstance(data, dict) and data.get("agent_name") == agent_name
        status_disabled  = isinstance(data, dict) and data.get("status") == "DISABLED"
        message          = data.get("message") if isinstance(data, dict) else None
        has_message      = bool(message)

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name    : {agent_name}\n"
            f"\nResult:\n"
            f"  message       : {message}\n"
            f"  agent_name    : {'YES (PASS)' if name_match else 'NO (FAIL)'}\n"
            f"  status=DISABLED: {'YES (PASS)' if status_disabled else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 5,
            description      = (
                f"POST disable custom agent '{agent_name}' — verify 200, agent_name "
                f"matches, status='DISABLED', message returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_name}/disable",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and status_disabled and has_message,
        )

        assert passed,          f"DISABLE custom agent failed: expected 200, got {resp.status_code}"
        assert name_match,      f"agent_name mismatch: expected {agent_name!r}, got {data.get('agent_name')!r}"
        assert status_disabled, f"Expected status='DISABLED', got {data.get('status')!r}"
        assert has_message,     "Response missing 'message'"
        logger.info("[CA05] custom agent %r disabled", agent_name)

    # ── Step 6: ENABLE CUSTOM AGENT ────────────────────────────
    def test_ca06_enable_custom_agent(self, ncp_token, report_collector):
        agent_name = self._target_agent_name()

        resp = enable_custom_agent(agent_name, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA06] POST /api/v1/custom_agents/%s/enable → %s\n%s",
            agent_name, resp.status_code, pretty,
        )

        name_match     = isinstance(data, dict) and data.get("agent_name") == agent_name
        status_active  = isinstance(data, dict) and data.get("status") == "ACTIVE"
        message        = data.get("message") if isinstance(data, dict) else None
        has_message    = bool(message)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name   : {agent_name}\n"
            f"\nResult:\n"
            f"  message      : {message}\n"
            f"  agent_name   : {'YES (PASS)' if name_match else 'NO (FAIL)'}\n"
            f"  status=ACTIVE: {'YES (PASS)' if status_active else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 6,
            description      = (
                f"POST enable custom agent '{agent_name}' — verify 200, agent_name "
                f"matches, status='ACTIVE', message returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_name}/enable",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and status_active and has_message,
        )

        assert passed,        f"ENABLE custom agent failed: expected 200, got {resp.status_code}"
        assert name_match,    f"agent_name mismatch: expected {agent_name!r}, got {data.get('agent_name')!r}"
        assert status_active, f"Expected status='ACTIVE', got {data.get('status')!r}"
        assert has_message,   "Response missing 'message'"
        logger.info("[CA06] custom agent %r enabled", agent_name)

    # ── Step 7: ENABLE CUSTOM AGENT BACKGROUND ─────────────────
    def test_ca07_enable_custom_agent_background(self, ncp_token, report_collector):
        agent_name = self._target_agent_name()

        resp = enable_custom_agent_background(agent_name, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA07] POST /api/v1/custom_agents/%s/enable-background → %s\n%s",
            agent_name, resp.status_code, pretty,
        )

        name_match  = isinstance(data, dict) and data.get("agent_name") == agent_name
        supports_bg = isinstance(data, dict) and data.get("supports_background") is True
        message     = data.get("message") if isinstance(data, dict) else None
        has_message = bool(message)

        summary = (
            f"Status              : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name        : {agent_name}\n"
            f"\nResult:\n"
            f"  message           : {message}\n"
            f"  agent_name        : {'YES (PASS)' if name_match else 'NO (FAIL)'}\n"
            f"  supports_background: {data.get('supports_background') if isinstance(data, dict) else None} "
            f"{'✓' if supports_bg else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 7,
            description      = (
                f"POST enable-background custom agent '{agent_name}' — verify 200, "
                f"agent_name matches, supports_background=true, message returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_name}/enable-background",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and supports_bg and has_message,
        )

        assert passed,      f"ENABLE-BACKGROUND failed: expected 200, got {resp.status_code}"
        assert name_match,  f"agent_name mismatch: expected {agent_name!r}, got {data.get('agent_name')!r}"
        assert supports_bg, f"Expected supports_background=true, got {data.get('supports_background')!r}"
        assert has_message, "Response missing 'message'"
        logger.info("[CA07] custom agent %r background-enabled", agent_name)

    # ── Step 8: DISABLE CUSTOM AGENT BACKGROUND ────────────────
    def test_ca08_disable_custom_agent_background(self, ncp_token, report_collector):
        agent_name = self._target_agent_name()

        resp = disable_custom_agent_background(agent_name, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA08] POST /api/v1/custom_agents/%s/disable-background → %s\n%s",
            agent_name, resp.status_code, pretty,
        )

        name_match   = isinstance(data, dict) and data.get("agent_name") == agent_name
        bg_disabled  = isinstance(data, dict) and data.get("supports_background") is False
        message      = data.get("message") if isinstance(data, dict) else None
        has_message  = bool(message)

        summary = (
            f"Status              : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name        : {agent_name}\n"
            f"\nResult:\n"
            f"  message           : {message}\n"
            f"  agent_name        : {'YES (PASS)' if name_match else 'NO (FAIL)'}\n"
            f"  supports_background: {data.get('supports_background') if isinstance(data, dict) else None} "
            f"{'✓ (false)' if bg_disabled else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 8,
            description      = (
                f"POST disable-background custom agent '{agent_name}' — verify 200, "
                f"agent_name matches, supports_background=false, message returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_name}/disable-background",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and bg_disabled and has_message,
        )

        assert passed,      f"DISABLE-BACKGROUND failed: expected 200, got {resp.status_code}"
        assert name_match,  f"agent_name mismatch: expected {agent_name!r}, got {data.get('agent_name')!r}"
        assert bg_disabled, f"Expected supports_background=false, got {data.get('supports_background')!r}"
        assert has_message, "Response missing 'message'"
        logger.info("[CA08] custom agent %r background-disabled", agent_name)

    # ── Step 9: ADMIN LIST CUSTOM AGENTS ───────────────────────
    def test_ca09_admin_list_custom_agents(self, ncp_token, report_collector):
        resp = admin_list_custom_agents(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        agents = data.get("agents", []) if isinstance(data, dict) else []
        total  = data.get("total") if isinstance(data, dict) else None

        agents_is_list = isinstance(agents, list)
        total_matches  = total == len(agents) if agents_is_list else False

        # Admin view carries richer review/status fields incl. assigned_roles.
        required_keys = (
            "agent_id", "name", "description", "status", "version",
            "submitted_by", "created_at", "updated_at", "reviewed_by",
            "reviewed_at", "rejection_reason", "status_changed_by",
            "status_changed_at", "submitted_at", "assigned_roles",
        )
        schema_ok = agents_is_list and all(
            isinstance(a, dict) and all(k in a for k in required_keys)
            for a in agents
        )
        # assigned_roles must be a list on every agent.
        roles_ok = agents_is_list and all(
            isinstance(a, dict) and isinstance(a.get("assigned_roles"), list)
            for a in agents
        )

        agent_names = [a.get("name") for a in agents if isinstance(a, dict)]

        logger.info(
            "[CA09] GET /api/v1/custom_agents/admin/list → %s (agents=%d, total=%s)",
            resp.status_code, len(agents), total,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  agents returned : {len(agents)}\n"
            f"  total field     : {total}\n"
            f"  total==count    : {'YES (PASS)' if total_matches else 'NO (FAIL)'}\n"
            f"  admin schema ok : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  assigned_roles  : {'list (PASS)' if roles_ok else 'NOT a list (FAIL)'}\n"
            f"\nAgent names     :\n  {agent_names}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 9,
            description      = (
                "GET admin list custom agents — verify 200, agents+total present, total "
                "matches count, admin schema keys present incl. assigned_roles (a list)"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/custom_agents/admin/list",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and agents_is_list and total_matches and schema_ok and roles_ok,
        )

        assert passed,        f"ADMIN list custom agents failed: expected 200, got {resp.status_code}"
        assert agents_is_list, "Response 'agents' is missing or not a list"
        assert total_matches, f"'total' ({total}) does not match agent count ({len(agents)})"
        assert schema_ok,     f"One or more agents missing admin keys {required_keys}"
        assert roles_ok,      "One or more agents have non-list 'assigned_roles'"
        logger.info(
            "[CA09] %d custom agent(s) in admin list — total=%s", len(agents), total,
        )

    # ── Step 10: GET MY CUSTOM AGENTS ──────────────────────────
    def test_ca10_get_my_custom_agents(self, ncp_token, report_collector):
        resp = get_my_custom_agents(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        agents = data.get("agents", []) if isinstance(data, dict) else []
        total  = data.get("total") if isinstance(data, dict) else None

        agents_is_list = isinstance(agents, list)
        total_matches  = total == len(agents) if agents_is_list else False

        required_keys = (
            "agent_id", "name", "description", "status", "version",
            "submitted_by", "created_at", "updated_at", "supports_background",
        )
        schema_ok = agents_is_list and all(
            isinstance(a, dict) and all(k in a for k in required_keys)
            for a in agents
        )

        # Every returned agent must have been submitted by the caller.
        mine_only = agents_is_list and all(
            isinstance(a, dict) and a.get("submitted_by") == NCP_USERNAME
            for a in agents
        )

        agent_names = [a.get("name") for a in agents if isinstance(a, dict)]

        logger.info(
            "[CA10] GET /api/v1/custom_agents/user/my-agent → %s (agents=%d, total=%s)",
            resp.status_code, len(agents), total,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  agents returned : {len(agents)}\n"
            f"  total field     : {total}\n"
            f"  total==count    : {'YES (PASS)' if total_matches else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  all mine ('{NCP_USERNAME}'): {'YES (PASS)' if mine_only else 'NO (FAIL)'}\n"
            f"\nAgent names     :\n  {agent_names}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 10,
            description      = (
                "GET my custom agents — verify 200, agents+total present, total matches "
                f"count, schema keys present, every agent submitted_by '{NCP_USERNAME}'"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/custom_agents/user/my-agent",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and agents_is_list and total_matches and schema_ok and mine_only,
        )

        assert passed,        f"GET my custom agents failed: expected 200, got {resp.status_code}"
        assert agents_is_list, "Response 'agents' is missing or not a list"
        assert total_matches, f"'total' ({total}) does not match agent count ({len(agents)})"
        assert schema_ok,     f"One or more agents missing required keys {required_keys}"
        assert mine_only,     f"One or more agents not submitted_by '{NCP_USERNAME}'"
        logger.info(
            "[CA10] %d custom agent(s) submitted by %s — total=%s",
            len(agents), NCP_USERNAME, total,
        )

    # ── Step 11: SUBMIT CUSTOM AGENT ───────────────────────────
    def test_ca11_submit_custom_agent(self, ncp_token, report_collector):
        # Guard: confirm the .ncp package exists before attempting upload.
        assert os.path.isfile(ONBOARD_PACKAGE_PATH), (
            f"Submit package not found at: {ONBOARD_PACKAGE_PATH}\n"
            f"Place '{TEST_CA_PACKAGE_FILENAME}' in the same folder as the test files."
        )

        resp = submit_custom_agent(ONBOARD_PACKAGE_PATH, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA11] POST /api/v1/custom_agents/user/submit → %s\n%s",
            resp.status_code, pretty,
        )

        agent_id   = data.get("agent_id") if isinstance(data, dict) else None
        agent_name = data.get("agent_name") if isinstance(data, dict) else None
        status     = data.get("status") if isinstance(data, dict) else None
        message    = data.get("message") if isinstance(data, dict) else None

        has_agent_id = agent_id is not None
        name_match   = agent_name == TEST_CA_AGENT_NAME
        # Role-aware: admin → ACTIVE, regular user → PENDING.
        status_ok    = status in ("ACTIVE", "PENDING")
        has_message  = bool(message)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  file         : {TEST_CA_PACKAGE_FILENAME}\n"
            f"\nResult:\n"
            f"  message      : {message}\n"
            f"  agent_id     : {agent_id} {'✓' if has_agent_id else '✗'}\n"
            f"  agent_name   : {agent_name} {'✓' if name_match else '✗'}\n"
            f"  status       : {status} {'✓ (ACTIVE/PENDING)' if status_ok else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 11,
            description      = (
                f"POST submit custom agent from '{TEST_CA_PACKAGE_FILENAME}' — verify 200, "
                f"success message, agent_id returned, agent_name='{TEST_CA_AGENT_NAME}', "
                f"status ACTIVE (admin) or PENDING (user)"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/user/submit",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_agent_id and name_match and status_ok and has_message,
        )

        assert passed,       f"SUBMIT custom agent failed: expected 200, got {resp.status_code}"
        assert has_agent_id, "Response missing 'agent_id'"
        assert name_match,   f"agent_name mismatch: expected {TEST_CA_AGENT_NAME!r}, got {agent_name!r}"
        assert status_ok,    f"Expected status ACTIVE or PENDING, got {status!r}"
        assert has_message,  "Response missing 'message'"
        logger.info(
            "[CA11] custom agent submitted — agent_id=%s name=%r status=%s",
            agent_id, agent_name, status,
        )

    # ── Step 12: UPDATE CUSTOM AGENT (NEW VERSION) ─────────────
    def test_ca12_update_custom_agent_version(self, ncp_token, report_collector):
        # Guard: confirm the bumped-version .ncp package exists before upload.
        # This is a SEPARATE file from the base package (same filename, higher
        # version), kept in the TEST_CA_VERSION_SUBDIR subfolder.
        assert os.path.isfile(VERSION_PACKAGE_PATH), (
            f"Version-bump package not found at: {VERSION_PACKAGE_PATH}\n"
            f"Place the higher-version '{TEST_CA_PACKAGE_FILENAME}' in the "
            f"'{TEST_CA_VERSION_SUBDIR}' subfolder next to the test files."
        )

        agent_id = self._target_agent_id()

        resp = update_custom_agent_version(agent_id, VERSION_PACKAGE_PATH, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA12] POST /api/v1/custom_agents/%s/version → %s\n%s",
            agent_id, resp.status_code, pretty,
        )

        # agent_id path param may echo back as int; compare leniently.
        id_match     = isinstance(data, dict) and str(data.get("agent_id")) == str(agent_id)
        name_match   = isinstance(data, dict) and data.get("agent_name") == TEST_CA_AGENT_NAME
        version      = data.get("version") if isinstance(data, dict) else None
        has_version  = bool(version)
        status       = data.get("status") if isinstance(data, dict) else None
        status_ok    = status in ("ACTIVE", "PENDING")
        message      = data.get("message") if isinstance(data, dict) else None
        has_message  = bool(message)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_id     : {agent_id}\n"
            f"  file         : {TEST_CA_PACKAGE_FILENAME}\n"
            f"\nResult:\n"
            f"  message      : {message}\n"
            f"  agent_id     : {'YES' if id_match else 'NO'} (got {data.get('agent_id') if isinstance(data, dict) else None})\n"
            f"  agent_name   : {'YES' if name_match else 'NO'} (got {data.get('agent_name') if isinstance(data, dict) else None!r})\n"
            f"  version      : {version} {'✓' if has_version else '✗'}\n"
            f"  status       : {status} {'✓ (ACTIVE/PENDING)' if status_ok else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 12,
            description      = (
                f"POST update custom agent {agent_id} version from '{TEST_CA_PACKAGE_FILENAME}' "
                f"— verify 200, agent_id matches, agent_name echoed, version returned, "
                f"status ACTIVE/PENDING"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_id}/version",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and name_match and has_version and status_ok and has_message,
        )

        assert passed,      f"UPDATE version failed: expected 200, got {resp.status_code}"
        assert id_match,    f"agent_id mismatch: expected {agent_id}, got {data.get('agent_id')}"
        assert name_match,  f"agent_name mismatch: expected {TEST_CA_AGENT_NAME!r}, got {data.get('agent_name')!r}"
        assert has_version, "Response missing 'version'"
        assert status_ok,   f"Expected status ACTIVE or PENDING, got {status!r}"
        assert has_message, "Response missing 'message'"
        logger.info(
            "[CA12] custom agent %s updated — version=%s status=%s",
            agent_id, version, status,
        )

    # ── Step 13: APPROVE CUSTOM AGENT ──────────────────────────
    def test_ca13_approve_custom_agent(self, ncp_token, report_collector):
        agent_id = self._target_agent_id()

        resp = approve_custom_agent(agent_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA13] POST /api/v1/custom_agents/%s/approve → %s\n%s",
            agent_id, resp.status_code, pretty,
        )

        name_match    = isinstance(data, dict) and data.get("agent_name") == TEST_CA_AGENT_NAME
        status_active = isinstance(data, dict) and data.get("status") == "ACTIVE"
        message       = data.get("message") if isinstance(data, dict) else None
        has_message   = bool(message)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_id     : {agent_id}\n"
            f"\nResult:\n"
            f"  message      : {message}\n"
            f"  agent_name   : {'YES (PASS)' if name_match else 'NO (FAIL)'} "
            f"(got {data.get('agent_name') if isinstance(data, dict) else None!r})\n"
            f"  status=ACTIVE: {'YES (PASS)' if status_active else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 13,
            description      = (
                f"POST approve custom agent {agent_id} — verify 200, agent_name matches, "
                f"status='ACTIVE', message returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_id}/approve",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and status_active and has_message,
        )

        assert passed,        f"APPROVE custom agent failed: expected 200, got {resp.status_code}"
        assert name_match,    f"agent_name mismatch: expected {TEST_CA_AGENT_NAME!r}, got {data.get('agent_name')!r}"
        assert status_active, f"Expected status='ACTIVE', got {data.get('status')!r}"
        assert has_message,   "Response missing 'message'"
        logger.info("[CA13] custom agent %s approved", agent_id)

    # ── Step 14: DECLINE CUSTOM AGENT ──────────────────────────
    def test_ca14_decline_custom_agent(self, ncp_token, report_collector):
        agent_id = self._target_agent_id()
        feedback = TEST_CA_DECLINE_FEEDBACK

        resp = decline_custom_agent(agent_id, feedback=feedback, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA14] POST /api/v1/custom_agents/%s/decline → %s\n%s",
            agent_id, resp.status_code, pretty,
        )

        name_match      = isinstance(data, dict) and data.get("agent_name") == TEST_CA_AGENT_NAME
        status_rejected = isinstance(data, dict) and data.get("status") == "REJECTED"
        message         = data.get("message") if isinstance(data, dict) else None
        has_message     = bool(message)

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_id      : {agent_id}\n"
            f"  feedback      : {feedback}\n"
            f"\nResult:\n"
            f"  message       : {message}\n"
            f"  agent_name    : {'YES (PASS)' if name_match else 'NO (FAIL)'} "
            f"(got {data.get('agent_name') if isinstance(data, dict) else None!r})\n"
            f"  status=REJECTED: {'YES (PASS)' if status_rejected else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 14,
            description      = (
                f"POST decline custom agent {agent_id} (feedback={feedback!r}) — verify 200, "
                f"agent_name matches, status='REJECTED', message returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_id}/decline",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and status_rejected and has_message,
        )

        assert passed,          f"DECLINE custom agent failed: expected 200, got {resp.status_code}"
        assert name_match,      f"agent_name mismatch: expected {TEST_CA_AGENT_NAME!r}, got {data.get('agent_name')!r}"
        assert status_rejected, f"Expected status='REJECTED', got {data.get('status')!r}"
        assert has_message,     "Response missing 'message'"
        logger.info("[CA14] custom agent %s declined", agent_id)

    # ── Step 15: FEEDBACK CUSTOM AGENT ─────────────────────────
    def test_ca15_feedback_custom_agent(self, ncp_token, report_collector):
        agent_id      = self._target_agent_id()
        message_in    = TEST_CA_FEEDBACK_MESSAGE
        feedback_type = TEST_CA_FEEDBACK_TYPE

        resp = submit_custom_agent_feedback(
            agent_id      = agent_id,
            message       = message_in,
            feedback_type = feedback_type,
            token         = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA15] POST /api/v1/custom_agents/%s/feedback → %s\n%s",
            agent_id, resp.status_code, pretty,
        )

        name_match  = isinstance(data, dict) and data.get("agent_name") == TEST_CA_AGENT_NAME
        message_out = data.get("message") if isinstance(data, dict) else None
        has_message = bool(message_out)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_id     : {agent_id}\n"
            f"  message      : {message_in}\n"
            f"  feedback_type: {feedback_type}\n"
            f"\nResult:\n"
            f"  message      : {message_out} {'✓' if has_message else '✗'}\n"
            f"  agent_name   : {'YES (PASS)' if name_match else 'NO (FAIL)'} "
            f"(got {data.get('agent_name') if isinstance(data, dict) else None!r})\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 15,
            description      = (
                f"POST feedback custom agent {agent_id} (message={message_in!r}) — verify 200, "
                f"agent_name matches, confirmation message returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/custom_agents/{agent_id}/feedback",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and has_message,
        )

        assert passed,      f"FEEDBACK custom agent failed: expected 200, got {resp.status_code}"
        assert name_match,  f"agent_name mismatch: expected {TEST_CA_AGENT_NAME!r}, got {data.get('agent_name')!r}"
        assert has_message, "Response missing 'message'"
        logger.info("[CA15] feedback submitted for custom agent %s", agent_id)

    # ── Step 16: DOWNLOAD CUSTOM AGENT ─────────────────────────
    def test_ca16_download_custom_agent(self, ncp_token, report_collector):
        agent_id = self._target_agent_id()

        resp = download_custom_agent(agent_id, token=ncp_token)
        passed = resp.status_code == 200

        content_disp = resp.headers.get("Content-Disposition", "")
        content_type = resp.headers.get("Content-Type", "")
        body_bytes   = resp.content or b""

        has_disposition = "attachment" in content_disp.lower()
        has_ncp_name    = ".ncp" in content_disp.lower()
        has_bytes       = len(body_bytes) > 0

        logger.info(
            "[CA16] GET /api/v1/custom_agents/%s/download → %s (%d bytes, type=%s)",
            agent_id, resp.status_code, len(body_bytes), content_type,
        )

        summary = (
            f"Status             : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_id         : {agent_id}\n"
            f"\nResult:\n"
            f"  Content-Type     : {content_type}\n"
            f"  Content-Disposition: {content_disp}\n"
            f"  attachment       : {'YES (PASS)' if has_disposition else 'NO (FAIL)'}\n"
            f"  .ncp filename    : {'YES (PASS)' if has_ncp_name else 'NO (FAIL)'}\n"
            f"  bytes received   : {len(body_bytes)} {'✓' if has_bytes else '✗'}\n"
        )

        report_collector.add_flow(
            step             = 16,
            description      = (
                f"GET download custom agent {agent_id} — verify 200, Content-Disposition "
                f"attachment header with a .ncp filename, and non-empty package bytes"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/custom_agents/{agent_id}/download",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_disposition and has_ncp_name and has_bytes,
        )

        assert passed,          f"DOWNLOAD custom agent failed: expected 200, got {resp.status_code}"
        assert has_disposition, f"Missing 'attachment' Content-Disposition: {content_disp!r}"
        assert has_ncp_name,    f"Content-Disposition filename is not a .ncp: {content_disp!r}"
        assert has_bytes,       "Downloaded package is empty"
        logger.info(
            "[CA16] downloaded custom agent %s package — %d bytes", agent_id, len(body_bytes),
        )

    # ── Step 17: CAN SUBMIT CUSTOM AGENT ───────────────────────
    def test_ca17_can_submit_custom_agent(self, ncp_token, report_collector):
        expected = TEST_CA_CAN_SUBMIT_EXPECTED

        resp = can_submit_custom_agent(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA17] GET /api/v1/custom_agents/user/can-submit-agent → %s\n%s",
            resp.status_code, pretty,
        )

        can_submit   = data.get("submitAgent") if isinstance(data, dict) else None
        key_present  = isinstance(data, dict) and "submitAgent" in data
        is_bool      = isinstance(can_submit, bool)
        matches_role = can_submit is expected

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  submitAgent   : {can_submit} {'✓' if is_bool else '✗'}\n"
            f"  key present   : {'YES (PASS)' if key_present else 'NO (FAIL)'}\n"
            f"  expected (role): {expected}\n"
            f"  matches       : {'YES (PASS)' if matches_role else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 17,
            description      = (
                "GET can-submit-agent — verify 200, 'submitAgent' present as a bool and "
                f"matches expected ({expected}) for the test role"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/custom_agents/user/can-submit-agent",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and key_present and is_bool and matches_role,
        )

        assert passed,       f"CAN-SUBMIT-AGENT failed: expected 200, got {resp.status_code}"
        assert key_present,  "Response missing 'submitAgent' key"
        assert is_bool,      f"'submitAgent' is not a bool: {can_submit!r}"
        assert matches_role, f"Expected submitAgent={expected}, got {can_submit}"
        logger.info("[CA17] submitAgent=%s (expected %s)", can_submit, expected)

    # ── Step 18: REMOVE (DELETE) CUSTOM AGENT ──────────────────
    def test_ca18_remove_custom_agent(self, ncp_token, report_collector):
        agent_name = self._target_agent_name()

        resp = remove_custom_agent(agent_name, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA18] DELETE /api/v1/custom_agents/%s → %s\n%s",
            agent_name, resp.status_code, pretty,
        )

        name_match  = isinstance(data, dict) and data.get("agent_name") == agent_name
        message     = data.get("message") if isinstance(data, dict) else None
        has_message = bool(message)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name   : {agent_name}\n"
            f"\nResult:\n"
            f"  message      : {message}\n"
            f"  agent_name   : {'YES (PASS)' if name_match else 'NO (FAIL)'} "
            f"(got {data.get('agent_name') if isinstance(data, dict) else None!r})\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 18,
            description      = (
                f"DELETE remove custom agent '{agent_name}' — verify 200, agent_name "
                f"matches, removal-confirmation message returned"
            ),
            api_method       = "DELETE",
            endpoint         = "/api/v1/custom_agents/{agent_name}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and has_message,
        )

        assert passed,      f"REMOVE custom agent failed: expected 200, got {resp.status_code}"
        assert name_match,  f"agent_name mismatch: expected {agent_name!r}, got {data.get('agent_name')!r}"
        assert has_message, "Response missing 'message'"
        logger.info("[CA18] custom agent %r removed", agent_name)

    # ── Step 19: REMOVE (DELETE) USER CUSTOM AGENT ─────────────
    def test_ca19_remove_user_custom_agent(self, ncp_token, report_collector):
        agent_name = self._target_agent_name()
        force       = TEST_CA_ALLOW_FORCE_DELETE

        # Setup: CA18 already removed the shared agent, so re-onboard it (best
        # effort) to give this user-scoped force-delete something to remove.
        if os.path.isfile(ONBOARD_PACKAGE_PATH):
            setup = onboard_custom_agent(ONBOARD_PACKAGE_PATH, token=ncp_token)
            logger.info("[CA19] setup re-onboard → %s", setup.status_code)
        else:
            logger.warning(
                "[CA19] onboard package missing (%s); attempting delete without setup",
                ONBOARD_PACKAGE_PATH,
            )

        resp = remove_user_custom_agent(
            agent_name         = agent_name,
            allow_force_delete = force,
            token              = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[CA19] DELETE /api/v1/custom_agents/user/%s?allow_force_delete=%s → %s\n%s",
            agent_name, force, resp.status_code, pretty,
        )

        name_match  = isinstance(data, dict) and data.get("agent_name") == agent_name
        message     = data.get("message") if isinstance(data, dict) else None
        has_message = bool(message)

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name      : {agent_name}\n"
            f"  allow_force_delete: {force}\n"
            f"\nResult:\n"
            f"  message         : {message}\n"
            f"  agent_name      : {'YES (PASS)' if name_match else 'NO (FAIL)'} "
            f"(got {data.get('agent_name') if isinstance(data, dict) else None!r})\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 19,
            description      = (
                f"DELETE remove user custom agent '{agent_name}' (allow_force_delete={force}) "
                f"— verify 200, agent_name matches, removal-confirmation message returned"
            ),
            api_method       = "DELETE",
            endpoint         = "/api/v1/custom_agents/user/{agent_name}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and name_match and has_message,
        )

        assert passed,      f"REMOVE user custom agent failed: expected 200, got {resp.status_code}"
        assert name_match,  f"agent_name mismatch: expected {agent_name!r}, got {data.get('agent_name')!r}"
        assert has_message, "Response missing 'message'"
        logger.info("[CA19] user custom agent %r removed (force=%s)", agent_name, force)
