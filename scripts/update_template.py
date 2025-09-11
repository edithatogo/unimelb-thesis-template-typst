#!/usr/bin/env python3
"""
Typst Template Update Script
Helps update the University of Melbourne thesis template to newer Typst versions.
"""

import os
import sys
import re
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any

class TypstTemplateUpdater:
    def __init__(self, template_dir: str = "."):
        self.template_dir = Path(template_dir)
        self.typst_files = list(self.template_dir.rglob("*.typ"))
        self.toml_file = self.template_dir / "typst.toml"

    def get_current_typst_version(self) -> Optional[str]:
        """Get the current Typst version from typst.toml."""
        if not self.toml_file.exists():
            return None

        with open(self.toml_file, 'r') as f:
            content = f.read()

        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        return match.group(1) if match else None

    def check_typst_updates(self) -> Dict[str, Any]:
        """Check for available Typst updates."""
        try:
            # This would typically query the Typst release API
            # For now, we'll simulate checking for updates
            current = self.get_current_typst_version()
            if current:
                print(f"Current Typst version: {current}")
                print("Checking for updates...")

                # Simulate version check
                latest = "0.13.0"  # This would come from API
                if current != latest:
                    return {"current": current, "latest": latest, "update_available": True}
                else:
                    return {"current": current, "latest": latest, "update_available": False}
            else:
                print("Could not determine current Typst version")
                return {}
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return {}

    def update_package_versions(self) -> List[str]:
        """Update package versions in template files."""
        updates = []

        # Package version mappings for common updates
        package_updates = {
            "@preview/cetz:0.2.": "@preview/cetz:0.3.1",
            "@preview/codly:1.0.": "@preview/codly:1.1.0",
            "@preview/theorion:0.3.": "@preview/theorion:0.4.0",
        }

        for file_path in self.typst_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                original_content = content
                for old_version, new_version in package_updates.items():
                    if old_version in content:
                        content = content.replace(old_version, new_version)
                        updates.append(f"Updated {old_version} to {new_version} in {file_path}")

                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)

            except Exception as e:
                print(f"Error updating {file_path}: {e}")

        return updates

    def update_deprecated_syntax(self) -> List[str]:
        """Update deprecated Typst syntax."""
        updates = []

        deprecated_patterns = [
            (r'regex\("\\s+"\)', r'regex("\\\\s+")'),  # Fix regex syntax
            (r'#let\s+counter\(', r'#let counter('),     # Counter syntax updates
        ]

        for file_path in self.typst_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                original_content = content
                for old_pattern, new_pattern in deprecated_patterns:
                    content = re.sub(old_pattern, new_pattern, content)
                    if content != original_content:
                        updates.append(f"Updated deprecated syntax in {file_path}")

                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)

            except Exception as e:
                print(f"Error updating syntax in {file_path}: {e}")

        return updates

    def backup_template(self) -> bool:
        """Create a backup of the current template."""
        try:
            import shutil
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.template_dir.parent / f"template_backup_{timestamp}"

            shutil.copytree(self.template_dir, backup_dir)
            print(f"Backup created: {backup_dir}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def test_compilation(self) -> bool:
        """Test that the template still compiles after updates."""
        try:
            result = subprocess.run(
                ["typst", "compile", "thesis.typ"],
                cwd=self.template_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✅ Template compiles successfully")
                return True
            else:
                print("❌ Compilation failed:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("❌ Compilation timed out")
            return False
        except FileNotFoundError:
            print("❌ Typst not found. Please install Typst first.")
            return False

    def update_typst_toml(self, new_version: str) -> bool:
        """Update the Typst version in typst.toml."""
        if not self.toml_file.exists():
            print("❌ typst.toml not found")
            return False

        try:
            with open(self.toml_file, 'r') as f:
                content = f.read()

            # Update version
            content = re.sub(
                r'version\s*=\s*"[^"]*"',
                f'version = "{new_version}"',
                content
            )

            with open(self.toml_file, 'w') as f:
                f.write(content)

            print(f"✅ Updated Typst version to {new_version}")
            return True

        except Exception as e:
            print(f"❌ Error updating typst.toml: {e}")
            return False

def main():
    """Main update function."""
    print("🔄 University of Melbourne Typst Template Updater")
    print("=" * 50)

    updater = TypstTemplateUpdater()

    # Check for updates
    version_info = updater.check_typst_updates()
    if version_info.get("update_available"):
        print(f"📦 Update available: {version_info['current']} → {version_info['latest']}")

        # Ask user if they want to proceed
        response = input("Do you want to update the template? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Update cancelled.")
            return 0

        # Create backup
        if not updater.backup_template():
            print("❌ Backup failed. Aborting update.")
            return 1

        # Perform updates
        print("\n🔄 Performing updates...")

        # Update Typst version
        if version_info.get("latest"):
            updater.update_typst_toml(version_info["latest"])

        # Update packages
        package_updates = updater.update_package_versions()
        if package_updates:
            print("📦 Package updates:")
            for update in package_updates:
                print(f"  • {update}")

        # Update deprecated syntax
        syntax_updates = updater.update_deprecated_syntax()
        if syntax_updates:
            print("🔧 Syntax updates:")
            for update in syntax_updates:
                print(f"  • {update}")

        # Test compilation
        print("\n🧪 Testing compilation...")
        if updater.test_compilation():
            print("\n🎉 Template update completed successfully!")
            print("Please review the changes and test your thesis compilation.")
        else:
            print("\n❌ Template update completed but compilation failed.")
            print("Please check the error messages above and fix any issues.")

    else:
        print("✅ Template is up to date")

        # Still perform maintenance updates
        print("\n🔧 Performing maintenance updates...")
        package_updates = updater.update_package_versions()
        syntax_updates = updater.update_deprecated_syntax()

        if package_updates or syntax_updates:
            print("📦 Maintenance updates applied:")
            for update in package_updates + syntax_updates:
                print(f"  • {update}")

            if updater.test_compilation():
                print("✅ Maintenance updates completed successfully")
            else:
                print("❌ Maintenance updates completed but compilation failed")
        else:
            print("✅ No maintenance updates needed")

    return 0

if __name__ == '__main__':
    sys.exit(main())
