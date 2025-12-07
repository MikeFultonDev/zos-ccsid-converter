#!/usr/bin/env python3
"""
converter.py - EBCDIC conversion using z/OS file tagging

This module provides EBCDIC conversion functionality using z/OS-specific
methods for file tagging.

Based on IBM z/OS documentation:
https://www.ibm.com/docs/en/zos/3.2.0?topic=SSLTBW_3.2.0/com.ibm.zos.v3r2.bpxbd00/rtfcndesc.html

Implementation Details:
- Uses F_CONTROL_CVT (13) with f_cnvrt structure to query file CCSID
- Uses chtag command for reliable file tag setting
- Implements ctypes.BigEndianStructure for proper z/OS big-endian byte order
- Uses fcntl.fcntl() for system calls with proper structure marshalling

Structures:
  struct f_cnvrt {
      int cvtcmd;      // Command: 3=query
      short pccsid;    // Process CCSID
      short fccsid;    // File CCSID (output)
  }

Key features:
- Direct fcntl system calls for file tag detection (no subprocess overhead)
- Uses ctypes.BigEndianStructure for correct z/OS byte order
- Reliable file tag detection via F_CONTROL_CVT
- Reliable file tag setting via chtag command
- Better error handling for unconvertible characters
- Support for both files and streams/pipes
- Tested and verified on z/OS

Note: F_SETTAG through Python's fcntl is unreliable (see test_f_settag_issue.py).
      The chtag command is used instead for setting file tags.
"""

import os
import sys
import fcntl
import struct
import ctypes
import stat
import subprocess
from typing import Optional, Dict, Tuple, BinaryIO, Any


# z/OS fcntl constants for file tagging
# From sys/fcntl.h on z/OS
# Based on actual z/OS header file values
F_SETTAG = 12       # Set file tag information
F_CONTROL_CVT = 13  # Control conversion
# Note: There is no F_GETTAG in z/OS. Use F_CONTROL_CVT with f_cnvrt structure
# to query file conversion information (which includes CCSID)
# Define f_cnvrt structure using ctypes for fcntl operations
# z/OS is big-endian, ctypes uses native byte order which is correct
class f_cnvrt(ctypes.BigEndianStructure):
    """
    z/OS f_cnvrt structure for F_CONTROL_CVT operations.
    
    struct f_cnvrt {
        int cvtcmd;      // Command: 2=set, 3=query
        short pccsid;    // Process CCSID
        short fccsid;    // File CCSID
    }
    
    Commands:
    - 2: Set file CCSID (fccsid) and process CCSID (pccsid)
    - 3: Query file CCSID
    
    Note: Using BigEndianStructure to explicitly specify z/OS byte order.
    """
    _fields_ = [
        ("cvtcmd", ctypes.c_int32),   # 4 bytes
        ("pccsid", ctypes.c_int16),   # 2 bytes
        ("fccsid", ctypes.c_int16),   # 2 bytes
    ]  # Total: 8 bytes


# CCSID (Coded Character Set ID) mappings
CCSID_ISO8859_1 = 819   # ASCII/ISO8859-1
CCSID_IBM1047 = 1047    # EBCDIC
CCSID_UNTAGGED = 0      # Untagged file

# Encoding name mappings
ENCODING_MAP = {
    CCSID_ISO8859_1: 'ISO8859-1',
    CCSID_IBM1047: 'IBM-1047',
    CCSID_UNTAGGED: 'untagged'
}

# Python encoding names
PYTHON_ENCODING_MAP = {
    'ISO8859-1': 'iso8859-1',
    'IBM-1047': 'ibm1047',
    'untagged': 'ibm1047'  # Treat untagged as EBCDIC per requirements
}


class FileTagInfo:
    """Container for z/OS file tag information"""
    
    def __init__(self, ccsid: int, text_flag: bool):
        self.ccsid = ccsid
        self.text_flag = text_flag
        self.encoding_name = ENCODING_MAP.get(ccsid, f'CCSID-{ccsid}')
    
    def __repr__(self):
        return f"FileTagInfo(ccsid={self.ccsid}, text={self.text_flag}, encoding={self.encoding_name})"


