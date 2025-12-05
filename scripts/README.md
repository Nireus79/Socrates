# Socrates Development Scripts

Utility scripts for testing, benchmarking, documentation, and analysis.

## Scripts Overview

### 1. coverage_report.py

Generates comprehensive coverage reports in multiple formats.

**Usage:**

```bash
python scripts/coverage_report.py
```

**Features:**
- Runs pytest with coverage instrumentation
- Generates HTML report (htmlcov/index.html)
- Generates JSON report (coverage.json)
- Generates XML report (coverage.xml)
- Creates coverage badge (coverage.svg)
- Prints summary to terminal

**Output:**
- HTML coverage report with file-by-file breakdown
- Terminal summary with key metrics
- Badge showing overall coverage percentage
- Minimum coverage threshold enforcement (70%)

**Configuration:**
- See `.coveragerc` for coverage settings
- Modify `branch = True` to measure branch coverage
- Adjust `exclude_lines` for lines to ignore

**Example output:**
```
COVERAGE SUMMARY
Overall Coverage: 82.5%
  Statements: 82.5%
  Branches: 75.2%
  Lines: 2,450 statements
  Missing: 425 lines
```

### 2. test_performance.py

Performance benchmarking tests for key operations.

**Installation:**

```bash
pip install pytest-benchmark
```

**Usage:**

```bash
# Run all benchmarks
pytest tests/test_performance.py --benchmark-only

# Run specific benchmark
pytest tests/test_performance.py::TestConfigPerformance -v --benchmark-only

# Save benchmark results
pytest tests/test_performance.py --benchmark-only --benchmark-save=baseline

# Compare against baseline
pytest tests/test_performance.py --benchmark-only --benchmark-compare=baseline
```

**Benchmarks:**
- Configuration creation and loading
- Event emission and listener management
- Orchestrator initialization and requests
- Database operations (save, load, list)
- Data model creation
- Memory usage with large datasets

**Output:**
```
test_config_creation_benchmark        5.23 ms (0.32 ms)
test_event_emission_benchmark         2.15 ms (0.08 ms)
test_orchestrator_creation_benchmark  12.45 ms (1.02 ms)
```

**Track Performance Over Time:**
1. Run baseline: `pytest tests/test_performance.py --benchmark-save=baseline --benchmark-only`
2. Make changes
3. Compare: `pytest tests/test_performance.py --benchmark-compare=baseline --benchmark-only`

### 3. load_test.py

Load testing framework using locust for API endpoint stress testing.

**Installation:**

```bash
pip install locust
```

**Setup:**

1. Start the API server:
```bash
python socrates-api/src/socrates_api/main.py
```

2. Run load tests in another terminal:

**Interactive Mode (Web UI):**
```bash
locust -f tests/load_test.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser.

**Headless Mode:**

Light load:
```bash
locust -f tests/load_test.py --host=http://localhost:8000 \
    --users=10 --spawn-rate=2 --run-time=1m --headless
```

Medium load:
```bash
locust -f tests/load_test.py --host=http://localhost:8000 \
    --users=50 --spawn-rate=5 --run-time=5m --headless
```

Heavy load:
```bash
locust -f tests/load_test.py --host=http://localhost:8000 \
    --users=200 --spawn-rate=20 --run-time=10m --headless
```

Stress test:
```bash
locust -f tests/load_test.py --host=http://localhost:8000 \
    --users=500 --spawn-rate=50 --run-time=15m --headless
```

**Load Test Scenarios:**

| Scenario | Users | Spawn Rate | Duration | Purpose |
|----------|-------|-----------|----------|---------|
| Light | 10 | 2/sec | 1m | Smoke test |
| Medium | 50 | 5/sec | 5m | Normal load |
| Heavy | 200 | 20/sec | 10m | Peak load |
| Stress | 500 | 50/sec | 15m | Breaking point |

**Tasks Simulated:**

- List projects (30% of traffic)
- Create projects (20%)
- Get event history (20%)
- Health checks (10%)
- Test connections (10%)
- Admin monitoring (10%)

**Expected Performance:**

Light load:
- Throughput: 10-20 req/s
- Response time: 50-200ms

Medium load:
- Throughput: 50-100 req/s
- Response time: 100-500ms

Heavy load:
- Throughput: 100-200 req/s
- Response time: 200-1000ms

**Web UI Features:**
- Real-time request statistics
- Response time charts
- Failure tracking
- Request distribution
- Export results

### 4. generate_docs.py

Generates documentation from source code docstrings.

**Installation:**

```bash
# No additional dependencies required
```

**Usage:**

```bash
python scripts/generate_docs.py
```

**Generated Files:**

1. **docs/API.md** - Complete API reference
   - Extracted from source docstrings
   - Organized by module and class
   - Includes function signatures

2. **docs/TESTS.md** - Test documentation
   - Test classes and methods
   - Test descriptions and coverage
   - Organized by feature

3. **docs/FEATURES.md** - Feature overview
   - High-level feature descriptions
   - Capability lists
   - Integration points

4. **docs/INDEX.md** - Documentation index
   - Quick links
   - Documentation organization
   - Navigation guide

**Docstring Format:**

Use standard Python docstrings:

```python
def function_name(param1, param2):
    """
    Brief description.

    Longer description with details.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value
    """
    pass
