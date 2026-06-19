#!/usr/bin/env python3
"""
xml_stream_events.py

Event-emitting wrapper around XmlToolStreamAdapter for first-class XML command
streaming in the agent loop (no XML -> JSON-string -> reparse round trip).

feed()/finish() return an ordered list of structured events that an async caller
processes in order. Events mirror what the JSON command loop produces for a turn,
so downstream behavior (especially realtime TTS) is unchanged:

    {'kind': 'speak_partial', 'text': <growing text for the CURRENT speech segment>}
    {'kind': 'speak_final',   'text': <full text of the just-completed segment>}
    {'kind': 'cmd',           'name': <tool_name>, 'props': <dict_of_args>}

Why segments:
  The mr_kyutai partial_command pipe treats each speak command as a growing,
  prefix-diffed string and resets between commands. Speech is naturally
  segmented by tool tags (the adapter force-flushes speech before a tool) and by
  end-of-turn. Each segment maps to one streamed speak command:
      speak_partial* -> speak_final
  exactly like the JSON path emits partial_command('speak', growing) repeatedly
  and then executes the final speak command at the boundary.

  'speak_partial' carries text RELATIVE TO THE CURRENT SEGMENT (not cumulative
  across the whole turn), so the TTS prefix-diff starts fresh each segment, the
  same as when the JSON pipe opens a new speak command.

The adapter is forgiving: incomplete/unknown tags are spoken as literal text on
finish() rather than raising, so there is no 'invalid format' error path.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .xml_tool_stream_adapter_v3 import XmlToolStreamAdapter


class XmlEventStream:
    """Collects ordered speak/cmd events from streamed XML-ish model output."""

    def __init__(
        self,
        speak_command_name: str = 'speak',
        emit_partial_on_chars: int = 1,
        allowed_tools: Optional[set] = None,
        string_attr_keys: Optional[set] = None,
    ) -> None:
        self._events: List[Dict[str, Any]] = []
        self.speak_command_name = speak_command_name

        # Offset (within adapter.spoken_text) where the current speech segment
        # begins. Advanced to the current spoken length each time a tool fires.
        self._seg_base = 0

        def on_partial(name: str, props: Dict[str, Any]) -> None:
            if name != self.speak_command_name:
                return
            full = props.get('text', '') or ''
            seg = full[self._seg_base:]
            # Ignore pure-whitespace segments (models pad tool-only responses
            # with newlines/spaces around tags).
            if not seg.strip():
                return
            self._events.append({'kind': 'speak_partial', 'text': seg})

        def on_cmd(name: str, props: Dict[str, Any]) -> None:
            # Close the current speech segment (if it has real speech) before the
            # tool, then advance the segment base so the next segment is fresh.
            full = self._adapter.spoken_text
            seg = full[self._seg_base:]
            if seg.strip():
                self._events.append({'kind': 'speak_final', 'text': seg})
            self._seg_base = len(full)
            self._events.append({'kind': 'cmd', 'name': name, 'props': props})

        self._adapter = XmlToolStreamAdapter(
            partial_cmd=on_partial,
            cmd=on_cmd,
            speak_command_name=speak_command_name,
            emit_partial_on_chars=emit_partial_on_chars,
            allowed_tools=allowed_tools,
            string_attr_keys=string_attr_keys,
        )

    def feed(self, delta: str) -> List[Dict[str, Any]]:
        """Feed a streaming text delta; return any newly produced events."""
        self._adapter.feed(delta)
        return self._drain()

    def finish(self) -> List[Dict[str, Any]]:
        """Flush remaining buffered content; emit a final speak segment if any."""
        self._adapter.finish()
        # Close the trailing speech segment (no tool boundary will do it).
        full = self._adapter.spoken_text
        seg = full[self._seg_base:]
        if seg.strip():
            self._events.append({'kind': 'speak_final', 'text': seg})
            self._seg_base = len(full)
        return self._drain()

    @property
    def spoken_text(self) -> str:
        return self._adapter.spoken_text

    def _drain(self) -> List[Dict[str, Any]]:
        if not self._events:
            return []
        out = self._events
        self._events = []
        return out
