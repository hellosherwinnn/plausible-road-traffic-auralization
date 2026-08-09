from __future__ import annotations

from pathlib import Path
import argparse

from .config import PathConfig, ensure_directories
from .fcd import split_fcd_by_vehicle
from .pigeon import write_pigeon_frame_configs
from .trajectories import add_view_vectors, interpolate_trajectory, load_trajectory_csv, transform_coordinates


def run_pipeline(config_path: str | Path, *, interpolation_step: float = 0.01) -> None:
    """Run the public skeleton workflow up to acoustic-tool input generation."""

    config = PathConfig.from_json(config_path)
    ensure_directories(config)

    trajectory_files: list[Path] = []
    if config.fcd_xml:
        trajectory_files.extend(split_fcd_by_vehicle(config.fcd_xml, config.trajectory_output_dir / "from_fcd"))

    if config.measured_trajectory_dir:
        for csv_path in sorted(config.measured_trajectory_dir.glob("*.csv")):
            frame = load_trajectory_csv(csv_path)
            frame = transform_coordinates(frame)
            frame = add_view_vectors(frame)
            frame = interpolate_trajectory(frame, interpolation_step)
            output = config.trajectory_output_dir / "processed" / csv_path.name
            output.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(output, index=False)
            trajectory_files.append(output)

    if config.geometry_file:
        for trajectory in trajectory_files:
            write_pigeon_frame_configs(
                trajectory_csv=trajectory,
                output_dir=config.pigeon_output_dir / trajectory.stem,
                geometry_file=config.geometry_file,
                receiver=(0.0, 1.7, 0.0),
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate anonymized traffic-auralization inputs.")
    parser.add_argument("config", type=Path, help="Path to a pipeline JSON config.")
    parser.add_argument("--interpolation-step", type=float, default=0.01)
    args = parser.parse_args()
    run_pipeline(args.config, interpolation_step=args.interpolation_step)


if __name__ == "__main__":
    main()
