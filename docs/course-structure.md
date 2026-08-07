# Course Structure

## 1. Course model

<!-- BEGIN GENERATED: course-model -->
The shipped Round 1 schedule runs for 35 weeks in two semesters: 16 weeks followed by 19 weeks.
The 18 unit manifests provide 5,280 lesson minutes, 10,480 practice minutes, and 865 review minutes.
Manifested content is therefore 5,280 + 10,480 + 865 = 16,625 minutes = 277.08 hours.
Those manifests contain 63 lesson sessions and 407 practices across 18 units.
Every lesson session is between 60 and 90 minutes.
The scheduled course adds the 180-minute `r1-001` mock and its 60-minute debrief, for 16,625 + 240 = 16,865 minutes = 281.08 hours.
The manifested division is 88 lesson hours and 189.08 independent practice/review hours.
The scheduled division is 92 in-class hours, including the mock and debrief, and 189.08 independent hours.
Across 35 weeks, that is about 2.63 in-class hours and 5.4 independent hours per week.
The remaining planned extensions in `docs/curriculum-roadmap.md` are editorial estimates, not manifested time, and do not fit silently into this calendar.
<!-- END GENERATED: course-model -->

## 2. Semester split

<!-- BEGIN GENERATED: semester-model -->
Semester 1 is Weeks 1–16 and follows F1-scientific-python → F2-vectors → F4-multivar-calculus → F3-matrices → F5-probability → C1-ml-fundamentals → C2-linear-models → C3-gradient-descent → C4-classical-ml-practice → C8-embeddings.
Its manifested allocation is 7,915 minutes = 131.92 hours, or 8.24 hours per week.
Semester 2 is Weeks 17–35 and follows C5-neural-networks → F6-svd-spectral → C6-pytorch → F7-kernels-convex-optimization → C11-neural-training → C9-dimensionality-reduction → C7-cnn-transfer → C10-competition-craft → `r1-001`.
Its manifested allocation is 8,710 minutes = 145.17 hours.
Adding the 180-minute mock and 60-minute debrief gives 8,710 + 240 = 8,950 minutes = 149.17 hours, or 7.85 hours per week.
<!-- END GENERATED: semester-model -->

F7 is deliberately completed before C9 so kernel, convexity, and optimization language forms one coherent mathematical sequence before the final dimensionality-reduction unit.
The Plan 016 extensions appear at their manifested lengths: F1 has 4 sessions, F5 has 5, C2 has 3, C9 has 4, C10 has 4, and the new F7 has 4.

## 3. Week-by-week table

In-class minutes are manifested lesson sessions plus the final mock and debrief.
Independent minutes are manifested practice and review minutes.
A unit stays active through its review gate even when its final row contains no lesson session.
In a mixed row, “then” records allocation order; independent units may interleave rather than implying that every earlier unit must finish before a later unit begins.

