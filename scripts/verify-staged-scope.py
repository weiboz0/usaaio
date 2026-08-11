#!/usr/bin/env python3
"""Verify that Plan 019's atomic cutover contains only inventoried paths.

The cached check also enforces public-repository protected-path rules.  Its one
exception is the historical C8 tokenization lesson, whose migration may change
only the inventoried root-resolution cell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

import yaml


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=check
    )


def load_inventory(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path}: inventory must be a mapping")
    return raw


def changed_paths(mode: str, base: str | None = None) -> list[str]:
    if mode in {"--cached", "--protected-cached"}:
        out = git(
            "diff",
            "--cached",
            "--name-only",
            "-z",
            "--diff-filter=ACDMRTUXB",
        ).stdout
        return [path for path in out.split("\0") if path]
    if mode == "--protected-diff":
        out = git("diff", "HEAD", "--name-only", "-z", "--diff-filter=ACDMRTUXB").stdout
        return [path for path in out.split("\0") if path]
    if mode == "--protected-range":
        assert base is not None
        out = git(
            "diff", f"{base}..HEAD", "--name-only", "-z", "--diff-filter=ACDMRTUXB"
        ).stdout
        return [path for path in out.split("\0") if path]
    out = git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    records = out.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        status = record[:2]
        if status == "!!" or len(record) < 4:
            continue
        paths.append(record[3:])
        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise ValueError("git status returned an incomplete rename/copy record")
            paths.append(records[index])
            index += 1
    return paths


def allowed(path: str, inventory: dict) -> bool:
    scope = inventory.get("staged_scope", {})
    return path in set(scope.get("exact_files", [])) or any(
        path.startswith(prefix) for prefix in scope.get("prefixes", [])
    )


def protected_category(path: str) -> str | None:
    lowered = path.lower()
    name = PurePosixPath(lowered).name
    if name == ".gh-token" or "token" in lowered:
        return "token"
    if name == ".env" or name.startswith(".env."):
        return "env"
    if "secret" in lowered:
        return "secret"
    if "credential" in lowered:
        return "credential"
    if "/reference/r" in lowered and any(
        lowered.endswith(ext) for ext in (".pdf", ".doc", ".docx", ".txt")
    ):
        return "raw-paper"
    if "/students/" in lowered or "student-data" in lowered:
        return "student-data"
    if "/build/" in lowered or lowered.endswith("_solution.html"):
        return "generated-artifact"
    return None


def staged_status() -> dict[str, str]:
    rows = git("diff", "--cached", "--name-status", "-M").stdout.splitlines()
    result: dict[str, str] = {}
    for row in rows:
        fields = row.split("\t")
        status = fields[0]
        if status.startswith("R") and len(fields) == 3:
            result[fields[2]] = status
        elif len(fields) >= 2:
            result[fields[-1]] = status
    return result


def blob(ref: str, path: str) -> bytes:
    spec = f":{path}" if ref == ":" else f"{ref}:{path}"
    proc = subprocess.run(["git", "show", spec], capture_output=True, check=False)
    if proc.returncode:
        raise ValueError(f"cannot read {spec}")
    return proc.stdout


def validate_token_exception(
    path: str, inventory: dict, *, old_ref: str, new_ref: str, status: str
) -> None:
    exception = inventory.get("token_path_exception", {})
    old_path = exception.get("old_path")
    new_path = exception.get("new_path")
    cells = exception.get("path_resolution_cells")
    if path != new_path or not isinstance(old_path, str) or cells != [1]:
        raise ValueError(f"protected token path: {path}")
    old_deleted = old_path in git(
        "diff", "--cached" if new_ref == ":" else f"{old_ref}..{new_ref}",
        "--name-only", "--diff-filter=D"
    ).stdout.splitlines()
    if not (status.startswith("R") or (status == "A" and old_deleted)):
        raise ValueError(f"protected token exception must be a rename with scoped cell rewrite: {path}")
    old = json.loads(blob(old_ref, old_path))
    new = json.loads(blob(new_ref, path))
    if len(old.get("cells", [])) != len(new.get("cells", [])):
        raise ValueError(f"protected token notebook cell count changed: {path}")
    for index, (before, after) in enumerate(zip(old["cells"], new["cells"], strict=True)):
        if index == 1:
            source_hash = hashlib.sha256(
                json.dumps(
                    after.get("source", []), ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest()
            if source_hash != exception.get("path_resolution_source_sha256"):
                raise ValueError(f"protected token notebook path cell is not the expected rewrite: {path}")
            candidate_before = dict(before)
            candidate_after = dict(after)
            candidate_before.pop("source", None)
            candidate_after.pop("source", None)
            if candidate_before != candidate_after:
                raise ValueError(f"protected token notebook path cell metadata changed: {path}")
        elif before != after:
            raise ValueError(f"protected token notebook non-path cell {index} changed: {path}")
    for key in set(old) | set(new):
        if key != "cells" and old.get(key) != new.get(key):
            raise ValueError(f"protected token notebook metadata changed: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", dest="mode", action="store_const", const="--preflight")
    modes.add_argument("--cached", dest="mode", action="store_const", const="--cached")
    modes.add_argument(
        "--protected-cached", dest="mode", action="store_const", const="--protected-cached"
    )
    modes.add_argument(
        "--protected-diff", dest="mode", action="store_const", const="--protected-diff"
    )
    modes.add_argument(
        "--protected-range", dest="mode", action="store_const", const="--protected-range"
    )
    parser.add_argument("--base")
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    inventory = load_inventory(args.inventory)
    failures: list[str] = []
    if args.mode == "--protected-range" and not args.base:
        parser.error("--protected-range requires --base")
    paths = changed_paths(args.mode, args.base)
    if args.mode in {"--preflight", "--cached"}:
        for path in paths:
            if not allowed(path, inventory):
                failures.append(f"outside Plan 019 staged scope: {path}")
    if args.mode in {
        "--cached", "--protected-cached", "--protected-diff", "--protected-range"
    }:
        token_exception = inventory.get("token_path_exception", {})
        exception_path = token_exception.get("new_path")
        exception_old_path = token_exception.get("old_path")
        if args.mode in {"--cached", "--protected-cached"}:
            deleted_paths = set(
                git("diff", "--cached", "--name-only", "--diff-filter=D").stdout.splitlines()
            )
        elif args.mode == "--protected-diff":
            deleted_paths = set(
                git("diff", "HEAD", "--name-only", "--diff-filter=D").stdout.splitlines()
            )
        else:
            deleted_paths = set(
                git(
                    "diff", f"{args.base}..HEAD", "--name-only", "--diff-filter=D"
                ).stdout.splitlines()
            )
        for path in paths:
            category = protected_category(path)
            if category is None:
                continue
            if path == exception_old_path and path in deleted_paths and exception_path in paths:
                continue
            if path == exception_path:
                try:
                    if args.mode in {"--cached", "--protected-cached"}:
                        status = staged_status().get(path, "")
                        old_ref, new_ref = "HEAD", ":"
                    elif args.mode == "--protected-diff":
                        status = git("diff", "HEAD", "--name-status", "-M").stdout
                        status = next(
                            (row.split("\t")[0] for row in status.splitlines() if row.endswith("\t" + path)),
                            "",
                        )
                        old_ref, new_ref = "HEAD", ":"
                    else:
                        rows = git("diff", f"{args.base}..HEAD", "--name-status", "-M").stdout
                        status = next(
                            (row.split("\t")[0] for row in rows.splitlines() if row.endswith("\t" + path)),
                            "",
                        )
                        old_ref, new_ref = args.base, "HEAD"
                    validate_token_exception(
                        path, inventory, old_ref=old_ref, new_ref=new_ref, status=status
                    )
                except ValueError as exc:
                    failures.append(str(exc))
            else:
                failures.append(f"protected {category} path: {path}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Plan 019 scope {args.mode[2:]}: {len(paths)} path(s) accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
