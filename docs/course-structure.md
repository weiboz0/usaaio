# Course Structure

## 1. Course model

The shipped Round 1 schedule runs for 31 weeks in two semesters: 16 weeks followed by 15 weeks.
The 17 unit manifests provide 4,740 lesson minutes, 9,237 practice minutes, and 790 review minutes.
Manifested content is therefore 4,740 + 9,237 + 790 = 14,767 minutes = 246.1 hours.
Those manifests contain 57 lesson sessions and 383 practices across 17 units.
Every lesson session is between 60 and 90 minutes.
The scheduled course adds the 180-minute `r1-001` mock and its 60-minute debrief, for 14,767 + 240 = 15,007 minutes = 250.1 hours.
The manifested division is 79.0 lesson hours and 167.1 independent practice/review hours.
The scheduled division is 83.0 in-class hours, including the mock and debrief, and 167.1 independent hours.
Across 31 weeks, that is about 2.7 in-class hours and 5.4 independent hours per week.
The remaining planned extensions in `docs/curriculum-roadmap.md` are editorial estimates, not manifested time, and do not fit silently into this calendar.

## 2. Semester split

Semester 1 is Weeks 1–16 and follows F1 → F2 → F4 → F3 → F5 → C1 → C2 → C3 → C4 → C8.
Its unit arithmetic is 875 + 665 + 610 + 745 + 1,120 + 705 + 905 + 640 + 855 + 795 = 7,915 minutes = 131.9 hours, or 8.2 hours per week.
Semester 2 is Weeks 17–31 and follows F6 → F7 → C5 → C6 → C7 → C9 → C10 → `r1-001`.
Its manifested arithmetic is 1,075 + 1,025 + 845 + 815 + 972 + 1,000 + 1,120 = 6,852 minutes = 114.2 hours.
Adding the 180-minute mock and 60-minute debrief gives 6,852 + 240 = 7,092 minutes = 118.2 hours, or 7.9 hours per week.
F7 is deliberately completed before C9 so kernel, convexity, and optimization language forms one coherent mathematical sequence before the final dimensionality-reduction unit.
The Plan 016 extensions appear at their manifested lengths: F1 has 4 sessions, F5 has 5, C2 has 3, C9 has 4, C10 has 4, and the new F7 has 4.

## 3. Week-by-week table

In-class minutes are manifested lesson sessions plus the final mock and debrief.
Independent minutes are manifested practice and review minutes.
A unit stays active through its review gate even when its final row contains no lesson session.
In a mixed row, “then” gives strict within-week instructional order, so the earlier unit's remaining work and review finish before the later unit begins.