<!-- BEGIN GENERATED: weekly-table -->
| Week | Semester | Units and sessions covered | In-class minutes | Independent minutes | Checkpoint gate |
|---:|:---:|---|---:|---:|---|
| 1 | S1 | F1-scientific-python (prereqs: none): sessions 1, 2, 330 practice minutes. | 165 | 330 | No unit-review gate. |
| 2 | S1 | F1-scientific-python (prereqs: none): sessions 3, 4, 185 practice minutes, 50 review minutes; then F2-vectors (prereqs: F1-scientific-python): session 1, 40 practice minutes. | 220 | 275 | F1-scientific-python review gate. |
| 3 | S1 | F2-vectors (prereqs: F1-scientific-python): sessions 2, 3, 340 practice minutes. | 155 | 340 | No unit-review gate. |
| 4 | S1 | F2-vectors (prereqs: F1-scientific-python): 10 practice minutes, 45 review minutes; then F4-multivar-calculus (prereqs: F2-vectors): sessions 1, 2, 270 practice minutes. | 170 | 325 | F2-vectors review gate. |
| 5 | S1 | F4-multivar-calculus (prereqs: F2-vectors): 130 practice minutes, 40 review minutes; then F3-matrices (prereqs: F2-vectors): sessions 1, 2, 160 practice minutes. | 165 | 330 | F4-multivar-calculus review gate. |
| 6 | S1 | F3-matrices (prereqs: F2-vectors): session 3, 290 practice minutes, 45 review minutes; then F5-probability (prereqs: F1-scientific-python): session 1. | 165 | 335 | F3-matrices review gate. |
| 7 | S1 | F5-probability (prereqs: F1-scientific-python): sessions 2, 3, 330 practice minutes. | 170 | 330 | No unit-review gate. |
| 8 | S1 | F5-probability (prereqs: F1-scientific-python): sessions 4, 5, 320 practice minutes. | 165 | 320 | No unit-review gate. |
| 9 | S1 | F5-probability (prereqs: F1-scientific-python): 55 review minutes; then C1-ml-fundamentals (prereqs: F1-scientific-python): sessions 1, 2, 280 practice minutes. | 160 | 335 | F5-probability review gate. |
| 10 | S1 | C1-ml-fundamentals (prereqs: F1-scientific-python): session 3, 155 practice minutes, 30 review minutes; then C2-linear-models (prereqs: F3-matrices, F4-multivar-calculus, C1-ml-fundamentals): sessions 1, 2, 55 practice minutes. | 255 | 240 | C1-ml-fundamentals review gate. |
| 11 | S1 | C2-linear-models (prereqs: F3-matrices, F4-multivar-calculus, C1-ml-fundamentals): session 3, 410 practice minutes. | 85 | 410 | No unit-review gate. |
| 12 | S1 | C2-linear-models (prereqs: F3-matrices, F4-multivar-calculus, C1-ml-fundamentals): 125 practice minutes, 55 review minutes; then C3-gradient-descent (prereqs: F4-multivar-calculus, C2-linear-models): sessions 1, 2, 145 practice minutes. | 170 | 325 | C2-linear-models review gate. |
| 13 | S1 | C3-gradient-descent (prereqs: F4-multivar-calculus, C2-linear-models): 285 practice minutes, 40 review minutes; then C4-classical-ml-practice (prereqs: C1-ml-fundamentals, F1-scientific-python, F2-vectors, F5-probability): sessions 1, 2, 5 practice minutes. | 165 | 330 | C3-gradient-descent review gate. |
| 14 | S1 | C4-classical-ml-practice (prereqs: C1-ml-fundamentals, F1-scientific-python, F2-vectors, F5-probability): session 3, 410 practice minutes. | 85 | 410 | No unit-review gate. |
| 15 | S1 | C4-classical-ml-practice (prereqs: C1-ml-fundamentals, F1-scientific-python, F2-vectors, F5-probability): 145 practice minutes, 45 review minutes; then C8-embeddings (prereqs: F2-vectors, F3-matrices, F1-scientific-python): sessions 1, 2, 140 practice minutes. | 165 | 330 | C4-classical-ml-practice review gate. |
| 16 | S1 | C8-embeddings (prereqs: F2-vectors, F3-matrices, F1-scientific-python): session 3, 360 practice minutes, 45 review minutes. | 85 | 405 | C8-embeddings review gate, Semester 1 close. |
| 17 | S2 | C5-neural-networks (prereqs: C3-gradient-descent, F5-probability): session 1, 200 practice minutes; then F6-svd-spectral (prereqs: F3-matrices): session 1, 118 practice minutes. | 165 | 318 | No unit-review gate. |
| 18 | S2 | C5-neural-networks (prereqs: C3-gradient-descent, F5-probability): session 2, 77 practice minutes; then F6-svd-spectral (prereqs: F3-matrices): session 2, 236 practice minutes. | 170 | 313 | No unit-review gate. |
| 19 | S2 | C5-neural-networks (prereqs: C3-gradient-descent, F5-probability): session 3, 273 practice minutes, 45 review minutes; then C6-pytorch (prereqs: C5-neural-networks): session 1. | 165 | 318 | C5-neural-networks review gate. |
| 20 | S2 | C6-pytorch (prereqs: C5-neural-networks): session 2, 113 practice minutes; then F6-svd-spectral (prereqs: F3-matrices): session 3, 200 practice minutes. | 170 | 313 | No unit-review gate. |
| 21 | S2 | C6-pytorch (prereqs: C5-neural-networks): session 3, 262 practice minutes; then F6-svd-spectral (prereqs: F3-matrices): session 4, 51 practice minutes. | 170 | 313 | No unit-review gate. |
| 22 | S2 | F6-svd-spectral (prereqs: F3-matrices): session 5, 45 review minutes; then C6-pytorch (prereqs: C5-neural-networks): 145 practice minutes; then F7-kernels-convex-optimization (prereqs: F3-matrices, F4-multivar-calculus, F6-svd-spectral, C3-gradient-descent): session 1, 90 practice minutes. | 170 | 280 | F6-svd-spectral review gate. |
| 23 | S2 | C6-pytorch (prereqs: C5-neural-networks): 45 review minutes; then F7-kernels-convex-optimization (prereqs: F3-matrices, F4-multivar-calculus, F6-svd-spectral, C3-gradient-descent): session 2, 320 practice minutes. | 85 | 365 | C6-pytorch review gate. |
| 24 | S2 | C11-neural-training (prereqs: F4-multivar-calculus, C3-gradient-descent, C5-neural-networks, C6-pytorch): sessions 1, 2, 126 practice minutes; then F7-kernels-convex-optimization (prereqs: F3-matrices, F4-multivar-calculus, F6-svd-spectral, C3-gradient-descent): session 3, 61 practice minutes. | 265 | 187 | No unit-review gate. |
| 25 | S2 | C11-neural-training (prereqs: F4-multivar-calculus, C3-gradient-descent, C5-neural-networks, C6-pytorch): sessions 3, 4, 129 practice minutes; then F7-kernels-convex-optimization (prereqs: F3-matrices, F4-multivar-calculus, F6-svd-spectral, C3-gradient-descent): session 4, 56 practice minutes. | 265 | 185 | No unit-review gate. |
| 26 | S2 | C11-neural-training (prereqs: F4-multivar-calculus, C3-gradient-descent, C5-neural-networks, C6-pytorch): session 5, 235 practice minutes; then F7-kernels-convex-optimization (prereqs: F3-matrices, F4-multivar-calculus, F6-svd-spectral, C3-gradient-descent): 113 practice minutes, 45 review minutes. | 90 | 393 | F7-kernels-convex-optimization review gate. |
| 27 | S2 | C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): session 1; then C11-neural-training (prereqs: F4-multivar-calculus, C3-gradient-descent, C5-neural-networks, C6-pytorch): 370 practice minutes. | 80 | 370 | No unit-review gate. |
| 28 | S2 | C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): session 2, 120 practice minutes; then C11-neural-training (prereqs: F4-multivar-calculus, C3-gradient-descent, C5-neural-networks, C6-pytorch): 180 practice minutes, 60 review minutes. | 90 | 360 | C11-neural-training review gate. |
| 29 | S2 | C7-cnn-transfer (prereqs: C6-pytorch, C11-neural-training): session 1, 200 practice minutes; then C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): session 3, 85 practice minutes. | 170 | 285 | No unit-review gate. |
| 30 | S2 | C7-cnn-transfer (prereqs: C6-pytorch, C11-neural-training): session 2, 200 practice minutes; then C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): session 4, 85 practice minutes. | 170 | 285 | No unit-review gate. |
| 31 | S2 | C7-cnn-transfer (prereqs: C6-pytorch, C11-neural-training): session 3, 200 practice minutes; then C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): 170 practice minutes. | 85 | 370 | No unit-review gate. |
| 32 | S2 | C7-cnn-transfer (prereqs: C6-pytorch, C11-neural-training): session 4, 225 practice minutes, 60 review minutes; then C10-competition-craft (prereqs: C4-classical-ml-practice): session 1; then C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): 45 practice minutes. | 170 | 330 | C7-cnn-transfer review gate. |
| 33 | S2 | C10-competition-craft (prereqs: C4-classical-ml-practice): sessions 2, 3, 210 practice minutes; then C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): 60 practice minutes, 60 review minutes. | 170 | 330 | C9-dimensionality-reduction review gate. |
| 34 | S2 | C10-competition-craft (prereqs: C4-classical-ml-practice): session 4, 365 practice minutes; then C7-cnn-transfer (prereqs: C6-pytorch, C11-neural-training): 50 practice minutes. | 85 | 415 | No unit-review gate. |
| 35 | S2 | C10-competition-craft (prereqs: C4-classical-ml-practice): 155 practice minutes, 55 review minutes; then C9-dimensionality-reduction (prereqs: F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals): 35 practice minutes; then `r1-001` mock (180 minutes); then `r1-001` debrief (60 minutes). | 240 | 245 | C10-competition-craft review gate, `r1-001` summative gate, debrief. |
<!-- END GENERATED: weekly-table -->

