"""
NCP Dashboard API — Functional Flow Tests

Covers the Dashboard Metrics endpoint (DB01):

  Step 1  GET dashboard metrics (range_type=7d, granularity=day)
          → verify response structure: range, summary (chats, messages,
            files, dataconnectors) with counts and percentage_change

Parameters used:
  range_type  : 7d
  granularity : day
  from_ts     : computed dynamically (now - 7 days)
  to_ts       : computed dynamically (now)
  authorization: regular JWT from get_ncp_token() via _auth_headers()
"""

import pytest
import logging
import json
from datetime import datetime, timezone, timedelta

from api_client import (
    get_dashboard_metrics,
    safe_json,
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
        chats        = summary.get("chats", {})
        messages     = summary.get("messages", {})
        files        = summary.get("files", {})
        dataconn     = summary.get("dataconnectors", {})

        has_range   = bool(range_info)
        has_summary = bool(summary)

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
            f"  Chats         : count={chats.get('current_count', 'N/A')}, "
            f"change={chats.get('percentage_change', 'N/A')}%\n"
            f"  Messages      : count={messages.get('current_count', 'N/A')}, "
            f"change={messages.get('percentage_change', 'N/A')}%\n"
            f"  Files         : count={files.get('current_count', 'N/A')}, "
            f"change={files.get('percentage_change', 'N/A')}%\n"
            f"  DataConnectors: count={dataconn.get('current_count', 'N/A')}, "
            f"change={dataconn.get('percentage_change', 'N/A')}%\n"
            f"    type_counts : {dataconn.get('type_counts', {})}\n"
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
