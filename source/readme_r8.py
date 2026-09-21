from pathlib import Path
import json,re,csv
p=Path(__file__).resolve().parents[1];v=json.loads((p/'reports/Routing_validation.json').read_text());m=json.loads((p/'reports/Envelope_overlap_review.json').read_text());a=json.loads((p/'reports/Parts_list.json').read_text());c=v['DRC_counts']
rows=[]
for block in re.split(r'(?=^\[)',(p/'reports/After_routing_DRC.txt').read_text(),flags=re.M):
 if not block.startswith('[unconnected_items]'):continue
 ends=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.+)',block)
 if len(ends)!=2:continue
 rows.append([len(rows)+1,*ends[0],*ends[1]])
with (p/'reports/Remaining_connections_R8.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['finding','x1_mm','y1_mm','item1','x2_mm','y2_mm','item2']);w.writerows(rows)
(p/'README.md').write_text(f'''# R8 routing and mechanical checkpoint

**INCOMPLETE. Not released for fabrication, assembly or vehicle power.**

The requested complete routing was not achieved. Native KiCad reports {c.get('unconnected_items',0)} unconnected-item findings. These are connection findings, not necessarily distinct nets. No exclusions were added to hide them.

## Changes
- Reworked signal and power routing on the four copper layers, added ground stitching and net-tie fanouts, and screened resulting copper with native DRC.
- Repositioned 16 small passive components; see reports/R8_repositioned_passives.json. The final approximate assembly has {m['front_bodies']} front and {m['back_bodies']} back bodies.
- Low-current signal vias use 0.60 mm copper / 0.30 mm drills; power vias remain separate. This does not qualify current capability.
- Added atomic PCB saving with a native parse/count check after a save failure. The recovered pad/net map still matches all {v['assigned_pin_net_pairs_verified']} assigned pairs in the project netlist.
- Regenerated the test-fit STLs and drawings from this placement.

## Current native checks
{json.dumps(v,indent=2)}

The netlist comparison proves preservation of project assignments, not independent verification of Ford/MS3/MapDaddy/MicroSquirt wiring. Schematic content was not changed in R8. Native ERC was not rerun; the installed KiCad 7 CLI has no ERC command. Earlier ERC reports are historical. Library-footprint warnings remain visible and must be reviewed in the user's installed KiCad environment.

Authoritative current files: reports/After_routing_DRC.txt, Routing_validation.json, Remaining_connections_R8.csv, Current_path_audit_R8.json, Mechanical_geometry.json, Envelope_overlap_review.json and STL_validation.json. Other source and report files are historical work records and trial scripts, not instructions to rerun blindly.

## Mechanical trial
Board: 140.93 x 163.36 x 1.60 mm. Print mechanical/R8_Bare_Board_1p6mm.stl at 100%, in millimetres. There are 297 drilled holes, including seven 3.20 mm trial mounting holes. This rectangular outline does not reproduce the factory J3 notch.

R8_Component_Envelopes.stl includes the board and 236 approximate body prisms. Both STLs are watertight. The modelled bodies have {m['envelope_overlap_count']} same-side overlap findings.

User-provided back-to-cover gap: 6.35 mm. Maximum modelled underside body height: {m['maximum_modelled_back_height_mm']:.3f} mm. Nominal body-only margin: {m['nominal_body_only_margin_mm']:.3f} mm. These values do not include solder, lead protrusions, manufacturing tolerances, case hardware or insulation. The envelope print will need supports or a suitable orientation.

Missing from the mechanical assembly: MS3 daughtercard and its full connector stack, MapDaddy and hoses, Ford connector shell/bent pins, mating Micro-Fit housing/latch/wire bends, thermal clips and insulating pads. Approximate bodies cannot verify these items.

## Unfinished electrical engineering
{sum(x['part']=='UNSELECTED' for x in a)} of {len(a)} parts-list entries remain UNSELECTED; the included inventory is not an order-ready BOM. Optional TO-220/DPAK ignition alternatives are not implemented: Q13-Q16 remain provisional TO-220, and FGD3245G2-F085C requires a verified footprint/pinout and thermal design.

Width targets are not ampacity ratings. Some routes contain narrower escapes and via transitions; see Current_path_audit_R8.json for lengths below each target. Injector, ignition, IAC, transmission and shared-return paths still require current/thermal engineering, selected copper stackup, transient/clamp checks, and fuse coordination. The upstream 30 A fuse does not establish board or connector capacity. Do not treat a zero clearance count as an electrical release.

Open GrandMarquis97_RevA.kicad_pro. Portable project libraries, existing schematic/PDF, model provenance and parts inventory are included. R7 remains a separate prior revision.
''')
print('README and connection table generated')
