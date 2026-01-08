#!/usr/bin/env python3
"""
Script to systematically update all response_model=dict to response_model=APIResponse
and add APIResponse import where needed.
"""

import os
import re
from pathlib import Path

ROUTERS_DIR = Path("socrates-api/src/socrates_api/routers")

def update_router_file(filepath):
    """Update a single router file."""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Add APIResponse import if needed
    if 'response_model=APIResponse' in content or 'response_model=dict' in content:
        if 'from socrates_api.models import' in content and 'APIResponse' not in content:
            # Find the import statement and add APIResponse
            import_pattern = r'(from socrates_api\.models import \()'
            if re.search(import_pattern, content):
                content = re.sub(
                    import_pattern,
                    r'\1\n    APIResponse,',
                    content
                )
            else:
                # Single-line import
                import_pattern = r'(from socrates_api\.models import[^\n]*)'
                content = re.sub(
                    import_pattern,
                    lambda m: m.group(1).replace(')', ', APIResponse)') if ')' in m.group(1) else m.group(1) + ', APIResponse',
                    content
                )

    # Replace response_model=dict with response_model=APIResponse
    content = re.sub(r'response_model=dict,', 'response_model=APIResponse,', content)
    content = re.sub(r'response_model=dict\)', 'response_model=APIResponse)', content)

    # Write back if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Update all router files."""
    routers_dir = Path("C:/Users/themi/PycharmProjects/Socrates/socrates-api/src/socrates_api/routers")

    updated_count = 0
    for router_file in routers_dir.glob("*.py"):
        if router_file.name.startswith("__"):
            continue

        print(f"Processing {router_file.name}...", end=" ")
        if update_router_file(router_file):
            print("[Updated]")
            updated_count += 1
        else:
            print("[No changes]")

    print(f"\nTotal files updated: {updated_count}")

if __name__ == "__main__":
    main()
