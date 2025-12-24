# Testing the Bundled Package

## Overview

The package has been configured to bundle the zos_util shared library, making it self-contained. Here's how to test it.

## Testing Steps on z/OS

### 1. Build the Package

```bash
make build
```

This will:
- Clone zos-util (if not present in `../zos-util`)
- Compile the zos_util shared library
- Copy the .so file to `zos_ccsid_converter/lib/`
- Build the wheel and source distributions

### 2. Verify the Bundle

Check that the shared library was bundled:

```bash
# Check if the lib directory was created
ls -la zos_ccsid_converter/lib/

# Verify the wheel contains the shared library
unzip -l dist/zos_ccsid_converter-*.whl | grep "\.so"
```

You should see the zos_util shared library (.so file) in both locations.

### 3. Test Installation in a Clean Environment

Create a fresh virtual environment and install from the wheel:

```bash
# Create a new test environment
python3 -m venv test_env
source test_env/bin/activate

# Install from the built wheel
pip install dist/zos_ccsid_converter-*.whl

# Test that it works
zos-ccsid-converter --help

# Test the Python API
python3 -c "from zos_ccsid_converter import CodePageService; print('Import successful')"
```

### 4. Test Functionality

```bash
# Create a test file
echo "Hello World" > test_ascii.txt

# Convert it
zos-ccsid-converter test_ascii.txt test_ebcdic.txt

# Verify the conversion worked
ls -l test_ebcdic.txt
```

### 5. Test the Service API

```python
from zos_ccsid_converter import CodePageService

service = CodePageService(verbose=True)

# Test code page detection
ccsid = service.get_ccsid('test_ascii.txt')
print(f"CCSID: {ccsid}")

# Test conversion
service.convert_file('test_ascii.txt', 'output.txt')
```

## Expected Results

1. **Build**: Should complete without errors and create `zos_ccsid_converter/lib/*.so`
2. **Wheel contents**: Should include `zos_ccsid_converter/lib/*.so`
3. **Installation**: Should work without requiring separate zos-util installation
4. **Import**: Should successfully import and load the bundled library
5. **Functionality**: All conversion operations should work correctly

## Troubleshooting

### Library Not Found

If you see "zos_util module could not be loaded":

1. Check that `zos_ccsid_converter/lib/` exists and contains a .so file
2. Verify the wheel was built correctly: `unzip -l dist/*.whl | grep lib`
3. Rebuild with: `make clean && make build`

### Import Errors

If you see import errors:

1. Ensure you're on z/OS (the package only works on z/OS)
2. Check Python version (requires Python 3.12+)
3. Verify the shared library is compatible with your Python version

### Build Errors

If the build fails:

1. Ensure a C compiler is available (clang, xlc, c89, or c99)
2. Check that zos-util can be cloned from GitHub
3. Review the build output for specific errors

## Cleanup

After testing:

```bash
# Deactivate and remove test environment
deactivate
rm -rf test_env

# Clean build artifacts
make clean
```

## Next Steps

Once testing is successful:

1. Update version number in `setup.py` and `pyproject.toml`
2. Build final package: `make build`
3. Publish to PyPI: `make publish`