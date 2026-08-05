"""Detect reference overlap at the granularity appropriate to each artifact.

Following the plan-004 unit-path precedent, short structured mock manifest specs
provide the TF-IDF cosine signal. Full mock statement files, like unit practice
files, are checked only for verbatim-copy risk with lexical shingles.
"""

from __future__ import annotations

import math
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import nbformat

from tools.model import Report, _parse_yaml, load_mock_manifests

SHINGLE_SIZE = 8
SHINGLE_THRESHOLD = 2
COSINE_THRESHOLD = 0.35
REMEDY = "reference corpus absent; run bash scripts/fetch-reference.sh"

# Register mandated by mocktests/blueprint.yaml style_rules must not dominate
# mock-test cosine similarity. These patterns intentionally cover only that register.
MOCK_REGISTER_BOILERPLATE_PATTERNS = (
    r"(?im)^\s*(?:\*\*)?Total:\s*\d+\s+points?\.?(?:\*\*)?\s*$",
    r"(?i)(?:#+\s*)?Part\s+\d+\.\d+\s*\(\s*\d+\s+points?\s*\)",
    r"(?i)\bReasoning\s+(?:is\s+)?(?:not\s+)?required\b[.;]?",
    r"(?i)\bCoding\s+(?:is\s+)?(?:not\s+)?(?:allowed|required|needed)\b[.;]?",
    r"(?im)^\s*[-*]?\s*(?:\*\*)?[A-E][.)](?:\*\*)?\s*",
    r"(?im)\bWrite\s+[^\n]*?\s+in\s+the\s+unique\s+form\b[^\n]*",
    r"(?i)\bWhat\s+is\s+\$?p\s*\+\s*q\$?\s*\?",
)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _shingles(text: str) -> set[tuple[str, ...]]:
    words = _words(text)
    return {tuple(words[i : i + SHINGLE_SIZE]) for i in range(max(0, len(words) - SHINGLE_SIZE + 1))}


def _without_boilerplate(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if (
            stripped.startswith(("import ", "from "))
            or "default_rng" in line
            or "SEED =" in line
        ):
            continue
        lines.append(line)
    return "\n".join(lines)


def _without_mock_register_boilerplate(text: str) -> str:
    for pattern in MOCK_REGISTER_BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text)
    return text


def _tf(text: str) -> Counter[str]:
    return Counter(_words(text))


def _corpus_dfs(documents: list[str]) -> Counter[str]:
    dfs: Counter[str] = Counter()
    for doc in documents:
        dfs.update(set(_words(doc)))
    return dfs


def _cosine(query: str, document: str, doc_count: int, base_dfs: Counter[str]) -> float:
    q_tf = _tf(query)
    d_tf = _tf(document)
    if not q_tf or not d_tf:
        return 0.0
    dfs = base_dfs.copy()
    dfs.update(set(_words(query)))
    terms = set(q_tf) | set(d_tf)
    numerator = 0.0
    q_norm = 0.0
    d_norm = 0.0
    for term in terms:
        idf = math.log((1 + doc_count) / (1 + dfs[term])) + 1
        q_weight = q_tf[term] * idf
        d_weight = d_tf[term] * idf
        numerator += q_weight * d_weight
        q_norm += q_weight * q_weight
        d_norm += d_weight * d_weight
    if q_norm == 0 or d_norm == 0:
        return 0.0
    return numerator / math.sqrt(q_norm * d_norm)


def _collect_text_fields(node: Any) -> list[str]:
    if isinstance(node, dict):
        texts = [str(node["text"])] if node.get("text") else []
        for value in node.values():
            texts.extend(_collect_text_fields(value))
        return texts
    if isinstance(node, list):
        texts: list[str] = []
        for value in node:
            texts.extend(_collect_text_fields(value))
        return texts
    return []


