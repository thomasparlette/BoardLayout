# R10 static baseline audit

This report inventories the current working-tree native files without modifying the board. The preserved baseline is commit `b5af19f6b018b43a92e55f4675a8856e3b85c9b5`. This audit supplements, but does not replace, native KiCad DRC/ERC. KiCad was not available in the audit environment, so the checked-in DRC remains stale and release-blocking.

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

## Rule concerns

- Project minimum track width: 0.0 mm
- Project minimum clearance: 0.0 mm
- Globally ignored categories: footprint_type_mismatch, missing_courtyard, npth_inside_courtyard, pth_inside_courtyard
- DRC exclusions: 0
- The Default class remains 0.20 mm and there is no assigned 0.25 mm Signal class.

## Release disposition

`ROUTING_INCOMPLETE`

Do not modify routing or release fabrication outputs from this static audit. A fresh native DRC and ERC, zone refill, visual review, and all documented electrical/mechanical qualification gates remain required.
