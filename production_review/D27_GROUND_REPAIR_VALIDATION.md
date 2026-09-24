# R10 D27 ground repair validation

## Result

The reviewed local reroute closes D27.1, the last DGND unconnected finding,
without increasing any configured- or strict-profile rule category. Native
KiCad unconnected-item findings fall from **30 to 29**:

| Net | Before | After | Change |
|---|---:|---:|---:|
| DGND | 1 | 0 | −1 |
| PGND | 1 | 1 | 0 |
| All nets | 30 | 29 | −1 |

R80.2 remains the only ground-specific open. Its isolated F.Cu PGND fill still
requires a separately reviewed local reroute around coil/control copper.

## Electrical and geometry basis

D27 is the BAT54S clamp for `DATALOG_LOGIC`. R118 provides 10 kΩ series
impedance from `AUX_DATALOG`; D27.1 is therefore a transient clamp return, not
an injector, ignition, or aggregate 6 A load-current path. The route is kept
short for clamp-return inductance.

The assigned `Rails_unverified` DGND preference is 0.60 mm with a 0.80/0.40 mm
via. That geometry does not fit this pocket. The installed 0.25 mm local
neckdown and 0.60/0.30 mm through via match the previously reviewed D26/D28
clamp-return precedent, but remain release-held pending transient, component,
stackup, and fabricator-tolerance qualification.

The selected via is nominally at the 0.250 mm clearance boundary to existing
F.Cu `SPARE_PM2` track `dead8b89-46fc-4819-b211-3673a6696172`. It passes native
DRC but is not treated as fabrication-margin qualification.

## Copper changes

The edit preserves the board's legacy `20221018` serialization and changes only
the reviewed UUID-tagged copper records:

| Net | Removed | Added | Purpose |
|---|---|---|---|
| SPARE_PM2 | 1 × 0.20 mm In2.Cu segment | 2 × 0.25 mm In2.Cu segments | Clear the D27 through-via barrel while preserving J101.27–J130.18 continuity |
| HEATER_G1 | 1 × 0.20 mm In5.Cu segment | 3 × 0.25 mm In5.Cu segments | Clear the D27 through-via barrel while preserving Q26.1/R108.2/R109.1 continuity |
| DGND | None | 1 × 0.25 mm B.Cu segment; 1 × 0.60/0.30 mm through via | Join D27.1 to DGND fills on In1, In4, and In6 |

The board changes from 42,770 to 42,774 segments and from 2,235 to 2,236
through vias. All 246 footprints, 888 pads, 190 nets, 17 zones, pad/net
assignments, locked copper, and surviving pre-existing copper geometries are
unchanged. Zero-length segment and exact-duplicate-extra counts remain zero.

`D27_GROUND_REPAIR_AUDIT.json` records the two removed UUIDs, every deterministic
added UUID, exact geometry, connectivity guards, and installed hash.

## Native DRC regression

KiCad 10.0.6 ran both profiles with zone refill, all track errors, all
severities, and schematic parity against the exact candidate bytes later
installed:

`812efbeb56429a5944ccdd86b9af773ec80edf383730570cbbbdbac23a657999`

| Check | Before | After |
|---|---:|---:|
| Configured violations | 218 | 218 |
| Configured unconnected items | 30 | 29 |
| Configured parity notices | 286 | 286 |
| Configured ignored checks | 7 | 7 |
| Strict violations | 287 | 287 |
| Strict unconnected items | 30 | 29 |
| Strict parity notices | 286 | 286 |
| Strict ignored checks | 0 | 0 |

Configured categories remain 199 `track_dangling`, 17 `via_dangling`, and two
`silk_edge_clearance`. Strict adds the same 52
`track_not_centered_on_via` and 17 `missing_courtyard` findings as before. The
rule-violation UUID sets are unchanged in both profiles; no added repair object
is cited.

The unconnected per-net multiset changes only by removal of one DGND finding.
Connectivity recomputation selects alternate witness pairs for some existing
opens, but their per-net counts do not change.

Evidence:

- `POST_D27_GROUND_REPAIR_DRC.json`
- `POST_D27_GROUND_REPAIR_STRICT_DRC.json`
- `D27_GROUND_REPAIR_AUDIT.json`
- `UNCONNECTED_BEFORE_AFTER.csv`

## Reproduction and disposition

`source/repair_d27_ground_r10.py` validates the reviewed source hash, exact
removal geometry, pre/post pad connectivity, native object delta, DGND plane
overlap, and deterministic additions. It refuses installation unless the
candidate SHA-256 exactly matches the separately DRC-tested hash.

Because a KiCad 10 save would rewrite the legacy board, validation refills
zones without saving them. Refill zones in KiCad (`B`) after opening the board
before visual ratsnest review.

This is connectivity progress only. It does not make the board ready for
fabrication or vehicle use.
