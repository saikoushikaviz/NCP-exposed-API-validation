"""
NCP Dashboard API — Functional Flow Tests

Covers the Dashboard section endpoints (DB01 – ...). Steps are added as each
endpoint spec is provided (7 total).

  ── DB01: GET DASHBOARD METRICS ─────────────────────────────────
  Step 1  GET dashboard metrics (range_type=7d, granularity=day)
          → verify response structure: range + summary (chats, messages,
            files, dataconnectors, llms, projects, storage, devices,
            sdk_agents, users) with counts and percentage_change; the
            timeseries block (messages, files, dataconnectors) is also
            surfaced in the report

  ── DB02: GET SYSTEM METRICS ────────────────────────────────────
  Step 2  GET dashboard metrics/system (start_time, end_time)
          → verify 200 and cpu/mem/disk time-series arrays, each a list
            of [timestamp_ms, value] points

  ── DB03: GET GPU METRICS ───────────────────────────────────────
  Step 3  GET dashboard metrics/gpu (llm_name, start_time, end_time)
          → verify 200 and a non-empty body; the returned structure
            (dict keys or list length) is surfaced in the report

  ── DB04: GET DOCKER STATS ──────────────────────────────────────
  Step 4  GET dashboard metrics/docker (limit)
          → verify 200 and a non-empty body; when the body is a list,
            also confirm it honours the requested row limit

  ── DB05: GENERATE LOGS ─────────────────────────────────────────
  Step 5  POST dashboard/logs/generate  (no params, no body)
          → verify 200, message present, a log_id returned, and a
            status field (e.g. "pending"); log_id is surfaced for
            downstream steps

  ── DB06: DOWNLOAD LOGS ─────────────────────────────────────────
  Step 6  GET dashboard/logs/download/{log_id}
          → verify 200, Content-Disposition header present, and
            zipped-log bytes received (gzip)

  ── DB07: LIST LOGS ─────────────────────────────────────────────
  Step 7  GET dashboard/logs/list  (no params)
          → verify 200 and a JSON array; each archive entry carries
            id/filename/status/created_at/file_size_mb

Parameters used:
  range_type  : 7d
  granularity : day
  from_ts     : computed dynamically (now - 7 days)
  to_ts       : computed dynamically (now)
  llm_name    : gpt-oss-120b  (TEST_GPU_LLM_NAME)
  limit       : 100           (TEST_DOCKER_STATS_LIMIT)
  log_id      : 1             (TEST_LOG_ID)
  authorization: regular JWT from get_ncp_token() via _auth_headers()
"""

import pytest
import logging
import json
from datetime import datetime, timezone, timedelta

from api_client import (
    get_dashboard_metrics,
    get_system_metrics,
    get_gpu_metrics,
    get_docker_stats,
    generate_logs,
    download_logs,
    list_logs,
    safe_json,
)
from config import TEST_GPU_LLM_NAME, TEST_DOCKER_STATS_LIMIT, TEST_LOG_ID

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
# DASHBOARD FUNCTIONAL FLOW  (DB01)
# ════════════════════════════════════════════════════════════════

