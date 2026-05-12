import json
import re
import logging
from json import JSONDecodeError

logger = logging.getLogger(__name__)

# Known long-form field names (used as hints, but detection is primarily structural)
LONG_FORM_FIELDS = {'text', 'markdown', 'cmd', 'udiff', 'extensive_chain_of_thoughts', 'thoughts', 'content'}

# Known command names - recovered non-reasoning commands must match one of these
# This prevents phantom command extraction from reasoning content that
# happens to contain JSON-like code snippets
KNOWN_COMMANDS = {
    'say', 'tell_and_continue', 'wait_for_user_reply', 'markdown_await_user',
    'think', 'reasoning', 'delegate_task', 'task_result', 'task_complete',
    'execute_command', 'mkdir', 'tree', 'append', 'write', 'read', 'dir',
    'apply_udiff', 'memory_add', 'memory_update', 'memory_delete',
    'search_web', 'fetch_webpage', 'screenshot_webpage',
    'image', 'audio', 'video',
}

# Reasoning/thinking command names - these are treated differently:
# their content is just text to preserve, never parsed for sub-commands
REASONING_COMMANDS = {'reasoning', 'think'}


def recover_long_form(buffer):
    """Main entry point for long-form content recovery.

    Two distinct paths:
    1. REASONING PATH: If the buffer starts with a reasoning/think command,
       treat the entire buffer as reasoning content. Never try to extract
       sub-commands from reasoning text (it often contains JSON-like snippets).
    2. COMMAND PATH: For other commands, use structural analysis to find
       the broken long-form field, extract and sanitize it, then validate
       the recovered command names against KNOWN_COMMANDS.

    Args:
        buffer (str): The malformed JSON buffer string.

    Returns:
        list or None: A list of recovered command dicts, or None if recovery failed.
    """
    if not buffer or not buffer.strip():
        return None

    buffer = buffer.strip()

    if not buffer.startswith('['):
        if buffer.startswith('{'):
            buffer = '[' + buffer
        else:
            return None

    # === REASONING PATH ===
    # If the buffer starts with a reasoning/think command, treat the ENTIRE
    # buffer as reasoning content. Never extract sub-commands from it.
    if _is_reasoning_buffer(buffer):
        return _recover_reasoning(buffer)

    # === COMMAND PATH ===
    # For non-reasoning commands, use structural analysis with strict validation.
    error_pos, error_msg = find_parse_error(buffer)
    if error_pos is None:
        try:
            cmds = json.loads(buffer)
            if isinstance(cmds, list):
                return cmds
        except Exception:
            pass
        return None

    field_name, value_start = identify_broken_field(buffer, error_pos)
    if field_name is None:
        return _simple_command_recovery(buffer)

    raw_value, value_end = extract_long_value(buffer, value_start, field_name)
    if raw_value is None:
        return _simple_command_recovery(buffer)

    sanitized_value = normalize_escaping(raw_value)
    commands = reconstruct_commands(buffer, field_name, sanitized_value, value_start, value_end)

    # Validate: only keep commands with known names
    if commands:
        commands = [c for c in commands if _is_known_command(c)]

    if commands:
        _log_recovery(len(commands), field_name, len(sanitized_value))

    return commands if commands else None


def _is_reasoning_buffer(buffer):
    """Check if the buffer starts with a reasoning/think command.

    This determines whether we take the reasoning path (preserve all text)
    or the command path (structural analysis with validation).
    """
    # Match: [{"reasoning": ... or [{"think": ...
    pattern = r'^\s*\[\s*\{\s*"(?:reasoning|think)"\s*:'
    return bool(re.match(pattern, buffer))


