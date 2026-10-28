# B2-022-probabilistic-latent-models Errata

## Lesson 02: KL direction wording

**Corrected:** 2026-10-27 (Plan 033)

Section 1 of `lessons/02-kl-divergence.ipynb` introduced $\mathrm{KL}(P\,\|\,Q)$ as "the Kullback–Leibler divergence of $Q$ from $P$".
Sources disagree on which way "of … from …" reads, and the book's glossary and notation table describe the direction differently: "the extra expected log loss from using $Q$ when the data follow $P$".

The sentence now reads "The **Kullback–Leibler divergence** is", followed by the formula.
The next sentence already gives the direction in the back-matter sense ("the average extra log-loss you pay for believing $Q$ when outcomes really come from $P$").

The formula, every computation and every practice answer are unaffected.
