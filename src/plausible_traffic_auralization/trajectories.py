from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_trajectory_csv(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"time", "x", "y"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing trajectory columns: {sorted(missing)}")
    if "z" not in frame.columns:
        frame["z"] = 0.0
    return frame.sort_values("time").reset_index(drop=True)


def transform_coordinates(
    frame: pd.DataFrame,
    *,
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    axis_map: tuple[str, str, str] = ("x", "z", "y"),
    invert: tuple[bool, bool, bool] = (False, False, True),
) -> pd.DataFrame:
    """Map SUMO-style coordinates into the acoustic scene coordinate system."""

    output = frame.copy()
    source = {"x": frame["x"], "y": frame["y"], "z": frame["z"]}
    for target, axis, sign, delta in zip(("x", "y", "z"), axis_map, invert, offset):
        values = source[axis].astype(float)
        output[target] = (-values if sign else values) + delta
    return output


def add_view_vectors(frame: pd.DataFrame) -> pd.DataFrame:
    """Add normalized direction vectors based on consecutive trajectory points."""

    output = frame.copy()
    points = output[["x", "y", "z"]].to_numpy(dtype=float)
    deltas = np.gradient(points, axis=0)
    lengths = np.linalg.norm(deltas, axis=1)
    lengths[lengths == 0] = 1.0
    vectors = deltas / lengths[:, None]
    output[["view_x", "view_y", "view_z"]] = vectors
    return output


def add_view_vectors_from_sumo_angle(frame: pd.DataFrame) -> pd.DataFrame:
    """Add thesis-style view vectors from SUMO angles.

    SUMO angles rotate clockwise from the positive y-axis. The thesis workflow
    converts them to RAVEN-friendly view columns:
    `view_x = sin(-angle)`, `view_y = cos(angle)`, `view_z = 0`.
    """

    if "angle" not in frame.columns:
        raise ValueError("angle column is required")
    output = frame.copy()
    angle = np.deg2rad(output["angle"].astype(float))
    output["view_x"] = np.sin(-angle)
    output["view_y"] = np.cos(angle)
    output["view_z"] = 0.0
    return output


def to_raven_columns(frame: pd.DataFrame, *, source_height: float | None = None) -> pd.DataFrame:
    """Convert a trajectory to the RAVEN animation CSV order used in the thesis.

    Output columns:
    time, x, z, -y, view position x, view position z, -view position y,
    up position x, up position y, up position z, angle, speed.
    """

    source = frame.copy()
    for column in ("time", "x", "y"):
        if column not in source.columns:
            raise ValueError(f"{column} column is required")
    if "z" not in source.columns:
        source["z"] = source_height if source_height is not None else 0.0
    elif source_height is not None:
        source["z"] = source_height
    if not {"view_x", "view_y", "view_z"}.issubset(source.columns):
        source = add_view_vectors_from_sumo_angle(source) if "angle" in source.columns else add_view_vectors(source)
    if "angle" not in source.columns:
        source["angle"] = 0.0
    if "speed" not in source.columns:
        source["speed"] = 0.0

    return pd.DataFrame(
        {
            "time": source["time"].astype(float),
            "x": source["x"].astype(float),
            "z": source["z"].astype(float),
            "-y": -source["y"].astype(float),
            "view_x": source["view_x"].astype(float),
            "view_z": source["view_z"].astype(float),
            "-view_y": -source["view_y"].astype(float),
            "up_x": 0.0,
            "up_y": 1.0,
            "up_z": 0.0,
            "angle": source["angle"].astype(float),
            "speed": source["speed"].astype(float),
        }
    )


def interpolate_trajectory(frame: pd.DataFrame, step: float, method: str = "linear") -> pd.DataFrame:
    """Resample a trajectory to a target time step such as 0.01 s or 0.005 s."""

    if step <= 0:
        raise ValueError("step must be positive")
    if method != "linear":
        raise ValueError("The public skeleton currently supports linear interpolation only")

    source = frame.sort_values("time").reset_index(drop=True)
    time = source["time"].to_numpy(dtype=float)
    target_time = np.arange(time[0], time[-1] + step / 2, step)
    result = pd.DataFrame({"time": np.round(target_time - target_time[0], 6)})

    for column in source.columns:
        if column == "time":
            continue
        if pd.api.types.is_numeric_dtype(source[column]):
            result[column] = np.interp(target_time, time, source[column])

    return result


def write_per_vehicle_csvs(frame: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    """Split a trajectory table by vehicle_id and reset each start time to zero."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    if "vehicle_id" not in frame.columns:
        path = output / "trajectory.csv"
        reset_start_time(frame).to_csv(path, index=False)
        return [path]

    for vehicle_id, group in frame.groupby("vehicle_id", sort=True):
        vehicle_frame = reset_start_time(group.sort_values("time"))
        path = output / f"{_safe_name(str(vehicle_id))}.csv"
        vehicle_frame.to_csv(path, index=False)
        written.append(path)
    return written


def reset_start_time(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy().reset_index(drop=True)
    output["time"] = output["time"] - output["time"].iloc[0]
    return output


def extract_velocity_table(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"time", "speed"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing velocity columns: {sorted(missing)}")
    columns = ["vehicle_id", "time", "speed"] if "vehicle_id" in frame.columns else ["time", "speed"]
    return frame.loc[:, columns].copy()


def extract_start_times(frame: pd.DataFrame) -> pd.DataFrame:
    if "vehicle_id" not in frame.columns:
        return pd.DataFrame({"vehicle_id": ["trajectory"], "start_time": [float(frame["time"].iloc[0])]})
    rows = []
    for vehicle_id, group in frame.groupby("vehicle_id", sort=True):
        rows.append({"vehicle_id": vehicle_id, "start_time": float(group.sort_values("time")["time"].iloc[0])})
    return pd.DataFrame(rows)


def process_trajectory_file(
    input_csv: str | Path,
    output_csv: str | Path,
    *,
    interpolation_step: float | None = None,
    source_height: float | None = None,
    raven_order: bool = True,
) -> Path:
    frame = load_trajectory_csv(input_csv)
    frame = add_view_vectors_from_sumo_angle(frame) if "angle" in frame.columns else add_view_vectors(frame)
    frame = reset_start_time(frame)
    if interpolation_step is not None:
        frame = interpolate_trajectory(frame, interpolation_step)
    if raven_order:
        frame = to_raven_columns(frame, source_height=source_height)
    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    return output


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
