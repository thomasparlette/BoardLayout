# R10 D27 via-margin validation

## Result

The D27 clamp return now has a fabrication-margin-oriented layout rather than
the rule-boundary geometry installed by the first connectivity repair. The
short B.Cu return is restored to the assigned 0.60 mm rail width, and its
through via is shifted and increased to 0.65/0.30 mm. Only the obstructing
local `HEATER_G1` escape on In5.Cu is rerouted; CAN, `SPARE_PM2`,
`WB_ENABLE_CMD`, and VCC_5 copper remain unchanged.

This closes the D27-specific zero-margin layout hold. It does **not** release
the board for fabrication or vehicle use: the remaining PCB findings,
fabricator-specific eight-layer stackup, D27 component/transient behavior, and
physical validation still control release.

## Geometry improvement

| Attribute | Before | After |
|---|---:|---:|
| D27 DGND return width | 0.25 mm | 0.60 mm |
| Via position | (78.650, 127.400) mm | (78.735, 127.575) mm |
| Via pad / drill | 0.60 / 0.30 mm | 0.65 / 0.30 mm |
| Nominal annular ring | 0.150 mm | 0.175 mm |
| Nominal aspect ratio at 1.6 mm | 5.33:1 | 5.33:1 |
| Minimum routed-copper clearance | 0.250002 mm | 0.310000 mm |
| Return-segment minimum clearance | not separately qualified | 0.432376 mm |

The new via's limiting object is the unchanged F.Cu `SPARE_PM2` segment
`dead8b89-46fc-4819-b211-3673a6696172` at 0.310000 mm. The next routed-copper
gap is 0.310390 mm to the unchanged F.Cu `CAN_L` segment. The 0.60 mm B.Cu
return is limited by VCC_5 at 0.432376 mm. All exceed the active 0.25 mm
clearance rule without moving CAN or power copper.

JLCPCB's current [via-reliability guidance](https://jlcpcb.com/blog/via-aspect-ratio-critical-pcb-reliability)
identifies 0.30 mm and larger drills as a standard process, while its
[rigid-PCB capability table](https://jlcpcb.com/capabilities/Capab) prefers a
via diameter at least 0.15 mm larger than the hole. This design uses a 0.35 mm
pad-minus-hole difference. The published capability is useful layout evidence,
but the actual eight-layer order stackup and DFM result must still be reviewed.

`Rails_unverified` prefers a 0.80/0.40 mm via, but that size cannot be enlarged
in place without hitting four nets. A shifted 0.80/0.40 mm candidate required
three local signal reroutes and was pinched to about 0.284 mm by unchanged CAN,
WB_ENABLE_CMD, and VCC_5 copper. The selected 0.65/0.30 mm geometry instead
retains the standard drill, improves the ring and clearance together, and
requires only the `HEATER_G1` reroute. The class value remains a preference,
not evidence that the smaller low-current clamp via is electrically qualified.

## Copper changes

The follow-on removes the first repair's five-segment `HEATER_G1` tail and
replaces it with this 0.25 mm In5.Cu path:

`(78.7,125.3) -> (77.5,126.5) -> (77.5,128.5) -> (78.6,129.6)`

It also replaces the former D27 DGND segment/via with:

- one 0.60 mm B.Cu segment from D27.1 at `(79.0625,126.95)` to
  `(78.735,127.575)`; and
- one 0.65/0.30 mm through via at `(78.735,127.575)`.

The board changes from 42,774 to 42,772 segments and remains at 2,236 through
vias. All 246 footprints, 888 pads, 190 nets, 17 zones, pad/net assignments,
locked copper, and every surviving pre-existing copper geometry are unchanged.
Zero-length segment and exact-duplicate-extra counts remain zero.

Native connectivity confirms:

- all three reviewed `HEATER_G1` pads remain connected;
- the reviewed `SPARE_PM2` pad pair remains connected without another edit;
- D27.1 reaches both the new segment and via; and
- after refill, the via lands the DGND fills on In1.Cu, In4.Cu, and In6.Cu.

## Native DRC regression

KiCad 10.0.6 ran both profiles with zone refill, all track errors, all
severities, and schematic parity against the exact candidate bytes later
installed:

`b1b8caa84cc4fc4244a08e210aef1ae3a51cb8fe917399a7fb6356737368066d`

| Check | Parent | D27 margin result |
|---|---:|---:|
| Configured violations | 218 | 218 |
| Configured unconnected items | 29 | 29 |
| Configured parity notices | 286 | 286 |
| Configured ignored checks | 7 | 7 |
| Strict violations | 287 | 287 |
| Strict unconnected items | 29 | 29 |
| Strict parity notices | 286 | 286 |
| Strict ignored checks | 0 | 0 |

Configured rule categories and item-UUID signatures are unchanged. Strict
category totals are also unchanged: 199 `track_dangling`, 52
`track_not_centered_on_via`, 17 `missing_courtyard`, 17 `via_dangling`, and two
`silk_edge_clearance`. No new D27 or `HEATER_G1` object is cited by a rule,
open, or parity finding.

KiCad selected alternate representative objects for one remote strict
`track_not_centered_on_via` finding and three existing remote open findings.
Their categories and per-net counts are unchanged, and a fresh parent control
independently reproduced one such witness swap. The regression decision
therefore uses invariant category totals, per-net open counts, geometry, and
zero citations of the new objects rather than claiming unstable witness UUIDs
are byte-for-byte identical.

Evidence:

- `POST_D27_VIA_MARGIN_DRC.json`
- `POST_D27_VIA_MARGIN_STRICT_DRC.json`
- `D27_VIA_MARGIN_AUDIT.json`
- `D27_GROUND_REPAIR_VALIDATION.md` (historical parent checkpoint)

## Reproduction and disposition

`source/qualify_d27_via_margin_r10.py` validates the reviewed parent hash,
exact removal geometry, pad connectivity, native object delta, DGND plane
overlap, and native-shape clearance. It refuses installation unless the
candidate SHA-256 exactly matches the separately DRC-tested hash.

Because a KiCad 10 save would rewrite the legacy board, validation refills
zones without saving them. Refill zones in KiCad (`B`) after opening the board
before visual ratsnest review.

The next ground-specific layout repair remains the R80.2 PGND island. The
overall project remains `ROUTING_INCOMPLETE`.
