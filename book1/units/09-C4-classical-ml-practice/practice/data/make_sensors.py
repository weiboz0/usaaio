"""Seeded generator for sensors.csv (source of truth for the committed CSV).

Machine-health readings with features on wildly different scales:
temperature and vibration carry the ok/faulty signal on small scales,
while pressure sits near 101000 Pa with large but UNINFORMATIVE spread —
raw Euclidean distances are dominated by the feature that matters least.
That distortion is the point of the problems built on this file.
Regenerate with:

    python make_sensors.py

The committed sensors.csv is a convenience artifact of exactly this script;
any edit to the script must be followed by regeneration.
"""

import numpy as np
import pandas as pd

SEED = 20260804
N_OK = 36
N_FAULTY = 24


def main() -> None:
    rng = np.random.default_rng(SEED)
    ok = np.column_stack(
        [
            rng.normal(65.0, 1.8, N_OK),       # temp_c
            rng.normal(3.0, 0.7, N_OK),        # vibration_mm_s
            rng.normal(101000.0, 1400.0, N_OK),  # pressure_pa (no class signal)
        ]
    )
    faulty = np.column_stack(
        [
            rng.normal(68.2, 1.8, N_FAULTY),
            rng.normal(4.6, 0.7, N_FAULTY),
            rng.normal(101000.0, 1400.0, N_FAULTY),
        ]
    )
    sensors = pd.DataFrame(
        np.vstack([ok, faulty]), columns=["temp_c", "vibration_mm_s", "pressure_pa"]
    )
    sensors.insert(0, "status", ["ok"] * N_OK + ["faulty"] * N_FAULTY)
    order = rng.permutation(len(sensors))
    sensors = sensors.iloc[order].reset_index(drop=True)
    sensors = sensors.round({"temp_c": 2, "vibration_mm_s": 2, "pressure_pa": 1})
    sensors.to_csv("sensors.csv", index=False)
    print(f"wrote sensors.csv: {sensors.shape[0]} rows, {sensors.shape[1]} columns")


if __name__ == "__main__":
    main()
