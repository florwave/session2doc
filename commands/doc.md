---
description: Compile marked conversations into a document
argument-hint: "<desc> <path>"
---

Compile all marked conversations under the specified topic group into a document.

Parameters:
- `desc` (required): Topic description, corresponding to the group identifier used when marking.
- `path` (required): Output file path where the document will be written.

Steps:
1. Determine the current session file path (same as mark command).
2. Extract marked conversation content:
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py extract .session2doc/state.json <session_file> "$ARGUMENTS.desc"
   ```
   If python3 is unavailable:
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs extract .session2doc/state.json <session_file> "$ARGUMENTS.desc"
   ```
3. Organize the extracted JSON content into a markdown document and write to "$ARGUMENTS.path". Formatting principles:
   - Preserve original text: keep original descriptions, code, and examples from the conversation
   - Format only: add heading levels, code block language annotations, list formatting
   - Remove noise: strip tool call details, system messages, and other non-content parts
   - Maintain order: organize by conversation chronological order
   - No extra content: do not add information that doesn't exist in the conversation
4. Confirm the document has been generated.
