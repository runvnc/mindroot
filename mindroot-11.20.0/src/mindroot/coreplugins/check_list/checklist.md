"""
checklist.py — minimal checklist helper for an LLM‑agent system
────────────────────────────────────────────────────────────────
Purpose
-------
• Parse a Markdown “## Checklist” section where each subtask is
  written as a task‑list line:

      - [ ] label of subtask
          arbitrary markdown body… (until next task or heading)

• Store parsed tasks + cursor in `context.data['checklist']`.

• Runtime helpers:
    load_checklist(md, ctx)   → parse markdown + reset state
    current_reminder(ctx)     → body of next unchecked subtask
    complete_subtask(ctx, i)  → mark subtask done, advance cursor,
                                and *return* a Markdown summary:
        Completed: - [x] label
        Next subtask:
        - [ ] next‑label
        next body…

`complete_subtask` lives at module level so the agent can call it
as a tool.  No third‑party deps—only Python’s `re` module.
"""

import re

# ---------- parsing ------------------------------------------------------

TASK_RE   = re.compile(r'^-\s*\[(?P<done>[ xX])\]\s*(?P<label>.*?)\s*$')
HEADER_RE = re.compile(r'^#{1,6}\s')           # any Markdown heading

def _parse(md: str):
    """Extract tasks as a list of dicts: {label, body, done}."""
    lines, tasks, i = md.splitlines(), [], 0
    while i < len(lines):
        m = TASK_RE.match(lines[i])
        if not m:                            # not a task‑list line
            i += 1
            continue

        done  = m.group("done").strip().lower() in ("x", "✓")
        label = m.group("label").strip()

        # collect everything until next task or heading
        body_lines = []
        i += 1
        while i < len(lines) and not (
            TASK_RE.match(lines[i]) or HEADER_RE.match(lines[i])
        ):
            body_lines.append(lines[i])
            i += 1

        tasks.append({
            "label": label,
            "body": "\n".join(body_lines).strip(),
            "done": done,
        })
    return tasks


# ---------- state helpers ------------------------------------------------

def _state(ctx):
    """Return the mutable checklist state in ctx.data."""
    return ctx.data.setdefault("checklist", {"tasks": [], "cursor": 0})

def load_checklist(md: str, ctx):
    """Parse markdown and reset cursor to first unchecked subtask."""
    st = _state(ctx)
    st["tasks"]  = _parse(md)
    st["cursor"] = next(
        (i for i, t in enumerate(st["tasks"]) if not t["done"]),
        len(st["tasks"]),
    )

def current_reminder(ctx):
    """Return body of the current subtask or None if all done."""
    st  = _state(ctx)
    cur = st["cursor"]
    return st["tasks"][cur]["body"] if cur < len(st["tasks"]) else None


# ---------- module‑level tool command ------------------------------------

def complete_subtask(ctx, idx=None):
    """
    Mark a subtask complete and return a Markdown status message.

    If `idx` is None, completes the current cursor position.
    """
    st = _state(ctx)
    idx = st["cursor"] if idx is None else idx
    if not (0 <= idx < len(st["tasks"])):
        return "_Invalid subtask index._"

    # mark as done
    done_task = st["tasks"][idx]
    done_task["done"] = True

    # advance cursor to next open subtask
    st["cursor"] = next(
        (i for i, t in enumerate(st["tasks"][idx + 1:], idx + 1) if not t["done"]),
        len(st["tasks"]),
    )

    # build markdown response
    completed = f"Completed: - [x] {done_task['label']}"
    if st["cursor"] >= len(st["tasks"]):
        return f"{completed}\n\nAll subtasks complete ✅"

    next_task = st["tasks"][st['cursor']]
    return (
        f"{completed}\n\n"
        f"Next subtask:\n"
        f"- [ ] {next_task['label']}\n"
        f"{next_task['body']}"
    )

