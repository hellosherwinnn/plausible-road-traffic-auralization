from __future__ import annotations

from pathlib import Path

import numpy as np


def crop_around_timestamp(
    input_file: str | Path,
    output_file: str | Path,
    *,
    center_time: float,
    before_samples: int,
    after_samples: int | None = None,
) -> Path:
    """Crop a short audio grain around the frame timestamp."""

    import soundfile as sf

    data, sample_rate = sf.read(input_file)
    after = before_samples if after_samples is None else after_samples
    center = int(center_time * sample_rate)
    start = max(0, center - before_samples)
    end = min(len(data), center + after)
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output, data[start:end], sample_rate)
    return output


def crop_wav_folder_by_timestamps(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    before_samples: int,
    after_samples: int | None = None,
    skip_first: bool = True,
) -> list[Path]:
    """Crop every WAV file around the timestamp encoded in its file name."""

    written: list[Path] = []
    audio_paths = sorted(Path(input_dir).glob("*.wav"))
    for index, audio_path in enumerate(audio_paths):
        if skip_first and index == 0:
            continue
        center_time = parse_timestamp_from_name(audio_path)
        written.append(
            crop_around_timestamp(
                audio_path,
                Path(output_dir) / audio_path.name,
                center_time=center_time,
                before_samples=before_samples,
                after_samples=after_samples,
            )
        )
    return written


def crossfade_segments(
    segments: list[np.ndarray],
    overlap_samples: int,
    *,
    method: str = "sine",
) -> np.ndarray:
    """Concatenate audio grains with linear or sine-power crossfading."""

    if not segments:
        return np.array([], dtype=np.float32)
    if overlap_samples <= 0:
        return np.concatenate(segments)

    output = np.asarray(segments[0], dtype=np.float64)
    for segment in segments[1:]:
        current = np.asarray(segment, dtype=np.float64)
        overlap = min(overlap_samples, len(output), len(current))
        if overlap == 0:
            output = np.concatenate([output, current])
            continue

        fade_out, fade_in = _fade_windows(overlap, method)
        mixed = output[-overlap:] * fade_out + current[:overlap] * fade_in
        output = np.concatenate([output[:-overlap], mixed, current[overlap:]])

    return output.astype(np.float32)


def mix_wav_folder(input_dir: str | Path, output_file: str | Path, *, overlap_samples: int, method: str) -> Path:
    import soundfile as sf

    audio_paths = sorted(Path(input_dir).glob("*.wav"))
    if not audio_paths:
        raise ValueError(f"No wav files found in {input_dir}")

    sample_rate = None
    segments: list[np.ndarray] = []
    for path in audio_paths:
        data, current_rate = sf.read(path)
        sample_rate = current_rate if sample_rate is None else sample_rate
        if current_rate != sample_rate:
            raise ValueError("All input wav files must use the same sample rate")
        segments.append(np.asarray(data))

    mixed = crossfade_segments(segments, overlap_samples, method=method)
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output, mixed, sample_rate)
    return output


def _fade_windows(overlap: int, method: str) -> tuple[np.ndarray, np.ndarray]:
    if method == "linear":
        fade_in = np.linspace(0.0, 1.0, overlap)
    elif method == "sine":
        fade_in = np.sin(np.linspace(0.0, np.pi / 2.0, overlap))
    else:
        raise ValueError("method must be 'linear' or 'sine'")
    return 1.0 - fade_in, fade_in


def parse_timestamp_from_name(path: str | Path) -> float:
    stem = Path(path).stem
    token = stem.split("_")[-1]
    return float(token)