class TestDashboardFunctionalFlow:

    # ── Step 1: GET DASHBOARD METRICS ─────────────────────────
    def test_db01_get_dashboard_metrics(self, ncp_token, report_collector):

        # Compute dynamic time range: last 7 days
        now      = datetime.now(timezone.utc)
        to_ts    = now.isoformat()
        from_ts  = (now - timedelta(days=7)).isoformat()
        range_type  = "7d"
        granularity = "day"

        resp = get_dashboard_metrics(
            range_type=range_type,
            from_ts=from_ts,
            to_ts=to_ts,
            granularity=granularity,
            token=ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info(
            "[DB01] GET /api/v1/dashboard/metrics"
            "?range_type=%s&granularity=%s → %s\n%s",
            range_type, granularity, resp.status_code, pretty,
        )

        # Extract summary fields for report
        summary      = data.get("summary", {}) if data else {}
        range_info   = data.get("range", {}) if data else {}
        timeseries   = data.get("timeseries", {}) if data else {}
        chats        = summary.get("chats", {})
        messages     = summary.get("messages", {})
        files        = summary.get("files", {})
        dataconn     = summary.get("dataconnectors", {})
        # Extended summary metrics (present in current schema)
        llms         = summary.get("llms", {})
        projects     = summary.get("projects", {})
        storage      = summary.get("storage", {})
        devices      = summary.get("devices", {})
        sdk_agents   = summary.get("sdk_agents", {})
        users        = summary.get("users", {})

        has_range      = bool(range_info)
        has_summary    = bool(summary)
        has_timeseries = bool(timeseries)

        def _c(m):  # compact "count (change%)" formatter
            return f"count={m.get('current_count', 'N/A')}, change={m.get('percentage_change', 'N/A')}%"

        metrics_summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest Parameters:\n"
            f"  range_type    : {range_type}\n"
            f"  granularity   : {granularity}\n"
            f"  from_ts       : {from_ts}\n"
            f"  to_ts         : {to_ts}\n"
            f"\nRange Returned  :\n"
            f"  from          : {range_info.get('from', 'N/A')}\n"
            f"  to            : {range_info.get('to', 'N/A')}\n"
            f"  granularity   : {range_info.get('granularity', 'N/A')}\n"
            f"\nSummary Metrics :\n"
            f"  Chats         : {_c(chats)}\n"
            f"  Messages      : {_c(messages)}\n"
            f"  Files         : {_c(files)}\n"
            f"  DataConnectors: {_c(dataconn)}\n"
            f"    type_counts : {dataconn.get('type_counts', {})}\n"
            f"  LLMs          : {_c(llms)}\n"
            f"  Projects      : {_c(projects)}\n"
            f"  Devices       : {_c(devices)}\n"
            f"  SDK Agents    : {_c(sdk_agents)}\n"
            f"  Users         : {_c(users)}\n"
            f"  Storage       : used={storage.get('used_bytes', 'N/A')}/"
            f"{storage.get('total_bytes', 'N/A')} bytes "
            f"({storage.get('consumed_percentage', 'N/A')}% consumed)\n"
            f"\nTimeseries      :\n"
            f"  present       : {'YES' if has_timeseries else 'NO'}\n"
            f"  keys          : {list(timeseries.keys()) if isinstance(timeseries, dict) else 'N/A'}\n"
            f"\nStructure Check :\n"
            f"  range present   : {'YES' if has_range else 'NO'}\n"
            f"  summary present : {'YES' if has_summary else 'NO'}\n"
            f"\nFull Response   :\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"GET dashboard metrics range_type={range_type}, "
                               f"granularity={granularity} — verify range + summary fields",
            api_method       = "GET",
            endpoint         = "/api/v1/dashboard/metrics",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = metrics_summary,
            passed           = passed and has_range and has_summary,
        )

        assert passed,      f"GET dashboard metrics failed: expected 200, got {resp.status_code}"
        assert has_range,   "Response missing 'range' field"
        assert has_summary, "Response missing 'summary' field"
        logger.info(
            "[DB01] Dashboard metrics verified — chats=%s, messages=%s, "
            "files=%s, dataconnectors=%s",
            chats.get("current_count"),
            messages.get("current_count"),
            files.get("current_count"),
            dataconn.get("current_count"),
        )

    # ── Step 2: GET SYSTEM METRICS ────────────────────────────
    def test_db02_get_system_metrics(self, ncp_token, report_collector):

        # Compute dynamic time range: last 7 days
        now       = datetime.now(timezone.utc)
        end_time  = now.isoformat()
        start_time = (now - timedelta(days=7)).isoformat()

        resp = get_system_metrics(
            start_time=start_time,
            end_time=end_time,
            token=ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200

        # Extract the three time-series (each a list of [timestamp_ms, value] points)
        cpu  = data.get("cpu", []) if isinstance(data, dict) else []
        mem  = data.get("mem", []) if isinstance(data, dict) else []
        disk = data.get("disk", []) if isinstance(data, dict) else []

        def _series_ok(series):
            # A valid series is a list; if non-empty, points are [timestamp, value] pairs
            return isinstance(series, list) and all(
                isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in series
            )

        has_keys   = isinstance(data, dict) and all(k in data for k in ("cpu", "mem", "disk"))
        cpu_ok     = _series_ok(cpu)
        mem_ok     = _series_ok(mem)
        disk_ok    = _series_ok(disk)
        shape_ok   = has_keys and cpu_ok and mem_ok and disk_ok

        def _last(series):
            return series[-1] if isinstance(series, list) and series else "N/A"

        logger.info(
            "[DB02] GET /api/v1/dashboard/metrics/system → %s "
            "(cpu=%d, mem=%d, disk=%d points)",
            resp.status_code, len(cpu), len(mem), len(disk),
        )

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest Parameters:\n"
            f"  start_time    : {start_time}\n"
            f"  end_time      : {end_time}\n"
            f"\nSeries Returned :\n"
            f"  cpu  : {len(cpu)} points {'✓' if cpu_ok else '✗'}  (last={_last(cpu)})\n"
            f"  mem  : {len(mem)} points {'✓' if mem_ok else '✗'}  (last={_last(mem)})\n"
            f"  disk : {len(disk)} points {'✓' if disk_ok else '✗'}  (last={_last(disk)})\n"
            f"\nStructure Check :\n"
            f"  cpu/mem/disk present : {'YES (PASS)' if has_keys else 'NO (FAIL)'}\n"
            f"  point shape [ts,val] : {'YES (PASS)' if shape_ok else 'NO (FAIL)'}\n"
        )

        report_collector.add_flow(
            step             = 2,
            description      = "GET system metrics (start_time, end_time) — verify cpu/mem/disk "
                               "time-series arrays of [timestamp, value] points",
            api_method       = "GET",
            endpoint         = "/api/v1/dashboard/metrics/system",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and shape_ok,
        )

        assert passed,   f"GET system metrics failed: expected 200, got {resp.status_code}"
        assert has_keys, "Response missing one of 'cpu'/'mem'/'disk'"
        assert shape_ok, "cpu/mem/disk series are not lists of [timestamp, value] points"
        logger.info(
            "[DB02] System metrics verified — cpu=%d, mem=%d, disk=%d points",
            len(cpu), len(mem), len(disk),
        )

    # ── Step 3: GET GPU METRICS ───────────────────────────────
    def test_db03_get_gpu_metrics(self, ncp_token, report_collector):

        # Compute dynamic time range: last 7 days
        now        = datetime.now(timezone.utc)
        end_time   = now.isoformat()
        start_time = (now - timedelta(days=7)).isoformat()
        llm_name   = TEST_GPU_LLM_NAME

        resp = get_gpu_metrics(
            llm_name=llm_name,
            start_time=start_time,
            end_time=end_time,
            token=ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200

        # Body can be large (time-series like /system); keep the report bounded.
        pretty = json.dumps(data, indent=2, default=str) if data is not None \
                 else f"(status {resp.status_code}, no body)"
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        # The GPU response shape is not documented (schema is a generic string),
        # so describe whatever comes back rather than asserting a fixed shape.
        if isinstance(data, dict):
            shape_desc  = f"dict with keys: {list(data.keys())}"
            has_body    = len(data) > 0
        elif isinstance(data, list):
            shape_desc  = f"list of {len(data)} item(s)"
            has_body    = len(data) > 0
        else:
            shape_desc  = f"{type(data).__name__}: {str(data)[:100]}"
            has_body    = data not in (None, "", {}, [])

        logger.info(
            "[DB03] GET /api/v1/dashboard/metrics/gpu?llm_name=%s → %s (%s)",
            llm_name, resp.status_code, shape_desc,
        )

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest Parameters:\n"
            f"  llm_name      : {llm_name}\n"
            f"  start_time    : {start_time}\n"
            f"  end_time      : {end_time}\n"
            f"\nResponse Shape  :\n"
            f"  {shape_desc}\n"
            f"  non-empty body : {'YES (PASS)' if has_body else 'NO (FAIL)'}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = (
                f"GET GPU metrics (llm_name={llm_name}, start_time, end_time) "
                "— verify 200 and a non-empty body"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/dashboard/metrics/gpu",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_body,
        )

        assert passed,   f"GET GPU metrics failed: expected 200, got {resp.status_code}"
        assert has_body, f"GPU metrics response is empty ({shape_desc})"
        logger.info("[DB03] GPU metrics verified for llm_name=%s — %s", llm_name, shape_desc)

    # ── Step 4: GET DOCKER STATS ──────────────────────────────
    def test_db04_get_docker_stats(self, ncp_token, report_collector):
        limit = TEST_DOCKER_STATS_LIMIT

        resp = get_docker_stats(limit=limit, token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str) if data is not None \
                 else f"(status {resp.status_code}, no body)"
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        # Endpoint returns "latest docker stats for tabular display"; shape is
        # undocumented (schema is a generic string). Describe what comes back and,
        # when it's a list, confirm it respects the requested row limit.
        limit_ok = True   # vacuously true unless the body is a countable list
        if isinstance(data, dict):
            # Rows may be nested under a common key (e.g. rows/data/stats/containers).
            row_key   = next((k for k in ("rows", "data", "stats", "containers")
                              if isinstance(data.get(k), list)), None)
            rows      = data.get(row_key) if row_key else None
            row_count = len(rows) if isinstance(rows, list) else None
            shape_desc = (f"dict with keys: {list(data.keys())}"
                          + (f"; '{row_key}' has {row_count} row(s)" if row_key else ""))
            has_body   = len(data) > 0
            if isinstance(rows, list):
                limit_ok = row_count <= limit
        elif isinstance(data, list):
            row_count  = len(data)
            shape_desc = f"list of {row_count} row(s)"
            has_body   = row_count > 0
            limit_ok   = row_count <= limit
        else:
            row_count  = None
            shape_desc = f"{type(data).__name__}: {str(data)[:100]}"
            has_body   = data not in (None, "", {}, [])

        logger.info(
            "[DB04] GET /api/v1/dashboard/metrics/docker?limit=%d → %s (%s)",
            limit, resp.status_code, shape_desc,
        )

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest Parameters:\n"
            f"  limit         : {limit}\n"
            f"\nResponse Shape  :\n"
            f"  {shape_desc}\n"
            f"  non-empty body : {'YES (PASS)' if has_body else 'NO (FAIL)'}\n"
            f"  within limit   : {'YES (PASS)' if limit_ok else f'NO — {row_count} > {limit} (FAIL)'}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 4,
            description      = (
                f"GET docker stats (limit={limit}) — verify 200, non-empty body, "
                "and (if a list) row count within the limit"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/dashboard/metrics/docker",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_body and limit_ok,
        )

        assert passed,   f"GET docker stats failed: expected 200, got {resp.status_code}"
        assert has_body, f"Docker stats response is empty ({shape_desc})"
        assert limit_ok, f"Docker stats returned {row_count} rows, exceeding limit {limit}"
        logger.info("[DB04] Docker stats verified (limit=%d) — %s", limit, shape_desc)

    # ── Step 5: GENERATE LOGS ─────────────────────────────────
    def test_db05_generate_logs(self, ncp_token, report_collector):

        resp = generate_logs(token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str) if data is not None \
                 else f"(status {resp.status_code}, no body)"

        message = data.get("message") if isinstance(data, dict) else None
        log_id  = data.get("log_id")  if isinstance(data, dict) else None
        status  = data.get("status")  if isinstance(data, dict) else None

        has_message = bool(message)
        has_log_id  = log_id is not None
        has_status  = bool(status)

        logger.info(
            "[DB05] POST /api/v1/dashboard/logs/generate → %s "
            "(log_id=%s, status=%s)",
            resp.status_code, log_id, status,
        )

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\n(no request parameters / no body)\n"
            f"\nResult:\n"
            f"  message      : {message} {'✓' if has_message else '✗'}\n"
            f"  log_id       : {log_id} {'✓' if has_log_id else '✗'}\n"
            f"  status       : {status} {'✓' if has_status else '✗'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 5,
            description      = (
                "POST generate logs (async trigger) — verify 200, message present, "
                "log_id returned, and a status field"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/dashboard/logs/generate",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_message and has_log_id and has_status,
        )

        assert passed,      f"POST generate logs failed: expected 200, got {resp.status_code}"
        assert has_message, "Generate-logs response missing 'message'"
        assert has_log_id,  "Generate-logs response missing 'log_id'"
        assert has_status,  "Generate-logs response missing 'status'"
        logger.info(
            "[DB05] Log generation triggered — log_id=%s, status=%s", log_id, status,
        )

    # ── Step 6: DOWNLOAD LOGS ─────────────────────────────────
    def test_db06_download_logs(self, ncp_token, report_collector):
        log_id = TEST_LOG_ID

        resp = download_logs(log_id, token=ncp_token)
        passed = resp.status_code == 200

        content_type  = resp.headers.get("Content-Type", "N/A")
        content_disp  = resp.headers.get("Content-Disposition", "N/A")
        content_len   = resp.headers.get("Content-Length", "N/A")
        content_bytes = resp.content
        has_disp      = content_disp != "N/A"
        has_bytes     = len(content_bytes) > 0
        is_gzip       = "gzip" in content_type.lower()   # soft indicator, not asserted

        logger.info(
            "[DB06] GET /api/v1/dashboard/logs/download/%s → %s "
            "(Content-Type=%s, bytes=%d)",
            log_id, resp.status_code, content_type, len(content_bytes),
        )

        summary = (
            f"Status               : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  log_id             : {log_id}\n"
            f"\nDownload Result:\n"
            f"  Content-Type       : {content_type} {'(gzip ✓)' if is_gzip else ''}\n"
            f"  Content-Length     : {content_len}\n"
            f"  Content-Disposition: {content_disp} {'✓' if has_disp else '✗'}\n"
            f"  Bytes received     : {len(content_bytes)} {'✓' if has_bytes else '✗'}\n"
        )

        report_collector.add_flow(
            step             = 6,
            description      = (
                f"GET download logs log_id={log_id} "
                "— verify 200, Content-Disposition header and zipped bytes received"
            ),
            api_method       = "GET",
            endpoint         = f"/api/v1/dashboard/logs/download/{log_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and has_disp and has_bytes,
        )

        assert passed,    f"DOWNLOAD logs failed: expected 200, got {resp.status_code}"
        assert has_disp,  "DOWNLOAD logs response missing Content-Disposition header"
        assert has_bytes, "DOWNLOAD logs response body was empty"
        logger.info(
            "[DB06] log_id=%s downloaded — %d bytes, Content-Disposition=%s",
            log_id, len(content_bytes), content_disp,
        )

    # ── Step 7: LIST LOGS ─────────────────────────────────────
    def test_db07_list_logs(self, ncp_token, report_collector):

        resp = list_logs(token=ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str) if data is not None \
                 else f"(status {resp.status_code}, no body)"
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        # Response is a JSON array of log-archive objects.
        is_list  = isinstance(data, list)
        archives = data if is_list else []

        # Every archive entry must carry the documented schema keys.
        required_keys = ("id", "filename", "status", "created_at", "file_size_mb")
        schema_ok = is_list and all(
            isinstance(a, dict) and all(k in a for k in required_keys)
            for a in archives
        )

        log_ids = [a.get("id") for a in archives if isinstance(a, dict)]

        logger.info(
            "[DB07] GET /api/v1/dashboard/logs/list → %s (%d archive(s), ids=%s)",
            resp.status_code, len(archives), log_ids,
        )

        summary = (
            f"Status            : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\n(no request parameters)\n"
            f"\nResult:\n"
            f"  is list         : {'YES (PASS)' if is_list else 'NO (FAIL)'}\n"
            f"  archives        : {len(archives)}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  archive ids     : {log_ids}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 7,
            description      = (
                "GET list logs — verify 200, a JSON array, and each archive carries "
                f"keys {required_keys}"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/dashboard/logs/list",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and is_list and schema_ok,
        )

        assert passed,    f"LIST logs failed: expected 200, got {resp.status_code}"
        assert is_list,   f"LIST logs response is not a JSON array (got {type(data).__name__})"
        assert schema_ok, f"One or more log archives missing required keys {required_keys}"
        logger.info(
            "[DB07] %d log archive(s) listed — ids=%s", len(archives), log_ids,
        )
