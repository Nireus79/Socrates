# GIT WORKFLOW QUICK REFERENCE
## One-Page Command Reference for All 12 Libraries

**Quick Access:** Print this page for terminal-side reference

---

## INITIAL SETUP

```bash
# Set git configuration
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Create workspace
mkdir C:\Users\themi\Socrates-Libraries
cd C:\Users\themi\Socrates-Libraries
```

---

## BATCH 1: CORE LIBRARIES (Parallel)

### Library 1: socratic-core

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-core.git
cd Socratic-core

# Extract files
monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_core
cp "$monolith/socratic_system/core/"*.py socratic_core/

# Verify
ls -1 socratic_core/*.py | wc -l  # Should be 12

# Stage, commit, push
git add .
git commit -m "refactor: extract core module from monolith v1.3.3

- Extract all 12 core calculation modules
- Add packaging configuration (pyproject.toml)
- Add README and __init__.py
- Preserve all original functionality"
git push origin main

# Verify on GitHub
git log --oneline -1 origin/main
```

---

### Library 2: socratic-nexus

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-nexus.git
cd Socratic-nexus

# Extract files
monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_nexus
cp "$monolith/socratic_system/clients/"*.py socratic_nexus/

# Verify
ls -1 socratic_nexus/*.py | wc -l  # Should be 2

# Commit and push
git add .
git commit -m "refactor: extract nexus (Claude client) from monolith v1.3.3

- Extract Claude API client module
- Add packaging configuration
- Add README and __init__.py"
git push origin main
```

---

### Library 3: socratic-conflict

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-conflict.git
cd Socratic-conflict

# Extract files
monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_conflict
cp "$monolith/socratic_system/conflict_resolution/"*.py socratic_conflict/

# Verify
ls -1 socratic_conflict/*.py | wc -l  # Should be 4

# Commit and push
git add .
git commit -m "refactor: extract conflict resolution from monolith v1.3.3

- Extract all 4 conflict resolution modules
- Add packaging configuration
- Add README and __init__.py"
git push origin main
```

---

## BATCH 2: SECONDARY LIBRARIES (Parallel - After Batch 1)

### Library 4: socratic-agents

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-agents.git
cd Socratic-agents

# Extract files
monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_agents
cp "$monolith/socratic_system/agents/__init__.py" socratic_agents/
cp "$monolith/socratic_system/agents/base.py" socratic_agents/
cp "$monolith/socratic_system/agents/multi_llm_agent.py" socratic_agents/
cp "$monolith/socratic_system/agents/socratic_counselor.py" socratic_agents/
cp "$monolith/socratic_system/agents/note_manager.py" socratic_agents/
cp "$monolith/socratic_system/agents/quality_controller.py" socratic_agents/

# Verify
ls -1 socratic_agents/*.py | wc -l  # Should be 6

# Commit and push
git add .
git commit -m "refactor: extract agents framework from monolith v1.3.3

- Extract 6 core agent modules and base class
- Add packaging configuration
- Add README and __init__.py
- Agents can be extended for specialized tasks"
git push origin main
```

---

### Library 5: socratic-rag

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-rag.git
cd Socratic-rag

# Extract files
monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_rag
cp "$monolith/socratic_system/database/vector_db.py" socratic_rag/
cp "$monolith/socratic_system/database/embedding_cache.py" socratic_rag/
cp "$monolith/socratic_system/database/connection_pool.py" socratic_rag/
cp "$monolith/socratic_system/database/search_cache.py" socratic_rag/
cp "$monolith/socratic_system/agents/document_processor.py" socratic_rag/

# Verify
ls -1 socratic_rag/*.py | wc -l  # Should be 5

# Commit and push
git add .
git commit -m "refactor: extract RAG database module from monolith v1.3.3

- Extract vector database and caching layer
- Extract document processing agent
- Add connection pooling for database access
- Add packaging configuration"
git push origin main
```

---

### Library 6: socratic-workflow

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-workflow.git
cd Socratic-workflow

# Extract files
monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_workflow
cp "$monolith/socratic_system/core/workflow_builder.py" socratic_workflow/
cp "$monolith/socratic_system/core/workflow_optimizer.py" socratic_workflow/
cp "$monolith/socratic_system/core/workflow_path_finder.py" socratic_workflow/
cp "$monolith/socratic_system/core/workflow_cost_calculator.py" socratic_workflow/
cp "$monolith/socratic_system/core/workflow_risk_calculator.py" socratic_workflow/
cp "$monolith/socratic_system/orchestration/orchestrator.py" socratic_workflow/

# Verify
ls -1 socratic_workflow/*.py | wc -l  # Should be 6

# Commit and push
git add .
git commit -m "refactor: extract workflow management from monolith v1.3.3

- Extract workflow builder and optimization engine
- Extract cost and risk calculation modules
- Extract orchestration layer
- Add packaging configuration"
git push origin main
```

---

## BATCH 3: SPECIALIZED LIBRARIES (Parallel - After Batch 2)

### Library 7: socratic-knowledge

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-knowledge.git
cd Socratic-knowledge

monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_knowledge
cp "$monolith/socratic_system/agents/knowledge_manager.py" socratic_knowledge/
cp "$monolith/socratic_system/agents/knowledge_analysis.py" socratic_knowledge/
cp "$monolith/socratic_system/orchestration/knowledge_base.py" socratic_knowledge/
cp "$monolith/socratic_system/database/vector_db.py" socratic_knowledge/
cp "$monolith/socratic_system/database/embedding_cache.py" socratic_knowledge/
cp "$monolith/socratic_system/database/search_cache.py" socratic_knowledge/

ls -1 socratic_knowledge/*.py | wc -l  # Should be 6

git add .
git commit -m "refactor: extract knowledge management from monolith v1.3.3

- Extract knowledge manager and analysis modules
- Extract knowledge base orchestration layer
- Include vector database and caching modules
- Add packaging configuration"
git push origin main
```

---

### Library 8: socratic-analyzer

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-analyzer.git
cd Socratic-analyzer

monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_analyzer
cp "$monolith/socratic_system/agents/context_analyzer.py" socratic_analyzer/
cp "$monolith/socratic_system/agents/document_context_analyzer.py" socratic_analyzer/
cp "$monolith/socratic_system/agents/code_generator.py" socratic_analyzer/
cp "$monolith/socratic_system/agents/code_validation_agent.py" socratic_analyzer/

ls -1 socratic_analyzer/*.py | wc -l  # Should be 4

git add .
git commit -m "refactor: extract analyzer (context analysis & code generation) from monolith v1.3.3

- Extract context analysis agents
- Extract document analysis tools
- Extract code generation and validation modules
- Add packaging configuration"
git push origin main
```

---

### Library 9: socratic-learning

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-learning.git
cd Socratic-learning

monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_learning
cp "$monolith/socratic_system/agents/learning_agent.py" socratic_learning/
cp "$monolith/socratic_system/agents/user_manager.py" socratic_learning/
cp "$monolith/socratic_system/core/learning_engine.py" socratic_learning/

ls -1 socratic_learning/*.py | wc -l  # Should be 3

git add .
git commit -m "refactor: extract learning management from monolith v1.3.3

- Extract learning agent and user tracking modules
- Extract learning calculation engine
- Add packaging configuration"
git push origin main
```

---

### Library 10: socratic-docs

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-docs.git
cd Socratic-docs

monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_docs/extractors
cp "$monolith/socratic_system/agents/document_processor.py" socratic_docs/
cp "$monolith/socratic_system/agents/document_context_analyzer.py" socratic_docs/
cp "$monolith/socratic_system/services/document_understanding.py" socratic_docs/
cp "$monolith/socratic_system/utils/code_structure_analyzer.py" socratic_docs/
cp "$monolith/socratic_system/utils/code_extractor.py" socratic_docs/
cp "$monolith/socratic_system/utils/extractors/"*.py socratic_docs/extractors/

ls -1 socratic_docs/*.py | wc -l  # Should be 5+

git add .
git commit -m "refactor: extract document processing from monolith v1.3.3

- Extract document processor and analysis agents
- Extract code structure and extraction utilities
- Extract document understanding service
- Include extractors module with specialized extractors
- Add packaging configuration"
git push origin main
```

---

### Library 11: socratic-performance

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-performance.git
cd Socratic-performance

monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_performance
cp "$monolith/socratic_system/core/analytics_calculator.py" socratic_performance/
cp "$monolith/socratic_system/monitoring_metrics.py" socratic_performance/
cp "$monolith/socratic_system/ui/analytics_display.py" socratic_performance/
cp "$monolith/socratic_system/ui/maturity_display.py" socratic_performance/
cp "$monolith/socratic_system/core/insight_categorizer.py" socratic_performance/

ls -1 socratic_performance/*.py | wc -l  # Should be 5

git add .
git commit -m "refactor: extract performance monitoring from monolith v1.3.3

- Extract analytics calculation engine
- Extract monitoring metrics and tracking
- Extract analytics and maturity display modules
- Extract insight categorization logic
- Add packaging configuration"
git push origin main
```

---

### Library 12: socratic-maturity

```bash
cd C:\Users\themi\Socrates-Libraries
git clone https://github.com/Nireus79/Socratic-maturity.git
cd Socratic-maturity

monolith="C:/Users/themi/PycharmProjects/Socrates"
mkdir -p socratic_maturity
cp "$monolith/socratic_system/core/maturity_calculator.py" socratic_maturity/
cp "$monolith/socratic_system/core/project_categories.py" socratic_maturity/
cp "$monolith/socratic_system/ui/maturity_display.py" socratic_maturity/

ls -1 socratic_maturity/*.py | wc -l  # Should be 3

git add .
git commit -m "refactor: extract maturity tracking from monolith v1.3.3

- Extract maturity calculation engine
- Extract project category definitions
- Extract maturity display and visualization
- Add packaging configuration"
git push origin main
```

---

## POST-EXTRACTION VERIFICATION

### Quick Verification All Libraries

```bash
cd C:\Users\themi\Socrates-Libraries

# Check all directories exist
ls -1d Socratic-*

# Verify each has pushed
for lib in Socratic-{core,nexus,agents,conflict,rag,workflow,knowledge,analyzer,learning,docs,performance,maturity}; do
  cd "$lib"
  echo "=== $lib ==="
  git log --oneline -1
  git status
  cd ..
done
```

### Fresh Clone Verification

```bash
mkdir /tmp/verify
cd /tmp/verify

for lib in socratic-core socratic-nexus socratic-agents socratic-conflict \
           socratic-rag socratic-workflow socratic-knowledge socratic-analyzer \
           socratic-learning socratic-docs socratic-performance socratic-maturity; do

  echo "Verifying $lib..."
  git clone https://github.com/Nireus79/$lib.git

  if [ -d "$lib" ]; then
    count=$(find "$lib" -name "*.py" -type f | wc -l)
    echo "  $lib: $count Python files"
    rm -rf "$lib"
  else
    echo "  ERROR: $lib not found!"
  fi
done
```

---

## COMMON COMMANDS REFERENCE

### Git Status Check
```bash
cd [library]
git status              # Check working tree status
git log --oneline -5    # See last 5 commits
git remote -v           # Verify remote URL
```

### Undo Changes (SAFE - No Push Yet)
```bash
cd [library]

# Unstage files
git reset HEAD [file]

# Discard changes
git checkout -- [file]

# Undo last commit (keeps changes staged)
git reset --soft HEAD~1

# Undo last commit (discards changes)
git reset --hard HEAD~1
```

### Push Verification
```bash
cd [library]

# Preview what will push
git log origin/main..main --oneline

# Perform push
git push origin main

# Verify pushed
git log --oneline -1 origin/main
```

### File Verification
```bash
cd [library]/socratic_[name]

# List all Python files
ls -la *.py

# Count files
ls -1 *.py | wc -l

# Check syntax
python -m py_compile *.py

# Test import
python -c "import [socratic_name]; print('OK')"
```

---

## TROUBLESHOOTING QUICK FIXES

### Problem: Directory already exists
```bash
rm -rf C:\Users\themi\Socrates-Libraries\[libname]
git clone https://github.com/Nireus79/[libname].git
```

### Problem: Authentication failed
```bash
# Use GitHub CLI
gh auth login

# OR configure SSH
ssh-keygen -t ed25519 -C "your-email@example.com"
```

### Problem: Files not visible on GitHub
```bash
cd [library]
git status                          # Verify committed
git log --oneline -1               # See local commit
git push origin main               # Push again
git log --oneline -1 origin/main   # Verify remote
```

### Problem: Wrong files committed
```bash
cd [library]
git reset --hard HEAD~1            # Undo commit
# Fix files
git add .
git commit -m "..."
git push origin main -f            # Force if already pushed
```

### Problem: Missing files
```bash
cd [library]
git status                    # See what's missing
# Verify extraction completed
ls -la socratic_[name]/*.py
```

---

## BATCH SUMMARY STATS

| Batch | Libraries | Total Files | Time |
|-------|-----------|------------|------|
| 1 | core, nexus, conflict | 18 | 15-20 min |
| 2 | agents, rag, workflow | 17 | 15-20 min |
| 3 | knowledge, analyzer, learning, docs, performance, maturity | 24+ | 30-40 min |
| **TOTAL** | **12** | **59+** | **90 min** |

---

## FINAL CHECKLIST

- [ ] All 12 repositories cloned successfully
- [ ] All files extracted to correct directories
- [ ] All commits created with correct messages
- [ ] All pushes completed without errors
- [ ] All repositories visible on GitHub
- [ ] File counts match expectations
- [ ] No corrupted or missing files
- [ ] Git history clean and accurate
- [ ] Ready for next phase (publishing)

---

**Quick Reference Version:** 1.0.0
**Date:** 2026-04-21
**Print-Friendly:** Yes - Use monospace font for terminal output
