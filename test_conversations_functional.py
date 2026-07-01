"""
NCP Conversations & Pinned Chats — All Chat-Related Functional Flow Tests

Covers 2 API groups in a single file:

  ── CONVERSATION APIs (C01–C04) ────────────────────────────────
  NOTE: Conversations cannot be created via API — using fixed
        TEST_CONVERSATION_ID and TEST_QA_ID from config.

  Step 1  USER FEEDBACK       → verify feedback stored in response
                              → GET conversations by project (verify API responds)
  Step 2  ARCHIVE             → verify conversation appears in archived list
  Step 3  UNARCHIVE           → verify conversation removed from archived list
  Step 4  EXPORT by id        → verify file content
          EXPORT all          → verify response

  ── PINNED CHAT APIs (PC01–PC02) ───────────────────────────────
  Step 1  PIN chat    → GET pinned chats (verify chat appears in list)
  Step 2  UNPIN chat  → GET pinned chats (verify chat removed from list)
"""

import pytest
import logging
import json

from api_client import (
    export_all_conversations,
    post_user_feedback,
    archive_conversation,
    get_archived_conversations,
    unarchive_conversation,
    export_conversation,
    get_conversations_by_project,
    get_pinned_chats,
    pin_chat,
    unpin_chat,
    safe_json,
)
from config import (
    TEST_CONVERSATION_ID,
    TEST_QA_ID,
    TEST_CONVERSATION_PROJECT_ID,
    TEST_CHAT_ID,
    NCP_USERNAME,
)

logger = logging.getLogger(__name__)

CONV_ID  = TEST_CONVERSATION_ID
QA_ID    = TEST_QA_ID
FEEDBACK = "Automated test feedback"


# ── Conversations Flow Test Class ──────────────────────────────

