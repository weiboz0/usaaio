# Book 1 unit renumbering (Plan 031)

On 2026-10-12 the Book 1 units were put in teaching order.
Each unit folder gained a two-digit prefix, `NN-<unit id>`, and the F and C codes were renumbered so that F1–F7 and C1–C12 each count up in the order the course teaches them.
The teaching order is declared in `book1/curriculum/course-schedule.yaml` (`teaching_order:`) and enforced by `unit-order-check`.

Plans, designs, `TODO.md` history and `ERRATA.md` files written before Plan 031 keep the old codes as written.
Use this table to translate them.

| Order | Old id | New id | Folder |
|---|---|---|---|
| 01 | `F1-scientific-python` | `F1-scientific-python` | `01-F1-scientific-python` |
| 02 | `F2-vectors` | `F2-vectors` | `02-F2-vectors` |
| 03 | `F4-multivar-calculus` | `F3-multivar-calculus` | `03-F3-multivar-calculus` |
| 04 | `F3-matrices` | `F4-matrices` | `04-F4-matrices` |
| 05 | `F5-probability` | `F5-probability` | `05-F5-probability` |
| 06 | `C1-ml-fundamentals` | `C1-ml-fundamentals` | `06-C1-ml-fundamentals` |
| 07 | `C2-linear-models` | `C2-linear-models` | `07-C2-linear-models` |
| 08 | `C3-gradient-descent` | `C3-gradient-descent` | `08-C3-gradient-descent` |
| 09 | `C4-classical-ml-practice` | `C4-classical-ml-practice` | `09-C4-classical-ml-practice` |
| 10 | `C8-embeddings` | `C5-embeddings` | `10-C5-embeddings` |
| 11 | `C5-neural-networks` | `C6-neural-networks` | `11-C6-neural-networks` |
| 12 | `F6-svd-spectral` | `F6-svd-spectral` | `12-F6-svd-spectral` |
| 13 | `C6-pytorch` | `C7-pytorch` | `13-C7-pytorch` |
| 14 | `F7-kernels-convex-optimization` | `F7-kernels-convex-optimization` | `14-F7-kernels-convex-optimization` |
| 15 | `C11-neural-training` | `C8-neural-training` | `15-C8-neural-training` |
| 16 | `C9-dimensionality-reduction` | `C9-dimensionality-reduction` | `16-C9-dimensionality-reduction` |
| 17 | `C7-cnn-transfer` | `C10-cnn-transfer` | `17-C10-cnn-transfer` |
| 18 | `C10-competition-craft` | `C11-competition-craft` | `18-C11-competition-craft` |
| 19 | `C12-classical-models` | `C12-classical-models` | `19-C12-classical-models` |

Eight codes changed: the swap F3 ↔ F4 and the cycle old C5→C6, C6→C7, C7→C10, C10→C11, C11→C8, C8→C5.
Practice ids carry their unit's code and moved with it (old `C7-p10` is now `C10-p10`, old `C11-p16` is now `C8-p16`).
Book 2 folders and ids did not change; Book 2's `book1:` references use the new codes.

The rewrite was mechanical and is reproducible from `scripts/renumber-book1-units.py`, which holds this table as data.
