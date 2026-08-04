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
  local id="$1" dest="$2" tmp
  if [[ -s "$dest" ]]; then
    echo "exists: $dest"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  tmp="${dest}.tmp"
  # -f: fail on HTTP errors instead of saving the error body; tmp+mv: no truncated files
  # survive an interruption (a truncated PDF would pass the magic check and be kept forever).
  curl -fsSL --retry 3 --max-time 120 \
    "https://drive.google.com/uc?export=download&id=${id}" -o "$tmp" || true
  if ! file "$tmp" 2>/dev/null | grep -q 'PDF document'; then
    # Large/flagged files get an HTML interstitial; retry via the usercontent endpoint.
    curl -fsSL --retry 3 --max-time 120 \
      "https://drive.usercontent.google.com/download?id=${id}&export=download&confirm=t" -o "$tmp" || true
  fi
  if ! file "$tmp" 2>/dev/null | grep -q 'PDF document'; then
    echo "FAIL: $dest is not a PDF (download blocked or link rotated; try gdown)" >&2
    rm -f "$tmp"
    return 1
  fi
  mv "$tmp" "$dest"
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
      - id: r1-2026-p01a   # one entry per GRADABLE SUB-PART: p01, or p01a/p01b/… when
                           # a problem has parts; a parts-less problem is just pNN
        type: theory | programming
        topics: [<free-form topic tags>]
        points: <int|null>
        difficulty: intro | core | advanced   # judgment call
        summary: <1-2 sentence PARAPHRASE of what the problem asks>
        text: <VERBATIM problem text — LOCAL-ONLY file, legal here; this is what plan 004's
               lexical overlap-scan matches against (a paraphrase would be useless for
               n-gram similarity). NEVER copy this field into any committed file.>
        answer_form: <numeric | proof | code | multiple-choice | short-answer>
```

- [ ] **Step 1: Read `reference/r1-2026/paper.pdf`** (all pages) and write `reference/r1-2026/index.yaml`
      covering every problem and sub-part with the schema above. Record duration/points as printed
      (null if absent).

- [ ] **Step 2: Read the three R2 PDFs and write `reference/r2-2026/index.yaml`** — lighter:
      per-problem `id/type/topics/summary` only; note in a top-level `note:` field that R2 is
      out of current scope. Mine `rationale.pdf` for difficulty intent — capture per-problem
      `design_intent:` paraphrases where the rationale states them.

- [ ] **Step 3: Attempt the 2025 R1 export** — try fetching the forum thread
      (https://forum.beaver-edge.ai/c/ai-olympiads/usa-north-america-ai-olympiad/8) read-only;
      if problem PDFs/text are plainly downloadable without auth, ingest as `reference/r1-2025/`
      (same index schema); otherwise record the exact obstacle in `analysis.md ## Sources`.
      Doing the attempt now (not at plan 003) because it is a one-time manual export and n=2
      R1 samples materially de-risk the blueprint.

- [ ] **Step 4: Verify still nothing tracked**

Run: `git ls-files reference/`
Expected: only `reference/.gitkeep`.

(No commit — these files are local-only by policy. Fresh clones rebuild them via
`bash scripts/fetch-reference.sh` + re-index; plan 004 MUST make `overlap-scan` SKIP LOUDLY,
naming that remedy, when `reference/*/index.yaml` is absent — a real overlap verdict exists
only on a machine with the fetched corpus.)

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
- [ ] **Step 2: Scripted leak check** — `pdftotext` every corpus PDF, then grep every ≥6-word
      shingle of `analysis.md` against the extracted text (guard with
      `command -v pdftotext || echo "pdftotext missing — fall back to 5-phrase manual check"`).
      Zero verbatim shingle hits allowed (topic/section names shorter than the shingle window
      pass by construction). **The same no-verbatim rule applies to every committed review
      finding** — content-gate reviewers must paraphrase when citing the PDFs in this plan file.
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

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-03)

- **Verdict**: APPROVE WITH NITS

1. `[NOTED]` Google Drive `uc?export=download` serves an HTML interstitial for large files;
   the script's PDF-magic check turns that into a clean failure rather than a corrupt file.
   The R1 paper (2MB) was live-verified before planning; if an R2 file trips the interstitial,
   the implementer adds the confirm-token handling then.