def _recover_reasoning(buffer):
    """Recover reasoning/think content from a malformed buffer.

    Strategy: Try json_repair on the full buffer first. If it produces
    valid commands (all known), return them. If it produces phantom
    commands (unknown names likely from reasoning content), fall back
    to manually extracting just the reasoning value.

    Args:
        buffer (str): The malformed JSON buffer starting with reasoning/think.

    Returns:
        list or None: A list with a single reasoning or think command dict.
    """
    # Try json_repair first - it might fix the whole thing
    try:
        from json_repair import repair_json
        repaired = repair_json(buffer)
        cmds = json.loads(repaired)
        if isinstance(cmds, list) and len(cmds) > 0:
            # Validate: all commands must have known names
            valid_cmds = [c for c in cmds if _is_known_command(c)]
            if len(valid_cmds) == len(cmds):
                # All commands are known - return them
                return valid_cmds
            # Some commands have unknown names - might be phantom
            # Fall through to manual extraction of just the reasoning
            pass
    except Exception:
        pass

    # Extract reasoning content ourselves
    # Find the start of the reasoning text value
    think_match = re.search(r'"extensive_chain_of_thoughts"\s*:\s*"', buffer)
    reasoning_match = re.search(r'"reasoning"\s*:\s*"', buffer)

    match = think_match or reasoning_match
    if not match:
        obj_think_match = re.search(r'"think"\s*:\s*\{\s*"extensive_chain_of_thoughts"\s*:\s*"', buffer)
        if obj_think_match:
            match = obj_think_match
            think_match = True  # treat as think match
            think_match = True
        else:
            return None

    value_start = match.end()

    # Find the actual end of the reasoning value
    raw_value, value_end = extract_long_value(buffer, value_start, 'reasoning')
    if raw_value is None:
        return None

    sanitized = normalize_escaping(raw_value)
    try:
        value = json.loads('"' + sanitized + '"')
    except Exception:
        value = raw_value

    if think_match:
        reasoning_cmd = {'think': {'extensive_chain_of_thoughts': value}}
    else:
        reasoning_cmd = {'reasoning': value}

    # Try to parse remaining buffer after reasoning for subsequent commands
    subsequent = _parse_subsequent_commands(buffer, value_end, reasoning_cmd)
    return [reasoning_cmd] + subsequent if subsequent else [reasoning_cmd]


def _parse_subsequent_commands(buffer, value_end, reasoning_cmd):
    """Try to parse commands that come after the reasoning block in the buffer.

    We build a valid JSON array by combining the reasoning command with
    the remaining buffer content, then parse and validate.
    """
    if value_end is None or value_end >= len(buffer):
        return []

    remaining = buffer[value_end:]
    # remaining starts with the close pattern, e.g. '"}, {"say": ...}]'
    # Build a valid array: [reasoning_cmd_json, ...subsequent]
    # Replace the broken reasoning value with our sanitized version
    try:
        # The remaining should close the reasoning value and open subsequent commands
        # e.g., '"}, {"say": {"text": "Hello"}}]'
        # Build: [reasoning_cmd, {"say": {"text": "Hello"}}]
        test_json = '[' + json.dumps(reasoning_cmd) + remaining.lstrip('"').lstrip() + ']'
        # This might have extra ] at the end, handle that
        parsed = json.loads(test_json, strict=False)
        if isinstance(parsed, list) and len(parsed) > 1:
            return [c for c in parsed[1:] if _is_known_command(c)]
    except Exception:
        pass

    # Try simpler approach: just look for the next command object after reasoning
    try:
        # Find the next command after the reasoning close
        # Pattern: }, {"cmd_name":
        next_cmd_pattern = r'\},\s*\{(\s*"([\\w_]+)")'
        remaining_text = buffer[value_end:]
        next_match = re.search(next_cmd_pattern, remaining_text)
        if next_match:
            cmd_name = next_match.group(2)
            if cmd_name in KNOWN_COMMANDS:
                # Try to parse from this point
                next_start = value_end + next_match.start() + 1  # after the {
                rest = '[' + buffer[next_start:].rstrip('] ').rstrip(',') + ']'
                parsed = json.loads(rest, strict=False)
                if isinstance(parsed, list):
                    return [c for c in parsed if _is_known_command(c)]
    except Exception:
        pass

    return []


def _simple_command_recovery(buffer):
    """Simple recovery for non-reasoning commands when structural analysis fails.

    Only tries json_repair. Does NOT use loose regex to find command patterns
    in the buffer (that causes phantom command extraction from reasoning content).

    Args:
        buffer (str): The malformed JSON buffer.

    Returns:
        list or None: Recovered commands, or None.
    """
    # Try json_repair
    try:
        from json_repair import repair_json
        repaired = repair_json(buffer)
        cmds = json.loads(repaired)
        if isinstance(cmds, list) and len(cmds) > 0:
            # Validate all command names
            cmds = [c for c in cmds if _is_known_command(c)]
            if cmds:
                return cmds
    except Exception:
        pass

    return None