| Week | Semester | Units and sessions covered | In-class minutes | Independent minutes | Checkpoint gate |
|---:|:---:|---|---:|---:|---|
| 1 | S1 | F1 (prereqs: none): sessions 1–2 and 330 practice minutes. | 165 | 330 | No unit-review gate. |
| 2 | S1 | F1 (prereqs: none): sessions 3–4, 185 practice minutes, and 50 review minutes; then F2 (prereqs: F1): session 1 and 40 practice minutes. | 220 | 275 | F1 review gate. |
| 3 | S1 | F2 (prereqs: F1): sessions 2–3 and 340 practice minutes. | 155 | 340 | No unit-review gate. |
| 4 | S1 | F2 (prereqs: F1): 10 practice minutes and 45 review minutes; then F4 (prereqs: F2): sessions 1–2 and 270 practice minutes. | 170 | 325 | F2 review gate. |
| 5 | S1 | F4 (prereqs: F2): 130 practice minutes and 40 review minutes; then F3 (prereqs: F2): sessions 1–2 and 160 practice minutes. | 165 | 330 | F4 review gate. |
| 6 | S1 | F3 (prereqs: F2): session 3, 290 practice minutes, and 45 review minutes; then F5 (prereqs: F1): session 1. | 165 | 335 | F3 review gate. |
| 7 | S1 | F5 (prereqs: F1): sessions 2–3 and 330 practice minutes. | 170 | 330 | No unit-review gate. |
| 8 | S1 | F5 (prereqs: F1): sessions 4–5 and 320 practice minutes. | 165 | 320 | No unit-review gate. |
| 9 | S1 | F5 (prereqs: F1): 55 review minutes; then C1 (prereqs: F1): sessions 1–2 and 280 practice minutes. | 160 | 335 | F5 review gate. |
| 10 | S1 | C1 (prereqs: F1): session 3, 155 practice minutes, and 30 review minutes; then C2 (prereqs: F3, F4, C1): sessions 1–2 and 55 practice minutes. | 255 | 240 | C1 review gate. |
| 11 | S1 | C2 (prereqs: F3, F4, C1): session 3 and 410 practice minutes. | 85 | 410 | No unit-review gate. |
| 12 | S1 | C2 (prereqs: F3, F4, C1): 125 practice minutes and 55 review minutes; then C3 (prereqs: F4, C2): sessions 1–2 and 145 practice minutes. | 170 | 325 | C2 review gate. |
| 13 | S1 | C3 (prereqs: F4, C2): 285 practice minutes and 40 review minutes; then C4 (prereqs: C1, F1, F2, F5): sessions 1–2 and 5 practice minutes. | 165 | 330 | C3 review gate. |
| 14 | S1 | C4 (prereqs: C1, F1, F2, F5): session 3 and 410 practice minutes. | 85 | 410 | No unit-review gate. |
| 15 | S1 | C4 (prereqs: C1, F1, F2, F5): 145 practice minutes and 45 review minutes; then C8 (prereqs: F2, F3, F1): sessions 1–2 and 140 practice minutes. | 165 | 330 | C4 review gate. |
| 16 | S1 | C8 (prereqs: F2, F3, F1): session 3, 360 C-set/challenge practice minutes, and 45 review minutes. | 85 | 405 | C8 review gate and Semester 1 close. |
| 17 | S2 | F6 (prereqs: F3): sessions 1–2 and 303 practice minutes. | 170 | 303 | No unit-review gate. |
| 18 | S2 | F6 (prereqs: F3): sessions 3–4 and 302 practice minutes. | 170 | 302 | No unit-review gate. |
| 19 | S2 | F6 (prereqs: F3): session 5 and 45 review minutes; then F7 (prereqs: F3, F4, F6, C3): sessions 1–3 and 88 practice minutes. | 340 | 133 | F6 review gate. |
| 20 | S2 | F7 (prereqs: F3, F4, F6, C3): session 4 and 388 practice minutes. | 85 | 388 | No unit-review gate. |
| 21 | S2 | F7 (prereqs: F3, F4, F6, C3): 164 practice minutes and 45 review minutes; then C5 (prereqs: C3, F5): sessions 1–2 and 99 practice minutes. | 165 | 308 | F7 review gate. |
| 22 | S2 | C5 (prereqs: C3, F5): session 3 and 388 practice minutes. | 85 | 388 | No unit-review gate. |
| 23 | S2 | C5 (prereqs: C3, F5): 63 practice minutes and 45 review minutes; then C6 (prereqs: C5): sessions 1–2 and 176 practice minutes. | 165 | 284 | C5 review gate. |
| 24 | S2 | C6 (prereqs: C5): session 3, 344 practice minutes, and 45 review minutes. | 85 | 389 | C6 review gate. |
| 25 | S2 | C7 (prereqs: C6): sessions 1–2 and 303 practice minutes. | 170 | 303 | No unit-review gate. |
| 26 | S2 | C7 (prereqs: C6): session 3, 369 practice minutes, and 45 review minutes. | 85 | 414 | C7 review gate. |
| 27 | S2 | C9 (prereqs: F6, C8, F5, C1): sessions 1–2 and 303 practice minutes. | 170 | 303 | No unit-review gate. |
| 28 | S2 | C9 (prereqs: F6, C8, F5, C1): sessions 3–4 and 297 practice minutes. | 170 | 297 | No unit-review gate. |
| 29 | S2 | C9 (prereqs: F6, C8, F5, C1): 60 review minutes; then C10 (prereqs: C4): sessions 1–2 and 248 practice minutes. | 165 | 308 | C9 review gate. |
| 30 | S2 | C10 (prereqs: C4): sessions 3–4 and 307 practice minutes. | 170 | 307 | No unit-review gate. |
| 31 | S2 | C10 (prereqs: C4): 175 practice minutes and 55 review minutes; then `r1-001` for 180 minutes; then its debrief for 60 minutes. | 240 | 230 | C10 review gate, `r1-001` summative gate, and debrief. |

