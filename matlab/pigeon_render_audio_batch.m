%% Pigeon/ITA audio rendering batch template
% Converts frame-wise Pigeon JSON paths into WAV grains using ITA Toolbox.
% Crossfading is intentionally handled by Python or REAPER after cropping.

scriptDir = fileparts(mfilename('fullpath'));
localConfig = fullfile(scriptDir, 'config.local.m');
if exist(localConfig, 'file')
    run(localConfig);
else
    run(fullfile(scriptDir, 'config.example.m'));
end

if ~exist(cfg.audioOutputDir, 'dir')
    mkdir(cfg.audioOutputDir);
end

carSound = ita_read(cfg.tyreSignalFile);
geoPropSim = itaGeoPropagation();
geoPropSim.load_material_database(cfg.materialDatabase);

vehicleDirs = dir(cfg.pigeonJsonDir);
vehicleDirs = vehicleDirs([vehicleDirs.isdir]);

for iDir = 1:numel(vehicleDirs)
    name = vehicleDirs(iDir).name;
    if startsWith(name, '.')
        continue;
    end

    jsonDir = fullfile(vehicleDirs(iDir).folder, name);
    audioDir = fullfile(cfg.audioOutputDir, name);
    if ~exist(audioDir, 'dir')
        mkdir(audioDir);
    end

    jsonFiles = dir(fullfile(jsonDir, '*.json'));
    for iFile = 1:numel(jsonFiles)
        if strcmp(jsonFiles(iFile).name, 'pigeon_config_stats.json')
            continue;
        end

        jsonPath = fullfile(jsonFiles(iFile).folder, jsonFiles(iFile).name);
        geoPropSim.load_paths(jsonPath);

        impulseResponse = itaAudio();
        impulseResponse.freqData = geoPropSim.run();
        impulseResponse.signalType = 'energy';

        rendered = ita_convolve(impulseResponse, carSound);
        rendered.channelUnits = 'Pa';

        [~, grainName, ~] = fileparts(jsonPath);
        ita_write(rendered, fullfile(audioDir, [grainName '.wav']), 'overwrite');
    end
end
