#!/usr/bin/env python3
"""
get_websocket_response.py

Reads prompts from an input .txt file (one prompt per line) and fetches
WebSocket responses for each prompt from the LLM via the NCP WebSocket API.

Usage:
    python get_websocket_response.py --input prompts.txt [--output responses.txt]
                                     [--uri wss://10.4.5.10:9001/api/v1/ws]
                                     [--timeout 120]

Output:
    For each prompt, prints and optionally saves:
        - The prompt text
        - The full LLM response
        - Execution time
"""

import argparse
import asyncio
import json
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3
import websockets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_WS_URI   = "wss://10.4.5.10:9001/api/v1/ws"
LOGIN_URL        = "https://10.4.5.10/api/user/login"
USERNAME         = "superadmin"
PASSWORD         = "Admin@123"


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────

def get_jwt_token() -> str:
    """Fetch a JWT token from the NCP login endpoint."""
    payload = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(LOGIN_URL, json=payload, verify=False)
    response.raise_for_status()
    return response.json()["data"]["token"]


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET HANDLER
# ─────────────────────────────────────────────────────────────────────────────

async def handle_single_conversation(
    uri: str, question: str, timeout: int = 120
) -> tuple[str, float]:
    """
    Opens a WebSocket connection, authenticates, starts a conversation,
    sends the prompt, and collects the full streaming response.

    Returns (response_text, execution_time_seconds).
    """
    start_time = datetime.now()

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    response_str = ""
    message_count = 0
    inactivity_timeout = 30

    try:
        async with websockets.connect(uri, ssl=ssl_ctx, open_timeout=20) as websocket:
            print(f"  [WS] Connected")

            # Step 1: Receive connection_id
            raw = await asyncio.wait_for(websocket.recv(), timeout=10)
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return "Error: Malformed initial JSON response", _elapsed(start_time)

            if data.get("type") != "connection_id":
                return (
                    f"Error: Expected connection_id, got {data.get('type')}",
                    _elapsed(start_time),
                )
            connection_id = data.get("client_id")

            # Step 2: Send auth
            token = get_jwt_token()
            await websocket.send(json.dumps({"type": "auth", "token": token}))

            # Step 3: Wait for auth_success
            raw = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(raw)
            if data.get("type") != "auth_success":
                return (
                    f"Error: Authentication failed - {data.get('type')}",
                    _elapsed(start_time),
                )
            print(f"  [WS] Authenticated")

            # Step 4: Skip optional conversations_loaded message
            try:
                await asyncio.wait_for(websocket.recv(), timeout=5)
            except asyncio.TimeoutError:
                pass

            # Step 5: Send new_conversation
            conversation_payload = {
                "type": "new_conversation",
                "conversation": {
                    "id": None,
                    "username": USERNAME,
                    "title": question,
                    "messages": [],
                    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                },
                "connection_id": connection_id,
                "mentioned_users": "",
            }
            await websocket.send(json.dumps(conversation_payload))

            # Step 6: Wait for conversation_id
            conversation_id = None
            for _ in range(10):
                try:
                    raw = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(raw)
                    if "conversation_id" in data:
                        conversation_id = data["conversation_id"]
                        break
                    if isinstance(data.get("conversation"), dict) and "id" in data["conversation"]:
                        conversation_id = data["conversation"]["id"]
                        break
                except (asyncio.TimeoutError, json.JSONDecodeError):
                    continue

            if not conversation_id:
                return "Error: No conversation_id received", _elapsed(start_time)

            print(f"  [WS] Conversation ID: {conversation_id}")

            # Step 7: Send the prompt
            await websocket.send(json.dumps({
                "type": "new_message",
                "conversation_id": conversation_id,
                "message": question,
                "username": USERNAME,
            }))
            print(f"  [WS] Prompt sent, waiting for response...")

            # Step 8: Collect streaming response
            message_ended = False
            last_activity = datetime.now()

            while not message_ended:
                try:
                    raw = await asyncio.wait_for(
                        websocket.recv(), timeout=min(inactivity_timeout, timeout)
                    )
                    last_activity = datetime.now()
                    message_count += 1

                    if message_count % 50 == 0:
                        print(f"  [WS] {message_count} chunks, {len(response_str)} chars so far...")

                except asyncio.TimeoutError:
                    if (datetime.now() - last_activity).total_seconds() >= (inactivity_timeout - 1):
                        print(f"  [WS] Inactivity timeout — response assumed complete")
                        break
                    return "Error: Server response timed out", _elapsed(start_time)

                except websockets.ConnectionClosed:
                    print(f"  [WS] Connection closed — response assumed complete")
                    break

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")

                if msg_type == "agent_llm_stream":
                    response_str += data.get("chunk", "")

                elif msg_type == "new_streaming_message_content":
                    response_str += data.get("content", "")

                elif msg_type == "new_message":
                    for content in data.get("message", {}).get("contents", []):
                        ctype = content.get("content_type")
                        if ctype == "TEXT":
                            response_str += content.get("content", "")
                        elif ctype == "IMAGE":
                            response_str += f"[IMAGE: {content.get('data', '')[:80]}...]\n"
                        elif ctype == "REPORT":
                            response_str += data.get("content", "")

                elif msg_type == "new_content":
                    ctype = data.get("content_type")
                    if ctype == "TEXT":
                        response_str += data.get("content", "")
                    elif ctype == "IMAGE":
                        response_str += f"[IMAGE: {data.get('data', '')[:80]}...]\n"
                    else:
                        response_str += f"[{ctype} CONTENT]\n"

                elif msg_type in ("agent_completed", "agent_stopped", "end_message"):
                    print(f"  [WS] End signal '{msg_type}' received after {message_count} chunks")
                    message_ended = True

                elif msg_type == "error":
                    return (
                        f"Error: {data.get('message', 'Unknown WebSocket error')}",
                        _elapsed(start_time),
                    )

    except Exception as exc:
        return f"Error: WebSocket connection failed - {exc}", _elapsed(start_time)

    exec_time = _elapsed(start_time)
    final = response_str if response_str else "Error: No response content received"
    print(f"  [WS] Done — {len(final)} chars, {exec_time:.1f}s")
    return final, exec_time


