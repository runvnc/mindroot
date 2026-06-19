# XML / Raw-Text Command Streaming — Implementation Handoff

Status: **scaffolding + core wiring complete, not yet runtime-tested.** This doc
lets a fresh session finish verification and debugging.

## Goal

Let voice (and small-model) agents emit **raw text + XML-ish tags** instead of
JSON command arrays, to cut first-token latency. Raw text outside tags is
spoken; tags are commands. The model's own raw output is stored in the chat log
so it sees its own format next turn. Gated by env var `MR_XML_STREAMING`
(resolvable **per-agent** via the admin env vars, because `os.environ` is
context-aware — see `lib/context_environ.py`, which walks the stack for a
`context` local and checks `context.env` first).

This replaces the earlier prototype that lived in `mr_kyutai` and faked JSON
(XML → JSON-string → reparse). XML is now a **first-class grammar in core**,
parallel to JSON. The JSON path is untouched.

## Architecture decisions (already made)

- **Dual representation** in the chat log for XML assistant turns:
  - `content = [{"type":"text","text": <raw model output>, "format":"xml"}]`
    (what the LLM sees next turn)
  - `message["commands"] = [{name: args}, ...]` (pre-parsed; UI / cascade
    deletion / token tools read this, so nothing downstream parses XML).
- **One authoritative assistant write per turn** via
  `ChatLog.replace_last_assistant(content, commands=...)` — no reliance on the
  fragile repeat-role JSON-merge heuristic in `_add_message_impl`.
- **Direct execution**: the XML adapter drives `context.partial_command` /
  `execute_command` / `context.command_result` directly. No
  `parse_streaming_commands`, no buffer string surgery, no `invalid_start_format`
  error path (unknown/incomplete tags are simply spoken).
- **System prompt**: a separate clean template `system_xml.jinja2` is rendered
  when XML mode is on (chosen by page name, so there is no plugin
  override-precedence ambiguity). The `process_system_message` pipe still runs
  as a hook but nothing implements it now.

## Files changed / added

### Core (under `/files/mindroot/src/mindroot`)

1. **`lib/xml_stream_events.py`** (NEW) — `XmlEventStream`, an event-emitting
   wrapper around `XmlToolStreamAdapter`. `feed(delta)` / `finish()` return
   ordered events:
   - `{'kind':'speak_partial','text': <growing text for CURRENT segment>}`
   - `{'kind':'speak_final','text': <full text of completed segment>}`
   - `{'kind':'cmd','name':..., 'props': {...}}`
   Speech is segmented by tool boundaries (adapter force-flushes speech before a
   tool) and end-of-turn. `speak_partial` text is **relative to the current
   segment** (resets after each tool), matching how the TTS layer prefix-diffs
   each speak command. Unit-tested standalone (4 scenarios) — works.

2. **`lib/chatlog.py`**:
   - Added `ChatLog.replace_last_assistant(content, commands=None)` (replaces
     last assistant msg in place, else appends; saves async; fires the
     message_added hook).
   - `parsed_commands()` now prefers `message['commands']` when present.
   - `extract_delegate_task_log_ids()` now reads `message['commands']` first so
     cascade deletion finds XML-issued `delegate_task`/`delegate_subtask`.

3. **`coreplugins/agent/agent.py`**:
   - New import: `from lib.xml_stream_events import XmlEventStream` and
     `from lib.xml_docstring_adapter import convert_docstring_json_examples_to_xml`.
   - New module fn `xml_streaming_enabled()` → checks `MR_XML_STREAMING`
     (1/true/yes/on). Context-aware via `os.environ` patch.
   - `Agent.execute_command(cmd_name, cmd_args, context, cmd_id)` — execution
     half of `handle_cmds` WITHOUT the chat-log write.
   - `Agent._persist_xml_assistant(context, original_buffer, collected)` —
     writes dual-rep assistant message via `replace_last_assistant`.
   - `Agent.parse_xml_cmd_stream(stream, context)` — the XML event loop
     (partials throttled with the same `MR_PARTIAL_COMMAND_MIN_INTERVAL` /
     `MR_PARTIAL_COMMAND_MIN_CHARS` knobs; speak segment partials + final share
     one `cmd_id`; tool commands get fresh `cmd_id`; honors
     `cancel_current_turn`/`finished_conversation`; handles the
     `"SYSTEM: WARNING - Command interrupted!\n\n"` result like the JSON loop).
   - `render_system_msg`: when XML mode, converts command docstrings to XML-ish
     via `convert_docstring_json_examples_to_xml`, and renders page
     `system_xml` instead of `system` (then still runs the
     `process_system_message` pipe + `add_instructions` hook as before).
   - `chat_commands`: branches — `if xml_streaming_enabled(): parse_xml_cmd_stream`
     else `parse_cmd_stream`.

4. **`coreplugins/agent/templates/system_xml.jinja2`** (NEW) — compact,
   voice-friendly system prompt explaining raw-text-is-speech + tag syntax
   (attribute form `<cmd a="b"/>` and `<tool name="x">{json}</tool>`), plus
   persona/instructions/available-actions blocks. Uses the same render `data`
   keys as `system.jinja2` (`formatted_datetime`, `context_data`, `agent`,
   `persona`, `command_docs`).

5. **`coreplugins/chat/static/js/chat-history.js`**:
   - `_processAssistantMessage(part, persona, msg)` now prefers
     `msg.commands` (array) and falls back to `JSON.parse(part.text)`, then to
     plain text. Call site passes `msg`. This is the ONLY frontend change
     needed; the live SSE path is unaffected.

### Plugin (`/xfiles/plugins_ah/mr_kyutai/src/mr_kyutai`)

