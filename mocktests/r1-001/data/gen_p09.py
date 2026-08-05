"""Generate the seeded P9 urban street-tree health dataset.

The prediction target is whether a tree ``thrives`` or ``declines``.  The
table deliberately mixes informative, correlated, weak, and noise features,
including differently scaled columns that make preprocessing important for
distance-based models.

Usage (outputs are written next to this script):

    python gen_p09.py              # writes p09_train.csv only
    python gen_p09.py --with-test  # also writes p09_heldout.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 20260806
N_TOTAL = 800
N_TRAIN = 600

FEATURES = [
    "species_diversity_index",
    "soil_compaction_kpa",
    "canopy_width_m",
    "nearest_traffic_lane_m",
    "watering_visits_monthly",
    "trunk_diameter_cm",
    "leaf_chlorophyll_index",
    "root_zone_area_m2",
    "summer_heat_days",
    "pest_damage_pct",
    "sidewalk_width_m",
    "night_light_lux",
]


def build_table() -> pd.DataFrame:
    """Return the full deterministic 800-row table in shuffled order."""
    rng = np.random.default_rng(SEED)

    # Pin the total class ratio, then shuffle rows only after all draws.
    thrives = np.zeros(N_TOTAL, dtype=bool)
    thrives[:533] = True
    health = rng.normal(0.0, 1.0, N_TOTAL) + np.where(thrives, 0.82, -0.82)

    diversity = np.clip(0.55 + 0.11 * health + rng.normal(0.0, 0.10, N_TOTAL), 0.05, 0.95)
    compaction = np.clip(245.0 - 29.0 * health + rng.normal(0.0, 30.0, N_TOTAL), 80.0, 430.0)
    canopy = np.clip(5.8 + 1.15 * health + rng.normal(0.0, 1.15, N_TOTAL), 1.0, None)
    traffic_distance = np.clip(5.5 + 1.15 * health + rng.normal(0.0, 2.0, N_TOTAL), 0.3, None)
    watering = np.clip(3.2 + 0.75 * health + rng.normal(0.0, 1.0, N_TOTAL), 0.0, None)
    trunk_diameter = np.clip(12.0 + 3.9 * canopy + rng.normal(0.0, 4.0, N_TOTAL), 4.0, None)
    chlorophyll = np.clip(39.0 + 4.9 * health + rng.normal(0.0, 4.7, N_TOTAL), 10.0, 70.0)
    root_zone = np.clip(4.0 + 0.72 * canopy + rng.normal(0.0, 1.5, N_TOTAL), 0.8, None)
    heat_days = np.clip(24.0 - 2.2 * health + rng.normal(0.0, 7.0, N_TOTAL), 0.0, None)
    pest_damage = np.clip(17.0 - 4.4 * health + rng.normal(0.0, 6.5, N_TOTAL), 0.0, 60.0)

    # Pure noise at intentionally different scales.
    sidewalk_width = np.clip(2.6 + rng.normal(0.0, 0.65, N_TOTAL), 0.8, None)
    night_light = np.clip(165.0 + rng.normal(0.0, 75.0, N_TOTAL), 0.0, None)

    table = pd.DataFrame(
        {
            "outcome": np.where(thrives, "thrives", "declines"),
            "species_diversity_index": diversity,
            "soil_compaction_kpa": compaction,
            "canopy_width_m": canopy,
            "nearest_traffic_lane_m": traffic_distance,
            "watering_visits_monthly": watering,
            "trunk_diameter_cm": trunk_diameter,
            "leaf_chlorophyll_index": chlorophyll,
            "root_zone_area_m2": root_zone,
            "summer_heat_days": heat_days,
            "pest_damage_pct": pest_damage,
            "sidewalk_width_m": sidewalk_width,
            "night_light_lux": night_light,
        }
    )

    order = rng.permutation(N_TOTAL)
    return table.iloc[order].reset_index(drop=True).round(3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--with-test",
        action="store_true",
        help="also write p09_heldout.csv",
    )
    args = parser.parse_args()

    output_dir = Path(__file__).resolve().parent
    table = build_table()
    train = table.iloc[:N_TRAIN]
    heldout = table.iloc[N_TRAIN:].reset_index(drop=True)

    train.to_csv(output_dir / "p09_train.csv", index=False)
    print(f"wrote p09_train.csv: {len(train)} rows, {train.shape[1]} columns")
    print("train outcome counts:", train["outcome"].value_counts().to_dict())

    if args.with_test:
        heldout.to_csv(output_dir / "p09_heldout.csv", index=False)
        print(f"wrote p09_heldout.csv: {len(heldout)} rows")


if __name__ == "__main__":
    main()
