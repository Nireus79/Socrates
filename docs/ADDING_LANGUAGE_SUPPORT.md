# Adding Language Support to Socrates Code Extraction

This guide explains how to add support for new programming languages in the Socrates code extraction system.

## Overview

The code extraction system uses a **plugin architecture** where each language has its own "extractor" class. This allows community contributions without modifying core code.

### Key Concepts

- **Extractor**: Language-specific class that extracts code from markdown and validates syntax
- **Registry**: Central registry that manages all extractors (plugin system)
- **Metadata**: Information about an extractor (name, extensions, fence IDs, etc.)

## Quick Start: Adding TypeScript Support

Here's a complete example of adding TypeScript extraction.

### Step 1: Create the Extractor Class

Create a new file: `socratic_system/utils/extractors/typescript_extractor.py`

```python
"""TypeScript code extractor and validator"""

import subprocess
import tempfile
import logging
from typing import List

from .base import BaseLanguageExtractor
from .models import ValidationResult

logger = logging.getLogger(__name__)


class TypeScriptExtractor(BaseLanguageExtractor):
    """TypeScript code extraction using tsc compiler"""

    def get_file_extensions(self) -> List[str]:
        """Return TypeScript file extensions"""
        return [".ts", ".tsx"]

    def get_code_fence_identifiers(self) -> List[str]:
        """Return markdown fence identifiers for TypeScript"""
        return ["typescript", "ts", "tsx"]

    def validate_syntax(self, code: str) -> ValidationResult:
        """Validate TypeScript code using tsc compiler"""

        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Empty code"
            )

        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
                f.write(code)
                temp_path = f.name

            # Run TypeScript compiler in check mode (no output)
            result = subprocess.run(
                ['tsc', '--noEmit', temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.debug("TypeScript code validation: syntax is valid")
                return ValidationResult(is_valid=True)
            else:
                logger.error(f"TypeScript validation failed: {result.stderr}")
                return ValidationResult(
                    is_valid=False,
                    error_message=result.stderr
                )

        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                error_message="TypeScript compiler (tsc) not found. Install with: npm install -g typescript"
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                is_valid=False,
                error_message="TypeScript compilation timed out"
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unexpected error: {str(e)}"
            )

    def get_import_statements(self, code: str) -> List[str]:
        """Extract import statements from TypeScript"""

        imports = []

        for line in code.split('\n'):
            line = line.strip()

            # Match TypeScript/JavaScript import styles
            if line.startswith('import '):  # import x from 'y'
                imports.append(line)
            elif line.startswith('require('):  # require('x')
                imports.append(line)

        return imports
```

### Step 2: Register the Extractor

Add registration code to `socratic_system/utils/extractors/registry.py` in the `auto_register_extractors()` function:

```python
# In auto_register_extractors() function, add:

try:
    from .typescript_extractor import TypeScriptExtractor

    LanguageExtractorRegistry.register(
        LanguageExtractorMetadata(
            language="typescript",
            display_name="TypeScript",
            file_extensions=[".ts", ".tsx"],
            fence_identifiers=["typescript", "ts", "tsx"],
            extractor_class=TypeScriptExtractor,
            supports_ast=True,
            supports_linting=False,
            available=True,
            description="TypeScript extraction and validation using tsc compiler",
            requires_external_tool=True,
            dependencies=["typescript"]  # npm package required
        )
    )
    logger.info("Registered TypeScript extractor")

except ImportError:
    # Register as unavailable if tsc is not installed
    LanguageExtractorRegistry.register(
        LanguageExtractorMetadata(
            language="typescript",
            display_name="TypeScript",
            file_extensions=[".ts", ".tsx"],
            fence_identifiers=["typescript", "ts", "tsx"],
            extractor_class=None,
            supports_ast=False,
            supports_linting=False,
            available=False,
            description="TypeScript extraction (requires: npm install -g typescript)",
            requires_external_tool=True,
            dependencies=["typescript"]
        )
    )
    logger.debug("TypeScript extractor not available (typescript not installed)")
```

### Step 3: Test Your Extractor

Create a test file to verify it works:

