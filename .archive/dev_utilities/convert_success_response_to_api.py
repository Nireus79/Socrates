#!/usr/bin/env python3
"""
Convert all SuccessResponse routers to use APIResponse
"""

import re
from pathlib import Path

ROUTERS_DIR = Path("C:/Users/themi/PycharmProjects/Socrates/socrates-api/src/socrates_api/routers")

# Routers that use SuccessResponse
SUCCESSRESPONSE_ROUTERS = [
    "analytics.py",
    "analysis.py",
    "auth.py",
    "chat.py",
    "chat_sessions.py",
    "finalization.py",
    "free_session.py",
    "github.py",
    "knowledge_management.py",
    "llm.py",
    "llm_config.py",
    "nlu.py",
    "notes.py",
    "progress.py",
    "query.py",
    "security.py",
    "skills.py",
    "subscription.py",
]

def update_router(filepath):
    """Update a router file to use APIResponse instead of SuccessResponse"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Step 1: Add APIResponse to imports if not present
    if 'SuccessResponse' in content:
        # Check if APIResponse is already imported
        if 'APIResponse' not in content:
            # Add APIResponse to imports
            # Pattern: from socrates_api.models import (...)
            if 'from socrates_api.models import' in content:
                # Multi-line import
                if '(' in content:
                    # Add APIResponse at the beginning
                    content = re.sub(
                        r'(from socrates_api\.models import \()\s*',
                        r'\1\n    APIResponse,\n    ',
                        content
                    )
                else:
                    # Single-line import - add APIResponse
                    content = re.sub(
                        r'(from socrates_api\.models import )([^)\n]+)',
                        r'\1APIResponse, \2',
                        content
                    )

        # Step 2: Replace SuccessResponse returns with APIResponse
        # Pattern: return SuccessResponse(...)

        # Handle multi-line SuccessResponse returns
        pattern = r'return SuccessResponse\(\s*success=True,?\s*message=([^,]+),\s*data=(\{[^}]*\})\s*\)'

        def replacer(match):
            message = match.group(1)
            data = match.group(2)
            return f'return APIResponse(\n        success=True,\n        status="success",\n        message={message},\n        data={data},\n    )'

        content = re.sub(pattern, replacer, content, flags=re.DOTALL)

        # Handle simpler pattern: return SuccessResponse(...)
        # For cases where it's on multiple lines
        lines = content.split('\n')
        in_return = False
        return_buffer = []
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if 'return SuccessResponse(' in line and not in_return:
                in_return = True
                return_buffer = [line]
                # Check if it's a single-line return
                if ')' in line:
                    # Single line - convert it
                    converted = line.replace('SuccessResponse(', 'APIResponse(')
                    # Add status="success" if not present
                    if 'status=' not in converted:
                        # Insert after success=True
                        converted = re.sub(
                            r'success=True,',
                            'success=True,\n        status="success",',
                            converted
                        )
                    new_lines.append(converted)
                    in_return = False
                    return_buffer = []
                i += 1
                continue

            if in_return:
                return_buffer.append(line)
                if ')' in line and not line.strip().startswith('('):
                    # End of return statement
                    full_return = '\n'.join(return_buffer)

                    # Convert SuccessResponse to APIResponse
                    full_return = full_return.replace('SuccessResponse(', 'APIResponse(')

                    # Add status="success" if not present
                    if 'status=' not in full_return:
                        full_return = re.sub(
                            r'success=True,',
                            'success=True,\n        status="success",',
                            full_return
                        )

                    new_lines.extend(full_return.split('\n'))
                    in_return = False
                    return_buffer = []
                i += 1
                continue

            new_lines.append(line)
            i += 1

        if in_return and return_buffer:
            # Unclosed return statement
            full_return = '\n'.join(return_buffer)
            full_return = full_return.replace('SuccessResponse(', 'APIResponse(')
            if 'status=' not in full_return:
                full_return = re.sub(
                    r'success=True,',
                    'success=True,\n        status="success",',
                    full_return
                )
            new_lines.extend(full_return.split('\n'))

        content = '\n'.join(new_lines)

    # Write back if changed
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Update all SuccessResponse routers"""
    updated_count = 0

    for router_name in SUCCESSRESPONSE_ROUTERS:
        router_path = ROUTERS_DIR / router_name
        if router_path.exists():
            print(f"Processing {router_name}...", end=" ")
            if update_router(router_path):
                print("Updated")
                updated_count += 1
            else:
                print("No changes")
        else:
            print(f"File not found: {router_name}")

    print(f"\nTotal files updated: {updated_count}")

if __name__ == "__main__":
    main()
