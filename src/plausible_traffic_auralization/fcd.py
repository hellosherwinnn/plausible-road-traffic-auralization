from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from lxml import etree
import pandas as pd


@dataclass(slots=True)
class FcdRecord:
    time: float
    vehicle_id: str
    x: float
    y: float
    z: float
    angle: float
    speed: float
    lane: str | None = None


def iter_fcd_records(xml_file: str | Path):
    """Stream SUMO floating car data without loading the full XML tree."""

    context = etree.iterparse(str(xml_file), events=("end",), tag="timestep")
    for _, timestep in context:
        time_value = float(timestep.get("time", "0"))
        for vehicle in timestep.iterfind("vehicle"):
            yield FcdRecord(
                time=time_value,
                vehicle_id=vehicle.get("id", ""),
                x=float(vehicle.get("x", "0")),
                y=float(vehicle.get("y", "0")),
                z=float(vehicle.get("z", "0")),
                angle=float(vehicle.get("angle", "0")),
                speed=float(vehicle.get("speed", "0")),
                lane=vehicle.get("lane"),
            )
        timestep.clear()


def fcd_to_dataframe(xml_file: str | Path) -> pd.DataFrame:
    records = [asdict(record) for record in iter_fcd_records(xml_file)]
    return pd.DataFrame.from_records(records)


def split_fcd_by_vehicle(xml_file: str | Path, output_dir: str | Path) -> list[Path]:
    """Write one CSV trajectory per vehicle from a SUMO FCD XML file."""

    frame = fcd_to_dataframe(xml_file)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    if frame.empty:
        return written

    for vehicle_id, group in frame.groupby("vehicle_id", sort=True):
        vehicle_frame = group.sort_values("time").reset_index(drop=True)
        vehicle_frame["time"] = vehicle_frame["time"] - vehicle_frame["time"].iloc[0]
        path = output / f"{_safe_name(vehicle_id)}.csv"
        vehicle_frame.to_csv(path, index=False)
        written.append(path)

    return written


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
