# Package Location Note

This package was moved from the CBSA project to its own standalone location because it is a general-purpose z/OS utility, not specific to the CICS Banking Sample Application.

## Original Location
`cics-banking-sample-application-cbsa/etc/install/base/uss_build/zos_ebcdic_converter/`

## Current Location
`/Users/fultonm/Documents/Development/zos_ccsid_converter/`

## Reason for Move
The z/OS EBCDIC converter is a general-purpose utility for converting files between ASCII (ISO8859-1) and EBCDIC (IBM-1047) encodings on z/OS systems. It can be used by any z/OS project, not just CBSA.

By placing it in its own directory, it can be:
- Developed independently
- Versioned separately
- Distributed to customers as a standalone package
- Used by multiple projects

## Original Files Preserved
The original implementation files remain in the CBSA project at:
`cics-banking-sample-application-cbsa/etc/install/base/uss_build/bin/`
- `ebcdic_converter_fcntl.py`
- `test_ebcdic_converter.py`
- `example_service_usage.py`
- `README_ebcdic_converter.md`

These can be used as reference or for backward compatibility.