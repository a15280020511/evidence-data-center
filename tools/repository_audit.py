#!/usr/bin/env python3
"""Deterministic, read-only audit for an isolated decision-center repository."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

IGNORED_PARTS = {
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__",
    "audit-artifacts", "artifacts", "validation-artifacts", "ticket-artifacts",
    "runtime-state", "performance-state", "tmp-test-artifacts",
}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
PINNED_ACTION_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}(?:\s*#.*)?$")
SENSITIVE_NAME_RE = re.compile(r"(?i)(api[_-]?key|secret|token|password|credential)")
PLACEHOLDER_RE = re.compile(r"(?i)(example|placeholder|dummy|redacted|replace[-_ ]?me|not[-_ ]?set|your[-_ ])")
REQ_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*(?:==|~=|>=|<=|>|<|!=).*$")
HISTORICAL_FILES = {"MIGRATION.md", "MIGRATION_PROVENANCE.json", "RECOVERY.md"}


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class FileRecord:
    path: str
    size_bytes: int
    sha256: str
    line_count: int | None
    kind: str


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        yield path


def decode_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def kind(path: Path) -> str:
    name = path.name.lower()
    if path.suffix == ".py": return "python"
    if path.suffix == ".json": return "json"
    if path.suffix in {".yml", ".yaml"}: return "yaml"
    if path.suffix == ".md": return "markdown"
    if path.suffix == ".sh": return "shell"
    if "requirements" in name and path.suffix == ".txt": return "requirements"
    if name == "dockerfile" or name.endswith(".dockerfile"): return "dockerfile"
    return "text"


def complexity(node: ast.AST) -> int:
    score = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.IfExp, ast.Match, ast.comprehension)):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(1, len(child.values) - 1)
    return score


def assignment_names(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for item in target.elts for name in assignment_names(item)]
    return []


def python_audit(rel: str, text: str) -> tuple[list[Finding], dict[str, Any], set[str]]:
    findings: list[Finding] = []
    metrics = {"functions": 0, "classes": 0, "max_complexity": 0, "max_function_lines": 0}
    imports: set[str] = set()
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        return [Finding("critical", "PY-SYNTAX", rel, int(exc.lineno or 1), str(exc))], metrics, imports

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            metrics["functions"] += 1
            score = complexity(node)
            metrics["max_complexity"] = max(metrics["max_complexity"], score)
            length = int(getattr(node, "end_lineno", node.lineno)) - int(node.lineno) + 1
            metrics["max_function_lines"] = max(metrics["max_function_lines"], length)
            if score > 20:
                findings.append(Finding("medium", "PY-COMPLEXITY", rel, node.lineno, f"function {node.name!r} complexity={score}"))
            if length > 180:
                findings.append(Finding("medium", "PY-FUNCTION-SIZE", rel, node.lineno, f"function {node.name!r} spans {length} lines"))
        elif isinstance(node, ast.ClassDef):
            metrics["classes"] += 1
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                findings.append(Finding("high", "PY-BARE-EXCEPT", rel, node.lineno, "bare except hides termination and programming errors"))
            elif isinstance(node.type, ast.Name) and node.type.id == "BaseException":
                findings.append(Finding("high", "PY-BASE-EXCEPTION", rel, node.lineno, "BaseException handler catches process termination"))
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in {"eval", "exec"}:
                findings.append(Finding("critical", "PY-DYNAMIC-CODE", rel, node.lineno, f"use of {func.id}()"))
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                owner, name = func.value.id, func.attr
                if owner == "os" and name == "system":
                    findings.append(Finding("critical", "PY-OS-SYSTEM", rel, node.lineno, "os.system executes a shell"))
                if owner == "subprocess" and any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                    findings.append(Finding("critical", "PY-SHELL-TRUE", rel, node.lineno, "subprocess call uses shell=True"))
                if owner in {"pickle", "dill"} and name in {"load", "loads"}:
                    findings.append(Finding("high", "PY-UNSAFE-DESERIALIZE", rel, node.lineno, f"{owner}.{name} can execute an untrusted payload"))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and "tests" not in Path(rel).parts and rel != "tools/repository_audit.py":
            targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                names = [name for target in targets for name in assignment_names(target)]
                literal = value.value
                if any(SENSITIVE_NAME_RE.search(name) for name in names) and len(literal) >= 12 and not PLACEHOLDER_RE.search(literal):
                    findings.append(Finding("critical", "PY-HARDCODED-CREDENTIAL", rel, int(getattr(node, "lineno", 1)), f"sensitive variable {names[0]!r} contains a literal value"))
    return findings, metrics, imports


def line_audit(rel: str, text: str, file_kind: str) -> list[Finding]:
    findings: list[Finding] = []
    for index, line in enumerate(text.splitlines(), 1):
        if line.rstrip(" \t") != line:
            findings.append(Finding("low", "TXT-TRAILING-WHITESPACE", rel, index, "trailing whitespace"))
        if "\t" in line and file_kind in {"python", "yaml", "json"}:
            findings.append(Finding("low", "TXT-TAB", rel, index, "tab character in structured source"))
        if len(line) > 220 and not re.search(r"https?://|sha256|BEGIN|END", line):
            findings.append(Finding("low", "TXT-LONG-LINE", rel, index, f"line length={len(line)}"))
        if rel != "tools/repository_audit.py" and re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
            findings.append(Finding("medium", "TXT-DEBT-MARKER", rel, index, line.strip()[:240]))
        if "a15280020511/test" in line and Path(rel).name not in HISTORICAL_FILES:
            findings.append(Finding("medium", "ARCH-LEGACY-REPOSITORY", rel, index, "legacy repository reference remains outside migration provenance"))
        if file_kind == "yaml" and re.match(r"\s*repository_dispatch\s*:", line):
            findings.append(Finding("critical", "ARCH-CROSS-REPO-DISPATCH", rel, index, "repository_dispatch violates center isolation"))
        if file_kind == "yaml" and re.match(r"\s*pull_request_target\s*:", line):
            findings.append(Finding("high", "GHA-PR-TARGET", rel, index, "pull_request_target expands workflow trust"))
        if file_kind == "yaml" and re.search(r"\bpermissions:\s*write-all\b", line):
            findings.append(Finding("critical", "GHA-WRITE-ALL", rel, index, "workflow grants write-all"))
        if file_kind == "yaml" and re.match(r"\s*uses:\s*", line):
            action = line.split("uses:", 1)[1].strip()
            if not action.startswith(("./", "docker://")) and not PINNED_ACTION_RE.match(action):
                findings.append(Finding("high", "GHA-UNPINNED-ACTION", rel, index, f"action is not pinned to a full commit SHA: {action}"))
    return findings


def audit(root: Path) -> dict[str, Any]:
    findings: list[Finding] = []
    files: list[FileRecord] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    requirements: dict[str, str] = {}
    python_metrics: dict[str, dict[str, Any]] = {}
    python_imports: dict[str, set[str]] = {}
    parsed_json = 0

    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        hashes[digest].append(rel)
        file_kind = kind(path)
        text = decode_text(path)
        files.append(FileRecord(rel, len(data), digest, None if text is None else len(text.splitlines()), file_kind))
        if len(data) > 2_000_000:
            findings.append(Finding("medium", "FILE-LARGE", rel, 1, f"repository file size={len(data)} bytes"))
        if text is None:
            continue
        findings.extend(line_audit(rel, text, file_kind))
        if file_kind == "python":
            py_findings, metrics, imports = python_audit(rel, text)
            findings.extend(py_findings)
            python_metrics[rel] = metrics
            python_imports[rel] = imports
        elif file_kind == "json":
            try:
                json.loads(text)
                parsed_json += 1
            except json.JSONDecodeError as exc:
                findings.append(Finding("critical", "JSON-PARSE", rel, exc.lineno, exc.msg))
        elif file_kind == "requirements":
            requirements[rel] = text

    for digest, paths in hashes.items():
        nontrivial = [p for p in paths if not p.endswith(("__init__.py", ".gitkeep"))]
        if len(nontrivial) > 1:
            findings.append(Finding("low", "FILE-DUPLICATE", nontrivial[0], 1, f"identical content shared by {nontrivial}; sha256={digest}"))

    package_specs: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for rel, text in requirements.items():
        for index, raw in enumerate(text.splitlines(), 1):
            value = raw.strip()
            if not value or value.startswith("#") or value.startswith("-r "):
                continue
            match = REQ_RE.match(value)
            if not match:
                findings.append(Finding("medium", "REQ-UNPINNED", rel, index, f"dependency is not constrained: {value}"))
                continue
            package_specs[match.group(1).lower().replace("_", "-")].append((rel, index, value))
    for package, specs in package_specs.items():
        values = {spec for _, _, spec in specs}
        if len(values) > 1:
            findings.append(Finding("medium", "REQ-CONFLICTING-SPECS", specs[0][0], specs[0][1], f"{package} has multiple constraints: {sorted(values)}"))

    imported = set().union(*python_imports.values()) if python_imports else set()
    orphan_candidates = []
    for rel in sorted(python_metrics):
        path = Path(rel)
        if "tests" in path.parts or path.name in {"__init__.py", "repository_audit.py"} or path.parts[0] == "tools":
            continue
        if path.stem not in imported and not path.name.endswith("_task.py"):
            orphan_candidates.append(rel)
            findings.append(Finding("info", "PY-ORPHAN-CANDIDATE", rel, 1, "module is not imported by another Python file; verify workflow or CLI use before removal"))

    findings.sort(key=lambda x: (SEVERITY_ORDER[x.severity], x.path, x.line, x.rule))
    counts = Counter(item.severity for item in findings)
    return {
        "schema_version": "repository-audit-v3",
        "file_count": len(files),
        "text_file_count": sum(record.line_count is not None for record in files),
        "python_file_count": len(python_metrics),
        "total_lines": sum(record.line_count or 0 for record in files),
        "finding_counts": {name: counts.get(name, 0) for name in SEVERITY_ORDER},
        "findings": [asdict(item) for item in findings],
        "files": [asdict(item) for item in files],
        "python_metrics": python_metrics,
        "orphan_candidates": orphan_candidates,
        "parsed_json_files": parsed_json,
    }


def markdown(report: dict[str, Any]) -> str:
    rows = [
        "# Full Repository Audit", "",
        f"- Files: `{report['file_count']}`", f"- Lines inspected: `{report['total_lines']}`",
        f"- Critical: `{report['finding_counts']['critical']}`", f"- High: `{report['finding_counts']['high']}`",
        f"- Medium: `{report['finding_counts']['medium']}`", f"- Low: `{report['finding_counts']['low']}`",
        f"- Info: `{report['finding_counts']['info']}`", "", "## Findings", "",
        "| Severity | Rule | File | Line | Finding |", "|---|---|---|---:|---|",
    ]
    for item in report["findings"]:
        message = str(item["message"]).replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {item['severity']} | `{item['rule']}` | `{item['path']}` | {item['line']} | {message} |")
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="audit-artifacts")
    parser.add_argument("--fail-on", choices=("none", "critical", "high"), default="high")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report = audit(Path(args.root).resolve())
    (output / "repository-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "repository-audit.md").write_text(markdown(report), encoding="utf-8")
    summary = {"status": "PASS" if not report["finding_counts"]["critical"] and not report["finding_counts"]["high"] else "FINDINGS", "finding_counts": report["finding_counts"], "file_count": report["file_count"], "total_lines": report["total_lines"]}
    print(json.dumps(summary, ensure_ascii=False))
    for item in report["findings"][:50]:
        print(f"::{ 'error' if item['severity'] in {'critical','high'} else 'warning' } file={item['path']},line={item['line']}::{item['severity']} {item['rule']}: {item['message']}")
    if args.fail_on == "critical" and report["finding_counts"]["critical"]:
        return 1
    if args.fail_on == "high" and (report["finding_counts"]["critical"] or report["finding_counts"]["high"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