<!-- BEGIN GENERATED: semester-summary -->
The verified Semester 1 columns sum to 2,545 in-class minutes + 5,370 independent minutes = 7,915 minutes.
The Semester 1 average is 494.69 minutes, and its rows range from 485 to 500 minutes.
The verified Semester 2 columns sum to 2,975 in-class minutes + 5,975 independent minutes = 8,950 minutes.
The Semester 2 average is 471.05 minutes, and its rows range from 450 to 500 minutes.
<!-- END GENERATED: semester-summary -->

## 4. Milestones and assessment

Every manifested unit review is a formative checkpoint at the gate shown in the table.
<!-- BEGIN GENERATED: summative-milestone -->
The summative milestone is `r1-001` in Week 35, scored against its 300-point blueprint during its 180-minute duration and followed by the 60-minute debrief.
<!-- END GENERATED: summative-milestone -->
An `r1-002` slot remains optional and is not included in the baseline table.
If used, `r1-002` displaces 180 of Week 16's 360 C8 C-set/challenge practice minutes.
That substitution leaves 85 lesson minutes + 180 C8 practice minutes + 45 C8 review minutes + the 180-minute optional mock = the same 490-minute week.
The optional mock therefore replaces challenge practice rather than adding time or removing a lesson or unit review.

## 5. Provenance and regeneration

