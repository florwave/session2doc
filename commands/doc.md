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
   如果 python3 不可用：
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs extract .session2doc/state.json <session_file> "$ARGUMENTS.desc"
   ```
3. 根据提取的 JSON 内容，整理为 markdown 文档并写入 "$ARGUMENTS.path"。整理原则：
   - 保留原文：尽可能保留对话中的原始描述、代码、示例
   - 只做格式化：添加标题层级、代码块语言标注、列表整理
   - 去除噪声：去掉工具调用细节、系统消息等非内容部分
   - 保持顺序：按对话时间顺序组织
   - 不添加额外内容：不自行补充对话中不存在的信息
4. 确认文档已生成。
