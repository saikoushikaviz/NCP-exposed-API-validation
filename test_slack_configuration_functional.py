"""
NCP Slack Configuration API — Functional Flow Tests

Covers the 5 Slack Configuration endpoints (SC01 – SC05), happy path only:

  ── SC01: CREATE ────────────────────────────────────────────────
  Step 1  POST /api/v1/slack_configuration/create
          body: {webhookURL, channelName, channelId}
          → verify a config is created; capture its id.

  ── SC02: GET ALL ───────────────────────────────────────────────
  Step 2  GET /api/v1/slack_configuration/get_all
          → verify JSON array, schema keys, created config present.

  ── SC03: CHANNELS (FE picker) ──────────────────────────────────
  Step 3  GET /api/v1/slack_configuration/channels
          → verify {channel, channel_id} entries and that webhook_url is NOT
            exposed here.

  ── SC04: UPDATE ────────────────────────────────────────────────
  Step 4  PUT /api/v1/slack_configuration/update/{id}
          → verify the edited fields are reflected.

  ── SC05: DELETE ────────────────────────────────────────────────
  Step 5  DELETE /api/v1/slack_configuration/delete/{id}
          → verify deletion confirmation, then confirm it is gone.

Notes:
  • The POST/PUT bodies are raw JSON (no pydantic model), using the documented
    camelCase names (webhookURL/channelName/channelId). Stored/returned fields
    are snake_case (webhook_url/channel/channel_id).
  • create/update store the value verbatim (no live Slack call) — a placeholder
    webhook is fine, no real secret required.
  • This API currently returns HTTP 200 for every outcome, so these tests
    assert on the RESPONSE BODY (id present, fields echoed), not on the status
    code alone. (Negative/error-handling defects are tracked separately, not
    in this happy-path suite.)
"""

import pytest
import logging
import json

from api_client import (
    create_slack_config,
    get_all_slack_configs,
    get_slack_channels,
    update_slack_config,
    delete_slack_config,
    safe_json,
)
from config import (
    TEST_SLACK_WEBHOOK_URL,
    TEST_SLACK_CHANNEL_NAME,
    TEST_SLACK_CHANNEL_ID,
    TEST_SLACK_UPDATE_WEBHOOK_URL,
    TEST_SLACK_UPDATE_CHANNEL_NAME,
)

logger = logging.getLogger(__name__)


def _embedded_error(data):
    """True if the body embeds a >=400 status_code (the API's 200-wrapping-error pattern)."""
    return isinstance(data, dict) and isinstance(data.get("status_code"), int) and data["status_code"] >= 400


# ════════════════════════════════════════════════════════════════
# SLACK CONFIGURATION FUNCTIONAL FLOW  (SC01 – SC05)
# ════════════════════════════════════════════════════════════════

