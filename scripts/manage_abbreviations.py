#!/usr/bin/env python3
"""
Abbreviation Management Utility for University of Melbourne Thesis Template

This script provides command-line tools for managing abbreviations in the Typst thesis template.
It can add, remove, validate, and export abbreviations from the config/abbreviations.typ file.

Usage:
    python manage_abbreviations.py [command] [options]

Commands:
    add         Add a new abbreviation
    remove      Remove an abbreviation
    list        List all abbreviations
    validate    Validate abbreviations file
    export      Export abbreviations to different formats
    import      Import abbreviations from CSV/JSON
    stats       Show abbreviation statistics

Examples:
    python manage_abbreviations.py add --key "Machine Learning" --short "ML" --long "A method of data analysis..."
    python manage_abbreviations.py list --sort short
    python manage_abbreviations.py validate
    python manage_abbreviations.py export --format csv --output abbreviations.csv
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AbbreviationManager:
    """Manages abbreviations in the Typst template."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.abbreviations = []
        self.load_abbreviations()

    def load_abbreviations(self) -> None:
        """Load abbreviations from the Typst config file."""
        if not self.config_path.exists():
            print(f"Error: Config file not found at {self.config_path}")
            return

        content = self.config_path.read_text()

        # Extract the abbreviations array using regex
        # Match from #let abbreviations = ( to the closing ) followed by newline
        array_match = re.search(r'#let abbreviations = \((.*?)\)\s*$', content, re.MULTILINE | re.DOTALL)
        if not array_match:
            print("Error: Could not find abbreviations array in config file")
            return

        array_content = array_match.group(1)

        # Parse individual entries
        entries = []
        current_entry = {}
        in_entry = False
        paren_depth = 0

        lines = array_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            if line.startswith('('):
                in_entry = True
                current_entry = {}
                paren_depth = 0

            if in_entry:
                paren_depth += line.count('(') - line.count(')')

                # Extract key-value pairs
                key_match = re.search(r'key:\s*"([^"]*)"', line)
                short_match = re.search(r'short:\s*"([^"]*)"', line)
                long_match = re.search(r'long:\s*"([^"]*)"', line)

                if key_match:
                    current_entry['key'] = key_match.group(1)
                if short_match:
                    current_entry['short'] = short_match.group(1)
                if long_match:
                    current_entry['long'] = long_match.group(1)

                if paren_depth == 0 and current_entry:
                    entries.append(current_entry)
                    current_entry = {}
                    in_entry = False

        self.abbreviations = entries

    def save_abbreviations(self) -> None:
        """Save abbreviations back to the config file."""
        if not self.config_path.exists():
            print(f"Error: Config file not found at {self.config_path}")
            return

        content = self.config_path.read_text()

        # Generate new abbreviations array
        abbr_lines = ['#let abbreviations = (']
        for entry in self.abbreviations:
            abbr_lines.append('  (')
            abbr_lines.append(f'    key: "{entry["key"]}",')
            abbr_lines.append(f'    short: "{entry["short"]}",')
            abbr_lines.append(f'    long: "{entry["long"]}"')
            abbr_lines.append('  ),')
        abbr_lines.append(')')

        new_abbreviations = '\n'.join(abbr_lines)

        # Replace the old abbreviations array
        pattern = r'#let abbreviations = \((.*?)\)'
        new_content = re.sub(pattern, new_abbreviations, content, flags=re.DOTALL)

        self.config_path.write_text(new_content)
        print(f"Saved {len(self.abbreviations)} abbreviations to {self.config_path}")

    def add_abbreviation(self, key: str, short: str, long_desc: str) -> bool:
        """Add a new abbreviation."""
        # Validate inputs
        if not key or not short:
            print("Error: Key and abbreviation are required")
            return False

        # Check for duplicates
        for abbr in self.abbreviations:
            if abbr['short'] == short:
                print(f"Error: Abbreviation '{short}' already exists")
                return False
            if abbr['key'] == key:
                print(f"Error: Key '{key}' already exists")
                return False

        # Validate abbreviation format
        if not re.match(r'^[A-Z]{2,8}$', short):
            print(f"Warning: Abbreviation '{short}' doesn't match recommended format (2-8 uppercase letters)")

        self.abbreviations.append({
            'key': key,
            'short': short,
            'long': long_desc
        })

        print(f"Added abbreviation: {key} ({short})")
        return True

    def remove_abbreviation(self, short: str) -> bool:
        """Remove an abbreviation by its short form."""
        for i, abbr in enumerate(self.abbreviations):
            if abbr['short'] == short:
                removed = self.abbreviations.pop(i)
                print(f"Removed abbreviation: {removed['key']} ({short})")
                return True

        print(f"Error: Abbreviation '{short}' not found")
        return False

    def list_abbreviations(self, sort_by: str = 'key', reverse: bool = False) -> None:
        """List all abbreviations."""
        if not self.abbreviations:
            print("No abbreviations found")
            return

        # Sort abbreviations
        sorted_abbr = sorted(self.abbreviations, key=lambda x: x[sort_by], reverse=reverse)

        print(f"{'Key':<30} {'Short':<10} {'Description'}")
        print("-" * 80)
        for abbr in sorted_abbr:
            desc = abbr['long'][:50] + "..." if len(abbr['long']) > 50 else abbr['long']
            print(f"{abbr['key']:<30} {abbr['short']:<10} {desc}")

    def validate_abbreviations(self) -> Tuple[List[str], List[str]]:
        """Validate abbreviations and return errors and warnings."""
        errors = []
        warnings = []

        shorts = [abbr['short'] for abbr in self.abbreviations]
        keys = [abbr['key'] for abbr in self.abbreviations]

        # Check for duplicates
        for i, short in enumerate(shorts):
            if shorts.count(short) > 1:
                errors.append(f"Duplicate abbreviation: {short}")

        for i, key in enumerate(keys):
            if keys.count(key) > 1:
                errors.append(f"Duplicate key: {key}")

        # Check for empty fields
        for abbr in self.abbreviations:
            if not abbr['key'].strip():
                errors.append("Empty key found")
            if not abbr['short'].strip():
                errors.append(f"Empty abbreviation for key: {abbr['key']}")
            if not abbr['long'].strip():
                warnings.append(f"Empty description for: {abbr['key']} ({abbr['short']})")

        # Check abbreviation format
        for abbr in self.abbreviations:
            if not re.match(r'^[A-Z]{2,8}$', abbr['short']):
                warnings.append(f"Non-standard abbreviation format: {abbr['short']}")

        return errors, warnings

    def get_statistics(self) -> Dict:
        """Get abbreviation statistics."""
        if not self.abbreviations:
            return {'total': 0}

        total = len(self.abbreviations)
        avg_key_len = sum(len(abbr['key']) for abbr in self.abbreviations) / total
        avg_short_len = sum(len(abbr['short']) for abbr in self.abbreviations) / total
        avg_long_len = sum(len(abbr['long']) for abbr in self.abbreviations) / total

        return {
            'total': total,
            'avg_key_length': round(avg_key_len, 1),
            'avg_abbrev_length': round(avg_short_len, 1),
            'avg_description_length': round(avg_long_len, 1)
        }

    def export_abbreviations(self, format_type: str, output_path: Optional[Path] = None) -> str:
        """Export abbreviations to different formats."""
        if format_type == 'csv':
            lines = ['Key,Abbreviation,Description']
            for abbr in self.abbreviations:
                # Escape quotes in CSV
                key = abbr['key'].replace('"', '""')
                short = abbr['short'].replace('"', '""')
                long_desc = abbr['long'].replace('"', '""')
                lines.append(f'"{key}","{short}","{long_desc}"')
            content = '\n'.join(lines)

        elif format_type == 'json':
            import json
            content = json.dumps(self.abbreviations, indent=2)

        else:
            raise ValueError(f"Unsupported format: {format_type}")

        if output_path:
            output_path.write_text(content)
            print(f"Exported {len(self.abbreviations)} abbreviations to {output_path}")
        else:
            print(content)

        return content


