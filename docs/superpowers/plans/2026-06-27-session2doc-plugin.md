# Session2Doc Plugin 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个 Claude Code plugin，通过 mark/doc 和 begin/end 两种模式标记并整理对话历史为文档。

**Architecture:** Plugin 由 4 个 command 文件驱动 Agent 行为，底层通过 Python/Node.js 脚本解析 session jsonl 文件并管理标记状态。脚本提供统一 CLI 接口，command prompt 指导 Agent 调用脚本并整理输出。

**Tech Stack:** Claude Code Plugin（plugin.json + command markdown），Python 3 脚本，Node.js (ESM) 脚本，JSON 状态文件。

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `plugin.json` | 插件清单，声明名称、命令列表 |
| `commands/mark.md` | mark 命令定义，指导 Agent 标记上一轮对话 |
| `commands/doc.md` | doc 命令定义，指导 Agent 提取并整理文档 |
| `commands/begin.md` | begin 命令定义，指导 Agent 开始录制 |
| `commands/end.md` | end 命令定义，指导 Agent 结束录制并生成文档 |
| `scripts/session2doc.py` | Python 版解析脚本（locate-last, add-mark, begin, extract, extract-range） |
| `scripts/session2doc.mjs` | Node.js 版解析脚本，接口与 Python 版完全一致 |

---

### Task 1: 创建 plugin.json

**Files:**
- Create: `plugin.json`

- [ ] **Step 1: 创建 plugin.json**

```json
{
  "name": "session2doc",
  "description": "标记对话历史并整理为文档",
  "commands": [
    "commands/mark.md",
    "commands/doc.md",
    "commands/begin.md",
    "commands/end.md"
  ]
}
```

- [ ] **Step 2: Commit**

```bash
git add plugin.json
git commit -m "feat: add plugin.json manifest"
```

---

### Task 2: 实现 Python 脚本 - locate-last 子命令

**Files:**
- Create: `scripts/session2doc.py`

- [ ] **Step 1: 创建脚本骨架和 locate-last 子命令**

```python
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
```

- [ ] **Step 2: 验证脚本可以对当前 session 运行**

Run: `python3 scripts/session2doc.py locate-last ~/.claude/projects/-Users-lorainli-Projects-session2doc/9f11984b-1741-489f-b456-7868422572ed.jsonl`
Expected: JSON 输出包含 `user_uuid`、`assistant_uuid`、`timestamp` 字段

- [ ] **Step 3: Commit**

```bash
git add scripts/session2doc.py
git commit -m "feat: add session2doc.py with locate-last command"
```

---

### Task 3: 实现 Python 脚本 - add-mark 和 begin 子命令

**Files:**
- Modify: `scripts/session2doc.py`

- [ ] **Step 1: 添加 add-mark 子命令**

在 `main()` 函数的 cmd 分支中添加：

```python
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
```

- [ ] **Step 2: 添加 begin 子命令**

```python
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
```

- [ ] **Step 3: 在 main() 中注册新命令**

```python
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
```

- [ ] **Step 4: 验证 add-mark**

Run: `python3 scripts/session2doc.py add-mark /tmp/test-state.json "测试主题" "uuid-1" "uuid-2"`
Expected: 输出 `{"status": "ok", "desc": "测试主题", "count": 1}`，且 `/tmp/test-state.json` 文件已创建

- [ ] **Step 5: 验证 begin**

Run: `python3 scripts/session2doc.py begin /tmp/test-state.json "uuid-start"`
Expected: 输出 `{"status": "ok", "start_uuid": "uuid-start"}`

- [ ] **Step 6: Commit**

```bash
git add scripts/session2doc.py
git commit -m "feat: add add-mark and begin commands to session2doc.py"
```

---

### Task 4: 实现 Python 脚本 - extract 和 extract-range 子命令

**Files:**
- Modify: `scripts/session2doc.py`

- [ ] **Step 1: 添加消息内容提取辅助函数**

```python
def extract_text(message):
    """从 message.content 中提取纯文本。"""
    content = message.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block["text"])
                elif block.get("type") == "tool_result":
                    # 跳过 tool_result
                    pass
        return "\n".join(texts)
    return ""
```

- [ ] **Step 2: 添加 extract 子命令**

```python
def extract_marks(state_file, session_file, desc):
    """提取指定 desc 分组下所有标记的对话内容。"""
    with open(state_file) as f:
        state = json.load(f)

    marks = state.get("marks", {}).get(desc, [])
    if not marks:
        print(json.dumps({"error": f"no marks found for '{desc}'"}))
        sys.exit(1)

    # 读取 session 中所有消息，建立 uuid 索引
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
```

