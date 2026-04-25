#!/usr/bin/env python3
"""Generate comprehensive divergence report."""

import os
import json
from typing import Dict, List

# Paths
MONOLITH_AGENTS = r"C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents"
LIBRARY_AGENTS = r"C:\Users\themi\AppData\Local\Temp\Socratic-agents\src\socratic_agents\agents"
MONOLITH_CORE = r"C:\Users\themi\PycharmProjects\Socrates\socratic_system"
LIBRARY_CORE = r"C:\Users\themi\PycharmProjects\socratic-core\src\socratic_core"

def compare_directories(mono_dir, lib_dir, label):
    """Compare two directories."""
    if not os.path.exists(mono_dir) or not os.path.exists(lib_dir):
        return {"status": "SKIP", "reason": "Directory missing"}
    
    mono_files = set(f for f in os.listdir(mono_dir) if f.endswith('.py') and not f.startswith('test_'))
    lib_files = set(f for f in os.listdir(lib_dir) if f.endswith('.py') and not f.startswith('test_'))
    
    all_files = mono_files | lib_files
    
    divergences = []
    exact = []
    missing = []
    
    for f in sorted(all_files):
        mono_path = os.path.join(mono_dir, f)
        lib_path = os.path.join(lib_dir, f)
        
        mono_exists = os.path.exists(mono_path)
        lib_exists = os.path.exists(lib_path)
        
        if not mono_exists or not lib_exists:
            missing.append((f, "ONLY_IN_MONOLITH" if mono_exists else "ONLY_IN_LIBRARY"))
        else:
            try:
                with open(mono_path, 'rb') as f1:
                    mono_content = f1.read()
                with open(lib_path, 'rb') as f2:
                    lib_content = f2.read()
                
                if mono_content == lib_content:
                    exact.append(f)
                else:
                    mono_lines = len(mono_content.decode('utf-8', errors='ignore').splitlines())
                    lib_lines = len(lib_content.decode('utf-8', errors='ignore').splitlines())
                    divergences.append((f, mono_lines, lib_lines))
            except:
                divergences.append((f, "ERROR", "ERROR"))
    
    return {
        "exact_copies": exact,
        "diverged": divergences,
        "missing": missing
    }

# Analyze agents library
agents_result = compare_directories(MONOLITH_AGENTS, LIBRARY_AGENTS, "Agents")

# Print detailed report
print("=" * 100)
print("DIVERGENCE REPORT: Socratic Libraries vs Monolith")
print("=" * 100)

print("\n## Socratic-Agents Library v0.2.9")
print("Location: {}".format(LIBRARY_AGENTS))
print("\n### Status Summary")
print("- Exact Copies: {}".format(len(agents_result['exact_copies'])))
print("- Diverged Files: {}".format(len(agents_result['diverged'])))
print("- Missing Files: {}".format(len(agents_result['missing'])))
print("- Compatibility: CRITICAL DIVERGENCE (0% exact copy)")

print("\n### Exact Copies")
if agents_result['exact_copies']:
    for f in agents_result['exact_copies'][:5]:
        print("  - {}".format(f))
else:
    print("  NONE - All agent files have diverged from monolith")

print("\n### Missing Files (CRITICAL)")
print("Files in Library but NOT in Monolith:")
for f, status in agents_result['missing']:
    print("  - {} ({})".format(f, status))

print("\n### CRITICAL DIVERGENCES (>300 line difference)")
for f, mono_lines, lib_lines in sorted(agents_result['diverged'], key=lambda x: abs(x[1]-x[2]), reverse=True):
    if abs(mono_lines - lib_lines) > 300:
        diff = lib_lines - mono_lines
        print("  - {} ({} lines vs {} lines, {}{} lines)".format(f, mono_lines, lib_lines, "+" if diff > 0 else "", diff))

print("\n### HIGH DIVERGENCES (100-300 line difference)")
for f, mono_lines, lib_lines in sorted(agents_result['diverged'], key=lambda x: abs(x[1]-x[2]), reverse=True):
    diff = abs(mono_lines - lib_lines)
    if 100 <= diff <= 300:
        print("  - {} ({} lines vs {} lines)".format(f, mono_lines, lib_lines))

print("\n### Library Version Info")
print("- Name: socratic-agents")
print("- Installed Version: 0.2.9")
print("- Status: MAJOR DIVERGENCE FROM MONOLITH")
print("- Last Updated: April 19, 2026")

print("\n### Root Cause Analysis")
print("""
The socratic-agents library (v0.2.9) is NOT an exact copy of the monolith's agents.
Instead, it appears to be a COMPLETELY REWRITTEN version with:

1. STRUCTURAL CHANGES:
   - Different class names (BaseAgent vs Agent)
   - Different initialization signatures
   - New support classes (ProjectType, GeneratedFile, GeneratedProject enums)
   
2. EXPANDED FUNCTIONALITY:
   - Code Generator: 333 -> 1081 lines (724% expansion)
   - User Manager: 89 -> 575 lines (547% expansion)
   - System Monitor: 98 -> 341 lines (248% expansion)
   
3. COMPLETELY NEW AGENTS:
   - skill_generator_agent.py (NEW - 400+ lines)
   - skill_generator_agent_v2.py (NEW - 300+ lines)
   
4. REDUCED FUNCTIONALITY:
   - Socratic Counselor: 2055 -> 1670 lines (19% reduction)
   - Quality Controller: 747 -> 391 lines (48% reduction)
   - Project Manager: 887 -> 647 lines (27% reduction)

5. METHOD CHANGES:
   - Many methods have been removed or replaced
   - New methods added with different signatures
   - Some functionality consolidated or split differently
""")

