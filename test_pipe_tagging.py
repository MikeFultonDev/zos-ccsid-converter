#!/usr/bin/env python3
"""
Test if we can tag and read tags from named pipes on z/OS after opening them
"""

import os
import sys
import subprocess
import threading
import time
import tempfile
from zos_ccsid_converter import CodePageService

def test_pipe_tagging_after_open():
    """Test if we can read pipe tags after opening the pipe"""
    pipe_path = f"/tmp/test_pipe_{os.getpid()}.pipe"
    output_path = f"/tmp/test_output_{os.getpid()}.txt"
    
    try:
        # Create named pipe
        os.mkfifo(pipe_path)
        print(f"Created pipe: {pipe_path}")
        
        # Tag the pipe as EBCDIC
        print("\n1. Tagging pipe as IBM-1047...")
        result = subprocess.run(['chtag', '-tc', 'IBM-1047', pipe_path],
                              capture_output=True, text=True)
        print(f"   chtag result: rc={result.returncode}")
        
        # Write EBCDIC data to pipe in a thread
        def write_ebcdic():
            time.sleep(0.5)
            print("\n2. Writing EBCDIC data to pipe...")
            with open(pipe_path, 'wb') as f:
                content = "alloc da(test.dataset) new\n"
                f.write(content.encode('ibm1047'))
            print(f"   Wrote {len(content)} chars as EBCDIC")
        
        writer = threading.Thread(target=write_ebcdic, daemon=True)
        writer.start()
        
        # Use convert_input to read and convert
        print("\n3. Using convert_input to read pipe (should detect EBCDIC)...")
        service = CodePageService(verbose=True)
        stats = service.convert_input(pipe_path, output_path, target_encoding='IBM-1047')
        
        writer.join(timeout=2)
        
        print(f"\n4. Conversion results:")
        print(f"   Success: {stats['success']}")
        print(f"   Encoding detected: {stats.get('encoding_detected', 'N/A')}")
        print(f"   Bytes read: {stats.get('bytes_read', 0)}")
        print(f"   Bytes written: {stats.get('bytes_written', 0)}")
        
        if stats['success']:
            with open(output_path, 'r', encoding='ibm1047') as f:
                output = f.read()
            print(f"\n5. Output content: {repr(output)}")
        
    finally:
        for path in [pipe_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)
        print(f"\nCleaned up files")


def test_pipe_ascii():
    """Test with ASCII data"""
    pipe_path = f"/tmp/test_pipe_ascii_{os.getpid()}.pipe"
    output_path = f"/tmp/test_output_ascii_{os.getpid()}.txt"
    
    try:
        # Create named pipe
        os.mkfifo(pipe_path)
        print(f"\nCreated pipe: {pipe_path}")
        
        # Tag the pipe as ISO8859-1
        print("\n1. Tagging pipe as ISO8859-1...")
        result = subprocess.run(['chtag', '-tc', 'ISO8859-1', pipe_path],
                              capture_output=True, text=True)
        print(f"   chtag result: rc={result.returncode}")
        
        # Write ASCII data to pipe in a thread
        def write_ascii():
            time.sleep(0.5)
            print("\n2. Writing ASCII data to pipe...")
            with open(pipe_path, 'wb') as f:
                content = "alloc da(test.dataset) new\n"
                f.write(content.encode('iso8859-1'))
            print(f"   Wrote {len(content)} chars as ASCII")
        
        writer = threading.Thread(target=write_ascii, daemon=True)
        writer.start()
        
        # Use convert_input to read and convert
        print("\n3. Using convert_input to read pipe (should detect ASCII)...")
        service = CodePageService(verbose=True)
        stats = service.convert_input(pipe_path, output_path, target_encoding='IBM-1047')
        
        writer.join(timeout=2)
        
        print(f"\n4. Conversion results:")
        print(f"   Success: {stats['success']}")
        print(f"   Encoding detected: {stats.get('encoding_detected', 'N/A')}")
        print(f"   Bytes read: {stats.get('bytes_read', 0)}")
        print(f"   Bytes written: {stats.get('bytes_written', 0)}")
        
        if stats['success']:
            with open(output_path, 'r', encoding='ibm1047') as f:
                output = f.read()
            print(f"\n5. Output content: {repr(output)}")
        
    finally:
        for path in [pipe_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)
        print(f"\nCleaned up files")

if __name__ == '__main__':
    print("=" * 70)
    print("Testing Pipe Tagging on z/OS (After Opening)")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("TEST 1: EBCDIC Pipe")
    print("=" * 70)
    test_pipe_tagging_after_open()
    
    print("\n" + "=" * 70)
    print("TEST 2: ASCII Pipe")
    print("=" * 70)
    test_pipe_ascii()
    
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

# Made with Bob
