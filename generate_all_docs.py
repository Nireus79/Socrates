from pathlib import Path

libs = {
    "socrates-nexus": ("C:/Users/themi/PycharmProjects/Socrates-nexus", "Universal LLM abstraction layer"),
    "socratic-rag": ("C:/Users/themi/PycharmProjects/Socratic-rag", "Retrieval-Augmented Generation system"),
    "socratic-agents": ("C:/Users/themi/PycharmProjects/socratic-agents-repo", "Agent framework for autonomous execution"),
    "socratic-conflict": ("C:/Users/themi/PycharmProjects/socratic-conflict", "Conflict resolution and debate system"),
    "socratic-learning": ("C:/Users/themi/PycharmProjects/socratic-learning", "Adaptive learning system"),
    "socratic-analyzer": ("C:/Users/themi/PycharmProjects/socratic-analyzer", "Analysis engine for questions and responses"),
    "socratic-knowledge": ("C:/Users/themi/PycharmProjects/socratic-knowledge", "Knowledge management system"),
    "socratic-performance": ("C:/Users/themi/PycharmProjects/socratic-performance", "Performance monitoring and optimization"),
    "socratic-workflow": ("C:/Users/themi/PycharmProjects/Socratic-workflow", "Workflow orchestration system"),
    "socrates-maturity": ("C:/Users/themi/PycharmProjects/Socratic-maturity", "Maturity assessment framework"),
    "socratic-docs": ("C:/Users/themi/PycharmProjects/socratic-docs", "Documentation generation system"),
}

for name, (path, desc) in libs.items():
    p = Path(path)
    if not p.exists():
        print(f"SKIP {name}: path not found")
        continue
    
    print(f"Processing {name}...")
    
    # Check if README exists
    readme_path = p / "README.md"
    if readme_path.exists():
        print(f"  README.md already exists")
    else:
        print(f"  Would create README.md")
    
    arch_path = p / "ARCHITECTURE.md"
    if arch_path.exists():
        print(f"  ARCHITECTURE.md already exists")
    else:
        print(f"  Would create ARCHITECTURE.md")

print("\nDone!")
