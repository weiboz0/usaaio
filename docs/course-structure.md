# Course Structure

## 1. Course model

The currently shipped R1-first schedule runs for two 13-week semesters, or 26 weeks in all.
The manifests provide 3,900 lesson minutes, 7,767 practice minutes, and 680 review minutes,
so manifested content is 3,900 + 7,767 + 680 = 12,347 minutes = 205.8 hours.
Lessons supply 3,900 / 60 = 65 in-class hours, while practice and reviews supply
(7,767 + 680) / 60 = 140.8 independent hours.
Across 26 weeks, that content-only division is 2.5 in-class hours and 5.4 independent hours
per week.
Semester 1 contains 6,270 minutes = 104.5 hours, or 8.0 hours per week.
Semester 2 contains 6,077 manifested minutes plus the 180-minute mock and 60-minute debrief:
6,077 + 240 = 6,317 minutes = 105.3 hours, or 8.1 hours per week.
The full scheduled course is therefore 6,270 + 6,317 = 12,587 minutes = 209.8 hours, of
which manifested curriculum contributes 205.8 hours and the final mock plus debrief contributes
4 hours. The planned official-topic extensions in `docs/curriculum-roadmap.md` are estimates,
not manifested time, and do not fit silently into this schedule.

## 2. Semester split

Semester 1 follows F1 → F2 → {F4, F3} → F5 → C1 → C2 → C3 → C4.
Its unit arithmetic is 700 + 665 + 610 + 745 + 720 + 705 + 630 + 640 + 855 = 6,270 minutes = 104.5 hours.
This sequence covers the foundations and classical-ML core and ends with C4's sklearn practice as the semester capstone.
Semester 2 follows C5 → C6 → C7 ∥ C8 → F6 → C9 → C10 → r1-001.
Its content arithmetic is 845 + 815 + 972 + 795 + 1,075 + 745 + 830 = 6,077 minutes = 101.3 hours.
Adding the 180-minute mock and 60-minute debrief gives 6,077 + 240 = 6,317 minutes = 105.3 hours.
F6 sits directly before its C9 consumer, and its five 85-minute sessions are split 2 + 2 + 1 across three teaching weeks so every sitting remains within the 60–90-minute session rule.

## 3. Week-by-week table

In-class minutes are manifest lesson sessions plus the final mock and debrief, while independent minutes are manifest practice and review minutes.
Fixed sessions and reviews are placed first,
and each unit's practice is then distributed across its active teaching window in proportion to the weekly capacity remaining inside the ±10% authoring-convention load band (a pacing choice, not manifest-derived).
A unit remains active through its review gate even when its final row has no new lesson session.
In a mixed row, “then” gives the within-week instructional order.

