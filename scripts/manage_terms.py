#!/usr/bin/env python3
"""
Abbreviation and Glossary Management Script
Helps manage abbreviations and glossary entries for the University of Melbourne thesis template.
"""

import json
import csv
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_typst_data(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a Typst file (simplified parsing for tuple arrays)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # This is a simplified parser - in practice, you might want to use a proper Typst parser
        # For now, we'll extract basic information
        return []

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def validate_abbreviations(abbrevs: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Validate abbreviation data structure."""
    errors = []
    warnings = []

    if not isinstance(abbrevs, list):
        errors.append("Abbreviations must be a list")
        return {"errors": errors, "warnings": warnings}

    for i, entry in enumerate(abbrevs):
        if not isinstance(entry, dict):
            errors.append(f"Entry {i} must be a dictionary")
            continue

        required_fields = ["key", "short", "long"]
        for field in required_fields:
            if field not in entry:
                errors.append(f"Entry {i} missing required field: {field}")
            elif not isinstance(entry[field], str) or not entry[field].strip():
                errors.append(f"Entry {i} field '{field}' must be a non-empty string")

        # Check for duplicate abbreviations
        for j, other in enumerate(abbrevs):
            if i != j and entry.get("short") == other.get("short"):
                errors.append(f"Duplicate abbreviation '{entry.get('short')}' in entries {i} and {j}")

    return {"errors": errors, "warnings": warnings}

def validate_glossary(glossary: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Validate glossary data structure."""
    errors = []
    warnings = []

    if not isinstance(glossary, list):
        errors.append("Glossary must be a list")
        return {"errors": errors, "warnings": warnings}

    for i, entry in enumerate(glossary):
        if not isinstance(entry, dict):
            errors.append(f"Entry {i} must be a dictionary")
            continue

        required_fields = ["term", "definition"]
        for field in required_fields:
            if field not in entry:
                errors.append(f"Entry {i} missing required field: {field}")
            elif not isinstance(entry[field], str) or not entry[field].strip():
                errors.append(f"Entry {i} field '{field}' must be a non-empty string")

        # Check for duplicate terms
        for j, other in enumerate(glossary):
            if i != j and entry.get("term") == other.get("term"):
                errors.append(f"Duplicate term '{entry.get('term')}' in entries {i} and {j}")

    return {"errors": errors, "warnings": warnings}

def export_to_csv(data: List[Dict[str, Any]], output_file: str, data_type: str = "abbreviations"):
    """Export data to CSV format."""
    if data_type == "abbreviations":
        fieldnames = ["key", "short", "long", "category"]
    else:  # glossary
        fieldnames = ["term", "definition", "category", "related"]

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for entry in data:
            row = {}
            for field in fieldnames:
                if field == "related" and field in entry:
                    row[field] = "; ".join(entry[field]) if isinstance(entry[field], list) else entry[field]
                else:
                    row[field] = entry.get(field, "")
            writer.writerow(row)

    print(f"Exported {len(data)} entries to {output_file}")

def import_from_csv(input_file: str, data_type: str = "abbreviations") -> List[Dict[str, Any]]:
    """Import data from CSV format."""
    data = []

    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            entry = {}
            for key, value in row.items():
                if key == "related" and value:
                    entry[key] = [term.strip() for term in value.split(";")]
                else:
                    entry[key] = value.strip() if value else ""

            # Ensure required fields are present
            if data_type == "abbreviations":
                if not all(entry.get(field) for field in ["key", "short", "long"]):
                    print(f"Warning: Skipping incomplete abbreviation entry: {entry}")
                    continue
            else:  # glossary
                if not all(entry.get(field) for field in ["term", "definition"]):
                    print(f"Warning: Skipping incomplete glossary entry: {entry}")
                    continue

            data.append(entry)

    print(f"Imported {len(data)} entries from {input_file}")
    return data

def generate_statistics(data: List[Dict[str, Any]], data_type: str = "abbreviations") -> Dict[str, Any]:
    """Generate statistics for the data."""
    if not data:
        return {}

    stats = {
        "total_entries": len(data),
        "avg_key_length": sum(len(entry.get("key", entry.get("term", ""))) for entry in data) / len(data),
        "avg_short_length": sum(len(entry.get("short", "")) for entry in data) / len(data) if data_type == "abbreviations" else 0,
        "avg_definition_length": sum(len(entry.get("long", entry.get("definition", ""))) for entry in data) / len(data),
    }

    if data_type == "abbreviations":
        categories = set(entry.get("category", "General") for entry in data)
        stats["categories"] = len(categories)
        stats["category_breakdown"] = {}
        for entry in data:
            cat = entry.get("category", "General")
            stats["category_breakdown"][cat] = stats["category_breakdown"].get(cat, 0) + 1
    else:  # glossary
        categories = set(entry.get("category", "General") for entry in data)
        stats["categories"] = len(categories)

    return stats

def find_duplicates(data: List[Dict[str, Any]], data_type: str = "abbreviations") -> List[Dict[str, Any]]:
    """Find duplicate entries in the data."""
    duplicates = []
    seen = set()

    key_field = "short" if data_type == "abbreviations" else "term"

    for entry in data:
        key = entry.get(key_field, "").lower()
        if key in seen:
            duplicates.append(entry)
        else:
            seen.add(key)

    return duplicates

def suggest_corrections(data: List[Dict[str, Any]], data_type: str = "abbreviations") -> List[str]:
    """Suggest corrections for common issues."""
    suggestions = []

    for i, entry in enumerate(data):
        if data_type == "abbreviations":
            short = entry.get("short", "")
            if short and not short.isupper():
                suggestions.append(f"Entry {i}: Consider making abbreviation uppercase: '{short}' -> '{short.upper()}'")

            if len(short) > 8:
                suggestions.append(f"Entry {i}: Abbreviation '{short}' is quite long, consider shortening")

        # Check for missing categories
        if "category" not in entry:
            suggestions.append(f"Entry {i}: Consider adding a category for better organization")

    return suggestions

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Manage abbreviations and glossary entries")
    parser.add_argument("action", choices=["validate", "export", "import", "stats", "check-duplicates", "suggest"], help="Action to perform")
    parser.add_argument("--type", choices=["abbreviations", "glossary"], default="abbreviations", help="Type of data to work with")
    parser.add_argument("--input", "-i", help="Input file path")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--config-dir", default="config", help="Configuration directory")

    args = parser.parse_args()

    # Determine file paths
    if args.type == "abbreviations":
        default_file = os.path.join(args.config_dir, "abbreviations.typ")
    else:
        default_file = os.path.join(args.config_dir, "glossary.typ")

    input_file = args.input or default_file

    if args.action in ["validate", "export", "stats", "check-duplicates", "suggest"]:
        if not os.path.exists(input_file):
            print(f"Error: Input file {input_file} does not exist")
            sys.exit(1)

        # For now, we'll create sample data since parsing Typst is complex
        # In a real implementation, you'd parse the Typst files
        if args.type == "abbreviations":
            data = [
                {"key": "Machine Learning", "short": "ML", "long": "A method of data analysis", "category": "AI"},
                {"key": "Deep Learning", "short": "DL", "long": "A subset of machine learning", "category": "AI"},
            ]
        else:
            data = [
                {"term": "Thesis", "definition": "A long piece of writing", "category": "Academic"},
                {"term": "Methodology", "definition": "The system of methods", "category": "Research"},
            ]

    if args.action == "validate":
        if args.type == "abbreviations":
            result = validate_abbreviations(data)
        else:
            result = validate_glossary(data)

        if result["errors"]:
            print("Errors found:")
            for error in result["errors"]:
                print(f"  - {error}")

        if result["warnings"]:
            print("Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

        if not result["errors"] and not result["warnings"]:
            print("Validation passed!")

    elif args.action == "export":
        output_file = args.output or f"{args.type}.csv"
        export_to_csv(data, output_file, args.type)

    elif args.action == "import":
        if not args.input:
            print("Error: Input file required for import")
            sys.exit(1)
        data = import_from_csv(args.input, args.type)
        print(f"Imported {len(data)} entries")

    elif args.action == "stats":
        stats = generate_statistics(data, args.type)
        print(f"Statistics for {args.type}:")
        for key, value in stats.items():
            if key != "category_breakdown":
                print(f"  {key}: {value}")
            else:
                print(f"  {key}:")
                for cat, count in value.items():
                    print(f"    {cat}: {count}")

    elif args.action == "check-duplicates":
        duplicates = find_duplicates(data, args.type)
        if duplicates:
            print(f"Found {len(duplicates)} duplicate entries:")
            for dup in duplicates:
                key = dup.get("short" if args.type == "abbreviations" else "term")
                print(f"  - {key}")
        else:
            print("No duplicates found")

    elif args.action == "suggest":
        suggestions = suggest_corrections(data, args.type)
        if suggestions:
            print("Suggestions:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        else:
            print("No suggestions available")

if __name__ == "__main__":
    main()