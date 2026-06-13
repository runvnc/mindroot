#!/usr/bin/env python3
"""
xml_docstring_adapter.py

Utilities to convert tool docstrings that mention JSON examples into a compact
XML-ish tool-call syntax for low-latency voice model prompts.

The intent is pragmatic:
    - Replaces/removes the word "JSON" in common phrases.
    - Finds balanced JSON object examples in the docstring.
    - Converts simple single-tool examples like:
          {"send_dtmf": {"digits": "1"}}
      into:
          <send_dtmf digits="1"/>
    - Converts complex/general JSON objects into:
          <tool name="...">{...}</tool>
      where useful.
    - Provides a function-based helper using inspect.getdoc(fn).
"""

from __future__ import annotations

import inspect
import json
import re
from typing import Any, Callable, Dict, Iterable, Optional
from xml.sax.saxutils import escape as _xml_escape


_JSON_WORD_RE = re.compile(r"\bJSON\b", re.IGNORECASE)


def convert_docstring_json_examples_to_xml(
    docstring: str,
    *,
    prefer_attributes: bool = True,
    remove_json_word: bool = True,
    generic_tool_tag: str = "tool",
) -> str:
    """
    Convert JSON examples inside a docstring to XML-ish examples.

    Args:
        docstring: Original docstring text.
        prefer_attributes: If True, simple scalar properties become attributes.
        remove_json_word: If True, removes/replaces "JSON" wording.
        generic_tool_tag: Tag name for complex fallback examples.

    Returns:
        Converted docstring.
    """
    if not docstring:
        return ""

    text = inspect.cleandoc(docstring)

    replacements: list[tuple[int, int, str]] = []
    for start, end, obj_text in _find_json_objects(text):
        converted = json_example_to_xml(
            obj_text,
            prefer_attributes=prefer_attributes,
            generic_tool_tag=generic_tool_tag,
        )
        if converted is not None:
            replacements.append((start, end, converted))

    if replacements:
        out = []
        last = 0
        for start, end, repl in replacements:
            out.append(text[last:start])
            out.append(repl)
            last = end
        out.append(text[last:])
        text = "".join(out)

    if remove_json_word:
        text = _remove_json_word(text)

    return text


def docstring_for_function_as_xml(
    fn: Callable[..., Any],
    *,
    include_signature: bool = False,
    prefer_attributes: bool = True,
    remove_json_word: bool = True,
    generic_tool_tag: str = "tool",
) -> str:
    """
    Extract a function docstring and convert JSON examples to XML-ish examples.

    Args:
        fn: Function object.
        include_signature: If True, prepends function signature.
    """
    doc = inspect.getdoc(fn) or ""
    converted = convert_docstring_json_examples_to_xml(
        doc,
        prefer_attributes=prefer_attributes,
        remove_json_word=remove_json_word,
        generic_tool_tag=generic_tool_tag,
    )
    if include_signature:
        try:
            sig = str(inspect.signature(fn))
        except Exception:
            sig = "(...)"
        return f"{fn.__name__}{sig}\n{converted}".strip()
    return converted


def json_example_to_xml(
    json_text: str,
    *,
    prefer_attributes: bool = True,
    generic_tool_tag: str = "tool",
) -> Optional[str]:
    """
    Convert one JSON object example to XML-ish syntax.

    Examples:
        {"send_dtmf": {"digits": "1"}} -> <send_dtmf digits="1"/>
        {"hangup": {}}                  -> <hangup/>
        {"speak": {"text": "Hi"}}       -> Hi
    """
    try:
        obj = json.loads(json_text)
    except Exception:
        return None

    if not isinstance(obj, dict):
        return None

    # OpenAI-ish function-call shape.
    if "name" in obj and ("arguments" in obj or "parameters" in obj):
        name = str(obj["name"])
        args = obj.get("arguments", obj.get("parameters", {}))
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {"text": args}
        if not isinstance(args, dict):
            args = {"value": args}
        return _command_to_xml(
            name,
            args,
            prefer_attributes=prefer_attributes,
            generic_tool_tag=generic_tool_tag,
        )

    # Common command shape: {"cmd_name": {"arg": "value"}}
    if len(obj) == 1:
        name, args = next(iter(obj.items()))
        if isinstance(args, dict):
            return _command_to_xml(
                str(name),
                args,
                prefer_attributes=prefer_attributes,
                generic_tool_tag=generic_tool_tag,
            )
        return _command_to_xml(
            str(name),
            {"value": args},
            prefer_attributes=prefer_attributes,
            generic_tool_tag=generic_tool_tag,
        )

    # Multi-key object. Fall back to generic tool tag if it has a command-ish name.
    if "tool" in obj and isinstance(obj.get("tool"), str):
        name = obj["tool"]
        args = {k: v for k, v in obj.items() if k != "tool"}
        return _command_to_xml(
            str(name),
            args,
            prefer_attributes=prefer_attributes,
            generic_tool_tag=generic_tool_tag,
        )

    return f'<{generic_tool_tag}>{_xml_escape(json.dumps(obj, separators=(",", ":")))}</{generic_tool_tag}>'


