# Makefile for zos-ccsid-converter package
# Provides targets for building, testing, and publishing the package

# Virtual environment settings
VENV_DIR = .venv
PYTHON = python3
# On z/OS, use python -m instead of venv bin paths due to symlink issues
VENV_ACTIVATE = . $(VENV_DIR)/bin/activate &&

.PHONY: help clean build test install install-dev publish publish-test lint format check-format all venv

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

# Create virtual environment
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "Upgrading pip..."; \
		$(VENV_ACTIVATE) python3 -m pip install --upgrade pip; \
		echo "Virtual environment created and pip upgraded!"; \
	else \
		echo "Virtual environment already exists."; \
		echo "Upgrading pip..."; \
		$(VENV_ACTIVATE) python3 -m pip install --upgrade pip; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf zos_ccsid_converter.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} \; 2>/dev/null || true
	find . -type f -name '*.pyc' -exec rm -f {} \;
	find . -type f -name '*.pyo' -exec rm -f {} \;
	find . -type f -name '*~' -exec rm -f {} \;
	@echo "Clean complete!"

# Build distribution packages
build: venv clean
	@echo "Building distribution packages..."
	@echo "Installing build tools if needed..."
	$(VENV_ACTIVATE) python3 -m pip install --upgrade build wheel setuptools
	@echo "Building wheel and source distribution..."
	$(VENV_ACTIVATE) python3 -m build
	@echo ""
	@echo "Build complete! Packages created:"
	@ls -l dist/
	@echo ""
	@echo "To install locally: pip install dist/zos_ccsid_converter-*.whl"

# Run tests
test: venv install-dev
	@echo "Running test suite..."
	@echo ""
	$(VENV_ACTIVATE) cd tests && python3 test_ebcdic_converter.py
	@echo ""
	@echo "Tests complete!"

# Run tests with verbose output
test-verbose: venv
	@echo "Running test suite (verbose)..."
	@echo ""
	$(VENV_ACTIVATE) cd tests && python3 test_ebcdic_converter.py --verbose
	@echo ""
	@echo "Tests complete!"

# Run tests and keep test files
test-keep: venv
	@echo "Running test suite (keeping test files)..."
	@echo ""
	$(VENV_ACTIVATE) cd tests && python3 test_ebcdic_converter.py --keep-files
	@echo ""
	@echo "Tests complete! Test files preserved."

# Install package locally
install: venv build
	@echo "Installing package..."
	$(VENV_ACTIVATE) python3 -m pip install dist/zos_ccsid_converter-*.whl
	@echo ""
	@echo "Installation complete!"
	@echo "Test with: zos-ccsid-converter --help"

# Install in development mode
install-dev: venv
	@echo "Installing package in development mode..."
	$(VENV_ACTIVATE) python3 -m pip install -e .
	@echo ""
	@echo "Development installation complete!"
	@echo "Changes to source files will be immediately available."
	@echo "Test with: zos-ccsid-converter --help"

# Publish to TestPyPI (for testing)
publish-test: venv build
	@echo "Publishing to TestPyPI..."
	@echo "Note: You need TestPyPI credentials configured"
	@echo "Installing z/OS-compatible twine version..."
	$(VENV_ACTIVATE) python3 -m pip install 'twine==3.8.0' 'readme-renderer<42.0'
	$(VENV_ACTIVATE) python3 -m twine upload --repository testpypi dist/*
	@echo ""
	@echo "Published to TestPyPI!"
	@echo "Install with: pip install --index-url https://test.pypi.org/simple/ zos-ccsid-converter"

# Publish to PyPI (production)
publish: venv build
	@echo "WARNING: This will publish to production PyPI!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	@echo "Publishing to PyPI..."
	@echo "Installing z/OS-compatible twine version..."
	$(VENV_ACTIVATE) python3 -m pip install 'twine==3.8.0' 'readme-renderer<42.0'
	$(VENV_ACTIVATE) python3 -m twine upload dist/*
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
check: venv build
	@echo "Checking package with twine..."
	@echo "Installing z/OS-compatible twine version..."
	$(VENV_ACTIVATE) python3 -m pip install 'twine==3.8.0' 'readme-renderer<42.0'
	$(VENV_ACTIVATE) python3 -m twine check dist/*
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