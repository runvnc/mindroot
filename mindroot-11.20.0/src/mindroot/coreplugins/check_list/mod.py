"""
checklist helper for an LLM-agent system
————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
Purpose
-------

• Parse a Markdown checklist section where each subtask is written as a task-list line
• Store parsed tasks + cursor in `context.data['checklist']`
• Support nested subtasks within parent task bodies
• Runtime helpers for managing both top-level and nested subtasks

`complete_subtask` and other commands live at module level so the agent can call them
as tools. No third-party deps—only Python's `re` module.
"""
import re
from lib.providers.commands import command, command_manager
from lib.providers.services import service
import traceback
from collections import Counter
from .helpers import find_nested_subtask, update_nested_subtask_status, resolve_subtask_id_with_nesting, format_nested_task_status, get_next_incomplete_task, has_incomplete_nested_tasks

def _parse(text):
    """Simple, robust checklist parser.
    
    Finds checklist items (- [ ] or - [x]) at any indentation level,
    but only processes items at the same indentation as the first one found.
    
    Returns list of {label, body, done} dicts.
    """
    lines = text.splitlines()
    tasks = []
    i = 0
    first_task_indent = None
    task_indents = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('- [ ]') or stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            indent = len(line) - len(stripped)
            task_indents.append(indent)
    if not task_indents:
        return tasks
    reference_indent = min(task_indents)
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith('- [ ]') or stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            current_indent = len(line) - len(stripped)
            if current_indent == reference_indent:
                done = stripped.startswith('- [x]') or stripped.startswith('- [X]')
                if stripped.startswith('- [ ]'):
                    label = stripped[5:].strip()
                else:
                    label = stripped[5:].strip()
                body_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.lstrip()
                    next_indent = len(next_line) - len(next_stripped)
                    if (next_stripped.startswith('- [ ]') or next_stripped.startswith('- [x]') or next_stripped.startswith('- [X]')) and next_indent <= reference_indent:
                        break
                    if next_stripped.startswith('#'):
                        break
                    body_lines.append(next_line)
                    i += 1
                tasks.append({'label': label, 'body': '\n'.join(body_lines), 'done': done})
                continue
        i += 1
    return tasks

def extract_checklist_section(md: str):
    """Extract checklist items from the entire markdown text.
    
    No longer requires a specific 'Checklist' heading - processes the entire text
    and extracts only top-level checklist items, leaving nested ones intact.
    """
    return md

def _state(ctx):
    """Return the mutable checklist state in ctx.data."""
    return ctx.data.setdefault('checklist', {'tasks': [], 'cursor': 0})

def load_checklist(md: str, ctx):
    """Parse markdown and reset cursor to first unchecked subtask."""
    st = _state(ctx)
    st['tasks'] = _parse(md)
    st['cursor'] = next((i for i, t in enumerate(st['tasks']) if not t['done']), len(st['tasks']))

@service()
async def load_checklist_from_instructions(md: str, context=None):
    """Load checklist from instructions.
    
    Processes the entire text and extracts top-level checklist items.
    """
    checklist_section = extract_checklist_section(md)
    load_checklist(checklist_section, context)
    return f'Loaded checklist from instructions.\n\n{_format_checklist_status(context)}'

def _resolve_subtask_id(subtask_id, context):
    """Resolve a subtask_id to an index (0-based) with nested task support.
    
    subtask_id can be:
    - A number (1-based index, converted to 0-based)
    - A string matching a subtask label (top-level or nested)
    - None/default (-1) to use the current cursor position
    
    Returns tuple of (index, nested_info) where nested_info is None for top-level tasks
    """
    st = _state(context)
    return resolve_subtask_id_with_nesting(subtask_id, st['tasks'], st['cursor'])

def _format_checklist_status(context):
    """Format the full checklist status as a markdown string."""
    st = _state(context)
    if not st['tasks']:
        return '_No checklist found. Make sure to include a checklist in your instructions._'
    lines = ['### Checklist Status\n']
    for i, task in enumerate(st['tasks']):
        if i == st['cursor']:
            status = '➡️ '
        elif task['done']:
            status = '✅ '
        else:
            status = '❌ '
        lines.append(f"{status}**Subtask**: {task['label']}")
        nested_tasks = _parse(task['body'])
        if nested_tasks:
            for nested_task in nested_tasks:
                nested_status = '✅' if nested_task['done'] else '❌'
                lines.append(f"  {nested_status} {nested_task['label']}")
    return '\n'.join(lines)

