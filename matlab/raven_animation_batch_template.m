%% RAVEN animation batch template
% The processed CSV files follow the thesis/RAVEN column order:
% time, x, z, -y, view_x, view_z, -view_y, up_x, up_y, up_z, angle, speed.

scriptDir = fileparts(mfilename('fullpath'));
localConfig = fullfile(scriptDir, 'config.local.m');
if exist(localConfig, 'file')
    run(localConfig);
else
    run(fullfile(scriptDir, 'config.example.m'));
end

trajectoryFiles = dir(fullfile(cfg.trajectoryDir, '*.csv'));

for iFile = 1:numel(trajectoryFiles)
    trajectoryPath = fullfile(trajectoryFiles(iFile).folder, trajectoryFiles(iFile).name);
    [~, trajectoryName, ~] = fileparts(trajectoryPath);

    fprintf('Prepare RAVEN animation source for %s\n', trajectoryPath);

    %% Project-specific RAVEN calls go here:
    %% 1. Open or initialize the .rpf model.
    %% 2. Set temperature, humidity, receiver, and source signal.
    %% 3. Assign trajectoryPath as the animation-source CSV.
    %% 4. Render impulse responses and convolve with cfg.tyreSignalFile.
    %% 5. Save full per-vehicle WAV to cfg.audioOutputDir.

    outputWav = fullfile(cfg.audioOutputDir, [trajectoryName '.wav']);
    fprintf('Expected RAVEN output: %s\n', outputWav);
end
