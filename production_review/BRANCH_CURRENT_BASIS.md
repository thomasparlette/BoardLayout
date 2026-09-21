# Injector and ignition branch-current basis

## User-supplied inputs — 2026-09-21

| Case | RMS design input | Peak design input | Maximum active channels |
|---|---:|---:|---:|
| Injector branch | 0.7 A | 1.2 A (upper end of 1.0–1.2 A) | 1 |
| Ignition branch | Not separately supplied | 1.5 A (upper end of 1.2–1.5 A) | 1 |

For conservative conductor screening, the ignition branch is treated as 1.5 A
continuous until an actual dwell waveform is measured. This is deliberately
more severe thermally than treating its peak as an unspecified low duty cycle.

Eight hypothetical simultaneous injectors would total 5.6 A RMS. That is within
the user-supplied 6 A aggregate budget. This aggregate value is not divided by
eight to size an active branch; the 0.7 A RMS and 1.2 A peak branch values above
control instead.

## Copper basis

- F.Cu and B.Cu: nominal 1 oz copper, approximately 35 µm.
- In1.Cu through In6.Cu: nominal 0.5 oz copper, approximately 17.5 µm.
- Board thickness: nominal 1.6 mm.
- Fabricator dielectric construction, finished-copper tolerances and via
  capability: not yet selected.
- Approved conductor temperature-rise limit: not yet selected.

## Routing consequence

The former report assumption of 70 µm copper is superseded. The 2.0 mm injector
and 3.0 mm ignition figures remain conservative legacy trunk targets, not
certified minimum widths. Native KiCad inventory shows that both net families
already contain 0.6 mm inner-layer segments and 0.8 mm vias mixed with the
wider trunks.

The regenerated geometry audit reports the following material below the legacy
trunk targets. Lengths are the sum of segment lengths, not source-to-load path
lengths and not evidence that parallel geometry shares current equally.

| Net | Segments below legacy target | Summed length |
|---|---:|---:|
| COIL_1 | 164 | 102.47 mm |
| COIL_2 | 202 | 136.10 mm |
| COIL_3 | 447 | 172.22 mm |
| COIL_4 | 297 | 160.76 mm |
| INJECTOR_1 | 378 | 199.15 mm |
| INJECTOR_2 | 269 | 110.43 mm |
| INJECTOR_3 | 254 | 136.80 mm |
| INJECTOR_4 | 248 | 107.47 mm |
| INJECTOR_5 | 152 | 63.40 mm |
| INJECTOR_6 | 240 | 74.18 mm |
| INJECTOR_7 | 247 | 132.21 mm |
| INJECTOR_8 | 193 | 153.44 mm |

The new branch currents support evaluating smaller geometry, but they do not
justify a blanket width edit. Width changes must be made against complete
source-to-load paths after open-connection repair, including every neckdown and
via transition. The review must cover voltage drop, copper temperature rise,
route length, current sharing, connector limits, driver fault behavior and the
final fabricator stackup.

[IPC-2152](https://www.ipc.org/TOC/IPC-2152.pdf) is the applicable
current-carrying-capacity design framework, but its result depends on acceptable
temperature rise and board construction. This document therefore records inputs
and holds; it does not claim an ampacity or manufacturing release.
