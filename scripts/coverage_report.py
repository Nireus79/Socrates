"""
Coverage reporting script for Socrates

Generates comprehensive coverage reports in multiple formats:
- HTML report
- Terminal report
- JSON report
- Coverage badge
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict


def run_coverage() -> int:
    """Run coverage tests and generate reports"""
    print("=" * 70)
    print("SOCRATES COVERAGE REPORT GENERATOR")
    print("=" * 70)
    print()

    # Run pytest with coverage
    print("Running tests with coverage...")
    cmd = [
        "pytest",
        "--cov=socratic_system",
        "--cov=socrates_cli",
        "--cov=socrates_api",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-report=json",
        "--cov-report=xml",
        "-v",
    ]

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n[ERROR] Tests failed!")
        return result.returncode

    print("\n[SUCCESS] Tests completed!")

    # Parse coverage report
    coverage_file = Path("coverage.json")
    if coverage_file.exists():
        with open(coverage_file) as f:
            coverage_data = json.load(f)

        print_coverage_summary(coverage_data)

    return 0


def print_coverage_summary(coverage_data: Dict) -> None:
    """Print coverage summary from JSON report"""
    print("\n" + "=" * 70)
    print("COVERAGE SUMMARY")
    print("=" * 70)

    totals = coverage_data.get("totals", {})

    print("\nOverall Coverage:")
    print(f"  Statements: {totals.get('percent_covered', 0):.1f}%")
    print(f"  Branches: {totals.get('percent_covered_branch', 0):.1f}%")
    print(f"  Lines: {totals.get('num_statements', 0)} statements")
    print(f"  Missing: {totals.get('missing_lines', 0)} lines")

    # File coverage
    files = coverage_data.get("files", {})
    file_coverage = []

    for filepath, file_data in sorted(files.items()):
        if (
            "socratic_system" in filepath
            or "socrates_cli" in filepath
            or "socrates_api" in filepath
        ):
            percent = file_data.get("summary", {}).get("percent_covered", 0)
            file_coverage.append((filepath, percent))

    if file_coverage:
        print("\nFile Coverage (Top 10):")
        print(f"  {'File':<50} {'Coverage':>10}")
        print(f"  {'-' * 50} {'-' * 10}")

        for filepath, percent in sorted(file_coverage, key=lambda x: x[1])[:10]:
            short_name = filepath.replace("C:\\Users\\themi\\PycharmProjects\\Socrates\\", "")
            print(f"  {short_name:<50} {percent:>9.1f}%")

    # Check minimum coverage
    min_coverage = 70
    overall = totals.get("percent_covered", 0)

    print(f"\nMinimum Coverage Threshold: {min_coverage}%")
    if overall >= min_coverage:
        print(f"✓ Overall coverage {overall:.1f}% meets threshold")
        return 0
    else:
        print(f"✗ Overall coverage {overall:.1f}% below threshold")
        return 1


def generate_badge() -> None:
    """Generate coverage badge"""
    try:
        subprocess.run(["coverage-badge", "-o", "coverage.svg", "-f"], check=True)
        print("\n[SUCCESS] Coverage badge generated: coverage.svg")
    except FileNotFoundError:
        print("\n[INFO] coverage-badge not installed, skipping badge generation")
        print("  Install with: pip install coverage-badge")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Failed to generate badge: {e}")


def generate_html_report() -> None:
    """Generate HTML coverage report"""
    html_dir = Path("htmlcov")
    if html_dir.exists():
        index_file = html_dir / "index.html"
        if index_file.exists():
            print("\n[SUCCESS] HTML coverage report: htmlcov/index.html")
            print(f"  Open in browser: file://{index_file.absolute()}")


def main() -> int:
    """Main entry point"""
    # Run coverage
    exit_code = run_coverage()

    if exit_code == 0:
        # Generate badge
        generate_badge()

        # Show HTML report info
        generate_html_report()

        print("\n" + "=" * 70)
        print("REPORTS GENERATED:")
        print("  - htmlcov/index.html (HTML report)")
        print("  - coverage.json (JSON report)")
        print("  - coverage.xml (XML report)")
        print("  - coverage.svg (Badge)")
        print("=" * 70)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
