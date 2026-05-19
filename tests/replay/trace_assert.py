"""Assertions for Harness Trace replay tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_trace(path: str | Path) -> dict[str, Any]:
    trace_path = Path(path)
    text = trace_path.read_text(encoding="utf-8")
    if trace_path.suffix == ".jsonl":
      line = next((ln for ln in reversed(text.splitlines()) if ln.strip()), "{}")
      return json.loads(line)
    if trace_path.suffix == ".json":
      return json.loads(text)
    return {"raw_text": text, "loaded_rule_ids": _extract_rule_ids(text)}


def _extract_rule_ids(text: str) -> list[str]:
    import re

    return sorted(set(re.findall(r"RULE-[A-Z0-9-]+-[0-9]+", text)))


def rule_ids(trace: dict[str, Any]) -> set[str]:
    ids = trace.get("loaded_rule_ids")
    if isinstance(ids, list) and ids:
        return {str(item) for item in ids}
    raw = trace.get("raw_text", "")
    if isinstance(raw, str):
        return set(_extract_rule_ids(raw))
    return set()


def check_trace(trace: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, str]]:
    found = rule_ids(trace)
    results: list[dict[str, str]] = []

    for rule_id in expected.get("must_include_rule_ids", []) or []:
        results.append({
            "section": "Harness Trace Check",
            "status": "PASS" if rule_id in found else "FAIL",
            "item": str(rule_id),
        })

    for rule_id in expected.get("must_not_include_rule_ids", []) or []:
        results.append({
            "section": "Harness Trace Check",
            "status": "PASS" if rule_id not in found else "FAIL",
            "item": f"not {rule_id}",
        })

    return results
