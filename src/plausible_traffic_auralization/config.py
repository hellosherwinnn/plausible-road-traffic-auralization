from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass(slots=True)
class PathConfig:
    """Centralized paths used by the batch workflow."""

    project_root: Path
    sumo_config: Path | None = None
    fcd_xml: Path | None = None
    measured_trajectory_dir: Path | None = None
    trajectory_output_dir: Path = Path("outputs/trajectories")
    pigeon_output_dir: Path = Path("outputs/pigeon")
    audio_output_dir: Path = Path("outputs/audio")
    geometry_file: Path | None = None
    pigeon_executable: Path | None = None
    raven_project_dir: Path | None = None

    @classmethod
    def from_json(cls, path: str | Path) -> "PathConfig":
        config_path = Path(path).expanduser().resolve()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        root = Path(data.get("project_root", config_path.parent)).expanduser().resolve()

        def resolve_optional(key: str) -> Path | None:
            value = data.get(key)
            if value in (None, ""):
                return None
            return _resolve(root, value)

        return cls(
            project_root=root,
            sumo_config=resolve_optional("sumo_config"),
            fcd_xml=resolve_optional("fcd_xml"),
            measured_trajectory_dir=resolve_optional("measured_trajectory_dir"),
            trajectory_output_dir=_resolve(root, data.get("trajectory_output_dir", "outputs/trajectories")),
            pigeon_output_dir=_resolve(root, data.get("pigeon_output_dir", "outputs/pigeon")),
            audio_output_dir=_resolve(root, data.get("audio_output_dir", "outputs/audio")),
            geometry_file=resolve_optional("geometry_file"),
            pigeon_executable=resolve_optional("pigeon_executable"),
            raven_project_dir=resolve_optional("raven_project_dir"),
        )


@dataclass(slots=True)
class VehicleType:
    id: str
    max_speed: float
    vehicle_class: str = "passenger"
    color: str = "1,0,0"
    extra_attributes: dict[str, str] = field(default_factory=dict)


def ensure_directories(config: PathConfig) -> None:
    for path in (
        config.trajectory_output_dir,
        config.pigeon_output_dir,
        config.audio_output_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path
