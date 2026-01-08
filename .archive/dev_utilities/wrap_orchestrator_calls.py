#!/usr/bin/env python3
"""
Safely wrap all unwrapped orchestrator.process_request() calls with safe_orchestrator_call()
This script is careful to preserve formatting and handle nested structures properly.
"""

import re
import sys
from pathlib import Path

# Files to process
COMMAND_FILES = [
    "socratic_system/ui/commands/conv_commands.py",
    "socratic_system/ui/commands/github_commands.py",
    "socratic_system/ui/commands/collab_commands.py",
    "socratic_system/ui/commands/doc_commands.py",
    "socratic_system/ui/commands/finalize_commands.py",
    "socratic_system/ui/commands/llm_commands.py",
    "socratic_system/ui/commands/maturity_commands.py",
    "socratic_system/ui/commands/note_commands.py",
    "socratic_system/ui/commands/session_commands.py",
    "socratic_system/ui/commands/stats_commands.py",
    "socratic_system/ui/commands/system_commands.py",
    "socratic_system/ui/commands/user_commands.py",
    "socratic_system/ui/commands/project_commands.py",
]

def process_file(file_path):
    """Process a single command file"""
    full_path = Path(file_path)

    if not full_path.exists():
        print(f"[SKIP] {file_path} - does not exist")
        return False

    # Read file with UTF-8 encoding
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(full_path, 'r', encoding='latin-1') as f:
            content = f.read()

    # Count unwrapped calls
    unwrapped_count = len(re.findall(r'orchestrator\.process_request\(', content))

    if unwrapped_count == 0:
        print(f"[OK] {file_path} - 0 unwrapped calls")
        return True

    print(f"[PROCESS] {file_path} - {unwrapped_count} unwrapped calls to fix")

    # Add import if not present
    if "safe_orchestrator_call" not in content:
        # Find the import section
        import_pattern = r'(from socratic_system\.ui\.commands\.base import BaseCommand)'
        replacement = r'\1\nfrom socratic_system.utils.orchestrator_helper import safe_orchestrator_call'
        content = re.sub(import_pattern, replacement, content)
        print(f"  -> Added safe_orchestrator_call import")

    # Replace orchestrator.process_request with safe_orchestrator_call
    # Pattern: orchestrator.process_request( ... ) where ... can span multiple lines

    # For simplicity, we'll use a regex that finds:
    # orchestrator.process_request(\n    "agent_name",\n    {...}\n)
    # and wraps it properly

    def wrap_orchestrator_call(match):
        """Wrap a matched orchestrator.process_request call"""
        full_match = match.group(0)
        indent = match.group(1)

        # Extract the agent_name and params
        # Format: orchestrator.process_request(\n    "agent", {...}\n)
        lines = full_match.split('\n')

        # Find the agent name and parameters
        agent_match = re.search(r'"([^"]+)",', full_match)
        if not agent_match:
            return full_match  # Can't parse, return unchanged

        agent_name = agent_match.group(1)

        # Extract everything between agent name and closing paren
        # This is tricky, so we'll do a simple replacement

        # Simple case: replace orchestrator.process_request with safe_orchestrator_call
        # and restructure the parameters

        result = full_match.replace(
            'orchestrator.process_request(',
            'safe_orchestrator_call(\n' + indent + '    orchestrator,'
        )

        # Add operation_name parameter before the closing paren
        # Find the last closing paren and insert operation_name before it
        result = result.rstrip(')')
        result += f',\n{indent}    operation_name="{agent_name} operation"\n{indent})'

        return result

    # Find and wrap orchestrator.process_request calls
    # Pattern: (indentation) + orchestrator.process_request( ... )
    pattern = r'([ \t]*)orchestrator\.process_request\([^)]*\)'

    # This simple pattern won't work for multi-line calls
    # Let's use a more sophisticated approach

    # Actually, let's do this more carefully by finding the start and end of each call
    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line contains orchestrator.process_request(
        if 'orchestrator.process_request(' in line:
            # Extract indent
            indent_match = re.match(r'^(\s*)', line)
            indent = indent_match.group(1) if indent_match else ''

            # Find the matching closing paren
            paren_count = 0
            start_idx = i
            found_close = False

            for j in range(i, len(lines)):
                line_to_check = lines[j]

                # Count parens
                for char in line_to_check:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            found_close = True
                            break

                if found_close:
                    end_idx = j
                    break

            if found_close:
                # Extract the full call
                call_lines = lines[start_idx:end_idx + 1]
                call_text = '\n'.join(call_lines)

                # Parse to extract agent and params
                agent_match = re.search(r'"([^"]+)"', call_text)
                if agent_match:
                    agent_name = agent_match.group(1)

                    # Build wrapped call
                    wrapped = f'{indent}result = safe_orchestrator_call(\n'
                    wrapped += f'{indent}    orchestrator,\n'

                    # Extract the agent name line and params
                    param_start = call_text.find('orchestrator.process_request(') + len('orchestrator.process_request(')
                    param_text = call_text[param_start:-1]  # Remove final )

                    # Clean up and indent the params
                    param_lines = param_text.split('\n')
                    for param_line in param_lines:
                        if param_line.strip():
                            wrapped += f'{indent}    {param_line.strip()}\n'

                    wrapped += f'{indent}    operation_name="{agent_name} operation"\n'
                    wrapped = wrapped.rstrip('\n')
                    wrapped += f'\n{indent})'

                    # Add the wrapped call
                    new_lines.append(wrapped)

                    # Skip processed lines
                    i = end_idx + 1
                    continue

        new_lines.append(line)
        i += 1

    # Write back
    new_content = '\n'.join(new_lines)

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  -> File updated successfully")
        return True
    except Exception as e:
        print(f"  -> ERROR writing file: {e}")
        return False

def main():
    print("=" * 70)
    print("Wrapping orchestrator.process_request() calls")
    print("=" * 70)

    success_count = 0
    fail_count = 0

    for file_path in COMMAND_FILES:
        if process_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    print("=" * 70)
    print(f"Results: {success_count} processed, {fail_count} failed")
    print("=" * 70)

if __name__ == "__main__":
    main()
