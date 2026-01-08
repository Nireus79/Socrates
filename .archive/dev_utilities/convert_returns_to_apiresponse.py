#!/usr/bin/env python3
"""
Convert all 'return {...}' dict returns to APIResponse in router files.
Handles collaboration.py, projects.py, knowledge.py
"""

import re
from pathlib import Path


def extract_dict_return(content: str, start_pos: int) -> tuple:
    """
    Extract a complete dict return statement starting at position.
    Returns (full_statement, next_pos)
    """
    # Find the opening brace
    brace_start = content.find('{', start_pos)
    if brace_start == -1:
        return None, start_pos

    # Count braces to find matching closing brace
    brace_count = 0
    pos = brace_start
    in_string = False
    escape_next = False

    while pos < len(content):
        char = content[pos]

        if escape_next:
            escape_next = False
            pos += 1
            continue

        if char == '\\':
            escape_next = True
            pos += 1
            continue

        if char in ('"', "'"):
            in_string = not in_string
            pos += 1
            continue

        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[start_pos:pos + 1], pos + 1

        pos += 1

    return None, start_pos


def update_file(filepath: Path) -> bool:
    """Update a single file's return statements."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    updated_count = 0

    # Find all "return {" statements
    pos = 0
    while True:
        # Find next return statement
        return_pos = content.find('return ', pos)
        if return_pos == -1:
            break

        # Check if it's followed by "{"
        rest = content[return_pos + 7:].lstrip()
        if rest.startswith('{'):
            # Extract the dict return
            dict_start = content.find('{', return_pos)
            dict_return, next_pos = extract_dict_return(content, return_pos)

            if dict_return:
                # Check if already wrapped in APIResponse
                if 'APIResponse(' not in dict_return:
                    # Skip simple dict returns that are just {"status": "success", ...}
                    # and convert to APIResponse
                    try:
                        # Get indentation
                        line_start = content.rfind('\n', 0, return_pos) + 1
                        indent = ' ' * (return_pos - line_start)

                        # Replace return {...} with return APIResponse(...)
                        old_code = dict_return

                        # Parse dict content
                        dict_content = dict_return[dict_return.find('{'):dict_return.rfind('}') + 1]

                        # Create new APIResponse wrapper
                        new_code = f'{indent}return APIResponse(\n'
                        new_code += f'{indent}    success=True,\n'
                        new_code += f'{indent}    status="success",\n'
                        new_code += f'{indent}    data={dict_content},\n'
                        new_code += f'{indent})'

                        content = content[:return_pos] + new_code + content[next_pos:]
                        updated_count += 1

                        # Adjust pos for the change
                        pos = return_pos + len(new_code)
                    except Exception as e:
                        # If parsing fails, skip
                        pos = next_pos
                else:
                    pos = next_pos
            else:
                pos = return_pos + 1
        else:
            pos = return_pos + 1

    # Write back if changed
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False


def main():
    """Update target router files."""
    routers_to_update = [
        'C:/Users/themi/PycharmProjects/Socrates/socrates-api/src/socrates_api/routers/collaboration.py',
        'C:/Users/themi/PycharmProjects/Socrates/socrates-api/src/socrates_api/routers/projects.py',
        'C:/Users/themi/PycharmProjects/Socrates/socrates-api/src/socrates_api/routers/knowledge.py',
    ]

    for router_path in routers_to_update:
        router_file = Path(router_path)
        if router_file.exists():
            print(f"Processing {router_file.name}...", end=" ")
            if update_file(router_file):
                print("Updated")
            else:
                print("No changes needed")
        else:
            print(f"File not found: {router_path}")


if __name__ == "__main__":
    main()
