"""
z/OS CCSID Converter

A Python package for detecting and converting between ASCII (ISO8859-1) and
EBCDIC (IBM-1047) encodings on z/OS using native fcntl system calls.
Supports regular files, named pipes (FIFOs), and streams.

Example usage:
    from zos_ccsid_converter import CodePageService
    
    service = CodePageService()
    ccsid = service.get_ccsid('/path/to/file')
    ebcdic_data = service.convert_to_ebcdic(b"Hello World")
    
    # Convert files or pipes automatically
    stats = service.convert_input('/input.txt', '/output.txt')
    stats = service.convert_input('/tmp/mypipe', '/output.txt', source_encoding='ISO8859-1')
"""

from .converter import (
    CodePageService,
    detect_code_page,
    detect_encoding,
    convert_data,
    CCSID_ISO8859_1,
    CCSID_IBM1047,
    CCSID_UNTAGGED,
    ENCODING_MAP,
    PYTHON_ENCODING_MAP,
)

__version__ = '0.1.8'
__author__ = 'Mike Fulton'
__all__ = [
    'CodePageService',
    'detect_code_page',
    'detect_encoding',
    'convert_data',
    'CCSID_ISO8859_1',
    'CCSID_IBM1047',
    'CCSID_UNTAGGED',
    'ENCODING_MAP',
    'PYTHON_ENCODING_MAP',
]

# Made with Bob