@command()
async def complete_subtask(subtask_id=None, context=None):
    """
    Mark a subtask complete and return a Markdown status message.
    Now supports both top-level and nested subtasks.
    
    Parameters:
    - subtask_id: Optional. The subtask to complete, specified by:
                 - The exact subtask label text (top-level or nested)
                 - Omit to complete the current subtask
    
    Example:
    { "complete_subtask": {} }  # Complete current subtask
    { "complete_subtask": { "subtask_id": "Review documents" } }  # Complete by label
    { "complete_subtask": { "subtask_id": "USP" } }  # Complete nested subtask
    """
    if context is None:
        return '_Context is required._'
    st = _state(context)
    if not st['tasks']:
        try:
            instructions = context.agent['instructions']
            await load_checklist_from_instructions(instructions, context)
        except Exception as e:
            trace = traceback.format_exc()
            return '_No checklist found. Make sure to include a checklist in your instructions._'
    idx, nested_info = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st['tasks']):
        return '_Invalid subtask identifier._'
    if nested_info is not None:
        nested_info['nested_task']['done'] = True
        parent_task = st['tasks'][idx]
        updated_body = update_nested_subtask_status(parent_task, nested_info['nested_index'], nested_info['parent_nested_tasks'], True)
        parent_task['body'] = updated_body
        all_nested_complete = all((task['done'] for task in nested_info['parent_nested_tasks']))
        if all_nested_complete:
            parent_task['done'] = True
            st['cursor'] = get_next_incomplete_task(st['tasks'], idx + 1)
        completed_msg = f"Completed Nested Subtask: - [x] {nested_info['nested_task']['label']} (within '{parent_task['label']}')"
        if all_nested_complete:
            completed_msg += f"\n\nParent task '{parent_task['label']}' is now complete!"
        if st['cursor'] >= len(st['tasks']):
            return f'{completed_msg}\n\nAll subtasks complete ✅\n\n{_format_checklist_status(context)}'
        next_task = st['tasks'][st['cursor']]
        return f"{completed_msg}\n\nNext subtask (Subtask {st['cursor'] + 1})\n- [ ] {next_task['label']}\n{next_task['body']}\n\n{_format_checklist_status(context)}"
    done_task = st['tasks'][idx]
    done_task['done'] = True
    st['cursor'] = get_next_incomplete_task(st['tasks'], idx + 1)
    completed = f"Completed Subtask {idx + 1}: - [x] {done_task['label']}"
    if st['cursor'] >= len(st['tasks']):
        return f'{completed}\n\nAll subtasks complete ✅\n\n{_format_checklist_status(context)}'
    next_task = st['tasks'][st['cursor']]
    return f"{completed}\n\nNext subtask (Subtask {st['cursor'] + 1})\n- [ ] {next_task['label']}\n{next_task['body']}\n\n{_format_checklist_status(context)}"

@command()
async def goto_subtask(subtask_id, context=None):
    """
    Move to a specific subtask without changing its completion status.
    Now supports both top-level and nested subtasks.
    
    Parameters:
    - subtask_id: Required. The subtask to navigate to, specified by:
                 - The exact subtask label text (top-level or nested)
    
    Example:
    { "goto_subtask": { "subtask_id": "Data analysis" } }  # Go to top-level task
    { "goto_subtask": { "subtask_id": "USP" } }  # Go to nested task
    """
    if context is None:
        return '_Context is required._'
    st = _state(context)
    if not st['tasks']:
        return '_No checklist found. Make sure to include a checklist in your instructions._'
    idx, nested_info = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st['tasks']):
        return '_Invalid subtask identifier._'
    st['cursor'] = idx
    if nested_info is not None:
        return f'Moved to Nested Subtask: {format_nested_task_status(nested_info)}\n\n{_format_checklist_status(context)}'
    current_task = st['tasks'][idx]
    status = '✅' if current_task['done'] else '❌'
    return f"Moved to Subtask {idx + 1}: {status} {current_task['label']}\n{current_task['body']}\n\n{_format_checklist_status(context)}"

