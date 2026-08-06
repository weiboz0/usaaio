# Content-Review Gate

The pre-PR quality gate for teaching content and mock tests
(the tailored equivalent of a code-review gate). 4-way, full-blocking consensus.

## Roster

| # | Reviewer | Dispatch | Model |
|---|----------|----------|-------|
| 1 | Self-review | active session inline | active session model |
| 2 | Sol reviewer | fresh read-only subagent | GPT-5.6-sol |
| 3 | Terra reviewer | separate fresh read-only subagent | GPT-5.6-terra |
| 4 | GLM | `opencode:opencode-review` subagent, read-only | opencode-go/glm-5.2 |

Dispatch 2–4 in parallel with the inline self-review.
Tooling code changes (`tools/`, `scripts/`) in the same plan get conventional code review
by the same roster in the same round.

## Reviewer duties (content)

1. **Solve blind first.** Attempt each problem from the student-facing materials alone,
   BEFORE reading the solution or answer key. Report your answer, then compare.
2. **Correctness.** Verify the answer key and rubric against your independent solution.
3. **Clarity.** Flag ambiguous wording, underspecified inputs, unstated assumptions.
4. **Difficulty + timing.** Judge against real Round 1 level and the stated time budget.
5. **Rubric fairness.** Points match difficulty; partial credit is well-defined.
6. **Provenance.** `adapted-from` tags present where content resembles a known past problem;
   note any resemblance the tags miss.
7. **Fidelity.** For mock tests: style, wording register, and problem shape match the
   reference corpus; record a per-section fidelity verdict.
8. **Accessibility.** For units: read as the target student
   (Calculus AB + basic Python + declared prerequisites only);
   flag any silently-assumed concept.

## Format

Findings append to the plan file's `## Content Review`, one review round per reviewer pass:

    ### Review N — <reviewer> (YYYY-MM-DD)
    - **Verdict**: Approved / Approved with suggestions / Changes requested
    1. `[OPEN]` Finding with file/section reference. Priority: Must Fix / Should Fix / Nice to Have.

Authors respond inline with `→ Response:` and retag `[FIXED]` / `[WONTFIX]` (with reason).
Source tags: `[self]` / `[sol]` / `[terra]` / `[glm]`.

## Acceptance

All four reviewers APPROVE (or approve-with-nits) and every `[OPEN]` item is resolved.
One REJECT blocks. Iterate fix → re-review to consensus.