```python
from socratic_system.utils.extractors.registry import LanguageExtractorRegistry

# Get the extractor
extractor = LanguageExtractorRegistry.get_extractor("typescript")

# Test markdown extraction
markdown = """
# TypeScript Module

```typescript
function greet(name: string): string {
    return `Hello, ${name}!`;
}
```
"""

result = extractor.extract_and_validate(markdown)
print(f"Valid: {result.is_valid}")
print(f"Code blocks found: {result.code_blocks_found}")
```

## Reference: BaseLanguageExtractor Interface

All extractors must inherit from `BaseLanguageExtractor` and implement these methods:

### Abstract Methods (must implement)

```python
def get_file_extensions(self) -> List[str]:
    """Return file extensions (e.g., ['.ts', '.tsx'])"""
    pass

def get_code_fence_identifiers(self) -> List[str]:
    """Return markdown fence IDs (e.g., ['typescript', 'ts'])"""
    pass

def validate_syntax(self, code: str) -> ValidationResult:
    """Validate code syntax and return ValidationResult"""
    pass

def get_import_statements(self, code: str) -> List[str]:
    """Extract imports/requires from code"""
    pass
```

### Provided Methods (inherited - you can use these)

```python
def is_markdown_format(self, content: str) -> bool:
    """Check if content is markdown (inherited from base)"""
    # Already implemented - no need to override

def extract_from_markdown(self, content: str) -> ExtractionResult:
    """Extract code from markdown (inherited from base)"""
    # Already implemented - uses your get_code_fence_identifiers()

def extract_and_validate(self, content: str) -> ExtractionResult:
    """Extract and validate in one call (inherited from base)"""
    # Already implemented - uses your extract_from_markdown() and validate_syntax()
```

## Other Language Examples

### JavaScript (Simple Pattern Matching)

```python
class JavaScriptExtractor(BaseLanguageExtractor):

    def get_file_extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]

    def get_code_fence_identifiers(self) -> List[str]:
        return ["javascript", "js"]

    def validate_syntax(self, code: str) -> ValidationResult:
        # For JavaScript, could use esprima:
        # pip install esprima
        try:
            import esprima
            esprima.parse(code)
            return ValidationResult(is_valid=True)
        except:
            return ValidationResult(is_valid=False, ...)

    def get_import_statements(self, code: str) -> List[str]:
        # Extract require() and import statements
        ...
```

### Rust (Using Compiler)

```python
class RustExtractor(BaseLanguageExtractor):

    def get_file_extensions(self) -> List[str]:
        return [".rs"]

    def get_code_fence_identifiers(self) -> List[str]:
        return ["rust", "rs", "rustlang"]

    def validate_syntax(self, code: str) -> ValidationResult:
        # Use rustc compiler to check syntax
        # rustc --crate-type lib --emit metadata <file>
        try:
            result = subprocess.run(['rustc', '--crate-type', 'lib', ...])
            # Parse result.stderr for errors
            ...
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                error_message="rustc not found. Install Rust with: rustup"
            )

    def get_import_statements(self, code: str) -> List[str]:
        # Extract use statements
        ...
```

### Go (Using Compiler)

```python
class GoExtractor(BaseLanguageExtractor):

    def get_file_extensions(self) -> List[str]:
        return [".go"]

    def get_code_fence_identifiers(self) -> List[str]:
        return ["go", "golang"]

    def validate_syntax(self, code: str) -> ValidationResult:
        # Use gofmt to check syntax
        try:
            result = subprocess.run(['gofmt', '-l'], input=code, ...)
            return ValidationResult(is_valid=(result.returncode == 0))
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                error_message="Go not found. Install from: https://golang.org"
            )

    def get_import_statements(self, code: str) -> List[str]:
        # Extract import statements
        ...
```

## Best Practices

### 1. Handle Missing Dependencies Gracefully

```python
try:
    from .javascript_extractor import JavaScriptExtractor
    # Register as available
except ImportError:
    # Register as unavailable with helpful message
    LanguageExtractorRegistry.register(
        LanguageExtractorMetadata(
            # ...
            available=False,
            description="Requires: pip install esprima"
        )
    )
```

### 2. Use Temporary Files for External Tools

