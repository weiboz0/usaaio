from __future__ import annotations

import math
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from tools.model import Report, _parse_yaml, load_mock_manifests

SHINGLE_SIZE = 8
SHINGLE_THRESHOLD = 2
COSINE_THRESHOLD = 0.35
REMEDY = "reference corpus absent; run bash scripts/fetch-reference.sh"


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _shingles(text: str) -> set[tuple[str, ...]]:
    words = _words(text)
    return {tuple(words[i : i + SHINGLE_SIZE]) for i in range(max(0, len(words) - SHINGLE_SIZE + 1))}


def _tf(text: str) -> Counter[str]:
    return Counter(_words(text))


def _cosine(query: str, document: str, documents: list[str]) -> float:
    q_tf = _tf(query)
    d_tf = _tf(document)
    if not q_tf or not d_tf:
        return 0.0
    doc_count = len(documents) + 1
    dfs: Counter[str] = Counter()
    for doc in [*documents, query]:
        dfs.update(set(_words(doc)))
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


def _corpus(root: Path) -> tuple[list[tuple[str, str]], str | None]:
    reference = root / "reference"
    # PDFs alone are a valid corpus (spec Task 5); index.yaml text fields are additive.
    if not reference.exists() or not (
        any(reference.glob("*/index.yaml")) or any(reference.glob("*/*.pdf"))
    ):
        return [], REMEDY
    if shutil.which("pdftotext") is None:
        return [], f"pdftotext unavailable; {REMEDY}"
    parts: list[tuple[str, str]] = []
    for ref_dir in sorted(reference.glob("*")):
        if not ref_dir.is_dir():
            continue
        index = ref_dir / "index.yaml"
        if index.exists():
            try:
                for offset, text in enumerate(_collect_text_fields(_parse_yaml(index.read_text()))):
                    parts.append((f"{index}#text-{offset}", text))
            except (OSError, ValueError) as exc:
                return [], f"{index}: cannot read corpus index ({exc}); {REMEDY}"
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
    if not parts:
        return [], REMEDY
    return parts, None


def _problem_text(root: Path, manifest_path: Path, problem) -> tuple[str, list[str]]:
    warnings: list[str] = []
    texts = [problem.spec]
    if not problem.files:
        warnings.append(f"{manifest_path}: {problem.id} has no files; scanning spec only")
    for rel in problem.files:
        path = manifest_path.parent / rel
        if path.exists():
            texts.append(path.read_text(errors="ignore"))
        else:
            warnings.append(f"{manifest_path}: {problem.id} listed missing file {rel}")
    return "\n".join(texts), warnings


def check_overlap(root: str | Path) -> Report:
    root = Path(root)
    corpus, skipped = _corpus(root)
    if skipped:
        return Report(name="overlap-scan", ok=True, skipped=skipped)
    corpus_texts = [text for _, text in corpus]
    errors: list[str] = []
    warnings: list[str] = []
    for manifest in load_mock_manifests(root):
        for problem in manifest.problems:
            text, text_warnings = _problem_text(root, manifest.path, problem)
            warnings.extend(text_warnings)
            problem_shingles = _shingles(text)
            for label, reference_text in corpus:
                overlap = len(problem_shingles & _shingles(reference_text))
                cosine = _cosine(text, reference_text, corpus_texts)
                if overlap >= SHINGLE_THRESHOLD or cosine >= COSINE_THRESHOLD:
                    hit = f"{manifest.path}: {problem.id} overlaps {label} (shingles={overlap}, cosine={cosine:.2f})"
                    if problem.provenance == "adapted" and problem.adapted_from:
                        warnings.append(hit)
                    else:
                        errors.append(hit)
                    break
    return Report(name="overlap-scan", ok=not errors, errors=errors, warnings=warnings)