| Week | Semester | Units and sessions covered | In-class minutes | Independent minutes | Checkpoint gate |
|---:|:---:|---|---:|---:|---|
| 1 | S1 | F1 (prereqs: none): sessions 1–2 and 270 practice minutes. | 165 | 270 | No unit-review gate. |
| 2 | S1 | F1 (prereqs: none): session 3, 150 practice minutes, and 40 review minutes; then F2 (prereqs: F1): session 1 and 155 practice minutes. | 150 | 345 | F1 review gate. |
| 3 | S1 | F2 (prereqs: F1): sessions 2–3, 235 practice minutes, and 45 review minutes. | 155 | 280 | F2 review gate. |
| 4 | S1 | F4 (prereqs: F2): session 1 and 218 practice minutes; F3 (prereqs: F2): session 1 and 135 practice minutes. | 160 | 353 | No unit-review gate. |
| 5 | S1 | F4 (prereqs: F2): session 2, 182 practice minutes, and 40 review minutes; F3 (prereqs: F2): session 2 and 116 practice minutes. | 175 | 338 | F4 review gate. |
| 6 | S1 | F3 (prereqs: F2): session 3, 199 practice minutes, and 45 review minutes; then F5 (prereqs: F1): session 1 and 93 practice minutes. | 165 | 337 | F3 review gate. |
| 7 | S1 | F5 (prereqs: F1): sessions 2–3 and 270 practice minutes. | 170 | 270 | No unit-review gate. |
| 8 | S1 | F5 (prereqs: F1): 67 practice minutes and 40 review minutes; then C1 (prereqs: F1): sessions 1–2 and 254 practice minutes. | 160 | 361 | F5 review gate. |
| 9 | S1 | C1 (prereqs: F1): session 3, 181 practice minutes, and 30 review minutes; then C2 (prereqs: F3, F4, C1): session 1 and 144 practice minutes. | 165 | 355 | C1 review gate. |
| 10 | S1 | C2 (prereqs: F3, F4, C1): session 2, 276 practice minutes, and 40 review minutes; then C3 (prereqs: F4, C2): session 1 and 20 practice minutes. | 170 | 336 | C2 review gate. |
| 11 | S1 | C3 (prereqs: F4, C2): session 2 and 215 practice minutes; then C4 (prereqs: C1, F1, F2, F5): session 1 and 84 practice minutes. | 165 | 299 | No unit-review gate. |
| 12 | S1 | C3 (prereqs: F4, C2): 195 practice minutes and 40 review minutes; C4 (prereqs: C1, F1, F2, F5): sessions 2–3 and 58 practice minutes. | 170 | 293 | C3 review gate. |
| 13 | S1 | C4 (prereqs: C1, F1, F2, F5): 418 capstone-practice minutes and 45 review minutes. | 0 | 463 | C4 review gate and sklearn practice capstone close S1. |
| 14 | S2 | C5 (prereqs: C3, F5): sessions 1–2 and 357 practice minutes. | 165 | 357 | No unit-review gate. |
| 15 | S2 | C5 (prereqs: C3, F5): session 3, 193 practice minutes, and 45 review minutes; then C6 (prereqs: C5): session 1 and 119 practice minutes. | 165 | 357 | C5 review gate. |
| 16 | S2 | C6 (prereqs: C5): sessions 2–3 and 287 practice minutes. | 170 | 287 | No unit-review gate. |
| 17 | S2 | C6 (prereqs: C5): 114 practice minutes and 45 review minutes; then C7 (prereqs: C6): session 1 and 118 practice minutes; C8 (prereqs: F2, F3, F1): session 1 and 92 practice minutes. | 165 | 369 | C6 review gate. |
| 18 | S2 | C7 (prereqs: C6): session 2 and 209 practice minutes; C8 (prereqs: F2, F3, F1): session 2 and 155 practice minutes. | 170 | 364 | No unit-review gate. |
| 19 | S2 | C7 (prereqs: C6): session 3 and 210 practice minutes; C8 (prereqs: F2, F3, F1): session 3 and 154 practice minutes. | 170 | 364 | No unit-review gate. |
| 20 | S2 | C7 (prereqs: C6): 135 practice minutes and 45 review minutes; C8 (prereqs: F2, F3, F1): 99 practice minutes and 45 review minutes; then F6 (prereqs: F3): sessions 1–2 and 29 practice minutes. | 170 | 353 | C7 and C8 review gates. |
| 21 | S2 | F6 (prereqs: F3): sessions 3–4 and 268 practice minutes. | 170 | 268 | No unit-review gate. |
| 22 | S2 | F6 (prereqs: F3): session 5, 308 practice minutes, and 45 review minutes. | 85 | 353 | F6 review gate. |
| 23 | S2 | C9 (prereqs: F6, C8, F5, C1): sessions 1–2 and 273 practice minutes. | 165 | 273 | No unit-review gate. |
| 24 | S2 | C9 (prereqs: F6, C8, F5, C1): session 3, 177 practice minutes, and 45 review minutes; then C10 (prereqs: C4): session 1 and 81 practice minutes. | 165 | 303 | C9 review gate. |
| 25 | S2 | C10 (prereqs: C4): sessions 2–3 and 285 practice minutes. | 170 | 285 | No unit-review gate. |
| 26 | S2 | C10 (prereqs: C4): 169 practice minutes and 45 review minutes; then r1-001 mock for 180 minutes; then debrief for 60 minutes. | 240 | 214 | C10 review gate, r1-001 summative gate, and debrief. |

