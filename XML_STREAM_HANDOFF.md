# XML Stream Pipe Handoff

## What was done

### 1. `partial_command` fast path
**File:** `src/mindroot/lib/providers/__init__.py`

Added `'partial_command'` to `fast_path_services` set in `ProviderManager.__init__`. This bypasses the slow model/provider resolution overhead since `partial_command` has one implementation and doesn't need model selection.

### 2. New `process_stream` pipe
**File:** `src/mindroot/lib/xml_stream_pipe.py` (new, 130 lines)

- `@pipe(name='process_stream', priority=5)` registers it with PipelineManager
- Activates when `context.agent.get('xml_streaming')` is truthy OR env var `MR_XML_STREAMING=1`
- **Format detection:** If first chunk starts with `[` or `{`, assumes JSON and passes through unchanged. Otherwise enters XML mode.
- **XML mode:** Uses `XmlToolStreamAdapter` (from `lib/xml_tool_stream_adapter_v3.py`) to:
  - Stream speech deltas via `context.partial_command('speak', ...)` (buffered in sync callback, flushed in async pipe)
  - Emit complete tool commands as JSON dicts (e.g. `{"send_dtmf": {"digits": "1"}}`)
- Returns `{'chunk': json.dumps(new_commands)}` for tool commands, or `{'chunk': ''}` if no new commands
- `finish=True` parameter calls `adapter.finish()` to flush remaining speech/tools
- Falls back to passthrough on adapter errors
- Configurable `xml_emit_partial_on_chars` via agent config (default 8)

### 3. Integration into `parse_cmd_stream`
**File:** `src/mindroot/coreplugins/agent/agent.py`

- Added `import lib.xml_stream_pipe` to register the pipe
- Reset `context.data.pop('_xml_stream_state', None)` at start of each turn
- Per chunk: call `pipeline_manager.process_stream({'chunk': part}, context=context)`, use returned chunk for `buffer`
- After for loop: call `pipeline_manager.process_stream({'chunk': '', 'finish': True}, context=context)` to flush remaining commands
- `original_buffer` still accumulates raw stream for debugging/chat log fallback

### 4. Deleted dead code
**File:** `src/mindroot/coreplugins/agent/buagentz1.py` (deleted)

Older backup version of agent.py. Had the same process_stream integration applied but is now removed.

## Key files

| File | Purpose |
|---|---|
| `lib/xml_tool_stream_adapter_v3.py` | XmlToolStreamAdapter - streaming parser for XML-ish speech+tool output |
| `lib/xml_docstring_adapter.py` | Converts JSON examples in docstrings to XML-ish syntax |
| `lib/xml_stream_pipe.py` | `@pipe(name='process_stream')` - pipeline hook that transforms XML stream to JSON commands |
| `lib/pipelines/pipe.py` | `@pipe` decorator, `pipeline_manager` singleton |
| `lib/pipelines/pipelines.py` | `PipelineManager` class (lightweight, not slow) |
| `lib/providers/__init__.py` | `ProviderManager` with `fast_path_services` set |
| `coreplugins/agent/agent.py` | `parse_cmd_stream` - where process_stream is integrated |
| `coreplugins/chat/services.py` | `partial_command` service, `@pipe(name='process_results')` |

## What still needs to be done

### Docstring conversion (not yet implemented)

When `xml_streaming` is enabled, command docstrings in the system prompt should be converted from JSON examples to XML-ish examples using `xml_docstring_adapter.convert_docstring_json_examples_to_xml()`.

Where to hook: `render_system_msg()` in `agent.py` (line ~488). It calls `command_manager.get_some_docstrings()` and passes them to the template. Could either:
- Convert docstrings before passing to template
- Or add a `@pipe` on `pre_process_msg` or a new pipeline for system message construction

### Testing

No testing has been done yet. The pipe is inert unless `xml_streaming` is enabled, so existing agents are unaffected.

To test:
1. Set `MR_XML_STREAMING=1` or add `"xml_streaming": true` to agent.json
2. Use a model that can output XML-ish tool syntax
3. Verify speech streams via partial_command and tools execute correctly

### Known issues / design considerations

1. **Chat log for speech-only XML output:** If the model only outputs speech (no tools), `original_buffer` contains raw XML tags. The end-of-turn logic adds `original_buffer` to chat log. Should add cleaned speech text instead.

2. **`say` vs `speak`:** The existing parser treats partial `say` commands specially (adds to chat log). The pipe uses `speak` for partial_command. For text chat agents, there is no `speak` command. XML streaming is primarily for S2S/voice agents where `speak` partials trigger TTS.

3. **Buffer accumulation:** The pipe returns only new tool commands as JSON arrays. The existing parser accumulates these in `buffer` and `merge_json_arrays` handles concatenated arrays like `[cmd1][cmd2]`.

4. **Performance:** `partial_command` is now fast path. The pipe itself is lightweight (dict lookup + direct calls). The adapter is sync and fast.

5. **`allowed_tools` not configured:** The XmlToolStreamAdapter accepts an `allowed_tools` allowlist. Currently not set, so all XML tags are treated as potential tools. Could configure per-agent.

6. **Speech delta tracking:** The pipe tracks `last_speech_len` to emit only new speech deltas, avoiding duplicate TTS output.

## Architecture overview

```
LLM stream_chat output
       |
       v
  parse_cmd_stream (agent.py)
       |
       +---> pipeline_manager.process_stream({'chunk': part})
       |         |
       |         +-- [xml_stream_pipe.py]
       |         |     - If xml_streaming disabled: pass through
       |         |     - If JSON detected: pass through  
       |         |     - If XML detected:
       |         |       - XmlToolStreamAdapter.feed(chunk)
       |         |       - Speech -> context.partial_command('speak', delta)
       |         |       - Tools -> return as JSON command list
       |         |
       |         +-- return {'chunk': json_commands or ''}
       |
       +---> buffer += transformed_chunk
       |
       +---> parse_streaming_commands(buffer)  [existing parser]
       |         |
       |         +-- handles JSON command lists (including from XML conversion)
       |         +-- executes commands via handle_cmds
       |         +-- emits partial commands for streaming
       |
       +---> [after loop] pipeline_manager.process_stream({'chunk': '', 'finish': True})
             flushes remaining XML adapter state
```
