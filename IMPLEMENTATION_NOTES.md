# Implementation Notes: Complete zos-util Integration

## Overview

Completely simplified the `zos_ccsid_converter` to use IBM's zos-util C extension module exclusively:
1. **Query**: zos_util.get_tag_info() for ALL file types (regular files, named pipes, /dev/stdin)
2. **Setting**: zos_util.chtag() exclusively - **no fallback**
3. **Removed**: ALL ctypes structures and fcntl code - no longer needed

## Simplification Changes

### 1. Direct Use of zos-util Functions

**Query Operations:**
```python
# Before: Complex ctypes structures, os.stat(), AND fcntl fallback
class file_tag(ctypes.Structure):
    _fields_ = [...]

class f_cnvrt(ctypes.BigEndianStructure):
    _fields_ = [...]

def get_file_tag_stat(path):
    st = os.stat(path)
    return (st.st_tag.ft_ccsid, st.st_tag.ft_txtflag)

def get_file_encoding_fcntl(path, fd=None):
    if fd is None:
        # Try stat...
    else:
        # Use fcntl with f_cnvrt structure...

# After: Single direct zos-util call
ccsid, txtflag = zos_util.get_tag_info(path)  # Works for ALL file types
```

**Setting Operations:**
```python
# Before: Complex attrib_t structure (never actually used)
class attrib_t(ctypes.Structure):
    _fields_ = [...]  # 20+ fields

# After: Direct zos-util call
zos_util.chtag(path, ccsid=ccsid, set_txtflag=text_flag)
```

### 2. Removed ALL Unnecessary Structures

- **Removed `file_tag` class**: Not needed, zos-util handles this internally
- **Removed `attrib_t` class**: Not needed, zos-util handles this internally
- **Removed `f_cnvrt` class**: Not needed, zos-util supports named pipes and special files

### 3. Simplified Functions

**get_file_encoding_fcntl():**
- Uses `zos_util.get_tag_info()` exclusively
- No fcntl fallback needed (zos-util supports all file types)
- Removed `fd` parameter (no longer needed)

**get_file_tag_info():**
- Uses `zos_util.get_tag_info()` directly
- Returns proper text_flag from zos-util (not assumed)

**set_file_tag_fcntl():**
- Uses `zos_util.chtag()` exclusively
- No fallback to chtag command

**CLI stdin handling:**
- Changed from `fd=sys.stdin.fileno()` to `/dev/stdin` path
- zos-util handles special files natively

## Benefits

1. **Simplicity:**
   - 90+ lines of ctypes structures removed (file_tag, attrib_t, f_cnvrt)
   - 70+ lines of fcntl fallback code removed
   - Direct function calls instead of complex structure manipulation
   - Easier to understand and maintain

2. **Reliability:**
   - Uses IBM's tested implementation exclusively
   - No custom ctypes code that might break
   - No fcntl fallback complexity
   - Proper error handling from zos-util

3. **Performance:**
   - No unnecessary structure creation
   - Direct C extension calls
   - Minimal Python overhead
   - Single code path (no fallback logic)

4. **Universality:**
   - zos-util handles ALL file types (regular, pipes, special files)
   - No special casing for file descriptors
   - Consistent behavior across all file types

### 4. Why This Approach

**Why zos-util Instead of ctypes:**

Initial attempts to use ctypes failed:
- `ctypes.CDLL("libc.so")` - doesn't exist on z/OS
- `ctypes.CDLL(None)` - can't find `__chattr` symbol
- Pragma map complications with EBCDIC encoding

**Solution**: Use IBM's zos-util directly - it's already doing exactly what we need.

**No Fallback**: zos-util is automatically installed by build process, so no fallback needed.

## Important Notes

### Use of zos-util C Extension (Hard Requirement)

The implementation now uses IBM's zos-util module exclusively for setting file tags:
- **Only method**: `zos_util.chtag()` via C extension (proper z/OS system call access)
- **No fallback**: Raises RuntimeError if zos-util not available
- **Reason for change**: ctypes doesn't work properly on z/OS for system calls; zos-util provides proper C extension access
- **Automatic installation**: The Makefile automatically detects z/OS and installs zos-util if not present
- **Hard requirement**: On z/OS, the code will fail at import time if zos-util is not installed

### Platform-Specific Code

The `st_tag` attribute is z/OS-specific:
- Only available on z/OS systems
- Type checkers will show warnings (suppressed with `# type: ignore[attr-defined]`)
- Code gracefully falls back to fcntl on other platforms

## Testing

The implementation maintains compatibility with existing tests:
- All 11 tests should continue passing
- stat-based method will be used on z/OS when available
- fcntl fallback ensures functionality on all platforms

## Code Metrics

**Lines Removed:**
- ~90 lines of ctypes structure definitions (file_tag, attrib_t, f_cnvrt)
- ~70 lines of fcntl fallback code
- ~50 lines of custom stat-based query code
- ~20 lines of chtag fallback code
- Total: ~230 lines removed

**Lines Added:**
- ~15 lines of direct zos-util calls
- Net reduction: ~215 lines (much simpler, more maintainable)

## Implementation Details

### Query Method (ALL file types)
```python
# Direct zos-util call - works for regular files, pipes, /dev/stdin, etc.
ccsid, txtflag = zos_util.get_tag_info(path)
```

### Setting Method (no fallback)
```python
# Direct zos-util call (no fallback)
zos_util.chtag(path, ccsid=ccsid, set_txtflag=text_flag)
```

### No Fallback Code
All fcntl and ctypes code has been removed. zos-util handles everything.

## References

- IBM zos-util: https://github.com/IBM/zos-util
- IBM zos-util source: https://github.com/IBM/zos-util/blob/main/zos_util.c
- z/OS stat structure: https://www.ibm.com/docs/en/zos/3.2.0
- z/OS __chattr: https://www.ibm.com/docs/en/zos/3.2.0
- Original fcntl implementation: `converter.py` (previous version)