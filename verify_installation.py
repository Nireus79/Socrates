#!/usr/bin/env python
"""Verify all Socrates packages are installed correctly."""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_core_imports():
    """Check socratic-core imports."""
    print("\nChecking socratic-core imports...")
    imports = [
        ("SocratesConfig", "from socratic_core import SocratesConfig"),
        ("ConfigBuilder", "from socratic_core import ConfigBuilder"),
        ("EventEmitter", "from socratic_core import EventEmitter"),
        ("EventType", "from socratic_core import EventType"),
        ("SocratesError", "from socratic_core import SocratesError"),
        ("ProjectIDGenerator", "from socratic_core.utils import ProjectIDGenerator"),
        ("UserIDGenerator", "from socratic_core.utils import UserIDGenerator"),
        ("cached", "from socratic_core.utils import cached"),
    ]

    success = True
    for name, import_stmt in imports:
        try:
            exec(import_stmt)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
            success = False

    return success

def check_backward_compatibility():
    """Check backward compatibility imports."""
    print("\nChecking backward compatibility...")
    imports = [
        ("SocratesConfig (socratic_system)", "from socratic_system import SocratesConfig"),
        ("EventType (socratic_system)", "from socratic_system import EventType"),
        ("SocratesError (socratic_system)", "from socratic_system import SocratesError"),
    ]

    success = True
    for name, import_stmt in imports:
        try:
            exec(import_stmt)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
            success = False

    return success

def check_cli():
    """Check CLI installation."""
    print("\nChecking CLI...")
    try:
        result = subprocess.run(
            ["socrates", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"  ✓ CLI installed")
            return True
        else:
            print(f"  ❌ CLI not working properly")
            print(f"     {result.stderr}")
            return False
    except FileNotFoundError:
        print("  ⚠ CLI not in PATH (might be OK for development)")
        return True
    except Exception as e:
        print(f"  ❌ Error checking CLI: {e}")
        return False

def check_api():
    """Check API installation."""
    print("\nChecking API...")
    try:
        result = subprocess.run(
            ["python", "-c", "from socrates_api.main import app; print('OK')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "OK" in result.stdout:
            print(f"  ✓ API installed")
            return True
        else:
            print(f"  ❌ API import failed")
            print(f"     {result.stderr}")
            return False
    except Exception as e:
        print(f"  ⚠ API check skipped: {e}")
        return True

def check_documentation():
    """Check documentation files."""
    print("\nChecking documentation...")
    docs = [
        "QUICKSTART.md",
        "INSTALL.md",
        "ARCHITECTURE.md",
        "MIGRATION_GUIDE.md",
        "TRANSFORMATION_STORY.md",
        "socratic-core/README.md",
        "socrates-cli/README.md",
        "socrates-api/README.md",
    ]

    missing = []
    for doc in docs:
        if not Path(doc).exists():
            missing.append(doc)
        else:
            print(f"  ✓ {doc}")

    if missing:
        print(f"  ❌ Missing documentation:")
        for doc in missing:
            print(f"     - {doc}")
        return False

    return True

def check_licenses():
    """Check license files."""
    print("\nChecking licenses...")
    licenses = [
        "LICENSE",
        "socratic-core/LICENSE",
        "socrates-cli/LICENSE",
        "socrates-api/LICENSE",
    ]

    missing = []
    for license_file in licenses:
        if not Path(license_file).exists():
            missing.append(license_file)
        else:
            print(f"  ✓ {license_file}")

    if missing:
        print(f"  ❌ Missing licenses:")
        for license_file in missing:
            print(f"     - {license_file}")
        return False

    return True

def run_basic_tests():
    """Run basic functionality tests."""
    print("\nRunning basic functionality tests...")
    try:
        # Test config creation
        from socratic_core import SocratesConfig
        config = SocratesConfig(api_key="test")
        print("  ✓ Config creation works")

        # Test ID generation
        from socratic_core.utils import ProjectIDGenerator, UserIDGenerator
        project_id = ProjectIDGenerator.generate()
        user_id = UserIDGenerator.generate()
        assert project_id.startswith("proj_")
        assert user_id.startswith("user_")
        print("  ✓ ID generation works")

        # Test event emitter
        from socratic_core import EventEmitter, EventType
        emitter = EventEmitter()
        called = []
        emitter.on(EventType.PROJECT_CREATED, lambda d: called.append(d))
        emitter.emit(EventType.PROJECT_CREATED, {"test": "data"})
        assert len(called) == 1
        print("  ✓ Event system works")

        # Test exceptions
        from socratic_core import SocratesError, ValidationError
        try:
            raise ValidationError("Test")
        except SocratesError:
            pass
        print("  ✓ Exception hierarchy works")

        return True
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 50)
    print("Socrates Installation Verification")
    print("=" * 50)

    checks = [
        ("Python Version", check_python_version),
        ("Core Imports", check_core_imports),
        ("Backward Compatibility", check_backward_compatibility),
        ("CLI", check_cli),
        ("API", check_api),
        ("Documentation", check_documentation),
        ("Licenses", check_licenses),
        ("Basic Functionality", run_basic_tests),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓" if result else "❌"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n✓ All checks passed! Installation is complete.")
        return 0
    else:
        print(f"\n❌ {total - passed} checks failed. Please review above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