- [ ] **Step 3: 添加 extract-range 子命令**

```python
def extract_range(state_file, session_file):
    """提取 begin 之后到 session 末尾的所有对话。"""
    with open(state_file) as f:
        state = json.load(f)

    recording = state.get("recording", {})
    if not recording.get("active"):
        print(json.dumps({"error": "no active recording"}))
        sys.exit(1)

    start_uuid = recording["start_uuid"]

    # 读取所有 user/assistant 消息
    messages = []
    with open(session_file) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("type") in ("user", "assistant"):
                messages.append(obj)

    # 找到 start_uuid 的位置，取其后的所有消息
    start_idx = None
    for i, msg in enumerate(messages):
        if msg.get("uuid") == start_uuid:
            start_idx = i
            break

    if start_idx is None:
        print(json.dumps({"error": f"start_uuid {start_uuid} not found"}))
        sys.exit(1)

    # 从 start_idx 之后开始，配对 user+assistant
    after = messages[start_idx + 1:]
    results = []
    i = 0
    while i < len(after):
        if after[i]["type"] == "user":
            user_msg = after[i]
            # 找下一个 assistant
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
```

- [ ] **Step 4: 在 main() 中注册**

```python
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
```

- [ ] **Step 5: 验证 extract（使用真实 session 文件）**

Run: 先 add-mark 一个真实 uuid，然后 extract
Expected: 输出 JSON 数组，包含 user 和 assistant 文本内容

- [ ] **Step 6: Commit**

```bash
git add scripts/session2doc.py
git commit -m "feat: add extract and extract-range commands"
```

---

### Task 5: 实现 Node.js 脚本

**Files:**
- Create: `scripts/session2doc.mjs`

- [ ] **Step 1: 创建完整的 session2doc.mjs**

实现与 Python 版完全相同的 CLI 接口和逻辑：`locate-last`、`add-mark`、`begin`、`extract`、`extract-range`。使用 Node.js 内置模块（`fs`、`path`、`readline`），不依赖第三方包。

脚本结构：
```javascript
#!/usr/bin/env node
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { dirname } from 'path';
import { createInterface } from 'readline';
import { createReadStream } from 'fs';

// 逐行读取 jsonl 的辅助函数
async function readJsonl(filepath) { ... }

// 提取消息文本
function extractText(message) { ... }

// 子命令实现（与 Python 版逻辑一致）
async function locateLast(sessionFile) { ... }
function addMark(stateFile, desc, userUuid, assistantUuid) { ... }
function beginRecording(stateFile, lastUuid) { ... }
async function extract(stateFile, sessionFile, desc) { ... }
async function extractRange(stateFile, sessionFile) { ... }

// main
const [,, cmd, ...args] = process.argv;
// 路由到对应子命令
```

- [ ] **Step 2: 验证 locate-last**

Run: `node scripts/session2doc.mjs locate-last ~/.claude/projects/-Users-lorainli-Projects-session2doc/9f11984b-1741-489f-b456-7868422572ed.jsonl`
Expected: 与 Python 版输出一致

- [ ] **Step 3: Commit**

```bash
git add scripts/session2doc.mjs
git commit -m "feat: add session2doc.mjs Node.js implementation"
```

---

### Task 6: 创建 Command 文件

**Files:**
- Create: `commands/mark.md`
- Create: `commands/doc.md`
- Create: `commands/begin.md`
- Create: `commands/end.md`

- [ ] **Step 1: 创建 commands/mark.md**

```markdown
---
name: mark
description: 标记上一轮对话到指定主题分组
arguments:
  - name: desc
    description: 主题描述，用于分组标识
    required: true
---

将当前 session 最近一轮对话标记到 "$ARGUMENTS.desc" 分组。

步骤：
1. 确定当前 session 文件路径：从 `~/.claude/projects/` 下找到与当前项目对应的目录，取最近修改的 `.jsonl` 文件。项目路径编码规则：将工作目录的 `/` 替换为 `-`。
2. 运行脚本定位最后一轮对话（优先 python3，fallback 到 node）：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py locate-last <session_file>
   ```
3. 用返回的 uuid 添加标记：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py add-mark .session2doc/state.json "$ARGUMENTS.desc" <user_uuid> <assistant_uuid>
   ```
4. 向用户确认：已将上一轮对话标记到 "$ARGUMENTS.desc"（共 N 条）。
```

