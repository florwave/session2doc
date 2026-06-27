# Session2Doc Plugin 设计规格

## 概述

一个 Claude Code plugin，用于在对话过程中标记需要整理的对话历史，最终将标记的内容整理为格式化文档。解决用户在 session 中学习知识点后需要手动整理分散对话记录的问题。

## 核心能力

- **mark 模式**：逐个标记对话轮次到指定主题，最后统一生成文档（适合分散的对话）
- **begin/end 模式**：标记一段连续对话范围，直接生成文档（适合连续的对话）

---

## 命令设计

| 命令 | 参数 | 作用 |
|------|------|------|
| `/session2doc:mark` | `<desc>` (必填) | 标记当前 session 最近一轮对话（user+assistant），关联到 `desc` 分组 |
| `/session2doc:doc` | `<desc> <path>` (必填) | 将 `desc` 分组下所有标记的对话整理为文档，输出到 `path` |
| `/session2doc:begin` | 无 | 开始录制模式，记录当前位置 |
| `/session2doc:end` | `<desc> <path>` (必填) | 结束录制，将 begin 之后的所有对话整理为文档，输出到 `path` |

---

## Plugin 目录结构

```
session2doc/
├── plugin.json
├── commands/
│   ├── mark.md
│   ├── doc.md
│   ├── begin.md
│   └── end.md
└── scripts/
    ├── session2doc.py
    └── session2doc.mjs
```

---

## 状态管理

状态文件路径：项目根目录下 `.session2doc/state.json`

```json
{
  "marks": {
    "<desc>": [
      {"user_uuid": "...", "assistant_uuid": "...", "timestamp": "..."}
    ]
  },
  "recording": {
    "active": false,
    "start_uuid": null,
    "start_timestamp": null
  }
}
```

- `marks`：按 desc 分组存储标记的对话 uuid
- `recording`：begin/end 模式的录制状态

---

## 脚本设计

### CLI 接口

提供 Python (`session2doc.py`) 和 Node.js (`session2doc.mjs`) 两个版本，接口完全一致。Command 执行时优先尝试 Python，失败则 fallback 到 Node.js。

```bash
# 定位当前 session 最后一轮对话的 uuid
session2doc locate-last <session_file>
# 输出: {"user_uuid": "...", "assistant_uuid": "...", "timestamp": "..."}

# 添加 mark 到指定 desc 分组
session2doc add-mark <state_file> <desc> <user_uuid> <assistant_uuid>

# 开始录制（记录起始 uuid）
session2doc begin <state_file> <last_uuid>

# 提取 mark 模式下指定 desc 的所有对话内容
session2doc extract <state_file> <session_file> <desc>
# 输出: JSON 数组

# 提取 begin/end 范围的对话内容
session2doc extract-range <state_file> <session_file>
# 输出: JSON 数组
```

### 提取输出格式

```json
[
  {
    "user": "用户的完整消息文本",
    "assistant": "AI 的完整回复文本",
    "timestamp": "2026-06-27T10:00:00Z"
  }
]
```

---

## 核心流程

### mark + doc 流程

1. 用户执行 `/session2doc:mark <desc>`
2. Agent 调用 `locate-last` 找到最后一轮对话的 uuid
3. Agent 调用 `add-mark` 将 uuid 写入 state.json 的对应 desc 分组
4. 向用户确认标记成功
5. （重复 1-4 标记更多对话）
6. 用户执行 `/session2doc:doc <desc> <path>`
7. Agent 调用 `extract` 提取该 desc 下所有标记对话的完整内容
8. Agent 将内容整理为文档，写入 `<path>`
9. 清除该 desc 的标记

### begin + end 流程

1. 用户执行 `/session2doc:begin`
2. Agent 调用 `locate-last` 获取当前最后一条消息 uuid，调用 `begin` 写入 state
3. 用户正常对话…
4. 用户执行 `/session2doc:end <desc> <path>`
5. Agent 调用 `extract-range` 提取从 start_uuid 之后到当前的所有对话
6. Agent 整理为文档写入 `<path>`
7. 清除 recording 状态

---

## Session 文件定位策略

Agent 执行命令时定位当前 session 文件：
1. 读取 `CLAUDE_SESSION_ID` 环境变量（如可用），拼接路径
2. 否则从 `~/.claude/projects/<当前项目编码路径>/` 下找到最近修改的 `.jsonl` 文件

项目路径编码规则：路径中 `/` 替换为 `-`，如 `/Users/lorainli/Projects/session2doc` → `-Users-lorainli-Projects-session2doc`

---

## 文档整理原则

Agent 在生成最终文档时遵循：

1. **保留原文**：尽可能保留对话中的原始描述、代码、示例
2. **只做格式化**：添加标题层级、代码块语言标注、列表整理
3. **去除噪声**：去掉工具调用细节、系统消息、文件快照等非内容部分
4. **保持顺序**：按对话时间顺序组织
5. **不添加额外内容**：避免 Agent 自行补充对话中不存在的信息

---

## Session JSONL 消息结构参考

每行 JSON 对象，关键字段：
- `type`：消息类型（`user` / `assistant` / `system` / `attachment` 等）
- `uuid`：消息唯一标识
- `parentUuid`：父消息 uuid（可构建对话链）
- `timestamp`：时间戳
- `message.content`：消息内容（user 为 string 或 content block 数组，assistant 为 content block 数组）

提取时只关注 `type: "user"` 和 `type: "assistant"` 的消息，忽略其他元数据类型。
