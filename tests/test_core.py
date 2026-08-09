from pathlib import Path

import numpy as np
import pandas as pd

from plausible_traffic_auralization.audio import crossfade_segments
from plausible_traffic_auralization.fcd import split_fcd_by_vehicle
from plausible_traffic_auralization.study import (
    crop_samples_per_side,
    crossfade_samples_per_side,
    generate_parameter_grid,
)
from plausible_traffic_auralization.trajectories import (
    extract_start_times,
    extract_velocity_table,
    interpolate_trajectory,
    reset_start_time,
    to_raven_columns,
)


def test_split_fcd_by_vehicle(tmp_path: Path) -> None:
    xml = tmp_path / "sample_fcd.xml"
    xml.write_text(
        """<fcd-export>
        <timestep time="1.0"><vehicle id="car.0" x="0" y="0" angle="0" speed="1"/></timestep>
        <timestep time="1.1"><vehicle id="car.0" x="1" y="0" angle="0" speed="1"/></timestep>
        </fcd-export>""",
        encoding="utf-8",
    )
    written = split_fcd_by_vehicle(xml, tmp_path / "out")
    assert len(written) == 1
    frame = pd.read_csv(written[0])
    assert frame["time"].tolist() == [0.0, 0.1]


def test_interpolate_trajectory() -> None:
    frame = pd.DataFrame({"time": [0.0, 0.1], "x": [0.0, 1.0], "y": [0.0, 0.0], "z": [0.0, 0.0]})
    result = interpolate_trajectory(frame, 0.05)
    assert result["time"].tolist() == [0.0, 0.05, 0.1]
    assert result["x"].tolist() == [0.0, 0.5, 1.0]


def test_reset_start_time() -> None:
    frame = pd.DataFrame({"time": [3.0, 3.5], "x": [0.0, 1.0]})
    assert reset_start_time(frame)["time"].tolist() == [0.0, 0.5]


def test_crossfade_segments() -> None:
    left = np.ones(4)
    right = np.zeros(4)
    mixed = crossfade_segments([left, right], 2, method="linear")
    assert len(mixed) == 6
    assert mixed[0] == 1
    assert mixed[-1] == 0


def test_raven_column_order_from_sumo_angle() -> None:
    frame = pd.DataFrame({"time": [0.0], "x": [1.0], "y": [2.0], "z": [0.3], "angle": [90.0], "speed": [4.0]})
    raven = to_raven_columns(frame)
    assert raven.columns.tolist() == ["time", "x", "z", "-y", "view_x", "view_z", "-view_y", "up_x", "up_y", "up_z", "angle", "speed"]
    assert raven.loc[0, "-y"] == -2.0
    assert round(raven.loc[0, "view_x"], 6) == -1.0


def test_velocity_and_start_time_extraction() -> None:
    frame = pd.DataFrame({"vehicle_id": ["b", "a", "a"], "time": [3.0, 1.0, 1.5], "speed": [5.0, 2.0, 2.5]})
    velocity = extract_velocity_table(frame)
    assert velocity.columns.tolist() == ["vehicle_id", "time", "speed"]
    starts = extract_start_times(frame)
    assert starts.to_dict("records") == [{"vehicle_id": "a", "start_time": 1.0}, {"vehicle_id": "b", "start_time": 3.0}]


def test_parameter_study_grid_and_sample_formulas() -> None:
    assert len(generate_parameter_grid()) == 288
    assert crop_samples_per_side(0.005, 5) == 121
    assert crossfade_samples_per_side(0.005, 5) == 22
