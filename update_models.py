#!/usr/bin/env python3
"""Remove try/except fallback blocks from integration classes in models_local.py"""

import re

with open("backend/src/socrates_api/models_local.py", "r") as f:
    content = f.read()

# Pattern 1: Remove self.available = False from init
content = re.sub(
    r'(\s+def __init__\(self\):)\n\s+self\.available = False\n',
    r'\1\n',
    content
)

# Pattern 2: Remove the entire try/except block for LearningIntegration
pattern = r'try:\s+from socratic_learning import \(\s+LearningEngine,\s+PatternDetector,\s+MetricsCollector,\s+RecommendationEngine\s+\)\s+self\.engine = LearningEngine\(\)\s+self\.pattern_detector = PatternDetector\(\)\s+self\.metrics_collector = MetricsCollector\(\)\s+self\.recommendation_engine = RecommendationEngine\(\)\s+self\.available = True\s+logger\.info\("socratic-learning library initialized successfully"\)\s+except ImportError:[\s\S]*?self\.available = False\s+except Exception as e:\s+logger\.warning\(f"Failed to initialize socratic-learning: \{e\}"\)\s+self\.available = False'

replacement = r'''from socratic_learning import (
            LearningEngine,
            PatternDetector,
            MetricsCollector,
            RecommendationEngine
        )
        self.engine = LearningEngine()
        self.pattern_detector = PatternDetector()
        self.metrics_collector = MetricsCollector()
        self.recommendation_engine = RecommendationEngine()
        logger.info("socratic-learning library initialized successfully")'''

# This is getting too complex - let's use a simpler line-by-line approach
lines = content.split('\n')
new_lines = []
skip_until_next_def = False
in_integration_init = False

for i, line in enumerate(lines):
    # Skip the try/except blocks in integration __init__ methods
    if 'try:' in line and i > 0 and '__init__' in lines[max(0,i-10):i]:
        in_init = True
        # Check if this is an integration class try/except
        for j in range(max(0, i-10), i):
            if 'LearningIntegration\|AnalyzerIntegration\|KnowledgeManager\|RAGIntegration\|WorkflowIntegration' in lines[j]:
                skip_until_next_def = True
                break

    # Skip lines while in try/except block
    if skip_until_next_def:
        # Stop skipping when we reach next method or class definition
        if re.match(r'\s+def \w+\(', line) and 'init' not in line:
            skip_until_next_def = False
            new_lines.append(line)
        elif re.match(r'^class \w+', line):
            skip_until_next_def = False
            new_lines.append(line)
        # Skip self.available = False/True lines
        elif 'self.available' in line:
            continue
        # Skip except blocks
        elif re.match(r'\s+except', line):
            # Skip until next non-except line
            while i < len(lines) - 1 and (re.match(r'\s+except', lines[i+1]) or re.match(r'\s+logger\.warning', lines[i+1])):
                i += 1
            skip_until_next_def = False
        else:
            new_lines.append(line)
    # Skip standalone self.available lines outside of try blocks
    elif 'self.available = ' in line and 'def ' not in lines[max(0,i-3):i]:
        # Check context - only skip if in integration class
        for j in range(max(0, i-20), i):
            if any(cls in lines[j] for cls in ['LearningIntegration', 'AnalyzerIntegration', 'KnowledgeManager', 'RAGIntegration', 'WorkflowIntegration']):
                continue  # Skip this line
        new_lines.append(line)
    else:
        new_lines.append(line)

with open("backend/src/socrates_api/models_local.py", "w") as f:
    f.write('\n'.join(new_lines))

print("Updated models_local.py")
