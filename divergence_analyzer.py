#!/usr/bin/env python3
"""Comprehensive divergence analyzer for Socratic libraries vs monolith."""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

# Paths
MONOLITH_BASE = r"C:\Users\themi\PycharmProjects\Socrates\socratic_system"
LIBRARY_AGENTS = r"C:\Users\themi\AppData\Local\Temp\Socratic-agents\src\socratic_agents\agents"

def get_file_hash(filepath: str) -> str:
    """Get SHA256 hash of file."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except:
        return "ERROR"

def compare_files(monolith_file: str, library_file: str) -> Dict:
    """Compare two Python files and return differences."""
    try:
        with open(monolith_file, 'r', encoding='utf-8') as f:
            monolith_content = f.read()
    except:
        monolith_content = None
    
    try:
        with open(library_file, 'r', encoding='utf-8') as f:
            library_content = f.read()
    except:
        library_content = None
    
    if monolith_content is None or library_content is None:
        return {"identical": False, "status": "MISSING"}
    
    is_identical = monolith_content == library_content
    
    return {
        "identical": is_identical,
        "monolith_lines": len(monolith_content.splitlines()),
        "library_lines": len(library_content.splitlines()),
    }

# Analyze agents
print("=" * 80)
print("AGENTS COMPARISON")
print("=" * 80)

monolith_agents_dir = os.path.join(MONOLITH_BASE, "agents")

if os.path.exists(monolith_agents_dir) and os.path.exists(LIBRARY_AGENTS):
    monolith_files = set(f for f in os.listdir(monolith_agents_dir) if f.endswith('.py') and not f.startswith('test_'))
    library_files = set(f for f in os.listdir(LIBRARY_AGENTS) if f.endswith('.py') and not f.startswith('test_'))
    
    all_files = monolith_files | library_files
    
    divergences = []
    exact_copies = []
    missing = []
    
    for filename in sorted(all_files):
        monolith_path = os.path.join(monolith_agents_dir, filename)
        library_path = os.path.join(LIBRARY_AGENTS, filename)
        
        monolith_exists = os.path.exists(monolith_path)
        library_exists = os.path.exists(library_path)
        
        if not monolith_exists or not library_exists:
            status = "ONLY_IN_MONOLITH" if monolith_exists else "ONLY_IN_LIBRARY"
            missing.append((filename, status))
        else:
            comparison = compare_files(monolith_path, library_path)
            if comparison["identical"]:
                exact_copies.append(filename)
            else:
                divergences.append({
                    "file": filename,
                    "monolith_lines": comparison["monolith_lines"],
                    "library_lines": comparison["library_lines"],
                    "line_diff": comparison["library_lines"] - comparison["monolith_lines"],
                })
    
    print("\nEXACT COPIES: {}".format(len(exact_copies)))
    for f in exact_copies[:5]:
        print("  OK - {}".format(f))
    if len(exact_copies) > 5:
        print("  ... and {} more".format(len(exact_copies) - 5))
    
    print("\nMISSING FILES: {}".format(len(missing)))
    for f, status in missing[:5]:
        print("  {} - {} ({})".format("!", f, status))
    if len(missing) > 5:
        print("  ... and {} more".format(len(missing) - 5))
    
    print("\nDIVERGED FILES: {}".format(len(divergences)))
    for d in sorted(divergences, key=lambda x: abs(x['line_diff']), reverse=True)[:10]:
        print("  DIFF - {} ({} vs {} lines, diff: {})".format(d['file'], d['monolith_lines'], d['library_lines'], d['line_diff']))

