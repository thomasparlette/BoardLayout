# Grand Marquis 1997 MS3 replacement PCB — R10 eight-layer candidate

> **Engineering checkpoint — not released for fabrication or vehicle use.**

This repository contains the active R10 eight-layer KiCad candidate for a custom controller in a 1997 Mercury Grand Marquis EEC-V enclosure. The design is still `ROUTING_INCOMPLETE`.

## Current verified inventory

The current native-board audit reports:

- 246 footprints and 888 pads;
- 737 assigned pad/net pairs matching `source/input_netlist.xml`, excluding the intentionally off-board J121 entry;
- eight copper layers (`F.Cu`, `In1.Cu`–`In6.Cu`, `B.Cu`);
- 42,770 segments and 2,235 through vias;
- zero zero-length segments and zero exact duplicate copper extras;
- 3,339 locked segments and 89 locked vias.

The immutable supplied-state inventory remains in `production_review/BASELINE_AUDIT.md`. Do not rerun the baseline generator as a current-state report: it intentionally consumes the baseline DRC evidence. Native KiCad DRC, ERC, zone refill, and visual review remain controlling.

## Stale validation warning

`reports/Routing_validation.json` and `reports/After_routing_DRC.txt` are historical checkpoints, not current native results. Use the dated reports in `production_review` for the configured and strict post-repair evidence.

KiCad 10.0.6 has validated the current board under both the configured and isolated strict profiles with zone refill. The ground-island repair reduces unconnected-item findings from 42 to 30. Strict DRC reports 287 rule violations with unchanged category totals and no added repair object cited by a rule violation, plus 286 schematic-parity warnings; strict ERC passes with zero violations and zero ignored checks. See `production_review/GROUND_ISLAND_REPAIR_VALIDATION.md` and `production_review/STRICT_PROFILE.md`.

## Release blockers

- The remaining 30 native unconnected-item findings, unintended dangling objects, and unexplained zone islands must be resolved without weakening rules.
- The 0.20 mm Default class conflicts with the 0.25 mm signal target in `REQUIREMENTS_CURRENT.md`.
- The nominal copper basis is 1 oz outer/0.5 oz inner, but the fabricator-specific eight-layer dielectric stackup and finished-copper tolerances are not selected.
- Footprints, procurement BOM, functional pin mapping, current paths, via arrays, thermal interfaces, mechanical fit, and automotive protection remain incompletely qualified.
- Bench, transient, engine, and transmission validation have not been performed.

See `production_review/RELEASE_STATUS.md` and `production_review/KNOWN_HOLDS.md` for the controlling release posture.

## Primary files

- `GrandMarquis97_RevA.kicad_pro`, `.kicad_sch`, and `.kicad_pcb`: active native project.
- `GM97_Layout.pretty`, `GM97.kicad_sym`, and `models`: project libraries.
- `REQUIREMENTS_CURRENT.md`: current project requirements.
- `production_review`: regenerated audit evidence and release status.
- `reports`: current and historical engineering reports; check each report's date and provenance before relying on it.
- `source`: audit and historical routing scripts. Do not rerun historical routing automation wholesale against the active board.

No release Gerbers or drill package are provided.
