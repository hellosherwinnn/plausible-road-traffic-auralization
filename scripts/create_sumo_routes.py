from __future__ import annotations

import argparse
import json
from pathlib import Path

from plausible_traffic_auralization.config import VehicleType
from plausible_traffic_auralization.sumo_routes import (
    generate_departures_from_csv_files,
    generate_random_departures,
    write_route_file,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a SUMO route file from public JSON settings.")
    parser.add_argument("config", type=Path)
    args = parser.parse_args()

    data = json.loads(args.config.read_text(encoding="utf-8"))
    routes = data["routes"]
    output_file = Path(data["output_file"])
    vehicle_types = {
        item["id"]: VehicleType(
            id=item["id"],
            max_speed=float(item["max_speed"]),
            vehicle_class=item.get("vehicle_class", "passenger"),
            color=item.get("color", "1,0,0"),
            extra_attributes=item.get("extra_attributes", {}),
        )
        for item in data["vehicle_types"]
    }

    mode = data.get("mode", "random")
    if mode == "csv":
        csv_settings = data["csv"]
        vehicle_types, vehicles = generate_departures_from_csv_files(
            input_dir=csv_settings["input_dir"],
            route_id=csv_settings.get("route_id", next(iter(routes))),
            depart_lanes=csv_settings.get("depart_lanes"),
            time_column=csv_settings.get("time_column", 0),
            speed_column=csv_settings.get("speed_column", 11),
        )
    elif mode == "random":
        random_settings = data["random"]
        vehicles = generate_random_departures(
            routes=routes,
            vehicle_types=vehicle_types,
            vehicles_per_hour=float(random_settings["vehicles_per_hour"]),
            simulation_duration=float(random_settings["simulation_duration"]),
            depart_lanes=random_settings.get("depart_lanes"),
            speed_range=tuple(random_settings.get("speed_range", [30.0, 50.0])),
            vehicle_probabilities=random_settings.get("vehicle_probabilities"),
            seed=random_settings.get("seed"),
        )
    else:
        raise ValueError("mode must be 'random' or 'csv'")

    written = write_route_file(
        output_file=output_file,
        routes=routes,
        vehicle_types=vehicle_types,
        vehicles=vehicles,
    )
    print(written)


if __name__ == "__main__":
    main()