```

**Class docstring:**

```python
class ClassName:
    """
    Brief class description.

    Longer description explaining purpose and usage.
    """

    def method(self):
        """Brief method description."""
        pass
```

## Running All Tests & Reports

Complete workflow:

```bash
# 1. Run all tests with coverage
python scripts/coverage_report.py

# 2. Run performance benchmarks
pytest tests/test_performance.py --benchmark-only

# 3. Generate documentation
python scripts/generate_docs.py

# 4. Start API for load testing
python socrates-api/src/socrates_api/main.py &

# 5. Run load tests
locust -f tests/load_test.py --host=http://localhost:8000 \
    --users=50 --spawn-rate=5 --run-time=5m --headless
```

## Integration with CI/CD

These scripts are integrated with GitHub Actions:

- **Coverage reports** - Run on every push and PR
- **Performance benchmarks** - Run before releases
- **Load tests** - Manual workflow dispatch
- **Documentation generation** - On documentation changes

## Interpreting Results

### Coverage Reports

- **Green (80%+)**: Excellent coverage
- **Yellow (70-80%)**: Acceptable coverage
- **Red (<70%)**: Needs improvement

Target: 70%+ overall coverage

### Performance Benchmarks

- **Regression**: Operation slower than baseline
- **Improvement**: Operation faster than baseline
- **Stable**: Within normal variation

Accept up to 10% variance due to system load.

### Load Test Results

- **Response time**: Should stay < 500ms at medium load
- **Error rate**: Should stay < 1%
- **Throughput**: Should scale linearly with users

### Documentation

- Check `docs/INDEX.md` for overview
- Use `docs/API.md` for API reference
- Use `docs/TESTS.md` for test details

## Troubleshooting

### Coverage Issues

**Problem**: Coverage report not generated

**Solution**:
```bash
pip install pytest-cov
python scripts/coverage_report.py
```

### Performance Benchmarks

**Problem**: Benchmarks too slow

**Solution**:
```bash
# Run quick benchmark only
pytest tests/test_performance.py::TestConfigPerformance -v --benchmark-only
```

### Load Testing

**Problem**: "Address already in use"

**Solution**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

### Documentation Generation

**Problem**: "No module named ast"

**Solution**: ast is built-in, check Python installation
```bash
python --version  # Should be 3.8+
```

## Best Practices

1. **Run coverage before committing**
   ```bash
   python scripts/coverage_report.py
   ```

2. **Check performance regressions before releasing**
   ```bash
   pytest tests/test_performance.py --benchmark-compare=baseline
   ```

3. **Load test major changes**
   ```bash
   locust -f tests/load_test.py --host=http://localhost:8000
   ```

4. **Update documentation after API changes**
   ```bash
   python scripts/generate_docs.py
   ```

5. **Track performance metrics**
   - Save benchmark baselines before releases
   - Compare performance over versions
   - Identify bottlenecks early

## Resources

- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [Python AST Documentation](https://docs.python.org/3/library/ast.html)

## Contributing

When adding new features:

1. Write tests in `tests/test_*.py`
2. Add docstrings to code
3. Run coverage: `python scripts/coverage_report.py`
4. Run benchmarks: `pytest tests/test_performance.py --benchmark-only`
5. Generate docs: `python scripts/generate_docs.py`
6. Update load tests if adding new endpoints

## Support

For script issues:
- Check script help: `python scripts/script_name.py --help`
- View detailed output: Add `-v` or `-vv` flags
- Check documentation: See docs/ folder
- Open GitHub issue: https://github.com/Nireus79/Socrates/issues
