# R10 ground-island repair validation

> Historical checkpoint: the later D27 local reroute closes the D27.1 finding
> described below. See `D27_GROUND_REPAIR_VALIDATION.md` for the current
> 29-open state; R80 is now the only remaining ground-specific open.

## Result

This repair reduces native KiCad unconnected-item findings from **42 to 30**
without increasing the configured- or strict-profile violation totals or
adding a violation category. No added repair object is cited by either DRC
report's rule-violation section. Ground findings change as follows:

| Net | Before | After | Findings removed |
|---|---:|---:|---:|
| DGND | 12 | 1 | 11 |
| PGND | 2 | 1 | 1 |
| All nets | 42 | 30 | 12 |

The remaining ground findings are deliberately not forced:

- **D27.1 DGND:** the relocated B.Cu pad is enclosed by existing signals. Its
  reachable 0.25 mm routing pocket contains no legal 0.60/0.30 mm through-via
  center. A blind B.Cu-to-In6.Cu construction could escape, but the project is
  currently through-via-only and has no approved blind-via stackup.
- **R80.2 PGND island:** the F.Cu fill island has no legal 0.60/0.30 or
  0.80/0.40 mm through-via site and no legal 0.25 mm F.Cu escape. Existing
  COIL_1 and control routing must be locally redesigned in a separate repair.

## Copper changes

The edit preserves the board's legacy `20221018` serialization.

- Removed 95 unlocked, padless DGND segments in five obsolete connectivity
  components.
- Removed 13 unlocked F.Cu dead-tail segments attached to three live DGND
  islands.
- Added seven unlocked 0.25 mm segments, four unlocked 0.60 mm segments, three
  unlocked 0.60/0.30 mm through vias, and two unlocked 0.80/0.40 mm through
  vias.
- Retained all existing locked copper and every existing surviving copper
  object's native geometry.
- Preserved all 246 footprints, 888 pads, 190 nets, 17 zones, and all pad/net
  assignments.
- Preserved zero zero-length segments and zero exact duplicate extras.

| Target | Repair | Copper added | Native result |
|---|---|---|---|
| D28.1 | B.Cu fanout to a DGND plane landing | 2 × 0.25 mm segments, 1 × 0.60/0.30 mm via | Closed |
| D30.2 | B.Cu escape plus In1.Cu plane landing | 2 × 0.60 mm segments, 1 × 0.80/0.40 mm via | Closed |
| D26.1 | B.Cu escape plus In1.Cu plane landing | 3 × 0.25 mm segments, 1 × 0.60/0.30 mm via | Closed |
| C42.2 + C43.2 | Directly join existing island to existing DGND via | 1 × 0.60 mm F.Cu segment | Closed |
| D31.2 + NT1.2 | Short F.Cu plane fanout | 1 × 0.60 mm segment, 1 × 0.80/0.40 mm via | Closed |
| D29.1 + D32.1 | Join live island directly to main-component Q30.2 | 2 × 0.25 mm F.Cu segments | Closed |
| NT1.1 PGND island | Stitch the isolated F.Cu island to main In5.Cu PGND | 1 × 0.60/0.30 mm via at (101.5, 12.8) mm | Closed |

The removed-object UUIDs and every added object's deterministic UUID and
geometry are recorded in `GROUND_ISLAND_REPAIR_AUDIT.json`.

## Preferred-size disposition

DGND is assigned to `Rails_unverified` (0.60 mm trace, 0.80/0.40 mm via).
D30, C42/C43, and D31/NT1 use those preferred sizes throughout. The following
complete-route exceptions retain standard smaller geometry and remain
unqualified release holds:

- **D28:** its two 0.25 mm B.Cu segments reach collision boundaries at 0.258745
  mm and 0.560741 mm. A 0.80/0.40 mm via nominally passes, but with only 0.004
  mm outer-diameter headroom; it stays 0.60/0.30 mm until fabricator tolerances
  are selected.
- **D26:** its first and second B.Cu segments collide at 0.547244 mm and
  0.360472 mm; its via collides at 0.736478 mm outer diameter. The short In1.Cu
  landing alone accepts 0.60 mm, but widening it would not remove the route's
  B.Cu/via bottleneck, so the complete route stays 0.25 mm plus 0.60/0.30 mm.
- **D29/D32:** the two F.Cu segments collide at 0.454071 mm and 0.427629 mm, so
  both remain 0.25 mm.

PGND is assigned to `Shared_power_unverified`, including a preferred
0.80/0.40 mm via. At NT1, that via collides with two In5.Cu `INJECTOR_2`
segments; its exact outer-diameter boundary is 0.698002 mm. The repair retains
the existing standard 0.60/0.30 mm size rather than introducing a
tolerance-edge custom via. These exceptions require current/return-path review
or local rerouting before fabrication.

## Native DRC regression

Both profiles were run with KiCad 10.0.6 using zone refill, all track errors,
all severities, and schematic parity. The configured and strict runs tested the
same exact candidate bytes later installed in the repository:

`1b387eafbcfb576f3ef0c462b303d157d2e03def681219a8f3fcaa12acb7f529`

| Check | Before | After |
|---|---:|---:|
| Configured violations | 218 | 218 |
| Configured unconnected items | 42 | 30 |
| Configured parity notices | 286 | 286 |
| Strict violations | 287 | 287 |
| Strict unconnected items | 42 | 30 |
| Strict parity notices | 286 | 286 |
| Strict ignored checks | 0 | 0 |

Configured categories remain 199 `track_dangling`, 17 `via_dangling`, and two
`silk_edge_clearance`. Strict adds 52 `track_not_centered_on_via` and 17
`missing_courtyard` findings, the same category totals as before the repair.
Connectivity recomputation changes 10 of the 199 `track_dangling` witness
UUIDs while leaving that total unchanged; none of those new witnesses is an
added repair object. Neither report contains a clearance, drill, short,
minimum-width, or copper-to-edge violation involving added repair copper.

Evidence:

- `POST_GROUND_ISLAND_REPAIR_DRC.json`
- `POST_GROUND_ISLAND_REPAIR_STRICT_DRC.json`
- `GROUND_ISLAND_REPAIR_AUDIT.json`
- `UNCONNECTED_BEFORE_AFTER.csv`

## Reproduction and review notes

`source/repair_ground_islands_r10.py` derives the reviewed padless DGND set,
checks its count and UUID-set digest, applies deterministic UUIDv5 additions,
reloads the staged board with native `pcbnew`, and refuses installation unless
the candidate hash matches the separately DRC-tested SHA-256.

Because saving through KiCad 10 would convert and rewrite the legacy board,
zone refill is performed during validation but not serialized. Refill zones in
KiCad (`B`) after opening the board before visually reviewing ratsnest state.

These repairs are connectivity work only. They do not resize or qualify the
injector, ignition, or shared-current paths, and they do not advance the board
to fabrication-ready status.
