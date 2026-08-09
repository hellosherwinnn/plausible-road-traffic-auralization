%% Pigeon path-list generation batch template
% Reads processed trajectory CSV files and runs one Pigeon path simulation per
% frame. The resulting JSON files can be rendered by pigeon_render_audio_batch.m.

scriptDir = fileparts(mfilename('fullpath'));
localConfig = fullfile(scriptDir, 'config.local.m');
if exist(localConfig, 'file')
    run(localConfig);
else
    run(fullfile(scriptDir, 'config.example.m'));
end

if ~exist(cfg.pigeonJsonDir, 'dir')
    mkdir(cfg.pigeonJsonDir);
end

trajectoryFiles = dir(fullfile(cfg.trajectoryDir, '*.csv'));

for iFile = 1:numel(trajectoryFiles)
    trajectoryPath = fullfile(trajectoryFiles(iFile).folder, trajectoryFiles(iFile).name);
    [~, trajectoryName, ~] = fileparts(trajectoryPath);
    trajectory = readtable(trajectoryPath);
    vehicleOutputDir = fullfile(cfg.pigeonJsonDir, trajectoryName);

    if ~exist(vehicleOutputDir, 'dir')
        mkdir(vehicleOutputDir);
    end

    for iFrame = 1:height(trajectory)
        pgn = itaPigeonProject();
        pgn.config_file_path = fullfile(vehicleOutputDir, 'pigeon_config.ini');
        pgn.geometry_file_path = cfg.geometryFile;
        pgn.material_database = cfg.materialDatabase;
        pgn.directivity_database = cfg.directivityDatabase;
        pgn.MaxDiffractionOrder = cfg.diffractionOrder;
        pgn.MaxReflectionOrder = cfg.reflectionOrder;
        pgn.MaxCombinedOrder = cfg.combinedOrder;
        pgn.FilterNotVisiblePaths = true;
        pgn.export_visualization = false;

        % Column order is: time, x, z, -y, ...
        source = [trajectory{iFrame, 2}, trajectory{iFrame, 3}, trajectory{iFrame, 4}];
        receiver = cfg.receiverPosition;
        pgn.result_file_path = fullfile(vehicleOutputDir, sprintf('%s_%0.3f.json', trajectoryName, trajectory.time(iFrame)));
        pgn.run(source, receiver);
    end
end
