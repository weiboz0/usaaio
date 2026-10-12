# For Teachers

This Teacher's Edition contains everything in the Student Book, plus three additions.

- **Answers in place.** The checkpoint and self-quiz answers that the notebooks hide in collapsed blocks are printed where they occur, in panels labelled **Answers**.
- **Full solutions.** Every practice problem, in all three sets, is followed by its complete solution.
- **The mock test.** The final part reproduces mock test `r1-001`: the paper, the answer key, the scoring rubric, and the solution notebooks.

The student books print worked solutions to Set A only.
Sets B and C stay answer-free outside this edition, so you can assign them as homework or quizzes.

Every solution notebook is executed from top to bottom, with fixed seeds, by the course's verification suite.
The student notebooks are checked too: they carry no solutions and no saved outputs.
This book prints code without its outputs; run a notebook to see the numbers it produces.

## Course pacing

The full schedule is in `book1/docs/course-structure.md`, generated from `book1/curriculum/course-schedule.yaml` and the unit manifests.
In outline:

- The course runs **40 weeks in two semesters**: Weeks 1–16, then Weeks 17–40.
- The 19 units hold 69 class sessions of 60 to 90 minutes each, and 437 practice problems.
- A typical week has about 2.5 hours in class and about 5.3 hours of independent practice and review.
- The mock test `r1-001` (180 minutes) and its 60-minute debrief fill Week 40.

The chapters of this book follow the unit numbering, but the schedule teaches them in dependency order:

- **Semester 1:** F1 → F2 → F3 → F4 → F5 → C1 → C2 → C3 → C4 → C5.
- **Semester 2:** C6 → F6 → C7 → F7 → C8 → C9 → C10 → C11 → C12, then `r1-001`.

Some weeks interleave two units once the prerequisites of both are complete.
The week-by-week table in the course structure lists each week's sessions, practice minutes, and unit-review gates.

Each session notebook is sized for one class meeting.
The `estimated_minutes` field in each unit's `manifest.yaml` gives the lesson minutes per session and the total practice and review time.
Practice problems carry a `difficulty:` tag (intro, core, or advanced) and a `set:` tag (A, B, or C) in the manifest.

When the calendar slips, trim Set C and challenge practice first.
Never cut a lesson session or a unit review: later units assume both.

The unit reviews are formative checkpoints and are not graded.
All summative weight belongs to the mock test.
The course structure gives no numeric pass mark; read results against the test's difficulty bands instead, where solid intro and core work is the bar and advanced work shows strength beyond it.

## Grading practice and open-ended problems

The course grades the way the competition does, and the rubrics in this book follow a few fixed conventions.

- **Multiple choice** is all or nothing: five options, one correct.
- **Short answers** must match the requested normal form exactly.
  An equivalent value in another form, such as an unreduced fraction or a decimal where an exact value was asked for, earns nothing.
- **Coding parts** are graded by running the student's notebook from the top in a fresh kernel.
  Required function names, signatures, and output shapes are part of the answer.
- **Banned tools** zero the part that uses them, however correct the result.
- **Derivations and proofs** marked *Reasoning is required* are scored step by step; the rubric names the points each step earns.

Open-ended problems, such as the modeling notebooks of C11 and Problem 9 of the mock test, are graded in layers.

1. **Hard gates.** A notebook that does not run cleanly from the top, breaks the prediction-function contract, uses a model family or library the statement rules out, or uses held-back rows to make decisions scores zero on the whole problem.
2. **Method and validation.** Points for an honest validation protocol, a meaningful baseline, a bounded and recorded comparison of alternatives, and a final model that follows the evidence.
3. **Measured performance.** The grader scores the held-back predictions with the stated metric and maps the result to points with the rubric's published table.
4. **Writeup.** A short summary cell is scored item by item: the full recipe, the validation details, a reason for the model choice and for the metric tied to this dataset, at least one alternative with its measured outcome, and an honest limitation.
   Each item must be a checkable sentence backed by a number the notebook prints.

C11 teaches this writeup register explicitly, so students meet it before the mock test.
When you grade a writeup, give credit only for claims you can find in the notebook's output.

## Giving the mock test

Mock test `r1-001` lives in `book1/mocktests/r1-001/`:

```text
r1-001/
  test.md          cover page: instructions, sections, points
  theory/          Problems 1–4, as documents
  problems/        Problems 5–9, as notebooks
  data/            the test's data and the seeded scripts that make it
  rubric.md        partial-credit rubric (teacher only)
  solutions/       answers.md and worked solution notebooks (teacher only)
  manifest.yaml    problem order, points, concepts
```

It runs **180 minutes for 300 points** across nine problems: a concept block of multiple-choice questions, three math-computation problems, an integrative arc, three engineering problems, and an open-ended modeling notebook.

To administer it:

- Give students `test.md`, the `theory/` documents, the `problems/` notebooks, and the `data/` folder.
  Do not give them `rubric.md`, `solutions/`, or the manifest.
- Problems 5 and 7 load the same pretrained assets as C5 and C10 (GloVe word vectors and ResNet-50 weights) from a local cache.
  Make sure they are cached on each student machine before the clock starts, as the test's instructions promise; they are not part of the course files.
- Run the test in one sitting, on a CPU, with no web access during the exam.
- Grade with `rubric.md`, using `solutions/answers.md` as the answer key, and rerun each submitted notebook from the top.
- Hold the debrief soon afterwards and send each student back to the units behind the parts they missed; the review notebooks list which practice problems to redo for each concept.

The paper is original work built to the Round 1 blueprint in `book1/mocktests/blueprint.yaml`.
It shares no text with any past competition paper.
Use it once per student; a second sitting measures memory, not skill.

## Compute policy

Round 1 is CPU-only, and so is this book.
Every lesson, practice problem, and solution runs on an ordinary laptop CPU, and the course's verification suite runs them that way.
No unit requires a GPU or a paid service.
Two units use pretrained assets: C10 loads ResNet-50 ImageNet weights through `torchvision`, and C5 loads GloVe word vectors through `gensim`.
Download and cache both once, before those units begin, so that class time never waits on the network.
C11 teaches the boundary explicitly: a Round 1 submission must not claim or depend on a GPU.

GPU work begins in the companion book for Round 2, which adds an optional Colab L4 extension to some capstone problems.
