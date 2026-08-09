from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

import pandas as pd


DEFAULT_SPEEDS_KMH = (30, 60, 90, 120)
DEFAULT_UPDATE_INTERVALS = (1.0, 0.5, 0.1, 0.05, 0.01, 0.005)
DEFAULT_OVERLAP_RATIOS = (5, 10, 20, 30, 40, 50)
DEFAULT_CROSSFADE_METHODS = ("sine", "linear")


@dataclass(frozen=True, slots=True)
class ParameterCase:
    speed_kmh: int
    update_interval_s: float
    overlap_ratio_percent: int
    crossfade_method: str

    @property
    def speed_mps(self) -> float:
        return self.speed_kmh / 3.6

    @property
    def label(self) -> str:
        interval = str(self.update_interval_s).replace(".", "")
        return f"{self.speed_kmh}kmh_{interval}s_{self.overlap_ratio_percent}pct_{self.crossfade_method}"


def generate_parameter_grid(
    speeds_kmh=DEFAULT_SPEEDS_KMH,
    update_intervals=DEFAULT_UPDATE_INTERVALS,
    overlap_ratios=DEFAULT_OVERLAP_RATIOS,
    crossfade_methods=DEFAULT_CROSSFADE_METHODS,
) -> list[ParameterCase]:
    return [
        ParameterCase(int(speed), float(interval), int(overlap), str(method))
        for speed, interval, overlap, method in product(
            speeds_kmh, update_intervals, overlap_ratios, crossfade_methods
        )
    ]


def parameter_grid_dataframe() -> pd.DataFrame:
    return pd.DataFrame([asdict(case) | {"label": case.label, "speed_mps": case.speed_mps} for case in generate_parameter_grid()])


def write_parameter_grid(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    parameter_grid_dataframe().to_csv(output, index=False)
    return output


def step_samples(update_interval_s: float, sample_rate: int = 44100) -> int:
    return int(round(update_interval_s * sample_rate))


def crossfade_samples_per_side(update_interval_s: float, overlap_ratio_percent: float, sample_rate: int = 44100) -> int:
    """Table 4.2 formula: one-side crossfade samples = step_samples * 2 * overlap."""

    return int(round(step_samples(update_interval_s, sample_rate) * (2.0 * overlap_ratio_percent / 100.0)))


def crop_samples_per_side(update_interval_s: float, overlap_ratio_percent: float, sample_rate: int = 44100) -> int:
    """Table 4.1 formula: one-side crop samples = step_samples * (0.5 + overlap)."""

    return int(round(step_samples(update_interval_s, sample_rate) * (0.5 + overlap_ratio_percent / 100.0)))
