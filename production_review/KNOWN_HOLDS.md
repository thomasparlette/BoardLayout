# Known R10 holds

| Hold | Why it matters | Evidence required to close | Blocks |
|---|---|---|---|
| `NATIVE_DRC_HOLD` | KiCad 10.0.6 finds 42 opens and 287 strict-profile rule violations. | Repair and rerun native zone refill/DRC with disposition of every finding. | Routing completion and all release states above it |
| `SCHEMATIC_PARITY_HOLD` | DRC reports 286 schematic/PCB parity warnings, including net, field, attribute, and extra-footprint differences. | Review each parity category and synchronize intentionally without changing logical connectivity to hide errors. | CAD review and prototype fabrication |
| `SIGNAL_WIDTH_CONFLICT` | The Default class is 0.20 mm while current requirements specify 0.25 mm signals. | Enforceable class assignment or an approved, documented engineering decision with exceptions. | CAD review |
| `STACKUP_HOLD` | Copper thickness, dielectric geometry, via capability, and impedance/current assumptions are not fixed. | Fabricator-specific eight-layer stackup checked against the design. | Prototype fabrication |
| `PIN_MAPPING_HOLD` | Stored-netlist agreement is not independent functional verification. | Authoritative Ford/MS3/MS3X/MicroSquirt mapping with reviewer sign-off. | Prototype fabrication |
| `IGNITION_DRIVER_HOLD` | Q13–Q16 device, pinout, tab, drive, clamp, package, and case interface are not fully qualified. | Authoritative part data, footprint comparison, electrical review, and thermal/mechanical definition. | Prototype fabrication and vehicle use |
| `BOM_HOLD` | Most exact orderable components and alternates remain unselected. | Buildable, lifecycle-checked BOM with verified footprints. | Prototype fabrication |
| `POWER_THERMAL_HOLD` | Trace targets alone do not establish ampacity or safe temperatures. | End-to-end path, via-sharing, transient, and thermal analyses using the selected stackup and real loads. | Prototype fabrication |
| `BRANCH_CURRENT_HOLD` | User clarified that injector and ignition figures are aggregate eight-cylinder budgets, while individual branch peak/RMS and concurrency values remain unknown. | Aggregate RMS/peak values, per-injector and per-coil peaks, maximum simultaneous channels, duty/dwell basis, and selected stackup. | Coil/injector width reduction and prototype fabrication |
| `MECHANICAL_HOLD` | Existing models omit critical bodies, leads, connectors, hoses, daughtercard, and thermal hardware. | Complete envelope model, test print, and actual enclosure fit check. | Prototype fabrication |
| `PHYSICAL_TEST_HOLD` | No prototype, dummy-load, transient, thermal, or vehicle evidence is archived. | Controlled test results and corrective-action closure. | Production release and vehicle validation |
