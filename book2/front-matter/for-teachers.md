# For Teachers

This Teacher's Edition contains everything in the Student Book, plus three additions.

- **Answers in place.** Any checkpoint or self-quiz answer that a notebook hides in a collapsed block is printed where it occurs, in a panel labelled **Answers**.
  Most Book 2 notebooks already print their checkpoint answers openly, under **Collected answers**.
- **Full solutions.** Every practice problem, in all three sets, is followed by its complete solution.
- **The mock test.** The final part reproduces mock test `r2-001`: the paper, the answer key, the scoring rubric, and the solution notebooks.

The student books print worked solutions to Set A only.
Sets B and C stay answer-free outside this edition, so you can assign them as homework or quizzes.

Every solution notebook is executed from top to bottom, on a CPU and with fixed seeds, by the course's verification suite.
The student notebooks are checked too: they carry no solutions and no saved outputs.
This book prints code without its outputs; run a notebook to see the numbers it produces.

## Prerequisites

Book 2 assumes the whole of Book 1 and does not reteach it.
Each unit opens with a 30-minute Book 1 bridge diagnostic that names the imported ideas (written `book1:<unit>` or `book1:<concept>`) and links to the units for review.
Use the diagnostic at the start of each unit's first week.
A student who struggles with one of its sections should review the linked Book 1 unit before Session 1, not after.

## Course pacing

The schedule is in `book2/docs/course-structure.md` and `book2/curriculum/course-schedule.yaml`.
In outline:

- Book 2 runs **37 weeks** and follows Book 1's 40, so its weeks are also numbered 41–77 on the combined calendar.
- The six units are taught in book order: B2-019, B2-020, B2-021, B2-022, B2-023, B2-024.
- Each unit has a 30-minute bridge diagnostic in its first week, one 90-minute class session per week (five sessions, or six for B2-024), and a practice chunk each week, followed by a 60-minute review week.
- The schedule totals 10,270 minutes.
  The 148 practice problems are assigned to specific weeks in the schedule.
- The two-day mock test `r2-001` follows Week 37.

The weekly load is deliberately uneven.
Teaching weeks run from about 200 to 420 minutes, and each review week is 60 minutes.
The load peaks in the derivation-heavy middle of each unit and tapers to the review week, instead of holding Book 1's steady weekly band.

The `estimated_minutes` field of each unit's `manifest.yaml` and the minutes line at the top of every notebook give the planned time for each item.
Practice problems carry `set:` (A, B, or C), `difficulty:`, and compute-policy tags in the manifest.

When the calendar slips, trim Set C practice first.
Never cut a bridge diagnostic, a lesson session, or a unit review.

## Grading practice and open-ended problems

The rubrics follow the same conventions as Book 1.

- **Multiple choice** is all or nothing: five options, one correct.
- **Short answers** must match the requested exact value or normal form.
- **Coding parts** are graded by running the notebook from the top in a fresh kernel, on a CPU, with the stated seed.
  Required identifiers, shapes, and dtypes are part of the answer, and a part that uses a banned API scores zero.
- **Derivations and proofs** marked *Reasoning is required* are scored step by step, as the rubric lists.

Open-ended modeling problems are graded in two portions.

**Test score (60%).**
Each problem prints a baseline score $B$ and its rubric gives a reference score $R$ from the published reference solution.
With the gap $g = \lvert B - R\rvert$, the portion is scored in tiers:

| Result | Credit |
|---|---|
| within $0.25g$ of $R$, or better | 100% |
| better than $B$ | 60% |
| worse than $B$, but by less than $0.25g$ | 25% |
| otherwise | 0% |

The test-score portion is zero for any protocol violation.
Violations include calling the final test function more than once, fitting on validation or test rows, exceeding the step or time budget, using banned tools or outside data, and a notebook that does not run from the top.

**Writeup (40%).**
The writeup has four equal parts, each scored full, half, or zero:

- **Approach:** the method, inputs, and settings, stated reproducibly, with a reason tied to this problem.
- **Alternatives considered:** at least two alternatives, each ruled out by a validation number or a precise, checked reason, under the same data roles and budget.
- **Evaluation:** the data roles and seeds, the single test score with its bootstrap interval, the baseline under the same protocol, and the validation comparison that justified the final choice.
- **Limitations:** a concrete failure mode and a specific test that would measure it.

