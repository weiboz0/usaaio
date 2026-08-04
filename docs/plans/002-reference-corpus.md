# Plan 002 — Reference Corpus Implementation Plan

> **For agentic workers:** Execute task-by-task with per-task commits. Steps use checkbox syntax.

**Goal:** Ingest the publicly available past USA-NA-AIO tests into local-only `reference/`, build a per-problem structured index, and commit an original analysis (`reference/analysis.md`) that will drive the syllabus, blueprint, and similarity tooling (plans 003–004).

**Architecture:** A committed fetch script re-downloads the corpus from public URLs on any machine (repeatability without committing copyrighted PDFs). Raw papers + per-problem index stay gitignored; only `analysis.md` — our own derived work, no verbatim problem text — is committed.

**Tech Stack:** bash + curl (fetch); PDFs read by the orchestrator/subagents; YAML index files (schema below, formalized by plan 004).

## Global Constraints

- **PUBLIC REPO:** under `reference/`, git may track ONLY `.gitkeep` and `analysis.md` (gitignore already enforces this). `analysis.md` must contain NO verbatim problem text — paraphrase everything; short technical terms (topic names, section titles) are fine.
- Corpus sources (from https://www.usaaio.org/past-problems, fetched 2026-08-03):
  - 2026 R1: Google Drive id `11z6HzS92y5f6OdeBf7GUtb7PBgF7_RlC` (verified: 6-page PDF)
  - 2026 R2 Day 1: id `1YXa62A14vF69ccAQjdWITwTCaCOoyscN`
  - 2026 R2 Day 2: id `1pp3PYo8f-M9HIvEs9VVKwCJAzIL-nmg4`
  - 2026 R2 Problems Design & Rationale: id `1C-2ewSPxNUX6dLL-oxE4FzhJBtjoOIo7`
  - 2025 R1 / R2: forum threads (https://forum.beaver-edge.ai/c/ai-olympiads/…/8 and …/9) — document URLs; ingest only if plainly downloadable, else record as a follow-up for manual export.
- Round 1 is the priority (design: target stage); R2 materials are ingested for later use but only lightly indexed.
- Semantic line breaks in docs.

---

### Task 1: Fetch script + corpus download

**Files:**
- Create: `scripts/fetch-reference.sh`
- Create (local-only, gitignored): `reference/r1-2026/paper.pdf`, `reference/r2-2026/day1.pdf`,
  `reference/r2-2026/day2.pdf`, `reference/r2-2026/rationale.pdf`

**Interfaces:**
- Produces: idempotent `bash scripts/fetch-reference.sh` — downloads any missing corpus file,
  verifies each is a PDF (`file` magic), never touches git-tracked paths.

- [ ] **Step 1: Write `scripts/fetch-reference.sh`**

```bash
#!/usr/bin/env bash
# Re-downloads the public past-test corpus into reference/ (gitignored, local-only).
# Sources: https://www.usaaio.org/past-problems (public Google Drive links).
# 2025 R1/R2 live in forum threads and are NOT auto-fetched:
#   https://forum.beaver-edge.ai/c/ai-olympiads/usa-north-america-ai-olympiad/8
#   https://forum.beaver-edge.ai/c/ai-olympiads/2025-usa-na-aio-round-2/9
set -euo pipefail
cd "$(dirname "$0")/.."

fetch() {  # fetch <drive-file-id> <dest-path>
  local id="$1" dest="$2"
  if [[ -s "$dest" ]]; then
    echo "exists: $dest"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  curl -sL "https://drive.google.com/uc?export=download&id=${id}" -o "$dest"
  if ! file "$dest" | grep -q 'PDF document'; then
    echo "FAIL: $dest is not a PDF (download blocked or link rotated)" >&2
    rm -f "$dest"
    return 1
  fi
  echo "fetched: $dest ($(file -b "$dest"))"
}

fetch "11z6HzS92y5f6OdeBf7GUtb7PBgF7_RlC" "reference/r1-2026/paper.pdf"
fetch "1YXa62A14vF69ccAQjdWITwTCaCOoyscN" "reference/r2-2026/day1.pdf"
fetch "1pp3PYo8f-M9HIvEs9VVKwCJAzIL-nmg4" "reference/r2-2026/day2.pdf"
fetch "1C-2ewSPxNUX6dLL-oxE4FzhJBtjoOIo7" "reference/r2-2026/rationale.pdf"

echo "corpus complete"
```

- [ ] **Step 2: Run it; verify all four PDFs land and re-run is a no-op**

Run: `chmod +x scripts/fetch-reference.sh && bash scripts/fetch-reference.sh && bash scripts/fetch-reference.sh`
Expected: four "fetched:" lines then four "exists:" lines; `corpus complete` twice.

- [ ] **Step 3: Verify git tracks nothing new under reference/**

Run: `git status --short reference/ ; git ls-files reference/`
Expected: no untracked entries shown (all ignored); ls-files lists only `reference/.gitkeep`.

- [ ] **Step 4: Commit**

```bash
git add scripts/fetch-reference.sh
git commit -m "feat: fetch script for public past-test corpus (reference/ stays local-only)"
```

---

### Task 2: Per-problem index (local-only)

**Files:**
- Create (local-only, gitignored): `reference/r1-2026/index.yaml`, `reference/r2-2026/index.yaml`

**Interfaces:**
- Produces: index schema consumed by plan 004's `overlap-scan` and plan 003's blueprint derivation:

```yaml
# reference/<test>/index.yaml
test: r1-2026            # corpus id
source_url: <url>
duration_minutes: <int|null>
sections:
  - name: <section title as printed>   # short titles are fine locally (file is untracked)
    problems:
      - id: r1-2026-p01
        type: theory | programming
        topics: [<free-form topic tags>]
        points: <int|null>
        difficulty: intro | core | advanced   # judgment call
        summary: <1-2 sentence PARAPHRASE of what the problem asks>
        answer_form: <numeric | proof | code | multiple-choice | short-answer>
```

- [ ] **Step 1: Read `reference/r1-2026/paper.pdf`** (all pages) and write `reference/r1-2026/index.yaml`
      covering every problem and sub-part with the schema above. Record duration/points as printed
      (null if absent).

- [ ] **Step 2: Read the three R2 PDFs and write `reference/r2-2026/index.yaml`** — lighter:
      per-problem `id/type/topics/summary` only; note in a top-level `note:` field that R2 is
      out of current scope. Mine `rationale.pdf` for difficulty intent — capture per-problem
      `design_intent:` paraphrases where the rationale states them.

- [ ] **Step 3: Verify still nothing tracked**

Run: `git ls-files reference/`
Expected: only `reference/.gitkeep`.

(No commit — these files are local-only by policy.)

---

### Task 3: reference/analysis.md (committed)

**Files:**
- Create: `reference/analysis.md`

**Interfaces:**
- Produces: the corpus analysis consumed by plan 003 (syllabus + blueprint) and the content
  gate's fidelity reviews. Required sections:

1. `## Sources` — table: test id, source URL, fetch date, local path, indexed yes/no.
   Note the 2025 forum-only sets and how to export them manually.
2. `## Round 1 format` — sections, problem counts, types, points, duration, answer forms;
   everything the blueprint needs, as observed from r1-2026 (state explicitly that n=1 test
   observed and which fields were printed vs inferred).
3. `## Topic distribution` — table of topics × problem counts (R1; R2 in a separate short table),
   using the index's topic tags.
4. `## Difficulty profile` — per-section difficulty observations, calibrated against the
   Calc AB + basic Python baseline: which problems a baseline student could attempt after
   which curriculum concepts; flag topics exceeding the current design scope.
5. `## Style notes` — wording register, scaffolding conventions, dataset/library conventions
   (paraphrased) — what a fidelity reviewer compares mock tests against.
6. `## Implications` — concrete recommendations for plan 003 (syllabus units, blueprint
   parameters) and plan 004 (overlap-scan corpus coverage).

**Constraint:** paraphrase only; no verbatim sentences from the papers.

- [ ] **Step 1: Write the analysis** from the Task 2 indexes (re-open PDFs where needed).
- [ ] **Step 2: Self-check for verbatim leakage** — for a sample of 5 distinctive phrases in
      `analysis.md`, confirm none appears verbatim in the PDFs (`pdftotext` + `grep -F`, or
      manual PDF search).
- [ ] **Step 3: Commit**

```bash
git add reference/analysis.md
git commit -m "docs: reference corpus analysis (format, topics, difficulty, style)"
```

---

### Task 4: Verification + ship

- [ ] **Step 1:** `bash scripts/ci-local.sh` → ALL GREEN.
- [ ] **Step 2:** `git ls-files reference/` → exactly `.gitkeep` + `analysis.md`.
- [ ] **Step 3:** Content-review gate (4-way per `docs/content-review-gate.md`; duties here:
      analysis accuracy vs the PDFs, no-verbatim policy, index completeness spot-check,
      usefulness for plans 003/004). Findings in `## Content Review`; resolve all `[OPEN]`.
- [ ] **Step 4:** Post-execution report; tick TODO 002; commit.
- [ ] **Step 5:** Push; PR; `bash scripts/pre-merge-guard.sh --pr`; squash-merge.

---

## Out of scope

- **Verification-phase exemption:** this plan ships no units or mock tests (docs + local data
  + one fetch script); the design-§2 named verification phase does not apply. The plan's own
  Task 4 checks (tracking policy, no-verbatim, ci-local) are the verification.
- 2025 R1/R2 ingestion if the forum threads aren't plainly downloadable (recorded in
  `analysis.md ## Sources` as manual follow-up; no new plan needed unless plan 003 finds the
  n=1 R1 sample insufficient).
- Index schema validation tooling (plan 004 owns the schema formally).
- Any curriculum or blueprint work (plan 003).

## Plan Review

(4-way gate verdicts land here.)

## Content Review

(Pre-PR gate findings land here.)
