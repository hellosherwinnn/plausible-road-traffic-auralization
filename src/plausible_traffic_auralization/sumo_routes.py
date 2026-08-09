from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import xml.etree.ElementTree as ET
from collections.abc import Mapping

import numpy as np
import pandas as pd

from .config import VehicleType


@dataclass(slots=True)
class VehicleDeparture:
    id: str
    type: str
    route: str
    depart: float
    depart_lane: str = "best"
    depart_pos: str = "0"
    depart_speed: float = 0.0


def generate_random_departures(
    *,
    routes: dict[str, str],
    vehicle_types: dict[str, VehicleType],
    vehicles_per_hour: float,
    simulation_duration: float,
    depart_lanes: list[str] | None = None,
    speed_range: tuple[float, float] = (30.0, 50.0),
    vehicle_probabilities: Mapping[str, float] | None = None,
    seed: int | None = None,
) -> list[VehicleDeparture]:
    """Create randomized SUMO vehicle departures for a route file."""

    rng = random.Random(seed)
    route_ids = list(routes)
    type_ids = list(vehicle_types)
    weights = [vehicle_probabilities.get(type_id, 0.0) for type_id in type_ids] if vehicle_probabilities else None
    if weights and sum(weights) <= 0:
        raise ValueError("vehicle_probabilities must contain at least one positive weight")
    lanes = depart_lanes or ["best"]
    total = int(vehicles_per_hour * simulation_duration / 3600)
    departures: list[VehicleDeparture] = []

    for index in range(total):
        chosen_type = rng.choices(type_ids, weights=weights, k=1)[0] if weights else rng.choice(type_ids)
        vehicle_type = vehicle_types[chosen_type]
        speed = min(rng.uniform(*speed_range), vehicle_type.max_speed)
        departures.append(
            VehicleDeparture(
                id=f"{vehicle_type.id}.{index}",
                type=vehicle_type.id,
                route=rng.choice(route_ids),
                depart=rng.uniform(0, simulation_duration),
                depart_lane=rng.choice(lanes),
                depart_speed=speed,
            )
        )

    return sorted(departures, key=lambda vehicle: vehicle.depart)


def generate_departures_from_csv_files(
    *,
    input_dir: str | Path,
    route_id: str,
    depart_lanes: list[str] | None = None,
    time_column: int | str = 0,
    speed_column: int | str = 11,
) -> tuple[dict[str, VehicleType], list[VehicleDeparture]]:
    """Build SUMO vehicle definitions from measured trajectory CSV files."""

    lanes = depart_lanes or ["best"]
    vehicle_types: dict[str, VehicleType] = {}
    vehicles: list[VehicleDeparture] = []

    for index, csv_path in enumerate(sorted(Path(input_dir).glob("*.csv"))):
        frame = pd.read_csv(csv_path, header=None)
        if frame.empty:
            continue

        vehicle_type = csv_path.stem.split(".")[0]
        speeds = pd.to_numeric(frame[speed_column], errors="coerce")
        max_speed = float(np.nanmax(speeds.to_numpy()))
        if vehicle_type not in vehicle_types:
            vehicle_types[vehicle_type] = VehicleType(id=vehicle_type, max_speed=round(max_speed, 2))

        depart_time = float(frame.iloc[0][time_column])
        depart_speed = min(float(frame.iloc[0][speed_column]), vehicle_types[vehicle_type].max_speed)
        vehicles.append(
            VehicleDeparture(
                id=f"{vehicle_type}.{len(vehicles)}",
                type=vehicle_type,
                route=route_id,
                depart=depart_time,
                depart_lane=lanes[index % len(lanes)],
                depart_speed=depart_speed,
            )
        )

    return vehicle_types, sorted(vehicles, key=lambda vehicle: vehicle.depart)


def write_route_file(
    *,
    output_file: str | Path,
    routes: dict[str, str],
    vehicle_types: dict[str, VehicleType],
    vehicles: list[VehicleDeparture],
) -> Path:
    """Write a SUMO `.rou.xml` file."""

    root = ET.Element(
        "routes",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/routes_file.xsd",
        },
    )

    for vehicle_type in vehicle_types.values():
        attributes = {
            "id": vehicle_type.id,
            "maxSpeed": f"{vehicle_type.max_speed:.2f}",
            "vClass": vehicle_type.vehicle_class,
            "color": vehicle_type.color,
        }
        attributes.update(vehicle_type.extra_attributes)
        ET.SubElement(root, "vType", attributes)

    for route_id, edges in routes.items():
        ET.SubElement(root, "route", {"id": route_id, "edges": edges})

    for vehicle in vehicles:
        ET.SubElement(
            root,
            "vehicle",
            {
                "id": vehicle.id,
                "type": vehicle.type,
                "route": vehicle.route,
                "depart": f"{vehicle.depart:.2f}",
                "departLane": vehicle.depart_lane,
                "departPos": vehicle.depart_pos,
                "departSpeed": f"{vehicle.depart_speed:.2f}",
            },
        )

    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    return output
