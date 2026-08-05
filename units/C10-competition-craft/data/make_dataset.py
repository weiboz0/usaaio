"""Seeded generator for the C10 mini-competition dataset (source of truth).

The task: predict whether a honeybee colony THRIVES or STRUGGLES through
winter from 12 numeric features recorded at the autumn apiary inspection.
Binary classification, classes imbalanced roughly 2:1 (thrives:struggles),
so macro-F1 and accuracy genuinely disagree.

Feature structure (all draws are seeded; the file is byte-identical across runs):

- informative: honey_stores_kg, varroa_mite_index, forager_traffic_per_min,
  brood_frames (all load on a latent colony-vigor variable);
- correlated: autumn_hive_mass_kg is built from honey_stores_kg plus noise,
  and forager_traffic_per_min / brood_frames share the vigor latent;
- weakly informative: daily_temp_swing_c, queen_age_years;
- pure noise: insulation_thickness_mm, hive_age_years, distance_to_water_m,
  ambient_noise_db, apiary_elevation_m.

The scales differ wildly on purpose (varroa index ~0-5 vs elevation ~400 m):
raw Euclidean k-NN is dominated by the large-scale NOISE columns, so feature
scaling matters exactly the way C4 taught.

Usage (run from anywhere; files are written next to this script):

    python make_dataset.py              # writes train.csv (600 rows) ONLY
    python make_dataset.py --with-test  # also writes heldout.csv (200 rows)

The held-back split `heldout.csv` is the GRADING artifact: student notebooks
never read it. Graders (and the course's solution notebooks) regenerate it
deterministically with the flag at grading time and score
`predict_labels(...)` on it. Both runs above produce byte-identical
train.csv; the flag only controls whether the held-back rows are written.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260804
N_TOTAL = 800
N_TRAIN = 600  # the remaining 200 rows are the held-back grading split

FEATURES = [
    "honey_stores_kg",
    "autumn_hive_mass_kg",
    "varroa_mite_index",
    "forager_traffic_per_min",
    "brood_frames",
    "daily_temp_swing_c",
    "queen_age_years",
    "insulation_thickness_mm",
    "hive_age_years",
    "distance_to_water_m",
    "ambient_noise_db",
    "apiary_elevation_m",
]


def build_table() -> pd.DataFrame:
    """Deterministically build the full 800-row table (fixed draw order)."""
    rng = np.random.default_rng(SEED)

    # Labels first: thrives with probability 2/3 (the ~2:1 imbalance).
    thrives = rng.random(N_TOTAL) < 2.0 / 3.0
    outcome = np.where(thrives, "thrives", "struggles")

    # Latent colony vigor: higher for colonies that go on to thrive.
    vigor = rng.normal(0.0, 1.0, N_TOTAL) + np.where(thrives, 0.85, -0.85)

    honey_stores = 14.0 + 3.0 * vigor + rng.normal(0.0, 1.6, N_TOTAL)
    hive_mass = 17.0 + 0.9 * honey_stores + rng.normal(0.0, 1.3, N_TOTAL)
    varroa = np.clip(2.6 - 0.85 * vigor + rng.normal(0.0, 0.75, N_TOTAL), 0.0, None)
    forager = np.clip(34.0 + 6.0 * vigor + rng.normal(0.0, 4.5, N_TOTAL), 0.0, None)
    brood = np.clip(6.5 + 1.1 * vigor + rng.normal(0.0, 1.1, N_TOTAL), 0.0, None)
    temp_swing = np.clip(9.0 - 0.7 * vigor + rng.normal(0.0, 2.1, N_TOTAL), 0.0, None)
    queen_age = np.clip(1.9 - 0.25 * vigor + rng.normal(0.0, 0.85, N_TOTAL), 0.1, None)
    insulation = np.clip(22.0 + rng.normal(0.0, 6.0, N_TOTAL), 4.0, None)
    hive_age = np.clip(5.0 + rng.normal(0.0, 2.4, N_TOTAL), 0.2, None)
    water_dist = np.clip(260.0 + rng.normal(0.0, 90.0, N_TOTAL), 20.0, None)
    noise_db = np.clip(46.0 + rng.normal(0.0, 7.0, N_TOTAL), 20.0, None)
    elevation = np.clip(410.0 + rng.normal(0.0, 120.0, N_TOTAL), 5.0, None)

    table = pd.DataFrame(
        {
            "outcome": outcome,
            "honey_stores_kg": honey_stores,
            "autumn_hive_mass_kg": hive_mass,
            "varroa_mite_index": varroa,
            "forager_traffic_per_min": forager,
            "brood_frames": brood,
            "daily_temp_swing_c": temp_swing,
            "queen_age_years": queen_age,
            "insulation_thickness_mm": insulation,
            "hive_age_years": hive_age,
            "distance_to_water_m": water_dist,
            "ambient_noise_db": noise_db,
            "apiary_elevation_m": elevation,
        }
    )

    # Seeded shuffle so classes interleave, then a fixed positional split.
    order = rng.permutation(N_TOTAL)
    table = table.iloc[order].reset_index(drop=True)
    return table.round(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--with-test",
        action="store_true",
        help="also write heldout.csv, the held-back grading split",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    table = build_table()
    train, heldout = table.iloc[:N_TRAIN], table.iloc[N_TRAIN:]

    train.to_csv(here / "train.csv", index=False)
    print(f"wrote train.csv: {train.shape[0]} rows, {train.shape[1]} columns")
    print("train outcome counts:", train["outcome"].value_counts().to_dict())

    if args.with_test:
        heldout.reset_index(drop=True).to_csv(here / "heldout.csv", index=False)
        print(f"wrote heldout.csv: {heldout.shape[0]} rows (grading register only)")


if __name__ == "__main__":
    main()