@command()
async def clear_subtask(subtask_id=None, context=None):
    """
    Mark a subtask as incomplete (not done).
    Now supports both top-level and nested subtasks.
    
    Parameters:
    - subtask_id: Optional. The subtask to clear, specified by:
                 - The exact subtask label text (top-level or nested)
                 - Omit to clear the current subtask
    
    Example:
    { "clear_subtask": {} }  # Clear current subtask
    { "clear_subtask": { "subtask_id": "Review documents" } }  # Clear top-level by label
    { "clear_subtask": { "subtask_id": "USP" } }  # Clear nested subtask
    """
    if context is None:
        return '_Context is required._'
    st = _state(context)
    if not st['tasks']:
        return '_No checklist found. Make sure to include a checklist in your instructions._'
    idx, nested_info = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st['tasks']):
        return '_Invalid subtask identifier._'
    if nested_info is not None:
        nested_task = nested_info['nested_task']
        was_done = nested_task['done']
        nested_task['done'] = False
        parent_task = st['tasks'][idx]
        updated_body = update_nested_subtask_status(parent_task, nested_info['nested_index'], nested_info['parent_nested_tasks'], False)
        parent_task['body'] = updated_body
        if parent_task['done'] and has_incomplete_nested_tasks(parent_task):
            parent_task['done'] = False
        if idx <= st['cursor']:
            st['cursor'] = idx
        action = 'Cleared' if was_done else 'Already clear'
        return f"{action} Nested Subtask: - [ ] {nested_task['label']} (within '{parent_task['label']}')\nCurrent subtask is now Subtask {st['cursor'] + 1}\n\n{_format_checklist_status(context)}"
    task = st['tasks'][idx]
    was_done = task['done']
    task['done'] = False
    if idx <= st['cursor']:
        st['cursor'] = idx
    action = 'Cleared' if was_done else 'Already clear'
    return f"{action} Subtask {idx + 1}: - [ ] {task['label']}\nCurrent subtask is now Subtask {st['cursor'] + 1}\n\n{_format_checklist_status(context)}"

@command()
async def get_checklist_status(context=None):
    """
    Show the full status of the checklist.
    
    Example:
    { "get_checklist_status": {} }
    """
    if context is None:
        return '_Context is required._'
    return _format_checklist_status(context)

@command()
async def get_parsed_subtasks(subtask_id=None, context=None):
    """
    Return parsed subtasks with their name/id and body for verification.
    Now supports getting nested subtasks from within parent tasks.
    
    Parameters:
    - subtask_id: Optional. If provided, parse subtasks from the body of this specific subtask.
                 If omitted, returns all top-level subtasks from the main checklist.
    
    Returns a list of dictionaries with:
    - label: The subtask name/label
    - body: The subtask body content
    - done: Whether the subtask is marked as complete
    - index: The 0-based index of the subtask
    
    Example:
    { "get_parsed_subtasks": {} }  # Get all top-level subtasks
    { "get_parsed_subtasks": { "subtask_id": "Research phase" } }  # Get nested subtasks from "Research phase"
    { "get_parsed_subtasks": { "subtask_id": "Core" } }  # Get nested subtasks from "Core"
    """
    if context is None:
        return '_Context is required._'
    st = _state(context)
    if not st['tasks']:
        try:
            instructions = context.agent['instructions']
            await load_checklist_from_instructions(instructions, context)
            st = _state(context)
        except Exception as e:
            return '_No checklist found. Make sure to include a checklist in your instructions._'
    if subtask_id is None:
        result = []
        for i, task in enumerate(st['tasks']):
            result.append({'index': i, 'label': task['label'], 'body': task['body'], 'done': task['done']})
        return {'source': 'top-level checklist', 'subtasks': result}
    idx, nested_info = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st['tasks']):
        return '_Invalid subtask identifier._'
    if nested_info is not None:
        target_task = nested_info['nested_task']
        source_desc = f"nested subtasks from '{target_task['label']}' (within '{nested_info['parent_task']['label']}')"
    else:
        target_task = st['tasks'][idx]
        source_desc = f"nested subtasks from '{target_task['label']}'"
    nested_tasks = _parse(target_task['body'])
    result = []
    for i, task in enumerate(nested_tasks):
        result.append({'index': i, 'label': task['label'], 'body': task['body'], 'done': task['done']})
    return {'source': source_desc, 'parent_task': {'index': idx, 'label': target_task['label'], 'done': target_task['done']}, 'subtasks': result}

