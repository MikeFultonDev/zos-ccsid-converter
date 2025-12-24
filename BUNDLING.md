# Bundling zos-util with zos-ccsid-converter

## Overview

This package is self-contained and bundles the `zos_util` shared library, eliminating the need for users to separately install `zos-util` as a prerequisite.

## Build Process

When building the package on z/OS, the build process automatically:

1. Clones the IBM zos-util repository (if not already present)
2. Compiles the zos_util C extension using the available C compiler (clang, xlc, c89, or c99)
3. Copies the compiled shared library (.so file) into `zos_ccsid_converter/lib/`
4. Includes the shared library in the wheel and source distributions

## Building the Package

To build a self-contained package on z/OS:

```bash
make build
```

This will:
- Create a virtual environment
- Bundle the zos_util shared library
- Build wheel and source distributions in the `dist/` directory

## How It Works

The `converter.py` module includes a `_load_bundled_zos_util()` function that:

1. First attempts to import `zos_util` if it's already installed system-wide
2. If not found, looks for the bundled shared library in `zos_ccsid_converter/lib/`
3. Dynamically loads the bundled library using Python's `importlib` module
4. Falls back to an error message if on z/OS and the library cannot be loaded

## Package Contents

The distributed package includes:

```
zos_ccsid_converter/
├── __init__.py
├── cli.py
├── converter.py
└── lib/
    └── zos_util.*.so  (bundled shared library)
```

## Installation

Users can install the package directly without any prerequisites:

```bash
pip install zos-ccsid-converter
```

No separate installation of zos-util is required.

## Development vs. Production

- **Development**: During development, you may have zos-util installed separately. The code will use the system-installed version if available.
- **Production**: When installed from PyPI, the package uses the bundled shared library.

## Makefile Targets

- `make bundle-zos-util`: Build and bundle the zos_util shared library
- `make build`: Build the complete package with bundled library
- `make install-zos-util`: Install zos-util system-wide (for development)

## Notes

- The bundled library is platform-specific (z/OS only)
- The package must be built on z/OS to include the correct shared library
- The `lib/` directory is excluded from git but included in distributions
- The shared library is automatically loaded when the module is imported