%% Local configuration template
% Copy this file to config.local.m and edit the paths for your machine.
% config.local.m is ignored by git when you add that pattern locally.

cfg = struct();
cfg.geometryFile = fullfile(pwd, 'examples', 'geometry', 'public-placeholder.dae');
cfg.materialDatabase = fullfile(pwd, 'examples', 'materials');
cfg.directivityDatabase = fullfile(pwd, 'examples', 'directivity');
cfg.trajectoryDir = fullfile(pwd, 'outputs', 'trajectories', 'raven_csv');
cfg.pigeonJsonDir = fullfile(pwd, 'outputs', 'pigeon_json');
cfg.audioOutputDir = fullfile(pwd, 'outputs', 'audio');
cfg.tyreSignalFile = fullfile(pwd, 'examples', 'audio', 'tyre_noise_placeholder.wav');
cfg.receiverPosition = [0, 1.7, 0];
cfg.reflectionOrder = 0;
cfg.diffractionOrder = 0;
cfg.combinedOrder = 0;
