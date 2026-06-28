---
description: Mark the last conversation turn to a topic group
argument-hint: "<desc>"
---

Mark the most recent conversation turn (user + assistant) in the current session to the specified topic group.

Parameters:
- `desc` (required): Topic description used as group identifier. Multiple topics can be maintained simultaneously and compiled into separate documents via `/session2doc:doc`.

Steps:
1. Determine the current session file path: find the corresponding project directory under `~/.claude/projects/`, and use the most recently modified `.jsonl` file. Path encoding rule: replace `/` in the working directory path with `-`.
2. Run the mark-last command (locates last turn and marks it in one step):
   ```
   python3 $PLUGIN_DIR/scripts/session2doc.py mark-last .session2doc/state.json "$ARGUMENTS.desc" <session_file>
   ```
   If python3 is unavailable:
   ```
   node $PLUGIN_DIR/scripts/session2doc.mjs mark-last .session2doc/state.json "$ARGUMENTS.desc" <session_file>
   ```
3. Confirm to user: marked the last conversation turn to "$ARGUMENTS.desc" (N total).
