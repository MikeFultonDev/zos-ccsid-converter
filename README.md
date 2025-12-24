# z/OS CCSID Converter

A Python package for working with z/OS file code pages (CCSID) and converting files between different encodings on z/OS systems.

## Overview

This package provides a robust, high-performance solution for code page detection and file conversion on z/OS. It uses IBM's zos-util C extension module exclusively for all file tag operations. File tag detection uses `zos_util.get_tag_info()` for all file types (regular files, named pipes, special files like /dev/stdin). File tag setting uses `zos_util.chtag()` exclusively.

**Self-Contained Package**: This package bundles the zos_util shared library, making it completely self-contained with no external dependencies. When you install from PyPI, everything you need is included in the package.

While currently focused on ASCII (ISO8859-1) and EBCDIC (IBM-1047) conversion, the architecture supports extension to additional code pages.

## Installation

### From PyPI (Recommended)

```bash
pip install zos-ccsid-converter
```

No additional dependencies or prerequisites required - the package is completely self-contained!

### From Source

On z/OS, the build process automatically bundles the zos-util shared library into the package.

```bash
# Clone or download the package
cd zos_ccsid_converter

# Build and install (zos-util installed automatically on z/OS)
make install

# Or use pip directly
pip install .
```

### For Development

```bash
# Install in editable mode (zos-util installed automatically on z/OS)
make install-dev

# Or use pip directly
pip install -e .
```

### Building from Source

The package bundles the zos-util shared library during the build process:

```bash
make build
```

This will:
- Clone and build zos-util from https://github.com/IBM/zos-util.git
- Bundle the compiled shared library into the package
- Create wheel and source distributions

See [BUNDLING.md](BUNDLING.md) for detailed information about the bundling process.

### Running Without Installation (Development)

If you want to run the CLI directly from your cloned git directory without installing:

```bash
# From the project root directory
python3 -m zos_ccsid_converter.cli --help

# Examples:
python3 -m zos_ccsid_converter.cli input.txt output.txt
python3 -m zos_ccsid_converter.cli --info input.txt
python3 -m zos_ccsid_converter.cli --version
cat input.txt | python3 -m zos_ccsid_converter.cli --info --stdin
```

Alternatively, you can use the Makefile for development setup:

```bash
# Create virtual environment and install in development mode
make install-dev

# Then use the CLI
zos-ccsid-converter --help
```

## Usage

### Command Line Interface

After installation, use the `zos-ccsid-converter` command:

```bash
# Convert a file to EBCDIC
zos-ccsid-converter input.txt output.txt

# Convert with verbose output
zos-ccsid-converter -v input.txt output.txt

# Get file encoding information
zos-ccsid-converter --info input.txt

# Convert from stdin to file
cat input.txt | zos-ccsid-converter --stdin output.txt

# Get encoding info from stdin (no output file needed)
cat input.txt | zos-ccsid-converter --info --stdin

# Show version
zos-ccsid-converter --version

# Show help
zos-ccsid-converter --help
```

### Python API

Import and use the package in your Python code:

```python
from zos_ccsid_converter import CodePageService, __version__

# Get package version
print(f"Version: {__version__}")

# Initialize service
service = CodePageService()

# Detect code page
ccsid = service.get_ccsid('/path/to/file')
encoding = service.get_encoding_name('/path/to/file')

# Check file type
if service.is_ascii('/path/to/file'):
    print("File is ASCII")

# Convert data
ebcdic_bytes = service.convert_to_ebcdic(ascii_bytes)
ascii_bytes = service.convert_to_ascii(ebcdic_bytes)

# Convert files or pipes
stats = service.convert_input('/input.txt', '/output.txt')

# Also available: convert_file() for backward compatibility
stats = service.convert_file('/input.txt', '/output.txt')
```

## Features

**Core Capabilities:**
- Uses IBM's zos_util C extension module exclusively for all file tag operations
- File tag detection via `zos_util.get_tag_info()` for all file types (regular files, named pipes, special files)
- File tag setting via `zos_util.chtag()` for reliable tag operations
- Support for regular files, named pipes (FIFOs), and streams
- Graceful handling of unconvertible characters
- Detailed conversion statistics
- No subprocess overhead - all operations use native C extensions
- Self-contained package with bundled zos_util shared library
- Tested and verified on z/OS with 11/11 tests passing