def _is_known_command(cmd):
    """Check if a command dict has a known command name."""
    try:
        cmd_name = next(iter(cmd))
        return cmd_name in KNOWN_COMMANDS
    except Exception:
        return False


def _log_recovery(num_commands, field_name, value_len):
    """Log a successful recovery for debugging."""
    try:
        log_path = '/tmp/cmd_parse_drops.log'
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        with open(log_path, 'a') as f:
            f.write(f"\n[{timestamp}] LONG_FORM_RECOVERY succeeded - "
                    f"recovered {num_commands} command(s), "
                    f"field='{field_name}', value_len={value_len}\n")
    except Exception:
        pass


# === Structural Analysis Functions ===
# These are used only for the COMMAND PATH (non-reasoning commands)

def find_parse_error(buffer):
    """Find where JSON parsing breaks in the buffer.

    Returns:
        tuple: (error_position, error_message) or (None, None) if no error found.
    """
    try:
        json.loads(buffer)
        return None, None  # Valid JSON
    except JSONDecodeError as e:
        return e.pos, str(e)


def identify_broken_field(buffer, error_pos):
    """Identify which field in the command object contains the parse error.

    Scans backwards from the error position to find the last key-value
    separator pattern.

    Args:
        buffer (str): The full buffer.
        error_pos (int): Position where JSON parsing failed.

    Returns:
        tuple: (field_name, value_start_position) or (None, None).
    """
    prefix = buffer[:error_pos]

    # Find all key-value starts in the prefix
    # Pattern: "key_name": "  (string value being parsed)
    kv_pattern = r'"([\w_]+)"\s*:\s*"'
    matches = list(re.finditer(kv_pattern, prefix))

    if matches:
        last_match = matches[-1]
        field_name = last_match.group(1)
        value_start = last_match.end()
        return field_name, value_start

    # Also check for non-string values (objects, arrays)
    kv_obj_pattern = r'"([\w_]+)"\s*:\s*\{'
    obj_matches = list(re.finditer(kv_obj_pattern, prefix))
    if obj_matches:
        last_match = obj_matches[-1]
        field_name = last_match.group(1)
        value_start = last_match.end()
        return field_name, value_start

    return None, None


def extract_long_value(buffer, value_start, field_name=None):
    """Extract a long-form value from a malformed JSON buffer.

    Scans from value_start looking for structural close patterns.

    Args:
        buffer (str): The full buffer.
        value_start (int): Position where the value content begins.
        field_name (str, optional): The field name (used for heuristics).

    Returns:
        tuple: (raw_value_text, value_end_position) or (None, None).
    """
    close_patterns = [
        '"}}]',
        '"}}\n]',
        '"}}',
        '"}, {',
        '"},\n{',
        '"},\n\n{',
        '"}]',
    ]

    best_end = None
    for pattern in close_patterns:
        idx = buffer.find(pattern, value_start)
        if idx != -1:
            if best_end is None or idx < best_end:
                best_end = idx

    if best_end is not None:
        raw = buffer[value_start:best_end]
        return raw, best_end

    # No close pattern found - try to find a reasonable end
    if buffer.rstrip().endswith(']'):
        stripped = buffer.rstrip()
        temp = stripped[:-1].rstrip()
        if temp.endswith('}'):
            temp = temp[:-1].rstrip()
        if temp.endswith('"'):
            raw = buffer[value_start:len(temp)]
            return raw, len(temp)

    # Last resort: take everything from value_start to end of buffer
    raw = buffer[value_start:]
    raw = raw.rstrip('"}]\n ')
    if raw:
        return raw, len(buffer)

    return None, None


