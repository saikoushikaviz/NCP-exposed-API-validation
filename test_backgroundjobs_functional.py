"""
NCP Background Jobs API — Functional Flow Tests

Covers the Background Jobs endpoints (BJ01 – ...). This suite groups all 13
Background Jobs APIs together; steps are added as each endpoint spec is
provided.

  ── BJ01: PREVIEW CRON ──────────────────────────────────────────
  Step 1  POST /api/v1/background_jobs/cron/preview
          body: {cron_expression, timezone}
          → validate a CRON expression and return the next 5 fire times.
            Verify 200, valid=true, error is null, and next_runs is a
            non-empty list of 5 upcoming run timestamps.

  ── BJ02: CAN CREATE BACKGROUND JOB ─────────────────────────────
  Step 2  GET /api/v1/background_jobs/user/can-create
          → whether the caller's role can create / trigger background jobs.
            Verify 200, "canCreateBackgroundJob" present as a bool, and it
            matches the expected value for the test role (admin → true).

  ── BJ03: CREATE BACKGROUND JOB ─────────────────────────────────
  Step 3  POST /api/v1/background_jobs
          body: {project_id, agent_name, prompt, cron_expression, timezone,
                 name, notification_channels, slack_channel_ids}
          → create a recurring background job. Verify 201, a job_id is
            returned, the echoed fields match the request, status="active"
            and trigger_type="scheduled". The job_id is captured on the class
            so later steps (get / update / run / delete) can reuse it.

  ── BJ04: LIST BACKGROUND JOBS ──────────────────────────────────
  Step 4  GET /api/v1/background_jobs?project_id=&mine_only=&include_removed=
          → list jobs in a project. Verify 200, "jobs" list + "total" present,
            total matches the number of jobs, each job carries the expected
            schema keys, and (if BJ03 ran) the created job_id is in the list.

  ── BJ05: ADMIN LIST ALL BACKGROUND JOBS ────────────────────────
  Step 5  GET /api/v1/background_jobs/admin/all?include_removed=
          → list every job across all projects (role-aware). Verify 200,
            "jobs" list + "total" present, total matches count, each job
            carries the schema keys incl. "project_name", and (if BJ03 ran)
            the created job_id is in the list.

  ── BJ06: UPDATE BACKGROUND JOB ─────────────────────────────────
  Step 6  PATCH /api/v1/background_jobs/{job_id}
          body: {name, prompt, cron_expression, notification_channels, ...}
          → partial update of the job created in BJ03 (falls back to a
            configured job_id). Verify 200, job_id unchanged, and the edited
            fields (name / prompt / cron) are echoed back with the new values.

  ── BJ07: GET BACKGROUND JOB ────────────────────────────────────
  Step 7  GET /api/v1/background_jobs/{job_id}
          → fetch a single job (any project member). Verify 200, the returned
            job_id matches the requested one, and the payload carries the
            expected schema keys.

  ── BJ08: RUN BACKGROUND JOB NOW ────────────────────────────────
  Step 8  POST /api/v1/background_jobs/{job_id}/run-now
          → trigger an immediate one-off run. Verify 200, the returned job_id
            matches, status="queued", and a task_id is returned.

  ── BJ09: PAUSE BACKGROUND JOB ──────────────────────────────────
  Step 9  POST /api/v1/background_jobs/{job_id}/pause
          → pause an active job (unregisters the schedule, DB row preserved).
            Verify 200, job_id matches, status="paused", next_run_at is null.

  ── BJ10: RESUME BACKGROUND JOB ─────────────────────────────────
  Step 10 POST /api/v1/background_jobs/{job_id}/resume
          → resume a paused job (re-registers the schedule from its stored
            cron). Verify 200, job_id matches, status="active", and
            next_run_at is set again.

  ── BJ11: LIST BACKGROUND JOB RUNS ──────────────────────────────
  Step 11 GET /api/v1/background_jobs/{job_id}/runs
          → list a job's runs + aggregates. Verify 200, job_id matches, "runs"
            is a list (each row carrying the run schema keys), the aggregate
            fields are present, succeeded+failed == total_runs, and
            success_rate is a ratio in [0, 1]. A run message_id is captured for
            BJ12.

  ── BJ12: GET BACKGROUND JOB RUN ────────────────────────────────
  Step 12 GET /api/v1/background_jobs/{job_id}/runs/{message_id}
          → fetch a single run's metadata + output. Verify 200, job_id and
            message_id match, "output" present, "timeline" is a list, and
            "usage" is an object carrying the token/iteration keys.

  ── BJ13: DELETE (REMOVE) BACKGROUND JOB ────────────────────────
  Step 13 DELETE /api/v1/background_jobs/{job_id}
          → permanently remove a job (unregisters schedule, soft-deletes the
            row, hard-deletes the result conversation). Runs last so it cleans
            up the job BJ03 created. Verify 200, job_id matches, status=
            "removed", and next_run_at is null.

Test data:
  cron_expression : */5 * * * *   (every 5 minutes)
  timezone        : UTC
  can-create role : superadmin (admin) → expected true
  create job      : agent=verizon-bigquery-agent, project_id=1,
                    cron=*/6 * * * *, name="List all the devices"
"""

import pytest
import logging
import json

