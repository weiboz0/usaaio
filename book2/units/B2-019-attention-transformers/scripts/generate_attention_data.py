"""Generate the deterministic numeric probes used by B2-019."""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import numpy as np

SEED = 20260808


def arrays() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(SEED)
    return {
        "q": rng.normal(size=(2, 3, 4)).astype(np.float64),
        "k": rng.normal(size=(2, 5, 4)).astype(np.float64),
        "v": rng.normal(size=(2, 5, 6)).astype(np.float64),
        "one_hot": np.eye(4, dtype=np.float64)[[0, 1, 2, 1, 3, 0]],
    }


def write_deterministic_npz(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, value in sorted(arrays().items()):
            buffer = io.BytesIO()
            np.lib.format.write_array(buffer, value, allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o600 << 16
            archive.writestr(info, buffer.getvalue())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_deterministic_npz(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
