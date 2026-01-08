#!/usr/bin/env python3
"""
Automatically wrap all orchestrator.process_request calls with safe_orchestrator_call.
Usage: python apply_orchestrator_fixes.py
"""

import re
from pathlib import Path

def add_import_if_needed(content):
    """Add safe_orchestrator_call import if not present"""
    if 'safe_orchestrator_call' in content:
        return content

    import_line = 'from socratic_system.utils.orchestrator_helper import safe_orchestrator_call\n'

    # Find where to insert import (after other socratic_system imports)
    lines = content.split('\n')
    insert_idx = 0

    for i, line in enumerate(lines):
        if line.startswith('from socratic_system'):
            insert_idx = i + 1

    lines.insert(insert_idx, import_line)
    return '\n'.join(lines)

def wrap_orchestrator_call(content):
    """Replace orchestrator.process_request with safe_orchestrator_call"""

    # Handle multi-line orchestrator.process_request calls
    # Pattern 1: Single line
    pattern1 = r'(\s*)result\s*=\s*orchestrator\.process_request\(\s*"([^"]+)",\s*(\{[^}]+\})\s*\)'

    def replace1(match):
        indent = match.group(1)
        agent = match.group(2)
        data = match.group(3)
        op_name = agent.replace('_', ' ')

        return f"""{indent}result = safe_orchestrator_call(
{indent}    orchestrator,
{indent}    "{agent}",
{indent}    {data},
{indent}    operation_name="{op_name} operation"
{indent})"""

    content = re.sub(pattern1, replace1, content)

    # Pattern 2: Multi-line calls (more complex)
    # This handles calls that span multiple lines
    pattern2 = r'(\s*)result\s*=\s*orchestrator\.process_request\(\s*"([^"]+)",\s*(\{[\s\S]*?\}\s*)\)'

    def replace2(match):
        indent = match.group(1)
        agent = match.group(2)
        data_block = match.group(3).strip()
        op_name = agent.replace('_', ' ')

        # Preserve indentation in data block
        data_lines = data_block.split('\n')
        data_lines = [indent + '    ' + line if line.strip() else line for line in data_lines]
        data_block = '\n'.join(data_lines)

        return f"""{indent}result = safe_orchestrator_call(
{indent}    orchestrator,
{indent}    "{agent}",
{data_block},
{indent}    operation_name="{op_name} operation"
{indent})"""

    content = re.sub(pattern2, replace2, content)

    # Pattern 3: Direct returns without assignment
    pattern3 = r'(\s*)return\s+orchestrator\.process_request\(\s*"([^"]+)",\s*(\{[\s\S]*?\}\s*)\)'

    def replace3(match):
        indent = match.group(1)
        agent = match.group(2)
        data_block = match.group(3).strip()
        op_name = agent.replace('_', ' ')

        data_lines = data_block.split('\n')
        data_lines = [indent + '    ' + line if line.strip() else line for line in data_lines]
        data_block = '\n'.join(data_lines)

        return f"""{indent}return safe_orchestrator_call(
{indent}    orchestrator,
{indent}    "{agent}",
{data_block},
{indent}    operation_name="{op_name} operation"
{indent})"""

    content = re.sub(pattern3, replace3, content)

    return content

def process_file(filepath):
    """Process a single file"""
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Try with different encoding
        content = filepath.read_text(encoding='latin-1')

    # Count orchestrator calls before
    calls_before = content.count('orchestrator.process_request(')
    calls_safe_before = content.count('safe_orchestrator_call(')

    # Apply fixes
    content = add_import_if_needed(content)
    content = wrap_orchestrator_call(content)

    # Count after
    calls_after = content.count('orchestrator.process_request(')
    calls_safe_after = content.count('safe_orchestrator_call(')

    # Only write if changes were made
    if calls_before > calls_after:
        filepath.write_text(content, encoding='utf-8')
        wrapped = calls_before - calls_after
        return filepath.name, wrapped

    return None, 0

# Target files
command_files = [
    "socratic_system/ui/commands/llm_commands.py",
    "socratic_system/ui/commands/project_commands.py",
    "socratic_system/ui/commands/session_commands.py",
    "socratic_system/ui/commands/code_commands.py",
    "socratic_system/ui/commands/note_commands.py",
    "socratic_system/ui/commands/collab_commands.py",
    "socratic_system/ui/commands/conv_commands.py",
    "socratic_system/ui/commands/maturity_commands.py",
    "socratic_system/ui/commands/finalize_commands.py",
    "socratic_system/ui/commands/github_commands.py",
    "socratic_system/ui/commands/stats_commands.py",
    "socratic_system/ui/commands/user_commands.py",
    "socratic_system/ui/commands/system_commands.py",
]

agent_files = [
    "socratic_system/agents/project_manager.py",
    "socratic_system/agents/socratic_counselor.py",
]

all_files = command_files + agent_files

print("=" * 70)
print("WRAPPING ORCHESTRATOR CALLS WITH safe_orchestrator_call")
print("=" * 70)

total_wrapped = 0

for filepath_str in all_files:
    filepath = Path(filepath_str)
    if not filepath.exists():
        continue

    filename, wrapped = process_file(filepath)
    if filename:
        total_wrapped += wrapped
        print(f"[OK] {filename}: wrapped {wrapped} call(s)")

print("=" * 70)
print(f"TOTAL WRAPPED: {total_wrapped} orchestrator calls")
print("=" * 70)
