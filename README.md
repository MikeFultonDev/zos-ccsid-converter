# z/OS CCSID Converter

A Python package for working with z/OS file code pages (CCSID) and converting files between different encodings on z/OS systems using native fcntl system calls.

## Overview

This package provides a robust, high-performance solution for code page detection and file conversion on z/OS. It uses z/OS-specific `fcntl` system calls for file tagging instead of external commands, providing better performance, reliability, and direct access to file metadata. While currently focused on ASCII (ISO8859-1) and EBCDIC (IBM-1047) conversion, the architecture supports extension to additional code pages.

## Installation

### From Source

```bash
# Clone or download the package
cd zos_ccsid_converter

# Install the package
pip install .
```

### For Development

```bash
# Install in editable mode with development dependencies
pip install -e .
```

## Usage

### Command Line Interface

After installation, use the `zos-ccsid-converter` command:

```bash
# Convert a file to EBCDIC
zos-ccsid-converter input.txt output.txt

# Convert with verbose output
zos-ccsid-converter -v input.txt output.txt

# Show help
zos-ccsid-converter --help
```

### Python API

Import and use the package in your Python code:

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

## Features

**Core Capabilities:**
- Direct fcntl system calls for file tag detection (F_CONTROL_CVT with f_cnvrt structure)
- Direct fcntl system calls for file tag setting (F_SETTAG with attrib_t structure - may not be supported)
- Uses Python ctypes.BigEndianStructure for proper z/OS big-endian byte order
- Support for both regular files and streams/pipes
- Graceful handling of unconvertible characters
- Detailed conversion statistics
- No subprocess overhead
- Tested and verified on z/OS with 10/10 tests passing

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

**`convert_file(input_path: str, output_path: str, source_encoding: Optional[str] = None, target_encoding: str = 'IBM-1047') -> Dict`**
- Convert entire file from one encoding to another
- Auto-detects source encoding if not specified
- Returns dictionary with conversion statistics
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
- ISO8859-1 pipe conversion
- IBM-1047 pipe conversion
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

### z/OS fcntl Implementation

The package uses z/OS-specific fcntl system calls for file tagging:

**Encoding Detection:**
```python
# Uses F_CONTROL_CVT (13) with f_cnvrt structure
qcvt = f_cnvrt(3, 0, 0)  # cvtcmd=3 for query
    result = fcntl.fcntl(fd, F_CONTROL_CVT, qcvt)
    cvt_result = f_cnvrt.from_buffer_copy(result)
    
    # Get file CCSID directly
    ccsid = cvt_result.fccsid
```

**Advantages:**
- Direct system call (no subprocess)
- Uses ctypes.BigEndianStructure for proper z/OS big-endian byte order
- Lower overhead
- Works with file descriptors
- Native z/OS API usage
- Correct handling of z/OS-specific structures
- Tested and verified on z/OS

## z/OS fcntl File Tagging

### CCSID Mappings

| CCSID | Encoding | Description |
|-------|----------|-------------|
| 819   | ISO8859-1 | ASCII/Latin-1 |
| 1047  | IBM-1047 | EBCDIC |
| 0     | untagged | No tag set |

### fcntl Constants

```python
F_SETTAG = 12       # Set file tag information
F_CONTROL_CVT = 13  # Control conversion (query/set file CCSID)
```

**Note:** z/OS does not have F_GETTAG. Use F_CONTROL_CVT with the f_cnvrt structure to query file tags.

### File Tag Structures

**Important:** Both structures use `ctypes.BigEndianStructure` to match z/OS big-endian byte order.

#### f_cnvrt Structure (for F_CONTROL_CVT)

Used to query file conversion settings (CCSID detection):

```c
struct f_cnvrt {
    int cvtcmd;      // Command: 3=query, others for setting
    short pccsid;    // Process CCSID
    short fccsid;    // File CCSID (output when querying)
}
```

Total size: 8 bytes (4+2+2)

```python
# Python ctypes definition with big-endian byte order
class f_cnvrt(ctypes.BigEndianStructure):
    _fields_ = [
        ("cvtcmd", ctypes.c_int32),   # 4 bytes
        ("pccsid", ctypes.c_int16),   # 2 bytes
        ("fccsid", ctypes.c_int16),   # 2 bytes
    ]

# Usage example:
qcvt = f_cnvrt(3, 0, 0)  # cvtcmd=3 for query
result = fcntl.fcntl(fd, F_CONTROL_CVT, qcvt)
cvt_result = f_cnvrt.from_buffer_copy(result)
file_ccsid = cvt_result.fccsid  # Get file CCSID
```

**Status:** ✅ Fully working and tested on z/OS

#### attrib_t Structure (for F_SETTAG)

Used to set file tag information:

```c
typedef struct attrib_t {
    int att_filetagchg;           // File tag change flag (1=change)
    int att_rsvd1;                // Reserved (0)
    unsigned short att_txtflag;   // Text flag (1=text, 0=binary)
    unsigned short att_ccsid;     // CCSID
    int att_rsvd2[2];             // Reserved (0, 0)
}
```

Total size: 20 bytes (4+4+2+2+8)

