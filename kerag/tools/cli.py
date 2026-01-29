#!/usr/bin/env python3
"""
KERAG Tool Command Line Interface

Provides various utility tools
"""

import sys
import argparse
from pathlib import Path

# Add KERAG root directory to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from kerag.tools.md_split import split_markdown
from kerag.tools.pack import pack_module


def cmd_split(args):
    """Execute document splitting command"""
    try:
        result = split_markdown(
            file_path=Path(args.file),
            split_level=args.level,
            output_dir=Path(args.output),
            all_labeled=args.all_labeled
        )

        print(f"✓ Document splitting completed")
        print(f"  - Main file: {result['main_file']}")
        print(f"  - Sub-files count: {result['total_sub_files']}")
        print(f"  - Total lines: {result['total_lines_processed']}")
        print(f"\nGenerated sub-files:")
        for sub in result['sub_files']:
            print(f"  - {sub['file']} ({sub['lines']} lines)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def add_split_parser_args(parser):
    """Add arguments for split command"""
    parser.add_argument('file', help='Input Markdown file')
    parser.add_argument('-o', '--output', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('-l', '--level', type=int, default=3,
                       help='Split level (default: 3, meaning split from ###)')
    parser.add_argument('--all-labeled', action='store_true',
                       help='Add [@label] tag to all headings')


def add_pack_parser_args(parser):
    """Add arguments for pack command"""
    parser.add_argument('module_dir', help='Module directory to pack')
    parser.add_argument('-o', '--output', help='Output filename or path')
    parser.add_argument('--meta', help='Path to kerag_meta.txt file')
    parser.add_argument('--name', help='Module name (overrides detected)')
    parser.add_argument('--version', help='Module version')
    parser.add_argument('--description', help='Module description')


def cmd_pack(args):
    """Execute module pack command"""
    try:
        success, result = pack_module(
            module_dir=args.module_dir,
            meta_file=args.meta,
            name=args.name,
            version=args.version,
            description=args.description,
            output_path=args.output
        )

        if success:
            print(f"✓ Module packaging completed")
            print(f"  - Output file: {result}")
        else:
            print(f"✗ Packaging failed: {result}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main command entry"""
    parser = argparse.ArgumentParser(
        prog='kerag',
        description='KERAG Utility Tools'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # tools subcommand
    tools_parser = subparsers.add_parser(
        'tools',
        help='KERAG tools related commands'
    )
    tools_subparsers = tools_parser.add_subparsers(dest='tools_command', help='Tool commands')

    # split subcommand (under tools)
    split_parser = tools_subparsers.add_parser(
        'split',
        help='Split Markdown documents'
    )
    split_parser.add_argument('file', help='Input Markdown file')
    split_parser.add_argument('-o', '--output', default='output',
                             help='Output directory (default: output)')
    split_parser.add_argument('-l', '--level', type=int, default=3,
                             help='Split level (default: 3, meaning split from ###)')
    split_parser.add_argument('--all-labeled', action='store_true',
                             help='Add [@label] tag to all headings')
    split_parser.set_defaults(func=cmd_split)

    # pack subcommand (under tools)
    pack_parser = tools_subparsers.add_parser(
        'pack',
        help='Pack knowledge modules into distributable tar files'
    )
    pack_parser.add_argument('module_dir', help='Module directory to pack')
    pack_parser.add_argument('--meta', help='Path to kerag_meta.txt file')
    pack_parser.add_argument('--name', help='Module name (overrides detected)')
    pack_parser.add_argument('--version', help='Module version')
    pack_parser.add_argument('--description', help='Module description')
    pack_parser.set_defaults(func=cmd_pack)

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'tools':
        if not args.tools_command:
            tools_parser.print_help()
            sys.exit(1)
        # 执行tools子命令
        args.func(args)
    else:
        # 执行其他主命令
        args.func(args)


if __name__ == "__main__":
    main()
