# How to Use This Book

Each chapter of this book is one unit of the course.
A unit begins with an overview: its goals, the prerequisites it relies on, a map of its class sessions, and advice on how to study it.
The sessions follow, one section of the chapter each, and the unit ends with a review.
Read a session with the notebook open beside you, run the examples, and change them to see what happens.
Then work the unit's practice problems.

## Reading the page

- **Motivation / Definition / Worked example:** A session section usually opens with a problem that needs the new idea, states the idea precisely, and then works one example in full.
- **Checkpoint:** Short questions placed right after the idea they test, usually two per section.
  Answer them before you read on.
- **Worked exam-style example:** A problem solved step by step in the same form a competition question uses, including its answer form and any banned tools.
- **Common pitfalls:** Mistakes newcomers really make, each shown as broken code or a wrong argument, followed by the fix.
- **Exam connections:** How the unit's ideas tend to appear in Round 1 questions.
- **Going deeper:** Optional material that points ahead to a later unit.
  Nothing later in the book depends on it.
- **Review:** The unit's last section.
  It has a concept summary, a sheet of formulas and code idioms, a self-quiz, and a list of practice problems to redo for each weak spot.
- **Practice header:** Each practice problem opens with a line such as **Type:** constrained coding · **Difficulty:** intro · **Concepts:** gradient-descent.
  The concepts are the course's names for the ideas being tested; the glossary at the back gives each one in plain words.
- **Multiple choice:** Exactly five options, A to E, with one correct.
  Record your choice in the code cell, for example `answer_p01 = "B"`.
- **Reasoning is required / Reasoning is not required:** Tells you whether a written argument is graded, or only the final answer.
- **Normal form:** A numeric answer requested in an exact shape, such as a fraction $a/b$ in lowest terms with a positive denominator.
  An equivalent value in another form does not earn the points.
- **Banned (zero points):** A list of functions or operators you may not use.
  Code that uses one of them earns zero for that part, even if its answer is right.
- **`# YOUR CODE HERE`:** Where your code goes.
  Keep every function name, argument list, and variable name exactly as given; a grader looks for them by name.

<!-- edition: student|teacher -->
- **Starter code:** The code cells of a practice problem.
  They load data, fix a random seed, and leave blanks for you to fill in.
<!-- /edition -->
<!-- edition: student-print -->
- **Practice file:** In this print edition a practice problem shows its statement only.
  The line "Practice file:" under it names the notebook that holds the starter code, such as `units/C3-gradient-descent/practice/p05.ipynb` (relative to the `book1` folder).
  Open that file to write and run your answer.
<!-- /edition -->

## Work in the course files

The course files are the source of this book.
Every page of every unit comes from a Jupyter notebook in the `book1` folder:

```text
book1/
  units/
    <unit>/
      lesson.ipynb          the unit overview: goals, sessions, how to study
      lessons/
        01-<topic>.ipynb    one notebook per class session
        02-<topic>.ipynb
        ...
      review.ipynb          concept summary, formula sheet, self-quiz
      practice/
        p01.ipynb           practice problems: write your answers here
        p02.ipynb
        ...
      data/                 data files and the seeded scripts that make them, when used
      manifest.yaml         the unit's concepts, practice list, and timings
  mocktests/
    r1-001/                 the full-length mock test
```

A unit is named by its code and a short title, such as `C3-gradient-descent`.
Units whose code starts with **F** are the foundations; units starting with **C** are the core machine-learning units.
The chapters of this book follow that numbering, but the course schedule teaches them in a slightly different order (see For Teachers, or ask your teacher).

Open the unit's `practice/pNN.ipynb` in Jupyter, write your answer in the code cells, and run the whole notebook from the top before you call it done.
A notebook that only works when its cells are run in a special order is not finished.
Every random choice in the course uses a fixed seed, so when you run a notebook from the top you get the same numbers every time.
Datasets are never mysterious files: each one is made by a short seeded script that sits next to it in a `data/` folder, either in the unit folder or in its `practice` folder.

The practice folder also holds a solution notebook for each problem, named like `p05_solution.ipynb`.
Those files are for your teacher.
If you have them, leave them closed until you have made a real attempt and your teacher says it is time.

The `mocktests` folder holds a complete mock exam with its own statements, rubric, and solutions.
It is meant to be taken once, under timed conditions, at the end of the course; your teacher will give it to you.

## The three practice sets

Every unit's practice problems are grouped into three sets.

- **Set A — fundamentals:** One idea at a time, at introductory or core difficulty.
  Do these first.
- **Set B — exam register:** Questions in the form the competition uses: exact function contracts, banned tools, five-option multiple choice, and answers in normal form.
- **Set C — integration and challenge:** Multi-part problems in which later parts use earlier results, realistic scenarios, and advanced problems.

Most unit overviews list which problems belong to each set, and your teacher's assignments follow the same grouping.
Do Set A, then Set B, then Set C.

## Check your work

<!-- edition: student -->
Most checkpoint answers in the notebooks are hidden in a collapsed block that you click to open.
In this book, each of those places shows a short reference instead, and the answers are collected at the back in **Answers to Checkpoints and Selected Practice**.
Some sessions print their checkpoint answers openly at the end of the notebook; this book moves those to the appendix too.
That appendix gives the checkpoint and self-quiz answers for every unit, then worked solutions to the Set A practice problems.
Sets B and C have no printed answers.
<!-- /edition -->
<!-- edition: student-print -->
Most checkpoint answers in the notebooks are hidden in a collapsed block that you click to open.
This print edition does not reproduce them.
Where a notebook has checkpoint or self-quiz answers, hidden or printed openly, this book prints a one-line note instead.
Worked solutions to the Set A practice problems are in the separate Answer Key, and the full Student Book collects the checkpoint answers in an appendix.
The course files are at github.com/weiboz0/usaaio; ask your teacher for the Answer Key and the full Student Book.
<!-- /edition -->
<!-- edition: teacher -->
In this Teacher's Edition, the checkpoint and self-quiz answers that the notebooks hide in a collapsed block appear in place, in a panel labelled **Answers**.
Answers that a notebook prints openly appear in the same panels.
Every practice problem is followed by its full solution, and the final part of the book holds the mock test with its answer key and rubric.
The student books give worked solutions to the Set A practice problems only; Sets B and C have none.
<!-- /edition -->

Try every checkpoint and every problem before you look at an answer.
If you get stuck, read just enough of the answer to see your next step, close it, and finish on your own.
Then compare your work with the answer and ask why any difference matters.

<!-- edition: student|student-print -->
Sets B and C have no printed answers because they are where you show what you can do on your own.
Many coding problems state the exact names, shapes, and types your code must produce, and some end with a cell of `assert` checks, so you can test much of your work yourself.
When you cannot tell whether your answer is right, ask your teacher.
<!-- /edition -->

Some solutions in the course print values when they run.
Pages of this book show code without its output, so run the notebook to see the numbers.
