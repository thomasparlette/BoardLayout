# R10 static baseline audit

This report inventories the current working-tree native files without modifying the board. The preserved baseline is commit `b5af19f6b018b43a92e55f4675a8856e3b85c9b5`. Static parsing supplements the native KiCad 10.0.6 DRC/ERC results recorded below.

## Native-file inventory

- Board format version: `20221018`
- Board thickness: 1.60 mm
- Copper layers: F.Cu, In1.Cu, In2.Cu, In3.Cu, In4.Cu, In5.Cu, In6.Cu, B.Cu
- Embedded physical stackup: **no**
- Footprints / pads / named nets: 246 / 888 / 189
- Segments / vias / zones: 43176 / 2230 / 17
- Locked segments / vias: 3339 / 89
- Zero-length segments: 102
- Exact duplicate segment groups / extra records: 207 / 208
- Exact duplicate via groups / extra records: 0 / 0
- Stored-netlist comparison: 737 assigned pairs, MATCH

## Stale checked-in evidence

`reports/Routing_validation.json` understates the native board by **280 segments** and **4 vias**. The saved DRC was created on 2026-09-14 22:43:03 and was not rerun for this audit.

Saved DRC categories: `{"lib_footprint_mismatch": 199, "silk_edge_clearance": 2, "track_dangling": 199, "unconnected_items": 24, "via_dangling": 15}`

## Fresh native KiCad baseline

- DRC rule violations: 218 — `{"silk_edge_clearance": 2, "track_dangling": 199, "via_dangling": 17}`
- DRC unconnected items: 42
- Schematic parity issues: 286 — `{"extra_footprint": 7, "footprint_symbol_field_mismatch": 199, "footprint_symbol_mismatch": 10, "net_conflict": 70}`
- ERC violations under the configured profile: 0
- Strict-copy DRC rule violations: 287 — `{"missing_courtyard": 17, "silk_edge_clearance": 2, "track_dangling": 199, "track_not_centered_on_via": 52, "via_dangling": 17}`
- Strict-copy ERC violations: 0; ignored checks: 0
- DRC zone refill: in memory only; the native board was not saved or converted.
- Native input hashes remained unchanged. KiCad's incidental `.kicad_prl` preference migration was discarded.

The strict profile was applied only to an isolated Git worktree. Its ERC result is a full zero-violation pass. The strict DRC remains release-blocking and the active project still retains its original ignored-category settings pending reviewed disposition.

## Rule concerns

- Project minimum track width: 0.0 mm
- Project minimum clearance: 0.0 mm
- Globally ignored categories: footprint_type_mismatch, missing_courtyard, npth_inside_courtyard, pth_inside_courtyard
- DRC exclusions: 0
- The Default class remains 0.20 mm and there is no assigned 0.25 mm Signal class.

## Release disposition

`ROUTING_INCOMPLETE`

Do not release fabrication outputs from this baseline. DRC repair, post-repair native validation, visual review, and all documented electrical/mechanical qualification gates remain required.
