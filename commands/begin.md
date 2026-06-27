---
description: Start recording conversation history
---

Start recording mode, recording all subsequent conversations from the current position.

Steps:
1. Determine the current session file path (same as mark command).
2. Locate the last message:
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py locate-last <session_file>
   ```
   If python3 is unavailable:
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs locate-last <session_file>
   ```
3. Start recording:
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py begin .session2doc/state.json <assistant_uuid>
   ```
4. Confirm to user: recording has started. Use `/session2doc:end <desc> <path>` to stop recording and generate a document.
