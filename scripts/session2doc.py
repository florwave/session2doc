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
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
