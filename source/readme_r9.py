from pathlib import Path
import json
p=Path(__file__).resolve().parents[1];v=json.loads((p/'reports/Routing_validation.json').read_text());n=v['DRC_counts'].get('unconnected_items',0)
parts=json.loads((p/'reports/Parts_list.json').read_text());unselected=sum(x['part']=='UNSELECTED' for x in parts)
s=f'''# Grand Marquis 1997 MS3 replacement PCB — R9 six-layer option

**Engineering checkpoint. Not released for fabrication or vehicle operation.**

Routing has {n} native KiCad unconnected-item findings. This is not a completed PCB. See `reports/After_routing_DRC.txt` for individual locations and `reports/Remaining_connections_by_net.json` for the summary. No DRC rule severities or exclusions were changed in R9 to obtain a lower count.

## What changed

R9 adds two internal copper layers and continues signal, power and ground routing. It is a SIX-layer option, replacing R8's four-layer routing stack. The finished thickness remains provisionally 1.60 mm; a JLCPCB stackup and copper weights have not been selected or qualified.

All footprint positions, rotations, sides, mounting holes and the board outline remain identical to R8. The R8 fit-print models included in `mechanical` remain applicable. Printed component bodies are approximate envelopes, not manufacturer STEP models. Leads, mating connectors, MS3 daughtercard clearances, hoses and thermal hardware still need physical checks. The 6.35 mm back-cover gap is not a guarantee of assembled clearance.

## Verification performed

- Native KiCad loads the PCB and runs DRC.
- {v['assigned_pin_net_pairs_verified']} assigned pad/net pairs match the stored source netlist. This checks synchronization with that netlist, not correctness of the vehicle pin map or circuit design.
- {v['footprints']} footprints; {v['tracks']} track segments; {v['vias']} vias.
- DRC categories: `{json.dumps(v['DRC_counts'],sort_keys=True)}`.
- Outline, board thickness and all footprint placements compare equal to R8 (`reports/Mechanical_preservation_R9.json`).
- Native ERC was not rerun: this KiCad 7 environment does not provide the required schematic ERC CLI workflow. Historical ERC reports are not a fresh pass result.

## Remaining release blockers

1. Complete the remaining routing and review all dangling copper, footprint/library differences and silkscreen issues.
2. Resolve {unselected} UNSELECTED entries in the retained parts list. That list is not a procurement-ready Mouser BOM. Pinouts, optional ignition packages and final footprints still need component-specific review.
3. Qualify current paths, including local necks, layer changes, shared return currents, connector contacts, actual copper weights and temperature rise. Neither a trace-width target nor zero unconnected findings establishes ampacity.
4. Verify 6 A ignition operation using measured dwell/current waveforms. No 6 A limiter was established merely by changing the PCB. Keep the 10 A per-primary provisional routing allowance separate from the user's operating target.
5. Check automotive input protection, fault behavior and case thermal interfaces, then bench-test engine and external MicroSquirt transmission interfaces before connecting loads.
6. Confirm mechanical fit and the actual production stackup before fabrication outputs are released.

## Files

- `GrandMarquis97_RevA.kicad_pro`, `.kicad_sch`, `.kicad_pcb`: editable project.
- `mechanical/Layout_R9.png`: six-layer copper/layout overview.
- `mechanical`: inherited R8 fit-test STL files and updated layer pictures.
- `reports`: native DRC, remaining nets, routing targets, parts list and mechanical comparison.
- `LOAD_BUDGET_R9.md`: current user-supplied load basis and unresolved qualifications.
- `source`: reproducibility scripts and historical checkpoints. R8-prefixed scripts/reports may be reused by R9; the native DRC and Routing_validation.json describe the current main PCB.

No fabrication-ready Gerber release is provided in this checkpoint.
'''
(p/'README.md').write_text(s)
