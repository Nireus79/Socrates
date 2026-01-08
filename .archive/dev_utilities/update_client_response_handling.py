#!/usr/bin/env python3
"""
Update client code to handle new APIResponse format
Changes response access pattern from response[key] to response.get("data", {}).get(key)
"""

import re
from pathlib import Path

COMMANDS_DIR = Path("C:/Users/themi/PycharmProjects/Socrates/socratic_system/ui/commands")

def update_command_file(filepath):
    """Update a command file to handle new APIResponse format"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Pattern 1: response["key"] where response comes from orchestrator/api call
    # This needs to become response.get("data", {}).get("key")

    # But first, we need to be smart about this - we only want to update
    # responses that come from the API, not internal operations

    # Look for patterns like:
    # result = orchestrator.process_request(...)
    # if result["status"] == "success":
    #     data = result.get("code")

    # Change to:
    # result = orchestrator.process_request(...)
    # if result["status"] == "success":
    #     data = result.get("data", {}).get("code")

    # Update common patterns for accessing response data

    replacements = [
        # Pattern: result["code"] -> result.get("data", {}).get("code")
        (r'result\["([a-zA-Z_][a-zA-Z0-9_]*)"\](?!:)', r'result.get("data", {}).get("\1")'),
        # Pattern: response["key"] -> response.get("data", {}).get("key")
        (r'response\["([a-zA-Z_][a-zA-Z0-9_]*)"\](?!:)', r'response.get("data", {}).get("\1")'),
        # Pattern: data["key"] -> data.get("key") - leave this as is
        # Pattern: result.get("code") -> result.get("data", {}).get("code")
        (r'result\.get\("([a-zA-Z_][a-zA-Z0-9_]*)"\)(?!:)', r'result.get("data", {}).get("\1")'),
    ]

    for pattern, replacement in replacements:
        # Only apply if we find "status" == "success" checks, indicating API responses
        if 'status.*success' in content or '"status"' in content:
            content = re.sub(pattern, replacement, content)

    # Also add comment about format change
    if content != original and 'APIResponse format' not in content:
        content = content.replace(
            '"""',
            '"""\nNOTE: Responses now use APIResponse format with data wrapped in "data" field.',
            1
        )

    # Write back if changed
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Update all command files"""
    command_files = list(COMMANDS_DIR.glob("*_commands.py"))

    updated_count = 0
    for cmd_file in command_files:
        print(f"Processing {cmd_file.name}...", end=" ")
        if update_command_file(cmd_file):
            print("Updated")
            updated_count += 1
        else:
            print("No changes")

    print(f"\nTotal files updated: {updated_count}")

if __name__ == "__main__":
    main()
