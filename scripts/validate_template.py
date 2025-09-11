#!/usr/bin/env python3
"""
Template Validation Script
Validates the structure and integrity of the University of Melbourne Typst thesis template.
"""

import os
import sys
import yaml
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
        'assets/logos/unimelb-logo-official.svg',
        'assets/colors/unimelb-colors.typ'
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.isfile(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    print("✅ Required files are present")
    return True

def validate_typst_toml():
    """Validate typst.toml configuration."""
    try:
        with open('typst.toml', 'r') as f:
            content = f.read()

        # Check for required fields
        required_fields = ['name', 'version', 'entrypoint']
        for field in required_fields:
            if f'{field} =' not in content:
                print(f"❌ Missing required field in typst.toml: {field}")
                return False

        print("✅ typst.toml is valid")
        return True
    except Exception as e:
        print(f"❌ Error reading typst.toml: {e}")
        return False

def validate_color_definitions():
    """Validate color definitions in the assets."""
    try:
        with open('assets/colors/unimelb-colors.typ', 'r') as f:
            content = f.read()

        # Check for primary brand color
        if 'traditional-heritage-100: #000F46' not in content:
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

    issues = []
    for file_path in typst_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Check for common syntax issues
            if '#import(' in content and not content.count('#import(') == content.count(')'):
                issues.append(f"Unmatched parentheses in imports: {file_path}")

            if '#let' in content and not content.count('#let') == content.count('='):
                issues.append(f"Potential let binding issues: {file_path}")

        except Exception as e:
            issues.append(f"Error reading {file_path}: {e}")

    if issues:
        print("❌ Typst syntax issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✅ Typst syntax validation passed")
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
