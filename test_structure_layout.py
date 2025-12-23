#!/usr/bin/env python3
"""
Test to verify ctypes structure layout matches z/OS C structures.
"""
import ctypes
import sys

# Test 1: file_tag structure
print("=" * 60)
print("Testing file_tag structure layout")
print("=" * 60)

class file_tag_v1(ctypes.Structure):
    """Version 1: Using c_uint32 for flags"""
    _fields_ = [
        ("ft_ccsid", ctypes.c_ushort),     # 2 bytes
        ("ft_flags", ctypes.c_uint32),     # 4 bytes
    ]

class file_tag_v2(ctypes.Structure):
    """Version 2: Using bit fields (if supported)"""
    _fields_ = [
        ("ft_ccsid", ctypes.c_ushort),     # 2 bytes
        ("ft_txtflag", ctypes.c_uint, 1),  # 1 bit
        ("ft_deferred", ctypes.c_uint, 1), # 1 bit
        ("ft_rsvflags", ctypes.c_uint, 14),# 14 bits
    ]

print(f"file_tag_v1 size: {ctypes.sizeof(file_tag_v1)} bytes")
print(f"file_tag_v2 size: {ctypes.sizeof(file_tag_v2)} bytes")
print(f"Expected size: 6 bytes (2 + 4)")

# Test setting values
tag1 = file_tag_v1()
tag1.ft_ccsid = 819
tag1.ft_flags = 0x80000000  # txtflag = 1

print(f"\nfile_tag_v1:")
print(f"  ft_ccsid = {tag1.ft_ccsid}")
print(f"  ft_flags = 0x{tag1.ft_flags:08x}")

try:
    tag2 = file_tag_v2()
    tag2.ft_ccsid = 819
    tag2.ft_txtflag = 1
    
    print(f"\nfile_tag_v2:")
    print(f"  ft_ccsid = {tag2.ft_ccsid}")
    print(f"  ft_txtflag = {tag2.ft_txtflag}")
    print(f"  ft_deferred = {tag2.ft_deferred}")
    print(f"  ft_rsvflags = {tag2.ft_rsvflags}")
    
    # Check if bit fields work
    print("\nBit fields are supported in ctypes!")
    print("Recommended: Use file_tag_v2 with bit fields")
except Exception as e:
    print(f"\nBit fields error: {e}")
    print("Recommended: Use file_tag_v1 with property accessors")

print("\n" + "=" * 60)

# Made with Bob