def _corpus(root: Path) -> tuple[list[tuple[str, str]], str | None, list[str]]:
    reference = root / "reference"
    # PDFs alone are a valid corpus (spec Task 5); index.yaml text fields are additive.
    if not reference.exists() or not (
        any(reference.glob("*/index.yaml")) or any(reference.glob("*/*.pdf"))
    ):
        return [], REMEDY, []
    if shutil.which("pdftotext") is None:
        return [], f"pdftotext unavailable; {REMEDY}", []
    parts: list[tuple[str, str]] = []
    failures: list[str] = []
    for ref_dir in sorted(reference.glob("*")):
        if not ref_dir.is_dir():
            continue
        index = ref_dir / "index.yaml"
        if index.exists():
            try:
                for offset, text in enumerate(_collect_text_fields(_parse_yaml(index.read_text()))):
                    parts.append((f"{index}#text-{offset}", text))
            except (OSError, ValueError) as exc:
                return [], f"{index}: cannot read corpus index ({exc}); {REMEDY}", []
        for pdf in sorted(ref_dir.glob("*.pdf")):
            proc = subprocess.run(
                ["pdftotext", str(pdf), "-"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                parts.append((str(pdf), proc.stdout))
            else:
                # A silently-dropped corpus part would let copied content escape
                # scanning; surface every extraction failure as a loud warning.
                failures.append(
                    f"corpus part NOT scanned (pdftotext failed, rc={proc.returncode}): {pdf}"
                )
    if not parts:
        return [], REMEDY, failures
    return parts, None, failures


def _problem_texts(root: Path, manifest_path: Path, problem) -> tuple[str, str, list[str]]:
    warnings: list[str] = []
    statement_texts: list[str] = []
    if not problem.files:
        warnings.append(f"{manifest_path}: {problem.id} has no files; scanning spec only")
    for rel in problem.files:
        path = manifest_path.parent / rel
        if path.exists():
            statement_texts.append(path.read_text(errors="ignore"))
        else:
            warnings.append(f"{manifest_path}: {problem.id} listed missing file {rel}")
    return problem.spec, "\n".join(statement_texts), warnings


def _notebook_text(path: Path) -> str:
    notebook = nbformat.read(path, as_version=4)
    return "\n".join(
        str(cell.get("source", ""))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") in {"markdown", "code"}
    )


def check_overlap(root: str | Path) -> Report:
    root = Path(root)
    corpus, skipped, corpus_failures = _corpus(root)
    if skipped:
        return Report(name="overlap-scan", ok=True, skipped=skipped)
    corpus_texts = [text for _, text in corpus]
    corpus_cosine_texts = [_without_mock_register_boilerplate(text) for text in corpus_texts]
    # Hoisted per-corpus precomputation: shingles per reference doc + document frequencies
    # (previously recomputed inside the per-problem loop — O(P x R x |corpus|)).
    corpus_shingles = [
        (label, text, _shingles(text), _without_mock_register_boilerplate(text))
        for label, text in corpus
    ]
    base_dfs = _corpus_dfs(corpus_cosine_texts)
    doc_count = len(corpus_texts) + 1
    errors: list[str] = []
    warnings: list[str] = list(corpus_failures)
    for manifest in load_mock_manifests(root):
        for problem in manifest.problems:
            spec_text, statement_text, text_warnings = _problem_texts(
                root, manifest.path, problem
            )
            warnings.extend(text_warnings)
            problem_shingles = _shingles(_without_boilerplate(statement_text))
            cosine_text = _without_mock_register_boilerplate(
                _without_boilerplate(spec_text)
            )
            for label, _, reference_shingles, reference_cosine_text in corpus_shingles:
                overlap = len(problem_shingles & reference_shingles)
                cosine = _cosine(cosine_text, reference_cosine_text, doc_count, base_dfs)
                if overlap >= SHINGLE_THRESHOLD or cosine >= COSINE_THRESHOLD:
                    hit = f"{manifest.path}: {problem.id} overlaps {label} (shingles={overlap}, cosine={cosine:.2f})"
                    if problem.provenance == "adapted" and problem.adapted_from:
                        warnings.append(hit)
                    else:
                        errors.append(hit)
                    break
    for path in sorted(root.glob("units/*/practice/*.ipynb")):
        text = _without_boilerplate(_notebook_text(path))
        notebook_shingles = _shingles(text)
        for label, _, reference_shingles, _ in corpus_shingles:
            overlap = len(notebook_shingles & reference_shingles)
            if overlap >= SHINGLE_THRESHOLD:
                errors.append(f"{path} overlaps {label} (shingles={overlap})")
                break
    return Report(name="overlap-scan", ok=not errors, errors=errors, warnings=warnings)
