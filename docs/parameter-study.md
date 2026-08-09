# Parameter Study

The thesis evaluated a 288-case parameter study:

- 4 vehicle speeds: 30, 60, 90, and 120 km/h
- 6 update intervals: 1, 0.5, 0.1, 0.05, 0.01, and 0.005 seconds
- 6 overlap ratios: 5, 10, 20, 30, 40, and 50 percent
- 2 crossfading methods: linear and sine

The study combined SPL-derivative analysis with listening tests. The goal was to find settings that reduce audible discontinuities while keeping the batch simulation workload practical.

The code exposes the parameter grid and sample-count formulas in `plausible_traffic_auralization.study`:

- `generate_parameter_grid()` returns 288 cases.
- `crop_samples_per_side(update_interval_s, overlap_ratio_percent)` reproduces the one-side crop counts from Table 4.1.
- `crossfade_samples_per_side(update_interval_s, overlap_ratio_percent)` reproduces the one-side crossfade counts from Table 4.2.

The SPL-derivative top-10 analysis is intentionally documented rather than implemented in this public repository. It was used as an evaluation method alongside listening tests, not as a required pipeline step.

## Reproducing the Grid

The public skeleton provides the processing building blocks but not the thesis audio, listener responses, or generated results. To reproduce a comparable grid:

1. Generate or import vehicle trajectories for each speed.
2. Resample trajectories to the chosen update interval.
3. Create frame-wise RAVEN or Pigeon simulation inputs.
4. Render audio grains with the acoustic engine.
5. Crop grains around each frame timestamp.
6. Crossfade grains using the chosen overlap ratio and method.
7. Analyze the stitched output with an SPL-derivative or psychoacoustic analysis tool.

The REAPER helper in `scripts/reaper_crossfade.lua` can also be used when arranging one rendered grain per track.
