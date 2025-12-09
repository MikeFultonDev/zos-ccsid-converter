# Developer Usage Issue Analysis

## Problem Summary

The developer's test in `batchtsocmd/tests/test_dataset_operations.py` is failing because they are writing to named pipes in **text mode with encoding**, but `zos-ccsid-converter` expects **binary mode** for pipe operations.

## Root Cause

### Developer's Code (INCORRECT)

In `test_dataset_operations.py` lines 87-92:

```python
def write_pipe(pipe_path, content, encoding):
    try:
        with open(pipe_path, 'w', encoding=encoding) as f:  # TEXT MODE ❌
            f.write(content)
```

And lines 94-99:

```python
def read_pipe(pipe_path, output_list):
    try:
        with open(pipe_path, 'r', encoding='ibm1047') as f:  # TEXT MODE ❌
            output_list.append(f.read())
```

### The Problem

1. **Text Mode Writing**: When writing in text mode with `encoding='ibm1047'`, Python automatically encodes the string to EBCDIC bytes
2. **Text Mode Reading**: When reading in text mode with `encoding='ibm1047'`, Python automatically decodes EBCDIC bytes to string
3. **Double Conversion**: When `CodePageService.convert_input()` is used with a pipe, it expects **binary data** and will attempt to decode/encode again, causing corruption

### Why Our Tests Pass

Our tests in `tests/test_ebcdic_converter.py` use the **correct pattern**:

```python
def pipe_writer(pipe_path: str, content: str, encoding: str, delay: float = 0.1):
    """Helper function to write to a pipe in a separate thread"""
    time.sleep(delay)
    try:
        with open(pipe_path, 'wb') as pipe:  # BINARY MODE ✓
            pipe.write(content.encode(encoding))  # Pre-encode to bytes ✓
```

And when reading:

```python
with open(pipe_path, 'rb') as pipe_in:  # BINARY MODE ✓
    with open(output_file, 'wb') as file_out:
        stats = convert_stream_to_ebcdic(
            pipe_in, file_out,
            source_encoding='iso8859-1',
            verbose=env.verbose
        )
```

## Solution

The developer needs to modify their pipe I/O to use **binary mode**:

### Fix for Writing to Pipes

**Before (INCORRECT):**
```python
def write_pipe(pipe_path, content, encoding):
    try:
        with open(pipe_path, 'w', encoding=encoding) as f:
            f.write(content)
```

**After (CORRECT):**
```python
def write_pipe(pipe_path, content, encoding):
    try:
        with open(pipe_path, 'wb') as f:  # Binary mode
            f.write(content.encode(encoding))  # Encode to bytes first
```

### Fix for Reading from Pipes

**Before (INCORRECT):**
```python
def read_pipe(pipe_path, output_list):
    try:
        with open(pipe_path, 'r', encoding='ibm1047') as f:
            output_list.append(f.read())
```

**After (CORRECT):**
```python
def read_pipe(pipe_path, output_list):
    try:
        with open(pipe_path, 'rb') as f:  # Binary mode
            data = f.read()
            # Decode to string if needed
            output_list.append(data.decode('ibm1047'))
```

## Why This Matters

### Text Mode vs Binary Mode with Pipes

| Aspect | Text Mode | Binary Mode |
|--------|-----------|-------------|
| Encoding | Automatic by Python | Manual by developer |
| Data Type | `str` | `bytes` |
| Conversion | Implicit | Explicit |
| Control | Less control | Full control |
| Compatibility | May cause double-conversion | Works with binary APIs |

### The Double-Conversion Problem

When using text mode with `zos-ccsid-converter`:

1. Developer writes string → Python encodes to EBCDIC → Pipe contains EBCDIC bytes
2. `CodePageService` reads EBCDIC bytes → Decodes as EBCDIC → Encodes to EBCDIC again
3. Result: Corrupted data (double-encoded)

When using binary mode (correct):

1. Developer encodes string to EBCDIC bytes → Writes bytes → Pipe contains EBCDIC bytes
2. `CodePageService` reads EBCDIC bytes → Recognizes source=target → Copies as-is
3. Result: Correct data (no double-conversion)

## Testing

Run the diagnostic test to see the difference:

```bash
python3 tests/test_developer_usage_pattern.py
```

This test demonstrates:
1. The developer's pattern (text mode) - shows the problem
2. The correct pattern (binary mode) - shows it working

## API Design Note

The `CodePageService.convert_input()` method is designed to work with:
- **Files**: Can auto-detect encoding via file tags
- **Pipes**: Requires explicit `source_encoding` parameter and expects **binary data**

This is documented in the method signature:

```python
def convert_input(self, input_path: str, output_path: str,
                 source_encoding: Optional[str] = None,
                 target_encoding: str = 'IBM-1047') -> Dict[str, Any]:
    """
    Convert an input (file or pipe) from one encoding to another.
    
    For pipes: source_encoding is required (can't auto-detect)
    For files: source_encoding is optional (auto-detected via file tags)
    """
```

## Recommendation

The developer should:

1. **Change pipe I/O to binary mode** in their test code
2. **Explicitly encode/decode** when converting between strings and bytes
3. **Let `zos-ccsid-converter` handle the conversion** - don't do it twice

This follows the principle: **One conversion, one place, explicit control**.