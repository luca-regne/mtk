# Batuta Test Suite

This directory contains the test suite for the batuta project using pytest.

## Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Unit tests
│   └── cli/
│       └── test_apk.py     # Tests for src/batuta/cli/apk.py
└── README.md               # This file
```

## Running Tests

### Install Test Dependencies

```bash
# Using uv (recommended)
uv sync --group test

# Or using pip
pip install -e ".[test]"
```

### Run All Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run tests in a specific file
uv run pytest tests/unit/cli/test_apk.py
```

### Run with Coverage

```bash
# Run tests with coverage report
uv run pytest --cov=batuta.cli.apk --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=batuta.cli.apk --cov-report=html

# View HTML coverage report (opens in browser)
open htmlcov/index.html
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
uv run pytest tests/unit/cli/test_apk.py::TestListCommand

# Run a specific test method
uv run pytest tests/unit/cli/test_apk.py::TestListCommand::test_list_basic_success

# Run tests matching a pattern
uv run pytest -k "test_list"
```

### Run with Markers

```bash
# Run only unit tests
uv run pytest -m unit

# Run only CLI tests
uv run pytest -m cli
```

## Test Coverage

Current coverage for `src/batuta/cli/apk.py`:

- **84% statement coverage**
- **74 test cases**
- All commands tested (list, search, info, pull, merge, decompile, patch)
- Helper functions fully tested

### Coverage Breakdown

- **Helper Functions**: 95%+ coverage
  - `_parse_selection()` - fully tested with all edge cases
  - `_select_package()` - interactive selection tested
  - `_display_package_table()` - tested via integration

- **Commands**: 80%+ coverage
  - `list` - 8 test cases
  - `search` - 5 test cases
  - `info` - 5 test cases
  - `pull` - 11 test cases
  - `merge` - 4 test cases
  - `decompile` - 7 test cases
  - `patch` - 8 test cases

## Writing New Tests

### Test Structure

Tests are organized by functionality:

1. **Helper function tests**: Test utility functions in isolation
2. **Command tests**: Test CLI commands with mocked dependencies
3. **Integration tests**: (Future) Test with real tools

### Mocking Strategy

All external dependencies are mocked:

- `ADBWrapper` - Mock ADB operations
- `APKDecompiler` - Mock decompilation
- `SplitAPKMerger` - Mock APK merging
- `APKPatcher` - Mock patching
- `console` - Mock rich output
- `require()` - Mock tool checks

### Example Test

```python
@patch("batuta.cli.apk.require")
@patch("batuta.cli.apk.ADBWrapper")
def test_list_basic_success(mock_adb_class, mock_require, cli_runner):
    """Test basic list command without filters."""
    mock_adb = MagicMock()
    mock_adb_class.return_value = mock_adb
    mock_adb.list_packages.return_value = ["com.example.app"]

    result = cli_runner.invoke(app, ["list"])

    assert result.exit_code == 0
    mock_adb.list_packages.assert_called_once()
```

### Fixtures Available

See `conftest.py` for all available fixtures:

- `cli_runner` - Typer CLI runner
- `sample_package_info` - Sample PackageInfo model
- `sample_pulled_apk` - Sample PulledAPK model
- `sample_decompile_result` - Sample DecompileResult model
- `sample_patch_result` - Sample PatchResult model
- `temp_apk_file` - Temporary APK file
- `temp_split_dir` - Temporary split APK directory
- `temp_apktool_dir` - Temporary apktool directory

## Continuous Integration

The test suite is designed to run in CI environments:

- Fast execution (< 1 second for full suite)
- No external dependencies required
- All tools mocked
- Deterministic results

## Future Improvements

- [ ] Add integration tests with real tools (optional)
- [ ] Test other CLI modules (device, analyze)
- [ ] Test core modules (adb, decompiler, merger, patcher)
- [ ] Test utils modules (deps, process, config)
- [ ] Add property-based testing with Hypothesis
- [ ] Add mutation testing with mutmut