## API Reference

### CodePageService Class

The main service class for code page operations:

```python
from zos_ccsid_converter import CodePageService

# Initialize service
service = CodePageService()

# Detect code page
ccsid = service.get_ccsid('/path/to/file')
encoding = service.get_encoding_name('/path/to/file')

# Check file type
if service.is_ascii('/path/to/file'):
    print("File is ASCII")

# Convert data
ebcdic_bytes = service.convert_to_ebcdic(ascii_bytes)
ascii_bytes = service.convert_to_ascii(ebcdic_bytes)

# Convert files
stats = service.convert_file('/input.txt', '/output.txt')
```


#### Initialization
```python
service = CodePageService(verbose=False)
```

#### Code Page Detection Methods

**`get_ccsid(path: str) -> int`**
- Returns CCSID value (819=ISO8859-1, 1047=IBM-1047, 0=untagged)
- Example: `ccsid = service.get_ccsid('/tmp/file.txt')`

**`get_encoding_name(path: str) -> str`**
- Returns encoding name: 'ISO8859-1', 'IBM-1047', or 'untagged'
- Example: `encoding = service.get_encoding_name('/tmp/file.txt')`

**`is_ascii(path: str) -> bool`**
- Returns True if file is ASCII/ISO8859-1
- Example: `if service.is_ascii('/tmp/file.txt'): ...`

**`is_ebcdic(path: str) -> bool`**
- Returns True if file is EBCDIC/IBM-1047
- Example: `if service.is_ebcdic('/tmp/file.txt'): ...`

**`is_untagged(path: str) -> bool`**
- Returns True if file is untagged
- Example: `if service.is_untagged('/tmp/file.txt'): ...`

#### Data Conversion Methods

**`convert_bytes(data: bytes, source_encoding: str, target_encoding: str) -> bytes`**
- Convert bytes from one encoding to another
- Example: `ebcdic = service.convert_bytes(ascii_data, 'ISO8859-1', 'IBM-1047')`

**`convert_to_ebcdic(data: bytes, source_encoding: str = 'ISO8859-1') -> bytes`**
- Convert bytes to EBCDIC (IBM-1047)
- Example: `ebcdic = service.convert_to_ebcdic(b"Hello World")`

**`convert_to_ascii(data: bytes, source_encoding: str = 'IBM-1047') -> bytes`**
- Convert bytes to ASCII (ISO8859-1)
- Example: `ascii = service.convert_to_ascii(ebcdic_data)`

**`convert_input(input_path: str, output_path: str, source_encoding: Optional[str] = None, target_encoding: str = 'IBM-1047') -> Dict`**
- Convert file or named pipe from one encoding to another
- Automatically detects whether input is a regular file or named pipe (FIFO)
- Auto-detects source encoding for files; defaults to ISO8859-1 for pipes
- Returns dictionary with conversion statistics including 'input_type' field
- Example:
  ```python
  # Works with both files and pipes
  stats = service.convert_input('/input.txt', '/output.txt')
  stats = service.convert_input('/tmp/mypipe', '/output.txt', source_encoding='ISO8859-1')
  if stats['success']:
      print(f"Converted {stats['bytes_read']} bytes from {stats['input_type']}")
  ```

**`convert_file(input_path: str, output_path: str, source_encoding: Optional[str] = None, target_encoding: str = 'IBM-1047') -> Dict`**
- Convert regular file from one encoding to another
- Auto-detects source encoding if not specified
- Returns dictionary with conversion statistics
- Note: Use `convert_input()` for unified file/pipe handling
- Example:
  ```python
  stats = service.convert_file('/input.txt', '/output.txt')
  if stats['success']:
      print(f"Converted {stats['bytes_read']} bytes")
  ```

### Convenience Functions

```python
from zos_ccsid_converter import detect_code_page, detect_encoding, convert_data

# Detect code page without instantiating service
ccsid = detect_code_page('/tmp/file.txt')

# Detect encoding name
encoding = detect_encoding('/tmp/file.txt')

# Convert data
ebcdic = convert_data(b"Hello", 'ISO8859-1', 'IBM-1047')
```

