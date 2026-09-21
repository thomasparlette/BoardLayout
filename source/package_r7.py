from pathlib import Path
import json,re,collections,subprocess,hashlib,zipfile
from PIL import Image,ImageDraw,ImageFont
import cairosvg
p=Path(__file__).resolve().parents[1];v=json.loads((p/'reports/Routing_validation.json').read_text());r=(p/'reports/After_routing_DRC.txt').read_text();remaining=collections.Counter()
for block in re.split(r'(?=^\[)',r,flags=re.M):
 if block.startswith('[unconnected_items]'):
  m=re.search(r'@[^\n]*?\[([^]]+)\]',block)
  if m:remaining[m[1]]+=1
(p/'reports/Remaining_connections_by_net.json').write_text(json.dumps(dict(remaining.most_common()),indent=2))
a=json.loads((p/'reports/Parts_list.json').read_text());unselected=sum(x['part']=='UNSELECTED' for x in a)
(p/'README.md').write_text(f'''# R7 — connector revision and mechanical fit trial

**INCOMPLETE ELECTRICAL DESIGN. NOT FOR FABRICATION, ASSEMBLY OR VEHICLE POWER.**

The requested final routing was not achieved. This checkpoint has {v['DRC_counts'].get('unconnected_items',0)} native KiCad unconnected-item findings, compared with 86 in R6. The connector footprint and placement changes require additional rerouting. Do not order populated boards from these files.

## What changed
- J120 now uses the Molex 43045-2000 20-contact right-angle footprint, including locating holes; physical pin positions replaced the generic header while retaining numerical pin/net assignments.
- J120 origin (108,154.44), rotation 180 degrees, mating face at rear edge y=163.36. This leaves space beside J131.
- J130 at (62,146), J140 at (90,140), J131 at (62,156). Coordinates in mm from the board drawing origin.
- A full-reroute trial was stopped after failing to converge; its log is historical. The released checkpoint preserves and repairs the earlier copper.
- Copper affected by relocated parts was removed where it violated native clearance checks, and targeted signal routing added. Removal opens are reported, not hidden.
- 236 component package/envelope models attached; board drill and body-envelope STL files supplied. Zero pairwise body-envelope overlaps in this approximate model.
- J120 selection and harness accessories recorded in the parts inventory. {unselected} of {len(a)} inventory entries are still UNSELECTED. This is not an order-ready BOM.

## Native checks
{json.dumps(v,indent=2)}

All {v['assigned_pin_net_pairs_verified']} assigned pad/net pairs match the project's exported netlist; this is not independent vehicle-wiring verification. The connector component value was updated in the schematic and netlist. The latest schematic PDF is included. Native ERC was not rerun: the installed KiCad 7 CLI lacks an ERC command. Earlier supplied reports remain historical evidence only. Library footprint mismatch warnings have not been suppressed.

## Printing
Print mechanical/R7_Bare_Board_1p6mm.stl first, at **100%, millimetres**, flat on the bed. It is 140.93 x 163.36 x 1.60 mm with 297 drilled holes. Small contact holes may need clearing because of printer resolution. Seven mounting holes are trial 3.20 mm diameters; confirm against actual hardware.

R7_Component_Envelopes.stl is a separate union of the board and 236 solid bounding prisms for rough height/clearance checks. Both STL meshes are watertight. The envelope STL has 193 top and 43 underside bodies; supports or a suitable print orientation are required. Use the flat bare-board model for the first print. Generic package geometry and assumed headers are not exact purchased-part models. Orange objects in drawings identify assumed/approximate bodies. The outer board is rectangular and does not reproduce the old factory J3 notch.

**Not included:** MS3 daughtercard above its socket, MapDaddy module/hoses, Ford connector body/bent-pin geometry, mating Micro-Fit cable housing/latch/wire bends, component lead protrusions beneath the board, case clips/insulators or actual thermal contact geometry. The tall print cannot verify these assemblies. Supply exact CAD or measured envelopes before a full mechanical release.

## Electrical work still required
Complete all open routes listed in reports/Remaining_connections_by_net.json; resolve library/silkscreen findings; select and qualify remaining parts; independently check MS3/MapDaddy/MicroSquirt mappings; validate power regulation, transients, fuses, inductive clamps, return paths and heat transfer. Optional TO-220/DPAK ignition footprints are NOT implemented: Q13–Q16 remain provisional TO-220 with ignition pinout hold. The requested FGD3245G2-F085C needs its own checked DPAK placement and thermal design.

Width targets in Routing_targets.json are design targets, not measured ampacity. Existing neckdowns, vias, 30 A upstream fuse coordination, connector simultaneous-current derating and case cooling remain unqualified. The full 30 A supply is not approved through any single Micro-Fit contact. The transmission header assignment is a custom project map, not the MicroSquirt harness pin numbering.

## Project
Open GrandMarquis97_RevA.kicad_pro. Project libraries and relative 3D models are included. Authoritative current checks are reports/Routing_validation.json, After_routing_DRC.txt, Mechanical_geometry.json, Envelope_overlap_review.json and STL_validation.json. Source migration/trial scripts and older reports are history, not instructions to rerun indiscriminately. R6 is retained separately.

Connector sources: https://www.molex.com/en-us/products/part-detail/0430452000 and https://www.molex.com/en-us/products/part-detail/0430252000 . Crimps: https://www.molex.com/en-us/products/part-detail/0430300007 . Footprint: KiCad kicad-footprints Connector_Molex.pretty/Molex_Micro-Fit_3.0_43045-2000_2x10_P3.00mm_Horizontal.kicad_mod. Model provenance and license are in reports/Model_sources.json and models/LICENSE.md.
''')
cli='/tmp/kicad_local/usr/bin/kicad-cli'
for name,layers,mirror in [('top','F.Cu,F.SilkS,Edge.Cuts',False),('bottom','B.Cu,B.SilkS,Edge.Cuts',True),('inner1','In1.Cu,Edge.Cuts',False),('inner2','In2.Cu,Edge.Cuts',False)]:
 out=p/'mechanical'/f'{name}.svg';cmd=[cli,'pcb','export','svg','--layers',layers,'--page-size-mode','2','--exclude-drawing-sheet','--output',str(out),str(p/'GrandMarquis97_RevA.kicad_pcb')]
 if mirror:cmd.insert(-1,'--mirror')
 subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
 cairosvg.svg2png(url=str(out),write_to=str(out.with_suffix('.png')),output_width=700,background_color='#ffffff')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25);sm=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