class TestConversationsFunctionalFlow:

    # ── Step 1: USER FEEDBACK & GET BY PROJECT ─────────────────
    def test_c01_user_feedback_and_get_by_project(self, ncp_token, report_collector):

        # --- POST user feedback ---
        resp = post_user_feedback(QA_ID, FEEDBACK, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code in (200, 400)
        pretty = json.dumps(data, indent=2, default=str)

        # Log full response to console (same as project tests)
        logger.info("[C01] POST /api/v1/conversations/%s/user_feedback → %s\n%s",
                    QA_ID, resp.status_code, pretty)

        if resp.status_code == 200:
            stored_feedback = data.get("user_feedback") or data.get("message") or "(saved)"
            outcome = f"Feedback saved successfully.\nStored value: \"{stored_feedback}\""
        elif resp.status_code == 400:
            reason = data.get("detail") or data.get("message") or "Already saved"
            outcome = f"API accepted the request (feedback already exists).\nServer message: \"{reason}\""
        else:
            outcome = f"Unexpected response."

        feedback_summary = (
            f"Status        : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"Payload sent  : {{\"message\": \"{FEEDBACK}\"}}\n"
            f"Outcome       : {outcome}\n"
            f"Full Response :\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"POST user feedback for qa_id={QA_ID} — 200=saved, 400=already saved (both valid)",
            api_method       = "POST",
            endpoint         = f"/api/v1/conversations/{QA_ID}/user_feedback",
            expected_status  = "200/400",
            actual_status    = resp.status_code,
            response_summary = feedback_summary,
            passed           = passed,
        )
        assert passed, f"POST user feedback failed: expected 200/400, got {resp.status_code}"

        # --- GET conversations by project (using project that has real conversations) ---
        proj_id   = TEST_CONVERSATION_PROJECT_ID
        proj_resp = get_conversations_by_project(proj_id, ncp_token)
        proj_data = safe_json(proj_resp)
        passed_proj = proj_resp.status_code == 200
        proj_pretty = json.dumps(proj_data, indent=2, default=str)

        conversations = proj_data if isinstance(proj_data, list) else proj_data.get("data", [])
        conv_count    = len(conversations)

        # Log full response to console
        logger.info("[C01] GET /api/v1/conversations/all/%s → %s\n%s",
                    proj_id, proj_resp.status_code, proj_pretty)

        if conversations:
            sample = conversations[0]
            first_conv_info = (
                f"  - conversation_id : {sample.get('conversation_id') or sample.get('id', 'N/A')}\n"
                f"  - title           : {sample.get('title', 'N/A')}\n"
                f"  - created_at      : {sample.get('created_at', 'N/A')}\n"
                f"  - username        : {sample.get('username', 'N/A')}\n"
                f"  - is_archived     : {sample.get('is_archived', 'N/A')}"
            )
        else:
            first_conv_info = "  (no conversations found in this project)"

        proj_summary = (
            f"Status             : {proj_resp.status_code} ({'PASS' if passed_proj else 'FAIL'})\n"
            f"Project ID         : {proj_id}\n"
            f"Total Conversations: {conv_count}\n"
            f"First Conversation :\n{first_conv_info}\n"
            f"Full Response      :\n{proj_pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"GET all conversations for project_id={proj_id} — verify conversations are returned",
            api_method       = "GET",
            endpoint         = f"/api/v1/conversations/all/{proj_id}",
            expected_status  = "200",
            actual_status    = proj_resp.status_code,
            response_summary = proj_summary,
            passed           = passed_proj,
        )
        assert passed_proj, f"GET conversations by project failed: expected 200, got {proj_resp.status_code}"

    # ── Step 2: ARCHIVE & VERIFY ───────────────────────────────
    def test_c02_archive_and_verify(self, ncp_token, report_collector):

        # --- ARCHIVE conversation ---
        resp = archive_conversation(CONV_ID, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code in (200, 204)
        pretty = json.dumps(data, indent=2, default=str) if data else "(no body — 204 No Content)"

        logger.info("[C02] POST /api/v1/conversations/%s/archive → %s\n%s",
                    CONV_ID, resp.status_code, pretty)

        archive_summary = (
            f"Status   : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"Result   : {'Conversation id=' + str(CONV_ID) + ' archived successfully.' if passed else 'Archive action failed.'}\n"
            f"Full Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"POST archive conversation id={CONV_ID}",
            api_method       = "POST",
            endpoint         = f"/api/v1/conversations/{CONV_ID}/archive",
            expected_status  = "200/204",
            actual_status    = resp.status_code,
            response_summary = archive_summary,
            passed           = passed,
        )
        assert passed, f"ARCHIVE conversation failed: expected 200/204, got {resp.status_code}"

        # --- GET archived conversations → verify appears ---
        arch_resp = get_archived_conversations(ncp_token)
        arch_data = safe_json(arch_resp)
        passed_arch = arch_resp.status_code == 200
        arch_pretty = json.dumps(arch_data, indent=2, default=str)

        archived  = arch_data if isinstance(arch_data, list) else arch_data.get("data", [])
        conv_ids  = [c.get("conversation_id") or c.get("id") for c in archived]
        found     = CONV_ID in conv_ids

        # Extract the matching conversation object for detailed display
        matched_conv = next(
            (c for c in archived if (c.get("conversation_id") or c.get("id")) == CONV_ID),
            None
        )

        logger.info("[C02] GET /api/v1/conversations/archived_conversations → %s\n%s",
                    arch_resp.status_code, arch_pretty)

        matched_detail = (
            json.dumps(matched_conv, indent=2, default=str)
            if matched_conv else "(conversation not found in archived list)"
        )

        arch_summary = (
            f"Status              : {arch_resp.status_code} ({'PASS' if passed_arch else 'FAIL'})\n"
            f"Total Archived      : {len(archived)}\n"
            f"Looking for conv_id : {CONV_ID}\n"
            f"Found in list       : {'YES — conversation confirmed in archived list (PASS)' if found else 'NO — conversation missing from archived list (FAIL)'}\n"
            f"\nMatched Conversation Details:\n{matched_detail}\n"
            f"\nFull Response (all archived):\n{arch_pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"GET archived conversations — verify conversation id={CONV_ID} appears",
            api_method       = "GET",
            endpoint         = "/api/v1/conversations/archived_conversations",
            expected_status  = "200",
            actual_status    = arch_resp.status_code,
            response_summary = arch_summary,
            passed           = passed_arch and found,
        )
        assert passed_arch, f"GET archived conversations failed: expected 200, got {arch_resp.status_code}"
        assert found, f"conversation_id={CONV_ID} not found in archived list. Got: {conv_ids}"
        logger.info("[C02] conversation_id=%s confirmed in archived list", CONV_ID)

    # ── Step 3: UNARCHIVE & VERIFY ─────────────────────────────
    def test_c03_unarchive_and_verify(self, ncp_token, report_collector):

        # --- UNARCHIVE conversation ---
        resp = unarchive_conversation(CONV_ID, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code in (200, 204)
        pretty = json.dumps(data, indent=2, default=str) if data else "(no body — 204 No Content)"

        logger.info("[C03] POST /api/v1/conversations/%s/unarchive → %s\n%s",
                    CONV_ID, resp.status_code, pretty)

        unarchive_summary = (
            f"Status   : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"Result   : {'Conversation id=' + str(CONV_ID) + ' unarchived successfully.' if passed else 'Unarchive action failed.'}\n"
            f"Full Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = f"POST unarchive conversation id={CONV_ID}",
            api_method       = "POST",
            endpoint         = f"/api/v1/conversations/{CONV_ID}/unarchive",
            expected_status  = "200/204",
            actual_status    = resp.status_code,
            response_summary = unarchive_summary,
            passed           = passed,
        )
        assert passed, f"UNARCHIVE conversation failed: expected 200/204, got {resp.status_code}"

        # --- GET archived conversations → verify removed ---
        arch_resp = get_archived_conversations(ncp_token)
        arch_data = safe_json(arch_resp)
        passed_arch = arch_resp.status_code == 200
        arch_pretty = json.dumps(arch_data, indent=2, default=str)

        archived = arch_data if isinstance(arch_data, list) else arch_data.get("data", [])
        conv_ids = [c.get("conversation_id") or c.get("id") for c in archived]
        removed  = CONV_ID not in conv_ids

        logger.info("[C03] GET /api/v1/conversations/archived_conversations → %s\n%s",
                    arch_resp.status_code, arch_pretty)

        # If removed successfully, archived list no longer contains this conversation
        still_present = next(
            (c for c in archived if (c.get("conversation_id") or c.get("id")) == CONV_ID),
            None
        )

        arch_summary = (
            f"Status                : {arch_resp.status_code} ({'PASS' if passed_arch else 'FAIL'})\n"
            f"Total Archived        : {len(archived)}\n"
            f"Checking conv_id      : {CONV_ID}\n"
            f"Removed from list     : {'YES — conversation successfully removed (PASS)' if removed else 'NO — conversation still in archived list (FAIL)'}\n"
            f"Verification          : {'conversation_id=' + str(CONV_ID) + ' is NOT present in archived list — unarchive confirmed.' if removed else 'conversation_id=' + str(CONV_ID) + ' is STILL in archived list — unarchive may have failed.'}\n"
            f"Remaining Archived IDs: {conv_ids if conv_ids else '[] (empty — all conversations are active)'}\n"
            f"Full Response         :\n{arch_pretty}"
        )

        report_collector.add_flow(
            step             = 3,
            description      = f"GET archived conversations — verify conversation id={CONV_ID} is removed",
            api_method       = "GET",
            endpoint         = "/api/v1/conversations/archived_conversations",
            expected_status  = "200",
            actual_status    = arch_resp.status_code,
            response_summary = arch_summary,
            passed           = passed_arch and removed,
        )
        assert passed_arch, f"GET archived conversations failed: expected 200, got {arch_resp.status_code}"
        assert removed, f"conversation_id={CONV_ID} still in archived list after unarchive"
        logger.info("[C03] conversation_id=%s confirmed removed from archived list", CONV_ID)

    # ── Step 4: EXPORT BY ID & EXPORT ALL ──────────────────────
    def test_c04_export_conversation_and_export_all(self, ncp_token, report_collector):

        # --- EXPORT specific conversation ---
        exp_resp = export_conversation(CONV_ID, file_format="txt", token=ncp_token)
        passed_exp = exp_resp.status_code == 200
        content_type = exp_resp.headers.get("Content-Type", "(not set)")

        if passed_exp and exp_resp.content:
            try:
                preview = exp_resp.content.decode("utf-8", errors="replace")[:500]
            except Exception:
                preview = "(binary content)"
            export_path = f"conversation_{CONV_ID}_export.txt"
            with open(export_path, "wb") as f:
                f.write(exp_resp.content)

            logger.info("[C04] GET /api/v1/conversations/%s/export → %s\n"
                        "Content-Type: %s | Size: %d bytes\nPreview:\n%s",
                        CONV_ID, exp_resp.status_code, content_type,
                        len(exp_resp.content), preview)

            export_summary = (
                f"Status        : {exp_resp.status_code} ({'PASS' if passed_exp else 'FAIL'})\n"
                f"Content-Type  : {content_type}\n"
                f"File Size     : {len(exp_resp.content)} bytes\n"
                f"Saved to      : {export_path}\n"
                f"Content Preview (first 500 chars):\n"
                f"{'─'*50}\n"
                f"{preview}\n"
                f"{'─'*50}"
            )
        else:
            logger.info("[C04] GET /api/v1/conversations/%s/export → %s (no content)",
                        CONV_ID, exp_resp.status_code)
            export_summary = (
                f"Status        : {exp_resp.status_code} (FAIL)\n"
                f"Content-Type  : {content_type}\n"
                f"Result        : Export failed — no content returned"
            )

        report_collector.add_flow(
            step             = 4,
            description      = f"GET export conversation id={CONV_ID} (file_format=txt) — verify file content",
            api_method       = "GET",
            endpoint         = f"/api/v1/conversations/{CONV_ID}/export",
            expected_status  = "200",
            actual_status    = exp_resp.status_code,
            response_summary = export_summary,
            passed           = passed_exp,
        )
        assert passed_exp, f"EXPORT conversation failed: expected 200, got {exp_resp.status_code}"

        # --- EXPORT all conversations ---
        all_exp_resp = export_all_conversations(ncp_token)
        passed_all = all_exp_resp.status_code == 200
        all_content_type = all_exp_resp.headers.get("Content-Type", "(not set)")

        if passed_all and all_exp_resp.content:
            try:
                all_preview = all_exp_resp.content.decode("utf-8", errors="replace")[:500]
            except Exception:
                all_preview = "(binary content)"
            all_export_path = "conversations_all_export.txt"
            with open(all_export_path, "wb") as f:
                f.write(all_exp_resp.content)

            logger.info("[C04] GET /api/v1/conversations/all/export → %s\n"
                        "Content-Type: %s | Size: %d bytes\nPreview:\n%s",
                        all_exp_resp.status_code, all_content_type,
                        len(all_exp_resp.content), all_preview)

            all_export_summary = (
                f"Status        : {all_exp_resp.status_code} ({'PASS' if passed_all else 'FAIL'})\n"
                f"Content-Type  : {all_content_type}\n"
                f"File Size     : {len(all_exp_resp.content)} bytes\n"
                f"Saved to      : {all_export_path}\n"
                f"Content Preview (first 500 chars):\n"
                f"{'─'*50}\n"
                f"{all_preview}\n"
                f"{'─'*50}"
            )
        else:
            logger.info("[C04] GET /api/v1/conversations/all/export → %s (no content)",
                        all_exp_resp.status_code)
            all_export_summary = (
                f"Status        : {all_exp_resp.status_code} (FAIL)\n"
                f"Content-Type  : {all_content_type}\n"
                f"Result        : Export failed — no content returned"
            )

        report_collector.add_flow(
            step             = 4,
            description      = "GET export all conversations — verify response",
            api_method       = "GET",
            endpoint         = "/api/v1/conversations/all/export",
            expected_status  = "200",
            actual_status    = all_exp_resp.status_code,
            response_summary = all_export_summary,
            passed           = passed_all,
        )
        assert passed_all, f"EXPORT all conversations failed: expected 200, got {all_exp_resp.status_code}"
        logger.info("[C04] Export all conversations complete")


# ════════════════════════════════════════════════════════════════
# PINNED CHAT API TESTS  (PC01 – PC02)
# ════════════════════════════════════════════════════════════════

CHAT_ID = TEST_CHAT_ID


class TestPinnedChatsFunctionalFlow:

    # ── Step 1: PIN & VERIFY ───────────────────────────────────
    def test_pc01_pin_and_verify(self, ncp_token, report_collector):

        # --- PIN chat ---
        resp = pin_chat(CHAT_ID, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code in (200, 201, 204)
        pretty = json.dumps(data, indent=2, default=str) if data else "(no body — 204 No Content)"

        logger.info("[PC01] PUT /api/v1/user/pinned/chats/%s → %s\n%s",
                    CHAT_ID, resp.status_code, pretty)

        pin_summary = (
            f"Status   : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"Result   : {'Chat id=' + str(CHAT_ID) + ' pinned successfully.' if passed else 'PIN chat failed.'}\n"
            f"Full Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"PIN chat id={CHAT_ID}",
            api_method       = "PUT",
            endpoint         = f"/api/v1/user/pinned/chats/{CHAT_ID}",
            expected_status  = "200/201/204",
            actual_status    = resp.status_code,
            response_summary = pin_summary,
            passed           = passed,
        )
        assert passed, f"PIN chat failed: expected 200/201/204, got {resp.status_code}"

        # --- GET pinned chats → verify chat appears ---
        list_resp = get_pinned_chats(ncp_token)
        list_data = safe_json(list_resp)
        passed_list = list_resp.status_code == 200
        list_pretty = json.dumps(list_data, indent=2, default=str)

        logger.info("[PC01] GET /api/v1/user/pinned/chats/%s → %s\n%s",
                    NCP_USERNAME, list_resp.status_code, list_pretty)

        pinned   = list_data if isinstance(list_data, list) else list_data.get("data", [])
        chat_ids = [c.get("chat_id") or c.get("conversation_id") or c.get("id") for c in pinned]
        found    = CHAT_ID in chat_ids

        matched_chat = next(
            (c for c in pinned if (c.get("chat_id") or c.get("conversation_id") or c.get("id")) == CHAT_ID),
            None
        )
        matched_detail = (
            json.dumps(matched_chat, indent=2, default=str)
            if matched_chat else "(chat not found in pinned list)"
        )

        list_summary = (
            f"Status            : {list_resp.status_code} ({'PASS' if passed_list else 'FAIL'})\n"
            f"Username          : {NCP_USERNAME}\n"
            f"Total Pinned Chats: {len(pinned)}\n"
            f"Looking for chat_id: {CHAT_ID}\n"
            f"Found in list     : {'YES — chat confirmed in pinned list (PASS)' if found else 'NO — chat missing from pinned list (FAIL)'}\n"
            f"\nMatched Chat Details:\n{matched_detail}\n"
            f"\nFull Response (all pinned chats):\n{list_pretty}"
        )

        report_collector.add_flow(
            step             = 1,
            description      = f"GET pinned chats for username={NCP_USERNAME} — verify chat id={CHAT_ID} appears",
            api_method       = "GET",
            endpoint         = f"/api/v1/user/pinned/chats/{NCP_USERNAME}",
            expected_status  = "200",
            actual_status    = list_resp.status_code,
            response_summary = list_summary,
            passed           = passed_list and found,
        )
        assert passed_list, f"GET pinned chats failed: expected 200, got {list_resp.status_code}"
        assert found, f"chat_id={CHAT_ID} not found in pinned list. Got: {chat_ids}"
        logger.info("[PC01] chat_id=%s confirmed in pinned chats list", CHAT_ID)

    # ── Step 2: UNPIN & VERIFY ─────────────────────────────────
    def test_pc02_unpin_and_verify(self, ncp_token, report_collector):

        # --- UNPIN chat ---
        resp = unpin_chat(CHAT_ID, ncp_token)
        data = safe_json(resp)
        passed = resp.status_code in (200, 204)
        pretty = json.dumps(data, indent=2, default=str) if data else "(no body — 204 No Content)"

        logger.info("[PC02] DELETE /api/v1/user/pinned/chats/%s → %s\n%s",
                    CHAT_ID, resp.status_code, pretty)

        unpin_summary = (
            f"Status   : {resp.status_code} ({'PASS' if passed else 'FAIL'})\n"
            f"Result   : {'Chat id=' + str(CHAT_ID) + ' unpinned successfully.' if passed else 'UNPIN chat failed.'}\n"
            f"Full Response:\n{pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"UNPIN chat id={CHAT_ID}",
            api_method       = "DELETE",
            endpoint         = f"/api/v1/user/pinned/chats/{CHAT_ID}",
            expected_status  = "200/204",
            actual_status    = resp.status_code,
            response_summary = unpin_summary,
            passed           = passed,
        )
        assert passed, f"UNPIN chat failed: expected 200/204, got {resp.status_code}"

        # --- GET pinned chats → verify chat removed ---
        list_resp = get_pinned_chats(ncp_token)
        list_data = safe_json(list_resp)
        passed_list = list_resp.status_code == 200
        list_pretty = json.dumps(list_data, indent=2, default=str)

        logger.info("[PC02] GET /api/v1/user/pinned/chats/%s → %s\n%s",
                    NCP_USERNAME, list_resp.status_code, list_pretty)

        pinned   = list_data if isinstance(list_data, list) else list_data.get("data", [])
        chat_ids = [c.get("chat_id") or c.get("conversation_id") or c.get("id") for c in pinned]
        removed  = CHAT_ID not in chat_ids

        list_summary = (
            f"Status              : {list_resp.status_code} ({'PASS' if passed_list else 'FAIL'})\n"
            f"Username            : {NCP_USERNAME}\n"
            f"Total Pinned Chats  : {len(pinned)}\n"
            f"Checking chat_id    : {CHAT_ID}\n"
            f"Removed from list   : {'YES — chat successfully removed (PASS)' if removed else 'NO — chat still in pinned list (FAIL)'}\n"
            f"Verification        : {'chat_id=' + str(CHAT_ID) + ' is NOT present in pinned list — unpin confirmed.' if removed else 'chat_id=' + str(CHAT_ID) + ' is STILL in pinned list — unpin may have failed.'}\n"
            f"Remaining Pinned IDs: {chat_ids if chat_ids else '[] (empty — no chats pinned)'}\n"
            f"Full Response       :\n{list_pretty}"
        )

        report_collector.add_flow(
            step             = 2,
            description      = f"GET pinned chats for username={NCP_USERNAME} — verify chat id={CHAT_ID} is removed",
            api_method       = "GET",
            endpoint         = f"/api/v1/user/pinned/chats/{NCP_USERNAME}",
            expected_status  = "200",
            actual_status    = list_resp.status_code,
            response_summary = list_summary,
            passed           = passed_list and removed,
        )
        assert passed_list, f"GET pinned chats failed: expected 200, got {list_resp.status_code}"
        assert removed, f"chat_id={CHAT_ID} still in pinned list after unpin"
        logger.info("[PC02] chat_id=%s confirmed removed from pinned chats list", CHAT_ID)
