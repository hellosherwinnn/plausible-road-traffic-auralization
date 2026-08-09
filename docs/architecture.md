# Architecture

This repository is a public skeleton of a road-traffic auralization workflow. It keeps the reusable processing logic while excluding private thesis material, raw measurements, generated audio, large 3D assets, and third-party binaries.

```text
SUMO / measured CSV
        |
        v
FCD extraction and trajectory cleaning
        |
        v
Coordinate transform, view vectors, interpolation
        |
        v
Per-vehicle CSVs and per-frame acoustic inputs
        |
        +--> RAVEN workflow
        |
        +--> Pigeon config / JSON generation
        |
        v
Audio cropping, crossfading, and multi-vehicle synthesis
```

## Modules

- `config.py` centralizes paths so local absolute paths stay outside version control.
- `sumo_routes.py` creates SUMO route files from random traffic settings or measured trajectory CSV files.
- `fcd.py` streams SUMO Floating Car Data XML with `lxml.etree.iterparse`.
- `trajectories.py` cleans, transforms, interpolates, splits vehicle trajectories, writes the RAVEN column order, and exports velocity/start-time tables.
- `pigeon.py` writes frame-wise Pigeon configuration files and can run a local Pigeon binary when configured.
- `raven.py` writes a MATLAB batch-template wrapper for RAVEN animation trajectories.
- `study.py` encodes the 288-case parameter grid and crop/crossfade sample-count formulas from the thesis.
- `audio.py` crops frame-centered audio grains and combines them with linear or sine crossfading.
- `batch.py` connects the processing stages into a one-command workflow.

## Script Templates

- `scripts/create_sumo_routes.py` turns `configs/example_routes.json` into a `.rou.xml` file with route selection, vehicle type probabilities, traffic flow, randomized departures, and vehicle properties.
- `scripts/process_fcd.py` extracts FCD XML into per-vehicle CSVs, RAVEN CSVs, velocity tables, and `start_times.csv`.
- `scripts/build_parameter_grid.py` writes the speed/update/overlap/crossfade grid used for batch experiments.
- `matlab/pigeon_generate_pathlist_batch.m` loops through processed trajectories and writes Pigeon JSON path files.
- `matlab/pigeon_render_audio_batch.m` renders those JSON files to audio grains with ITA Toolbox.
- `matlab/raven_animation_batch_template.m` documents the RAVEN animation loop points without redistributing project-specific RAVEN code.
- `scripts/reaper_crossfade.lua` arranges one audio grain per track with configurable overlap.

## External Tools

The original research workflow used SUMO, RAVEN, Pigeon, Blender, SketchUp, MATLAB/ITA Toolbox, Python, and REAPER Lua scripts. This public repository does not redistribute those tools or any project-specific binaries.
