"""
z/OS EBCDIC Converter

A Python package for detecting and converting between ASCII (ISO8859-1) and 
EBCDIC (IBM-1047) encodings on z/OS using native fcntl system calls.

Example usage:
    from zos_ebcdic_converter import CodePageService
    
    service = CodePageService()
    ccsid = service.get_ccsid('/path/to/file')
    ebcdic_data = service.convert_to_ebcdic(b"Hello World")
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

__version__ = '1.0.0'
__author__ = 'IBM'
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
