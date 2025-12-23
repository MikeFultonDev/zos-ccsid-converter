# Z-Python Mode Tips and Techniques

## Working with z/OS System Headers

When you need to examine z/OS system header files (like `/usr/include/sys/stat.h`), follow this process:

### Step 1: Convert EBCDIC to ASCII on z/OS

z/OS header files are stored in EBCDIC (IBM-1047) encoding. Convert them to ASCII on z/OS first:

```bash
ssh fultonm_9_47_93_202 "iconv -f IBM-1047 -t ISO8859-1 /usr/include/sys/stat.h > /tmp/stat_ascii.h && echo 'Converted successfully'"
```

**Why convert on z/OS?**
- The `iconv` on z/OS has proper IBM-1047 support
- macOS/Linux `iconv` may not have IBM-1047 codec
- Python on macOS doesn't have `ibm1047` codec by default

### Step 2: Download the Converted File

```bash
scp fultonm_9_47_93_202:/tmp/stat_ascii.h /tmp/zos_stat_ascii.h
```

### Step 3: Examine the File

```bash
grep -A 80 "struct f_attributes" /tmp/zos_stat_ascii.h
```

## Common z/OS System Headers

Useful headers for z/OS development:

- `/usr/include/sys/stat.h` - File attributes, stat structures, attrib_t
- `/usr/include/sys/types.h` - Basic system types
- `/usr/include/fcntl.h` - File control operations
- `/usr/include/unistd.h` - POSIX API definitions

## z/OS Connection Details

- **Host**: `fultonm_9_47_93_202`
- **System headers**: `/usr/include/`
- **Encoding**: IBM-1047 (EBCDIC)
- **Target encoding**: ISO8859-1 (ASCII)

## Example: Getting attrib_t Structure

```bash
# Step 1: Convert on z/OS
ssh fultonm_9_47_93_202 "iconv -f IBM-1047 -t ISO8859-1 /usr/include/sys/stat.h > /tmp/stat_ascii.h"

# Step 2: Download
scp fultonm_9_47_93_202:/tmp/stat_ascii.h /tmp/zos_stat_ascii.h

# Step 3: Search for structure
grep -A 80 "struct f_attributes" /tmp/zos_stat_ascii.h
```

## Working with ctypes Structures

When creating ctypes structures from z/OS headers:

1. **Bit fields**: Use `c_uint32` for packed bit fields, create properties for access
2. **Byte order**: z/OS is big-endian, use `ctypes.BigEndianStructure` if needed
3. **Alignment**: Pay attention to structure padding
4. **Eye-catchers**: Initialize strings like "ATT " properly

Example:
```python
class file_tag(ctypes.Structure):
    _fields_ = [
        ("ft_ccsid", ctypes.c_ushort),     # 2 bytes
        ("ft_flags", ctypes.c_uint32),     # 4 bytes with bit fields
    ]
    
    @property
    def ft_txtflag(self):
        return (self.ft_flags >> 31) & 1
```

## Verifying Structures

Always verify your ctypes structures match the actual z/OS headers:

1. Download the header file
2. Compare field names, types, and sizes
3. Test on actual z/OS system
4. Check alignment and padding

## References

- IBM z/OS documentation: https://www.ibm.com/docs/en/zos
- IBM zos-util reference: https://github.com/IBM/zos-util
- z/OS UNIX System Services: https://www.ibm.com/docs/en/zos/3.2.0?topic=services-zos-unix-system