---
description: 开始录制对话历史
---

开始录制模式，从当前位置开始记录后续所有对话。

步骤：
1. 确定当前 session 文件路径（同 mark 命令）。
2. 定位当前最后一条消息：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py locate-last <session_file>
   ```
   如果 python3 不可用：
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs locate-last <session_file>
   ```
3. 开始录制：
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py begin .session2doc/state.json <assistant_uuid>
   ```
4. 向用户确认：录制已开始，后续对话将被记录。使用 `/session2doc:end <desc> <path>` 结束录制并生成文档。