```python
import tempfile

with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
    f.write(code)
    temp_path = f.name

try:
    result = subprocess.run(['tsc', '--noEmit', temp_path], ...)
finally:
    import os
    os.unlink(temp_path)
```

### 3. Add Helpful Error Messages

```python
return ValidationResult(
    is_valid=False,
    error_message="TypeScript compiler (tsc) not found. Install with: npm install -g typescript"
)
```

### 4. Log Important Events

```python
logger = logging.getLogger(__name__)

logger.info(f"Validating {self.language} code...")
logger.error(f"Validation failed: {error_msg}")
logger.debug(f"Found {len(imports)} imports")
```

## Testing Your Extractor

Add unit tests in `tests/utils/extractors/test_yourLanguage_extractor.py`:

```python
import pytest
from socratic_system.utils.extractors.registry import LanguageExtractorRegistry

class TestTypeScriptExtractor:

    def test_get_extensions(self):
        extractor = LanguageExtractorRegistry.get_extractor("typescript")
        assert ".ts" in extractor.get_file_extensions()

    def test_validate_valid_code(self):
        extractor = LanguageExtractorRegistry.get_extractor("typescript")
        code = "function greet(name: string): string { return name; }"
        result = extractor.validate_syntax(code)
        assert result.is_valid

    def test_extract_from_markdown(self):
        extractor = LanguageExtractorRegistry.get_extractor("typescript")
        markdown = "```typescript\nfunction test() {}\n```"
        result = extractor.extract_from_markdown(markdown)
        assert "function test()" in result.extracted_code
```

## Integration Points

Once your extractor is registered, it automatically works with:

1. **Claude Client** - Extracts code from Claude's markdown responses
2. **Artifact Saver** - Validates before saving as files
3. **Multi-File Splitter** - Organizes code into project structure
4. **Code Analysis** - Gets import statements for requirements

No additional integration needed - the registry handles everything!

## Submitting Your Extractor

To contribute your extractor to Socrates:

1. Create a pull request with your new extractor file
2. Add it to `socratic_system/utils/extractors/`
3. Register it in `registry.py`
4. Add unit tests in `tests/utils/extractors/`
5. Update this guide with your example

The maintainers will review and merge!

## Troubleshooting

### "ExtractorNotFound" Error

Check if your extractor is registered:

```python
from socratic_system.utils.extractors.registry import LanguageExtractorRegistry

# List all extractors
for metadata in LanguageExtractorRegistry.list_all():
    print(f"{metadata.language}: available={metadata.available}")
```

### Extractor Marked as "Unavailable"

The dependency might not be installed:

```python
# Check metadata
metadata = LanguageExtractorRegistry.get_metadata("typescript")
print(f"Available: {metadata.available}")
print(f"Dependencies: {metadata.dependencies}")
```

Install the required dependency and try again.

### Markdown Not Extracted

Check if your fence identifiers match:

```python
extractor = LanguageExtractorRegistry.get_extractor("typescript")
print(extractor.get_code_fence_identifiers())
# Output: ['typescript', 'ts', 'tsx']

# Your markdown must use one of these:
# ```typescript ... ```
# ```ts ... ```
# ```tsx ... ```
```

## Architecture Overview

```
User asks for code generation
         |
         v
Claude API returns (often in markdown)
         |
         v
LanguageExtractorRegistry.get_extractor(language)
         |
         v
Language-specific Extractor
  ├─ extract_from_markdown() [inherited]
  │  ├─ Detect markdown format [inherited]
  │  ├─ Extract code blocks [inherited]
  │  ├─ validate_syntax() [implemented by you]
  │  └─ Return ExtractionResult
  |
  ├─ validate_syntax() [implemented by you]
  │  └─ Use language-specific parser
  │
  └─ get_import_statements() [implemented by you]
     └─ Extract dependencies

Result used by:
  - Artifact Saver (validation)
  - Multi-File Splitter (organization)
  - Code Analysis (dependency detection)
```

## Questions?

- Check existing extractors for examples: `PythonExtractor`, `GenericExtractor`
- Read the base class: `socratic_system/utils/extractors/base.py`
- Review the registry: `socratic_system/utils/extractors/registry.py`

Happy contributing!