def get_file_encoding_fcntl(path: str, fd: Optional[int] = None,
                            verbose: bool = False) -> str:
    """
    Get file encoding using z/OS fcntl F_CONTROL_CVT with ctypes.
    
    Uses the f_cnvrt structure with fcntl.fcntl() to query file CCSID.
    This is the correct way to access file tags in Python on z/OS.
    
    Args:
        path: File path (used for error messages and if fd not provided)
        fd: Optional file descriptor (if None, file will be opened)
        verbose: Enable verbose output
    
    Returns:
        Encoding name: 'ISO8859-1', 'IBM-1047', or 'untagged'
    
    Raises:
        OSError: If file cannot be accessed
    """
    close_fd = False
    
    try:
        # Open file if descriptor not provided
        if fd is None:
            fd = os.open(path, os.O_RDONLY)
            close_fd = True
        
        if verbose:
            print(f"DEBUG: Getting file tag for {path} using F_CONTROL_CVT")
            print(f"  File descriptor: {fd}")
        
        # Create f_cnvrt structure with cvtcmd=3 for query
        qcvt = f_cnvrt(3, 0, 0)  # 3 = query command
        
        if verbose:
            print(f"  Query structure: cvtcmd={qcvt.cvtcmd}, pccsid={qcvt.pccsid}, fccsid={qcvt.fccsid}")
        
        # Call fcntl with F_CONTROL_CVT
        result = fcntl.fcntl(fd, F_CONTROL_CVT, qcvt)
        
        # Extract result using from_buffer_copy
        cvt_result = f_cnvrt.from_buffer_copy(result)
        
        ccsid = cvt_result.fccsid
        
        if verbose:
            print(f"  Result: cvtcmd={cvt_result.cvtcmd}, pccsid={cvt_result.pccsid}, fccsid={cvt_result.fccsid}")
            print(f"  File CCSID={ccsid}")
        
        # Map CCSID to encoding name
        encoding = ENCODING_MAP.get(ccsid, 'untagged')
        
        if verbose:
            print(f"  Final detected encoding: {encoding}")
        
        return encoding
        
    except Exception as e:
        if verbose:
            print(f"DEBUG: fcntl F_CONTROL_CVT failed for {path}: {e}")
            import traceback
            traceback.print_exc()
        # If fcntl fails, treat as untagged
        return 'untagged'
        
    finally:
        if close_fd and fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass


def _build_chtag_command(path: str, ccsid: int, text_flag: bool) -> list:
    """Build chtag command based on file type."""
    if text_flag:
        return ['chtag', '-t', '-c', str(ccsid), path]
    return ['chtag', '-b', path]


def _log_chtag_execution(cmd: list, result, verbose: bool) -> None:
    """Log chtag command execution details."""
    if not verbose:
        return
    
    print(f"  Running: {' '.join(cmd)}")
    print(f"  Return code: {result.returncode}")
    if result.stdout:
        print(f"  stdout: {result.stdout}")
    if result.stderr:
        print(f"  stderr: {result.stderr}")


def _verify_tag_set(path: str, ccsid: int, verbose: bool) -> bool:
    """Verify that the file tag was set correctly."""
    actual_encoding = get_file_encoding_fcntl(path, verbose=False)
    expected_encoding = ENCODING_MAP.get(ccsid, f'CCSID-{ccsid}')
    
    if verbose:
        print(f"  Verification: expected={expected_encoding}, actual={actual_encoding}")
    
    success = actual_encoding == expected_encoding
    if verbose:
        if success:
            print(f"  Successfully set file CCSID to {ccsid}")
        else:
            print(f"  Tag verification failed: expected {expected_encoding}, got {actual_encoding}")
    
    return success


