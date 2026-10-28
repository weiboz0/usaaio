# C11-competition-craft Errata

## Practice p12 solution: lost inline-math delimiters

**Corrected:** 2026-10-27 (Plan 033)

The reasoning cell of `practice/p12_solution.ipynb` wrote six inline formulas with bare parentheses, such as `(A_j=\frac1{50}\sum_{i=1}^{50} I_{ji})`, where `\(…\)` was intended.
Jupyter therefore showed the raw TeX, and the Plan 030 editions printed it literally.

The six spans now use `\(…\)`, matching the cell's `\[…\]` display math.
No other text changed.

The answer, the code and the checks are unaffected.
A scan of every markdown cell in both books found no other cell with this defect.
