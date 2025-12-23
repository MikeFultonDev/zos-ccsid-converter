#!/usr/bin/env python3
"""
Test script to verify --info --stdin functionality
"""

import subprocess
import sys


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


def test_stdin_info_basic(results: TestResults):
    """Test that --info --stdin works without requiring an output file"""
    test_name = "CLI --info --stdin basic functionality"
    
    # Create test input
    test_input = "Hello, World!\n"
    
    try:
        # Get user site-packages and add to environment
        import os
        env = os.environ.copy()
        try:
            user_site = subprocess.run(
                [sys.executable, '-m', 'site', '--user-site'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            # Add both user site-packages and zoautil path
            zoautil_path = "/usr/lpp/IBM/zoautil/lib/3.13"
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{user_site}:{zoautil_path}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = f"{user_site}:{zoautil_path}"
        except:
            pass  # If we can't get user site, continue without it
        
        # Debug: Print PYTHONPATH being used (disabled by default)
        if False:  # Set to True to enable debug output
            print(f"DEBUG test_stdin_info: PYTHONPATH={env.get('PYTHONPATH', 'NOT SET')}", file=sys.stderr)
        
        # Run the command with stdin using current Python interpreter
        result = subprocess.run(
            [sys.executable, '-m', 'zos_ccsid_converter.cli', '--info', '--stdin'],
            input=test_input.encode('utf-8'),
            capture_output=True,
            text=False,
            env=env
        )
        
        # Decode output
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        
        # Check if it succeeded
        if result.returncode != 0:
            error_msg = f"Command returned exit code {result.returncode}"
            if stderr:
                error_msg += f"\nStderr: {stderr}"
            if stdout:
                error_msg += f"\nStdout: {stdout}"
            results.add_fail(test_name, error_msg)
            return
        
        if "Source: stdin" not in stdout:
            results.add_fail(test_name, "Output missing 'Source: stdin'")
            return
        
        if "CCSID:" not in stdout:
            results.add_fail(test_name, "Output missing CCSID information")
            return
        
        if "Encoding:" not in stdout:
            results.add_fail(test_name, "Output missing encoding information")
            return
        
        results.add_pass(test_name)
            
    except Exception as e:
        results.add_fail(test_name, f"Exception: {e}")


def test_stdin_info_no_output_required(results: TestResults):
    """Test that --info --stdin doesn't require an output file argument"""
    test_name = "CLI --info --stdin without output file"
    
    test_input = "Test data\n"
    
    try:
        # Get user site-packages and add to environment
        import os
        env = os.environ.copy()
        try:
            user_site = subprocess.run(
                [sys.executable, '-m', 'site', '--user-site'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            # Add both user site-packages and zoautil path
            zoautil_path = "/usr/lpp/IBM/zoautil/lib/3.13"
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{user_site}:{zoautil_path}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = f"{user_site}:{zoautil_path}"
        except:
            pass  # If we can't get user site, continue without it
        
        # This should work without any positional arguments
        result = subprocess.run(
            [sys.executable, '-m', 'zos_ccsid_converter.cli', '--info', '--stdin'],
            input=test_input.encode('utf-8'),
            capture_output=True,
            text=False,
            env=env
        )
        
        # Decode output for debugging
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        
        if result.returncode != 0:
            error_msg = "Should not require output file argument"
            if stderr:
                error_msg += f"\nStderr: {stderr}"
            if stdout:
                error_msg += f"\nStdout: {stdout}"
            results.add_fail(test_name, error_msg)
            return
        
        results.add_pass(test_name)
            
    except Exception as e:
        results.add_fail(test_name, f"Exception: {e}")


def main():
    """Run all tests"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test --info --stdin CLI functionality',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--keep-files', action='store_true',
                       help='Keep test files after completion (not used in this test)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("CLI --info --stdin Tests")
    print("Testing: stdin info functionality without output file")
    print("="*70)
    print()
    
    results = TestResults()
    
    try:
        print("Running CLI stdin info tests...")
        test_stdin_info_basic(results)
        test_stdin_info_no_output_required(results)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    
    # Print summary
    success = results.print_summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob

# Made with Bob
