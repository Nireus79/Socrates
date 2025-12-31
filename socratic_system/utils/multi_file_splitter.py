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

        # Organize code by category
        models_code = []
        controllers_code = []
        services_code = []
        utils_code = []
        tests_code = []
        config_code = []
        main_code = []

        # Extract and categorize top-level items
        imports = self._extract_imports()

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue  # Handle separately
            elif isinstance(node, ast.ClassDef):
                class_code = ast.unparse(node)
                category = self._categorize_class(node.name)

                if category == "model":
                    models_code.append(class_code)
                elif category == "controller":
                    controllers_code.append(class_code)
                elif category == "service":
                    services_code.append(class_code)
                else:
                    utils_code.append(class_code)

            elif isinstance(node, ast.FunctionDef):
                func_code = ast.unparse(node)

                if node.name.startswith("test_"):
                    tests_code.append(func_code)
                elif node.name in ["main", "run", "start"]:
                    main_code.append(func_code)
                elif "config" in node.name.lower():
                    config_code.append(func_code)
                else:
                    utils_code.append(func_code)

            else:
                # Other statements (assignments, etc.)
                other_code = ast.unparse(node)
                if "test" in other_code.lower():
                    tests_code.append(other_code)
                elif "config" in other_code.lower():
                    config_code.append(other_code)
                else:
                    utils_code.append(other_code)

        # Build file contents
        self.files = {}

        # Add imports to each file that needs them
        if models_code:
            self.files["src/models.py"] = imports + "\n\n" + "\n\n".join(models_code)

        if controllers_code:
            self.files["src/controllers.py"] = (
                imports + "\nfrom .models import *\n\n" + "\n\n".join(controllers_code)
            )

        if services_code:
            self.files["src/services.py"] = (
                imports + "\nfrom .models import *\n\n" + "\n\n".join(services_code)
            )

        if utils_code:
            self.files["src/utils.py"] = imports + "\n\n" + "\n\n".join(utils_code)

        if config_code:
            self.files["config/settings.py"] = imports + "\n\n" + "\n\n".join(
                config_code
            )

        if tests_code:
            self.files["tests/test_main.py"] = (
                imports + "\nimport pytest\n\n" + "\n\n".join(tests_code)
            )

        # Create main entry point
        if main_code:
            self.files["main.py"] = imports + "\n\n" + "\n\n".join(main_code)
        else:
            # Create a simple main.py if none exists
            if models_code or services_code or controllers_code:
                self.files["main.py"] = self._create_main_entry_point()

        # Add package init files
        self.files["src/__init__.py"] = self._create_init_file("src")
        self.files["config/__init__.py"] = self._create_init_file("config")
        if tests_code:
            self.files["tests/__init__.py"] = ""

        # Add requirements.txt
        self.files["requirements.txt"] = self._extract_requirements()

        # Add README
        self.files["README.md"] = self._create_readme()

        return self.files

    def _categorize_class(self, class_name: str) -> str:
        """Categorize class by name"""
        name_lower = class_name.lower()

        if any(
            keyword in name_lower for keyword in ["model", "entity", "schema", "dao"]
        ):
            return "model"
        elif any(
            keyword in name_lower
            for keyword in ["controller", "handler", "router", "api"]
        ):
            return "controller"
        elif any(
            keyword in name_lower for keyword in ["service", "manager", "factory"]
        ):
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
        return '''# Project

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
'''


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
            complete_structure["main.py"] = '''"""Entry point"""

if __name__ == "__main__":
    print("Starting application...")
'''

        # Add .gitignore if not present
        if ".gitignore" not in complete_structure:
            complete_structure[".gitignore"] = """# Python
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
