#!/usr/bin/env python3
"""
Workflow Doctor: GitHub Actions diagnostics for agents.

This tool inspects workflows under .github/workflows and surfaces common
configuration problems that frequently trip up automation agents.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Any, Dict, Iterable, List, Tuple

import yaml

WORKFLOWS_ROOT = Path(".github/workflows")


@dataclass
class Diagnostic:
    workflow: str
    level: str
    message: str


PIN_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"@[0-9a-f]{40}$"), "commit SHA"),
    (re.compile(r"@v?\d+(\.\d+){0,2}$"), "version tag"),
)
FLOATING_REFS = {"main", "master", "latest", "HEAD"}


def load_workflow(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:  # type: ignore[attr-defined]
        raise ValueError(f"{path}: YAML parsing failed ({exc})") from exc


def find_workflow_files() -> List[Path]:
    if not WORKFLOWS_ROOT.exists():
        return []
    return sorted(
        [path for path in WORKFLOWS_ROOT.iterdir() if path.suffix in {".yml", ".yaml"}]
    )


def list_triggers(on_field: Any) -> List[str]:
    if on_field is None:
        return []
    if isinstance(on_field, list):
        return [str(item) for item in on_field]
    if isinstance(on_field, dict):
        return [str(key) for key in on_field.keys()]
    return [str(on_field)]


def list_jobs(data: Dict[str, Any]) -> List[str]:
    jobs = data.get("jobs", {})
    if isinstance(jobs, dict):
        return list(jobs.keys())
    return []


def walk_uses(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "uses" and isinstance(child, str):
                yield child
            else:
                yield from walk_uses(child)
    elif isinstance(value, list):
        for item in value:
            yield from walk_uses(item)


def classify_reference(uses_value: str) -> str:
    if "@" not in uses_value:
        return "unversioned"
    reference = uses_value.split("@", 1)[1]
    if reference in FLOATING_REFS:
        return "floating"
    for pattern, label in PIN_PATTERNS:
        if pattern.search(uses_value):
            return label
    if re.match(r"^[0-9a-f]{7,}$", reference):
        return "short SHA"
    return "custom tag"


def diagnose_permissions(data: Dict[str, Any], workflow_name: str) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    if "permissions" not in data:
        diagnostics.append(
            Diagnostic(
                workflow=workflow_name,
                level="warning",
                message=(
                    "Missing top-level 'permissions'. Explicit permissions reduce "
                    "unexpected write access for the GITHUB_TOKEN."
                ),
            )
        )
    return diagnostics


def diagnose_uses(data: Dict[str, Any], workflow_name: str) -> Tuple[List[Diagnostic], List[str]]:
    diagnostics: List[Diagnostic] = []
    uses_entries = list(walk_uses(data))
    for uses_value in uses_entries:
        classification = classify_reference(uses_value)
        if classification in {"unversioned", "floating"}:
            diagnostics.append(
                Diagnostic(
                    workflow=workflow_name,
                    level="warning",
                    message=(
                        f"'{uses_value}' is {classification}; pin actions to a tag or SHA "
                        "to prevent supply-chain surprises."
                    ),
                )
            )
    return diagnostics, uses_entries


def summarize_workflow(path: Path) -> Tuple[str, Dict[str, Any], List[Diagnostic], List[str]]:
    data = load_workflow(path)
    name = data.get("name", path.stem)
    diagnostics: List[Diagnostic] = []
    diagnostics.extend(diagnose_permissions(data, name))
    uses_diags, uses_entries = diagnose_uses(data, name)
    diagnostics.extend(uses_diags)
    return name, data, diagnostics, uses_entries


def render_summary(name: str, path: Path, data: Dict[str, Any], uses_entries: List[str]) -> str:
    triggers = list_triggers(data.get("on"))
    jobs = list_jobs(data)
    lines = [f"=== Workflow: {name} ({path}) ==="]
    lines.append(f"Triggers: {', '.join(triggers) if triggers else 'None detected'}")
    lines.append(f"Jobs: {', '.join(jobs) if jobs else 'None detected'}")
    if uses_entries:
        lines.append("Action references:")
        for uses_value in sorted(set(uses_entries)):
            lines.append(f"  - {uses_value} ({classify_reference(uses_value)})")
    else:
        lines.append("Action references: none found")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect GitHub workflow files for common issues (missing permissions, "
            "unversioned actions, and trigger/job summaries)."
        )
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing .github/workflows (defaults to cwd).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only emit diagnostics; skip workflow summaries.",
    )
    args = parser.parse_args(argv)

    root = args.workdir
    global WORKFLOWS_ROOT
    WORKFLOWS_ROOT = root / ".github" / "workflows"

    workflow_files = find_workflow_files()
    if not workflow_files:
        print(f"No workflow files found under {WORKFLOWS_ROOT}.")
        return 0

    collected_diags: List[Diagnostic] = []
    for workflow_path in workflow_files:
        try:
            name, data, diagnostics, uses_entries = summarize_workflow(workflow_path)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            continue

        if not args.quiet:
            print(render_summary(name, workflow_path.relative_to(root), data, uses_entries))
            print()
        collected_diags.extend(diagnostics)

    if collected_diags:
        print("Diagnostics:")
        for diag in collected_diags:
            print(f"- [{diag.level.upper()}] {diag.workflow}: {diag.message}")
    else:
        print("No issues detected. Workflows look healthy!")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