## Package Structure

```
zos_ccsid_converter/
├── setup.py                    # Package configuration
├── pyproject.toml              # Modern Python packaging metadata
├── MANIFEST.in                 # File inclusion rules
├── LICENSE                     # Apache 2.0 license
├── README.md                   # This file
├── zos_ccsid_converter/       # Main package
│   ├── __init__.py            # Package exports
│   ├── converter.py           # Core conversion logic
│   └── cli.py                 # Command-line interface
├── tests/                      # Test suite
│   └── test_ebcdic_converter.py
└── examples/                   # Usage examples
    └── example_service_usage.py
```

## Building and Distribution

### Using the Makefile (Recommended)

The package includes a Makefile for easy building, testing, and publishing:

```bash
# Show all available targets
make help

# Build the package
make build

# Run tests
make test

# Build and test
make all

# Install locally
make install

# Install in development mode
make install-dev

# Publish to TestPyPI (for testing)
make publish-test

# Publish to PyPI (production)
make publish
```

### Manual Build

```bash
# Install build tools
pip install build

# Build distribution packages
python -m build

# This creates:
# - dist/zos_ccsid_converter-1.0.0-py3-none-any.whl
# - dist/zos_ccsid_converter-1.0.0.tar.gz
```

### Install from Built Package

```bash
# Install from wheel
pip install dist/zos_ccsid_converter-1.0.0-py3-none-any.whl

# Or install from source distribution
pip install dist/zos_ccsid_converter-1.0.0.tar.gz
```

## Testing

Run the comprehensive test suite:

```bash
# From package directory
cd tests
python3 test_ebcdic_converter.py

# With verbose output
python3 test_ebcdic_converter.py --verbose

# Keep test files for inspection
python3 test_ebcdic_converter.py --keep-files
```

**Test Coverage:**
- ISO8859-1 encoded file conversion
- IBM-1047 encoded file handling (no conversion)
- Untagged file handling (treated as EBCDIC)
- Empty file conversion
- Special characters conversion
- Large file conversion (~100KB)
- ISO8859-1 pipe conversion (stream API)
- IBM-1047 pipe conversion (stream API)
- CodePageService.convert_input() with ISO8859-1 pipe
- File tag operations (get/set)
- Error handling (nonexistent files)

## Examples

See `examples/example_service_usage.py` for complete working examples:

1. Detecting code pages
2. Checking file types
3. Converting bytes
4. Converting files
5. Auto-detection and conversion
6. Batch processing multiple files
7. Integration patterns for existing code

## Technical Details

### z/OS File Tagging Implementation

The package uses IBM's zos_util C extension module exclusively for all file tag operations:

**Encoding Detection:**
```python
# Uses zos_util.get_tag_info() for all file types
import zos_util

tag_info = zos_util.get_tag_info(path)
ccsid = tag_info['ccsid']
is_text = tag_info['text']
```

**File Tag Setting:**
```python
# Uses zos_util.chtag() for reliable tag setting
import zos_util

# Set text file tag
zos_util.chtag(path, text=True, ccsid=1047)

# Set binary file tag
zos_util.chtag(path, text=False)
```

**Advantages:**
- Native C extension for optimal performance
- No subprocess overhead
- Works with all file types (regular files, pipes, special files like /dev/stdin)
- Reliable and consistent tag operations
- Self-contained - bundled shared library included in package
- Tested and verified on z/OS

## CCSID Mappings

| CCSID | Encoding | Description |
|-------|----------|-------------|
| 819   | ISO8859-1 | ASCII/Latin-1 |
| 1047  | IBM-1047 | EBCDIC |
| 0     | untagged | No tag set |

## Requirements

- Python 3.6 or higher
- z/OS operating system

## License

Apache License 2.0 - See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting changes.

## Support

For issues or questions, please refer to the project documentation or contact the maintainers.
```
File: myfile.txt
  CCSID: 819
  Encoding: ISO8859-1
  Text: True
```

### Convert from stdin

