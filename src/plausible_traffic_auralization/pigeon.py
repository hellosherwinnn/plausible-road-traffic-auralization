from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import configparser
import math
import subprocess

import pandas as pd


@dataclass(slots=True)
class PigeonProject:
    pigeon_executable: Path
    geometry_file: Path
    working_dir: Path
    reflection_order: int = 0
    diffraction_order: int = 0
    combined_order: int = 0
    material_database: Path = Path(".")
    directivity_database: Path = Path(".")
    export_visualization: bool = True

    def create_config(
        self,
        *,
        source: tuple[float, float, float],
        receiver: tuple[float, float, float],
        source_rotation: tuple[float, float, float, float] = (0, 0, 0, 1),
        receiver_rotation: tuple[float, float, float, float] = (0, 0, 0, 1),
        result_file: Path = Path("pigeon_result.json"),
    ) -> Path:
        self.working_dir.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()

        config["pigeon:scene"] = {
            "GeometryFilePath": str(self.geometry_file),
            "OutputFilePath": str(self.working_dir / result_file),
            "MaterialDatabase": str(self.material_database),
            "DirectivityDatabase": str(self.directivity_database),
        }
        config["pigeon:scene:emitters"] = {
            "Emitter1": ",".join(map(str, ("E1", *source, *source_rotation, "directivity")))
        }
        config["pigeon:scene:sensors"] = {
            "Sensor1": ",".join(map(str, ("S1", *receiver, *receiver_rotation, "directivity")))
        }
        config["pigeon:config"] = {
            "MaxDiffractionOrder": str(self.diffraction_order),
            "MaxReflectionOrder": str(self.reflection_order),
            "MaxCombinedOrder": str(self.combined_order),
            "ExportVisualization": str(self.export_visualization),
            "FilterNotVisiblePaths": "True",
        }
        config["pigeon:visualization"] = {
            "VisualizationFilePath": str(self.working_dir / "visualization.dae"),
            "VisualizationFileFormat": "collada",
        }

        config_file = self.working_dir / "pigeon_config.ini"
        with config_file.open("w", encoding="utf-8") as stream:
            config.write(stream)
        return config_file

    def run_frame(
        self,
        *,
        source: tuple[float, float, float],
        receiver: tuple[float, float, float],
        source_rotation: tuple[float, float, float, float] = (0, 0, 0, 1),
        receiver_rotation: tuple[float, float, float, float] = (0, 0, 0, 1),
        result_file: Path = Path("pigeon_result.json"),
    ) -> Path:
        config_file = self.create_config(
            source=source,
            receiver=receiver,
            source_rotation=source_rotation,
            receiver_rotation=receiver_rotation,
            result_file=result_file,
        )
        subprocess.run([str(self.pigeon_executable), str(config_file)], check=True, cwd=self.working_dir)
        return self.working_dir / result_file


def yaw_to_quaternion(yaw_degrees: float, *, clockwise: bool = True) -> tuple[float, float, float, float]:
    """Return an x,y,z,w quaternion for Pigeon dynamic simulations."""

    yaw = -yaw_degrees if clockwise else yaw_degrees
    half_angle = math.radians(yaw) / 2.0
    return (0.0, 0.0, math.sin(half_angle), math.cos(half_angle))


def write_pigeon_frame_configs(
    *,
    trajectory_csv: str | Path,
    output_dir: str | Path,
    geometry_file: str | Path,
    receiver: tuple[float, float, float],
    reflection_order: int = 0,
    diffraction_order: int = 0,
    combined_order: int = 0,
) -> list[Path]:
    """Create one Pigeon `.ini` per trajectory frame without running the binary."""

    frame = pd.read_csv(trajectory_csv)
    output = Path(output_dir)
    project = PigeonProject(
        pigeon_executable=Path("pigeon"),
        geometry_file=Path(geometry_file),
        working_dir=output,
        reflection_order=reflection_order,
        diffraction_order=diffraction_order,
        combined_order=combined_order,
    )
    config_files: list[Path] = []

    for _, row in frame.iterrows():
        timestamp = float(row["time"])
        source = (float(row["x"]), float(row["y"]), float(row["z"]))
        source_rotation = yaw_to_quaternion(float(row.get("angle", 0.0)))
        result_file = Path(f"{Path(trajectory_csv).stem}_{timestamp:.3f}.json")
        config_file = project.create_config(
            source=source,
            receiver=receiver,
            source_rotation=source_rotation,
            result_file=result_file,
        )
        frame_config = output / f"{Path(trajectory_csv).stem}_{timestamp:.3f}.ini"
        config_file.replace(frame_config)
        config_files.append(frame_config)

    return config_files