```python
# Python ctypes definition with big-endian byte order
class attrib_t(ctypes.BigEndianStructure):
    _fields_ = [
        ("att_filetagchg", ctypes.c_int32),      # 4 bytes
        ("att_rsvd1", ctypes.c_int32),           # 4 bytes
        ("att_txtflag", ctypes.c_uint16),        # 2 bytes
        ("att_ccsid", ctypes.c_uint16),          # 2 bytes
        ("att_rsvd2", ctypes.c_int32 * 2),       # 8 bytes
    ]

# Usage example:
tag = attrib_t()
tag.att_filetagchg = 1
tag.att_ccsid = 819  # ISO8859-1
fcntl.fcntl(fd, F_SETTAG, bytes(tag))
```

**Status:** ⚠️ May not be supported through Python's fcntl on all z/OS systems

## Requirements

- Python 3.6 or higher
- z/OS operating system
- Access to z/OS fcntl system calls

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

```
======================================================================
EBCDIC Converter Test Suite
Testing: ebcdic_converter_fcntl.py
======================================================================

Running file conversion tests...
✓ PASS: ISO8859-1 file conversion
✓ PASS: IBM-1047 file handling
✓ PASS: Untagged file handling
✓ PASS: Empty file conversion
✓ PASS: Special characters conversion
✓ PASS: Large file conversion

Running pipe conversion tests...
✓ PASS: ISO8859-1 pipe conversion
✓ PASS: IBM-1047 pipe conversion

Running file tag operation tests...
✓ PASS: File tag operations

Running error handling tests...
✓ PASS: Nonexistent file error handling

======================================================================
TEST SUMMARY
======================================================================
Total tests: 10
Passed: 10
Failed: 0
======================================================================
```

## Key Behavioral Differences

### Untagged Files

**Original:** Treats untagged files as EBCDIC (copies as binary)
**New:** Same behavior - treats untagged files as IBM-1047

### Error Handling

**Original:** May fail silently or with generic errors
**New:** Returns detailed error information in stats dictionary

### Unconvertible Characters

**Original:** May fail on unconvertible characters
**New:** Uses `errors='replace'` to gracefully handle unconvertible characters, leaving them with their initial value or replacing with a substitute character

### Performance

**Original:** ~10-50ms overhead per file (subprocess spawn)
**New:** ~1-5ms overhead per file (direct system call)

## Integration with Existing Code

The new converter can be used as a drop-in replacement for the original `convert_to_ebcdic` function:

```python
# Original
from batchtsocmd import convert_to_ebcdic
success = convert_to_ebcdic(input_path, output_path, verbose=True)

# New (with enhanced return value)
from ebcdic_converter_fcntl import convert_to_ebcdic_fcntl
stats = convert_to_ebcdic_fcntl(input_path, output_path, verbose=True)
success = stats['success']
```

## Technical Details

### File Tag Detection Algorithm

1. Open file (or use provided file descriptor)
2. Prepare `attrib_t` structure initialized with zeros
3. Call `fcntl(fd, F_GETTAG, buffer)`
4. Unpack result to extract `att_ccsid` and `att_txtflag`
5. Map CCSID to encoding name

### File Tag Setting Algorithm

1. Open file with read/write access
2. Prepare `attrib_t` structure:
   - Set `att_filetagchg = 1` (indicate change)
   - Set `att_txtflag = 1` for text, `0` for binary
   - Set `att_ccsid` to desired CCSID
   - Set reserved fields to 0
3. Call `fcntl(fd, F_SETTAG, buffer)`
4. Close file

### Conversion Algorithm

For **ISO8859-1 → IBM-1047**:
1. Detect encoding using fcntl
2. Read file as ISO8859-1 text with `errors='replace'`
3. Write file as IBM-1047 text with `errors='replace'`
4. Tag output file as IBM-1047 using fcntl

For **IBM-1047 or untagged**:
1. Detect encoding using fcntl
2. Copy file as binary (no conversion)
3. Tag output file as IBM-1047 if untagged

## Troubleshooting

### "fcntl failed" Error

If fcntl operations fail, the converter falls back to treating files as untagged. This can happen if:
- File system doesn't support tagging
- Insufficient permissions
- File is on a non-z/OS file system

### Pipe Conversion Issues

Named pipes (FIFOs) cannot be tagged with fcntl. Use `convert_stream_to_ebcdic()` for pipes and tag the output file after conversion.

### Character Conversion Errors

The converter uses `errors='replace'` to handle unconvertible characters. Characters that cannot be converted are replaced with a substitute character (usually '?'). Check the `errors` field in the stats dictionary to see if any errors occurred.

## References

- [IBM z/OS fcntl Documentation](https://www.ibm.com/docs/en/zos/3.2.0?topic=SSLTBW_3.2.0/com.ibm.zos.v3r2.bpxbd00/rtfcndesc.html)
- [z/OS File Tagging](https://www.ibm.com/docs/en/zos/3.2.0?topic=files-tagging)
- [Python fcntl Module](https://docs.python.org/3/library/fcntl.html)

## License

This code is part of the CICS Banking Sample Application and follows the same license terms.

## Author

Created as an enhancement to the CICS Banking Sample Application build tools.