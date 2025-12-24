# Makefile for zos-ccsid-converter package
# Provides targets for building, testing, and publishing the package

# Virtual environment settings
VENV_DIR = .venv
PYTHON = python3
# On z/OS, use python -m instead of venv bin paths due to symlink issues
VENV_ACTIVATE = . $(VENV_DIR)/bin/activate &&

.PHONY: help clean build test install install-dev publish publish-test lint format check-format all venv install-zos-util

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

# Check if we're on z/OS and ensure zos-util is available
check-zos-util:
	@UNAME=$$(uname -s); \
	if [ "$$UNAME" = "OS/390" ]; then \
		echo "Detected z/OS system - checking for zos-util..."; \
		if ! python3 -m site --user-site >/dev/null 2>&1; then \
			echo "Enabling user site-packages..."; \
			export PYTHONUSERBASE=$$HOME/.local; \
		fi; \
		if ! python3 -c "import sys; import site; site.ENABLE_USER_SITE = True; import zos_util" 2>/dev/null; then \
			echo "zos-util not found - will install it"; \
			$(MAKE) install-zos-util; \
			echo "Verifying zos-util installation..."; \
			if python3 -c "import sys; import site; site.ENABLE_USER_SITE = True; import zos_util" 2>/dev/null; then \
				echo "zos-util successfully installed and verified"; \
			else \
				echo "ERROR: zos-util installation failed verification"; \
				echo "User site-packages: $$(python3 -m site --user-site)"; \
				exit 1; \
			fi; \
		else \
			echo "zos-util is already installed"; \
		fi; \
	else \
		echo "Not on z/OS (detected: $$UNAME) - skipping zos-util check"; \
	fi

# Build distribution packages
build: venv clean bundle-zos-util
	@UNAME=$$(uname -s); \
	if [ "$$UNAME" != "OS/390" ]; then \
		echo "ERROR: This package requires z/OS to build and run."; \
		echo "Detected system: $$UNAME"; \
		exit 1; \
	fi
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
test: venv check-zos-util install-dev
	@UNAME=$$(uname -s); \
	if [ "$$UNAME" != "OS/390" ]; then \
		echo "ERROR: This package requires z/OS to run tests."; \
		echo "Detected system: $$UNAME"; \
		exit 1; \
	fi
	@echo "Running test suite..."
	@echo ""
	@echo "Clearing Python cache..."
	@find . -type d -name __pycache__ -exec rm -rf {} \; 2>/dev/null || true
	@find . -type f -name '*.pyc' -exec rm -f {} \;
	@echo "Running on z/OS - ensuring user site-packages are accessible..."
	@USER_SITE=$$($(VENV_DIR)/bin/python3 -m site --user-site); \
	PROJ_DIR=$$(pwd); \
	echo "User site-packages: $$USER_SITE"; \
	echo "Project directory: $$PROJ_DIR"; \
	echo "Setting PYTHONPATH=$$PROJ_DIR:$$USER_SITE:/usr/lpp/IBM/zoautil/lib/3.13:$$PYTHONPATH"; \
	$(VENV_ACTIVATE) export PYTHONPATH=$$PROJ_DIR:$$USER_SITE:/usr/lpp/IBM/zoautil/lib/3.13:$$PYTHONPATH && cd tests && python3 -c "import sys; print('Python path:', sys.path)" && python3 run_all_tests.py
	@echo ""
	@echo "Tests complete!"

# Run tests with verbose output
test-verbose: venv install-dev
	@echo "Running test suite (verbose)..."
	@echo ""
	$(VENV_ACTIVATE) cd tests && python3 run_all_tests.py --verbose
	@echo ""
	@echo "Tests complete!"

# Run tests and keep test files
test-keep: venv install-dev
	@echo "Running test suite (keeping test files)..."
	@echo ""
	$(VENV_ACTIVATE) cd tests && python3 run_all_tests.py --keep-files
	@echo ""
	@echo "Tests complete! Test files preserved."

