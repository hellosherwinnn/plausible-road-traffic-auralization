-- Arrange one audio item per track with configurable overlap.
-- The defaults match a 0.005 s update interval with 50 percent overlap at 44.1 kHz.
-- Override with REAPER project ext-state keys:
--   ptra_sample_rate, ptra_grain_front, ptra_grain_back, ptra_overlap
local function ext_number(key, fallback)
  local ok, value = reaper.GetProjExtState(0, "ptra", key)
  if ok == 1 and tonumber(value) ~= nil then
    return tonumber(value)
  end
  return fallback
end

local sample_rate = ext_number("sample_rate", 44100)
local grain_samples_front = ext_number("grain_front", 220)
local grain_samples_back = ext_number("grain_back", 220)
local overlap_samples = ext_number("overlap", 220)

local project = reaper.EnumProjects(-1)
local track_count = reaper.CountTracks(project)
local grain_samples_total = grain_samples_front + grain_samples_back
local crossfade_length = overlap_samples / sample_rate
local step_size = (grain_samples_total - overlap_samples) / sample_rate

for track_index = 0, track_count - 1 do
  local track = reaper.GetTrack(project, track_index)
  local item_count = reaper.CountTrackMediaItems(track)

  if item_count > 0 then
    local item = reaper.GetTrackMediaItem(track, 0)
    reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", crossfade_length)
    reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", crossfade_length)
    reaper.SetMediaItemInfo_Value(item, "D_POSITION", track_index * step_size)
  end
end
