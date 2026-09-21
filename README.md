# Grand Marquis 1997 MS3 replacement PCB — R10 eight-layer candidate

> **Engineering checkpoint — not released for fabrication or vehicle use.**

This repository contains the active R10 eight-layer KiCad candidate for a custom controller in a 1997 Mercury Grand Marquis EEC-V enclosure. The design is still `ROUTING_INCOMPLETE`.

## Current verified inventory

The read-only static audit of the native board reports:

- 246 footprints and 888 pads;
- 737 assigned pad/net pairs matching `source/input_netlist.xml`, excluding the intentionally off-board J121 entry;
- eight copper layers (`F.Cu`, `In1.Cu`–`In6.Cu`, `B.Cu`);
- 43,176 segments and 2,230 through vias;
- 102 zero-length segments;
- 207 exact duplicate segment geometries, comprising 208 extra records;
- 3,339 locked segments and 89 locked vias.

Run `py source/production_baseline_audit.py` to regenerate `production_review/BASELINE_AUDIT.md` and the machine-readable audit. This parser is a reproducible inventory tool; it does not replace KiCad DRC, ERC, zone refill, or visual review.

## Stale validation warning

`reports/Routing_validation.json` is behind the current board by 280 segments and four vias. `reports/After_routing_DRC.txt` is also a saved checkpoint, not a current native run. Its 24 unconnected-item findings and other category counts must be regenerated before routing work begins.

## Release blockers

- Native DRC and ERC must be rerun on the current files.
- Every true open, unintended dangling object, zero-length segment, duplicate segment, and unexplained zone island must be resolved without weakening rules.
- The 0.20 mm Default class conflicts with the 0.25 mm signal target in `REQUIREMENTS_CURRENT.md`.
- The eight-layer physical stackup and copper weights are not selected.
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