# Install package locally
install: venv build
	@echo "Installing package..."
	$(VENV_ACTIVATE) python3 -m pip install dist/zos_ccsid_converter-*.whl
	@echo ""
	@echo "Installation complete!"
	@echo "Test with: zos-ccsid-converter --help"

# Install zos-util (required on z/OS)
install-zos-util:
	@echo "Installing zos-util..."
	@if [ ! -d "../zos-util" ]; then \
		echo "Cloning zos-util..."; \
		cd .. && git clone https://github.com/IBM/zos-util.git; \
	fi
	@echo "Checking for available C compiler..."
	@PROJ_DIR=$$(pwd); \
	if command -v clang >/dev/null 2>&1; then \
		echo "Found clang compiler"; \
		export CC=clang; \
	elif command -v xlc >/dev/null 2>&1; then \
		echo "Found xlc compiler"; \
		export CC=xlc; \
	elif command -v c89 >/dev/null 2>&1; then \
		echo "Found c89 compiler"; \
		export CC=c89; \
	elif command -v c99 >/dev/null 2>&1; then \
		echo "Found c99 compiler"; \
		export CC=c99; \
	else \
		echo "ERROR: No C compiler found. Please install clang, xlc, c89, or c99."; \
		exit 1; \
	fi; \
	echo "Building and installing zos-util with $$CC (user install)..."; \
	cd ../zos-util && CC=$$CC $$PROJ_DIR/$(VENV_DIR)/bin/python3 setup.py install --user
	@echo ""
	@echo "zos-util installation complete!"

# Bundle zos-util shared library into package
bundle-zos-util:
	@echo "Bundling zos-util shared library..."
	@if [ ! -d "../zos-util" ]; then \
		echo "Cloning zos-util..."; \
		cd .. && git clone https://github.com/IBM/zos-util.git; \
	fi
	@echo "Checking for available C compiler..."
	@PROJ_DIR=$$(pwd); \
	if command -v clang >/dev/null 2>&1; then \
		echo "Found clang compiler"; \
		export CC=clang; \
	elif command -v xlc >/dev/null 2>&1; then \
		echo "Found xlc compiler"; \
		export CC=xlc; \
	elif command -v c89 >/dev/null 2>&1; then \
		echo "Found c89 compiler"; \
		export CC=c89; \
	elif command -v c99 >/dev/null 2>&1; then \
		echo "Found c99 compiler"; \
		export CC=c99; \
	else \
		echo "ERROR: No C compiler found. Please install clang, xlc, c89, or c99."; \
		exit 1; \
	fi; \
	echo "Building zos-util with $$CC..."; \
	cd ../zos-util && CC=$$CC $$PROJ_DIR/$(VENV_DIR)/bin/python3 setup.py build; \
	echo "Copying shared library to package..."; \
	mkdir -p $$PROJ_DIR/zos_ccsid_converter/lib; \
	find ../zos-util/build -name "*.so" -exec cp {} $$PROJ_DIR/zos_ccsid_converter/lib/ \;; \
	if [ -f $$PROJ_DIR/zos_ccsid_converter/lib/*.so ]; then \
		echo "Successfully bundled zos-util shared library"; \
		ls -l $$PROJ_DIR/zos_ccsid_converter/lib/; \
	else \
		echo "ERROR: Failed to find zos-util shared library"; \
		exit 1; \
	fi
	@echo ""
	@echo "zos-util bundling complete!"

# Install in development mode
install-dev: venv check-zos-util
	@echo "Installing package in development mode..."
	$(VENV_ACTIVATE) python3 -m pip install -e .
	@echo ""
	@echo "Development installation complete!"
	@echo "Changes to source files will be immediately available."
	@echo "Test with: zos-ccsid-converter --help"

# Install in development mode with z/OS extras
install-dev-zos: venv install-zos-util
	@echo "Installing package in development mode with z/OS extras..."
	$(VENV_ACTIVATE) python3 -m pip install -e .[zos]
	@echo ""
	@echo "Development installation complete with z/OS support!"

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