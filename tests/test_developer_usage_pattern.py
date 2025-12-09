#!/usr/bin/env python3
"""
Test to reproduce the developer's usage pattern from batchtsocmd.

This test demonstrates the issue when:
1. Writing to pipes in text mode with encoding
2. Reading from pipes expecting binary data
3. The mismatch between text/binary modes causes conversion issues
"""

import os
import sys
import threading
import tempfile
import time
from zos_ccsid_converter import CodePageService

def test_developer_pattern_text_mode():
    """
    Reproduce the developer's exact pattern:
    - Write to pipe in TEXT mode with encoding='ibm1047'
    - Read from pipe and convert
    
    This will fail because convert_stream_to_ebcdic expects binary streams.
    """
    print("=" * 70)
    print("Test: Developer's Pattern (Text Mode Writing)")
    print("=" * 70)
    
    pipe_path = f"/tmp/test_dev_pattern_{os.getpid()}.pipe"
    output_path = f"/tmp/test_dev_output_{os.getpid()}.txt"
    
    try:
        # Create named pipe
        os.mkfifo(pipe_path)
        print(f"Created pipe: {pipe_path}")
        
        content = "alloc da(temp.batchtso.dataset) new\n"
        
        # Developer's pattern: Write in TEXT mode with encoding
        def write_pipe_text_mode():
            time.sleep(0.1)  # Give reader time to open
            try:
                # THIS IS THE PROBLEM: Writing in text mode
                with open(pipe_path, 'w', encoding='ibm1047') as f:
                    f.write(content)
                print("  Wrote to pipe in TEXT mode with encoding='ibm1047'")
            except Exception as e:
                print(f"  Write error: {e}")
        
        writer = threading.Thread(target=write_pipe_text_mode, daemon=True)
        writer.start()
        
        # Try to use CodePageService.convert_input()
        service = CodePageService(verbose=True)
        
        print("\nAttempting conversion with source_encoding='IBM-1047'...")
        stats = service.convert_input(
            pipe_path,
            output_path,
            source_encoding='IBM-1047',
            target_encoding='IBM-1047'
        )
        
        writer.join(timeout=5)
        
        if stats['success']:
            print(f"\n✓ Conversion succeeded")
            print(f"  Bytes read: {stats['bytes_read']}")
            print(f"  Bytes written: {stats['bytes_written']}")
            
            # Verify content
            with open(output_path, 'r', encoding='ibm1047') as f:
                output_content = f.read()
            
            print(f"\nOriginal: {repr(content)}")
            print(f"Output:   {repr(output_content)}")
            
            if output_content == content:
                print("✓ Content matches!")
            else:
                print("✗ Content MISMATCH - data was corrupted!")
                print(f"  Expected bytes: {content.encode('ibm1047').hex()}")
                print(f"  Got bytes:      {output_content.encode('ibm1047').hex()}")
        else:
            print(f"\n✗ Conversion failed: {stats.get('error_message')}")
        
    except Exception as e:
        print(f"\n✗ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        for path in [pipe_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    print()


def test_correct_pattern_binary_mode():
    """
    Demonstrate the CORRECT pattern:
    - Write to pipe in BINARY mode
    - Read from pipe and convert
    
    This should work correctly.
    """
    print("=" * 70)
    print("Test: Correct Pattern (Binary Mode Writing)")
    print("=" * 70)
    
    pipe_path = f"/tmp/test_correct_pattern_{os.getpid()}.pipe"
    output_path = f"/tmp/test_correct_output_{os.getpid()}.txt"
    
    try:
        # Create named pipe
        os.mkfifo(pipe_path)
        print(f"Created pipe: {pipe_path}")
        
        content = "alloc da(temp.batchtso.dataset) new\n"
        
        # CORRECT: Write in BINARY mode
        def write_pipe_binary_mode():
            time.sleep(0.1)
            try:
                with open(pipe_path, 'wb') as f:
                    # Encode to EBCDIC bytes before writing
                    f.write(content.encode('ibm1047'))
                print("  Wrote to pipe in BINARY mode (pre-encoded to EBCDIC)")
            except Exception as e:
                print(f"  Write error: {e}")
        
        writer = threading.Thread(target=write_pipe_binary_mode, daemon=True)
        writer.start()
        
        # Use CodePageService.convert_input()
        service = CodePageService(verbose=True)
        
        print("\nAttempting conversion with source_encoding='IBM-1047'...")
        stats = service.convert_input(
            pipe_path,
            output_path,
            source_encoding='IBM-1047',
            target_encoding='IBM-1047'
        )
        
        writer.join(timeout=5)
        
        if stats['success']:
            print(f"\n✓ Conversion succeeded")
            print(f"  Bytes read: {stats['bytes_read']}")
            print(f"  Bytes written: {stats['bytes_written']}")
            
            # Verify content
            with open(output_path, 'r', encoding='ibm1047') as f:
                output_content = f.read()
            
            print(f"\nOriginal: {repr(content)}")
            print(f"Output:   {repr(output_content)}")
            
            if output_content == content:
                print("✓ Content matches!")
            else:
                print("✗ Content MISMATCH!")
        else:
            print(f"\n✗ Conversion failed: {stats.get('error_message')}")
        
    except Exception as e:
        print(f"\n✗ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        for path in [pipe_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing Developer's Usage Pattern vs Correct Pattern")
    print("=" * 70 + "\n")
    
    test_developer_pattern_text_mode()
    test_correct_pattern_binary_mode()
    
    print("=" * 70)
    print("DIAGNOSIS:")
    print("=" * 70)
    print("""
The issue is that the developer is writing to named pipes in TEXT mode
with encoding, but CodePageService.convert_input() expects BINARY data.

PROBLEM in batchtsocmd test (lines 87-92):
    with open(pipe_path, 'w', encoding=encoding) as f:  # TEXT MODE
        f.write(content)

SOLUTION:
The developer should write to pipes in BINARY mode:
    with open(pipe_path, 'wb') as f:  # BINARY MODE
        f.write(content.encode(encoding))

When writing in text mode with encoding='ibm1047', Python performs
encoding internally, but then our service tries to read it as binary
and decode it again, causing double-encoding issues.
""")
    print("=" * 70)

# Made with Bob