def normalize_escaping(raw_text):
    """Normalize escaping in raw text to produce a valid JSON string value.

    Preserves already-escaped sequences while fixing broken ones.

    Args:
        raw_text (str): The raw text that may have escaping issues.

    Returns:
        str: Text with valid JSON escaping.
    """
    result = []
    i = 0
    while i < len(raw_text):
        if raw_text[i] == '\\':
            if i + 1 < len(raw_text):
                next_ch = raw_text[i + 1]
                if next_ch in '"\\/bfnrt':
                    result.append('\\')
                    result.append(next_ch)
                    i += 2
                    continue
                elif next_ch == 'u':
                    if i + 5 < len(raw_text) and all(
                        c in '0123456789abcdefABCDEF' for c in raw_text[i+2:i+6]
                    ):
                        result.append(raw_text[i:i+6])
                        i += 6
                        continue
                    result.append('\\\\')
                    i += 1
                    continue
                else:
                    # Invalid escape - escape the backslash
                    result.append('\\\\')
                    result.append(next_ch)
                    i += 2
                    continue
            else:
                result.append('\\\\')
                i += 1
                continue

        ch = raw_text[i]
        if ch == '"':
            result.append('\\"')
        elif ch == '\n':
            result.append('\\n')
        elif ch == '\r':
            result.append('\\r')
        elif ch == '\t':
            result.append('\\t')
        elif ch == '\b':
            result.append('\\b')
        elif ch == '\f':
            result.append('\\f')
        elif ord(ch) < 0x20:
            result.append(f'\\u{ord(ch):04x}')
        else:
            result.append(ch)
        i += 1

    return ''.join(result)


def reconstruct_commands(buffer, field_name, sanitized_value, value_start, value_end):
    """Reconstruct valid command objects from the buffer.

    Args:
        buffer (str): The original malformed buffer.
        field_name (str): The name of the long-form field.
        sanitized_value (str): The sanitized value (already JSON-escaped).
        value_start (int): Where the value content begins.
        value_end (int): Where the value content ends.

    Returns:
        list: A list of recovered command dicts.
    """
    value_quote_start = value_start - 1
    if value_quote_start >= 0 and buffer[value_quote_start] == '"':
        pass
    else:
        for j in range(value_start - 1, max(value_start - 10, -1), -1):
            if buffer[j] == '"':
                value_quote_start = j
                break

    remainder = buffer[value_end:]

    close_quote_pos = None
    if remainder.startswith('"'):
        close_quote_pos = 0
    else:
        for j in range(len(remainder)):
            if remainder[j] == '"' and (j == 0 or remainder[j-1] != '\\'):
                close_quote_pos = j
                break

    if close_quote_pos is not None:
        after_value = remainder[close_quote_pos + 1:]
    else:
        after_value = remainder

    prefix = buffer[:value_quote_start]
    reconstructed = prefix + '"' + sanitized_value + '"' + after_value

    try:
        cmds = json.loads(reconstructed, strict=False)
        if isinstance(cmds, list):
            return cmds
    except Exception:
        pass

    return extract_single_command(buffer, field_name, sanitized_value, value_start, value_end)


def extract_single_command(buffer, field_name, sanitized_value, value_start, value_end):
    """Extract a single command from the buffer when full reconstruction fails.

    Args:
        buffer (str): The original malformed buffer.
        field_name (str): The name of the long-form field.
        sanitized_value (str): The sanitized value.
        value_start (int): Where the value content begins.
        value_end (int): Where the value content ends.

    Returns:
        list: A list containing the single recovered command, or empty list.
    """
    prefix = buffer[:value_start]

    cmd_pattern = r'\{\s*"([\w_]+)"\s*:\s*\{'
    matches = list(re.finditer(cmd_pattern, prefix))

    if not matches:
        cmd_pattern = r'\{\s*"([\w_]+)"\s*:'
        matches = list(re.finditer(cmd_pattern, prefix))

    if matches:
        last_match = matches[-1]
        cmd_name = last_match.group(1)

        # Validate command name
        if cmd_name not in KNOWN_COMMANDS:
            return []

        cmd_start = last_match.start()
        cmd_prefix = buffer[cmd_start:value_start]

        other_args = {}
        arg_pattern = r'"([\w_]+)"\s*:\s*(?:"([^"]*)"|([0-9]+|true|false|null))'
        arg_matches = list(re.finditer(arg_pattern, cmd_prefix))
        for am in arg_matches:
            key = am.group(1)
            if key == cmd_name:
                continue
            if am.group(2) is not None:
                other_args[key] = am.group(2)
            elif am.group(3) is not None:
                val = am.group(3)
                if val == 'true':
                    other_args[key] = True
                elif val == 'false':
                    other_args[key] = False
                elif val == 'null':
                    other_args[key] = None
                else:
                    try:
                        other_args[key] = int(val)
                    except ValueError:
                        other_args[key] = val

        try:
            value_json = json.loads('"' + sanitized_value + '"')
        except Exception:
            value_json = sanitized_value

        other_args[field_name] = value_json
        return [{cmd_name: other_args}]

    return []
