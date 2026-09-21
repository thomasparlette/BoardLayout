# Strict native audit profile

KiCad 10.0.6 native DRC and ERC were run twice: once with the active project configuration, and once from an isolated detached Git worktree with ignored categories promoted to warnings. The active `.kicad_pro`, board, and schematic were not changed. `STRICT_PROFILE_OVERRIDES.json` records the exact overrides and profile source.

## PCB checks enabled in the isolated copy

- `missing_courtyard`
- `track_not_centered_on_via`
- `tuning_profile_track_geometries`
- `footprint_filters_mismatch`
- `pth_inside_courtyard`
- `npth_inside_courtyard`
- `footprint_type_mismatch`

Strict DRC results:

- 199 dangling-track warnings
- 52 track-end-not-centered-on-via warnings
- 17 missing-courtyard warnings
- 17 dangling-via warnings
- 2 silkscreen-to-edge warnings
- 42 unconnected-item errors
- 286 schematic-parity warnings
- no checks left in the native report's ignored list

## ERC checks enabled in the isolated copy

- `single_global_label`
- `four_way_junction`
- `simulation_model_issue`
- `footprint_filter`

Strict ERC result: **zero violations and zero ignored checks**.

The legacy project has no top-level ERC settings object. The isolated copy therefore used the default ERC settings object from KiCad 10.0.6's bundled Arduino Uno template, then promoted the four ignored checks above to warnings. This preserves KiCad's default pin-conflict matrix while exposing all previously ignored categories.

## Interpretation

The strict ERC is a current native pass for the checked-in schematic hierarchy. It does not independently prove functional pin mapping or component correctness. The strict DRC remains release-blocking. Rule changes have not been copied into the active project because each legacy ignore and its resulting findings require review before a controlled project-rule migration.
