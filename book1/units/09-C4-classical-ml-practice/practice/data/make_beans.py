"""Seeded generator for beans.csv (source of truth for the committed CSV).

Three bean varieties with four numeric features on comparable scales.
The classes overlap on purpose: a k-nearest-neighbors classifier should do
well but not perfectly.  Regenerate with:

    python make_beans.py

The committed beans.csv is a convenience artifact of exactly this script;
any edit to the script must be followed by regeneration.
"""

import numpy as np
import pandas as pd

SEED = 20260804
N_PER_CLASS = 30

# species -> (length_mm, width_mm, mass_g, moisture_pct) means, then stds
MEANS = {
    "alba": (11.5, 6.0, 0.45, 10.8),
    "brio": (13.0, 7.0, 0.60, 11.4),
    "cava": (15.5, 7.8, 0.82, 12.1),
}
STDS = (1.1, 0.55, 0.09, 0.7)


def main() -> None:
    rng = np.random.default_rng(SEED)
    frames = []
    for species, means in MEANS.items():
        block = rng.normal(means, STDS, size=(N_PER_CLASS, 4))
        frame = pd.DataFrame(
            block, columns=["length_mm", "width_mm", "mass_g", "moisture_pct"]
        )
        frame.insert(0, "species", species)
        frames.append(frame)
    beans = pd.concat(frames, ignore_index=True)
    # shuffle rows with the same seeded generator so classes interleave
    order = rng.permutation(len(beans))
    beans = beans.iloc[order].reset_index(drop=True)
    beans = beans.round({"length_mm": 2, "width_mm": 2, "mass_g": 3, "moisture_pct": 2})
    beans.to_csv("beans.csv", index=False)
    print(f"wrote beans.csv: {beans.shape[0]} rows, {beans.shape[1]} columns")


if __name__ == "__main__":
    main()