Lesson, practice, and review minutes come from `units/*/manifest.yaml`.
Prerequisite edges come from `syllabus.md` and are cross-checked against each unit manifest.
The mock duration and points come from `mocktests/r1-001/manifest.yaml`.
The count command deliberately sums every `lesson_sessions` list and every manifested review field.

<!-- BEGIN GENERATED: counts-output -->
<!-- Maintainer regeneration command: uv run python -m tools.render_course_structure -->

The command's captured stdout is:

```text
5280 10480 865 407 63 18
```
<!-- END GENERATED: counts-output -->

<!-- BEGIN GENERATED: arithmetic-output -->
The semester and table arithmetic was captured independently as:

```text
S1: 7915
S2: 8950
full: 7915 + 8950 = 16865
```
<!-- END GENERATED: arithmetic-output -->

## 6. Grading and calendar buffer

Unit-review checkpoints remain formative and ungraded.
The entire summative assessment weight belongs to `r1-001`'s 300-point blueprint score.
The pass bar should reference the blueprint's intro, core, and advanced difficulty bands: reliable performance on intro and core work supports a pass, while advanced work distinguishes performance above that bar.
No numeric course-pass cutoff is introduced because the authoritative inputs define difficulty bands and points but no course-pass percentage.
Recovery trims C-set and challenge practice first; lessons and unit reviews are never trimmed.
The optional `r1-002` follows the same buffer policy by displacing Week 16 challenge practice rather than adding time.

## 7. Prerequisite integrity

Prerequisite integrity holds at session granularity.
Within a shared week, “then” means the earlier unit's remaining practice and review finish before the later unit's first session.
<!-- BEGIN GENERATED: first-instruction -->
| Unit | First instruction |
|---|---:|
| F1-scientific-python | Week 1 |
| F2-vectors | Week 2 |
| F4-multivar-calculus | Week 4 |
| F3-matrices | Week 5 |
| F5-probability | Week 6 |
| C1-ml-fundamentals | Week 9 |
| C2-linear-models | Week 10 |
| C3-gradient-descent | Week 12 |
| C4-classical-ml-practice | Week 13 |
| C8-embeddings | Week 15 |
| C5-neural-networks | Week 17 |
| F6-svd-spectral | Week 17 |
| C6-pytorch | Week 19 |
| F7-kernels-convex-optimization | Week 22 |
| C11-neural-training | Week 24 |
| C9-dimensionality-reduction | Week 27 |
| C7-cnn-transfer | Week 29 |
| C10-competition-craft | Week 32 |
<!-- END GENERATED: first-instruction -->
For each actual prerequisite edge, the prerequisite's complete allocation must finish before the dependent unit's first session.
The table repeats every unit's complete prerequisite list beside every active week so the check remains local.