im=Image.new('RGB',(1500,1450),'#142331');d=ImageDraw.Draw(im)
d.text((30,20),'R7 FIT-TEST REVISION — ELECTRICAL ROUTING INCOMPLETE',fill='white',font=font)
d.text((30,62),str(v['DRC_counts'].get('unconnected_items',0))+' open-connection findings | Not for fabrication',fill='#ffd39a',font=sm)
for i,(name,title) in enumerate([('top','Front copper + silkscreen'),('bottom','Back copper + silkscreen — mirrored'),('inner1','Inner copper 1'),('inner2','Inner copper 2')]):
 x=25+(i%2)*745;y=115+(i//2)*645;d.text((x,y),title,font=sm,fill='white');img=Image.open(p/'mechanical'/f'{name}.png').convert('RGB');img.thumbnail((700,580));im.paste(img,(x,y+32))
im.save(p/'mechanical/Layout_R7.png')
(p/'GrandMarquis97_RevA.kicad_prl').unlink(missing_ok=True)
for q in (p/'mechanical').glob('Layout_R[456].png'):q.unlink()
manifest={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='SHA256.json'}
(p/'SHA256.json').write_text(json.dumps(manifest,indent=2))
z=p.parent/'GrandMarquis97_R7_FIT_TEST_DRAFT.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 for f in p.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:out.write(f,str(Path(p.name)/f.relative_to(p)))
print(z, z.stat().st_size, v, 'UNSELECTED',unselected)
