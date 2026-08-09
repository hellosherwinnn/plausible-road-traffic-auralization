from __future__ import annotations

from pathlib import Path


def write_raven_animation_batch_script(
    *,
    trajectory_dir: str | Path,
    output_script: str | Path,
    raven_project_file: str = "scene.rpf",
    tyre_signal_file: str = "tyre_noise.wav",
    output_dir: str = "outputs/raven",
) -> Path:
    """Write a MATLAB template that loops over RAVEN animation CSV files."""

    script = f"""%% Auto-generated RAVEN animation batch template
% This template intentionally uses relative paths. Configure the paths below
% for your local RAVEN/MATLAB environment before running.

trajectoryDir = '{Path(trajectory_dir).as_posix()}';
ravenProjectFile = '{raven_project_file}';
tyreSignalFile = '{tyre_signal_file}';
outputDir = '{output_dir}';

if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end

trajectoryFiles = dir(fullfile(trajectoryDir, '*.csv'));

for iFile = 1:numel(trajectoryFiles)
    trajectoryPath = fullfile(trajectoryFiles(iFile).folder, trajectoryFiles(iFile).name);
    [~, trajectoryName, ~] = fileparts(trajectoryPath);

    %% Project-specific RAVEN calls go here. The thesis workflow used a loop
    %% around RAVEN's animation source script so every vehicle trajectory is
    %% rendered independently before later multi-vehicle synthesis.
    fprintf('Render RAVEN animation for %s using %s\\n', trajectoryPath, ravenProjectFile);

    outputWav = fullfile(outputDir, [trajectoryName '.wav']);
    fprintf('Expected output: %s with source signal %s\\n', outputWav, tyreSignalFile);
end
"""
    output = Path(output_script)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(script, encoding="utf-8")
    return output
