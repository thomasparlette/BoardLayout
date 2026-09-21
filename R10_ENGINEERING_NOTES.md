# R10 eight-layer routing candidate

Routing is in progress. The latest native result is reports/Routing_validation.json; this document does not declare completion or manufacturing release.

The candidate retains the 140.93 × 163.36 mm outline, mounting-hole coordinates and nominal 1.6 mm board thickness. The following diodes moved to the underside: D26 (89,120), D27 (80,126), D28 (80,117), D30 (90,131), and D33 (78,133), coordinates in millimetres. Other placements are unchanged from R9. Copper layers are F.Cu, In1–In6.Cu and B.Cu. The two added internal layers carry PGND and DGND pours as well as routed traces. Through vias only.

Power routing preserves the unqualified targets in reports/Routing_targets.json. The VPWR branch serving only F1 pin 1 uses a 1.0 mm trunk and 0.6 mm neck; the schematic specifies F1 as 1 A, with its actual part unselected. The ACTUATOR_12 branch serving D33 pin 1 uses the 1.2 mm EPC branch target. Shared VPWR and ACTUATOR_12 trunks remain 4.0 mm targets. Connector fanouts use parallel 0.6 mm necks on three layers and via arrays where space permits. None of these geometries establishes a current rating.

On 2026-09-21 the user supplied the branch basis: only one injector and one ignition channel are active at a time; one injector is 0.7 A maximum RMS and 1.0–1.2 A peak; one ignition channel is 1.2–1.5 A peak. Use 1.2 A for injector branch peak and conservatively use 1.5 A as both ignition peak and continuous-current sizing case until a measured dwell waveform is available. Eight simultaneous injectors would be 5.6 A RMS, within the stated 6 A aggregate budget. Nominal copper is 1 oz (about 35 µm) outer and 0.5 oz (about 17.5 µm) inner.

The existing 2.0 mm injector and 3.0 mm coil values remain conservative legacy targets, not certified minimums. Native inventory shows both net families already contain 0.6 mm inner-layer sections and 0.8 mm vias, so width changes must follow complete-path review rather than a blanket edit. The earlier 70 µm assumption does not apply to the selected stackup.

The source-netlist comparison verifies 737 pad/net assignments. This is consistency with the existing design, not an independent verification against Ford and MS3 hardware documentation.

## Release holds

- 216 of 240 parts-list entries remain UNSELECTED; component selection is incomplete.
- Q13–Q16 ignition footprints/pinouts remain on hold. The requested TO-220/DPAK alternatives are not qualified.
- Nominal copper weights are selected at 1 oz outer and 0.5 oz inner. The dielectric construction, finished-copper tolerance and via capability still require a fabricator-specific stackup.
- Neckdowns, via arrays, current sharing, coil dwell and thermal interfaces require electrical/thermal validation. User-supplied current values are design inputs, not bench verification or proof of hardware current regulation.
- KiCad 10.0.6 strict-profile ERC passes with zero violations and zero ignored checks. PCB/schematic parity still has 286 warnings requiring disposition.
- No bench, dummy-load, automotive-transient or engine/transmission validation has been performed.

## Mechanical fit files

The R10 STL files contain the board and available component body envelopes. The maximum modeled underside depth is 2.22 mm, within the user-specified 6.35 mm cover gap. They exclude solder and leads, the complete MS3 daughtercard, MapDaddy assembly and hoses, cable mating/latch envelopes, Ford connector body/bent-pin envelope, thermal clips and insulating pads. They are fit aids, not a complete assembly-clearance approval.
