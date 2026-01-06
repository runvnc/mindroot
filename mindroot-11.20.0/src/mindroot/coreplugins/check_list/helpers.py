"""
Helper functions for nested subtask handling in the checklist system.

This module provides utilities for:
- Finding nested subtasks within parent task bodies
- Updating nested subtask completion status
- Managing hierarchical task structures
"""
import re
from typing import Dict, List, Optional, Tuple, Any

def find_nested_subtask(subtask_id: str, tasks: List[Dict]) -> Dict[str, Any]:
    """
    Search for a nested subtask within all top-level tasks.
    
    Args:
        subtask_id: The label of the nested subtask to find
        tasks: List of top-level task dictionaries
    
    Returns:
        Dictionary with:
        - found: bool - Whether the nested subtask was found
        - nested_task: dict - The nested task if found
        - nested_index: int - Index of nested task within parent
        - parent_task: dict - The parent task containing the nested task
        - parent_index: int - Index of parent task in main list
        - parent_nested_tasks: list - All nested tasks from the parent
    """
    from .mod import _parse
    for parent_index, parent_task in enumerate(tasks):
        nested_tasks = _parse(parent_task['body'])
        for nested_index, nested_task in enumerate(nested_tasks):
            if nested_task['label'] == subtask_id:
                return {'found': True, 'nested_task': nested_task, 'nested_index': nested_index, 'parent_task': parent_task, 'parent_index': parent_index, 'parent_nested_tasks': nested_tasks}
    return {'found': False}

def update_nested_subtask_status(parent_task: Dict, nested_index: int, nested_tasks: List[Dict], done: bool) -> str:
    """
    Update the completion status of a nested subtask within its parent's body.
    
    Args:
        parent_task: The parent task dictionary
        nested_index: Index of the nested task to update
        nested_tasks: List of all nested tasks from the parent
        done: New completion status
    
    Returns:
        Updated body text for the parent task
    """
    nested_tasks[nested_index]['done'] = done
    body_lines = parent_task['body'].splitlines()
    updated_lines = []
    nested_task_line_indices = []
    for i, line in enumerate(body_lines):
        stripped = line.lstrip()
        if stripped.startswith('- [ ]') or stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            nested_task_line_indices.append(i)
    current_nested_idx = 0
    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        stripped = line.lstrip()
        if stripped.startswith('- [ ]') or stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            if current_nested_idx < len(nested_tasks):
                indent = len(line) - len(stripped)
                checkbox = '- [x]' if nested_tasks[current_nested_idx]['done'] else '- [ ]'
                updated_line = ' ' * indent + checkbox + ' ' + nested_tasks[current_nested_idx]['label']
                updated_lines.append(updated_line)
                current_nested_idx += 1
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
        i += 1
    return '\n'.join(updated_lines)

def resolve_subtask_id_with_nesting(subtask_id: Any, tasks: List[Dict], cursor: int) -> Tuple[int, Optional[Dict]]:
    """
    Resolve a subtask_id to an index, checking both top-level and nested tasks.
    
    Args:
        subtask_id: The subtask identifier (int, string, or None)
        tasks: List of top-level tasks
        cursor: Current cursor position
    
    Returns:
        Tuple of (index, nested_info)
        - index: The resolved index (-1 if not found)
        - nested_info: Dict with nested task info if found, None if top-level
    """
    if subtask_id is None or subtask_id == -1:
        return (cursor, None)
    if isinstance(subtask_id, int):
        idx = subtask_id - 1
        if 0 <= idx < len(tasks):
            return (idx, None)
        else:
            return (-1, None)
    for i, task in enumerate(tasks):
        if task['label'] == subtask_id:
            return (i, None)
    nested_result = find_nested_subtask(subtask_id, tasks)
    if nested_result['found']:
        return (nested_result['parent_index'], nested_result)
    return (-1, None)

def format_nested_task_status(nested_info: Dict) -> str:
    """
    Format a nested task for display.
    
    Args:
        nested_info: Dictionary containing nested task information
    
    Returns:
        Formatted string showing the nested task status
    """
    nested_task = nested_info['nested_task']
    parent_task = nested_info['parent_task']
    status = '✅' if nested_task['done'] else '❌'
    return f"{status} **Nested Subtask**: {nested_task['label']} (within '{parent_task['label']}')\n{nested_task['body']}"

def get_next_incomplete_task(tasks: List[Dict], current_cursor: int) -> int:
    """
    Find the next incomplete task starting from the given cursor position.
    
    Args:
        tasks: List of top-level tasks
        current_cursor: Current cursor position
    
    Returns:
        Index of next incomplete task, or len(tasks) if all complete
    """
    return next((i for i, t in enumerate(tasks[current_cursor:], current_cursor) if not t['done']), len(tasks))

def has_incomplete_nested_tasks(task: Dict) -> bool:
    """
    Check if a task has any incomplete nested subtasks.
    
    Args:
        task: Task dictionary to check
    
    Returns:
        True if there are incomplete nested tasks, False otherwise
    """
    from .mod import _parse
    nested_tasks = _parse(task['body'])
    return any((not nested_task['done'] for nested_task in nested_tasks))