class TestSlackConfigurationFunctionalFlow:

    # Captured by SC01 (create) so later steps operate on a real config.
    created_config_id = None

    # ── Step 1: CREATE ─────────────────────────────────────────
    def test_sc01_create(self, ncp_token, report_collector):
        resp = create_slack_config(
            webhook_url  = TEST_SLACK_WEBHOOK_URL,
            channel_name = TEST_SLACK_CHANNEL_NAME,
            channel_id   = TEST_SLACK_CHANNEL_ID,
            token        = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[SC01] POST /api/v1/slack_configuration/create → %s\n%s",
                    resp.status_code, pretty)

        config_id     = data.get("id") if isinstance(data, dict) else None
        no_error      = isinstance(data, dict) and not _embedded_error(data)
        has_id        = config_id is not None
        channel_match = isinstance(data, dict) and data.get("channel") == TEST_SLACK_CHANNEL_NAME
        chanid_match  = isinstance(data, dict) and data.get("channel_id") == TEST_SLACK_CHANNEL_ID
        webhook_match = isinstance(data, dict) and data.get("webhook_url") == TEST_SLACK_WEBHOOK_URL

        if has_id:
            TestSlackConfigurationFunctionalFlow.created_config_id = config_id

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  channelName  : {TEST_SLACK_CHANNEL_NAME}\n"
            f"  channelId    : {TEST_SLACK_CHANNEL_ID}\n"
            f"\nResult:\n"
            f"  id           : {config_id} {'✓' if has_id else '✗'}\n"
            f"  no error body: {'YES' if no_error else 'NO'}\n"
            f"  channel match: {'YES' if channel_match else 'NO'}\n"
            f"  channel_id   : {'YES' if chanid_match else 'NO'}\n"
            f"  webhook_url  : {'YES' if webhook_match else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = (
                "POST create slack configuration — verify a config is created (id "
                "returned, fields echoed, no embedded error)"
            ),
            api_method       = "POST",
            endpoint         = "/api/v1/slack_configuration/create",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and no_error and has_id and channel_match and chanid_match and webhook_match,
        )

        assert passed,        f"CREATE slack config failed: expected 200, got {resp.status_code}"
        assert no_error,      f"CREATE returned an embedded error body: {data}"
        assert has_id,        "CREATE response missing 'id'"
        assert channel_match, f"channelName not echoed as 'channel': {data.get('channel')!r}"
        assert chanid_match,  f"channelId not echoed as 'channel_id': {data.get('channel_id')!r}"
        assert webhook_match, "webhookURL not stored as 'webhook_url'"
        logger.info("[SC01] slack config created — id=%s", config_id)

    # ── Step 2: GET ALL ────────────────────────────────────────
    def test_sc02_get_all(self, ncp_token, report_collector):
        resp = get_all_slack_configs(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200

        pretty = json.dumps(data, indent=2, default=str)
        pretty_capped = pretty if len(pretty) <= 8000 else pretty[:8000] + "\n... (truncated)"

        configs = data if isinstance(data, list) else []
        is_list = isinstance(data, list)

        required_keys = ("id", "channel", "channel_id", "webhook_url", "created_at", "updated_at")
        schema_ok = is_list and all(
            isinstance(c, dict) and all(k in c for k in required_keys) for c in configs
        )
        created_id    = TestSlackConfigurationFunctionalFlow.created_config_id
        created_found = created_id in {c.get("id") for c in configs} if created_id else None

        logger.info("[SC02] GET /api/v1/slack_configuration/get_all → %s (configs=%d)",
                    resp.status_code, len(configs))

        summary = (
            f"Status          : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  configs returned: {len(configs)}\n"
            f"  body is a list  : {'YES (PASS)' if is_list else 'NO (FAIL)'}\n"
            f"  schema keys ok  : {'YES (PASS)' if schema_ok else 'NO (FAIL)'}\n"
            f"  created id '{created_id}': "
            f"{'FOUND' if created_found else ('MISSING' if created_id else 'n/a')}\n"
            f"\nResponse (capped):\n{pretty_capped}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = (
                "GET all slack configs — verify JSON array, schema keys present, "
                "created config present"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/slack_configuration/get_all",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and is_list and schema_ok,
        )

        assert passed,    f"GET all slack configs failed: expected 200, got {resp.status_code}"
        assert is_list,   "get_all did not return a JSON array"
        assert schema_ok, f"one or more configs missing keys {required_keys}"
        if created_id:
            assert created_found, f"created config {created_id} not present in get_all"
        logger.info("[SC02] %d slack config(s) returned", len(configs))

    # ── Step 3: CHANNELS (FE picker) ───────────────────────────
    def test_sc03_channels(self, ncp_token, report_collector):
        resp = get_slack_channels(ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[SC03] GET /api/v1/slack_configuration/channels → %s\n%s",
                    resp.status_code, pretty)

        channels = data if isinstance(data, list) else []
        is_list  = isinstance(data, list)
        shape_ok = is_list and all(
            isinstance(c, dict) and "channel" in c and "channel_id" in c for c in channels
        )
        # Security: the picker view must NOT leak the webhook.
        no_webhook = is_list and all("webhook_url" not in c for c in channels)

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nResult:\n"
            f"  channels      : {len(channels)}\n"
            f"  body is a list: {'YES (PASS)' if is_list else 'NO (FAIL)'}\n"
            f"  channel/channel_id keys: {'YES (PASS)' if shape_ok else 'NO (FAIL)'}\n"
            f"  webhook hidden: {'YES (PASS)' if no_webhook else 'NO (FAIL — leaked!)'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = (
                "GET slack channels (FE picker) — verify {channel, channel_id} entries "
                "and webhook_url is NOT exposed"
            ),
            api_method       = "GET",
            endpoint         = "/api/v1/slack_configuration/channels",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and is_list and shape_ok and no_webhook,
        )

        assert passed,     f"GET slack channels failed: expected 200, got {resp.status_code}"
        assert is_list,    "channels did not return a JSON array"
        assert shape_ok,   "channels entries missing channel/channel_id"
        assert no_webhook, "SECURITY: webhook_url must not be exposed by /channels"
        logger.info("[SC03] %d channel(s) returned", len(channels))

    # ── Step 4: UPDATE ─────────────────────────────────────────
    def test_sc04_update(self, ncp_token, report_collector):
        config_id = TestSlackConfigurationFunctionalFlow.created_config_id
        if config_id is None:
            pytest.skip("SC01 did not create a config (no id captured) — skipping UPDATE")

        resp = update_slack_config(
            config_id    = config_id,
            webhook_url  = TEST_SLACK_UPDATE_WEBHOOK_URL,
            channel_name = TEST_SLACK_UPDATE_CHANNEL_NAME,
            channel_id   = TEST_SLACK_CHANNEL_ID,
            token        = ncp_token,
        )
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[SC04] PUT /api/v1/slack_configuration/update/%s → %s\n%s",
                    config_id, resp.status_code, pretty)

        no_error      = isinstance(data, dict) and not _embedded_error(data)
        id_match      = isinstance(data, dict) and str(data.get("id")) == str(config_id)
        channel_upd   = isinstance(data, dict) and data.get("channel") == TEST_SLACK_UPDATE_CHANNEL_NAME
        webhook_upd   = isinstance(data, dict) and data.get("webhook_url") == TEST_SLACK_UPDATE_WEBHOOK_URL

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest (PUT):\n"
            f"  id           : {config_id}\n"
            f"  channelName  : {TEST_SLACK_UPDATE_CHANNEL_NAME}\n"
            f"\nResult:\n"
            f"  no error body: {'YES' if no_error else 'NO'}\n"
            f"  id match     : {'YES' if id_match else 'NO'}\n"
            f"  channel updated: {'YES' if channel_upd else 'NO'}\n"
            f"  webhook updated: {'YES' if webhook_upd else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 4,
            description      = (
                f"PUT update slack config {config_id} — verify edited channel/webhook "
                f"reflected in the response"
            ),
            api_method       = "PUT",
            endpoint         = "/api/v1/slack_configuration/update/{config_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and no_error and id_match and channel_upd and webhook_upd,
        )

        assert passed,      f"UPDATE slack config failed: expected 200, got {resp.status_code}"
        assert no_error,    f"UPDATE returned an embedded error body: {data}"
        assert id_match,    f"UPDATE returned a different id: {data.get('id')}"
        assert channel_upd, f"channel not updated: {data.get('channel')!r}"
        assert webhook_upd, "webhook_url not updated"
        logger.info("[SC04] slack config %s updated", config_id)

    # ── Step 5: DELETE ─────────────────────────────────────────
    def test_sc05_delete(self, ncp_token, report_collector):
        config_id = TestSlackConfigurationFunctionalFlow.created_config_id
        if config_id is None:
            pytest.skip("SC01 did not create a config (no id captured) — skipping DELETE")

        resp = delete_slack_config(config_id, ncp_token)
        data   = safe_json(resp)
        passed = resp.status_code == 200
        pretty = json.dumps(data, indent=2, default=str)

        logger.info("[SC05] DELETE /api/v1/slack_configuration/delete/%s → %s\n%s",
                    config_id, resp.status_code, pretty)

        confirmed = isinstance(data, dict) and "deleted" in str(data.get("msg", "")).lower()

        # Confirm it's gone from get_all.
        remaining = safe_json(get_all_slack_configs(ncp_token))
        ids = {c.get("id") for c in remaining if isinstance(c, dict)} if isinstance(remaining, list) else set()
        gone = config_id not in ids

        summary = (
            f"Status         : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"\nRequest:\n"
            f"  id           : {config_id}\n"
            f"\nResult:\n"
            f"  delete confirmed: {'YES' if confirmed else 'NO'} (msg={data.get('msg') if isinstance(data, dict) else None!r})\n"
            f"  gone from get_all: {'YES' if gone else 'NO'}\n"
            f"\nFull Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 5,
            description      = (
                f"DELETE slack config {config_id} — verify deletion confirmation and that "
                f"it is gone from get_all"
            ),
            api_method       = "DELETE",
            endpoint         = "/api/v1/slack_configuration/delete/{config_id}",
            expected_status  = "200",
            actual_status    = resp.status_code,
            response_summary = summary,
            passed           = passed and confirmed and gone,
        )

        assert passed,    f"DELETE slack config failed: expected 200, got {resp.status_code}"
        assert confirmed, f"unexpected delete response: {data}"
        assert gone,      f"config {config_id} still present after delete"
        TestSlackConfigurationFunctionalFlow.created_config_id = None
        logger.info("[SC05] slack config %s deleted", config_id)
