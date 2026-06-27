# Session2Doc：本地会话历史解析指南

## 概述

本文档整理了 Claude Code 和 Codex 两个 AI 编码工具的本地会话历史存储机制，以及如何解析和查看历史对话。

---

## 一、Claude Code 会话历史

### 存储位置

| 路径 | 作用 |
|------|------|
| `~/.claude/projects/<项目路径编码>/<session-uuid>.jsonl` | 每个 session 的完整对话记录（核心） |
| `~/.claude/history.jsonl` | 用户输入的命令/提示词索引（含 sessionId、时间戳、项目路径） |
| `~/.claude/sessions/<pid>.json` | 活跃/最近进程的会话元信息（pid、cwd、版本等） |

### 项目目录编码规则

项目路径中的 `/` 被替换为 `-`，例如：
- `/Users/lorainli/MINE` → `-Users-lorainli-MINE`

### JSONL 消息类型

每行一个 JSON 对象，`type` 字段标识类型：

- `user` — 用户消息，含 `message.content`、时间戳、cwd
- `assistant` — 模型回复，含完整输出和工具调用
- `system` — 系统消息
- `last-prompt` / `mode` / `permission-mode` — 会话元数据
- `attachment` / `file-history-snapshot` — 文件上下文快照
- `ai-title` — 会话自动生成的标题

### 快速查看命令

```bash
# 列出某项目所有 session（按时间排序）
ls -lt ~/.claude/projects/-Users-lorainli-MINE/*.jsonl | head -5

# 提取对话内容
python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    for line in f:
        obj = json.loads(line.strip())
        if obj.get('type') == 'user':
            print(f\"me: {obj['message']['content'][:200]}\")
        elif obj.get('type') == 'assistant':
            for b in obj.get('message',{}).get('content',[]):
                if isinstance(b,dict) and b.get('type')=='text':
                    print(f\"ai: {b['text'][:200]}\")
                    break
" <session-file>.jsonl

# 搜索包含关键词的 session
grep -l "关键词" ~/.claude/projects/-Users-lorainli-MINE/*.jsonl

# 查看 session 标题
python3 -c "
import json, os, glob
for f in sorted(glob.glob(os.path.expanduser('~/.claude/projects/-Users-lorainli-MINE/*.jsonl')), key=os.path.getmtime, reverse=True)[:10]:
    with open(f) as fp:
        for line in fp:
            obj = json.loads(line)
            if obj.get('type') == 'ai-title':
                print(f\"{os.path.basename(f)[:36]}  →  {obj.get('title', '')}\")
                break
"
```

---

## 二、Codex 会话历史

### 存储位置

| 路径 | 作用 |
|------|------|
| `~/.codex/sessions/<年>/<月>/<日>/rollout-<时间>-<uuid>.jsonl` | 每个 session 的完整对话记录 |
| `~/.codex/session_index.jsonl` | 会话索引（id、标题、更新时间） |
| `~/.codex/state_5.sqlite` | 会话状态 |
| `~/.codex/memories_1.sqlite` | 记忆 |

### 文件组织

按日期分层目录，文件名包含日期、时间和 session UUID：
```
~/.codex/sessions/2026/06/20/rollout-2026-06-20T21-16-57-019ee52d-6298-77d2-a072-558693999fde.jsonl
```

### JSONL 消息类型

- `session_meta` — 会话元信息（cwd、CLI 版本、模型、来源）
- `response_item` — 核心对话内容，`payload.role` 区分 `user` / `assistant` / `developer`
- `event_msg` — 事件（task_started、工具调用等）
- `turn_context` — 每轮的工作目录、权限策略等上下文

> 与 Claude Code 不同：Codex 的消息都包裹在 `payload` 里，需要多解一层。

### 快速查看命令

```bash
# 查看所有 session 标题
cat ~/.codex/session_index.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    obj = json.loads(line.strip())
    print(f\"{obj['id'][:8]}  {obj.get('updated_at','')[:10]}  {obj.get('thread_name','')}\")" | tail -20

# 提取对话内容
python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    for line in f:
        obj = json.loads(line.strip())
        if obj.get('type') != 'response_item': continue
        p = obj['payload']
        for c in p.get('content', []):
            if c.get('type')=='input_text' and p.get('role')=='user' and not c['text'].startswith('<'):
                print(f\"me: {c['text'][:200]}\")
            elif c.get('type')=='output_text' and p.get('role')=='assistant':
                print(f\"ai: {c['text'][:200]}\")
" <session-file>.jsonl

# 按关键词搜索
grep -rl "关键词" ~/.codex/sessions/
```

### Codex 内置命令

- `/resume` — 恢复之前的会话
- 界面内可搜索、归档、删除历史线程

---

## 三、对比总结

| 维度 | Claude Code | Codex |
|------|-------------|-------|
| 存储位置 | `~/.claude/projects/<编码路径>/` | `~/.codex/sessions/<年>/<月>/<日>/` |
| 索引 | `history.jsonl`（输入记录） | `session_index.jsonl`（标题+时间） |
| 格式 | 扁平 `type` + `message` | 嵌套 `type` + `payload` |
| 官方导出 | `/export` 命令 | 无专用导出命令 |
| 组织方式 | 按项目分目录 | 按日期分目录 |

---

## 四、解析脚本

项目根目录下的 `parse_sessions.py` 可自动解析两种格式并输出为 markdown：

```bash
python3 parse_sessions.py
```

脚本核心逻辑：

- `parse_claude_code(filepath)` — 提取 `type=user` 和 `type=assistant` 的 `message.content`
- `parse_codex(filepath)` — 从 `response_item` 的 `payload` 中提取 `input_text`（user）和 `output_text`（assistant），跳过以 `<` 开头的系统块
- 自动查找最近修改的 session 文件
- 长文本截断至 1000 字符

输出格式：

```markdown
**me:** 用户的问题

**ai:** AI 的回答
```

---

## 五、相关文件

| 文件 | 说明 |
|------|------|
| `session_parse_example.md` | 解析输出示例 |
| `parse_sessions.py` | 解析脚本 |
| `session2doc.md` | 本文档 |
