#!/usr/bin/env python3
"""session2doc: Parse Claude Code session history and manage mark state."""

import json
import sys
import os


def locate_last(session_file):
    """Find the last user+assistant conversation pair's uuids in the session file."""
    messages = []
    with open(session_file) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("type") in ("user", "assistant"):
                messages.append(obj)

    # Find the last assistant, then the nearest user before it
    last_assistant = None
    last_user = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["type"] == "assistant" and last_assistant is None:
            last_assistant = messages[i]
        elif messages[i]["type"] == "user" and last_assistant is not None:
            last_user = messages[i]
            break

    if not last_user or not last_assistant:
        print(json.dumps({"error": "no conversation pair found"}))
        sys.exit(1)

    print(json.dumps({
        "user_uuid": last_user["uuid"],
        "assistant_uuid": last_assistant["uuid"],
        "timestamp": last_user.get("timestamp", "")
    }))


def add_mark(state_file, desc, user_uuid, assistant_uuid):
    """Add a conversation pair's uuids to the specified desc group."""
    state = {"marks": {}, "recording": {"active": False, "start_uuid": None, "start_timestamp": None}}
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)

    if desc not in state["marks"]:
        state["marks"][desc] = []

    state["marks"][desc].append({
        "user_uuid": user_uuid,
        "assistant_uuid": assistant_uuid
    })

    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(json.dumps({"status": "ok", "desc": desc, "count": len(state["marks"][desc])}))


def begin_recording(state_file, last_uuid):
    """Start recording mode, save the starting uuid."""
    state = {"marks": {}, "recording": {"active": False, "start_uuid": None, "start_timestamp": None}}
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)

    state["recording"] = {"active": True, "start_uuid": last_uuid}

    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(json.dumps({"status": "ok", "start_uuid": last_uuid}))


def extract_text(message):
    """Extract plain text from message.content."""
    content = message.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block["text"])
        return "\n".join(texts)
    return ""


def extract_marks(state_file, session_file, desc):
    """Extract all marked conversation content for the specified desc group."""
    with open(state_file) as f:
        state = json.load(f)

    marks = state.get("marks", {}).get(desc, [])
    if not marks:
        print(json.dumps({"error": f"no marks found for '{desc}'"}))
        sys.exit(1)

    msg_by_uuid = {}
    with open(session_file) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("type") in ("user", "assistant") and "uuid" in obj:
                msg_by_uuid[obj["uuid"]] = obj

    results = []
    for mark in marks:
        user_msg = msg_by_uuid.get(mark["user_uuid"])
        assistant_msg = msg_by_uuid.get(mark["assistant_uuid"])
        if user_msg and assistant_msg:
            results.append({
                "user": extract_text(user_msg),
                "assistant": extract_text(assistant_msg),
                "timestamp": user_msg.get("timestamp", "")
            })

    print(json.dumps(results, ensure_ascii=False))


def extract_range(state_file, session_file):
    """Extract all conversations after the begin marker to end of session."""
    with open(state_file) as f:
        state = json.load(f)

    recording = state.get("recording", {})
    if not recording.get("active"):
        print(json.dumps({"error": "no active recording"}))
        sys.exit(1)

    start_uuid = recording["start_uuid"]

    messages = []
    with open(session_file) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("type") in ("user", "assistant"):
                messages.append(obj)

    start_idx = None
    for i, msg in enumerate(messages):
        if msg.get("uuid") == start_uuid:
            start_idx = i
            break

    if start_idx is None:
        print(json.dumps({"error": f"start_uuid {start_uuid} not found"}))
        sys.exit(1)

    after = messages[start_idx + 1:]
    results = []
    i = 0
    while i < len(after):
        if after[i]["type"] == "user":
            user_msg = after[i]
            assistant_msg = None
            for j in range(i + 1, len(after)):
                if after[j]["type"] == "assistant":
                    assistant_msg = after[j]
                    i = j + 1
                    break
            else:
                i += 1
                continue
            if assistant_msg:
                results.append({
                    "user": extract_text(user_msg),
                    "assistant": extract_text(assistant_msg),
                    "timestamp": user_msg.get("timestamp", "")
                })
        else:
            i += 1

    print(json.dumps(results, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage: session2doc.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "locate-last":
        if len(sys.argv) < 3:
            print("Usage: session2doc.py locate-last <session_file>", file=sys.stderr)
            sys.exit(1)
        locate_last(sys.argv[2])
    elif cmd == "add-mark":
        if len(sys.argv) < 6:
            print("Usage: session2doc.py add-mark <state_file> <desc> <user_uuid> <assistant_uuid>", file=sys.stderr)
            sys.exit(1)
        add_mark(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == "begin":
        if len(sys.argv) < 4:
            print("Usage: session2doc.py begin <state_file> <last_uuid>", file=sys.stderr)
            sys.exit(1)
        begin_recording(sys.argv[2], sys.argv[3])
    elif cmd == "extract":
        if len(sys.argv) < 5:
            print("Usage: session2doc.py extract <state_file> <session_file> <desc>", file=sys.stderr)
            sys.exit(1)
        extract_marks(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "extract-range":
        if len(sys.argv) < 4:
            print("Usage: session2doc.py extract-range <state_file> <session_file>", file=sys.stderr)
            sys.exit(1)
        extract_range(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