def _command_to_xml(
    name: str,
    args: Dict[str, Any],
    *,
    prefer_attributes: bool,
    generic_tool_tag: str,
) -> str:
    name = _safe_tag_name(name)

    # Low-latency default: speech does not need a wrapper.
    if name == "speak":
        text = args.get("text")
        if isinstance(text, str):
            return text
        return "<speak/>"

    if prefer_attributes and _all_attr_safe(args):
        if not args:
            return f"<{name}/>"
        attrs = " ".join(
            f'{_safe_attr_name(k)}="{_escape_attr(v)}"' for k, v in args.items()
        )
        return f"<{name} {attrs}/>"

    body = json.dumps(args, separators=(",", ":"), ensure_ascii=False)
    return f'<{generic_tool_tag} name="{_escape_attr(name)}">{_xml_escape(body)}</{generic_tool_tag}>'


def _all_attr_safe(args: Dict[str, Any]) -> bool:
    for v in args.values():
        if isinstance(v, (dict, list, tuple)):
            return False
    return True


def _escape_attr(value: Any) -> str:
    if value is True:
        s = "true"
    elif value is False:
        s = "false"
    elif value is None:
        s = "null"
    else:
        s = str(value)
    return _xml_escape(s, {'"': "&quot;"})


def _safe_tag_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_.:-]+", "_", name.strip())
    if not name or not re.match(r"[A-Za-z_]", name[0]):
        name = f"tool_{name}"
    return name


def _safe_attr_name(name: str) -> str:
    return _safe_tag_name(str(name))


def _remove_json_word(text: str) -> str:
    text = re.sub(r"\bvalid\s+JSON\s+object\b", "valid tool call", text, flags=re.IGNORECASE)
    text = re.sub(r"\bJSON\s+object\b", "tool call", text, flags=re.IGNORECASE)
    text = re.sub(r"\bJSON\s+format\b", "tool-call format", text, flags=re.IGNORECASE)
    text = re.sub(r"\bas\s+JSON\b", "as a tool call", text, flags=re.IGNORECASE)
    text = _JSON_WORD_RE.sub("tool-call", text)
    return text


def _find_json_objects(text: str) -> Iterable[tuple[int, int, str]]:
    """
    Yield balanced JSON object substrings from text.

    Quote-aware and brace-aware. Only returns objects that json.loads accepts.
    """
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue

        start = i
        depth = 0
        quote: Optional[str] = None
        escape = False
        j = i
        yielded = False

        while j < n:
            ch = text[j]

            if quote:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    quote = None
                j += 1
                continue

            if ch in ("'", '"'):
                quote = ch
                j += 1
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : j + 1]
                    try:
                        json.loads(candidate)
                    except Exception:
                        break
                    yield start, j + 1, candidate
                    i = j + 1
                    yielded = True
                    break
            j += 1

        if not yielded:
            i = start + 1


if __name__ == "__main__":
    def send_dtmf(digits: str):
        """
        Send DTMF digits.

        Return JSON like:
            {"send_dtmf": {"digits": "1"}}

        For hangup:
            {"hangup": {}}

        For DB:
            {"update_db": {"employee_id": "42", "fields": {"verified": true}}}
        """
        raise NotImplementedError

    print(docstring_for_function_as_xml(send_dtmf, include_signature=True))
