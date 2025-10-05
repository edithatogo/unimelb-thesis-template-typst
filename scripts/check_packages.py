#!/usr/bin/env python3
"""
Package Version Checker
Checks for outdated Typst packages and suggests updates.
"""

import os
import sys
import requests
import re
from pathlib import Path

def check_typst_packages():
    """Check for Typst packages used in the template."""
    packages = {}

    # Scan all .typ files for package imports
    typst_files = list(Path('.').rglob('*.typ'))

    for file_path in typst_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Find package imports
            import_pattern = r'#import "@preview/([^:]+):([^"]+)"'
            matches = re.findall(import_pattern, content)

            for package, version in matches:
                if package not in packages:
                    packages[package] = version
                elif packages[package] != version:
                    print(f"⚠️  Version mismatch for {package}: {packages[package]} vs {version}")

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return packages

def check_package_updates(packages):
    """Check if packages have newer versions available."""
    print("🔍 Checking for package updates...")

    updates_available = []

    for package, current_version in packages.items():
        try:
            # This is a simplified check - in practice you'd query the Typst package registry
            print(f"📦 {package}: {current_version} (checking...)")

            # For now, just report current versions
            # In a real implementation, you'd check against the Typst preview registry

        except Exception as e:
            print(f"❌ Error checking {package}: {e}")

    return updates_available

def validate_package_usage():
    """Validate that packages are used correctly."""
    issues = []

    # Check for common package usage issues
    typst_files = list(Path('.').rglob('*.typ'))

    for file_path in typst_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Check for unused imports (simplified check)
            imports = re.findall(r'#import "@preview/([^:]+):([^"]+)"', content)
            used_packages = set()

            for package, _ in imports:
                if package in content:
                    used_packages.add(package)

            for package, _ in imports:
                if package not in used_packages:
                    issues.append(f"Potentially unused import: {package} in {file_path}")

        except Exception as e:
            issues.append(f"Error analyzing {file_path}: {e}")

    return issues

def main():
    """Main package checking function."""
    print("📦 Checking Typst Package Versions")
    print("=" * 40)

    # Check packages
    packages = check_typst_packages()

    if not packages:
        print("❌ No packages found in the template")
        # Consider this an error for CI so maintainers notice missing imports
        return 2

    print(f"Found {len(packages)} packages:")
    for package, version in packages.items():
        print(f"  • {package}: {version}")

    print()

    # Check for updates
    updates = check_package_updates(packages)

    print()

    # Validate usage
    issues = validate_package_usage()

    if issues:
        print("⚠️  Package usage issues:")
        for issue in issues:
            print(f"  - {issue}")
        # Return non-zero so CI can fail the job and require fixes
        return 3
    else:
        print("✅ No package usage issues found")

    print()
    print("=" * 40)
    print("Package check complete!")

    return 0

if __name__ == '__main__':
    sys.exit(main())
