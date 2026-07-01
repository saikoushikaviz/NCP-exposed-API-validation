"""
NCP Platform Agents API — Functional Flow Tests

Covers the Platform Agents endpoints (PA01 – ...). This suite groups all
Platform Agents APIs together; steps are added as each endpoint spec is
provided.

  ── PA01: LIST PLATFORM AGENTS ──────────────────────────────────
  Step 1  GET /api/v1/platform-agents
          → verify 200, "agents" list + "total" present, total matches
            the number of agents, each agent carries the expected schema
            keys, and a known agent is present in the catalog

  ── PA02: EXECUTE PLATFORM AGENT ────────────────────────────────
  Step 2  POST /api/v1/platform-agents/{agent_name}/execute
          body: {query, project_id}
          → verify 200, success=true, agent_name echoed back, result present

Test data:
  known agent   : metrics_agent  (expected in the returned catalog)
  execute agent : metrics_agent  (query: "How many devices are in the inventory?")
"""

import pytest
import logging
import json

from api_client import (
    get_platform_agents,
    execute_platform_agent,
    safe_json,
)
from config import (
    TEST_PLATFORM_AGENT_NAME,
    TEST_EXECUTE_AGENT_NAME,
    TEST_EXECUTE_AGENT_QUERY,
    TEST_EXECUTE_AGENT_PROJECT_ID,
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
# PLATFORM AGENTS FUNCTIONAL FLOW  (PA01 – ...)
# ════════════════════════════════════════════════════════════════

class TestPlatformAgentsFunctionalFlow:

    # ── Step 1: LIST PLATFORM AGENTS ───────────────────────────
    def test_pa01_list_platform_agents(self, ncp_token, report_collector):

        resp = get_platform_agents(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        # Response can be large; keep the report body bounded.
        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        agents = data.get("agents", []) if isinstance(data, dict) else []
        total  = data.get("total") if isinstance(data, dict) else None

        agents_is_list = isinstance(agents, list) and len(agents) > 0
        total_matches  = total == len(agents) if isinstance(agents, list) else False

        # Every agent must carry the documented schema keys
        required_keys = ("name", "description", "requires_connector", "input_schema", "tools")
        schema_ok = agents_is_list and all(
            isinstance(a, dict) and all(k in a for k in required_keys)
            for a in agents
        )

        agent_names   = [a.get("name") for a in agents if isinstance(a, dict)]
        target_found  = TEST_PLATFORM_AGENT_NAME in agent_names

        logger.info(
            "[PA01] GET /api/v1/platform-agents → %s (agents=%d, total=%s)",
            resp.status_code, len(agents), total,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  Agents returned : {len(agents)}\n"
            f"  total field     : {total}\n"
            f"  total==count    : {'YES (PASS)' if total_matches else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  known agent '{TEST_PLATFORM_AGENT_NAME}': "
            f"{'FOUND (PASS)' if target_found else 'MISSING (FAIL)'}\n"
            f"\nAgent names     :\n  {agent_names}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = (
                "GET list platform agents — verify 200, agents+total present, "
                f"total matches count, schema keys present, '{TEST_PLATFORM_AGENT_NAME}' in catalog"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/platform-agents",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and agents_is_list and total_matches and schema_ok and target_found,
        )

        assert passed,         f"LIST platform agents failed: expected 200, got {resp.status_code}"
        assert agents_is_list, "Response 'agents' missing or empty"
        assert total_matches,  f"'total' ({total}) does not match agent count ({len(agents)})"
        assert schema_ok,      f"One or more agents missing required keys {required_keys}"
        assert target_found,   f"Known agent '{TEST_PLATFORM_AGENT_NAME}' not present in catalog"
        logger.info(
            "[PA01] %d platform agent(s) returned — total=%s, '%s' present",
            len(agents), total, TEST_PLATFORM_AGENT_NAME,
        )

    # ── Step 2: EXECUTE PLATFORM AGENT ─────────────────────────
    def test_pa02_execute_platform_agent(self, ncp_token, report_collector):
        agent_name = TEST_EXECUTE_AGENT_NAME
        query      = TEST_EXECUTE_AGENT_QUERY
        project_id = TEST_EXECUTE_AGENT_PROJECT_ID

        resp = execute_platform_agent(
            agent_name = agent_name,
            query      = query,
            project_id = project_id,
            token      = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[PA02] POST /api/v1/platform-agents/%s/execute → %s\n%s",
            agent_name, resp.status_code, pretty,
        )

        success        = data.get("success") if isinstance(data, dict) else None
        result         = data.get("result") if isinstance(data, dict) else None
        error          = data.get("error") if isinstance(data, dict) else None
        returned_agent = data.get("agent_name") if isinstance(data, dict) else None

        success_true  = success is True
        agent_match   = returned_agent == agent_name
        has_result    = bool(result)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  agent_name   : {agent_name}\n"
            f"  project_id   : {project_id}\n"
            f"  query        : {query}\n"
            f"\nResult:\n"
            f"  success      : {success} {'✓' if success_true else '✗'}\n"
            f"  agent_name   : {returned_agent} {'✓' if agent_match else '✗'}\n"
            f"  result       : {'present' if has_result else 'MISSING'} {'✓' if has_result else '✗'}\n"
            f"  error        : {error}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = (
                f"POST execute platform agent '{agent_name}' (project_id={project_id}) "
                f"— verify 200, success=true, agent_name echoed, result present"
            ),
            api_method       = "POST",
            endpoint         = f"/api/v1/platform-agents/{agent_name}/execute",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and success_true and agent_match and has_result,
        )

        assert passed,       f"EXECUTE platform agent failed: expected 200, got {resp.status_code}"
        assert success_true, f"Agent execution not successful: success={success}, error={error!r}"
        assert agent_match,  f"Returned agent_name mismatch: expected {agent_name}, got {returned_agent}"
        assert has_result,   "EXECUTE response missing 'result'"
        logger.info(
            "[PA02] agent '%s' executed successfully — result length=%d chars",
            agent_name, len(str(result)),
        )