The verified Semester 1 columns sum to 2,545 in-class minutes + 5,370 independent minutes = 7,915 minutes.
The verified Semester 2 columns sum to 2,435 in-class minutes + 4,657 independent minutes = 7,092 minutes, where the in-class total includes the 180-minute mock and 60-minute debrief.
The Semester 1 average is 494.69 minutes, and its rows range from 485 to 500 minutes.
The Semester 2 average is 472.80 minutes, and its rows range from 449 to 499 minutes.

## 4. Milestones and assessment

Every manifested unit review is a formative checkpoint at the gate shown in the table.
The summative milestone is `r1-001` in Week 31, scored against its 300-point blueprint during its 180-minute duration and followed by the 60-minute debrief.
An `r1-002` slot remains optional and is not included in the baseline table.
If used, `r1-002` displaces 180 of Week 16's 360 C8 C-set/challenge practice minutes.
That substitution leaves 85 lesson minutes + 180 C8 practice minutes + 45 C8 review minutes + the 180-minute optional mock = the same 490-minute week.
The optional mock therefore replaces challenge practice rather than adding time or removing a lesson or unit review.

## 5. Provenance and regeneration

Lesson, practice, and review minutes come from `units/*/manifest.yaml`.
Prerequisite edges come from `syllabus.md` and are cross-checked against each unit manifest.
The mock duration and points come from `mocktests/r1-001/manifest.yaml`.
The count command deliberately sums every `lesson_sessions` list and every manifested review field.

<!-- Maintainer regeneration command: python3 -c 'import glob,yaml;
ds=[yaml.safe_load(open(p)) for p in glob.glob("units/*/manifest.yaml")];
ms=[d["estimated_minutes"] for d in ds];
print(sum(sum(m["lesson_sessions"]) for m in ms),sum(m["practice"] for m in ms),sum(m.get("review",0) for m in ms),sum(len(d["practice"]) for d in ds),sum(len(m["lesson_sessions"]) for m in ms),len(ds))' -->

The command's captured stdout is:

```text
4740 9237 790 383 57 17
```

The semester and table arithmetic was captured independently as:

```text
S1: 2545 + 5370 = 7915
S2: 2435 + 4657 = 7092
full: 7915 + 7092 = 15007
```

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
The first-instruction order is F1 (Week 1) → F2 (Week 2) → F4 (Week 4) → F3 (Week 5) → F5 (Week 6) → C1 (Week 9) → C2 (Week 10) → C3 (Week 12) → C4 (Week 13) → C8 (Week 15) → F6 (Week 17) → F7 (Week 19) → C5 (Week 21) → C6 (Week 23) → C7 (Week 25) → C9 (Week 27) → C10 (Week 29).
This is a topological order of the shipped syllabus DAG because every listed prerequisite appears earlier in that sequence.
F7 also finishes before C9 begins, even though F7 is not a formal C9 prerequisite, to preserve the intended mathematical systematics.
The table repeats every unit's complete prerequisite list beside every active week so the check remains local.
