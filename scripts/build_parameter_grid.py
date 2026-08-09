from __future__ import annotations

import argparse
from pathlib import Path

from plausible_traffic_auralization.study import (
    crop_samples_per_side,
    crossfade_samples_per_side,
    parameter_grid_dataframe,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the 288-case thesis parameter-study grid.")
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--sample-rate", type=int, default=44100)
    args = parser.parse_args()

    frame = parameter_grid_dataframe()
    frame["crop_samples_per_side"] = [
        crop_samples_per_side(row.update_interval_s, row.overlap_ratio_percent, args.sample_rate)
        for row in frame.itertuples()
    ]
    frame["crossfade_samples_per_side"] = [
        crossfade_samples_per_side(row.update_interval_s, row.overlap_ratio_percent, args.sample_rate)
        for row in frame.itertuples()
    ]
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    print(args.output_csv)


if __name__ == "__main__":
    main()
