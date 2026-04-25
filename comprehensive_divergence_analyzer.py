#!/usr/bin/env python3
"""Comprehensive divergence analyzer - detailed analysis of all components."""

import os
import difflib
from typing import Dict, List, Tuple

MONOLITH_AGENTS = r"C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents"
LIBRARY_AGENTS = r"C:\Users\themi\AppData\Local\Temp\Socratic-agents\src\socratic_agents\agents"

def get_first_class_def(filepath: str) -> Tuple[str, int]:
    """Get the name of the first class and its line count."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        class_name = None
        for line in lines:
            if line.strip().startswith('class '):
                class_name = line.strip().split('(')[0].replace('class ', '')
                break
        
        return (class_name or "UNKNOWN", len(lines))
    except:
        return ("ERROR", 0)

def analyze_function_signatures(filepath: str) -> List[str]:
    """Extract all function/method signatures."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        sigs = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def '):
                # Extract just the def line
                sig = stripped.split(':')[0] if ':' in stripped else stripped
                sigs.append(sig)
        
        return sigs
    except:
        return []

print("=" * 100)
print("DETAILED AGENTS ANALYSIS - DIVERGENCE REPORT")
print("=" * 100)

monolith_files = {f: os.path.join(MONOLITH_AGENTS, f) 
                  for f in os.listdir(MONOLITH_AGENTS) if f.endswith('.py') and not f.startswith('test_')}
library_files = {f: os.path.join(LIBRARY_AGENTS, f) 
                 for f in os.listdir(LIBRARY_AGENTS) if f.endswith('.py') and not f.startswith('test_')}

divergences = {}

for filename in sorted(set(monolith_files.keys()) | set(library_files.keys())):
    monolith_path = monolith_files.get(filename)
    library_path = library_files.get(filename)
    
    if not monolith_path or not library_path:
        status = "ONLY_IN_" + ("MONOLITH" if monolith_path else "LIBRARY")
        divergences[filename] = {
            "status": status,
            "severity": "HIGH",
            "details": "File missing in " + ("library" if monolith_path else "monolith")
        }
        continue
    
    # Read both files
    try:
        with open(monolith_path, 'r', encoding='utf-8') as f:
            monolith_content = f.read()
    except:
        monolith_content = ""
    
    try:
        with open(library_path, 'r', encoding='utf-8') as f:
            library_content = f.read()
    except:
        library_content = ""
    
    if monolith_content == library_content:
        divergences[filename] = {
            "status": "EXACT_COPY",
            "severity": "NONE"
        }
    else:
        # Analyze differences
        monolith_class, monolith_lines = get_first_class_def(monolith_path)
        library_class, library_lines = get_first_class_def(library_path)
        
        monolith_funcs = analyze_function_signatures(monolith_path)
        library_funcs = analyze_function_signatures(library_path)
        
        line_diff = library_lines - monolith_lines
        
        # Determine severity
        if monolith_class != library_class:
            severity = "CRITICAL"
            reason = f"Class name differs: {monolith_class} vs {library_class}"
        elif abs(line_diff) > 500:
            severity = "HIGH"
            reason = f"Significant size difference: {abs(line_diff)} lines"
        elif abs(line_diff) > 200:
            severity = "MEDIUM"
            reason = f"Moderate size difference: {abs(line_diff)} lines"
        else:
            severity = "LOW"
            reason = f"Minor differences: {abs(line_diff)} lines"
        
        # Check function signatures
        monolith_set = set(f.split('(')[0] for f in monolith_funcs)
        library_set = set(f.split('(')[0] for f in library_funcs)
        missing_funcs = monolith_set - library_set
        added_funcs = library_set - monolith_set
        
        if missing_funcs or added_funcs:
            if severity == "NONE" or severity == "LOW":
                severity = "MEDIUM"
            if missing_funcs:
                reason += f"; Missing: {', '.join(list(missing_funcs)[:3])}"
            if added_funcs:
                reason += f"; Added: {', '.join(list(added_funcs)[:3])}"
        
        divergences[filename] = {
            "status": "DIVERGED",
            "severity": severity,
            "monolith_class": monolith_class,
            "library_class": library_class,
            "monolith_lines": monolith_lines,
            "library_lines": library_lines,
            "line_diff": line_diff,
            "monolith_funcs": len(monolith_funcs),
            "library_funcs": len(library_funcs),
            "missing_methods": list(missing_funcs)[:5],
            "added_methods": list(added_funcs)[:5],
            "reason": reason
        }

# Print summary
print("\nSUMMARY:")
print("-" * 100)
exact = sum(1 for d in divergences.values() if d['status'] == 'EXACT_COPY')
diverged = sum(1 for d in divergences.values() if d['status'] == 'DIVERGED')
missing = sum(1 for d in divergences.values() if 'ONLY_IN' in d['status'])

print("Exact Copies:        {}".format(exact))
print("Diverged Files:      {}".format(diverged))
print("Missing Files:       {}".format(missing))
print("Total Files:         {}".format(len(divergences)))

# Print by severity
print("\nBY SEVERITY:")
print("-" * 100)
for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]:
    files = [f for f, d in divergences.items() if d.get('severity') == severity]
    if files:
        print("\n{}:".format(severity))
        for f in sorted(files):
            d = divergences[f]
            if d['status'] == 'DIVERGED':
                print("  [{}] {} ({} vs {} lines, {} funcs vs {})".format(
                    d['status'][:3], f, d['monolith_lines'], d['library_lines'],
                    d['monolith_funcs'], d['library_funcs']))
                if d.get('reason'):
                    print("      {}".format(d['reason']))
            else:
                print("  [{}] {}".format(d['status'][:3], f))

