#!/usr/bin/env python3
"""
xml_tool_stream_adapter.py

Streaming adapter for low-latency LLM voice output.

Goal:
    Raw text streams from an LLM. Text outside XML-ish tags is speech.
    Recognized tool tags become command calls.

Core behavior:
    - Speech outside tags is accumulated.
    - On new speech, calls partial_cmd("speak", {"text": full_text_so_far})
    - Complete tool tags call cmd(name, properties).
    - Designed for streaming chunks: feed(delta), feed(delta), finish().

Recommended model syntax:
    Normal speech directly:
        Great, let's start.

    Simple self-closing controls:
        <send_dtmf digits="1"/>
        <hangup/>
        <wait ms="500"/>
        <call number="+18005551212"/>

    General JSON-backed tools:
        <tool name="update_db">{"employee_id":"42","verified":true}</tool>

Notes:
    This is intentionally XML-ish, not a full XML parser. It is optimized for
    streaming and low latency. It is forgiving of partial tags across chunks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import html
import json
import re
from typing import Any, Callable, Dict, Iterable, List, Optional


CommandCallback = Callable[[str, Dict[str, Any]], Any]
PartialCommandCallback = Callable[[str, Dict[str, Any]], Any]


_ATTR_RE = re.compile(
    r'''([A-Za-z_][\w:.-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s/>]+))'''
)

_STRING_ATTR_KEYS = {
    # Values that should usually remain strings even if numeric-looking.
    # Tool implementations can convert these if they really want numeric values.
    "digits", "dtmf", "number", "phone", "phone_number", "extension",
    "destination", "to", "from", "caller_id", "callee", "sip_uri",
    "id", "customer_id", "employee_id", "account_id", "zipcode", "zip",
}


@dataclass
class XmlToolStreamAdapter:
    """
    Incrementally parse raw speech + XML-ish tool tags.

    Args:
        partial_cmd:
            Called for streaming speech updates:
                partial_cmd("speak", {"text": full_spoken_text_so_far})

        cmd:
            Called for complete non-speech commands:
                cmd("send_dtmf", {"digits": "1"})

        speak_command_name:
            Name used for speech partials. Defaults to "speak".

        allowed_tools:
            Optional allowlist. If set, only these tags become commands.
            Unknown tags are treated as literal speech.

        emit_partial_on_chars:
            Emit speech update every N newly accepted speech chars.
            Use 1 for lowest latency. Use e.g. 8 or 16 to reduce callback churn.

        tool_text_json:
            If True, <tool name="x">{"a":1}</tool> parses inner JSON and calls
            cmd("x", {"a":1}). If false, inner text is passed as {"text": "..."}.
    """

    partial_cmd: PartialCommandCallback
    cmd: CommandCallback
    speak_command_name: str = "speak"
    allowed_tools: Optional[set[str]] = None
    emit_partial_on_chars: int = 1
    tool_text_json: bool = True
    strict_xml_entities: bool = False
    string_attr_keys: Optional[set[str]] = None

    _buf: str = ""
    _spoken_text: str = ""
    _last_emitted_speech_len: int = 0
    _open_tool_name: Optional[str] = None
    _open_tool_attrs: Dict[str, Any] = field(default_factory=dict)
    _open_tool_text: List[str] = field(default_factory=list)

    def feed(self, delta: str) -> None:
        """Feed one streaming text delta from the LLM."""
        if not delta:
            return
        self._buf += delta
        self._drain_buffer(final=False)

    def finish(self) -> None:
        """
        Flush remaining buffered content.

        If the model ended with an incomplete tag, we conservatively speak it
        as literal text rather than dropping it.
        """
        self._drain_buffer(final=True)
        self._emit_speech(force=True)

    @property
    def spoken_text(self) -> str:
        """Full speech text accepted so far."""
        return self._spoken_text

    def reset(self) -> None:
        """Reset adapter state for a new LLM response."""
        self._buf = ""
        self._spoken_text = ""
        self._last_emitted_speech_len = 0
        self._open_tool_name = None
        self._open_tool_attrs = {}
        self._open_tool_text = []

    def _drain_buffer(self, final: bool) -> None:
        while self._buf:
            if self._open_tool_name is not None:
                if not self._drain_open_tool(final=final):
                    return
                continue

            lt = self._buf.find("<")
            if lt == -1:
                self._accept_speech(self._buf)
                self._buf = ""
                return

            if lt > 0:
                self._accept_speech(self._buf[:lt])
                self._buf = self._buf[lt:]
                continue

            # Buffer starts with '<'. Need a complete tag or final fallback.
            gt = self._find_tag_end(self._buf)
            if gt is None:
                if final:
                    self._accept_speech(self._buf)
                    self._buf = ""
                return

            raw_tag = self._buf[: gt + 1]
            self._buf = self._buf[gt + 1 :]

            handled = self._handle_tag(raw_tag)
            if not handled:
                self._accept_speech(raw_tag)

    def _drain_open_tool(self, final: bool) -> bool:
        assert self._open_tool_name is not None
        close_pat = f"</{self._open_tool_name}>"
        close_idx = self._buf.find(close_pat)

        if close_idx == -1:
            if final:
                # Treat incomplete open tool as literal speech.
                start = self._format_start_tag(self._open_tool_name, self._open_tool_attrs)
                self._accept_speech(start + "".join(self._open_tool_text) + self._buf)
                self._buf = ""
                self._open_tool_name = None
                self._open_tool_attrs = {}
                self._open_tool_text = []
                return True

            self._open_tool_text.append(self._buf)
            self._buf = ""
            return False

        inner = self._buf[:close_idx]
        self._open_tool_text.append(inner)
        self._buf = self._buf[close_idx + len(close_pat) :]

        name = self._open_tool_name
        attrs = self._open_tool_attrs
        text = "".join(self._open_tool_text)

        self._open_tool_name = None
        self._open_tool_attrs = {}
        self._open_tool_text = []

        self._emit_tool_with_text(name, attrs, text)
        return True

    def _find_tag_end(self, s: str) -> Optional[int]:
        """Return index of closing '>' for a tag starting at s[0]."""
        quote: Optional[str] = None
        for i, ch in enumerate(s):
            if i == 0:
                continue
            if quote:
                if ch == quote:
                    quote = None
                continue
            if ch in ("'", '"'):
                quote = ch
                continue
            if ch == ">":
                return i
        return None

    def _handle_tag(self, raw_tag: str) -> bool:
        raw_tag = raw_tag.strip()
        if raw_tag.startswith("</"):
            return False

        self_closing = raw_tag.endswith("/>")
        inner = raw_tag[1:-2].strip() if self_closing else raw_tag[1:-1].strip()
        if not inner:
            return False

        parts = inner.split(None, 1)
        tag_name = parts[0]
        raw_attrs = parts[1] if len(parts) > 1 else ""

        # Special generic <tool name="..."> body </tool> is always allowed.
        if self.allowed_tools is not None and tag_name not in self.allowed_tools and tag_name != "tool":
            return False

        attrs = self._parse_attrs(raw_attrs)

        if tag_name == self.speak_command_name:
            text = str(attrs.get("text", ""))
            if text:
                self._accept_speech(text)
            return True

        if self_closing:
            self._emit_simple_tool(tag_name, attrs)
            return True

        if tag_name == "tool":
            tool_name = str(attrs.get("name", "")).strip()
            if not tool_name:
                return False
            self._open_tool_name = tag_name
            self._open_tool_attrs = attrs
            self._open_tool_text = []
            return True

        if self.allowed_tools is not None and tag_name in self.allowed_tools:
            self._open_tool_name = tag_name
            self._open_tool_attrs = attrs
            self._open_tool_text = []
            return True

        return False

    def _parse_attrs(self, raw_attrs: str) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {}
        for m in _ATTR_RE.finditer(raw_attrs):
            key = m.group(1)
            val = next(g for g in m.groups()[1:] if g is not None)
            if self.strict_xml_entities:
                val = html.unescape(val)
            attrs[key] = self._coerce_scalar(key, val)
        return attrs

    def _coerce_scalar(self, key: str, val: str) -> Any:
        v = val.strip()

        # Preserve identifiers and DTMF/phone strings. Leading zeros matter.
        string_keys = self.string_attr_keys if self.string_attr_keys is not None else _STRING_ATTR_KEYS
        if key.lower() in string_keys:
            return v

        if v.lower() == "true":
            return True
        if v.lower() == "false":
            return False
        if v.lower() in ("null", "none"):
            return None

        if any(ch in v for ch in ("#", "*", "+")):
            return v

        try:
            if re.fullmatch(r"-?\d+", v):
                return int(v)
            if re.fullmatch(r"-?\d+\.\d+", v):
                return float(v)
        except Exception:
            pass
        return v

    def _accept_speech(self, text: str) -> None:
        if not text:
            return
        if self.strict_xml_entities:
            text = html.unescape(text)

        if self._open_tool_name is not None:
            self._open_tool_text.append(text)
            return

        self._spoken_text += text
        self._emit_speech(force=False)

    def _emit_speech(self, force: bool) -> None:
        if not self._spoken_text:
            return
        pending = len(self._spoken_text) - self._last_emitted_speech_len
        if pending <= 0:
            return
        if not force and pending < max(1, self.emit_partial_on_chars):
            return
        self.partial_cmd(self.speak_command_name, {"text": self._spoken_text})
        self._last_emitted_speech_len = len(self._spoken_text)

    def _emit_simple_tool(self, tag_name: str, attrs: Dict[str, Any]) -> None:
        # Flush speech before executing a control command.
        self._emit_speech(force=True)
        self.cmd(tag_name, attrs)

    def _emit_tool_with_text(self, tag_name: str, attrs: Dict[str, Any], text: str) -> None:
        self._emit_speech(force=True)

        if tag_name == "tool":
            name = str(attrs.get("name", "")).strip()
            props = dict(attrs)
            props.pop("name", None)

            body = text.strip()
            if body:
                if self.tool_text_json:
                    try:
                        parsed = json.loads(body)
                        if isinstance(parsed, dict):
                            props.update(parsed)
                        else:
                            props["value"] = parsed
                    except json.JSONDecodeError:
                        props["text"] = body
                else:
                    props["text"] = body
            self.cmd(name, props)
            return

        props = dict(attrs)
        body = text.strip()
        if body:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    props.update(parsed)
                else:
                    props["value"] = parsed
            except json.JSONDecodeError:
                props["text"] = body
        self.cmd(tag_name, props)

    def _format_start_tag(self, name: str, attrs: Dict[str, Any]) -> str:
        if not attrs:
            return f"<{name}>"
        parts = []
        for k, v in attrs.items():
            parts.append(f'{k}="{html.escape(str(v), quote=True)}"')
        return f"<{name} {' '.join(parts)}>"


def adapt_stream(
    chunks: Iterable[str],
    partial_cmd: PartialCommandCallback,
    cmd: CommandCallback,
    **kwargs: Any,
) -> XmlToolStreamAdapter:
    """Convenience helper for non-async iterables of chunks."""
    adapter = XmlToolStreamAdapter(partial_cmd=partial_cmd, cmd=cmd, **kwargs)
    for chunk in chunks:
        adapter.feed(chunk)
    adapter.finish()
    return adapter


if __name__ == "__main__":
    events = []

    def partial(name: str, props: Dict[str, Any]) -> None:
        events.append(("partial", name, props))

    def command(name: str, props: Dict[str, Any]) -> None:
        events.append(("cmd", name, props))

    adapter = XmlToolStreamAdapter(partial_cmd=partial, cmd=command)
    for c in [
        "Please hold while I select ",
        "support. <send_dtmf digits=\"2\"/>",
        " Thanks.",
        " <tool name=\"update_db\">{\"verified\":true}</tool>",
    ]:
        adapter.feed(c)
    adapter.finish()

    for e in events:
        print(e)