The verified S1 column sums are 1,970 in-class minutes + 4,300 independent minutes = 6,270 minutes.
The verified S2 column sums are 2,170 in-class minutes + 4,147 independent minutes = 6,317 minutes, where the in-class total includes the 180-minute mock and 60-minute debrief.
The S1 average is 482.31 minutes, so its ±10% band is 434.08–530.54 minutes, and the table's S1 rows range from 435 to 521 minutes.
The S2 average is 485.92 minutes, so its ±10% band is 437.33–534.52 minutes, and the table's S2 rows range from 438 to 534 minutes.

## 4. Milestones and assessment

Every manifested unit review is a formative checkpoint at the gate shown in the table,
including F1's 40-minute review in Week 2.
The summative milestone is r1-001 in Week 26, scored against its 300-point blueprint during its 180-minute duration and followed by the 60-minute debrief.
An r1-002 slot is optional, generated on demand, and is not included in the baseline table.
If used, r1-002 displaces 180 of Week 13's 418 C4 capstone-practice minutes, leaving
238 C4 practice minutes + 45 C4 review minutes + the 180-minute second mock = the same
463-minute review week.
Note that this flips Week 13's in-class/independent split from 0/463 to 180/283, because the
proctored mock counts as in-class time under §3's definitions.
The optional mock therefore replaces challenge-practice time in the S1-end review week instead of adding hours or removing a lesson or unit review.

## 5. Provenance and regeneration

All lesson, practice,
and review minutes come from `units/*/manifest.yaml`, all prerequisite edges come from `syllabus.md`,
and the mock's duration and points come from `mocktests/r1-001/manifest.yaml`.
The lesson total deliberately sums every `lesson_sessions` list because C1 has no `lesson`
scalar, while the review total sums every manifested review field, including F1's 40-minute
review.
<!-- Maintainer regeneration command: python3 -c 'import glob,yaml;
ms=[yaml.safe_load(open(p))["estimated_minutes"] for p in glob.glob("units/*/manifest.yaml")];
print(sum(sum(m["lesson_sessions"]) for m in ms),sum(m["practice"] for m in ms),sum(m.get("review",0) for m in ms))' -->
The command's captured stdout is:

```text
3900 7767 680
```

## 6. Grading and calendar buffer

The suggested weighting leaves unit-review checkpoints formative and ungraded and assigns the entire summative assessment weight to r1-001's 300-point blueprint score.
The pass bar should reference the blueprint's intro, core,
and advanced difficulty bands: reliable performance on intro and core work supports a pass, while advanced work distinguishes performance above that bar.
No numeric course-pass cutoff is introduced because the authoritative inputs define difficulty bands and points but no course-pass percentage.
Semester 1 runs at 8.0 hours per week and Semester 2 at 8.1, with no calendar slack, so recovery starts by trimming C-set and challenge practice first.
Lessons and unit reviews are never trimmed.
The optional r1-002 follows the same buffer policy by displacing Week 13 challenge practice rather than adding time.

## 7. Prerequisite integrity

Prerequisite integrity holds at SESSION granularity.
Within a shared week, "then" denotes strict in-week sequence: a unit's first session always begins after its prerequisites' final sessions (and their practice) in that week's row.
Consequently the week-level order below lists first-instruction weeks; shared weeks (2, 9, 10, 15, 17) are sequenced internally by the table's "then" notation.


The first-instruction order is F1 (Week 1) → F2 (Week 2) → {F4, F3} (Week 4) → F5 (Week 6) → C1 (Week 8) → C2 (Week 9) → C3 (Week 10) → C4 (Week 11) → C5 (Week 14) → C6 (Week 15) → {C7, C8} (Week 17) → F6 (Week 20) → C9 (Week 23) → C10 (Week 24).
This is a topological order of the syllabus DAG because every unit's listed prerequisites appear earlier in that sequence.
The table makes the check local by repeating every unit's complete prerequisite list beside every week in which that unit appears.
Where a mixed week completes one unit and opens the next, the table's “then” order preserves the prerequisite sequence within that week.
