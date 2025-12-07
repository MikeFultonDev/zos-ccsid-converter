# Makefile for zos-ccsid-converter package
# Provides targets for building, testing, and publishing the package

.PHONY: help clean build test install install-dev publish publish-test lint format check-format all

# Default target
help:
	@echo "zos-ccsid-converter Package Makefile"
	@echo "===================================="
	@echo ""
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  clean         - Remove build artifacts and cache files"
	@echo "  build         - Build distribution packages (wheel and source)"
	@echo "  test          - Run test suite"
	@echo "  install       - Install package locally"
	@echo "  install-dev   - Install package in development mode"
	@echo "  publish-test  - Publish to TestPyPI (requires credentials)"
	@echo "  publish       - Publish to PyPI (requires credentials)"
	@echo "  lint          - Run linting checks"
	@echo "  format        - Format code with black"
	@echo "  check-format  - Check code formatting without changes"
	@echo "  all           - Clean, build, and test"
	@echo ""
	@echo "Examples:"
	@echo "  make build    - Build the package"
	@echo "  make test     - Run tests"
	@echo "  make all      - Clean, build, and test"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf zos_ccsid_converter.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete
	@echo "Clean complete!"

# Build distribution packages
build: clean
	@echo "Building distribution packages..."
	@echo "Installing build tools if needed..."
	pip install --upgrade build wheel setuptools
	@echo "Building wheel and source distribution..."
	python -m build
	@echo ""
	@echo "Build complete! Packages created:"
	@ls -lh dist/
	@echo ""
	@echo "To install locally: pip install dist/zos_ccsid_converter-*.whl"

# Run tests
test:
	@echo "Running test suite..."
	@echo ""
	cd tests && python3 test_ebcdic_converter.py
	@echo ""
	@echo "Tests complete!"

# Run tests with verbose output
test-verbose:
	@echo "Running test suite (verbose)..."
	@echo ""
	cd tests && python3 test_ebcdic_converter.py --verbose
	@echo ""
	@echo "Tests complete!"

# Run tests and keep test files
test-keep:
	@echo "Running test suite (keeping test files)..."
	@echo ""
	cd tests && python3 test_ebcdic_converter.py --keep-files
	@echo ""
	@echo "Tests complete! Test files preserved."

# Install package locally
install: build
	@echo "Installing package..."
	pip install dist/zos_ccsid_converter-*.whl
	@echo ""
	@echo "Installation complete!"
	@echo "Test with: zos-ccsid-converter --help"

# Install in development mode
install-dev:
	@echo "Installing package in development mode..."
	pip install -e .
	@echo ""
	@echo "Development installation complete!"
	@echo "Changes to source files will be immediately available."
	@echo "Test with: zos-ccsid-converter --help"

# Publish to TestPyPI (for testing)
publish-test: build
	@echo "Publishing to TestPyPI..."
	@echo "Note: You need TestPyPI credentials configured"
	pip install --upgrade twine
	python -m twine upload --repository testpypi dist/*
	@echo ""
	@echo "Published to TestPyPI!"
	@echo "Install with: pip install --index-url https://test.pypi.org/simple/ zos-ccsid-converter"

# Publish to PyPI (production)
publish: build
	@echo "WARNING: This will publish to production PyPI!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	@echo "Publishing to PyPI..."
	pip install --upgrade twine
	python -m twine upload dist/*
	@echo ""
	@echo "Published to PyPI!"
	@echo "Install with: pip install zos-ccsid-converter"

# Lint code (if linting tools are available)
lint:
	@echo "Running linting checks..."
	@if command -v pylint >/dev/null 2>&1; then \
		echo "Running pylint..."; \
		pylint zos_ccsid_converter/ || true; \
	else \
		echo "pylint not installed. Install with: pip install pylint"; \
	fi
	@if command -v flake8 >/dev/null 2>&1; then \
		echo "Running flake8..."; \
		flake8 zos_ccsid_converter/ || true; \
	else \
		echo "flake8 not installed. Install with: pip install flake8"; \
	fi

# Format code with black
format:
	@echo "Formatting code with black..."
	@if command -v black >/dev/null 2>&1; then \
		black zos_ccsid_converter/ tests/ examples/; \
		echo "Formatting complete!"; \
	else \
		echo "black not installed. Install with: pip install black"; \
		exit 1; \
	fi

# Check code formatting
check-format:
	@echo "Checking code formatting..."
	@if command -v black >/dev/null 2>&1; then \
		black --check zos_ccsid_converter/ tests/ examples/; \
	else \
		echo "black not installed. Install with: pip install black"; \
		exit 1; \
	fi

# Verify package contents
verify: build
	@echo "Verifying package contents..."
	@echo ""
	@echo "=== Wheel contents ==="
	unzip -l dist/zos_ccsid_converter-*.whl
	@echo ""
	@echo "=== Source distribution contents ==="
	tar -tzf dist/zos_ccsid_converter-*.tar.gz
	@echo ""
	@echo "Verification complete!"

# Check package with twine
check: build
	@echo "Checking package with twine..."
	pip install --upgrade twine
	python -m twine check dist/*
	@echo ""
	@echo "Package check complete!"

# Run all: clean, build, test
all: clean build test
	@echo ""
	@echo "All tasks complete!"
	@echo "Package is ready for distribution."

# Show package info
info:
	@echo "Package Information"
	@echo "==================="
	@echo "Name: zos-ccsid-converter"
	@echo "Version: 1.0.0"
	@echo "Location: $(PWD)"
	@echo ""
	@echo "Package structure:"
	@tree -L 2 -I '__pycache__|*.pyc|*.egg-info' . || ls -R

# Create a release (build, test, verify, check)
release: clean build test verify check
	@echo ""
	@echo "Release preparation complete!"
	@echo ""
	@echo "Package is ready for publishing."
	@echo "To publish to TestPyPI: make publish-test"
	@echo "To publish to PyPI:     make publish"