2. `[NOTED]` The index keeps `summary:` paraphrase-only even though the file is local-only
   (verbatim would be legal there). Rationale: paraphrase eliminates accidental copy-through
   into committed docs; plan 004's `overlap-scan` should extract verbatim text at runtime
   via `pdftotext` from the local PDFs instead of relying on the index. Recorded for plan 004.
3. `[NOTED]` n=1 R1 observed sample is a real limitation for blueprint derivation;
   the analysis is required to state printed-vs-inferred per field, and the 2025 forum sets
   are documented for manual export if plan 003 needs more samples.
4. Checked: gitignore whitelist (`reference/*` + `!.gitkeep` + `!analysis.md`) already merged
   in plan 001 and behaviorally verified by the [opus] reviewer's isolated-repo matrix;
   Task 1/2 verification steps re-confirm nothing new becomes tracked.

### Review 2 — [fable] Independent Fable 5, fresh context (2026-08-03)

- **Verdict**: APPROVE WITH NITS

1. `[FIXED]` Partial-download corruption defeats idempotency (magic check passes on
   truncated PDFs; `-s` check skips them forever). → Response: download to `.tmp`,
   `mv` only after the magic check.
2. `[FIXED]` Drive interstitial detected but not handled. → Response: fallback to the
   `drive.usercontent.google.com/download?…&confirm=t` endpoint; `curl -fsSL` so HTTP
   errors don't write bodies; `gdown` named as the manual fallback.
3. `[FIXED]` Paraphrase-only index useless for lexical overlap-scan. → Response: verbatim
   `text:` field added (LOCAL-ONLY file; never copied into committed docs).
4. `[FIXED]` Overlap-scan availability on fresh clones not called out. → Response: Task 2
   note — plan 004 must make overlap-scan SKIP LOUDLY naming the fetch+index remedy.
5. `[FIXED]` 2025 export under-prioritized. → Response: Task 2 Step 3 attempts the forum
   export now; obstacle recorded in `## Sources` if blocked.
6. `[FIXED]` 5-phrase spot check thin. → Response: scripted ≥6-word shingle check via
   pdftotext (with availability guard).
7. `[FIXED]` Review-section leak vector. → Response: no-verbatim rule extended to all
   committed review findings, stated in Task 3 Step 2.
8. `[WONTFIX]` `set -e` aborts on first fetch failure. → Response: re-run is cheap and
   idempotent; per-file summary not worth the complexity.

### Review 3 — [glm] GLM 5.2 (2026-08-03)

- **Verdict**: APPROVE WITH NITS

1. `[FIXED]` Drive confirm flow — same as [fable] #2.
2. `[FIXED]` No sub-part representation. → Response: schema convention — one entry per
   gradable sub-part (`p01` or `p01a`/`p01b`).
3. `[FIXED]` `-s` hides curl diagnostics. → Response: `-fsSL`.
4. `[FIXED]` No retry/timeout. → Response: `--retry 3 --max-time 120`.
5. `[FIXED]` Stale corrupt file treated as "exists". → Response: tmp+mv atomicity means a
   non-empty `$dest` is always a validated PDF.
6. `[WONTFIX]` Page-count assertion per file. → Response: magic check + atomic write +
   Task 2's full read of every PDF cover this; hardcoding page counts makes link rotation
   a false failure.
7. `[NOTED]` `reference/.gitkeep` confirmed tracked since plan 001 (`git ls-files`).
8. `[FIXED]` pdftotext availability. → Response: `command -v` guard in Task 3 Step 2.

### Review 4 — [codex] Codex GPT-5.5 (2026-08-03)

- **Verdict**: REJECT (round 1, reviewed commit prior to cross-reviewer fixes)
  → all three blockers were fixed in the same round; re-verdict requested

1. `[FIXED]` Non-idempotent against partial downloads — same as [fable] #1 / [glm] #5.
2. `[FIXED]` Interstitial unhandled — same as [fable] #2.
3. `[FIXED]` Index insufficient for overlap-scan — same as [fable] #3; the verbatim `text:`
   field IS the downstream input contract, stated in the schema itself.
4. `[NOTED]` `git ls-files` is detection, not prevention (forced `git add` bypasses).
   Accepted: the hard safeguard in CLAUDE.md forbids exactly that action; detection here is
   defense-in-depth.
5. `[NOTED]` Exemption confirmed legitimate.

## Content Review

(Pre-PR gate findings land here.)
