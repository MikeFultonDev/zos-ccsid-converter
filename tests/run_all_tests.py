#!/usr/bin/env python3
"""
run_all_tests.py - Test runner for all zos-ccsid-converter tests

This script discovers and runs all test files in the tests directory,
providing a unified test harness with summary reporting.

Usage:
    python3 run_all_tests.py [--verbose] [--keep-files]
"""

import os
import sys
import subprocess
from pathlib import Path


class TestRunner:
    """Manages test execution and reporting"""
    
    def __init__(self, verbose: bool = False, keep_files: bool = False):
        self.verbose = verbose
        self.keep_files = keep_files
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
    
    def run_test_file(self, test_file: Path) -> bool:
        """
        Run a single test file and return success status
        
        Args:
            test_file: Path to the test file
            
        Returns:
            True if test passed (exit code 0), False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Running: {test_file.name}")
        print(f"{'='*70}")
        
        # Build command
        cmd = [sys.executable, str(test_file)]
        if self.verbose:
            cmd.append('--verbose')
        if self.keep_files:
            cmd.append('--keep-files')
        
        try:
            # Run the test - inherit environment to pass PYTHONPATH
            result = subprocess.run(
                cmd,
                cwd=test_file.parent,
                capture_output=False,  # Let output go to stdout/stderr
                text=True,
                env=os.environ.copy()  # Inherit environment including PYTHONPATH
            )
            
            self.tests_run += 1
            
            if result.returncode == 0:
                self.tests_passed += 1
                print(f"\n✓ {test_file.name} PASSED")
                return True
            else:
                self.tests_failed += 1
                self.failed_tests.append(test_file.name)
                print(f"\n✗ {test_file.name} FAILED (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            self.tests_failed += 1
            self.failed_tests.append(test_file.name)
            print(f"\n✗ {test_file.name} FAILED with exception: {e}")
            return False
    
    def discover_tests(self, test_dir: Path) -> list:
        """
        Discover all test files in the directory
        
        Args:
            test_dir: Directory to search for tests
            
        Returns:
            List of test file paths
        """
        test_files = []
        
        # Find all Python files starting with 'test_'
        for file_path in sorted(test_dir.glob('test_*.py')):
            if file_path.name != 'test_runner.py':  # Skip the runner itself
                test_files.append(file_path)
        
        return test_files
    
    def print_summary(self):
        """Print test execution summary"""
        print("\n" + "="*70)
        print("TEST EXECUTION SUMMARY")
        print("="*70)
        print(f"Total test files run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        
        if self.failed_tests:
            print("\nFailed test files:")
            for test_name in self.failed_tests:
                print(f"  - {test_name}")
        
        print("="*70)
        
        if self.tests_failed == 0:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        
        print("="*70)


def main():
    """Main test runner entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run all zos-ccsid-converter tests',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output for tests')
    parser.add_argument('--keep-files', action='store_true',
                       help='Keep test files after completion')
    
    args = parser.parse_args()
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    print("="*70)
    print("zos-ccsid-converter Test Suite")
    print("="*70)
    print(f"Test directory: {test_dir}")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    print("="*70)
    
    # Create runner
    runner = TestRunner(verbose=args.verbose, keep_files=args.keep_files)
    
    # Discover tests
    test_files = runner.discover_tests(test_dir)
    
    if not test_files:
        print("\n✗ No test files found!")
        return 1
    
    print(f"\nDiscovered {len(test_files)} test file(s):")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # Run all tests
    for test_file in test_files:
        runner.run_test_file(test_file)
    
    # Print summary
    runner.print_summary()
    
    # Return appropriate exit code
    return 0 if runner.tests_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob