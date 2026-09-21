# R10 exact-copper cleanup validation

## Scope

This change removes only geometry that cannot add a connection or a distinct
copper shape:

- 102 zero-length track segments
- 207 extra records from nonzero exact-duplicate groups
- 309 unique objects total

No via, footprint, pad, net assignment, zone, width rule, or nonduplicate route
was changed. Injector and ignition widths remain unchanged pending the branch
current and simultaneity inputs recorded in `KNOWN_HOLDS.md`.

## Method

`source/cleanup_exact_copper_r10.py` loads the board through KiCad 10.0.6
`pcbnew`, selects exact candidates by native object UUID, and then removes only
the corresponding one-line records from the legacy board serialization. This
avoids an unrelated full-file format migration. Before replacing the board, the
script reloads a staged file through `pcbnew` and checks object-count deltas and
unchanged footprint, pad, and net counts.

The full removed-object ledger, including UUID, reason, net, layer, dimensions,
lock state, and retained duplicate UUID, is in `TRACK_CLEANUP_AUDIT.csv` and
`TRACK_CLEANUP_AUDIT.json`.

## Structural result

| Check | Before | After |
|---|---:|---:|
| Segments | 43,176 | 42,867 |
| Vias | 2,230 | 2,230 |
| Zero-length segments | 102 | 0 |
| Exact-duplicate groups / extras | 207 / 208 | 0 / 0 |
| Footprints | 246 | 246 |
| Pads | 888 | 888 |
| Native net entries (including net 0) | 190 | 190 |
| Removed locked objects | 0 | 0 |

The 208 original duplicate extras included one duplicate zero-length record;
therefore the disjoint removal total is 102 zero-length objects plus 207
nonzero duplicate extras.

The stored source-netlist comparison remains an exact match for all 737 assigned
pad/net pairs (excluding off-board J121).

## Native KiCad regression

Both post-cleanup runs used KiCad 10.0.6 with in-memory zone refill,
`--severity-all`, `--all-track-errors`, and `--schematic-parity`.

| Result | Configured profile, before / after | Strict profile, before / after |
|---|---:|---:|
| Rule violations | 218 / 218 | 287 / 287 |
| Opens | 42 / 42 | 42 / 42 |
| Schematic parity | 286 / 286 | 286 / 286 |
| Ignored checks | 7 / 7 | 0 / 0 |

Post-cleanup category counts are unchanged:

- Configured: 199 track dangling, 17 via dangling, 2 silkscreen-to-edge.
- Strict: the configured findings plus 52 track-end-to-via centering and 17
  missing-courtyard findings.
- The open count and per-net distribution are unchanged.

Some DRC witness UUIDs and dangling-track net attribution changed because KiCad
selected different representative objects after duplicate UUIDs were removed.
This does not change the total/category counts, the open-net distribution, or
the represented nonzero copper geometry. The post-cleanup reports are
`POST_EXACT_CLEANUP_DRC.json` and `POST_EXACT_CLEANUP_STRICT_DRC.json`.

## Release conclusion

Exact redundant-copper cleanup is complete, but the release state remains
`ROUTING_INCOMPLETE`. The 42 opens, strict DRC findings, schematic parity,
stackup, current-path, component, mechanical, and physical-test holds remain.
