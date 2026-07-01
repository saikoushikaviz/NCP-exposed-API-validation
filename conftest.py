"""
NCP Projects API - Pytest Fixtures & Hooks
"""

import time
import logging
import pytest

from config import LOG_LEVEL, LOG_FORMAT
from api_client import get_ncp_token, create_project, delete_project, get_projects, safe_json
from report_generator import ReportCollector, generate_report

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


# ── Auth ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def ncp_token():
    """Authenticate once and share the JWT token across all tests."""
    token = get_ncp_token()
    assert token, "NCP authentication failed — no JWT token returned"
    logger.info("NCP JWT token acquired for test session")
    return token


# ── Report collector (session-wide) ───────────────────────────

@pytest.fixture(scope="session")
def report_collector():
    """Single ReportCollector instance shared by all tests."""
    return ReportCollector()


# ── Shared flow state (session-wide dict) ─────────────────────

@pytest.fixture(scope="session")
def flow_state():
    """Mutable dict for passing state between functional flow steps."""
    return {}


# ── Baseline project: created fresh each session ──────────────
# Used by functional flow (archive/unarchive/download steps).

@pytest.fixture(scope="session")
def baseline_project_id(ncp_token, _test_project_tracker):
    """Create a dedicated project for archive/unarchive/download tests."""
    payload = {"name": "NCP-Baseline-Test", "description": "Baseline project for API tests",
               "org_id": 0, "username": "superadmin"}
    resp = create_project(payload, ncp_token)
    project_id = safe_json(resp).get("project_id")
    assert project_id, "Could not create baseline project"
    _test_project_tracker.append(project_id)
    logger.info("Baseline project created: id=%s", project_id)
    return project_id


# ── Tracker: any project created by tests gets registered here ─

@pytest.fixture(scope="session")
def _test_project_tracker():
    """List of project_ids created during this session — cleaned up at end."""
    return []


# ── Session-end cleanup: delete all test-created projects ──────

@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_projects(ncp_token, _test_project_tracker):
    """Delete every project created during the test session."""
    yield
    # Sweep for any leftover projects with test prefixes from old runs
    try:
        all_resp = get_projects(ncp_token)
        all_projects = safe_json(all_resp)
        if isinstance(all_projects, list):
            TEST_PREFIXES = ("Flow-", "Auto-Test-", "Automation Test",
                             "Automation Report", "NCP-Baseline-Test")
            stale = [
                p["project_id"] for p in all_projects
                if any(p.get("name", "").startswith(pfx) for pfx in TEST_PREFIXES)
            ]
            for pid in stale:
                if pid not in _test_project_tracker:
                    _test_project_tracker.append(pid)
    except Exception:
        pass

    for pid in _test_project_tracker:
        try:
            delete_project(pid, ncp_token)
            logger.info("Cleaned up test project id=%s", pid)
        except Exception:
            pass


# ── Report generation after session ends ──────────────────────

def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    collector = session.config._ncp_report_collector
    if collector is None:
        return
    try:
        path = generate_report(collector, output_dir=".")
        print(f"\n{'='*60}")
        print(f"  NCP API Report saved to: {path}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"\nWarning: Could not generate report — {e}\n")


def pytest_configure(config):
    """Store collector on config so pytest_sessionfinish can access it."""
    config._ncp_report_collector = None


@pytest.fixture(scope="session", autouse=True)
def _register_collector(report_collector, pytestconfig):
    """Wire the collector into pytest config for the finish hook."""
    pytestconfig._ncp_report_collector = report_collector
    yield


# ── Playwright browser context: ignore self-signed cert ───────

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Allow Playwright to connect to the NCP server without SSL errors."""
    return {**browser_context_args, "ignore_https_errors": True}
