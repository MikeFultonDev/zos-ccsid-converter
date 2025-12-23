#!/usr/bin/env python3
"""
Diagnostic script to check zos_util availability and functionality
"""

import sys
import os

print("="*70)
print("Checking zos_util Availability on z/OS")
print("="*70)

print("\nPython Environment:")
print(f"  Python version: {sys.version}")
print(f"  Platform: {sys.platform}")
print(f"  Executable: {sys.executable}")

print("\n" + "="*70)
print("Testing zos_util with converter module")
print("="*70)

try:
    # First check if we can import
    print("\nImporting converter module...")
    from zos_ccsid_converter import converter
    print("✓ Module imported successfully")
    
    print(f"\nZOS_UTIL_AVAILABLE flag: {converter.ZOS_UTIL_AVAILABLE}")
    
    if not converter.ZOS_UTIL_AVAILABLE:
        print("\n✗ zos_util is NOT available")
        print("  This is why chtag fallback is being used")
        print("\nTo install zos_util:")
        print("  1. Clone: git clone https://github.com/IBM/zos-util.git")
        print("  2. Build: cd zos-util && python3 setup.py install")
        print("  Or: pip install zos-util (if available on PyPI)")
        
        # Try to import directly
        print("\nAttempting direct import...")
        try:
            import zos_util
            print(f"  ✓ zos_util imported: {zos_util}")
            print("  This is unexpected - module should be available!")
        except ImportError as e:
            print(f"  ✗ Cannot import zos_util: {e}")
            print("  zos_util needs to be installed")
        
        sys.exit(1)
    
    print("✓ zos_util is available")
    
    # Show zos_util module
    if converter.zos_util:
        print(f"  zos_util module: {converter.zos_util}")
        print(f"  Available functions: {dir(converter.zos_util)}")
    
    # Create a test file
    test_file = "/tmp/chattr_test.txt"
    with open(test_file, 'w') as f:
        f.write("test\n")
    print(f"\nCreated test file: {test_file}")
    
    print("\nAttempting to set CCSID using zos_util...")
    success = converter.set_file_tag_zos_util(test_file, 1047, text_flag=True, verbose=True)
    
    if success:
        print("\n✓ zos_util worked successfully!")
        print("  The code should now use zos_util instead of chtag")
    else:
        print("\n✗ zos_util failed")
        print("  This explains why chtag fallback is being used")
    
    # Cleanup
    os.unlink(test_file)
    print(f"\nCleaned up test file")
    
except ImportError as e:
    print(f"\n✗ Could not import converter module: {e}")
    print("  Make sure the package is installed or in PYTHONPATH")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Error during test: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to cleanup
    if os.path.exists(test_file):
        os.unlink(test_file)
    sys.exit(1)

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
try:
    if converter.ZOS_UTIL_AVAILABLE and success:
        print("✓ zos_util is working correctly")
        print("  chtag fallback should not occur")
    else:
        print("✗ zos_util is not working")
        print("  chtag fallback will continue to be used")
except:
    print("✗ Could not determine status")
print("="*70)

# Made with Bob
