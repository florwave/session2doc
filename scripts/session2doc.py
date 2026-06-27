#!/usr/bin/env python3
"""session2doc: 解析 Claude Code session 历史并管理标记状态。"""

import json
import sys
import os


def locate_last(session_file):
    """找到 session 文件中最后一轮 user+assistant 对话的 uuid。"""
    messages = []
    with open(session_file) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("type") in ("user", "assistant"):
                messages.append(obj)

    # 从后往前找最后一个 assistant，再找它前面最近的 user
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
    """将一轮对话的 uuid 添加到指定 desc 分组。"""
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
    """开始录制模式，记录起始 uuid。"""
    state = {"marks": {}, "recording": {"active": False, "start_uuid": None, "start_timestamp": None}}
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)

    state["recording"] = {"active": True, "start_uuid": last_uuid}

    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(json.dumps({"status": "ok", "start_uuid": last_uuid}))


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
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
