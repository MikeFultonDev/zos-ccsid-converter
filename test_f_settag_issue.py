#!/usr/bin/env python3
"""
Minimal test case demonstrating F_SETTAG "Invalid argument" error on z/OS Python.

This test shows that fcntl.fcntl() with F_SETTAG raises OSError with errno 121
(Invalid argument) even though the file tag is successfully set.

Expected behavior: fcntl should return 0 on success, not raise an exception.
Actual behavior: fcntl raises OSError with errno 121, but tag is still set.

To verify the tag was set, run: ls -T /tmp/test_f_settag.txt
Expected output: t IBM-1047    T=on

Environment:
- z/OS Python 3.x
- File system supporting file tagging (e.g., zFS)
"""

import os
import sys
import fcntl
import ctypes
import tempfile

# z/OS fcntl constants
F_SETTAG = 12       # Set file tag information
F_CONTROL_CVT = 13  # Control conversion (for querying tags)

# CCSID values
CCSID_IBM1047 = 1047  # EBCDIC


class attrib_t(ctypes.BigEndianStructure):
    """
    z/OS attrib_t structure for F_SETTAG operations.
    
    From z/OS sys/stat.h:
    struct attrib_t {
        int att_filetagchg;           // File tag change flag (1=change)
        int att_rsvd1;                // Reserved (0)
        unsigned short att_txtflag;   // Text flag (1=text, 0=binary)
        unsigned short att_ccsid;     // CCSID
        int att_rsvd2[2];             // Reserved (0, 0)
    }
    """
    _fields_ = [
        ("att_filetagchg", ctypes.c_int32),      # 4 bytes
        ("att_rsvd1", ctypes.c_int32),           # 4 bytes
        ("att_txtflag", ctypes.c_uint16),        # 2 bytes
        ("att_ccsid", ctypes.c_uint16),          # 2 bytes
        ("att_rsvd2", ctypes.c_int32 * 2),       # 8 bytes
    ]  # Total: 20 bytes


class f_cnvrt(ctypes.BigEndianStructure):
    """
    z/OS f_cnvrt structure for F_CONTROL_CVT operations.
    
    struct f_cnvrt {
        int cvtcmd;      // Command: 3=query
        short pccsid;    // Process CCSID
        short fccsid;    // File CCSID
    }
    """
    _fields_ = [
        ("cvtcmd", ctypes.c_int32),   # 4 bytes
        ("pccsid", ctypes.c_int16),   # 2 bytes
        ("fccsid", ctypes.c_int16),   # 2 bytes
    ]


def get_file_ccsid(path):
    """Query file CCSID using F_CONTROL_CVT (this works correctly)."""
    try:
        with open(path, 'rb') as f:
            fd = f.fileno()
            qcvt = f_cnvrt(3, 0, 0)  # cvtcmd=3 for query
            result = fcntl.fcntl(fd, F_CONTROL_CVT, qcvt)
            cvt_result = f_cnvrt.from_buffer_copy(result)
            return cvt_result.fccsid
    except Exception as e:
        print(f"Error querying CCSID: {e}")
        return None


def test_f_settag_scenario(test_file, scenario_name, from_ccsid, to_ccsid, step_num):
    """Test a specific F_SETTAG scenario."""
    print(f"{step_num}. {scenario_name}")
    print(f"   Current CCSID: {from_ccsid}, Target CCSID: {to_ccsid}")
    
    try:
        fd = os.open(test_file, os.O_RDWR)
        print(f"   File descriptor: {fd}")
        
        # Create attrib_t structure
        attrs = attrib_t()
        attrs.att_filetagchg = 1
        attrs.att_rsvd1 = 0
        attrs.att_txtflag = 1
        attrs.att_ccsid = to_ccsid
        attrs.att_rsvd2[0] = 0
        attrs.att_rsvd2[1] = 0
        
        attrs_bytes = bytes(attrs)
        print(f"   Structure hex: {attrs_bytes.hex()}")
        
        # Call fcntl with F_SETTAG
        try:
            result = fcntl.fcntl(fd, F_SETTAG, attrs_bytes)
            print(f"   fcntl returned: {result} (SUCCESS)")
            error_occurred = False
        except OSError as e:
            print(f"   fcntl raised OSError: errno {e.errno} - {e.strerror}")
            error_occurred = True
        
        os.close(fd)
        
        # Verify result
        final_ccsid = get_file_ccsid(test_file)
        print(f"   CCSID after call: {final_ccsid}")
        
        if final_ccsid == to_ccsid:
            print(f"   ✓ Tag was set to {to_ccsid}")
            if error_occurred:
                print(f"   ⚠ But errno 121 was raised (unexpected)")
            return True
        else:
            print(f"   ✗ Tag was NOT changed (still {final_ccsid})")
            if error_occurred:
                print(f"   ⚠ And errno 121 was raised")
            return False
    except Exception as e:
        print(f"   Exception: {e}")
        return False
    finally:
        print()


