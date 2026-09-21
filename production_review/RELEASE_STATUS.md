# R10 release status

## Current state

`ROUTING_INCOMPLETE`

Exact zero-length/duplicate cleanup and the first ground-island repair are complete, but 30 native unconnected-item findings and the remaining DRC violations are unresolved. No fabrication package is authorized.

## Evidence available

- Native-board static inventory in `BASELINE_AUDIT.md` and `BASELINE_AUDIT.json`.
- UUID-level exact-copper cleanup and native regression evidence in `EXACT_COPPER_CLEANUP_VALIDATION.md`, `TRACK_CLEANUP_AUDIT.json`, and the post-cleanup DRC reports.
- UUID-level ground-remnant cleanup and seven live-island repairs in `GROUND_ISLAND_REPAIR_VALIDATION.md`, `GROUND_ISLAND_REPAIR_AUDIT.json`, and the post-repair DRC reports. Native unconnected-item findings are reduced from 42 to 30; D27 DGND and the R80 PGND island remain explicitly blocked.
- User-supplied injector/ignition branch loads and nominal 1 oz outer/0.5 oz inner copper basis in `BRANCH_CURRENT_BASIS.md`.
- 737 assigned PCB pad/net pairs match the stored source netlist, excluding J121.
- Checked-in saved DRC from 2026-09-14, retained only as a checkpoint.
- Existing mechanical envelope models retained as fit aids, not physical qualification.

## Evidence still required

- Repair and rerun native KiCad DRC after the remaining 30 unconnected-item findings and 287 strict-profile rule violations are dispositioned. The next ground work requires local rerouting around D27 and R80 rather than another standalone via insertion.
- Reviewed routing repairs with before/after evidence.
- Independent Ford/MS3/MS3X/MicroSquirt functional mapping.
- Selected and verified footprints, BOM, fabricator-specific dielectric stackup and copper tolerances, current paths, vias, and thermal interfaces.
- Complete mechanical fit evidence and prototype fabrication outputs.
- Prototype assembly, bench, automotive-transient, thermal, and vehicle testing as applicable to each higher release state.

KiCad 10.0.6 strict-profile ERC currently passes with zero violations and zero ignored checks. That result does not close PCB, component-selection, mapping, stackup, mechanical, or physical-test holds.

The state must not advance until the applicable evidence exists in the repository and has been reviewed.
