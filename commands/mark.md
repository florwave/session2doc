---
description: 标记上一轮对话到指定主题分组
argument-hint: "<desc>"
---

将当前 session 最近一轮对话标记到指定主题分组。

参数：
- `desc`（必填）：主题描述，用于分组标识。可同时维护多个主题，通过 `/session2doc:doc` 分别生成文档。

步骤：
1. 确定当前 session 文件路径：从 `~/.claude/projects/` 下找到与当前项目对应的目录，取最近修改的 `.jsonl` 文件。项目路径编码规则：将工作目录的 `/` 替换为 `-`。
2. 运行脚本定位最后一轮对话（优先 python3，fallback 到 node）：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py locate-last <session_file>
   ```
   如果 python3 不可用：
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs locate-last <session_file>
   ```
3. 用返回的 uuid 添加标记：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py add-mark .session2doc/state.json "$ARGUMENTS.desc" <user_uuid> <assistant_uuid>
   ```
4. 向用户确认：已将上一轮对话标记到 "$ARGUMENTS.desc"（共 N 条）。
