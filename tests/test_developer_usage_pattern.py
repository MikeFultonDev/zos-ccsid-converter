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


class TestResults:
    """Track test results"""
    
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"✓ PASS: {test_name}")
    
    def add_fail(self, test_name: str, reason: str):
        self.total += 1
        self.failed += 1
        self.errors.append((test_name, reason))
        print(f"✗ FAIL: {test_name}")
        print(f"  Reason: {reason}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total tests: {self.total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.errors:
            print("\nFailed tests:")
            for test_name, reason in self.errors:
                print(f"  - {test_name}: {reason}")
        
        print("="*70)
        
        return self.failed == 0

def test_developer_pattern_text_mode(results: TestResults):
    """
    Reproduce the developer's exact pattern:
    - Write to pipe in TEXT mode with encoding='ibm1047'
    - Read from pipe and convert
    
    This will fail because convert_stream_to_ebcdic expects binary streams.
    """
    test_name = "Developer's pattern (text mode writing)"
    
    pipe_path = f"/tmp/test_dev_pattern_{os.getpid()}.pipe"
    output_path = f"/tmp/test_dev_output_{os.getpid()}.txt"
    
    try:
        # Create named pipe
        os.mkfifo(pipe_path)
        
        content = "alloc da(temp.batchtso.dataset) new\n"
        
        # Developer's pattern: Write in TEXT mode with encoding
        def write_pipe_text_mode():
            time.sleep(0.1)  # Give reader time to open
            try:
                # THIS IS THE PROBLEM: Writing in text mode
                with open(pipe_path, 'w', encoding='ibm1047') as f:
                    f.write(content)
            except Exception as e:
                pass  # Errors handled in main test
        
        writer = threading.Thread(target=write_pipe_text_mode, daemon=True)
        writer.start()
        
        # Try to use CodePageService.convert_input()
        service = CodePageService(verbose=False)
        
        stats = service.convert_input(
            pipe_path,
            output_path,
            source_encoding='IBM-1047',
            target_encoding='IBM-1047'
        )
        
        writer.join(timeout=5)
        
        if not stats['success']:
            results.add_fail(test_name, f"Conversion failed: {stats.get('error_message')}")
            return
        
        # Verify content
        with open(output_path, 'r', encoding='ibm1047') as f:
            output_content = f.read()
        
        if output_content != content:
            results.add_fail(test_name, "Content mismatch - data was corrupted by double encoding")
            return
        
        results.add_pass(test_name)
        
    except Exception as e:
        results.add_fail(test_name, f"Exception: {e}")
    
    finally:
        # Cleanup
        for path in [pipe_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_correct_pattern_binary_mode(results: TestResults):
    """
    Demonstrate the CORRECT pattern:
    - Write to pipe in BINARY mode
    - Read from pipe and convert
    
    This should work correctly.
    """
    test_name = "Correct pattern (binary mode writing)"
    
    pipe_path = f"/tmp/test_correct_pattern_{os.getpid()}.pipe"
    output_path = f"/tmp/test_correct_output_{os.getpid()}.txt"
    
    try:
        # Create named pipe
        os.mkfifo(pipe_path)
        
        content = "alloc da(temp.batchtso.dataset) new\n"
        
        # CORRECT: Write in BINARY mode
        def write_pipe_binary_mode():
            time.sleep(0.1)
            try:
                with open(pipe_path, 'wb') as f:
                    # Encode to EBCDIC bytes before writing
                    f.write(content.encode('ibm1047'))
            except Exception as e:
                pass  # Errors handled in main test
        
        writer = threading.Thread(target=write_pipe_binary_mode, daemon=True)
        writer.start()
        
        # Use CodePageService.convert_input()
        service = CodePageService(verbose=False)
        
        stats = service.convert_input(
            pipe_path,
            output_path,
            source_encoding='IBM-1047',
            target_encoding='IBM-1047'
        )
        
        writer.join(timeout=5)
        
        if not stats['success']:
            results.add_fail(test_name, f"Conversion failed: {stats.get('error_message')}")
            return
        
        # Verify content
        with open(output_path, 'r', encoding='ibm1047') as f:
            output_content = f.read()
        
        if output_content != content:
            results.add_fail(test_name, "Content mismatch")
            return
        
        results.add_pass(test_name)
        
    except Exception as e:
        results.add_fail(test_name, f"Exception: {e}")
    
    finally:
        # Cleanup
        for path in [pipe_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)


def main():
    """Run all tests"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test developer usage patterns with pipes',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--keep-files', action='store_true',
                       help='Keep test files after completion (not used in this test)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("Developer Usage Pattern Tests")
    print("Testing: Pipe writing patterns (text vs binary mode)")
    print("="*70)
    print()
    
    results = TestResults()
    
    try:
        print("Running pipe usage pattern tests...")
        test_developer_pattern_text_mode(results)
        test_correct_pattern_binary_mode(results)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    
    # Print summary
    success = results.print_summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