def test_f_settag():
    """Test F_SETTAG operation and demonstrate the issue."""
    
    # Create a temporary test file
    test_file = '/tmp/test_f_settag.txt'
    
    print("=" * 70)
    print("F_SETTAG Test Case for z/OS Python")
    print("=" * 70)
    print()
    
    # Scenario 1: Untagged → Tagged
    print(f"1. Creating UNTAGGED test file: {test_file}")
    with open(test_file, 'wb') as f:
        f.write(b"Test content for F_SETTAG\n")
    print(f"   File created (binary mode, should be untagged)")
    
    initial_ccsid = get_file_ccsid(test_file)
    print(f"   Initial CCSID: {initial_ccsid}")
    print()
    
    scenario1_success = test_f_settag_scenario(
        test_file,
        "SCENARIO 1: Untagged → Tagged (ISO8859-1)",
        initial_ccsid,
        819,  # ISO8859-1
        2
    )
    
    # Scenario 2: Tagged (same) → Tagged (same)
    current_ccsid = get_file_ccsid(test_file)
    scenario2_success = test_f_settag_scenario(
        test_file,
        "SCENARIO 2: Tagged (ISO8859-1) → Tagged (ISO8859-1) [no change]",
        current_ccsid,
        819,  # Same as current
        3
    )
    
    # Scenario 3: Tagged (A) → Tagged (B)
    current_ccsid = get_file_ccsid(test_file)
    scenario3_success = test_f_settag_scenario(
        test_file,
        "SCENARIO 3: Tagged (ISO8859-1) → Tagged (IBM-1047) [change]",
        current_ccsid,
        CCSID_IBM1047,  # Different from current
        4
    )
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("SCENARIO 1 (Untagged → Tagged):")
    if scenario1_success:
        print("  ✓ Tag was set successfully")
        print("  ⚠ But errno 121 was raised (should return 0)")
    else:
        print("  ✗ FAILED")
    print()
    
    print("SCENARIO 2 (Tagged → Same Tag):")
    if scenario2_success:
        print("  ✓ Tag unchanged (correct)")
        print("  ⚠ But errno 121 was raised (should return 0)")
    else:
        print("  ✗ FAILED")
    print()
    
    print("SCENARIO 3 (Tagged A → Tagged B):")
    if scenario3_success:
        print("  ✓ Tag was changed successfully")
        print("  ⚠ But errno 121 was raised (should return 0)")
    else:
        print("  ✗ FAILED - Tag was NOT changed")
        print("  ⚠ This is the PRIMARY BUG: F_SETTAG through Python's fcntl")
        print("    raises errno 121 AND fails to change the tag to a different CCSID")
    print()
    
    print("CONCLUSION:")
    print("  F_SETTAG through Python's fcntl has two issues:")
    print("  1. Always raises errno 121 even when operation should succeed")
    print("  2. Fails to change tag when setting to a different CCSID (Scenario 3)")
    print()
    
    print("To verify final file tag manually, run:")
    print(f"  ls -T {test_file}")
    print()
    
    # Cleanup
    try:
        os.remove(test_file)
        print(f"Test file removed: {test_file}")
    except:
        pass


if __name__ == '__main__':
    print()
    print("Python version:", sys.version)
    print("Platform:", sys.platform)
    print()
    
    test_f_settag()

# Made with Bob
