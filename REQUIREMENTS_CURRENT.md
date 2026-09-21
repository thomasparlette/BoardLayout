# 1997 Grand Marquis MS3 EEC-V Replacement Board — Current Requirements

## Vehicle and project objective

- Vehicle: 1997 Mercury Grand Marquis, 4.6 L SOHC 2-valve V8.
- Retain the factory EEC-V PCM enclosure, factory harness connector, mounting arrangement and original case cooling edges.
- Replace the factory PCB with a custom KiCad PCB that hosts the MS3 mainboard interface and an integrated MS3X-equivalent I/O implementation.
- Reuse the verified factory EEC-V connector pad numbering and the supplied Ford pin-reference material.
- Provide design files suitable for a mechanical prototype now and a later manufactured PCB after electrical validation.

## Engine control scope

- Use MegaSquirt 3 architecture with the existing MS3 card.
- Recreate the MS3X functions on the custom PCB.
- Use MapDaddy alone for MAP and barometric pressure.
- Use factory crank and cam signals with appropriate conditioning.
- Retain factory IAC: Ford F6AZ-9F715-EB, 1.0–1.2 A, commanded near 300 Hz.
- Use Bosch OE 62395 high-impedance injectors, 11–18 ohm.
- Initial ignition is dual waste-spark factory coil packs; COP/D585 coils are excluded from this revision.
- User clarification dated 2026-09-21: only one injector and one ignition channel are active at a time. Each injector is 0.7 A maximum RMS and 1.0–1.2 A peak; use 1.2 A as the branch design peak. Each ignition channel is 1.2–1.5 A peak; use 1.5 A as both the branch peak and a conservative continuous-current sizing case until a measured dwell waveform is available. The hypothetical eight-injector simultaneous load is 5.6 A RMS and is covered by the stated 6 A aggregate budget.
- Do not include EGR, EVAP, purge or other emissions controls.
- Replace factory narrowband O2 operation with external wideband controllers for Bosch LSU 4.2 or 4.9 sensors.
- Factory O2 heater circuits may provide the external controller supply; narrowband-related wiring may be used as a switched ground/enable only, subject to final schematic verification.

## Transmission and auxiliary control scope

- Retain the 4R70W automatic transmission.
- Use a MicroSquirt v3.0 mounted inside the vehicle for transmission control.
- Add a pass-through connector from the PCM shell to the custom PCB so the MicroSquirt can use the factory harness circuits.
- Pass-through opening available: approximately 0.75 in high by 1.5 in long. A flanged or PCB-edge solution is acceptable; removable crimp terminals are preferred.
- Transmission load assumptions: SSA/SSB 0.4–0.6 A; TCC 0.7–1.2 A; EPC 2.1–4.8 A pulsed. Verify against the actual transmission hardware before release.
- Fuel pump, fan and A/C outputs drive relay coils only. Other auxiliary loads assume 1–1.5 A maximum unless separately specified.

## Electrical requirements

- PCM receives 12 V through the original fused vehicle circuits; upstream ECM fuse is 30 A.
- The board provides internal power regulation.
- Support injector channels and the MS3X I/O assignments supplied by the user, including injector outputs, logic spark outputs, boost/idle mid-current outputs, flex-fuel, launch, table switch, datalog and auxiliary analog inputs.
- Use factory coil driver strategy initially. Requested ignition driver is FGD3245G2-F085C.
- Provide future compatibility for TO-220 and DPAK ignition-driver options, pending pinout, thermal and footprint verification.
- Separate power, digital, sensor and case-ground strategy must be retained and verified with the net-tie implementation.
- Preserve the existing power copper until complete paths are qualified: 4.0 mm shared VPWR/ACTUATOR_12/PGND; 3.0 mm coil; 2.0 mm injector; 1.2 mm auxiliary/transmission; 0.6 mm rail; 0.25 mm signal. The coil and injector widths are conservative legacy targets, not required final widths or certified current ratings. The branch-current and nominal copper-weight inputs are now known, but smaller widths still require temperature-rise, route-length, via, neckdown, connector, fault-current and complete-path review.

## Mechanical and layout requirements

- Board outline: 140.93 mm × 163.36 mm.
- Nominal board thickness: 1.60 mm.
- Use the supplied factory mounting-hole measurements and actual mounting-hole locations.
- J120, J130, J131 and J140 are located at the bottom/rear of the board.
- Rear cover clearance from the board: 6.35 mm (1/4 in). Components may be mounted on both sides; clearance must be checked.
- Place heat-producing FETs/driver hardware adjacent to the case cooling edges with a defined thermal interface before production.
- Current R10 routing candidate uses eight copper layers: F.Cu, In1–In6.Cu and B.Cu, with through vias only. User-selected nominal copper weights are 1 oz (about 35 µm) on F.Cu/B.Cu and 0.5 oz (about 17.5 µm) on In1–In6.Cu. The fabricator-specific dielectric stackup, finished-copper tolerances and via capability remain to be selected and checked.
- Current underside component moves: D26 (89,120), D27 (80,126), D28 (80,117), D30 (90,131), D33 (78,133), all coordinates in mm.

## Manufacturing and documentation requirements

- Prefer SMD components where feasible; use both sides of the PCB when needed.
- Use JLCPCB constraints for final fabrication rules and confirm the selected eight-layer stackup before release.
- Create/update the BOM with actual orderable Mouser parts and verified footprints.
- Provide KiCad project, schematic sheets, board, custom symbols/footprints/models, BOM, current-routing report, layout images and STL mechanical-fit files.
- Provide a board-only STL and a component-envelope STL for test printing.

## Mandatory completion gates before manufacturing or vehicle use

- Resolve every KiCad unconnected-items error and every clearance, hole-clearance, edge-clearance, courtyard and rule error without suppressing rules.
- Remove unintended track/via dangling stubs and re-run DRC.
- Run a fresh ERC after the schematic is finalized.
- Independently verify the Ford connector pin map and every MS3/MS3X/MicroSquirt connection against authoritative documents and the actual hardware.
- Select and verify every BOM item, especially Q13–Q16 ignition driver footprints/pinouts, pass-through connector, fusing/protection, high-current parts and thermal hardware.
- Select the fabricator-specific stackup using the nominal 1 oz outer/0.5 oz inner copper requirement, then verify ampacity, via current sharing, neckdowns and heat dissipation for coils, injectors, IAC, EPC and other loads.
- Complete bench testing with JimStim, dummy loads and the actual MS3/MicroSquirt hardware, followed by automotive transient and engine/transmission validation.
- Confirm the printed mechanical fit in the factory PCM case, including connector engagement, shell pass-through, daughtercard height, MapDaddy/hose clearance, solder/lead protrusion and thermal clips/insulators.