from api_client import (
    preview_cron,
    can_create_background_job,
    create_background_job,
    list_background_jobs,
    admin_list_all_background_jobs,
    update_background_job,
    get_background_job,
    run_background_job_now,
    pause_background_job,
    resume_background_job,
    list_background_job_runs,
    get_background_job_run,
    delete_background_job,
    get_projects,
    safe_json,
)
from config import (
    TEST_CRON_EXPRESSION,
    TEST_CRON_TIMEZONE,
    TEST_CAN_CREATE_BG_JOB_EXPECTED,
    TEST_BG_JOB_PROJECT_ID,
    TEST_BG_JOB_AGENT_NAME,
    TEST_BG_JOB_PROMPT,
    TEST_BG_JOB_CRON,
    TEST_BG_JOB_TIMEZONE,
    TEST_BG_JOB_NAME,
    TEST_BG_JOB_NOTIFICATION_CHANNELS,
    TEST_BG_JOB_SLACK_CHANNEL_IDS,
    TEST_BG_JOBS_PROJECT_ID,
    TEST_BG_JOBS_MINE_ONLY,
    TEST_BG_JOBS_INCLUDE_REMOVED,
    TEST_BG_JOBS_ADMIN_INCLUDE_REMOVED,
    TEST_BG_JOB_ID,
    TEST_BG_JOB_RUN_MESSAGE_ID,
    TEST_BG_JOB_UPDATE_NAME,
    TEST_BG_JOB_UPDATE_PROMPT,
    TEST_BG_JOB_UPDATE_AGENT_NAME,
    TEST_BG_JOB_UPDATE_TRIGGER_TYPE,
    TEST_BG_JOB_UPDATE_CRON,
    TEST_BG_JOB_UPDATE_TIMEZONE,
    TEST_BG_JOB_UPDATE_NOTIFICATION_CHANNELS,
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
# BACKGROUND JOBS FUNCTIONAL FLOW  (BJ01 – ...)
# ════════════════════════════════════════════════════════════════

class TestBackgroundJobsFunctionalFlow:

    # Captured at runtime by BJ03 (create) so later steps
    # (get / update / run / delete) can operate on a real job.
    created_job_id = None

    # Captured at runtime by BJ11 (list runs) so BJ12 can fetch a real run.
    sample_message_id = None

    # Resolved at runtime from the projects list so create/list target a real
    # project the caller belongs to (instead of a hardcoded id that may drift).
    resolved_project_id = None

    @classmethod
    def _resolve_project_id(cls, token):
        """A valid project_id to use for create/list: the first project returned
        by GET /projects (caller is a member), cached; falls back to config."""
        if cls.resolved_project_id is not None:
            return cls.resolved_project_id
        try:
            data = safe_json(get_projects(token))
            projs = data if isinstance(data, list) \
                    else data.get("projects", []) if isinstance(data, dict) else []
            for p in projs:
                if isinstance(p, dict) and p.get("project_id") is not None:
                    cls.resolved_project_id = p["project_id"]
                    break
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("[BJ] project resolve failed: %s", exc)
        if cls.resolved_project_id is None:
            cls.resolved_project_id = TEST_BG_JOB_PROJECT_ID
        logger.info("[BJ] using project_id=%s", cls.resolved_project_id)
        return cls.resolved_project_id

    @classmethod
    def _target_job_id(cls):
        """job_id to operate on: the one BJ03 created, else the configured fallback."""
        return cls.created_job_id or TEST_BG_JOB_ID

    @classmethod
    def _target_message_id(cls):
        """run message_id to fetch: the one BJ11 captured, else the configured fallback."""
        return cls.sample_message_id or TEST_BG_JOB_RUN_MESSAGE_ID

    # ── Step 1: PREVIEW CRON ───────────────────────────────────
    def test_bj01_preview_cron(self, ncp_token, report_collector):
        cron_expression = TEST_CRON_EXPRESSION
        timezone        = TEST_CRON_TIMEZONE

        resp = preview_cron(
            cron_expression = cron_expression,
            timezone        = timezone,
            token           = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ01] POST /api/v1/background_jobs/cron/preview → %s\n%s",
            resp.status_code, pretty,
        )

        valid          = data.get("valid") if isinstance(data, dict) else None
        error          = data.get("error") if isinstance(data, dict) else None
        next_runs      = data.get("next_runs") if isinstance(data, dict) else None
        human_readable = data.get("human_readable") if isinstance(data, dict) else None

        valid_true    = valid is True
        error_is_null = error is None
        runs_is_list  = isinstance(next_runs, list) and len(next_runs) > 0
        five_runs     = isinstance(next_runs, list) and len(next_runs) == 5

        summary = (
            f"Status           : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  cron_expression: {cron_expression}\n"
            f"  timezone       : {timezone}\n"
            f"\nResult:\n"
            f"  valid          : {valid} {'✓' if valid_true else '✗'}\n"
            f"  error          : {error} {'✓' if error_is_null else '✗'}\n"
            f"  human_readable : {human_readable}\n"
            f"  next_runs count: {len(next_runs) if isinstance(next_runs, list) else 'N/A'} "
            f"{'✓' if five_runs else '(expected 5)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = (
                f"POST preview cron (cron_expression={cron_expression}, timezone={timezone}) "
                f"— verify 200, valid=true, error null, next_runs is a non-empty list of 5"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/background_jobs/cron/preview",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and valid_true and error_is_null and runs_is_list,
        )

        assert passed,        f"PREVIEW cron failed: expected 200, got {resp.status_code}"
        assert valid_true,    f"Expected valid=true, got valid={valid} (error={error!r})"
        assert error_is_null, f"Expected error to be null, got {error!r}"
        assert runs_is_list,  "Response 'next_runs' missing or empty"
        logger.info(
            "[BJ01] cron '%s' valid — %d upcoming run(s) returned",
            cron_expression, len(next_runs),
        )

    # ── Step 2: CAN CREATE BACKGROUND JOB ──────────────────────
    def test_bj02_can_create_background_job(self, ncp_token, report_collector):
        expected = TEST_CAN_CREATE_BG_JOB_EXPECTED

        resp = can_create_background_job(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ02] GET /api/v1/background_jobs/user/can-create → %s\n%s",
            resp.status_code, pretty,
        )

        can_create = data.get("canCreateBackgroundJob") if isinstance(data, dict) else None

        key_present  = isinstance(data, dict) and "canCreateBackgroundJob" in data
        is_bool      = isinstance(can_create, bool)
        matches_role = can_create is expected

        summary = (
            f"Status             : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  canCreateBackgroundJob: {can_create} {'✓' if is_bool else '✗'}\n"
            f"  key present          : {'YES (PASS)' if key_present else 'NO (FAIL)'}\n"
            f"  expected (role)      : {expected}\n"
            f"  matches expected     : {'YES (PASS)' if matches_role else 'NO (FAIL)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = (
                "GET can-create background job — verify 200, 'canCreateBackgroundJob' "
                f"present as a bool and matches expected ({expected}) for the test role"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/background_jobs/user/can-create",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and key_present and is_bool and matches_role,
        )

        assert passed,       f"CAN-CREATE background job failed: expected 200, got {resp.status_code}"
        assert key_present,  "Response missing 'canCreateBackgroundJob' key"
        assert is_bool,      f"'canCreateBackgroundJob' is not a bool: {can_create!r}"
        assert matches_role, f"Expected canCreateBackgroundJob={expected}, got {can_create}"
        logger.info("[BJ02] canCreateBackgroundJob=%s (expected %s)", can_create, expected)

    # ── Step 3: CREATE BACKGROUND JOB ──────────────────────────
    def test_bj03_create_background_job(self, ncp_token, report_collector):
        project_id = self._resolve_project_id(ncp_token)
        agent_name = TEST_BG_JOB_AGENT_NAME
        prompt     = TEST_BG_JOB_PROMPT
        cron       = TEST_BG_JOB_CRON
        timezone   = TEST_BG_JOB_TIMEZONE
        name       = TEST_BG_JOB_NAME
        channels   = TEST_BG_JOB_NOTIFICATION_CHANNELS
        slack_ids  = TEST_BG_JOB_SLACK_CHANNEL_IDS

        resp = create_background_job(
            project_id            = project_id,
            agent_name            = agent_name,
            prompt                = prompt,
            cron_expression       = cron,
            name                  = name,
            timezone              = timezone,
            notification_channels = channels,
            slack_channel_ids     = slack_ids,
            token                 = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 201
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ03] POST /api/v1/background_jobs → %s\n%s",
            resp.status_code, pretty,
        )

        job_id = data.get("job_id") if isinstance(data, dict) else None

        # Capture for later steps regardless of assertion outcome below.
        if job_id:
            TestBackgroundJobsFunctionalFlow.created_job_id = job_id

        has_job_id     = bool(job_id)
        name_match     = isinstance(data, dict) and data.get("name") == name
        agent_match    = isinstance(data, dict) and data.get("agent_name") == agent_name
        project_match  = isinstance(data, dict) and data.get("project_id") == project_id
        cron_match     = isinstance(data, dict) and data.get("cron_expression") == cron
        status_active  = isinstance(data, dict) and data.get("status") == "active"
        trigger_sched  = isinstance(data, dict) and data.get("trigger_type") == "scheduled"

        summary = (
            f"Status           : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id     : {project_id}\n"
            f"  agent_name     : {agent_name}\n"
            f"  cron_expression: {cron}\n"
            f"  name           : {name}\n"
            f"  channels       : {channels}\n"
            f"  slack_channels : {slack_ids}\n"
            f"\nResult:\n"
            f"  job_id         : {job_id} {'✓' if has_job_id else '✗'}\n"
            f"  name match     : {'YES' if name_match else 'NO'}\n"
            f"  agent match    : {'YES' if agent_match else 'NO'}\n"
            f"  project match  : {'YES' if project_match else 'NO'}\n"
            f"  cron match     : {'YES' if cron_match else 'NO'}\n"
            f"  status=active  : {'YES' if status_active else 'NO'}\n"
            f"  trigger=scheduled: {'YES' if trigger_sched else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = (
                f"POST create background job '{name}' (project_id={project_id}, "
                f"agent={agent_name}, cron={cron}) — verify 201, job_id returned, "
                f"fields echoed, status=active, trigger_type=scheduled"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/background_jobs",
            expected_status  = "201",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = (passed and has_job_id and name_match and agent_match
                                and project_match and cron_match and status_active
                                and trigger_sched),
        )

        assert passed,        f"CREATE background job failed: expected 201, got {resp.status_code}"
        assert has_job_id,    "Response missing 'job_id'"
        assert name_match,    f"name mismatch: expected {name!r}, got {data.get('name')!r}"
        assert agent_match,   f"agent_name mismatch: expected {agent_name!r}, got {data.get('agent_name')!r}"
        assert project_match, f"project_id mismatch: expected {project_id}, got {data.get('project_id')}"
        assert cron_match,    f"cron_expression mismatch: expected {cron!r}, got {data.get('cron_expression')!r}"
        assert status_active, f"Expected status='active', got {data.get('status')!r}"
        assert trigger_sched, f"Expected trigger_type='scheduled', got {data.get('trigger_type')!r}"
        logger.info("[BJ03] background job created — job_id=%s", job_id)

    # ── Step 4: LIST BACKGROUND JOBS ───────────────────────────
    def test_bj04_list_background_jobs(self, ncp_token, report_collector):
        # Same project BJ03 created the job in, so the created job is in the list.
        project_id      = self._resolve_project_id(ncp_token)
        mine_only       = TEST_BG_JOBS_MINE_ONLY
        include_removed = TEST_BG_JOBS_INCLUDE_REMOVED

        resp = list_background_jobs(
            project_id      = project_id,
            mine_only       = mine_only,
            include_removed = include_removed,
            token           = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        jobs  = data.get("jobs", []) if isinstance(data, dict) else []
        total = data.get("total") if isinstance(data, dict) else None

        jobs_is_list  = isinstance(jobs, list)
        total_matches = total == len(jobs) if jobs_is_list else False

        # Every job must carry the documented schema keys
        required_keys = (
            "job_id", "project_id", "name", "agent_name", "prompt",
            "trigger_type", "cron_expression", "status", "creator_username",
            "notification_channels", "slack_channel_ids",
        )
        schema_ok = jobs_is_list and all(
            isinstance(j, dict) and all(k in j for k in required_keys)
            for j in jobs
        )

        # All returned jobs should belong to the requested project.
        project_ok = jobs_is_list and all(
            isinstance(j, dict) and j.get("project_id") == project_id for j in jobs
        )

        # If BJ03 created a job, it should appear in this (mine_only) list.
        created_id    = TestBackgroundJobsFunctionalFlow.created_job_id
        job_ids       = [j.get("job_id") for j in jobs if isinstance(j, dict)]
        created_found = created_id in job_ids if created_id else None

        logger.info(
            "[BJ04] GET /api/v1/background_jobs → %s (jobs=%d, total=%s)",
            resp.status_code, len(jobs), total,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  project_id      : {project_id}\n"
            f"  mine_only       : {mine_only}\n"
            f"  include_removed : {include_removed}\n"
            f"\nResult:\n"
            f"  jobs returned   : {len(jobs)}\n"
            f"  total field     : {total}\n"
            f"  total==count    : {'YES (PASS)' if total_matches else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  all in project  : {'YES (PASS)' if project_ok else 'NO (FAIL)'}\n"
            f"  created job '{created_id}': "
            f"{'FOUND (PASS)' if created_found else ('MISSING' if created_id else 'n/a — BJ03 not run')}\n"
            f"\nJob IDs         :\n  {job_ids}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 4,
            description      = (
                f"GET list background jobs (project_id={project_id}, mine_only={mine_only}, "
                f"include_removed={include_removed}) — verify 200, jobs+total present, "
                f"total matches count, schema keys present, all scoped to project"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/background_jobs",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and jobs_is_list and total_matches and schema_ok and project_ok,
        )

        assert passed,        f"LIST background jobs failed: expected 200, got {resp.status_code}"
        assert jobs_is_list,  "Response 'jobs' is missing or not a list"
        assert total_matches, f"'total' ({total}) does not match job count ({len(jobs)})"
        assert schema_ok,     f"One or more jobs missing required keys {required_keys}"
        assert project_ok,    f"One or more jobs not scoped to project_id={project_id}"
        if created_id:
            assert created_found, f"Created job '{created_id}' not present in list"
        logger.info(
            "[BJ04] %d background job(s) returned — total=%s", len(jobs), total,
        )

    # ── Step 5: ADMIN LIST ALL BACKGROUND JOBS ─────────────────
    def test_bj05_admin_list_all_background_jobs(self, ncp_token, report_collector):
        include_removed = TEST_BG_JOBS_ADMIN_INCLUDE_REMOVED

        resp = admin_list_all_background_jobs(
            include_removed = include_removed,
            token           = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        jobs  = data.get("jobs", []) if isinstance(data, dict) else []
        total = data.get("total") if isinstance(data, dict) else None

        jobs_is_list  = isinstance(jobs, list)
        total_matches = total == len(jobs) if jobs_is_list else False

        # Admin view carries project names alongside the standard job schema.
        required_keys = (
            "job_id", "project_id", "project_name", "name", "agent_name",
            "prompt", "trigger_type", "cron_expression", "status",
            "creator_username", "notification_channels", "slack_channel_ids",
        )
        schema_ok = jobs_is_list and all(
            isinstance(j, dict) and all(k in j for k in required_keys)
            for j in jobs
        )
        project_names_ok = jobs_is_list and all(
            isinstance(j, dict) and j.get("project_name") for j in jobs
        )

        # If BJ03 created a job, an admin should see it here.
        created_id    = TestBackgroundJobsFunctionalFlow.created_job_id
        job_ids       = [j.get("job_id") for j in jobs if isinstance(j, dict)]
        created_found = created_id in job_ids if created_id else None

        logger.info(
            "[BJ05] GET /api/v1/background_jobs/admin/all → %s (jobs=%d, total=%s)",
            resp.status_code, len(jobs), total,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  include_removed : {include_removed}\n"
            f"\nResult:\n"
            f"  jobs returned   : {len(jobs)}\n"
            f"  total field     : {total}\n"
            f"  total==count    : {'YES (PASS)' if total_matches else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  project_name set: {'YES (PASS)' if project_names_ok else 'NO (FAIL)'}\n"
            f"  created job '{created_id}': "
            f"{'FOUND (PASS)' if created_found else ('MISSING' if created_id else 'n/a — BJ03 not run')}\n"
            f"\nJob IDs         :\n  {job_ids}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 5,
            description      = (
                f"GET admin list all background jobs (include_removed={include_removed}) "
                f"— verify 200, jobs+total present, total matches count, schema keys "
                f"present incl. project_name"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/background_jobs/admin/all",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = (passed and jobs_is_list and total_matches
                                and schema_ok and project_names_ok),
        )

        assert passed,           f"ADMIN list all failed: expected 200, got {resp.status_code}"
        assert jobs_is_list,     "Response 'jobs' is missing or not a list"
        assert total_matches,    f"'total' ({total}) does not match job count ({len(jobs)})"
        assert schema_ok,        f"One or more jobs missing required keys {required_keys}"
        assert project_names_ok, "One or more jobs missing 'project_name'"
        if created_id:
            assert created_found, f"Created job '{created_id}' not present in admin list"
        logger.info(
            "[BJ05] %d background job(s) across all projects — total=%s", len(jobs), total,
        )

    # ── Step 6: UPDATE BACKGROUND JOB ──────────────────────────
    def test_bj06_update_background_job(self, ncp_token, report_collector):
        job_id   = self._target_job_id()
        new_name = TEST_BG_JOB_UPDATE_NAME
        new_prompt = TEST_BG_JOB_UPDATE_PROMPT
        new_cron   = TEST_BG_JOB_UPDATE_CRON
        channels   = TEST_BG_JOB_UPDATE_NOTIFICATION_CHANNELS

        resp = update_background_job(
            job_id                = job_id,
            name                  = new_name,
            prompt                = new_prompt,
            agent_name            = TEST_BG_JOB_UPDATE_AGENT_NAME,
            trigger_type          = TEST_BG_JOB_UPDATE_TRIGGER_TYPE,
            cron_expression       = new_cron,
            timezone              = TEST_BG_JOB_UPDATE_TIMEZONE,
            notification_channels = channels,
            token                 = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ06] PATCH /api/v1/background_jobs/%s → %s\n%s",
            job_id, resp.status_code, pretty,
        )

        id_match     = isinstance(data, dict) and data.get("job_id") == job_id
        name_match   = isinstance(data, dict) and data.get("name") == new_name
        prompt_match = isinstance(data, dict) and data.get("prompt") == new_prompt
        cron_match   = isinstance(data, dict) and data.get("cron_expression") == new_cron

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest (PATCH):\n"
            f"  job_id       : {job_id}\n"
            f"  name         : {new_name}\n"
            f"  prompt       : {new_prompt}\n"
            f"  cron         : {new_cron}\n"
            f"  channels     : {channels}\n"
            f"\nResult:\n"
            f"  job_id match : {'YES' if id_match else 'NO'}\n"
            f"  name updated : {'YES' if name_match else 'NO'} (got {data.get('name') if isinstance(data, dict) else None!r})\n"
            f"  prompt updated: {'YES' if prompt_match else 'NO'}\n"
            f"  cron updated : {'YES' if cron_match else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 6,
            description      = (
                f"PATCH update background job {job_id} (name/prompt/cron) "
                f"— verify 200, job_id unchanged, edited fields echoed with new values"
            ),
            api_method       = "PATCH",
            endpoint         = "/api/v1/background_jobs/{job_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and name_match and prompt_match and cron_match,
        )

        assert passed,       f"UPDATE background job failed: expected 200, got {resp.status_code}"
        assert id_match,     f"job_id changed: expected {job_id}, got {data.get('job_id')}"
        assert name_match,   f"name not updated: expected {new_name!r}, got {data.get('name')!r}"
        assert prompt_match, f"prompt not updated: expected {new_prompt!r}, got {data.get('prompt')!r}"
        assert cron_match,   f"cron not updated: expected {new_cron!r}, got {data.get('cron_expression')!r}"
        logger.info("[BJ06] background job %s updated — name=%r", job_id, new_name)

    # ── Step 7: GET BACKGROUND JOB ─────────────────────────────
    def test_bj07_get_background_job(self, ncp_token, report_collector):
        job_id = self._target_job_id()

        resp = get_background_job(job_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ07] GET /api/v1/background_jobs/%s → %s\n%s",
            job_id, resp.status_code, pretty,
        )

        id_match = isinstance(data, dict) and data.get("job_id") == job_id

        required_keys = (
            "job_id", "project_id", "project_name", "name", "agent_name",
            "prompt", "trigger_type", "cron_expression", "status",
            "creator_username", "notification_channels", "slack_channel_ids",
        )
        schema_ok = isinstance(data, dict) and all(k in data for k in required_keys)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  job_id       : {job_id}\n"
            f"\nResult:\n"
            f"  job_id match : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  schema keys  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  name         : {data.get('name') if isinstance(data, dict) else None}\n"
            f"  status       : {data.get('status') if isinstance(data, dict) else None}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 7,
            description      = (
                f"GET background job {job_id} — verify 200, returned job_id matches "
                f"the requested one, and payload carries the expected schema keys"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/background_jobs/{job_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and schema_ok,
        )

        assert passed,    f"GET background job failed: expected 200, got {resp.status_code}"
        assert id_match,  f"Returned job_id mismatch: expected {job_id}, got {data.get('job_id')}"
        assert schema_ok, f"Job payload missing required keys {required_keys}"
        logger.info("[BJ07] fetched background job %s — status=%s", job_id, data.get("status"))

    # ── Step 8: RUN BACKGROUND JOB NOW ─────────────────────────
    def test_bj08_run_background_job_now(self, ncp_token, report_collector):
        job_id = self._target_job_id()

        resp = run_background_job_now(job_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ08] POST /api/v1/background_jobs/%s/run-now → %s\n%s",
            job_id, resp.status_code, pretty,
        )

        id_match      = isinstance(data, dict) and data.get("job_id") == job_id
        status_queued = isinstance(data, dict) and data.get("status") == "queued"
        task_id       = data.get("task_id") if isinstance(data, dict) else None
        has_task_id   = bool(task_id)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  job_id       : {job_id}\n"
            f"\nResult:\n"
            f"  job_id match : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  status=queued: {'YES (PASS)' if status_queued else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"  task_id      : {task_id} {'✓' if has_task_id else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 8,
            description      = (
                f"POST run background job {job_id} now — verify 200, job_id matches, "
                f"status='queued', and a task_id is returned"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/background_jobs/{job_id}/run-now",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and status_queued and has_task_id,
        )

        assert passed,        f"RUN-NOW failed: expected 200, got {resp.status_code}"
        assert id_match,      f"Returned job_id mismatch: expected {job_id}, got {data.get('job_id')}"
        assert status_queued, f"Expected status='queued', got {data.get('status')!r}"
        assert has_task_id,   "Response missing 'task_id'"
        logger.info("[BJ08] job %s queued — task_id=%s", job_id, task_id)

    # ── Step 9: PAUSE BACKGROUND JOB ───────────────────────────
    def test_bj09_pause_background_job(self, ncp_token, report_collector):
        job_id = self._target_job_id()

        resp = pause_background_job(job_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ09] POST /api/v1/background_jobs/%s/pause → %s\n%s",
            job_id, resp.status_code, pretty,
        )

        id_match      = isinstance(data, dict) and data.get("job_id") == job_id
        status_paused = isinstance(data, dict) and data.get("status") == "paused"
        # A paused job has no scheduled next run.
        next_run      = data.get("next_run_at") if isinstance(data, dict) else "missing"
        next_run_null = next_run is None

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  job_id       : {job_id}\n"
            f"\nResult:\n"
            f"  job_id match : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  status=paused: {'YES (PASS)' if status_paused else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"  next_run_at  : {next_run} {'✓ (null)' if next_run_null else ''}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 9,
            description      = (
                f"POST pause background job {job_id} — verify 200, job_id matches, "
                f"status='paused', next_run_at is null"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/background_jobs/{job_id}/pause",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and status_paused and next_run_null,
        )

        assert passed,        f"PAUSE failed: expected 200, got {resp.status_code}"
        assert id_match,      f"Returned job_id mismatch: expected {job_id}, got {data.get('job_id')}"
        assert status_paused, f"Expected status='paused', got {data.get('status')!r}"
        assert next_run_null, f"Expected next_run_at to be null, got {next_run!r}"
        logger.info("[BJ09] job %s paused", job_id)

    # ── Step 10: RESUME BACKGROUND JOB ─────────────────────────
    def test_bj10_resume_background_job(self, ncp_token, report_collector):
        job_id = self._target_job_id()

        resp = resume_background_job(job_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ10] POST /api/v1/background_jobs/%s/resume → %s\n%s",
            job_id, resp.status_code, pretty,
        )

        id_match      = isinstance(data, dict) and data.get("job_id") == job_id
        status_active = isinstance(data, dict) and data.get("status") == "active"
        # A resumed scheduled job gets its next run re-registered.
        next_run      = data.get("next_run_at") if isinstance(data, dict) else None
        next_run_set  = bool(next_run)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  job_id       : {job_id}\n"
            f"\nResult:\n"
            f"  job_id match : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  status=active: {'YES (PASS)' if status_active else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"  next_run_at  : {next_run} {'✓ (re-registered)' if next_run_set else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 10,
            description      = (
                f"POST resume background job {job_id} — verify 200, job_id matches, "
                f"status='active', next_run_at re-registered"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/background_jobs/{job_id}/resume",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and status_active and next_run_set,
        )

        assert passed,        f"RESUME failed: expected 200, got {resp.status_code}"
        assert id_match,      f"Returned job_id mismatch: expected {job_id}, got {data.get('job_id')}"
        assert status_active, f"Expected status='active', got {data.get('status')!r}"
        assert next_run_set,  "Expected next_run_at to be set after resume"
        logger.info("[BJ10] job %s resumed — next_run_at=%s", job_id, next_run)

    # ── Step 11: LIST BACKGROUND JOB RUNS ──────────────────────
    def test_bj11_list_background_job_runs(self, ncp_token, report_collector):
        job_id = self._target_job_id()

        resp = list_background_job_runs(job_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        id_match = isinstance(data, dict) and data.get("job_id") == job_id
        runs     = data.get("runs", []) if isinstance(data, dict) else []
        runs_is_list = isinstance(runs, list)

        # Capture a run's message_id for BJ12 (get-run-detail).
        if runs_is_list and runs and isinstance(runs[0], dict) and runs[0].get("message_id"):
            TestBackgroundJobsFunctionalFlow.sample_message_id = runs[0]["message_id"]

        # Each run row carries the documented schema keys.
        run_keys = ("message_id", "run_at", "status", "duration_seconds", "total_tokens")
        runs_schema_ok = runs_is_list and all(
            isinstance(r, dict) and all(k in r for k in run_keys) for r in runs
        )

        # Aggregate stat-card fields.
        agg_keys = ("total_runs", "succeeded_runs", "failed_runs",
                    "skipped_runs", "success_rate", "avg_duration_seconds")
        agg_present = isinstance(data, dict) and all(k in data for k in agg_keys)

        total_runs     = data.get("total_runs") if isinstance(data, dict) else None
        succeeded_runs = data.get("succeeded_runs") if isinstance(data, dict) else None
        failed_runs    = data.get("failed_runs") if isinstance(data, dict) else None
        success_rate   = data.get("success_rate") if isinstance(data, dict) else None

        totals_consistent = (
            isinstance(total_runs, int) and isinstance(succeeded_runs, int)
            and isinstance(failed_runs, int)
            and (succeeded_runs + failed_runs) == total_runs
        )
        # success_rate is null when there are no counted runs yet (e.g. the
        # job's only run is still in progress → total_runs == 0). Accept None
        # in that case; otherwise it must be a ratio in [0, 1].
        rate_valid = (
            (success_rate is None and total_runs == 0)
            or (isinstance(success_rate, (int, float)) and 0 <= success_rate <= 1)
        )

        logger.info(
            "[BJ11] GET /api/v1/background_jobs/%s/runs → %s (runs=%d, total_runs=%s)",
            job_id, resp.status_code, len(runs), total_runs,
        )

        summary = (
            f"Status              : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  job_id            : {job_id}\n"
            f"\nResult:\n"
            f"  job_id match      : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  run rows returned : {len(runs)}\n"
            f"  run schema ok     : {'YES (PASS)' if runs_schema_ok else 'NO (FAIL)'}\n"
            f"  aggregates present: {'YES (PASS)' if agg_present else 'NO (FAIL)'}\n"
            f"  total_runs        : {total_runs}\n"
            f"  succeeded_runs    : {succeeded_runs}\n"
            f"  failed_runs       : {failed_runs}\n"
            f"  skipped_runs      : {data.get('skipped_runs') if isinstance(data, dict) else None}\n"
            f"  succ+fail==total  : {'YES (PASS)' if totals_consistent else 'NO (FAIL)'}\n"
            f"  success_rate      : {success_rate} {'✓' if rate_valid else '✗ (want 0..1)'}\n"
            f"  avg_duration_secs : {data.get('avg_duration_seconds') if isinstance(data, dict) else None}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 11,
            description      = (
                f"GET background job runs {job_id} — verify 200, job_id matches, runs "
                f"is a list w/ run schema keys, aggregates present, succeeded+failed=="
                f"total_runs, success_rate in [0,1]"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/background_jobs/{job_id}/runs",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = (passed and id_match and runs_is_list and runs_schema_ok
                                and agg_present and totals_consistent and rate_valid),
        )

        assert passed,            f"LIST runs failed: expected 200, got {resp.status_code}"
        assert id_match,          f"Returned job_id mismatch: expected {job_id}, got {data.get('job_id')}"
        assert runs_is_list,      "Response 'runs' is missing or not a list"
        assert runs_schema_ok,    f"One or more run rows missing keys {run_keys}"
        assert agg_present,       f"Response missing aggregate keys {agg_keys}"
        assert totals_consistent, f"succeeded+failed ({succeeded_runs}+{failed_runs}) != total_runs ({total_runs})"
        assert rate_valid,        f"success_rate out of range [0,1]: {success_rate}"
        logger.info(
            "[BJ11] %d run row(s) — total=%s succeeded=%s failed=%s rate=%s",
            len(runs), total_runs, succeeded_runs, failed_runs, success_rate,
        )

    # ── Step 12: GET BACKGROUND JOB RUN ────────────────────────
    def test_bj12_get_background_job_run(self, ncp_token, report_collector):
        job_id     = self._target_job_id()
        message_id = self._target_message_id()

        resp = get_background_job_run(job_id, message_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        id_match  = isinstance(data, dict) and data.get("job_id") == job_id
        # message_id in the path may echo back as int; compare leniently.
        msg_match = isinstance(data, dict) and str(data.get("message_id")) == str(message_id)

        has_status   = isinstance(data, dict) and "status" in data
        run_status   = data.get("status") if isinstance(data, dict) else None
        # output + usage are only populated once a run has SUCCEEDED. A run
        # still in progress ("running") or "skipped" legitimately has neither,
        # so only require them for a succeeded run.
        is_succeeded = run_status == "succeeded"
        has_output   = isinstance(data, dict) and "output" in data
        timeline     = data.get("timeline") if isinstance(data, dict) else None
        timeline_ok  = isinstance(timeline, list)
        usage        = data.get("usage") if isinstance(data, dict) else None
        usage_keys   = ("total_tokens", "prompt_tokens", "completion_tokens", "iterations")
        usage_present = isinstance(usage, dict) and all(k in usage for k in usage_keys)
        # Conditional: enforced only when the run has succeeded.
        output_ok = has_output if is_succeeded else True
        usage_ok  = usage_present if is_succeeded else True

        logger.info(
            "[BJ12] GET /api/v1/background_jobs/%s/runs/%s → %s",
            job_id, message_id, resp.status_code,
        )

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  job_id        : {job_id}\n"
            f"  message_id    : {message_id}\n"
            f"\nResult:\n"
            f"  job_id match  : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  message match : {'YES (PASS)' if msg_match else 'NO (FAIL)'}\n"
            f"  status        : {run_status}\n"
            f"  output present: {'YES' if has_output else 'no'} "
            f"({'required' if is_succeeded else 'optional — run not succeeded'})\n"
            f"  timeline list : {'YES (PASS)' if timeline_ok else 'NO (FAIL)'} "
            f"({len(timeline) if timeline_ok else 'n/a'} phase(s))\n"
            f"  usage keys ok : {'YES' if usage_present else 'no'} "
            f"({'required' if is_succeeded else 'optional — run not succeeded'})\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 12,
            description      = (
                f"GET background job run {job_id}/{message_id} — verify 200, job_id + "
                f"message_id match, timeline is a list; output + usage token keys "
                f"required only when the run has succeeded"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/background_jobs/{job_id}/runs/{message_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = (passed and id_match and msg_match and has_status
                                and timeline_ok and output_ok and usage_ok),
        )

        assert passed,       f"GET run detail failed: expected 200, got {resp.status_code}"
        assert id_match,     f"Returned job_id mismatch: expected {job_id}, got {data.get('job_id')}"
        assert msg_match,    f"Returned message_id mismatch: expected {message_id}, got {data.get('message_id')}"
        assert has_status,   "Run detail missing 'status'"
        assert timeline_ok,  "Run detail 'timeline' is missing or not a list"
        assert output_ok,    "Run detail missing 'output' for a succeeded run"
        assert usage_ok,     f"Run detail 'usage' missing keys {usage_keys} for a succeeded run"
        logger.info(
            "[BJ12] fetched run %s/%s — status=%s",
            job_id, message_id, data.get("status"),
        )

    # ── Step 13: DELETE (REMOVE) BACKGROUND JOB ────────────────
    def test_bj13_delete_background_job(self, ncp_token, report_collector):
        job_id = self._target_job_id()

        resp = delete_background_job(job_id, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[BJ13] DELETE /api/v1/background_jobs/%s → %s\n%s",
            job_id, resp.status_code, pretty,
        )

        id_match       = isinstance(data, dict) and data.get("job_id") == job_id
        status_removed = isinstance(data, dict) and data.get("status") == "removed"
        next_run       = data.get("next_run_at") if isinstance(data, dict) else "missing"
        next_run_null  = next_run is None

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  job_id       : {job_id}\n"
            f"\nResult:\n"
            f"  job_id match : {'YES (PASS)' if id_match else 'NO (FAIL)'}\n"
            f"  status=removed: {'YES (PASS)' if status_removed else 'NO (FAIL)'} "
            f"(got {data.get('status') if isinstance(data, dict) else None!r})\n"
            f"  next_run_at  : {next_run} {'✓ (null)' if next_run_null else ''}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 13,
            description      = (
                f"DELETE remove background job {job_id} — verify 200, job_id matches, "
                f"status='removed', next_run_at is null"
            ),
            api_method       = "DELETE",
            endpoint         = "/api/v1/background_jobs/{job_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and id_match and status_removed and next_run_null,
        )

        assert passed,         f"DELETE background job failed: expected 200, got {resp.status_code}"
        assert id_match,       f"Returned job_id mismatch: expected {job_id}, got {data.get('job_id')}"
        assert status_removed, f"Expected status='removed', got {data.get('status')!r}"
        assert next_run_null,  f"Expected next_run_at to be null, got {next_run!r}"
        logger.info("[BJ13] job %s removed", job_id)
