"""
Multi-File Code Splitter - Split monolithic generated code into organized files

Intelligently distributes code across multiple files based on:
- Class and function organization
- Logical boundaries (models, controllers, services)
- Import dependencies
- Code patterns
"""

import ast
import logging
from typing import Dict

logger = logging.getLogger("socrates.utils.multi_file_splitter")


class MultiFileCodeSplitter:
    """Split generated code into multiple organized files"""

    def __init__(self, code: str, language: str = "python", project_type: str = "software"):
        """
        Initialize splitter.

        Args:
            code: Generated code as string
            language: Programming language (default: python)
            project_type: Type of project (software, library, etc.)
        """
        self.code = code
        self.language = language.lower()
        self.project_type = project_type
        self.files: Dict[str, str] = {}

    def split(self) -> Dict[str, str]:
        """
        Split code into organized files.

        Returns:
            Dictionary with file paths as keys and content as values
        """
        if self.language == "python":
            return self._split_python()
        else:
            # For non-Python, keep as single file
            return {"main.py" if self.language == "javascript" else "main": self.code}

    def _split_python(self) -> Dict[str, str]:
        """Split Python code into organized files"""
        try:
            tree = ast.parse(self.code)
        except SyntaxError as e:
            logger.error(f"Syntax error splitting code: {e}")
            return {"main.py": self.code}

        # Categorize code into different modules
        categorized_code = self._categorize_code_blocks(tree)
        imports = self._extract_imports()

        # Build organized file structure
        self._build_organized_files(categorized_code, imports)

        # Add supporting files
        self._add_supporting_files(categorized_code)

        return self.files

    def _categorize_code_blocks(self, tree: ast.Module) -> Dict[str, list]:
        """Categorize code blocks from AST"""
        categorized: Dict[str, list] = {
            "models": [],
            "controllers": [],
            "services": [],
            "utils": [],
            "tests": [],
            "config": [],
            "main": [],
        }

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue

            if isinstance(node, ast.ClassDef):
                self._categorize_and_add_class(node, categorized)
            elif isinstance(node, ast.FunctionDef):
                self._categorize_and_add_function(node, categorized)
            else:
                self._categorize_and_add_other(node, categorized)

        return categorized

    def _categorize_and_add_class(self, node: ast.ClassDef, categorized: Dict[str, list]) -> None:
        """Categorize and add class definition to appropriate category"""
        class_code = ast.unparse(node)
        category = self._categorize_class(node.name)

        if category == "model":
            categorized["models"].append(class_code)
        elif category == "controller":
            categorized["controllers"].append(class_code)
        elif category == "service":
            categorized["services"].append(class_code)
        else:
            categorized["utils"].append(class_code)

    def _categorize_and_add_function(
        self, node: ast.FunctionDef, categorized: Dict[str, list]
    ) -> None:
        """Categorize and add function definition to appropriate category"""
        func_code = ast.unparse(node)

        if node.name.startswith("test_"):
            categorized["tests"].append(func_code)
        elif node.name in ["main", "run", "start"]:
            categorized["main"].append(func_code)
        elif "config" in node.name.lower():
            categorized["config"].append(func_code)
        else:
            categorized["utils"].append(func_code)

    def _categorize_and_add_other(self, node: ast.stmt, categorized: Dict[str, list]) -> None:
        """Categorize and add other statements to appropriate category"""
        other_code = ast.unparse(node)

        if "test" in other_code.lower():
            categorized["tests"].append(other_code)
        elif "config" in other_code.lower():
            categorized["config"].append(other_code)
        else:
            categorized["utils"].append(other_code)

    def _build_organized_files(self, categorized: Dict[str, list], imports: str) -> None:
        """Build organized files from categorized code"""
        self.files = {}

        if categorized["models"]:
            self.files["src/models.py"] = imports + "\n\n" + "\n\n".join(categorized["models"])

        if categorized["controllers"]:
            self.files["src/controllers.py"] = (
                imports + "\nfrom .models import *\n\n" + "\n\n".join(categorized["controllers"])
            )

        if categorized["services"]:
            self.files["src/services.py"] = (
                imports + "\nfrom .models import *\n\n" + "\n\n".join(categorized["services"])
            )

        if categorized["utils"]:
            self.files["src/utils.py"] = imports + "\n\n" + "\n\n".join(categorized["utils"])

        if categorized["config"]:
            self.files["config/settings.py"] = imports + "\n\n" + "\n\n".join(categorized["config"])

        if categorized["tests"]:
            self.files["tests/test_main.py"] = (
                imports + "\nimport pytest\n\n" + "\n\n".join(categorized["tests"])
            )

        self._add_main_entry_point(categorized, imports)

    def _add_main_entry_point(self, categorized: Dict[str, list], imports: str) -> None:
        """Add main entry point file"""
        if categorized["main"]:
            self.files["main.py"] = imports + "\n\n" + "\n\n".join(categorized["main"])
        elif categorized["models"] or categorized["services"] or categorized["controllers"]:
            self.files["main.py"] = self._create_main_entry_point()

    def _add_supporting_files(self, categorized: Dict[str, list]) -> None:
        """Add supporting files (init files, requirements, readme)"""
        self.files["src/__init__.py"] = self._create_init_file("src")
        self.files["config/__init__.py"] = self._create_init_file("config")
        if categorized["tests"]:
            self.files["tests/__init__.py"] = ""

        self.files["requirements.txt"] = self._extract_requirements()
        self.files["README.md"] = self._create_readme()

    def _categorize_class(self, class_name: str) -> str:
        """Categorize class by name"""
        name_lower = class_name.lower()

        if any(keyword in name_lower for keyword in ["model", "entity", "schema", "dao"]):
            return "model"
        elif any(keyword in name_lower for keyword in ["controller", "handler", "router", "api"]):
            return "controller"
        elif any(keyword in name_lower for keyword in ["service", "manager", "factory"]):
            return "service"
        elif any(
            keyword in name_lower
            for keyword in ["util", "helper", "tool", "config", "settings", "constant"]
        ):
            return "utility"
        else:
            # Default: treat standalone classes (User, Product, etc.) as models
            return "model"

    def _extract_imports(self) -> str:
        """Extract import statements from code"""
        import_lines = []
        for line in self.code.split("\n"):
            if line.strip().startswith(("import ", "from ")):
                import_lines.append(line)

        return "\n".join(import_lines) if import_lines else "# Standard library imports"

    def _extract_requirements(self) -> str:
        """Extract external package requirements from imports"""
        requirements = set()

        # Common third-party packages
        packages = {
            "django": "Django>=4.0",
            "flask": "Flask>=2.0",
            "fastapi": "FastAPI>=0.95",
            "requests": "requests>=2.28",
            "numpy": "numpy>=1.21",
            "pandas": "pandas>=1.3",
            "sqlalchemy": "SQLAlchemy>=1.4",
            "pytest": "pytest>=7.0",
        }

        code_lower = self.code.lower()
        for package, requirement in packages.items():
            if package in code_lower:
                requirements.add(requirement)

        if requirements:
            return "\n".join(sorted(requirements))
        else:
            return "# Add your dependencies here\n# Example: requests>=2.28\n"

    def _create_main_entry_point(self) -> str:
        """Create a main entry point if none exists"""
        return '''"""Main entry point for the application"""

if __name__ == "__main__":
    # Initialize and run application
    print("Application started")
    # Add your main logic here
'''

    def _create_init_file(self, package_name: str) -> str:
        """Create __init__.py file for a package"""
        if package_name == "src":
            return '''"""Source code package"""

# Import main components for easier access
# from .models import *
# from .services import *
# from .controllers import *
'''
        elif package_name == "config":
            return '''"""Configuration package"""

# Import settings
# from .settings import *
'''
        return ""

    def _create_readme(self) -> str:
        """Create README.md file"""
        return """# Project

## Overview

Generated project structure with organized code files.

## Directory Structure

```
├── src/
│   ├── __init__.py
│   ├── models.py          # Data models and entities
│   ├── controllers.py     # API controllers and handlers
│   ├── services.py        # Business logic
│   └── utils.py           # Utility functions
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration
├── tests/
│   ├── __init__.py
│   └── test_main.py       # Test cases
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

3. Run tests:
   ```bash
   pytest
   ```

## Features

- Organized code structure
- Modular architecture
- Test coverage

## Contributing

Contributions are welcome!
"""


class ProjectStructureGenerator:
    """Generate complete project structure with all necessary files"""

    @staticmethod
    def create_structure(
        project_name: str,
        generated_files: Dict[str, str],
        project_type: str = "software",
    ) -> Dict[str, str]:
        """
        Create complete project structure.

        Args:
            project_name: Name of the project
            generated_files: Dictionary of generated code files
            project_type: Type of project

        Returns:
            Complete file structure with paths and contents
        """
        complete_structure = {}

        # Add generated files
        for file_path, content in generated_files.items():
            complete_structure[file_path] = content

        # Ensure key files exist
        if "requirements.txt" not in complete_structure:
            complete_structure["requirements.txt"] = "# Add dependencies here\n"

        if "README.md" not in complete_structure:
            complete_structure["README.md"] = f"# {project_name}\n\nProject description.\n"

        if "main.py" not in complete_structure and "src/__init__.py" in complete_structure:
            complete_structure[
                "main.py"
            ] = '''"""Entry point"""

if __name__ == "__main__":
    print("Starting application...")
'''

        # Add .gitignore if not present
        if ".gitignore" not in complete_structure:
            complete_structure[
                ".gitignore"
            ] = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project
*.db
.coverage
htmlcov/
dist/
build/
"""

        return complete_structure
