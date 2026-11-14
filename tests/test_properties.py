#!/usr/bin/env python3
"""Bounded generated contracts for the template's Python validation helpers.

Run: python tests/test_properties.py --seed 20261115 --cases 64
Replay a failure with the seed/case count recorded in the JSON report. Each
unittest subtest includes its case index and synthetic input. The generators
exercise supported data contracts; they do not parse or compile Typst source.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time
import traceback
import unittest

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261115
CASES = 64
CASE_COUNTS: dict[str, int] = {}
terms = None
template = None


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def quiet(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*args, **kwargs)


@contextlib.contextmanager
def in_directory(path):
    previous = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(previous)


def rich_text(rng):
    # Quotes, commas, line breaks, parentheses and Unicode probe CSV escaping.
    alphabet = 'AaZz09 ,;"()\n\\éā漢字α'
    return "α" + "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 48))) + "z"


def abbreviation_rows(rng):
    return [
        {
            "key": f"key-{i}-{rich_text(rng)}",
            "short": f"AB{i}",
            "long": rich_text(rng),
            "category": rich_text(rng),
        }
        for i in range(rng.randint(1, 8))
    ]


def glossary_rows(rng):
    return [
        {
            "term": f"term-{i}-{rich_text(rng)}",
            "definition": rich_text(rng),
            "category": rich_text(rng),
            # Semicolon is the documented related-term CSV delimiter.
            "related": [rich_text(rng).replace(";", ",") for _ in range(rng.randint(1, 4))],
        }
        for i in range(rng.randint(1, 8))
    ]


class GeneratedProperties(unittest.TestCase):
    def cases(self):
        name = self._testMethodName
        offset = sum((index + 1) * ord(character) for index, character in enumerate(name))
        rng = random.Random(SEED + offset)
        for case in range(CASES):
            CASE_COUNTS[name] = CASE_COUNTS.get(name, 0) + 1
            yield case, rng

    def test_valid_data_survives_permutation_without_mutation(self):
        for case, rng in self.cases():
            for factory, validator in (
                (abbreviation_rows, terms.validate_abbreviations),
                (glossary_rows, terms.validate_glossary),
            ):
                rows = factory(rng)
                rng.shuffle(rows)
                original = copy.deepcopy(rows)
                with self.subTest(seed=SEED, case=case, input=rows):
                    self.assertEqual(validator(rows), {"errors": [], "warnings": []})
                    self.assertEqual(rows, original)

    def test_required_fields_are_enforced(self):
        bad_values = [None, True, 0, 1.5, [], {}, "", " ", "\n\t"]
        for case, rng in self.cases():
            for factory, validator, fields in (
                (abbreviation_rows, terms.validate_abbreviations, ("key", "short", "long")),
                (glossary_rows, terms.validate_glossary, ("term", "definition")),
            ):
                rows = factory(rng)
                row = rng.choice(rows)
                field = fields[case % len(fields)]
                if case % (len(bad_values) + 1) == len(bad_values):
                    del row[field]
                else:
                    row[field] = bad_values[case % (len(bad_values) + 1)]
                with self.subTest(seed=SEED, case=case, input=rows):
                    self.assertTrue(validator(rows)["errors"])

    def test_non_list_containers_are_rejected(self):
        malformed = [None, {}, {"key": "A"}, "entries", 42, False, ()]
        for case, _ in self.cases():
            value = malformed[case % len(malformed)]
            for validator in (terms.validate_abbreviations, terms.validate_glossary):
                with self.subTest(seed=SEED, case=case, validator=validator.__name__, input=value):
                    self.assertTrue(validator(value)["errors"])

    def test_mixed_entries_are_reported_without_crashing(self):
        malformed = [None, 0, False, "entry", [], ["nested"], {}]
        for case, rng in self.cases():
            for factory, validator in (
                (abbreviation_rows, terms.validate_abbreviations),
                (glossary_rows, terms.validate_glossary),
            ):
                rows = factory(rng)
                rows.insert(rng.randrange(len(rows) + 1), malformed[case % len(malformed)])
                original = copy.deepcopy(rows)
                with self.subTest(seed=SEED, case=case, input=rows):
                    self.assertTrue(validator(rows)["errors"])
                    self.assertEqual(rows, original)

    def test_duplicates_are_rejected_after_reordering(self):
        for case, rng in self.cases():
            for factory, validator in (
                (abbreviation_rows, terms.validate_abbreviations),
                (glossary_rows, terms.validate_glossary),
            ):
                rows = factory(rng)
                duplicate = copy.deepcopy(rng.choice(rows))
                # Equal identities must fail even if descriptive fields differ.
                duplicate["long" if "short" in duplicate else "definition"] = rich_text(rng)
                rows.append(duplicate)
                rng.shuffle(rows)
                with self.subTest(seed=SEED, case=case, input=rows):
                    self.assertTrue(any("Duplicate" in error for error in validator(rows)["errors"]))

    def test_abbreviation_csv_round_trip(self):
        for case, rng in self.cases():
            rows = abbreviation_rows(rng)
            # Import normalizes surrounding whitespace by contract.
            for row in rows:
                for key in row:
                    row[key] = " \t" + row[key] + "\n "
            expected = [{key: value.strip() for key, value in row.items()} for row in rows]
            with self.subTest(seed=SEED, case=case, input=rows), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "abbreviations.csv"
                quiet(terms.export_to_csv, rows, str(path), "abbreviations")
                actual = quiet(terms.import_from_csv, str(path), "abbreviations")
                self.assertEqual(actual, expected)
                self.assertFalse(terms.validate_abbreviations(actual)["errors"])

    def test_glossary_csv_round_trip(self):
        for case, rng in self.cases():
            rows = glossary_rows(rng)
            expected = [
                {
                    key: [item.strip() for item in value] if key == "related" else value.strip()
                    for key, value in row.items()
                }
                for row in rows
            ]
            with self.subTest(seed=SEED, case=case, input=rows), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "glossary.csv"
                quiet(terms.export_to_csv, rows, str(path), "glossary")
                actual = quiet(terms.import_from_csv, str(path), "glossary")
                self.assertEqual(actual, expected)
                self.assertFalse(terms.validate_glossary(actual)["errors"])

    def test_valid_manifest_accepts_whitespace_and_key_order(self):
        for case, rng in self.cases():
            fields = [("name", f"synthetic-{case}"), ("version", "0.2.1"), ("entrypoint", "lib.typ")]
            rng.shuffle(fields)
            separator = rng.choice(["=", " = ", "\t=\t"])
            manifest = "# synthetic test\n[package]\n" + "\n".join(
                key + separator + json.dumps(value) for key, value in fields
            )
            with self.subTest(seed=SEED, case=case, input=manifest), tempfile.TemporaryDirectory() as directory:
                with in_directory(directory):
                    Path("typst.toml").write_text(manifest, encoding="utf-8")
                    self.assertTrue(quiet(template.validate_typst_toml))

    def test_manifest_required_metadata_rejects_wrong_types(self):
        bad_values = ["false", "0", "1.5", "[]", "{}", '""', '"  "']
        for case, rng in self.cases():
            fields = {"name": '"synthetic"', "version": '"0.2.1"', "entrypoint": '"lib.typ"'}
            field = tuple(fields)[case % len(fields)]
            if case % (len(bad_values) + 1) == len(bad_values):
                del fields[field]
            else:
                fields[field] = bad_values[case % (len(bad_values) + 1)]
            items = list(fields.items())
            rng.shuffle(items)
            manifest = "[package]\n" + "\n".join(f"{key} = {value}" for key, value in items)
            with self.subTest(seed=SEED, case=case, input=manifest), tempfile.TemporaryDirectory() as directory:
                with in_directory(directory):
                    Path("typst.toml").write_text(manifest, encoding="utf-8")
                    self.assertFalse(quiet(template.validate_typst_toml))

    def test_manifest_comments_or_wrong_tables_never_supply_package_fields(self):
        invalid_manifests = [
            '# name = "synthetic"\n# version = "0.2.1"\n# entrypoint = "lib.typ"\n',
            '[template]\nname = "synthetic"\nversion = "0.2.1"\nentrypoint = "lib.typ"\n',
            '[package]\n# name = "synthetic"\n# version = "0.2.1"\n# entrypoint = "lib.typ"\n',
            '[package]\nname = "synthetic"\nversion = "0.2.1"\nentrypoint = "lib.typ"\ninvalid TOML',
            'package = "name = version = entrypoint = "\n',
        ]
        for case, rng in self.cases():
            manifest = "# case-" + str(rng.randrange(100000)) + "\n" + invalid_manifests[case % len(invalid_manifests)]
            with self.subTest(seed=SEED, case=case, input=manifest), tempfile.TemporaryDirectory() as directory:
                with in_directory(directory):
                    Path("typst.toml").write_text(manifest, encoding="utf-8")
                    self.assertFalse(quiet(template.validate_typst_toml))


def main(argv=None):
    global SEED, CASES, terms, template
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--cases", type=int, default=CASES, help="Generated cases per property (1..1024).")
    parser.add_argument("--report", type=Path, default=Path("build/property-tests.json"))
    args = parser.parse_args(argv)
    if not 0 <= args.seed <= 2**32 - 1:
        parser.error("--seed must be between 0 and 4294967295")
    if not 1 <= args.cases <= 1024:
        parser.error("--cases must be between 1 and 1024")
    SEED, CASES = args.seed, args.cases
    CASE_COUNTS.clear()
    started = time.monotonic()
    report = {
        "schema_version": 1,
        "seed": SEED,
        "cases_per_property": CASES,
        "failure_threshold": 0,
        "python": sys.version,
        "replay": f"python tests/test_properties.py --seed {SEED} --cases {CASES}",
        "passed": False,
    }
    try:
        terms = load_script("manage_terms")
        template = load_script("validate_template")
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(GeneratedProperties)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        report.update(
            tests_run=result.testsRun,
            failures=[{"test": str(test), "detail": detail} for test, detail in result.failures],
            errors=[{"test": str(test), "detail": detail} for test, detail in result.errors],
            skipped=[{"test": str(test), "reason": reason} for test, reason in result.skipped],
        )
        report["passed"] = (
            result.wasSuccessful()
            and not result.skipped
            and result.testsRun > 0
            and sum(CASE_COUNTS.values()) == result.testsRun * CASES
        )
    except Exception:
        report["harness_error"] = traceback.format_exc()
        print(report["harness_error"], file=sys.stderr)
    finally:
        report["generated_cases"] = dict(sorted(CASE_COUNTS.items()))
        report["elapsed_seconds"] = round(time.monotonic() - started, 6)
        report["source_sha256"] = {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), ROOT / "scripts/manage_terms.py", ROOT / "scripts/validate_template.py")
            if path.is_file()
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Property evidence: {args.report}; seed={SEED}; cases/property={CASES}; passed={report['passed']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