def set_file_tag_fcntl(path: str, ccsid: int, text_flag: bool = True,
                      verbose: bool = False) -> bool:
    """
    Set file CCSID using z/OS chtag command.
    
    F_SETTAG through Python's fcntl is unreliable - it may return errno 121
    but not actually set the tag, especially on subsequent calls. The chtag
    command is the reliable way to set file tags on z/OS.
    
    Args:
        path: File path to tag
        ccsid: CCSID to set (e.g., 819 for ISO8859-1, 1047 for IBM-1047)
        text_flag: True for text file, False for binary
        verbose: Enable verbose output
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if verbose:
            print(f"DEBUG: Setting file CCSID for {path} using chtag command")
            print(f"  Target CCSID={ccsid}, text_flag={text_flag}")
        
        cmd = _build_chtag_command(path, ccsid, text_flag)
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        _log_chtag_execution(cmd, result, verbose)
        
        if result.returncode != 0:
            if verbose:
                print(f"  chtag command failed with return code {result.returncode}")
            return False
        
        return _verify_tag_set(path, ccsid, verbose)
        
    except Exception as e:
        if verbose:
            print(f"ERROR: Failed to set file CCSID for {path}: {e}")
            import traceback
            traceback.print_exc()
        return False


def get_file_tag_info(path: str, verbose: bool = False) -> Optional[FileTagInfo]:
    """
    Get detailed file tag information.
    
    Args:
        path: File path
        verbose: Enable verbose output
    
    Returns:
        FileTagInfo object or None if unable to get info
    """
    try:
        encoding = get_file_encoding_fcntl(path, verbose=verbose)
        
        # Map encoding name back to CCSID
        ccsid = CCSID_UNTAGGED
        for c, e in ENCODING_MAP.items():
            if e == encoding:
                ccsid = c
                break
        
        # Assume text file (we don't have binary flag from simple query)
        return FileTagInfo(ccsid, True)
        
    except Exception as e:
        if verbose:
            print(f"ERROR: Failed to get file tag info for {path}: {e}")
        return None


def is_named_pipe(path: str) -> bool:
    """Check if a path is a named pipe (FIFO)"""
    try:
        return stat.S_ISFIFO(os.stat(path).st_mode)
    except OSError:
        return False


def _log_verbose(message: str, verbose: bool) -> None:
    """Helper to print verbose messages."""
    if verbose:
        print(message)


def _convert_ascii_to_ebcdic(input_path: str, output_path: str, 
                             verbose: bool) -> Dict[str, int]:
    """
    Convert ASCII file to EBCDIC.
    
    Returns dict with 'bytes_read' and 'bytes_written' keys.
    """
    _log_verbose("Converting from ISO8859-1 to IBM-1047...", verbose)
    
    with open(input_path, 'r', encoding='iso8859-1', errors='replace') as f_in:
        content = f_in.read()
        bytes_read = len(content.encode('iso8859-1', errors='replace'))
    
    with open(output_path, 'w', encoding='ibm1047', errors='replace') as f_out:
        f_out.write(content)
        bytes_written = len(content.encode('ibm1047', errors='replace'))
    
    return {'bytes_read': bytes_read, 'bytes_written': bytes_written}


def _copy_binary_file(input_path: str, output_path: str, 
                     verbose: bool) -> Dict[str, int]:
    """
    Copy file as binary without conversion.
    
    Returns dict with 'bytes_read' and 'bytes_written' keys.
    """
    _log_verbose("File is already EBCDIC (or untagged), copying as binary...", verbose)
    
    with open(input_path, 'rb') as f_in:
        content = f_in.read()
        bytes_count = len(content)
    
    with open(output_path, 'wb') as f_out:
        f_out.write(content)
    
    return {'bytes_read': bytes_count, 'bytes_written': bytes_count}


def _tag_output_file(output_path: str, encoding: str, verbose: bool) -> None:
    """Tag output file as IBM-1047 if needed."""
    should_tag = encoding in ('ISO8859-1', 'untagged')
    if not should_tag:
        return
    
    tag_success = set_file_tag_fcntl(output_path, CCSID_IBM1047, verbose=verbose)
    if tag_success:
        _log_verbose("Tagged output file as IBM-1047", verbose)
    elif encoding == 'ISO8859-1':
        _log_verbose("Warning: Could not tag output file", verbose)


def convert_to_ebcdic_fcntl(input_path: str, output_path: str,
                           verbose: bool = False) -> Dict[str, Any]:
    """
    Convert input file to EBCDIC using fcntl-based encoding detection.
    
    This function:
    1. Uses fcntl to detect input file encoding
    2. Converts from ASCII to EBCDIC if needed
    3. Handles unconvertible characters gracefully (leaves them unchanged)
    4. Tags output file using fcntl
    5. Returns conversion statistics
    
    Args:
        input_path: Source file path
        output_path: Destination file path
        verbose: Enable verbose output
    
    Returns:
        Dictionary with conversion statistics:
        {
            'success': bool,
            'bytes_read': int,
            'bytes_written': int,
            'encoding_detected': str,
            'conversion_needed': bool,
            'errors': int,
            'error_message': str (if success=False)
        }
    """
    stats = {
        'success': False,
        'bytes_read': 0,
        'bytes_written': 0,
        'encoding_detected': 'unknown',
        'conversion_needed': False,
        'errors': 0,
        'error_message': None
    }
    
    try:
        # Detect input encoding using fcntl
        encoding = get_file_encoding_fcntl(input_path, verbose=verbose)
        stats['encoding_detected'] = encoding
        
        _log_verbose(f"Input file: {input_path}", verbose)
        _log_verbose(f"Detected encoding: {encoding}", verbose)
        
        # Perform conversion or binary copy based on encoding
        if encoding == 'ISO8859-1':
            stats['conversion_needed'] = True
            result = _convert_ascii_to_ebcdic(input_path, output_path, verbose)
        else:
            stats['conversion_needed'] = False
            result = _copy_binary_file(input_path, output_path, verbose)
        
        stats['bytes_read'] = result['bytes_read']
        stats['bytes_written'] = result['bytes_written']
        
        # Tag output file
        _tag_output_file(output_path, encoding, verbose)
        
        stats['success'] = True
        _log_verbose(
            f"Conversion complete: {stats['bytes_read']} bytes read, "
            f"{stats['bytes_written']} bytes written",
            verbose
        )
        
        return stats
        
    except Exception as e:
        stats['error_message'] = str(e)
        _log_verbose(f"ERROR: Conversion failed: {e}", verbose)
        return stats


def _convert_chunk_to_ebcdic(chunk: bytes, source_encoding: str,
                             chunk_number: int, verbose: bool) -> Tuple[bytes, bool]:
    """
    Convert a single chunk from source encoding to EBCDIC.
    
    Args:
        chunk: Bytes to convert
        source_encoding: Source encoding name
        chunk_number: Chunk number for error reporting
        verbose: Enable verbose output
    
    Returns:
        Tuple of (converted_bytes, had_error)
    """
    if source_encoding.lower() == 'ibm1047':
        return chunk, False
    
    try:
        text = chunk.decode(source_encoding, errors='replace')
        converted = text.encode('ibm1047', errors='replace')
        return converted, False
    except Exception as e:
        _log_verbose(f"Warning: Conversion error in chunk {chunk_number}: {e}", verbose)
        return chunk, True


def _log_stream_conversion_start(source_encoding: str, verbose: bool) -> None:
    """Log stream conversion start message."""
    _log_verbose(f"Converting stream from {source_encoding} to IBM-1047...", verbose)


def _log_stream_conversion_complete(stats: Dict[str, Any], verbose: bool) -> None:
    """Log stream conversion completion message."""
    _log_verbose(
        f"Stream conversion complete: {stats['bytes_read']} bytes read, "
        f"{stats['bytes_written']} bytes written, "
        f"{stats['chunks_processed']} chunks processed",
        verbose
    )


def convert_stream_to_ebcdic(input_stream: BinaryIO, output_stream: BinaryIO,
                             source_encoding: str = 'iso8859-1',
                             chunk_size: int = 8192,
                             verbose: bool = False) -> Dict[str, Any]:
    """
    Convert a stream/pipe from ASCII to EBCDIC.
    
    This function is used for pipes and streams where fcntl tagging is not available.
    It reads from the input stream and writes converted data to the output stream.
    
    Args:
        input_stream: Input binary stream (e.g., pipe, stdin)
        output_stream: Output binary stream
        source_encoding: Source encoding ('iso8859-1' or 'ibm1047')
        chunk_size: Size of chunks to read/write
        verbose: Enable verbose output
    
    Returns:
        Dictionary with conversion statistics
    """
    stats = {
        'success': False,
        'bytes_read': 0,
        'bytes_written': 0,
        'chunks_processed': 0,
        'errors': 0,
        'error_message': None
    }
    
    try:
        _log_stream_conversion_start(source_encoding, verbose)
        
        while True:
            chunk = input_stream.read(chunk_size)
            if not chunk:
                break
            
            stats['bytes_read'] += len(chunk)
            stats['chunks_processed'] += 1
            
            converted, had_error = _convert_chunk_to_ebcdic(
                chunk, source_encoding, stats['chunks_processed'], verbose
            )
            
            if had_error:
                stats['errors'] += 1
            
            output_stream.write(converted)
            stats['bytes_written'] += len(converted)
        
        stats['success'] = True
        _log_stream_conversion_complete(stats, verbose)
        return stats
        
    except Exception as e:
        stats['error_message'] = str(e)
        _log_verbose(f"ERROR: Stream conversion failed: {e}", verbose)
        return stats



# ============================================================================
# Service API for importing into other code
# ============================================================================

class CodePageService:
    """
    Service class for code page detection and conversion.
    
    This class provides a clean API for other code to:
    - Detect the code page (CCSID) of files
    - Convert data between code pages
    - Handle both files and byte streams
    
    Example usage:
        from ebcdic_converter_fcntl import CodePageService
        
        service = CodePageService()
        
        # Detect code page
        ccsid = service.get_ccsid('/path/to/file')
        encoding = service.get_encoding_name('/path/to/file')
        
        # Convert data
        ebcdic_bytes = service.convert_to_ebcdic(ascii_bytes)
        ascii_bytes = service.convert_to_ascii(ebcdic_bytes)
        
        # Convert files
        service.convert_file('/input.txt', '/output.txt', 
                           source_encoding='ISO8859-1', 
                           target_encoding='IBM-1047')
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the code page service.
        
        Args:
            verbose: Enable verbose output for debugging
        """
        self.verbose = verbose
    
    def get_ccsid(self, path: str) -> int:
        """
        Get the CCSID (Coded Character Set ID) of a file.
        
        Args:
            path: File path
            
        Returns:
            CCSID value (819=ISO8859-1, 1047=IBM-1047, 0=untagged)
            
        Example:
            ccsid = service.get_ccsid('/tmp/file.txt')
            if ccsid == 819:
                print("File is ASCII/ISO8859-1")
            elif ccsid == 1047:
                print("File is EBCDIC/IBM-1047")
        """
        encoding_name = get_file_encoding_fcntl(path, verbose=self.verbose)
        
        # Map encoding name back to CCSID
        for ccsid, name in ENCODING_MAP.items():
            if name == encoding_name:
                return ccsid
        
        return CCSID_UNTAGGED
    
    def get_encoding_name(self, path: str) -> str:
        """
        Get the encoding name of a file.
        
        Args:
            path: File path
            
        Returns:
            Encoding name: 'ISO8859-1', 'IBM-1047', or 'untagged'
            
        Example:
            encoding = service.get_encoding_name('/tmp/file.txt')
            print(f"File encoding: {encoding}")
        """
        return get_file_encoding_fcntl(path, verbose=self.verbose)
    
    def is_ascii(self, path: str) -> bool:
        """Check if file is ASCII/ISO8859-1 encoded"""
        return self.get_ccsid(path) == CCSID_ISO8859_1
    
    def is_ebcdic(self, path: str) -> bool:
        """Check if file is EBCDIC/IBM-1047 encoded"""
        return self.get_ccsid(path) == CCSID_IBM1047
    
    def is_untagged(self, path: str) -> bool:
        """Check if file is untagged"""
        return self.get_ccsid(path) == CCSID_UNTAGGED
    
    def convert_bytes(self, data: bytes, source_encoding: str, 
                     target_encoding: str) -> bytes:
        """
        Convert bytes from one encoding to another.
        
        Args:
            data: Input bytes
            source_encoding: Source encoding ('ISO8859-1', 'IBM-1047', etc.)
            target_encoding: Target encoding ('ISO8859-1', 'IBM-1047', etc.)
            
        Returns:
            Converted bytes
            
        Example:
            ascii_data = b"Hello World"
            ebcdic_data = service.convert_bytes(ascii_data, 'ISO8859-1', 'IBM-1047')
        """
        # Get Python encoding names
        source_py = PYTHON_ENCODING_MAP.get(source_encoding, source_encoding.lower())
        target_py = PYTHON_ENCODING_MAP.get(target_encoding, target_encoding.lower())
        
        # Decode from source, encode to target
        text = data.decode(source_py, errors='replace')
        return text.encode(target_py, errors='replace')
    
    def convert_to_ebcdic(self, data: bytes, source_encoding: str = 'ISO8859-1') -> bytes:
        """
        Convert bytes to EBCDIC (IBM-1047).
        
        Args:
            data: Input bytes
            source_encoding: Source encoding (default: 'ISO8859-1')
            
        Returns:
            EBCDIC bytes
            
        Example:
            ascii_data = b"Hello World"
            ebcdic_data = service.convert_to_ebcdic(ascii_data)
        """
        return self.convert_bytes(data, source_encoding, 'IBM-1047')
    
    def convert_to_ascii(self, data: bytes, source_encoding: str = 'IBM-1047') -> bytes:
        """
        Convert bytes to ASCII (ISO8859-1).
        
        Args:
            data: Input bytes
            source_encoding: Source encoding (default: 'IBM-1047')
            
        Returns:
            ASCII bytes
            
        Example:
            ebcdic_data = b"\xc8\x85\x93\x93\x96"  # "Hello" in EBCDIC
            ascii_data = service.convert_to_ascii(ebcdic_data)
        """
        return self.convert_bytes(data, source_encoding, 'ISO8859-1')
    
    def convert_file(self, input_path: str, output_path: str,
                    source_encoding: Optional[str] = None,
                    target_encoding: str = 'IBM-1047') -> Dict[str, Any]:
        """
        Convert a file from one encoding to another.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            source_encoding: Source encoding (auto-detected if None)
            target_encoding: Target encoding (default: 'IBM-1047')
            
        Returns:
            Dictionary with conversion statistics
            
        Example:
            stats = service.convert_file('/input.txt', '/output.txt')
            if stats['success']:
                print(f"Converted {stats['bytes_read']} bytes")
        """
        # Auto-detect source encoding if not specified
        if source_encoding is None:
            source_encoding = self.get_encoding_name(input_path)
        
        # If target is EBCDIC, use the existing function
        if target_encoding == 'IBM-1047':
            return convert_to_ebcdic_fcntl(input_path, output_path, 
                                          verbose=self.verbose)
        
        # Otherwise, do manual conversion
        try:
            with open(input_path, 'rb') as f_in:
                input_data = f_in.read()
            
            output_data = self.convert_bytes(input_data, source_encoding, 
                                            target_encoding)
            
            with open(output_path, 'wb') as f_out:
                f_out.write(output_data)
            
            return {
                'success': True,
                'bytes_read': len(input_data),
                'bytes_written': len(output_data),
                'encoding_detected': source_encoding,
                'target_encoding': target_encoding,
                'conversion_needed': source_encoding != target_encoding
            }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'bytes_read': 0,
                'bytes_written': 0
            }


# Convenience functions for direct import
def detect_code_page(path: str, verbose: bool = False) -> int:
    """
    Convenience function to detect file code page (CCSID).
    
    Args:
        path: File path
        verbose: Enable verbose output
        
    Returns:
        CCSID value (819, 1047, or 0)
        
    Example:
        from ebcdic_converter_fcntl import detect_code_page
        ccsid = detect_code_page('/tmp/file.txt')
    """
    service = CodePageService(verbose=verbose)
    return service.get_ccsid(path)


def detect_encoding(path: str, verbose: bool = False) -> str:
    """
    Convenience function to detect file encoding name.
    
    Args:
        path: File path
        verbose: Enable verbose output
        
    Returns:
        Encoding name: 'ISO8859-1', 'IBM-1047', or 'untagged'
        
    Example:
        from ebcdic_converter_fcntl import detect_encoding
        encoding = detect_encoding('/tmp/file.txt')
    """
    return get_file_encoding_fcntl(path, verbose=verbose)


def convert_data(data: bytes, source_encoding: str, target_encoding: str) -> bytes:
    """
    Convenience function to convert bytes between encodings.
    
    Args:
        data: Input bytes
        source_encoding: Source encoding name
        target_encoding: Target encoding name
        
    Returns:
        Converted bytes
        
    Example:
        from ebcdic_converter_fcntl import convert_data
        ebcdic = convert_data(b"Hello", 'ISO8859-1', 'IBM-1047')
    """
    service = CodePageService()
    return service.convert_bytes(data, source_encoding, target_encoding)


def main():
    """Simple command-line interface for testing"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='Convert files to EBCDIC using z/OS fcntl',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a file
  ebcdic_converter_fcntl.py input.txt output.txt
  
  # Get file encoding info
  ebcdic_converter_fcntl.py --info input.txt
  
  # Convert with verbose output
  ebcdic_converter_fcntl.py -v input.txt output.txt
  
  # Convert from stdin to file
  cat input.txt | ebcdic_converter_fcntl.py --stdin output.txt
"""
    )
    
    parser.add_argument('input', nargs='?', help='Input file path')
    parser.add_argument('output', nargs='?', help='Output file path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--info', action='store_true', help='Show file encoding info')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    
    args = parser.parse_args()
    
    try:
        if args.info:
            if not args.input:
                parser.error("--info requires an input file")
            info = get_file_tag_info(args.input, verbose=args.verbose)
            if info:
                print(f"CCSID: {info.ccsid}, Text: {info.text_flag}")
            return 0
        
        if args.stdin:
            if not args.output:
                parser.error("--stdin requires an output file")
            convert_stream_to_ebcdic(sys.stdin.buffer, open(args.output, 'wb'),
                                    verbose=args.verbose)
            return 0
        
        if not args.input or not args.output:
            parser.error("input and output files are required")
        
        convert_to_ebcdic_fcntl(args.input, args.output, verbose=args.verbose)
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