6. **`xml_stream_pipe.py`** — gutted to **no-op passthroughs** for both
   `process_stream` and `process_system_message` (kept so `mod.py`'s
   `from . import xml_stream_pipe` still imports; documents the migration to
   core). mr_kyutai now only provides TTS (realtime_stream.py partial pipe +
   speak command in mod.py).

All Python above passes `python -m py_compile`.

## TTS parity contract (critical — verified by reading the code, NOT yet runtime-tested)

From `mr_kyutai/realtime_stream.py` `handle_speak_partial` (a `partial_command`
pipe, priority 10) and `mr_kyutai/mod.py` `speak` command:

- partials: `partial_command('speak', json.dumps({'text': X}), {'text': X}, cmd_id=...)`
  where **X is the growing per-command text**; the pipe prefix-diffs vs
  `previous_text` to get deltas and resets when text isn't a prefix
  continuation (new command). A new session is created per speak command and
  cleaned up after the final speak drains.
- final: executing the `speak` command (`execute_command('speak', {'text': X})`)
  acquires a per-log_id serial lock, feeds remaining text, calls
  `session.finish()` (drains audio via AudioPacer), then `cleanup_session`.
- `parse_xml_cmd_stream` reproduces exactly this: per speech segment it streams
  `speak_partial` then runs the final `speak` command on `speak_final`, sharing
  one `cmd_id`. Tool commands run in stream order between segments.

**This is the #1 thing to validate at runtime.** Watch `/workspace/kyutai.err`
and `/tmp/sip_e2e_latency.log`.

## What remains to do / verify

1. **Create `system_xml.jinja2` review** — confirm it renders (the parent_env
   in `lib/templates.py` resolves parent templates from coreplugins; `agent` is
   in the coreplugins list, so `coreplugins/agent/templates/system_xml.jinja2`
   should be found). If `render('system_xml', ...)` returns "Template Not
   Found", fall back to `render_direct_template('system_xml.jinja2', data)` or
   verify the file is on a template search path. **Test this first.**
2. **End-to-end voice test** with an agent that has `MR_XML_STREAMING=1` in its
   admin env vars and the `speak` command enabled. Verify:
   - speech streams to TTS with low latency (partials),
   - tool tags execute in order,
   - the final speak drains audio,
   - barge-in/interrupt still works (`on_interrupt` hook cancels session).
3. **Chat log inspection** — confirm assistant messages are stored as
   `content:[{type,text,format:'xml'}]` + `commands:[...]`. Confirm a JSON-mode
   agent is completely unaffected.
4. **History reload UI** — confirm `chat-history.js` renders XML turns via
   `msg.commands` (say bubbles + `<action-component>`), not raw tag soup.
5. **Docstring → XML conversion quality** — eyeball the rendered `system_xml`
   for a few commands; `convert_docstring_json_examples_to_xml` may leave some
   JSON examples that confuse small models. Tune the converter or the command
   docstrings if needed.
6. **`emit_partial_on_chars`** — currently read from `context.agent`
   (`xml_emit_partial_on_chars`). Consider also honoring an env var.

## Known risks / edge cases

- **Trailing speech after the last tool** is captured: `XmlEventStream.finish()`
  emits a final `speak_final`, and `parse_xml_cmd_stream` does a final
  `_persist_xml_assistant` with the full `original_buffer`.
- **`<tool name="x">{json}</tool>`** yields `props` = parsed JSON dict merged
  with attrs; attribute-only tags yield a flat `{key: value}` dict (scalars
  coerced by `_coerce_scalar` in `xml_tool_stream_adapter_v3.py`). Commands
  needing nested args must use the `<tool>` body form. If a command gets wrong
  arg types, check `_coerce_scalar` / `_STRING_ATTR_KEYS`.
- **`reasoning`/`think`**: `execute_command` returns None for `cmd_name ==
  'reasoning'` (same as handle_cmds). If you want `<think>...</think>` in XML,
  decide how it maps (probably a `think` tool tag) and ensure it's stored in
  `commands` for the UI.
- **`context.partial_command` signature** mirrors the JSON loop:
  `(cmd_name, json.dumps(args), args, cmd_id=...)`. If mr_kyutai's pipe expects
  something else, adjust here.
- **No `invalid_start_format` path** for XML by design. If the model emits a
  literal `[{...}]` JSON array while in XML mode, it will be spoken as text.
  Don't enable XML mode for agents you expect to emit JSON.
- **`mr_kyutai` realtime_stream import timing**: the partial pipe + on_interrupt
  hook register when `realtime_stream` is imported (currently lazy inside
  `speak()`). If first-turn partials aren't intercepted, ensure realtime_stream
  is imported at plugin load (e.g. add `from . import realtime_stream` to
  `mod.py`). Not changed here — verify.

## Quick test of the adapter (no app needed)

```
cd /files/mindroot/src && python -c "
import json
from mindroot.lib.xml_stream_events import XmlEventStream
ev = XmlEventStream(emit_partial_on_chars=1)
out=[]
for c in ['Sure, let me ','look that up. ','<search_web query=\"x\"/>',' Done.']:
    out+=ev.feed(c)
out+=ev.finish()
for e in out: print(json.dumps(e))
"
```

## Switch summary

- Enable per-agent: set `MR_XML_STREAMING=1` in the agent's env (admin screen).
- Tuning: `MR_PARTIAL_COMMAND_MIN_INTERVAL`, `MR_PARTIAL_COMMAND_MIN_CHARS`,
  agent `xml_emit_partial_on_chars`.
- JSON agents: leave `MR_XML_STREAMING` unset → zero behavior change.
