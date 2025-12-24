#!/usr/bin/env python3
"""
Command-line interface for zos-ccsid-converter.
"""

import sys
import argparse
from . import __version__
from .converter import (
    get_file_tag_info,
    get_file_encoding,
    convert_to_ebcdic,
    convert_stream_to_ebcdic,
    set_file_tag,
    CCSID_IBM1047,
    ENCODING_MAP,
)


def main():
    """Command-line interface for the CCSID converter"""
    parser = argparse.ArgumentParser(
        description='Convert files to EBCDIC using z/OS file tagging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='zos-ccsid-converter',
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
  
  # Get encoding info from stdin
  cat input.txt | zos-ccsid-converter --info --stdin
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
    parser.add_argument('--version', action='version',
                       version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    if args.info:
        if args.stdin:
            # Get info from stdin using /dev/stdin path
            # zos-util supports named pipes and special files
            try:
                encoding = get_file_encoding("/dev/stdin", verbose=args.verbose)
                
                # Map encoding to CCSID for display
                ccsid = None
                for ccsid_val, enc_name in ENCODING_MAP.items():
                    if enc_name == encoding:
                        ccsid = ccsid_val
                        break
                
                print("Source: stdin")
                print(f"  CCSID: {ccsid if ccsid is not None else 'unknown'}")
                print(f"  Encoding: {encoding}")
                return 0
            except Exception as e:
                print(f"ERROR: Could not get tag info from stdin: {e}", file=sys.stderr)
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                return 1
        else:
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
            set_file_tag(output_file, CCSID_IBM1047, verbose=args.verbose)
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
        stats = convert_to_ebcdic(args.input, args.output, verbose=args.verbose)
        
        
        if stats['success']:
            print(f"Conversion successful: {stats['bytes_read']} bytes -> {stats['bytes_written']} bytes")
            return 0
        else:
            print(f"ERROR: {stats['error_message']}", file=sys.stderr)
            return 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
