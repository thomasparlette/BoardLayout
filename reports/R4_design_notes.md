# Grand Marquis 1997 - R4 engineering review

**NOT FOR FABRICATION, ASSEMBLY OR VEHICLE POWER.** This package contains actual corrected KiCad sources and a routing experiment. It is not a completed or current-qualified ECU. Read the generated reports before use. No Gerbers are supplied.

## Changes

- J101 now follows MS3 JP2 as shown in MS3XV30 Hardware 1.5 pages 205 and 206. In particular Spark A is pin 12, 5 V is pin 31, ground is pins 28/30/32, and 12 V is pins 33/34. The complete reviewed mapping is in reports/JP2_verified_mapping.json.
- Existing MapDaddy alone supplies MAP and barometric pressure. J150 is a four-wire adapter, **not** a native sensor footprint: 1 MAP signal, 2 signal ground, 3 regulated sensor 5 V, 4 barometric signal. Barometric conditioning reaches J100 pin 29 (JS5/AD6). J131 pin 2 is disconnected so an external source cannot drive this dedicated input. Confirm the actual module calibration and wire identities before connecting it.
- Schematic connection geometry aligned to 1.27 mm. Explicit source declarations added for externally supplied/return and derived rails. These flags describe intent; they do not supply power.
- All previous copper removed before synchronization to avoid retaining wrong-header connections. Forty-three small analog components moved to B.Cu. Underside clearance is unmeasured.
- J120/J130/J131/J140 retain the R3 rear-edge positions. Board outline and seven mounting locations retain R3 geometry and its unverified assumptions.
- Factory IAC retained with PWM low-side control. Factory wasted spark uses four power stages; no COP, EGR, purge or EVAP added. External wideband controllers and cabin MicroSquirt remain the intended architecture.

## Current targets are not validated ratings

Routing targets assume 70 micrometres copper and use 2.0 mm injector trunks, 1.2 mm auxiliary trunks, 3.0 mm ignition trunks and 4.0 mm shared power trunks. Signal traces use 0.25 mm. These dimensions alone DO NOT establish current capacity. The proposed copper assumption is not a released stackup.

The user's MS3X table describes the commercial MS3X external DB37, not the internal JP2 connector and not a simultaneous load rating. This PCB uses the Ford connector. Power returns, pad escapes, barrel plating, parallel-via transitions, voltage drop and total load still require assessment. The routing experiment can contain single-via transitions and incomplete paths; it is not suitable for high-current testing.

VND5N07TR-E has a typical 5 A current limit. That is not a guaranteed continuous 5 A channel rating. At 0.2 ohm, 5 A implies 5 W conduction loss per driver before temperature effects; eight such channels cannot be assumed thermally acceptable. No heatsink contact or copper area is qualified by these files.

MK-CoilDrvr is the proposed DIYAutoTune sourcing exception for Q13-Q16. Its exact supplied transistor and physical pinout must be checked against the existing provisional TO-220 footprints. Do not assume BIP373 protection or dwell limits carry over to the replacement device. Ignition primary peak current is separate from the table's 30 mA logic-output rating.

## Validation and remaining work

See reports/Schematic_checks.json and reports/Routing_validation.json. Native KiCad netlist export and PCB DRC were available. Native ERC was not run: this KiCad 7 CLI does not expose ERC. Run Inspect > Electrical Rules Checker in KiCad on the ROOT schematic; keep checks enabled. The custom grid/netlist checks are not equivalent to ERC.

Parts_list.md / reports/Parts_list.json enumerate all schematic components. **This is not an order-ready Mouser BOM.** Unselected components, exact land-pattern compatibility, fuse/PTC coordination, LM2937 load/ESR stability, automotive transients, driver thermal design and the transmission pass-through connector remain holds. No substitute component selection is implied by a generic value.

Further release requirements: finish missing routes; resolve DRC findings; verify ERC; establish stackup and current/thermal budget; verify case fit including module heights, pads and insulators; identify MK-CoilDrvr device; qualify vehicle wiring; complete an actual BOM; bench-test with current-limited power and simulated loads before engine use. This package does not include a validated ECU calibration.

The source migration scripts are one-time transformations of the prior revision, not an idempotent build system. Do not rerun them on this output. route_input.dsn and route_final.ses describe only this routing trial. The native PCB is the review output.

## References

- https://www.msextra.com/doc/pdf/MS3XV30_Hardware-1.5.pdf
- https://www.st.com/resource/en/datasheet/vnd5n07-e.pdf
- https://diyautotune.com/products/mapdaddy4
- https://diyautotune.com/products/mk-coildrvr
- https://www.ti.com/lit/gpn/LM2937
