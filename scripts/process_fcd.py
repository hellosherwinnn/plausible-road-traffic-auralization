from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from plausible_traffic_auralization.fcd import fcd_to_dataframe, split_fcd_by_vehicle
from plausible_traffic_auralization.trajectories import (
    extract_start_times,
    extract_velocity_table,
    process_trajectory_file,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and process SUMO FCD trajectories.")
    parser.add_argument("fcd_xml", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--interpolation-step", type=float, default=None)
    parser.add_argument("--source-height", type=float, default=None)
    args = parser.parse_args()

    raw_dir = args.output_dir / "raw_by_vehicle"
    processed_dir = args.output_dir / "raven_csv"
    velocity_dir = args.output_dir / "velocity"
    raw_files = split_fcd_by_vehicle(args.fcd_xml, raw_dir)

    all_frames = []
    for raw_file in raw_files:
        processed = process_trajectory_file(
            raw_file,
            processed_dir / raw_file.name,
            interpolation_step=args.interpolation_step,
            source_height=args.source_height,
            raven_order=True,
        )
        raw_frame = pd.read_csv(raw_file)
        raw_frame["vehicle_id"] = raw_file.stem
        all_frames.append(raw_frame)
        velocity_dir.mkdir(parents=True, exist_ok=True)
        extract_velocity_table(raw_frame).to_csv(velocity_dir / raw_file.name, index=False)
        print(processed)

    if all_frames:
        starts = extract_start_times(pd.concat(all_frames, ignore_index=True))
        starts.to_csv(args.output_dir / "start_times.csv", index=False)


if __name__ == "__main__":
    main()
