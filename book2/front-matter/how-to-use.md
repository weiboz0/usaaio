# How to Use This Book

Each chapter of this book is one unit of the course.
A unit begins with an overview: its goals, the Book 1 units it builds on, a map of its class sessions, and advice on how to study it.
Next comes the Book 1 bridge, a 30-minute diagnostic of the earlier ideas the unit uses.
The class sessions follow, and the unit ends with a review.
Read a session with its notebook open, run the code, and change it to see what happens.
Then work the unit's practice problems.

## Before you start

This book assumes everything in *Machine Learning for the AI Olympiad* (Book 1).
Book 2 does not reteach those ideas; instead it names them and links back to them.
A Book 1 unit or concept is written with the prefix `book1:`, for example `book1:C6-pytorch` or `book1:softmax`.
If a bridge diagnostic shows a gap, follow the named link and review that Book 1 unit before Session 1.

## Reading the page

- **Header block:** Every notebook opens with a short block of lines like these.
  - **Program layer** is always *Round 2 extension*.
  - **Compute** gives the compute policy and the fixed random seed (see below).
  - **Qualified prerequisites** lists the Book 1 and earlier Book 2 units the notebook relies on.
  - **Remediation links** point to the units to review if those ideas are not fluent.
  - **Data boundary**, when present, says which data and libraries you may use.
- **Minutes:** The time the notebook is planned to take, such as *20 minutes.*
- **Checkpoint 1A, 1B, …:** Two short questions at the end of each section.
  Answer both before you read on.
- **Collected answers:** The answers to a section's checkpoints, printed in the notebook right after them or gathered at the end of the session.
  Cover them until you have answered.
- **Worked example / Worked laboratory:** A problem or small experiment carried out in full, often with a recorded trace of shapes and losses.
- **Common pitfalls:** Real mistakes, such as a mask applied after the softmax or targets that are not shifted, each with its repair.
- **Exam connections:** How the unit's ideas tend to appear in Round 2 questions.
- **Going deeper:** Optional, forward-looking material.
  Nothing required depends on it.
- **Review:** The unit's last section.
  It has a sheet of formulas and protocols, a table that says which problems to redo for each concept, and a self-quiz with its answers.
- **Practice header:** A line such as **Set:** A · **Type:** mc · **Difficulty:** intro, followed by the concepts tested.
  The glossary gives each concept in plain words.
- **Reasoning is required / Reasoning is not required:** Tells you whether a written argument is graded, or only the final answer.
- **Normal form:** A numeric answer requested in an exact shape, such as a fraction in lowest terms.
  An equivalent value in another form earns nothing.
- **Banned APIs:** Functions or modules you may not use.
  A part that uses one scores zero.
- **Your response:** The cells where your derivations, code, and checks go.
  Many problems ask you to end coding work with an answer-check section of `assert` lines.
- **Accelerator extension:** An optional section, in some capstone problems, that reruns your code with a larger configuration on a Colab L4 GPU. It is never required and never graded.

<!-- edition: student-print -->
- **Practice file:** In this print edition a practice problem shows its statement only.
  The line "Practice file:" under it names the notebook that holds its code cells, such as `units/B2-022-probabilistic-latent-models/practice/p05.ipynb` (relative to the `book2` folder).
  Open that file to write and run your answer.
<!-- /edition -->

## Compute policy

Every notebook declares a compute policy in its header.

- **`cpu`:** Everything runs on an ordinary CPU, and that is the only path.
  Almost every notebook in the book is of this kind.
- **`optional-colab-l4`:** The required work still runs on a CPU. An extra *Accelerator extension* section shows how to run the same code, unchanged except for a configuration dictionary, on a Colab L4 GPU. Try it if you have access; skip it if you do not.

No notebook requires a GPU.
No required work downloads pretrained weights or outside datasets.

## Work in the course files

The course files are the source of this book.
Every page of every unit comes from a Jupyter notebook in the `book2` folder:

```text
book2/
  units/
    <unit>/
      lesson.ipynb              the unit overview: goals, sessions, how to study
      lessons/
        00-book1-bridge.ipynb   the Book 1 diagnostic
        01-<topic>.ipynb        one notebook per class session
        ...
      review.ipynb              formula sheet, retrieval table, self-quiz
      practice/
        p01.ipynb               practice problems: write your answers here
        ...
      data/                     data files and the loader your notebooks call, when used
      scripts/                  the seeded scripts that generate the data
      manifest.yaml             the unit's concepts, practice list, and timings
  mocktests/
    r2-001/                     the two-day mock test
```

A unit is named by its code and a short title, such as `B2-022-probabilistic-latent-models`.

Open the unit's `practice/pNN.ipynb` in Jupyter, write your answer in the response cells, and run the whole notebook from the top before you call it done.
Keep every seed line the notebook gives you; a fixed seed is what makes your numbers match the expected ones.
Load data only through the provided code cells and the loader in `data/`.

The practice folder also holds a solution notebook for each problem, named like `p05_solution.ipynb`.
Those files are for your teacher.
If you have them, leave them closed until you have made a real attempt and your teacher says it is time.

The `mocktests` folder holds a complete two-day mock exam.
It is meant to be taken once, at the end of the course; your teacher will give it to you.

## The three practice sets

Every unit's practice problems are grouped into three sets, and each problem's header names its set.

- **Set A — fundamentals:** One idea at a time, at introductory or core difficulty.
  Do these first.
- **Set B — exam register:** Questions in the form the competition uses: exact identifiers, banned APIs, five-option multiple choice, normal-form answers, and derivations where reasoning is required.
- **Set C — integration and challenge:** Multi-part arcs in which later parts use earlier results, scenario analyses, and open-ended modeling tasks.

Do Set A, then Set B, then Set C.

## Check your work

Most checkpoint answers are printed in the notebooks, in a paragraph or section headed **Collected answers**.
Answer each checkpoint first, then read the answer, then go back to the text if you missed.

<!-- edition: student -->
At the back, **Answers to Checkpoints and Selected Practice** gives worked solutions to the Set A practice problems of every unit, together with every unit's checkpoint and self-quiz answers; where a notebook prints those answers, this book shows a page reference instead.
Sets B and C have no printed answers.
<!-- /edition -->
<!-- edition: student-print -->
Where a notebook has checkpoint or self-quiz answers, this print edition shows a one-line note instead; open the notebook to read them.
Worked solutions to the Set A practice problems are in the separate Answer Key.
The course files are at github.com/weiboz0/usaaio; ask your teacher for the Answer Key and the full Student Book.
<!-- /edition -->
<!-- edition: teacher -->
In this Teacher's Edition, every checkpoint and self-quiz answer appears in place, in a panel labelled **Answers**.
Every practice problem is followed by its full solution, and the final part of the book holds the mock test with its answer key and rubric.
The student books give worked solutions to the Set A practice problems only; Sets B and C have none.
<!-- /edition -->

Try every problem before you look at an answer.
If you get stuck, read just enough of the answer to see your next step, close it, and finish on your own.

<!-- edition: student|student-print -->
Sets B and C have no printed answers because they are where you show what you can do on your own.
Most practice problems state the exact names, shapes, and checks your code must satisfy, so an answer-check section of your own can test much of your work.
When you cannot tell whether your answer is right, ask your teacher.
<!-- /edition -->

Pages of this book show code without its output.
Run a notebook to see the numbers it produces.