def _elapsed(start: datetime) -> float:
    return (datetime.now() - start).total_seconds()


# ─────────────────────────────────────────────────────────────────────────────
# INPUT / OUTPUT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def read_prompts(path: str) -> list[str]:
    """Read non-empty lines from a text file as prompts."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def write_output(path: str, results: list[dict]) -> None:
    """Write results to a text file."""
    with open(path, "w", encoding="utf-8") as f:
        for i, r in enumerate(results, 1):
            f.write(f"{'='*70}\n")
            f.write(f"Prompt {i}: {r['prompt']}\n")
            f.write(f"{'─'*70}\n")
            f.write(f"Response:\n{r['response']}\n")
            f.write(f"\nExecution Time: {r['execution_time']:.2f}s\n")
            f.write(f"{'='*70}\n\n")
    print(f"\nResults written to: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main_async(args: argparse.Namespace) -> None:
    prompts = read_prompts(args.input)
    if not prompts:
        print("No prompts found in input file.")
        sys.exit(1)

    print(f"Loaded {len(prompts)} prompt(s) from '{args.input}'")
    print(f"WebSocket URI: {args.uri}\n")

    results = []

    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        response, exec_time = await handle_single_conversation(
            uri=args.uri,
            question=prompt,
            timeout=args.timeout,
        )
        results.append({
            "prompt": prompt,
            "response": response,
            "execution_time": exec_time,
        })

        # Print to console
        print(f"\n  Response:\n{response}\n")
        print(f"  Execution time: {exec_time:.2f}s")

    if args.output:
        write_output(args.output, results)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch WebSocket LLM responses for prompts listed in a .txt file."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input .txt file (one prompt per line)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Optional path to save results (text file)",
    )
    parser.add_argument(
        "--uri",
        default=DEFAULT_WS_URI,
        help=f"WebSocket URI (default: {DEFAULT_WS_URI})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Per-prompt timeout in seconds (default: 120)",
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
