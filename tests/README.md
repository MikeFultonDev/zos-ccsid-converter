# zos-ccsid-converter Test Suite

This directory contains the test suite for the zos-ccsid-converter package.

## Test Files

- **`run_all_tests.py`** - Main test runner that discovers and executes all tests
- **`test_ebcdic_converter.py`** - Comprehensive tests for EBCDIC conversion functionality
- **`test_developer_usage_pattern.py`** - Tests for developer usage patterns with pipes
- **`test_stdin_info.py`** - Tests for `--info --stdin` CLI functionality

## Running Tests

### Run All Tests

```bash
# From project root
make test

# Or directly
cd tests
python3 run_all_tests.py
```

### Run with Verbose Output

```bash
make test-verbose

# Or directly
cd tests
python3 run_all_tests.py --verbose
```

### Keep Test Files After Execution

```bash
make test-keep

# Or directly
cd tests
python3 run_all_tests.py --keep-files
```

### Run Individual Test Files

```bash
cd tests
python3 test_ebcdic_converter.py
python3 test_developer_usage_pattern.py
python3 test_stdin_info.py
```

## Test Structure

All test files follow these conventions:

1. **Self-checking**: Each test file returns exit code 0 on success, non-zero on failure
2. **Standalone**: Each test can be run independently
3. **Cleanup**: Tests clean up temporary files unless `--keep-files` is specified
4. **Verbose mode**: Tests support `--verbose` flag for detailed output

## Adding New Tests

To add a new test file:

1. Create a file named `test_*.py` in this directory
2. Make it executable: `chmod +x test_*.py`
3. Implement a `main()` function that returns 0 on success, 1 on failure
4. Support `--verbose` and `--keep-files` arguments (optional)
5. Add `if __name__ == '__main__': sys.exit(main())` at the end

The test runner will automatically discover and run your new test.

## Test Coverage

The test suite covers:

- File conversion (ASCII to EBCDIC, EBCDIC to EBCDIC)
- Named pipe (FIFO) handling
- Stream conversion
- File tagging operations
- Error handling
- Special characters and edge cases
- CLI functionality
- Developer usage patterns

## Requirements

Tests require:

- Python 3.12 or later
- z/OS system with EBCDIC support
- Package installed in development mode (`pip install -e .`)