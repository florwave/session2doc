#!/usr/bin/env node
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { dirname } from 'path';

function extractText(message) {
  const content = message?.message?.content ?? '';
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content.filter(b => b?.type === 'text').map(b => b.text).join('\n');
  }
  return '';
}

function readJsonl(file) {
  return readFileSync(file, 'utf8').split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
}

function loadState(file) {
  if (existsSync(file)) return JSON.parse(readFileSync(file, 'utf8'));
  return { marks: {}, recording: { active: false, start_uuid: null, start_timestamp: null } };
}

function saveState(file, state) {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(state, null, 2));
}

function locateLast(sessionFile) {
  const messages = readJsonl(sessionFile).filter(o => o.type === 'user' || o.type === 'assistant');
  let lastAssistant = null, lastUser = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].type === 'assistant' && !lastAssistant) lastAssistant = messages[i];
    else if (messages[i].type === 'user' && lastAssistant) { lastUser = messages[i]; break; }
  }
  if (!lastUser || !lastAssistant) {
    console.log(JSON.stringify({ error: 'no conversation pair found' }));
    process.exit(1);
  }
  console.log(JSON.stringify({ user_uuid: lastUser.uuid, assistant_uuid: lastAssistant.uuid, timestamp: lastUser.timestamp ?? '' }));
}

function addMark(stateFile, desc, userUuid, assistantUuid) {
  const state = loadState(stateFile);
  if (!state.marks[desc]) state.marks[desc] = [];
  state.marks[desc].push({ user_uuid: userUuid, assistant_uuid: assistantUuid });
  saveState(stateFile, state);
  console.log(JSON.stringify({ status: 'ok', desc, count: state.marks[desc].length }));
}

function beginRecording(stateFile, lastUuid) {
  const state = loadState(stateFile);
  state.recording = { active: true, start_uuid: lastUuid };
  saveState(stateFile, state);
  console.log(JSON.stringify({ status: 'ok', start_uuid: lastUuid }));
}

function extractMarks(stateFile, sessionFile, desc) {
  const state = JSON.parse(readFileSync(stateFile, 'utf8'));
  const marks = state?.marks?.[desc] ?? [];
  if (!marks.length) { console.log(JSON.stringify({ error: `no marks found for '${desc}'` })); process.exit(1); }
  const msgByUuid = {};
  for (const obj of readJsonl(sessionFile)) {
    if ((obj.type === 'user' || obj.type === 'assistant') && obj.uuid) msgByUuid[obj.uuid] = obj;
  }
  const results = [];
  for (const mark of marks) {
    const u = msgByUuid[mark.user_uuid], a = msgByUuid[mark.assistant_uuid];
    if (u && a) results.push({ user: extractText(u), assistant: extractText(a), timestamp: u.timestamp ?? '' });
  }
  console.log(JSON.stringify(results));
}

function extractRange(stateFile, sessionFile) {
  const state = JSON.parse(readFileSync(stateFile, 'utf8'));
  const recording = state?.recording ?? {};
  if (!recording.active) { console.log(JSON.stringify({ error: 'no active recording' })); process.exit(1); }
  const startUuid = recording.start_uuid;
  const messages = readJsonl(sessionFile).filter(o => o.type === 'user' || o.type === 'assistant');
  const startIdx = messages.findIndex(m => m.uuid === startUuid);
  if (startIdx === -1) { console.log(JSON.stringify({ error: `start_uuid ${startUuid} not found` })); process.exit(1); }
  const after = messages.slice(startIdx + 1);
  const results = [];
  let i = 0;
  while (i < after.length) {
    if (after[i].type === 'user') {
      const userMsg = after[i];
      let assistantMsg = null;
      for (let j = i + 1; j < after.length; j++) {
        if (after[j].type === 'assistant') { assistantMsg = after[j]; i = j + 1; break; }
      }
      if (!assistantMsg) { i++; continue; }
      results.push({ user: extractText(userMsg), assistant: extractText(assistantMsg), timestamp: userMsg.timestamp ?? '' });
    } else { i++; }
  }
  console.log(JSON.stringify(results));
}

const [,, cmd, ...args] = process.argv;
const usage = (msg) => { process.stderr.write(msg + '\n'); process.exit(1); };

if (cmd === 'locate-last') { if (!args[0]) usage('Usage: session2doc.mjs locate-last <session_file>'); locateLast(args[0]); }
else if (cmd === 'add-mark') { if (args.length < 4) usage('Usage: session2doc.mjs add-mark <state_file> <desc> <user_uuid> <assistant_uuid>'); addMark(...args.slice(0, 4)); }
else if (cmd === 'begin') { if (args.length < 2) usage('Usage: session2doc.mjs begin <state_file> <last_uuid>'); beginRecording(args[0], args[1]); }
else if (cmd === 'extract') { if (args.length < 3) usage('Usage: session2doc.mjs extract <state_file> <session_file> <desc>'); extractMarks(args[0], args[1], args[2]); }
else if (cmd === 'extract-range') { if (args.length < 2) usage('Usage: session2doc.mjs extract-range <state_file> <session_file>'); extractRange(args[0], args[1]); }
else usage(cmd ? `Unknown command: ${cmd}` : 'Usage: session2doc.mjs <command> [args...]');