```bash
# Pipe data through converter
cat input.txt | ./ebcdic_converter_fcntl.py --stdin output.txt
```

### Python API Usage

```python
from ebcdic_converter_fcntl import convert_to_ebcdic_fcntl

# Convert a file
stats = convert_to_ebcdic_fcntl('input.txt', 'output.txt', verbose=True)

if stats['success']:
    print(f"Converted {stats['bytes_read']} bytes")
    print(f"Encoding detected: {stats['encoding_detected']}")
    print(f"Conversion needed: {stats['conversion_needed']}")
else:
    print(f"Error: {stats['error_message']}")
```

### Stream Conversion

```python
from ebcdic_converter_fcntl import convert_stream_to_ebcdic
import sys

# Convert stdin to file
with open('output.txt', 'wb') as f_out:
    stats = convert_stream_to_ebcdic(
        sys.stdin.buffer,
        f_out,
        source_encoding='iso8859-1'
    )
```

## Running Tests

### Run All Tests

```bash
./test_ebcdic_converter.py
```

### Run with Verbose Output

```bash
./test_ebcdic_converter.py --verbose
```

### Keep Test Files for Inspection

```bash
./test_ebcdic_converter.py --keep-files
```

### Expected Output

All tests should pass when run on z/OS. The test suite validates file conversion, pipe handling, tag operations, and error handling.

## Behavior

### Untagged Files

Treats untagged files as IBM-1047 (EBCDIC) and copies them as binary without conversion.

### Error Handling

Returns detailed error information in the stats dictionary, including error messages and context.

### Unconvertible Characters

Uses `errors='replace'` to gracefully handle unconvertible characters, replacing them with a substitute character rather than failing.

### Performance

Direct C extension calls provide optimal performance with minimal overhead.

## Technical Details

### File Tag Detection Algorithm

1. Call `zos_util.get_tag_info(path)` to get file tag information
2. Extract CCSID and text flag from returned dictionary
3. Map CCSID to encoding name (ISO8859-1, IBM-1047, or untagged)

### File Tag Setting Algorithm

1. Call `zos_util.chtag(path, text=True/False, ccsid=value)` to set file tag
2. zos_util handles all low-level system calls internally

### Conversion Algorithm

For **ISO8859-1 → IBM-1047**:
1. Detect encoding using `zos_util.get_tag_info()`
2. Read file as ISO8859-1 text with `errors='replace'`
3. Write file as IBM-1047 text with `errors='replace'`
4. Tag output file as IBM-1047 using `zos_util.chtag()`

For **IBM-1047 or untagged**:
1. Detect encoding using `zos_util.get_tag_info()`
2. Copy file as binary (no conversion)
3. Tag output file as IBM-1047 if untagged using `zos_util.chtag()`

## Troubleshooting

### File Tag Operations

The package uses zos_util for all file tag operations. If tag operations fail, this can happen if:
- File system doesn't support tagging
- Insufficient permissions
- File is on a non-z/OS file system

### Pipe Conversion

Named pipes (FIFOs) and special files like /dev/stdin are fully supported. The `convert_input()` method automatically detects pipes and uses the appropriate stream conversion method, then tags the output file.

Example:
```python
# Automatic pipe detection and conversion
stats = service.convert_input('/tmp/mypipe', '/output.txt', source_encoding='ISO8859-1')

# Or use stream API directly
with open('/tmp/mypipe', 'rb') as pipe_in:
    with open('/output.txt', 'wb') as file_out:
        stats = convert_stream_to_ebcdic(pipe_in, file_out, source_encoding='iso8859-1')
```

### Character Conversion Errors

The converter uses `errors='replace'` to handle unconvertible characters. Characters that cannot be converted are replaced with a substitute character (usually '?'). Check the `errors` field in the stats dictionary to see if any errors occurred.

## References

- [IBM zos-util GitHub Repository](https://github.com/IBM/zos-util)
- [z/OS File Tagging](https://www.ibm.com/docs/en/zos/3.2.0?topic=files-tagging)
- [Python Packaging Guide](https://packaging.python.org/)

## License

Apache License Version 2.0

## Author

Mike Fulton