---
description: Stop recording and generate document
argument-hint: "<desc> <path>"
---

Stop recording mode and compile all conversations from begin to now into a document.

Parameters:
- `desc` (required): Document topic description, used for the document title.
- `path` (required): Output file path where the document will be written.

Steps:
1. Determine the current session file path (same as mark command).
2. Extract conversation content within the range:
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py extract-range .session2doc/state.json <session_file>
   ```
   If python3 is unavailable:
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs extract-range .session2doc/state.json <session_file>
   ```
3. Organize the extracted JSON content into a markdown document and write to "$ARGUMENTS.path". Formatting principles:
   - Preserve original text: keep original descriptions, code, and examples from the conversation
   - Format only: add heading levels, code block language annotations, list formatting
   - Remove noise: strip tool call details, system messages, and other non-content parts
   - Maintain order: organize by conversation chronological order
   - No extra content: do not add information that doesn't exist in the conversation
4. Confirm the document has been generated to "$ARGUMENTS.path".