Give credit only for numbers that appear in the notebook's own output.
The B2-024 capstone teaches experiment design and honest evaluation before students meet this register on the mock test.

The optional *Accelerator extension* sections are never graded.

## Giving the mock test

Mock test `r2-001` lives in `book2/mocktests/r2-001/`:

```text
r2-001/
  test.md          cover page: instructions, days, sections, points
  theory/          the written parts of Problems 1 and 3
  problems/        the notebooks for Problems 1–5
  data/            the test data, its seeded generator, and the loader
  rubric.md        partial-credit rubric (teacher only)
  solutions/       answers.md and worked solution notebooks (teacher only)
  manifest.yaml    part order, points, concepts
```

It is a **two-day** test: 240 minutes each day, 300 points in all, five problems with 25 graded parts.

- **Day 1:** Problem 1, a scaffolded arc on a tiny causal language model (90 points), and Problem 2, an open-ended problem (70 points).
- **Day 2:** Problem 3, a scaffolded arc on a variational autoencoder (50 points), and Problems 4 and 5, two open-ended problems (40 and 50 points).

Open-ended work carries 160 of the 300 points.
The arcs mix written parts in `theory/` with coding parts in the notebooks, so students need both on the same day.

To administer it:

- On Day 1, give students `test.md`, the Day 1 files (`theory/p01.md`, `problems/p01.ipynb`, `problems/p02.ipynb`), and the `data/` folder.
  Collect their Day 1 notebooks at the end of the day.
- On Day 2, give them the Day 2 files (`theory/p03.md` and `problems/p03.ipynb` through `problems/p05.ipynb`).
- Never give out `rubric.md`, `solutions/`, or the manifest.
- Students may use Python's standard library, NumPy, and PyTorch on a CPU, with no web access, downloads, outside datasets, or pretrained weights.

**The locked-test protocol.**
Each open-ended problem splits its data into training, validation, and locked-test rows.
Students reach the locked-test rows only through the problem's `final_test_score` function, which they must call exactly once, after every fitting and selection decision is made.
Each problem also wraps every optimizer in a `StepBudget` that caps optimizer steps and wall-clock time.
The lock is a protocol, not encryption: the data files and their generator are in the students' `data/` folder.
Explain before Day 1 that reading the locked rows any other way, or using the generator to recover hidden parameters or labels, zeroes the test-score portion, and that the rubric checks the call count.

**Grading.**
Rerun each submitted notebook from the top on a CPU with the test's fixed seed.
Score the arcs part by part with `rubric.md`, using `solutions/answers.md` as the answer key.
For each open-ended problem, read the score from the single `final_test_score` call, apply the tier table in the rubric, check the protocol, and score the writeup.
The rubric states its tolerances, including small platform-dependent differences in the last printed digit.

The paper is original work built to the Round 2 blueprint in `book2/mocktests/blueprint.yaml`.
It shares no text with any past competition paper.
Use it once per student, and debrief afterwards by sending each student back to the units behind the parts they missed.

## Compute policy

Every notebook declares a compute policy and a fixed seed in its header.
The course uses two of the policies its design allows:

- **`cpu`:** the only path is a CPU path.
  Almost every lesson and practice problem is of this kind.
- **`optional-colab-l4`:** a required CPU correctness path, plus an optional *Accelerator extension* that reruns the same code with a larger configuration on a Colab L4 GPU.

The course's verification suite runs every notebook on a CPU and never runs an accelerator extension.
No notebook requires a GPU, and no required work downloads pretrained weights or outside data.

GPU work appears only in the capstone, B2-024.
Its overview carries the `optional-colab-l4` policy, its lessons guard GPU code with `torch.cuda.is_available()` so that they still run on a CPU, and six of its practice problems (p06, p07, p16, p17, p19, and p20) have accelerator extensions.
The open-ended problems of `r2-001` have optional accelerator extensions too, and they are never graded.
If your students have Colab access, an L4 session is a good way to try the extensions after the CPU work is complete; if they do not, nothing in the course or the mock test is lost.
