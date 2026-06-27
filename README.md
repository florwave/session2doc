# session2doc

A Claude Code plugin for marking conversation history during sessions and compiling them into formatted documents.

## Use Case

When learning a topic through AI conversations, useful information is scattered across multiple turns in a session. Manual organization is tedious — session2doc lets you mark conversations on the fly and generate a well-organized document with a single command.

## Installation

```bash
# Install from GitHub
claude plugins add https://github.com/florwave/session2doc

# Or install from marketplace
claude plugins add session2doc
```

## Commands

### Mark Mode (for scattered conversations)

Mark conversation turns at different positions, group by topic, and compile into documents.

```bash
# Mark the last conversation turn to a topic
/session2doc:mark websocket-internals

# Continue chatting... mark again
/session2doc:mark websocket-internals

# Mark multiple topics simultaneously
/session2doc:mark rust-lifetimes

# Generate documents
/session2doc:doc websocket-internals docs/websocket.md
/session2doc:doc rust-lifetimes docs/rust-lifetime.md
```

### Begin/End Mode (for continuous conversations)

Mark a continuous range of conversations and generate a document when done.

```bash
# Start recording
/session2doc:begin

# Chat normally... all subsequent conversations are recorded

# Stop recording and generate document
/session2doc:end goroutine-scheduling docs/goroutine.md
```

## Formatting Principles

Generated documents follow these principles:
- Preserve original descriptions, code, and examples from conversations
- Format only (headings, code blocks, lists)
- Remove tool calls, system messages, and other noise
- Organize in chronological order
- Never add content that doesn't exist in the original conversation

## Requirements

Scripts prefer Python 3, falling back to Node.js if unavailable. No external dependencies required.

## License

Apache-2.0