- [ ] **Step 2: 创建 commands/doc.md**

```markdown
---
name: doc
description: 将标记的对话整理为文档
arguments:
  - name: desc
    description: 要整理的主题描述
    required: true
  - name: path
    description: 输出文件路径
    required: true
---

将 "$ARGUMENTS.desc" 分组下所有标记的对话整理为文档，输出到 "$ARGUMENTS.path"。

步骤：
1. 确定当前 session 文件路径（同 mark 命令）。
2. 提取标记的对话内容：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py extract .session2doc/state.json <session_file> "$ARGUMENTS.desc"
   ```
3. 根据提取的 JSON 内容，整理为 markdown 文档并写入 "$ARGUMENTS.path"。整理原则：
   - 保留原文：尽可能保留对话中的原始描述、代码、示例
   - 只做格式化：添加标题层级、代码块语言标注、列表整理
   - 去除噪声：去掉工具调用细节、系统消息等非内容部分
   - 保持顺序：按对话时间顺序组织
   - 不添加额外内容：不自行补充对话中不存在的信息
4. 确认文档已生成。
```

- [ ] **Step 3: 创建 commands/begin.md**

```markdown
---
name: begin
description: 开始录制对话历史
---

开始录制模式，从当前位置开始记录后续所有对话。

步骤：
1. 确定当前 session 文件路径（同 mark 命令）。
2. 定位当前最后一条消息：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py locate-last <session_file>
   ```
3. 开始录制：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py begin .session2doc/state.json <assistant_uuid>
   ```
4. 向用户确认：录制已开始，后续对话将被记录。使用 `/session2doc:end <desc> <path>` 结束录制并生成文档。
```

- [ ] **Step 4: 创建 commands/end.md**

```markdown
---
name: end
description: 结束录制并生成文档
arguments:
  - name: desc
    description: 文档主题描述
    required: true
  - name: path
    description: 输出文件路径
    required: true
---

结束录制模式，将从 begin 到现在的所有对话整理为文档。

步骤：
1. 确定当前 session 文件路径（同 mark 命令）。
2. 提取范围内的对话内容：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py extract-range .session2doc/state.json <session_file>
   ```
3. 根据提取的 JSON 内容，整理为 markdown 文档并写入 "$ARGUMENTS.path"。整理原则：
   - 保留原文：尽可能保留对话中的原始描述、代码、示例
   - 只做格式化：添加标题层级、代码块语言标注、列表整理
   - 去除噪声：去掉工具调用细节、系统消息等非内容部分
   - 保持顺序：按对话时间顺序组织
   - 不添加额外内容：不自行补充对话中不存在的信息
4. 确认文档已生成到 "$ARGUMENTS.path"。
```

- [ ] **Step 5: Commit**

```bash
git add commands/
git commit -m "feat: add command definitions for mark, doc, begin, end"
```

---

### Task 7: 集成验证

**Files:** 无新增

- [ ] **Step 1: 验证 plugin 结构完整性**

Run: `find . -type f | grep -v '.git/' | grep -v '.idea/' | grep -v 'docs/' | sort`
Expected: 显示 plugin.json、commands/\*.md、scripts/session2doc.\* 文件

- [ ] **Step 2: 验证 Python 脚本全流程**

```bash
# 清理测试状态
rm -f .session2doc/state.json

SESSION=~/.claude/projects/-Users-lorainli-Projects-session2doc/9f11984b-1741-489f-b456-7868422572ed.jsonl

# locate-last
python3 scripts/session2doc.py locate-last "$SESSION"

# add-mark
python3 scripts/session2doc.py add-mark .session2doc/state.json "测试" <user_uuid> <assistant_uuid>

# extract
python3 scripts/session2doc.py extract .session2doc/state.json "$SESSION" "测试"
```

Expected: 每步输出合法 JSON，extract 输出包含 user/assistant 文本

- [ ] **Step 3: 验证 Node.js 脚本全流程**

```bash
rm -f .session2doc/state.json

# 同样的流程用 node 执行
node scripts/session2doc.mjs locate-last "$SESSION"
node scripts/session2doc.mjs add-mark .session2doc/state.json "测试" <user_uuid> <assistant_uuid>
node scripts/session2doc.mjs extract .session2doc/state.json "$SESSION" "测试"
```

Expected: 输出与 Python 版一致

- [ ] **Step 4: 将 .session2doc/ 添加到 .gitignore**

```bash
echo ".session2doc/" >> .gitignore
git add .gitignore
git commit -m "chore: add .session2doc to gitignore"
```
