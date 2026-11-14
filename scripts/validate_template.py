#!/usr/bin/env python3
"""
Template Validation Script
Validates the structure and integrity of the University of Melbourne Typst thesis template.
"""

import os
import sys
import tomllib
from pathlib import Path
import re

def validate_directory_structure():
    """Validate that all required directories exist."""
    required_dirs = [
        'utils',
        'pages',
        'layouts',
        'assets',
        'assets/logos',
        'assets/colors',
        'assets/fonts',
        'docs',
        '.github/workflows'
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False

    print("✅ Directory structure is valid")
    return True

def validate_required_files():
    """Validate that all required files exist."""
    required_files = [
        'thesis.typ',
        'lib.typ',
        'typst.toml',
        'README.md',
        'utils/style.typ',
        'pages/title.typ',
        'pages/abstract.typ',
        'pages/declaration.typ',
        'layouts/document.typ',
        'assets/colors/unimelb-colors.typ'
    ]
    
    optional_files = [
        'assets/logos/unimelb-logo-official.svg'
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.isfile(file_path):
            missing_files.append(file_path)

    missing_optional = []
    for file_path in optional_files:
        if not os.path.isfile(file_path):
            missing_optional.append(file_path)

    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    if missing_optional:
        print(f"⚠️  Missing optional files: {missing_optional}")
        print(f"   (See assets/logos/README.md for instructions)")

    print("✅ Required files are present")
    return True

def validate_typst_toml():
    """Parse TOML and require nonempty package metadata, not matching comments."""
    try:
        with open('typst.toml', 'rb') as f:
            manifest = tomllib.load(f)

        package = manifest.get('package')
        if not isinstance(package, dict):
            print("❌ Missing [package] table in typst.toml")
            return False

        for field in ('name', 'version', 'entrypoint'):
            value = package.get(field)
            if not isinstance(value, str) or not value.strip():
                print(f"❌ Package field '{field}' must be a non-empty string")
                return False

        print("✅ typst.toml is valid")
        return True
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        print(f"❌ Error reading typst.toml: {exc}")
        return False

def validate_color_definitions():
    """Validate color definitions in the assets."""
    try:
        with open('assets/colors/unimelb-colors.typ', 'r') as f:
            content = f.read()

        # Check for primary brand color (in Typst syntax)
        if 'traditional-heritage-100 = rgb("#000F46")' not in content and \
           'traditional-heritage-100 = rgb("000F46")' not in content:
            print("❌ Primary brand color not found in color definitions")
            return False

        print("✅ Color definitions are valid")
        return True
    except Exception as e:
        print(f"❌ Error reading color definitions: {e}")
        return False

def validate_typst_syntax():
    """Basic validation of Typst files for common syntax issues."""
    typst_files = list(Path('.').rglob('*.typ'))

    warnings = []
    
    for file_path in typst_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Remove code blocks, math expressions, and strings to avoid counting delimiters inside them
            import re
            content_no_blocks = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)
            content_no_math = re.sub(r'\$[^$]*\$', '', content_no_blocks, flags=re.DOTALL)
            content_no_strings = re.sub(r'"[^"]*"', '', content_no_math)
            content_no_strings = re.sub(r"'[^']*'", '', content_no_strings)
            
            # Check for obviously unmatched braces, brackets, and parentheses
            # Note: This is a basic check and may produce false positives due to complex Typst syntax
            if content_no_strings.count('{') != content_no_strings.count('}'):
                warnings.append(f"Possible unmatched braces: {file_path}")
            
            if content_no_strings.count('[') != content_no_strings.count(']'):
                warnings.append(f"Possible unmatched brackets: {file_path}")
            
            if content_no_strings.count('(') != content_no_strings.count(')'):
                warnings.append(f"Possible unmatched parentheses: {file_path}")

        except Exception as e:
            warnings.append(f"Error reading {file_path}: {e}")

    if warnings:
        print("⚠️  Typst syntax warnings (may include false positives):")
        for warning in warnings:
            print(f"  - {warning}")
        print("   Note: These are basic checks that may not account for all Typst syntax.")
        print("   Run 'typst compile' to verify actual syntax correctness.")

    print("✅ Typst syntax validation completed")
    return True

def main():
    """Run all validation checks."""
    print("🔍 Validating University of Melbourne Typst Thesis Template")
    print("=" * 60)

    checks = [
        validate_directory_structure,
        validate_required_files,
        validate_typst_toml,
        validate_color_definitions,
        validate_typst_syntax
    ]

    results = []
    for check in checks:
        results.append(check())
        print()

    passed = sum(results)
    total = len(results)

    print("=" * 60)
    print(f"Validation Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All validation checks passed!")
        return 0
    else:
        print("❌ Some validation checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
