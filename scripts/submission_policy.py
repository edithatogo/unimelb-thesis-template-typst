#!/usr/bin/env python3
"""Check dated Melbourne policy data and bind an outstanding-review checklist.

This module validates supplied records and local byte identities. It does not
inspect rendered policy compliance, authenticate approvals or approve submission.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from scripts.native_evidence import EvidenceError, strict_json
from scripts.thesis_contract import ContractError, configuration_digest, load_bundle, validate

POLICY_ID = "unimelb-gr-2026-11-15"
POLICY_ROOT = ROOT / "policies/unimelb/2026-11-15"
POLICY_SHA256 = "ee538a07aa7387fd5af45ae73095a42c1439130534df8ea6aa93bc01189ea37b"
CONTRACT_SHA256 = "338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c"
BOUNDARY = (
    "Supplied metadata and matching file hashes are not rendered observations, "
    "authenticity checks, institutional approval or authority to submit."
)


class PolicyError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read_json(path):
    try:
        return strict_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, EvidenceError) as exc:
        raise PolicyError("invalid-json", "Input is missing or is not strict JSON.") from exc


def load_policy(path=POLICY_ROOT):
    path = Path(path)
    try:
        if digest(path / "manifest.json") != POLICY_SHA256:
            raise PolicyError("policy-drift", "The dated policy manifest does not match its pin.")
        manifest = read_json(path / "manifest.json")
        expected = {"profile.json", "rules.json", "sources.json", "request.schema.json", "result.schema.json"}
        if set(manifest["files"]) != expected or manifest["policy_id"] != POLICY_ID:
            raise PolicyError("policy-drift", "The dated policy inventory is incomplete.")
        result = {}
        for name, expected_hash in manifest["files"].items():
            if digest(path / name) != expected_hash:
                raise PolicyError("policy-drift", "A dated policy file changed.")
            result[name.removesuffix(".json")] = read_json(path / name)
        return result
    except (OSError, KeyError, TypeError) as exc:
        raise PolicyError("policy-drift", "The dated policy bundle is unavailable.") from exc


def today():
    return datetime.now(timezone(timedelta(hours=10))).date()


def base_report(as_of):
    return {
        "schema_version": 1, "policy_id": POLICY_ID, "as_of": as_of.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_result": "fail", "data_result": "invalid", "submission_approved": False,
        "privacy": "internal-not-reviewer-safe", "evidence_boundary": BOUNDARY,
        "configuration_sha256": None, "request_sha256": None, "artifact": None,
        "identities": {"policy_manifest_sha256": POLICY_SHA256,
                       "canonical_bundle_sha256": CONTRACT_SHA256,
                       "checker_sha256": digest(Path(__file__))},
        "checks": [], "human_checklist": [], "metrics": {},
        "canonical_publication_bridge": "unexecuted", "errors": [],
    }


def indexed(items, length):
    indices = [item["index"] for item in items]
    if len(indices) != len(set(indices)) or set(indices) != set(range(length)):
        return None
    return {item["index"]: item for item in items}


class Evaluation:
    def __init__(self, request, pdf, evidence_root, as_of, policy):
        self.request, self.data, self.as_of, self.policy = request, request["policy"], as_of, policy
        self.report = base_report(as_of)
        self.report["request_sha256"] = canonical_digest(request)
        try:
            bundle = load_bundle(ROOT / "contracts/thesis/v1", CONTRACT_SHA256)
            layers = request["layers"]
            resolved = bundle.normalize(layers["metadata"], bundle.parse_cli(layers["cli"]), layers["explicit"])
        except ContractError as exc:
            raise PolicyError("configuration-invalid", "A canonical configuration layer or combination is invalid.") from exc
        self.config = resolved["configuration"]
        self.meta = self.config["metadata"]
        self.report["configuration_sha256"] = configuration_digest(self.config)
        self.subject = hashlib.sha256(self.meta.get("author", {}).get("student_record_name", "").encode()).hexdigest()
        self.course = self.meta.get("degree", {}).get("course")
        self.degree = self.meta.get("degree", {}).get("kind")
        self.final = self.config["purpose"] != "draft"
        self.deposit = self.config["purpose"].startswith("deposit-")
        self.documents, self.decisions, self.human_ids = {}, {}, set()
        pdf = Path(pdf)
        try:
            if pdf.suffix.lower() != ".pdf" or not pdf.is_file():
                raise PolicyError("artifact-invalid", "A written-thesis PDF file is required.")
            with pdf.open("rb") as source:
                if source.read(5) != b"%PDF-":
                    raise PolicyError("artifact-invalid", "The supplied file has no PDF header.")
            self.pdf_sha256 = digest(pdf)
            self.report["artifact"] = {"sha256": self.pdf_sha256, "bytes": pdf.stat().st_size,
                                       "pdf_structure": "unexecuted"}
        except OSError as exc:
            raise PolicyError("artifact-invalid", "The supplied PDF cannot be read.") from exc
        self.check("CONFIGURATION.REQUIRED", "CON-02", not any(
            item["code"].startswith("missing-") for item in resolved["diagnostics"]),
            "Canonical required metadata must be supplied for this policy assessment.")
        self.check("POL07.FILE", "POL-07", "," not in pdf.name and "#" not in pdf.name,
                   "The actual PDF filename must omit TES-prohibited commas and hashtags.", basis="byte-identity")
        self._load_evidence(Path(evidence_root))
        self._load_decisions()

    def check(self, rule, requirement, passed, message, *, applicable=True,
              basis="supplied-data", refs=(), result=None):
        self.report["checks"].append({
            "id": rule, "requirement": requirement,
            "applicability": "unknown" if applicable is None else ("applicable" if applicable else "not-applicable"),
            "result": "blocked" if applicable is None else ((result or ("pass" if passed else "fail")) if applicable else "not-applicable"),
            "basis": basis, "message": message, "evidence_refs": sorted(set(refs)),
        })

    def human(self, key, requirement, action, refs=()):
        if key not in self.human_ids:
            self.human_ids.add(key)
            self.report["human_checklist"].append({
                "id": key, "requirement": requirement, "status": "human-review-required",
                "action": action, "pdf_sha256": self.pdf_sha256, "record_refs": sorted(set(refs)),
            })

    def _load_evidence(self, root):
        ids = [item["id"] for item in self.data["documents"]]
        if len(ids) != len(set(ids)):
            raise PolicyError("duplicate-id", "Evidence document identifiers must be unique.")
        root = root.resolve()
        valid = True
        for item in self.data["documents"]:
            path = Path(item["path"])
            if path.is_absolute() or ".." in path.parts:
                raise PolicyError("evidence-path", "Evidence paths must remain inside the explicit evidence root.")
            candidate = root / path
            if any(part.is_symlink() for part in [candidate, *candidate.parents] if part != root and part.is_relative_to(root)):
                raise PolicyError("evidence-path", "Evidence links cannot escape the explicit evidence root.")
            try:
                resolved = candidate.resolve(strict=True)
                matches = (resolved.is_relative_to(root) and resolved.is_file()
                           and digest(resolved) == item["sha256"] and item["sha256"] != self.pdf_sha256)
            except (OSError, RuntimeError):
                matches = False
            self.documents[item["id"]] = {**item, "bytes_match": matches}
            valid = valid and matches
        self.check("EVIDENCE.IDENTITIES", "POL-07", valid,
                   "Every declared separate evidence file must match its bytes and remain distinct from the thesis.",
                   basis="byte-identity", refs=ids)

    def _load_decisions(self):
        ids = [item["id"] for item in self.data["decisions"]]
        if len(ids) != len(set(ids)):
            raise PolicyError("duplicate-id", "Decision identifiers must be unique.")
        self.decisions = {item["id"]: item for item in self.data["decisions"]}
        if ids:
            self.human("DECISION.AUTHENTICITY", "POL-07",
                       "Authenticate the claimed decisions, authority, scope and dates; file hashes verify byte identity only.", ids)

    def document(self, ref, kinds, *, private=False):
        value = self.documents.get(ref)
        return bool(value and value["bytes_match"] and value["kind"] in kinds
                    and (not private or value["classification"] in ("private", "synthetic")))

    def decision(self, ref, kind, authority, **scope):
        item = self.decisions.get(ref)
        if not item:
            return False
        expected = {"course": self.course, "subject_sha256": self.subject,
                    "purpose": self.config["purpose"], **scope}
        dates_ok = (date.fromisoformat(item["issued_on"]) <= self.as_of
                    and ("expires_on" not in item or self.as_of <= date.fromisoformat(item["expires_on"])))
        return bool(item["state"] == "approved" and item["kind"] == kind
                    and item["authority"] == authority and dates_ok
                    and all(item["scope"].get(key) == value for key, value in expected.items())
                    and ("artifact_sha256" not in item["scope"] or item["scope"]["artifact_sha256"] == self.pdf_sha256)
                    and self.document(item["document_ref"], {"approval", "human-review", "rights-record"}))

    def word_count(self):
        counts = self.data.get("word_count")
        limits = self.policy["profile"]["limits"].get(self.degree)
        valid = counts is not None and limits is not None
        self.check("POL03.COUNT", "POL-03", valid,
                   "Supply all word-count components, including footnotes, exclusions and the treatment of other content.")
        if not valid:
            return
        maximum, recommended = limits["maximum"], limits["recommended"]
        course = self.data.get("course_rule")
        course_ok = (not course or (course["course"] == self.course
                     and self.document(course["document_ref"], {"handbook"})
                     and course.get("recommended_words", course["maximum_words"]) <= course["maximum_words"]))
        self.check("POL03.COURSE", "POL-03", course_ok,
                   "A course override must match the selected course and a retained Handbook source; its interpretation needs review.",
                   applicable=bool(course), refs=[course["document_ref"]] if course else [])
        if course and course_ok:
            maximum = course["maximum_words"]
            recommended = course.get("recommended_words", maximum)
            self.human("HANDBOOK.INTERPRETATION", "POL-03", "Verify the Handbook year, cohort, course and clause interpretation.", [course["document_ref"]])
        counted = counts["body"] + counts["footnotes"] + counts["other_included"]
        adjustments = counts["adjustments"]
        adjustment_ids = [item["id"] for item in adjustments]
        adjusted_ok = len(adjustment_ids) == len(set(adjustment_ids))
        for item in adjustments:
            adjusted_ok = adjusted_ok and self.decision(item["decision_ref"], "count-adjustment", "author", adjustment_id=item["id"])
            counted += item["delta"]
        self.check("POL03.ADJUSTMENTS", "POL-03", adjusted_ok and counted >= 0,
                   "Manual count adjustments require an explicit reason and a scoped recorded author decision.",
                   applicable=bool(adjustments), refs=[x["decision_ref"] for x in adjustments])
        if counted < 0:
            return
        self.report["metrics"].update(counted_words=counted, maximum_words=maximum,
                                      recommended_words=recommended, above_recommendation=counted > recommended)
        self.check("POL03.DECLARATION", "POL-03", self.meta.get("declarations", {}).get("word_count") == counted,
                   "The supplied declaration count must equal the selected scoped count; rendered wording is not inspected.")
        exception = self.config["approval_refs"].get("word_limit")
        item = self.decisions.get(exception, {})
        approved_max = item.get("scope", {}).get("max_words", 0)
        exception_ok = (approved_max >= counted and self.decision(
            exception, "word-limit", "pro-vice-chancellor", max_words=approved_max))
        self.check("POL03.EXCEPTION", "POL-03", exception_ok,
                   "An excess needs a recorded approved exception within its subject, course, purpose, date and numerical scope.",
                   applicable=counted > maximum, basis="recorded-human-decision", refs=[exception] if exception else [])
        self.check("POL03.LIMIT", "POL-03", course_ok and adjusted_ok and (counted <= maximum or exception_ok),
                   "Apply the selected maximum; exceeding an advisory target alone is not a failure.")
        self.human("WORDCOUNT.METHODOLOGY", "POL-03", "Verify component counts, omitted material, adjustments and declaration wording against the actual thesis.")

    def language_and_creative(self):
        non_english = self.config["language"].split("-")[0] != "en"
        reference = self.config["approval_refs"].get("non_english")
        self.check("POL04.LANGUAGE", "POL-04", self.decision(reference, "non-english", "pro-vice-chancellor", language=self.config["language"]),
                   "Non-English thesis approval is independent of label locale and must match the actual thesis language.",
                   applicable=non_english, basis="recorded-human-decision", refs=[reference] if reference else [])
        words = len(self.meta.get("english_summary", "").split())
        bounds = self.policy["profile"]["limits"].get(self.degree, {}).get("english_summary", [])
        self.check("POL04.SUMMARY", "POL-04", bool(bounds and bounds[0] <= words <= bounds[1]),
                   "Count whitespace-delimited tokens in the supplied English summary; its English language and required content need review.",
                   applicable=non_english)
        if non_english:
            self.report["metrics"]["summary_words"] = words
            self.human("LANGUAGE.APPROVAL", "POL-04", "Verify early-candidature approval and the English summary's introduction, chapter outline, conclusion and final word count.", [reference] if reference else [])
        outputs = self.meta.get("creative_outputs", [])
        creative = self.data.get("creative")
        active = bool(outputs)
        components = creative.get("components", []) if creative else []
        ids = [item["id"] for item in components]
        valid = bool(creative and len(ids) == len(set(ids)) and set(ids) == {x["id"] for x in outputs}
                     and all("proportion" in x and x["description"].strip() for x in outputs)
                     and all(self.document(x["electronic_ref"], {"creative-electronic"}) for x in components))
        total = sum((Decimal(str(x.get("proportion", 0))) for x in outputs), Decimal(0))
        dissertation = Decimal(str(creative["dissertation_percent"])) if creative else Decimal(0)
        agreement = creative.get("agreement_ref") if creative else None
        valid = valid and total + dissertation == 100 and self.decision(
            agreement, "creative-agreement", "advisory-committee", dissertation_percent=float(dissertation), creative_percent=float(total))
        self.check("POL04.CREATIVE", "POL-04", valid if active else creative is None,
                   "Creative records need matching electronic components, descriptions, integration and an agreed 100-percent split.",
                   applicable=active or creative is not None, refs=[agreement] if agreement else [])
        if active:
            if total <= 100:
                self.report["metrics"].update(dissertation_percent=float(dissertation), creative_percent=float(total))
            self.human("CREATIVE.INTEGRATION", "POL-04", "Review the agreed weighting, form, integration and quality of all creative outputs.", [agreement] if agreement else [])
        durable = active and self.deposit
        self.check("POL04.DURABLE", "POL-04", bool(creative and all(
            self.document(x.get("durable_ref"), {"durable-component"}) for x in components)),
            "Final deposit requires retained durable components; their usability and completeness need human review.", applicable=durable)
        if durable:
            self.human("CREATIVE.DURABLE", "POL-04", "Inspect all durable components, including online material, and verify their preservation and accessibility.")

    def funding_and_disclosures(self):
        funders = self.meta.get("funding", [])
        funding = self.data.get("funding")
        grants = indexed(funding["grants"], len(funders)) if funding else None
        valid = bool(funding and funding["inventory_complete"] and grants is not None)
        if grants is not None:
            valid = valid and all((grants[i]["status"] == "issued" and bool(x.get("grant")))
                                 or (grants[i]["status"] == "not-issued" and not x.get("grant")
                                     and bool(grants[i].get("reason")))
                                 for i, x in enumerate(funders))
        self.check("POL05.FUNDING-INVENTORY", "POL-05", bool(funding and funding["inventory_complete"]),
                   "Explicitly declare whether the supplied funding inventory is complete; automation cannot establish completeness.")
        self.check("POL05.FUNDING", "POL-05", valid,
                   "Declare the complete funding inventory and every applicable grant ID; unavailable grant identifiers need an explicit explanation.",
                   applicable=bool(funders or (funding and funding["grants"])))
        rtp = bool(funding and (funding["rtp_stipend"] or funding["rtp_fee_offset"]))
        prescribed = self.policy["profile"]["rtp_acknowledgement"]
        acknowledgements = [" ".join(x.get("acknowledgement", "").split()) for x in funders]
        self.check("POL05.RTP", "POL-05", prescribed in acknowledgements,
                   "Stipend or fee-offset support triggers the dated Commonwealth RTP acknowledgement and DOI.", applicable=rtp if funding is not None else None)
        self.human("FUNDING.COMPLETENESS", "POL-05", "Verify all funders, grants, RTP applicability and the actual rendered acknowledgement.")
        prior = self.meta.get("prior_work", [])
        prior_details = self.data.get("prior_work", [])
        mapping = indexed(prior_details, len(prior))
        self.check("POL05.PRIOR", "POL-05", mapping is not None and all(
            value["before_enrolment"] or value["other_qualification"] for value in prior_details),
            "Classify each supplied prior-work disclosure independently as pre-enrolment and/or other-qualification work.",
            applicable=bool(prior or prior_details))
        assistance = self.meta.get("assistance", [])
        details = self.data.get("assistance", [])
        mapping = indexed(details, len(assistance))
        ai_claimed = any(item.get("ai_authorship_claimed") is True for item in details)
        valid = mapping is not None and not ai_claimed
        digital = False
        ai_active = ai_claimed or any(x["kind"] == "ai" for x in assistance)
        ai_valid = not ai_claimed
        for i, item in enumerate(assistance):
            detail = mapping.get(i) if mapping is not None else None
            if not detail:
                valid = False
                if item["kind"] == "ai":
                    ai_valid = False
                continue
            valid = valid and not detail["full_private_log_embedded"]
            if detail["use_kind"] == "editorial":
                allowed = {"C", "D", "E"} if item["kind"] == "human" and detail["role"] == "supervisor" else {"D", "E"}
                valid = valid and bool(detail["editing_standards"]) and set(detail["editing_standards"]) <= allowed
            if item["kind"] == "human":
                valid = valid and "discipline_knowledge" in detail
            else:
                digital = True
                valid = valid and self.document(detail.get("private_log_ref"), {"assistance-log"}, private=True)
                valid = valid and set(detail.get("log_fields", [])) == {"programs", "dates", "prompts"}
                valid = valid and self.decision(detail.get("verification_ref"), "author-verification", "author",
                                                artifact_sha256=self.pdf_sha256)
                if item["kind"] == "ai":
                    ai_active = True
                    ai_valid = ai_valid and detail.get("ai_authorship_claimed") is False
                    valid = valid and ai_valid
        self.check("POL05.ASSISTANCE", "POL-05", valid,
                   "Disclose provider, extent and locations; respect editing boundaries and retain private digital-use records without embedding full logs.",
                   applicable=bool(assistance or details))
        self.check("POL05.AI", "POL-05", ai_valid,
                   "The supplied records must not claim AI authorship; verification and acceptable use remain human responsibilities.",
                   applicable=ai_active)
        if prior:
            self.human("PRIORWORK.ACCURACY", "POL-05", "Verify the separate disclosures and the actual treatment of earlier or other-qualification work.")
        if assistance:
            self.human("ASSISTANCE.REVIEW", "POL-05", "Verify disclosure completeness, discipline knowledge, editing boundaries and author responsibility; research-tool use is not automatically approved.")
        if digital:
            self.human("DIGITAL.PRIVATELOGS", "POL-05", "Inspect private dates, tools and prompts on request; verify outputs and diagram-specific disclosure without publishing confidential inputs.")
        self.check("POL05.ETHICS", "POL-05", False,
                   "Absence of ethics applications from the actual PDF and appendices has not been inspected.",
                   basis="rendered-observation-unexecuted", result="unexecuted")

    def publications(self):
        canonical = self.meta.get("publications", [])
        record = self.data.get("publications")
        values = record["records"] if record else []
        active = bool(canonical or values)
        ids = [x["id"] for x in values]
        valid = len(ids) == len(set(ids)) and set(ids) == {x["id"] for x in canonical}
        lookup = {x["id"]: x for x in canonical}
        registry_ok, rights_ok, forms_ok, integration_ok = valid, valid, valid, valid
        self.report["canonical_publication_bridge"] = "supported"
        self.incorporated = {x["id"] for x in values if x["incorporation"] != "figure-only"}
        self.forms_applicable = None if canonical and not valid else bool(self.incorporated)
        self.complete_publications = {x["id"] for x in values if x["incorporation"] == "complete-publication"}
        for item in values:
            common = lookup.get(item["id"], {})
            status = item["official_status"]
            candidate_name = self.meta.get("author", {}).get("student_record_name")
            contributors = {x["name"] for x in common.get("contributions", [])}
            registry_ok = registry_ok and candidate_name in contributors
            registry_ok = registry_ok and bool(contributors - {candidate_name}) == item["coauthored"]
            registry_ok = registry_ok and ("version" not in common or common["version"] == item["version"])
            registry_ok = registry_ok and ("location" not in common or common["location"] in item["locations"])
            if "status_date" in item:
                registry_ok = registry_ok and date.fromisoformat(item["status_date"]) <= self.as_of
            if status == "in-revision":
                self.report["canonical_publication_bridge"] = "unsupported-in-revision"
            else:
                registry_ok = registry_ok and self.policy["profile"]["canonical_status_map"].get(common.get("status")) == status
            if status != "unpublished":
                registry_ok = registry_ok and bool(item.get("venue"))
            if status in {"submitted", "accepted", "published"}:
                registry_ok = registry_ok and bool(item.get("status_date"))
            partition = item.get("exclusive_partition")
            if partition:
                registry_ok = registry_ok and (len({x["name"] for x in partition}) == len(partition)
                    and {x["name"] for x in partition} == contributors
                    and sum(Decimal(str(x["percentage"])) for x in partition) == 100)
            if item["incorporation"] == "complete-publication" and status in {"accepted", "published"}:
                registry_ok = registry_ok and item["version"] in {"publisher", "author-accepted-manuscript"}
            if item["incorporation"] != "figure-only":
                integration_ok = integration_ok and item["undertaken_during_candidature"]
                expected_signatures = {"principal-supervisor"}
                if item["coauthored"]:
                    expected_signatures.add("coordinating-author")
                forms_ok = forms_ok and expected_signatures <= set(item.get("signatures_declared", []))
                forms_ok = forms_ok and self.document(item.get("form_ref"), {"publication-form"}, private=True)
            if item["literature_review"]:
                integration_ok = integration_ok and bool(item.get("updated_literature_note"))
            rights = item["rights_basis"]
            if rights == "permission":
                rights_ok = rights_ok and self.decision(item.get("rights_ref"), "publication-rights", "rights-holder",
                                                        publication_id=item["id"], version=item["version"])
            elif rights == "open-license":
                rights_ok = rights_ok and bool(item.get("license_url")) and self.document(item.get("rights_ref"), {"rights-record"})
            elif rights == "owned":
                if item["version"] == "publisher":
                    rights_ok = rights_ok and self.document(item.get("rights_ref"), {"rights-record"})
            else:
                rights_ok = False
        self.check("POL06.REGISTRY", "POL-06", registry_ok,
                   "Validate the five official statuses, citation/venue/date, selected version and explicit contribution partitions; overlapping role percentages need not sum.", applicable=active)
        bridge = self.report["canonical_publication_bridge"] == "unsupported-in-revision"
        self.check("POL06.CANONICAL-BRIDGE", "POL-06", True,
                   "The shared v1 enum cannot represent in-revision status; the sidecar retains it without changing or claiming a canonical rendering bridge.",
                   applicable=bridge, result="unsupported" if bridge else None)
        self.check("POL06.RIGHTS", "POL-06", rights_ok,
                   "Validate supplied version-specific rights records; authenticity and the publishing agreement require human review.", applicable=active)
        self.check("POL06.FORMS", "POL-06", forms_ok,
                   "Incorporated publications need separate form records and declared supervisor/coordinating-author signatures; figure-only cases are excepted.",
                   applicable=self.forms_applicable)
        bibliography_ok = bool(record and not self.incorporated.intersection(record["planned_thesis_bibliography_ids"])
                               and all(x["publication_id"] in ids for x in record["planned_publication_bibliographies"]))
        self.check("POL06.BIBLIOGRAPHY", "POL-06", bibliography_ok,
                   "Validate the supplied bibliography plan only; internal publication references may repeat incorporated works. Actual bibliography output remains unexecuted.", applicable=active)
        self.check("POL06.INTEGRATION", "POL-06", integration_ok and bool(record and record.get("integration_statement")),
                   "Supply an integration account and required literature-update notes; scholarly adequacy is not an automated decision.", applicable=active)
        self.check("POL06.LITERATURE", "POL-06", all(
            bool(x.get("updated_literature_note")) for x in values if x["literature_review"]),
            "A supplied literature-review publication needs an account of relevant later work; the analysis itself requires scholarly review.",
            applicable=any(x["literature_review"] for x in values))
        if active:
            self.human("PUBLICATIONS.INTEGRITY", "POL-06", "Assess substantial contribution, candidature timing, integration, updated literature, citation locations, rights and the actual bibliography.")
        if self.incorporated:
            self.human("PUBLICATIONS.SIGNEDFORMS", "POL-06", "Inspect all actual signatures and consents, combine the forms for a separate TES upload, and ensure no signed form is embedded in the thesis.")

    def submission(self):
        data = self.data.get("submission", {})
        self.check("POL07.SINGLE-WRITTEN-FILE", "POL-07", data.get("written_component_count") == 1,
                   "The supplied written-component inventory must declare one file; this tool does not inspect a TES upload.", applicable=self.final)
        report = data.get("originality")
        valid = bool(report and report["for_pdf_sha256"] == self.pdf_sha256
                     and self.document(report["document_ref"], {"originality-report"}, private=True))
        self.check("POL07.ORIGINALITY", "POL-07", valid,
                   "Bind the supplied full-thesis iThenticate record to this PDF; originality is assessed by the supervisor and chair.", applicable=self.final)
        excluded = report["excluded_publication_ids"] if report else []
        self.check("POL07.FILTERS", "POL-07", set(excluded) <= self.complete_publications
                   and bool(report and report.get("filters_explanation")),
                   "Only complete incorporated publication sources may be listed as matching-source exclusions, with a recorded explanation.", applicable=bool(excluded))
        supervisor = data.get("supervisor_review_ref")
        self.check("POL07.REVIEW", "POL-07", self.decision(supervisor, "supervisor-review", "principal-supervisor", artifact_sha256=self.pdf_sha256),
                   "A supervisor review record must concern exactly this PDF; its authenticity remains outstanding.",
                   applicable=self.final, basis="recorded-human-decision", refs=[supervisor] if supervisor else [])
        self.check("POL07.FORMS-BUNDLE", "POL-07", self.document(data.get("signed_forms_bundle_ref"), {"publication-forms-bundle"}, private=True),
                   "Keep the combined signed forms as a separate byte-identified upload.", applicable=self.forms_applicable if self.final else False)
        corrections, chair = data.get("final_corrections_ref"), data.get("chair_final_approval_ref")
        self.check("POL07.FINAL-CORRECTIONS", "POL-07", self.decision(corrections, "final-corrections", "chair-of-examiners", artifact_sha256=self.pdf_sha256),
                   "Doctoral final corrections require a scoped record; masters timing and amendment exceptions need individual review.",
                   applicable=self.deposit and (self.degree == "doctoral" or corrections is not None), refs=[corrections] if corrections else [])
        self.check("POL07.CHAIR-FINAL", "POL-07", self.decision(chair, "chair-final-approval", "chair-of-examiners", artifact_sha256=self.pdf_sha256),
                   "Final deposit needs a recorded chair decision about this PDF, without this tool authenticating or granting approval.",
                   applicable=self.deposit, refs=[chair] if chair else [])
        if self.final:
            self.human("SUBMISSION.ORIGINALITY", "POL-07", "Review the full-thesis similarity report, filters and originality; recheck the dated live-sharing service notice and current submission process.")
            self.human("SUBMISSION.SUPERVISOR", "POL-07", "Authenticate the supervisor review and confirm the intended TES upload is this exact PDF.", [supervisor] if supervisor else [])
            self.human("SUBMISSION.ADMINISTRATION", "POL-07", "Confirm enrolment, completion seminar, intention to submit, access decisions and any joint-institution requirements in the real systems.")
        if self.deposit:
            self.human("DEPOSIT.FINAL", "POL-07", "Confirm the actual pass result, corrections/masters exceptions, chair approval, all durable components and final access permissions.")

    def finish(self):
        self.word_count()
        self.language_and_creative()
        self.funding_and_disclosures()
        self.publications()
        self.submission()
        for requirement in ("POL-01", "POL-02"):
            self.check(requirement.replace("-", "") + ".RENDERED", requirement, False,
                       "No supplied order string or metadata assertion establishes actual PDF geometry, title/section order, abstract length, logos or signatures.",
                       basis="rendered-observation-unexecuted", result="unexecuted")
        self.human("OUTPUT.INSPECTION", "POL-01", "Inspect the exact PDF and all assets for required title/order/geometry/pagination, logos, signatures, ethics material and disclosure accuracy.")
        self.human("POLICY.CURRENTNESS", "POL-07", "Review current official clauses, the retained version-5/version-6 inconsistency and any course or institutional decisions before submission.")
        failed = any(item["result"] == "fail" for item in self.report["checks"])
        self.report.update(data_result="fail" if failed else "pass", overall_result="fail" if failed else "partial")
        validate(self.policy["result.schema"], self.report)
        return self.report


def evaluate(request, *, pdf_path, evidence_root, as_of=None, policy_root=POLICY_ROOT):
    """Return scoped data checks and unresolved human work for actual PDF bytes."""
    if as_of is not None and type(as_of) is not date:
        raise PolicyError("invalid-date", "The assessment date must be a calendar date.")
    policy = load_policy(policy_root)
    try:
        validate(policy["request.schema"], request)
    except ContractError as exc:
        raise PolicyError("input-invalid", "The policy request does not satisfy the strict sidecar schema.") from exc
    return Evaluation(request, pdf_path, evidence_root, as_of or today(), policy).finish()


def output_guard(report, protected):
    output_root = ROOT / "build/submission-policy"
    # Preserve lexical symlink components while making ancestor checks comparable.
    report = Path(report).absolute()
    if (output_root.is_symlink() or (ROOT / "build").is_symlink() or report.is_symlink()
            or any(part.is_symlink() for part in report.parents if part.is_relative_to(output_root))
            or not report.resolve().is_relative_to(output_root.resolve()) or report.resolve() == output_root.resolve()):
        raise PolicyError("unsafe-output", "Reports must be files under build/submission-policy without symbolic links.")
    if report.exists() and not report.is_file():
        raise PolicyError("unsafe-output", "The report destination must be a regular file.")
    if report.exists() and report.stat().st_nlink > 1:
        raise PolicyError("unsafe-output", "A report cannot replace a hard-linked file.")
    for path in protected:
        path = Path(path)
        if report.resolve() == path.resolve() or (report.exists() and path.exists() and report.samefile(path)):
            raise PolicyError("unsafe-output", "The report must not overwrite an input or evidence file.")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "build/submission-policy/report.json")
    parser.add_argument("--as-of", type=date.fromisoformat, default=today())
    args = parser.parse_args(argv)
    evidence_root = args.evidence_root or args.input.parent
    report = base_report(args.as_of)
    output = None
    try:
        request = read_json(args.input)
        protected = [args.input, args.pdf]
        if isinstance(request, dict) and isinstance(request.get("policy"), dict):
            documents = request["policy"].get("documents", [])
            if isinstance(documents, list):
                protected.extend(evidence_root / item["path"] for item in documents
                                 if isinstance(item, dict) and isinstance(item.get("path"), str))
        output = output_guard(args.report, protected)
        output.parent.mkdir(parents=True, exist_ok=True)
        # Replace stale success before evaluating any supplied approval or artifact.
        output.write_text(json.dumps(report, indent=2) + "\n")
        report = evaluate(request, pdf_path=args.pdf, evidence_root=evidence_root, as_of=args.as_of)
    except (PolicyError, OSError) as exc:
        report["errors"] = [{"code": getattr(exc, "code", "io-error"), "message": str(exc) if isinstance(exc, PolicyError) else "A required local file is unavailable."}]
        if output is None and getattr(exc, "code", None) != "unsafe-output":
            try:
                output = output_guard(args.report, [args.input, args.pdf])
                output.parent.mkdir(parents=True, exist_ok=True)
            except (PolicyError, OSError):
                output = None
        print("Policy validation could not complete: " + report["errors"][0]["code"], file=sys.stderr)
    if output is not None:
        try:
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        except OSError:
            print("Policy validation could not retain its report: report-write-failed", file=sys.stderr)
            return 2
    if report["data_result"] == "invalid":
        return 2
    print("Supplied-data result: " + report["data_result"] + "; overall: " + report["overall_result"] + "; submission is not approved.")
    return 0 if report["data_result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
