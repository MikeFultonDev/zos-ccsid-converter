#!/usr/bin/env python3
"""
Command-line interface for zos-ccsid-converter.
"""

import sys
import argparse
from .converter import (
    get_file_tag_info,
    convert_to_ebcdic_fcntl,
    convert_stream_to_ebcdic,
    set_file_tag_fcntl,
    CCSID_IBM1047,
)


def main():
    """Command-line interface for the CCSID converter"""
    parser = argparse.ArgumentParser(
        description='Convert files to EBCDIC using z/OS fcntl',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a file
  zos-ccsid-converter input.txt output.txt
  
  # Get file encoding info
  zos-ccsid-converter --info input.txt
  
  # Convert with verbose output
  zos-ccsid-converter -v input.txt output.txt
  
  # Convert from stdin to file
  cat input.txt | zos-ccsid-converter --stdin output.txt
"""
    )
    
    parser.add_argument('input', nargs='?', help='Input file path (or output file when using --stdin)')
    parser.add_argument('output', nargs='?', help='Output file path')
    parser.add_argument('--info', action='store_true',
                       help='Show file encoding info only')
    parser.add_argument('--stdin', action='store_true',
                       help='Read from stdin instead of file')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.info:
        if not args.input:
            print("ERROR: Input file required for --info", file=sys.stderr)
            return 1
        
        info = get_file_tag_info(args.input, verbose=args.verbose)
        if info:
            print(f"File: {args.input}")
            print(f"  CCSID: {info.ccsid}")
            print(f"  Encoding: {info.encoding_name}")
            print(f"  Text: {info.text_flag}")
            return 0
        else:
            print(f"ERROR: Could not get file tag info for {args.input}", 
                  file=sys.stderr)
            return 1
    
    elif args.stdin:
        # When using --stdin, the first positional argument is the output file
        output_file = args.input
        if not output_file:
            print("ERROR: Output file required with --stdin", file=sys.stderr)
            return 1
        
        with open(output_file, 'wb') as f_out:
            stats = convert_stream_to_ebcdic(
                sys.stdin.buffer,
                f_out,
                source_encoding='iso8859-1',
                verbose=args.verbose
            )
        
        if stats['success']:
            # Tag output file
            set_file_tag_fcntl(output_file, CCSID_IBM1047, verbose=args.verbose)
            print(f"Converted {stats['bytes_read']} bytes from stdin to {output_file}")
            return 0
        else:
            print(f"ERROR: {stats['error_message']}", file=sys.stderr)
            return 1
    
    else:
        if not args.input or not args.output:
            print("ERROR: Both input and output files required", file=sys.stderr)
            parser.print_help()
            return 1
        
        stats = convert_to_ebcdic_fcntl(args.input, args.output, verbose=args.verbose)
        
        if stats['success']:
            print(f"Conversion successful: {stats['bytes_read']} bytes -> {stats['bytes_written']} bytes")
            return 0
        else:
            print(f"ERROR: {stats['error_message']}", file=sys.stderr)
            return 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
