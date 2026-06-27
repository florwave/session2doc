#!/usr/bin/env python3
"""解析 Claude Code 和 Codex 的本地会话历史，输出为可读的 markdown 文档。"""

import json
import os
import glob

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_parse_example.md")
MAX_TEXT_LEN = 1000


def parse_claude_code(filepath):
    """解析 Claude Code 的 .jsonl 会话文件，返回 (role, text) 列表。"""
    messages = []
    with open(filepath) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("type") == "user":
                content = obj["message"]["content"]
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"
                    )
                else:
                    continue
                if text.strip():
                    messages.append(("me", text.strip()))
            elif obj.get("type") == "assistant":
                texts = [
                    block["text"]
                    for block in obj.get("message", {}).get("content", [])
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if texts:
                    messages.append(("ai", "\n".join(texts).strip()))
    return messages


def parse_codex(filepath):
    """解析 Codex 的 .jsonl 会话文件，返回 (role, text) 列表。"""
    messages = []
    with open(filepath) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("type") != "response_item":
                continue
            payload = obj["payload"]
            role = payload.get("role", "")
            for c in payload.get("content", []):
                if c.get("type") == "input_text" and role == "user":
                    text = c["text"].strip()
                    if text.startswith("<"):  # 跳过系统/环境 XML 块
                        continue
                    if text:
                        messages.append(("me", text))
                elif c.get("type") == "output_text" and role == "assistant":
                    text = c["text"].strip()
                    if text:
                        messages.append(("ai", text))
    return messages


def truncate(text, max_len=MAX_TEXT_LEN):
    if len(text) > max_len:
        return text[:max_len] + "\n\n...(truncated)"
    return text


def find_latest_claude_session(project_dir):
    """找到指定项目目录下最近修改的有内容的 session 文件。"""
    files = sorted(glob.glob(os.path.join(project_dir, "*.jsonl")), key=os.path.getmtime, reverse=True)
    for f in files:
        with open(f) as fp:
            if any('"type": "user"' in l or '"type":"user"' in l for l in fp):
                return f
    return files[0] if files else None


def find_latest_codex_session():
    """找到最近的 Codex session 文件。"""
    base = os.path.expanduser("~/.codex/sessions/")
    files = sorted(glob.glob(os.path.join(base, "**/*.jsonl"), recursive=True), key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def main():
    output_lines = ["# 会话历史解析示例\n"]

    # Claude Code
    claude_dir = os.path.expanduser("~/.claude/projects/-Users-lorainli-MINE/")
    claude_file = find_latest_claude_session(claude_dir)
    output_lines.append("## Claude Code\n")
    if claude_file:
        output_lines.append(f"> 源文件: `{claude_file}`\n")
        for role, text in parse_claude_code(claude_file):
            output_lines.append(f"**{role}:** {truncate(text)}\n")
    else:
        output_lines.append("未找到 Claude Code 会话文件。\n")

    # Codex
    output_lines.append("\n---\n")
    output_lines.append("## Codex\n")
    codex_file = find_latest_codex_session()
    if codex_file:
        output_lines.append(f"> 源文件: `{codex_file}`\n")
        for role, text in parse_codex(codex_file):
            output_lines.append(f"**{role}:** {truncate(text)}\n")
    else:
        output_lines.append("未找到 Codex 会话文件。\n")

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(output_lines))

    print(f"Done. Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
