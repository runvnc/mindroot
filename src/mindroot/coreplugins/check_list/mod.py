"""
checklist helper for an LLM‑agent system
—————————————————————————————————————————————————————————————————————————————
Purpose
-------
• Parse a Markdown "##\tChecklist" section where each subtask is
  written as a task‑list line:

      - [ ] label of subtask
          arbitrary markdown body… (until next task or heading)

• Store parsed tasks + cursor in `context.data['checklist']`.

• Runtime helpers:
    load_checklist(md, ctx)   → parse markdown + reset state
    complete_subtask(subtask_id, context)  → mark subtask done, advance cursor
    goto_subtask(subtask_id, context)  → move to a specific subtask
    clear_subtask(subtask_id, context)  → mark a subtask as incomplete
    get_checklist_status(context)  → show the full checklist status

`complete_subtask` and other commands live at module level so the agent can call them
as tools. No third‑party deps—only Python's `re` module.
"""

import re
from lib.providers.commands import command
from lib.providers.services import service
import traceback

# ---------- parsing ------------------------------------------------------

TASK_RE   = re.compile(r'^-\s*\[(?P<done>[ xX])\]\s*(?P<label>.*?)\s*$')
HEADER_RE = re.compile(r'^#{1,6}\s')           # any Markdown heading
CHECKLIST_HEADER_RE = re.compile(r'^#{1,6}\s+Checklist\b', re.IGNORECASE)  # Checklist heading

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


def extract_checklist_section(md: str):
    """Extract the checklist section from larger text.
    
    Looks for a heading like '# Checklist', '## Checklist', etc., and extracts
    all content from that heading until the next heading of the same or lower level,
    or the end of the text.
    
    Returns the extracted section, or the original text if no checklist section is found.
    """
    lines = md.splitlines()
    start_idx = None
    checklist_level = 0
    
    # Find the checklist heading
    for i, line in enumerate(lines):
        match = CHECKLIST_HEADER_RE.match(line)
        if match:
            start_idx = i
            # Count the number of # to determine heading level
            checklist_level = len(line) - len(line.lstrip('#'))
            break
    
    if start_idx is None:
        return md  # No checklist section found, return original text
    
    # Find the end of the section (next heading of same or lower level)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if HEADER_RE.match(lines[i]) and len(lines[i]) - len(lines[i].lstrip('#')) <= checklist_level:
            end_idx = i
            break
    
    return "\n".join(lines[start_idx:end_idx])


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


@service()
async def load_checklist_from_instructions(md: str, context=None):
    """Extract checklist section from instructions and load it.
    
    Looks for a section starting with '# Checklist' or similar heading.
    
    Example:
    { "load_checklist_from_instructions": { "md": "Full instructions with embedded checklist" } }
    """
    checklist_section = extract_checklist_section(md)
    load_checklist(checklist_section, context)
    return f"Loaded checklist from instructions.\n\n{_format_checklist_status(context)}"


# ---------- helper functions ---------------------------------------------

def _resolve_subtask_id(subtask_id, context):
    """Resolve a subtask_id to an index (0-based).
    
    subtask_id can be:
    - A number (1-based index, converted to 0-based)
    - A string matching a subtask label
    - None/default (-1) to use the current cursor position
    """
    st = _state(context)
    
    # Default to current cursor position
    if subtask_id is None or subtask_id == -1:
        return st["cursor"]
    
    # If it's a number, convert from 1-based to 0-based
    if isinstance(subtask_id, int):
        idx = subtask_id - 1
    else:
        # It's a string, try to find a matching label
        for i, task in enumerate(st["tasks"]):
            if task["label"] == subtask_id:
                return i
        # No match found
        return -1
    
    return idx


def _format_checklist_status(context):
    """Format the full checklist status as a markdown string."""
    st = _state(context)
    if not st["tasks"]:
        return "_No checklist found. Make sure to include a checklist in your instructions._"
    
    lines = ["### Checklist Status\n"]
    
    for i, task in enumerate(st["tasks"]):
        # Determine status indicator
        if i == st["cursor"]:
            status = "➡️ " # Current task
        elif task["done"]:
            status = "✅ " # Completed
        else:
            status = "❌ " # Not completed
        
        # Add task line
        lines.append(f"{status}**Subtask {i+1}**: {task['label']}")
    
    return "\n".join(lines)


# ---------- module‑level tool commands ----------------------------------

