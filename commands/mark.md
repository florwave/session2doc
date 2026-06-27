---
description: Mark the last conversation turn to a topic group
argument-hint: "<desc>"
---

Mark the most recent conversation turn (user + assistant) in the current session to the specified topic group.

Parameters:
- `desc` (required): Topic description used as group identifier. Multiple topics can be maintained simultaneously and compiled into separate documents via `/session2doc:doc`.

Steps:
1. Determine the current session file path: find the corresponding project directory under `~/.claude/projects/`, and use the most recently modified `.jsonl` file. Path encoding rule: replace `/` in the working directory path with `-`.
2. Run the script to locate the last conversation turn (prefer python3, fallback to node):
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py locate-last <session_file>
   ```
   If python3 is unavailable:
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs locate-last <session_file>
   ```
3. Add the mark using the returned uuids:
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py add-mark .session2doc/state.json "$ARGUMENTS.desc" <user_uuid> <assistant_uuid>
   ```
4. Confirm to user: marked the last conversation turn to "$ARGUMENTS.desc" (N total).