def main():
    parser = argparse.ArgumentParser(
        description="Manage abbreviations in University of Melbourne Thesis Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('command', choices=['add', 'remove', 'list', 'validate', 'export', 'import', 'stats'],
                       help='Command to execute')

    # Global options
    parser.add_argument('--config', type=Path, default=Path('config/abbreviations.typ'),
                       help='Path to abbreviations config file')

    # Add command options
    add_group = parser.add_argument_group('add command options')
    add_group.add_argument('--key', help='Full term/key')
    add_group.add_argument('--short', help='Abbreviation')
    add_group.add_argument('--long', help='Long description/definition')

    # Remove command options
    remove_group = parser.add_argument_group('remove command options')
    remove_group.add_argument('--abbrev', help='Abbreviation to remove', dest='remove_short')

    # List command options
    list_group = parser.add_argument_group('list command options')
    list_group.add_argument('--sort', choices=['key', 'short', 'long'], default='key',
                           help='Sort by field')
    list_group.add_argument('--reverse', action='store_true', help='Reverse sort order')

    # Export command options
    export_group = parser.add_argument_group('export command options')
    export_group.add_argument('--format', choices=['csv', 'json'], default='csv',
                             help='Export format')
    export_group.add_argument('--output', type=Path, help='Output file path')

    args = parser.parse_args()

    # Initialize manager
    config_path = args.config
    if not config_path.is_absolute():
        # Assume we're running from the repository root
        repo_root = Path(__file__).parent.parent
        config_path = repo_root / config_path

    manager = AbbreviationManager(config_path)

    # Execute command
    if args.command == 'add':
        if not all([args.key, args.short, args.long]):
            parser.error("add command requires --key, --short, and --long")
        success = manager.add_abbreviation(args.key, args.short, args.long)
        if success:
            manager.save_abbreviations()

    elif args.command == 'remove':
        if not args.remove_short:
            parser.error("remove command requires --short")
        success = manager.remove_abbreviation(args.remove_short)
        if success:
            manager.save_abbreviations()

    elif args.command == 'list':
        manager.list_abbreviations(args.sort, args.reverse)

    elif args.command == 'validate':
        errors, warnings = manager.validate_abbreviations()
        if errors:
            print("Validation Errors:")
            for error in errors:
                print(f"  - {error}")
        if warnings:
            print("Validation Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        if not errors and not warnings:
            print("All abbreviations validated successfully!")

    elif args.command == 'export':
        manager.export_abbreviations(args.format, args.output)

    elif args.command == 'stats':
        stats = manager.get_statistics()
        print("Abbreviation Statistics:")
        print(f"  Total abbreviations: {stats['total']}")
        if stats['total'] > 0:
            print(f"  Average key length: {stats['avg_key_length']}")
            print(f"  Average abbreviation length: {stats['avg_abbrev_length']}")
            print(f"  Average description length: {stats['avg_description_length']}")

    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == '__main__':
    main()