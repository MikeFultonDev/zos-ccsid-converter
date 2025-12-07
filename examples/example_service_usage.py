#!/usr/bin/env python3
"""
Example usage of the CodePageService for importing into other code.

This demonstrates how to use ebcdic_converter_fcntl as a service module.
"""

# Import the service class and convenience functions
from zos_ccsid_converter import (
    CodePageService,
    detect_code_page,
    detect_encoding,
    convert_data,
    CCSID_ISO8859_1,
    CCSID_IBM1047,
    CCSID_UNTAGGED
)


def example_1_detect_code_page():
    """Example 1: Detect the code page of a file"""
    print("=" * 60)
    print("Example 1: Detect Code Page")
    print("=" * 60)
    
    # Using convenience function
    ccsid = detect_code_page('/tmp/file.txt')
    print(f"CCSID: {ccsid}")
    
    if ccsid == CCSID_ISO8859_1:
        print("File is ASCII/ISO8859-1")
    elif ccsid == CCSID_IBM1047:
        print("File is EBCDIC/IBM-1047")
    else:
        print("File is untagged")
    
    # Using service class
    service = CodePageService()
    encoding = service.get_encoding_name('/tmp/file.txt')
    print(f"Encoding: {encoding}")
    print()


def example_2_check_file_type():
    """Example 2: Check if file is ASCII or EBCDIC"""
    print("=" * 60)
    print("Example 2: Check File Type")
    print("=" * 60)
    
    service = CodePageService()
    
    file_path = '/tmp/file.txt'
    
    if service.is_ascii(file_path):
        print(f"{file_path} is ASCII")
    elif service.is_ebcdic(file_path):
        print(f"{file_path} is EBCDIC")
    elif service.is_untagged(file_path):
        print(f"{file_path} is untagged")
    print()


def example_3_convert_bytes():
    """Example 3: Convert bytes between encodings"""
    print("=" * 60)
    print("Example 3: Convert Bytes")
    print("=" * 60)
    
    service = CodePageService()
    
    # ASCII to EBCDIC
    ascii_data = b"Hello World!"
    ebcdic_data = service.convert_to_ebcdic(ascii_data)
    print(f"ASCII:  {ascii_data}")
    print(f"EBCDIC: {ebcdic_data.hex()}")
    
    # EBCDIC back to ASCII
    ascii_back = service.convert_to_ascii(ebcdic_data)
    print(f"Back:   {ascii_back}")
    print()


def example_4_convert_file():
    """Example 4: Convert a file"""
    print("=" * 60)
    print("Example 4: Convert File")
    print("=" * 60)
    
    service = CodePageService(verbose=True)
    
    # Convert ASCII file to EBCDIC
    stats = service.convert_file(
        '/tmp/input.txt',
        '/tmp/output.txt',
        source_encoding='ISO8859-1',
        target_encoding='IBM-1047'
    )
    
    if stats['success']:
        print(f"✓ Conversion successful")
        print(f"  Bytes read: {stats['bytes_read']}")
        print(f"  Bytes written: {stats['bytes_written']}")
        print(f"  Source encoding: {stats['encoding_detected']}")
    else:
        print(f"✗ Conversion failed: {stats['error_message']}")
    print()


def example_5_auto_detect_and_convert():
    """Example 5: Auto-detect encoding and convert"""
    print("=" * 60)
    print("Example 5: Auto-detect and Convert")
    print("=" * 60)
    
    service = CodePageService()
    
    input_file = '/tmp/input.txt'
    output_file = '/tmp/output.txt'
    
    # Detect source encoding automatically
    source_encoding = service.get_encoding_name(input_file)
    print(f"Detected encoding: {source_encoding}")
    
    # Convert to EBCDIC (auto-detects source)
    stats = service.convert_file(input_file, output_file)
    
    if stats['success']:
        print(f"✓ Converted {stats['bytes_read']} bytes")
        print(f"  Conversion needed: {stats['conversion_needed']}")
    print()


def example_6_batch_processing():
    """Example 6: Process multiple files"""
    print("=" * 60)
    print("Example 6: Batch Processing")
    print("=" * 60)
    
    service = CodePageService()
    
    files = ['/tmp/file1.txt', '/tmp/file2.txt', '/tmp/file3.txt']
    
    for file_path in files:
        try:
            ccsid = service.get_ccsid(file_path)
            encoding = service.get_encoding_name(file_path)
            print(f"{file_path}: CCSID={ccsid}, Encoding={encoding}")
        except Exception as e:
            print(f"{file_path}: Error - {e}")
    print()


def example_7_integration_with_existing_code():
    """Example 7: Integration pattern for existing code"""
    print("=" * 60)
    print("Example 7: Integration Pattern")
    print("=" * 60)
    
    # Initialize service once
    codepage_service = CodePageService()
    
    def process_file(file_path: str) -> bytes:
        """Example function that processes a file"""
        # Detect encoding
        encoding = codepage_service.get_encoding_name(file_path)
        print(f"Processing {file_path} (encoding: {encoding})")
        
        # Read file with correct encoding
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Convert to EBCDIC if needed
        if encoding == 'ISO8859-1':
            data = codepage_service.convert_to_ebcdic(data)
            print("  Converted to EBCDIC")
        
        return data
    
    # Use in your code
    try:
        result = process_file('/tmp/file.txt')
        print(f"  Processed {len(result)} bytes")
    except Exception as e:
        print(f"  Error: {e}")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("CodePageService Usage Examples")
    print("=" * 60 + "\n")
    
    # Run examples (comment out ones that need actual files)
    # example_1_detect_code_page()
    # example_2_check_file_type()
    example_3_convert_bytes()
    # example_4_convert_file()
    # example_5_auto_detect_and_convert()
    # example_6_batch_processing()
    example_7_integration_with_existing_code()
    
    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)

# Made with Bob
