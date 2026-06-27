# session2doc

一个 Claude Code plugin，用于在对话过程中标记需要整理的对话历史，最终将标记的内容整理为格式化文档。

## 使用场景

在与 AI 对话学习某个知识点时，有用的信息散落在 session 的多轮对话中。手动整理费时费力，session2doc 让你在对话过程中随手标记，最后一键生成整理好的文档。

## 安装

```bash
# 在你的项目中添加为本地 plugin
claude plugins add /path/to/session2doc
```

## 命令

### mark 模式（适合分散的对话）

标记散落在不同位置的对话轮次，按主题分组，最后统一生成文档。

```bash
# 标记上一轮对话到指定主题
/session2doc:mark websocket原理

# 继续对话...再次标记
/session2doc:mark websocket原理

# 可以同时标记多个主题
/session2doc:mark rust生命周期

# 生成文档
/session2doc:doc websocket原理 docs/websocket.md
/session2doc:doc rust生命周期 docs/rust-lifetime.md
```

### begin/end 模式（适合连续的对话）

标记一段连续的对话范围，结束时直接生成文档。

```bash
# 开始录制
/session2doc:begin

# 正常对话...所有后续对话都会被记录

# 结束录制并生成文档
/session2doc:end goroutine调度 docs/goroutine.md
```

## 文档整理原则

生成的文档遵循以下原则：
- 保留对话中的原始描述、代码、示例
- 只做格式化整理（标题、代码块、列表）
- 去除工具调用、系统消息等噪声
- 按对话时间顺序组织
- 不添加对话中不存在的额外内容

## 环境要求

脚本优先使用 Python 3，如不可用则 fallback 到 Node.js，无需安装额外依赖。

## License

MIT
