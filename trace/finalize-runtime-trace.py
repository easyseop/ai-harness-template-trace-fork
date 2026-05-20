#!/usr/bin/env python3
"""Finalize a Runtime Trace session.

The finalizer separates three concepts:
- selected files: files the harness router selected for a workflow step
- loaded files: files explicitly marked as read with mark-loaded-file.sh
- applied evidence: file_path#RULE-ID references emitted in Spec Evidence

It cannot prove model comprehension. It can verify that cited Rule IDs exist in
loaded files and write a higher-confidence trace summary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVIDENCE_RE = re.compile(
    r"(?P<path>(?:\.?/?[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\."
    r"(?:md|markdown|yaml|yml|json|hbs|sh|py|txt))#(?P<rule>RULE-[A-Z0-9-]+-[0-9]+)"
)
RULE_RE = re.compile(r"RULE-[A-Z0-9-]+-[0-9]+")


def git_root() -> Path:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if value:
            return Path(value)
    except Exception:
        pass
    return Path.cwd()


ROOT = git_root()
TRACE_DIR = ROOT / ".harness" / "trace"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_trace_id(explicit: str | None) -> str:
    if explicit:
        return explicit
    latest = TRACE_DIR / "latest-runtime-trace.json"
    if not latest.exists():
        raise SystemExit("No latest runtime trace found. Run record-runtime-trace.sh first.")
    return str(load_json(latest).get("trace_id", ""))


def selected_record(trace_id: str) -> dict[str, Any]:
    session_selected = TRACE_DIR / "sessions" / trace_id / "selected-runtime-trace.json"
    if session_selected.exists():
        return load_json(session_selected)
    latest = TRACE_DIR / "latest-runtime-trace.json"
    if latest.exists():
        data = load_json(latest)
        if data.get("trace_id") == trace_id:
            return data
    raise SystemExit(f"No selected runtime trace found for trace_id={trace_id}")


def selected_paths(record: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in ["selected_command_files", "selected_reference_files", "selected_agent_files"]:
        value = record.get(key, [])
        if isinstance(value, list):
            paths.extend(str(item) for item in value)
    return sorted(set(paths))


def selected_paths_by_group(record: dict[str, Any]) -> dict[str, set[str]]:
    selected_files = record.get("selected_files")
    grouped: dict[str, set[str]] = {"command": set(), "reference": set(), "agent": set()}
    if isinstance(selected_files, dict):
        for group in grouped:
            values = selected_files.get(group, [])
            if isinstance(values, list):
                grouped[group].update(str(item) for item in values)

    grouped["command"].update(str(item) for item in (record.get("selected_command_files") or []))
    grouped["reference"].update(str(item) for item in (record.get("selected_reference_files") or []))
    grouped["agent"].update(str(item) for item in (record.get("selected_agent_files") or []))
    return grouped


def load_policy(path_value: str | None, require_policy: bool) -> tuple[dict[str, Any], str]:
    if not path_value:
        if require_policy:
            raise SystemExit("--require-policy needs --policy <trace-policy.json>.")
        return {}, ""
    path = Path(path_value)
    path = path if path.is_absolute() else ROOT / path
    if not path.exists():
        if require_policy:
            raise SystemExit(f"Trace policy file not found: {path_value}")
        return {}, str(path_value)
    return load_json(path), str(path_value)


def merged_step_policy(policy: dict[str, Any], workflow_step: str) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    default_policy = policy.get("default", {})
    step_policy = (policy.get("steps", {}) or {}).get(workflow_step, {})
    if isinstance(default_policy, dict):
        merged.update(default_policy)
    if isinstance(step_policy, dict):
        merged.update(step_policy)
    return merged


def policy_required_loaded_files(
    record: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[set[str], list[str]]:
    if not policy:
        return set(), []

    workflow_step = str(record.get("workflow_step", "")).strip().lstrip("/")
    selected_by_group = selected_paths_by_group(record)
    selected = set(selected_paths(record))
    step_policy = merged_step_policy(policy, workflow_step)

    required: set[str] = set()
    for group in step_policy.get("required_loaded_selected_groups", []) or []:
        required.update(selected_by_group.get(str(group), set()))

    policy_paths_not_selected: list[str] = []
    for path in step_policy.get("required_loaded_selected_paths", []) or []:
        normalized = str(path)
        if normalized in selected:
            required.add(normalized)
        else:
            policy_paths_not_selected.append(normalized)

    return required, sorted(policy_paths_not_selected)


def evidence_references(text: str, loaded_paths: set[str]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for match in EVIDENCE_RE.finditer(text):
        path = match.group("path").lstrip("./")
        rule_id = match.group("rule")
        full_path = ROOT / path
        path_exists = full_path.exists()
        text_content = full_path.read_text(encoding="utf-8", errors="ignore") if path_exists else ""
        rule_exists = rule_id in set(RULE_RE.findall(text_content))
        loaded = path in loaded_paths
        refs.append({
            "path": path,
            "rule_id": rule_id,
            "path_exists": path_exists,
            "rule_exists_in_path": rule_exists,
            "path_marked_loaded": loaded,
            "sha256": sha256_file(full_path),
            "verified": path_exists and rule_exists and loaded,
        })
    return refs


def confidence(loaded: list[dict[str, Any]], refs: list[dict[str, Any]]) -> str:
    if refs and all(bool(item.get("verified")) for item in refs):
        return "applied_evidence_verified"
    if refs:
        return "applied_evidence_mismatch"
    if loaded:
        return "loaded_files_recorded"
    return "selected_only"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-id")
    parser.add_argument("--evidence-file", help="File containing the final Spec Evidence block")
    parser.add_argument("--allow-missing-evidence", action="store_true")
    parser.add_argument(
        "--require-evidence",
        action="store_true",
        help="Fail unless Spec Evidence contains file_path#RULE-ID references or No explicit spec rule found.",
    )
    parser.add_argument(
        "--require-loaded-selected",
        choices=["none", "command", "all"],
        default="none",
        help="Fail if selected files at this level were not marked loaded.",
    )
    parser.add_argument("--policy", help="Trace policy JSON file with step-level required selected loads.")
    parser.add_argument(
        "--require-policy",
        action="store_true",
        help="Fail if --policy is missing or selected policy-required files were not marked loaded.",
    )
    args = parser.parse_args()

    trace_id = resolve_trace_id(args.trace_id)
    if not trace_id:
        raise SystemExit("Unable to resolve trace_id.")

    record = selected_record(trace_id)
    session_dir = TRACE_DIR / "sessions" / trace_id
    loaded = load_jsonl(session_dir / "loaded-files.jsonl")
    loaded_paths = {str(item.get("path", "")) for item in loaded if item.get("path")}
    selected = set(selected_paths(record))
    policy, policy_file = load_policy(args.policy, args.require_policy)
    policy_required_files, policy_paths_not_selected = policy_required_loaded_files(record, policy)

    evidence_text = ""
    if args.evidence_file:
        evidence_path = Path(args.evidence_file)
        evidence_path = evidence_path if evidence_path.is_absolute() else ROOT / evidence_path
        if not evidence_path.exists():
            raise SystemExit(f"Evidence file not found: {args.evidence_file}")
        evidence_text = evidence_path.read_text(encoding="utf-8")

    refs = evidence_references(evidence_text, loaded_paths) if evidence_text else []
    no_explicit_spec_rule_found = "No explicit spec rule found." in evidence_text
    trace_confidence = confidence(loaded, refs)
    applied_rule_ids = sorted({str(item["rule_id"]) for item in refs})
    selected_rule_ids = sorted(str(rule_id) for rule_id in (record.get("selected_rule_ids") or []))
    loaded_rule_ids = sorted({
        str(rule_id)
        for item in loaded
        for rule_id in (item.get("rule_ids") or [])
    })

    required_loaded_files: set[str] = set()
    if args.require_loaded_selected == "command":
        required_loaded_files.update(str(item) for item in (record.get("selected_command_files") or []))
    elif args.require_loaded_selected == "all":
        required_loaded_files.update(selected)
    required_loaded_files.update(policy_required_files)
    missing_required_loaded_files = sorted(required_loaded_files - loaded_paths)

    all_refs_verified: bool | None
    if refs:
        all_refs_verified = all(bool(item.get("verified")) for item in refs)
    elif no_explicit_spec_rule_found or args.allow_missing_evidence:
        all_refs_verified = None
    else:
        all_refs_verified = None

    evidence_present = bool(refs) or no_explicit_spec_rule_found
    evidence_required_satisfied = evidence_present or not args.require_evidence
    required_loaded_files_satisfied = not missing_required_loaded_files

    final = {
        "trace_schema_version": "1.1",
        "timestamp": now(),
        "trace_id": trace_id,
        "workflow_step": record.get("workflow_step", ""),
        "request_type": record.get("request_type", ""),
        "trace_confidence": trace_confidence,
        "selected_command_files": record.get("selected_command_files", []),
        "selected_reference_files": record.get("selected_reference_files", []),
        "selected_agent_files": record.get("selected_agent_files", []),
        "selected_files": sorted(selected),
        "selected_rule_ids": selected_rule_ids,
        "loaded_files": loaded,
        "selected_not_loaded": sorted(selected - loaded_paths),
        "loaded_not_selected": sorted(loaded_paths - selected),
        "loaded_rule_ids": loaded_rule_ids,
        "applied_rule_ids": applied_rule_ids,
        "spec_evidence": {
            "references": refs,
            "no_explicit_spec_rule_found": no_explicit_spec_rule_found,
        },
        "verification": {
            "all_applied_evidence_verified": all_refs_verified,
            "evidence_required": args.require_evidence,
            "evidence_required_satisfied": evidence_required_satisfied,
            "required_loaded_files_satisfied": required_loaded_files_satisfied,
            "required_loaded_files": sorted(required_loaded_files),
            "missing_required_loaded_files": missing_required_loaded_files,
            "policy_file": policy_file,
            "policy_required_files": sorted(policy_required_files),
            "policy_paths_not_selected": policy_paths_not_selected,
            "policy_scope": "selected files only; policy paths not selected are reported but not forced",
            "note": "This verifies file/hash/rule citation consistency, not model comprehension.",
        },
    }

    session_output = session_dir / "final-runtime-trace.json"
    latest_output = TRACE_DIR / "latest-runtime-trace-final.json"
    write_json(session_output, final)
    write_json(latest_output, final)
    print(str(latest_output))

    if args.require_evidence and not evidence_present:
        return 1
    if refs and not all(bool(item.get("verified")) for item in refs):
        return 1
    if missing_required_loaded_files:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