@command()
async def delegate_subtask(subtask_id, details: str, agent=None, context=None):
    """
    Delegate a subtask to an agent, automatically passing the subtask body as
    instructions, along with any details you add.
    Now supports both top-level and nested subtasks.

    IMPORTANT: You can only delegate ONE task a time.
    You must wait for this task delegation to complete before issuing 
    more delegate_subtask commands.

    If agent is not specified, the current agent name will be used for the subtask.
   
    IMPORTANT: Subtask ID may only contain alphanumerics; all other special characters are invalid.

    Example:
    { "delegate_subtask": { "subtask_id": "Research", 
                            "details": "Session data in /data/sess_1234/" }} 
    { "delegate_subtask": { "subtask_id": "USP", 
                            "details": "Focus on unique selling proposition analysis" }} 

    Note that you do not need to repeat the text of the subtask item from the checklist
    in your details.
    """
    st = _state(context)
    if not st['tasks']:
        try:
            instructions = context.agent['instructions']
            await load_checklist_from_instructions(instructions, context)
        except Exception as e:
            trace = traceback.format_exc()
            return '_No checklist found. Make sure to include a checklist in your instructions._'
    idx, nested_info = _resolve_subtask_id(subtask_id, context)
    if idx < 0 or idx >= len(st['tasks']):
        return '_Invalid subtask identifier._'
    if nested_info is not None:
        current_task = nested_info['nested_task']
        task_context = f"nested subtask '{current_task['label']}' within parent task '{nested_info['parent_task']['label']}'"
    else:
        current_task = st['tasks'][idx]
        task_context = f"subtask '{current_task['label']}'"
    subtask_body = current_task['body']
    reminder = f'Important: you may see system instructions for the full process. However, you are to ONLY \ndo (or delegate) the specified part of the process and then return a task result. If you have a sub-checklist assigned,\nuse delegate_subtask as needed for complex checklist items or per user instructions.\n\nYou are working on {task_context}.'
    instructions = f'You are working as part of a multi-step process. Please complete the following subtask:\n\n{subtask_body}\n\n{details}\n\n{reminder}\n'
    if agent is None:
        agent_name = context.agent['name']
    else:
        agent_name = agent
    return await command_manager.delegate_task(instructions, agent_name, context=context)

@command()
async def create_checklist(tasks, title=None, replace=True, context=None):
    """
    Create a new checklist dynamically from a list of task descriptions.
    
    Parameters:
    - tasks: Required. List of task description strings
    - title: Optional. Title for the checklist (for display purposes)
    - replace: Optional. Whether to replace existing checklist (default: True)
    
    Example:
    { "create_checklist": { 
        "tasks": [
            "Research the topic",
            "Create outline", 
            "Write first draft",
            "Review and edit"
        ],
        "title": "Article Writing Process"
    }}
    """
    if context is None:
        return '_Context is required._'
    if not tasks or not isinstance(tasks, list):
        return '_Tasks parameter must be a non-empty list of task descriptions._'
    st = _state(context)
    if not replace and st['tasks']:
        return '_Checklist already exists. Use replace=True to overwrite it._'
    markdown_lines = []
    if title:
        markdown_lines.append(f'# {title}\n')
    for task_desc in tasks:
        if not isinstance(task_desc, str):
            return '_All tasks must be strings._'
        markdown_lines.append(f'- [ ] {task_desc.strip()}')
    markdown_text = '\n'.join(markdown_lines)
    load_checklist(markdown_text, context)
    title_text = f" '{title}'" if title else ''
    return f'Created checklist{title_text} with {len(tasks)} tasks.\n\n{_format_checklist_status(context)}'