@command()
async def complete_subtask(subtask_id=None, context=None):
    """
    Mark a subtask complete and return a Markdown status message.
    
    Parameters:
    - subtask_id: Optional. The subtask to complete, specified by:
                 - A number (1-based index)
                 - The exact subtask label text
                 - Omit to complete the current subtask
    
    Example:
    { "complete_subtask": {} }  # Complete current subtask
    { "complete_subtask": { "subtask_id": 2 } }  # Complete subtask 2
    { "complete_subtask": { "subtask_id": "Review documents" } }  # Complete by label
    """
    if context is None:
        return "_Context is required._"
        
    st = _state(context)
    if not st["tasks"]:
        try:
            print("Loading checklist from instructions...")
            print("Agent is")
            print(context.agent)
            instructions = context.agent["instructions"]
            await load_checklist_from_instructions(instructions, context)
        except Exception as e:
            print(f"Error loading checklist: {e}")
            trace = traceback.format_exc()
            print(trace)
            return "_No checklist found. Make sure to include a checklist in your instructions._"
    
    idx = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st["tasks"]):
        return "_Invalid subtask identifier._"

    # mark as done
    done_task = st["tasks"][idx]
    done_task["done"] = True

    # advance cursor to next open subtask
    st["cursor"] = next(
        (i for i, t in enumerate(st["tasks"][idx + 1:], idx + 1) if not t["done"]),
        len(st["tasks"]),
    )

    # build markdown response
    completed = f"Completed Subtask {idx+1}: - [x] {done_task['label']}"
    if st["cursor"] >= len(st["tasks"]):
        return f"{completed}\n\nAll subtasks complete ✅\n\n{_format_checklist_status(context)}"

    next_task = st["tasks"][st['cursor']]
    return f"""
            {completed}

            Next subtask (Subtask {st['cursor']+1})
            - [ ] {next_task['label']}
            {next_task['body']}

            {_format_checklist_status(context)}
            """

@command()
async def goto_subtask(subtask_id, context=None):
    """
    Move to a specific subtask without changing its completion status.
    
    Parameters:
    - subtask_id: Required. The subtask to navigate to, specified by:
                 - A number (1-based index)
                 - The exact subtask label text
    
    Example:
    { "goto_subtask": { "subtask_id": 3 } }  # Go to subtask 3
    { "goto_subtask": { "subtask_id": "Data analysis" } }  # Go to by label
    """
    if context is None:
        return "_Context is required._"
        
    st = _state(context)
    if not st["tasks"]:
        return "_No checklist found. Make sure to include a checklist in your instructions._"
    
    idx = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st["tasks"]):
        return "_Invalid subtask identifier._"
    
    # Update cursor position
    st["cursor"] = idx
    
    # Get the current task
    current_task = st["tasks"][idx]
    
    # Build response
    status = "✅" if current_task["done"] else "❌"
    return (
        f"Moved to Subtask {idx+1}: {status} {current_task['label']}\n"
        f"{current_task['body']}\n\n"
        f"{_format_checklist_status(context)}"
    )


@command()
async def clear_subtask(subtask_id=None, context=None):
    """
    Mark a subtask as incomplete (not done).
    
    Parameters:
    - subtask_id: Optional. The subtask to clear, specified by:
                 - A number (1-based index)
                 - The exact subtask label text
                 - Omit to clear the current subtask
    
    Example:
    { "clear_subtask": {} }  # Clear current subtask
    { "clear_subtask": { "subtask_id": 2 } }  # Clear subtask 2
    { "clear_subtask": { "subtask_id": "Review documents" } }  # Clear by label
    """
    if context is None:
        return "_Context is required._"
        
    st = _state(context)
    if not st["tasks"]:
        return "_No checklist found. Make sure to include a checklist in your instructions._"
    
    idx = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st["tasks"]):
        return "_Invalid subtask identifier._"
    
    # Mark as not done
    task = st["tasks"][idx]
    was_done = task["done"]
    task["done"] = False
    
    # If we cleared the current or earlier task, update cursor
    if idx <= st["cursor"]:
        st["cursor"] = idx
    
    # Build response
    action = "Cleared" if was_done else "Already clear"
    return (
        f"{action} Subtask {idx+1}: - [ ] {task['label']}\n"
        f"Current subtask is now Subtask {st['cursor']+1}\n\n"
        f"{_format_checklist_status(context)}"
    )


@command()
async def get_checklist_status(context=None):
    """
    Show the full status of the checklist.
    
    Example:
    { "get_checklist_status": {} }
    """
    if context is None:
        return "_Context is required._"
    
    return _format_checklist_status(context)
