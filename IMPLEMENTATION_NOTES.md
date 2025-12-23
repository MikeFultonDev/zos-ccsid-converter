# Implementation Notes: stat-based File Tag Query and chattr-based Tag Setting

## Overview

Updated the `zos_ccsid_converter` to use IBM zos-util's approach for both querying and setting file tags:
1. **Query**: stat-based approach (more efficient than fcntl)
2. **Setting**: __chattr() system call (eliminates subprocess overhead)

## Changes Made

### 1. Added stat-based File Tag Query

**New Structure:**
```python
class ft_tag(ctypes.Structure):
    """z/OS file tag structure (part of stat structure)"""
    _fields_ = [
        ("ft_ccsid", ctypes.c_ushort),    # File CCSID
        ("ft_txtflag", ctypes.c_uint),    # Text flag
    ]
```

**New Function:**
```python
def get_file_tag_stat(path: str, verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Get file tag information using os.stat() - z/OS specific.
    
    Similar to IBM zos-util's _get_tag_impl implementation:
    - Uses stat() system call to access st_tag structure
    - Returns (ccsid, txtflag) tuple
    - More efficient than fcntl or subprocess calls
    """
```

### 2. Updated get_file_encoding_fcntl()

The function now uses a two-tier approach:

1. **Primary Method (stat-based):**
   - Tries `get_file_tag_stat()` first
   - Direct access to `st.st_tag.ft_ccsid` and `st.st_tag.ft_txtflag`
   - More efficient, no file descriptor needed
   - Similar to IBM's zos-util implementation

2. **Fallback Method (fcntl-based):**
   - Uses `F_CONTROL_CVT` with `f_cnvrt` structure
   - Used when file descriptor is provided
   - Used when stat-based method is unavailable

### 3. Reference Implementation

Based on IBM zos-util's `_get_tag_impl`:
```c
static PyObject *_get_tag_impl(PyObject *self, PyObject *args) {
  struct stat st;
  char *path;
  int res;

  if (!PyArg_ParseTuple(args, "s", &path))
    return NULL;

  res = stat(path, &st);
  if (res < 0) {
    PyErr_SetFromErrno(PyExc_OSError);
    return NULL;
  }

  unsigned short ccsid = st.st_tag.ft_ccsid;
  int txtflag = st.st_tag.ft_txtflag;

  return Py_BuildValue("(HN)", ccsid, PyBool_FromLong((long)(txtflag)));
}
```

## Benefits

1. **Performance:**
   - stat() is faster than fcntl() for file tag queries
   - __chattr() eliminates subprocess overhead for tag setting
2. **Simplicity:**
   - Direct structure access, no complex fcntl marshalling
   - No subprocess spawning for tag operations
3. **Compatibility:**
   - Maintains backward compatibility with fcntl fallback for queries
   - Maintains chtag fallback for tag setting
4. **Industry Standard:** Follows IBM's zos-util reference implementation pattern

### 4. Added chattr-based File Tag Setting

**New Structure:**
```python
class attrib_t(ctypes.Structure):
    """z/OS attrib_t structure for __chattr() system call"""
    _fields_ = [
        ("att_filetagchg", ctypes.c_uint),   # Flag: 1 = change file tag
        ("att_filetag", ft_tag),              # File tag structure
    ]
```

**New Function:**
```python
def set_file_tag_chattr(path: str, ccsid: int, text_flag: bool = True,
                        verbose: bool = False) -> bool:
    """
    Set file CCSID using z/OS __chattr() system call.
    
    Similar to IBM zos-util's __setccsid implementation:
    - Uses __chattr() system call directly
    - No subprocess overhead
    - More efficient than chtag command
    """
```

**Updated Function:**
```python
def set_file_tag_fcntl(path: str, ccsid: int, text_flag: bool = True,
                      verbose: bool = False) -> bool:
    """
    Now tries __chattr() first, falls back to chtag command.
    """
```

## Important Notes

### Elimination of chtag Subprocess

The implementation now uses `__chattr()` system call for setting file tags:
- **Primary method**: `__chattr()` via ctypes (similar to IBM zos-util)
- **Fallback**: `chtag` command via subprocess (for compatibility)
- **Reason for change**: Eliminate subprocess overhead, follow IBM's reference implementation

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

## Future Enhancements

Potential improvements:
1. Investigate native Python extension for tag setting (avoiding subprocess)
2. Add performance benchmarks comparing stat vs fcntl methods
3. Consider caching stat results for frequently accessed files

## Implementation Details

### Query Method (stat-based)
```c
// IBM zos-util reference
res = stat(path, &st);
unsigned short ccsid = st.st_tag.ft_ccsid;
int txtflag = st.st_tag.ft_txtflag;
```

### Setting Method (chattr-based)
```c
// IBM zos-util reference
attrib_t attr;
memset(&attr, 0, sizeof(attr));
attr.att_filetagchg = 1;
attr.att_filetag.ft_ccsid = ccsid;
attr.att_filetag.ft_txtflag = txtflag;
res = __chattr(path, &attr, sizeof(attr));
```

## References

- IBM zos-util: https://github.com/IBM/zos-util
- IBM zos-util source: https://github.com/IBM/zos-util/blob/main/zos_util.c
- z/OS stat structure: https://www.ibm.com/docs/en/zos/3.2.0
- z/OS __chattr: https://www.ibm.com/docs/en/zos/3.2.0
- Original fcntl implementation: `converter.py` (previous version)