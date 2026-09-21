from pathlib import Path
import json,re,collections,subprocess,shutil,hashlib,zipfile
from PIL import Image,ImageDraw,ImageFont
import cairosvg
p=Path(__file__).resolve().parents[1];v=json.loads((p/'reports/Routing_validation.json').read_text());r=(p/'reports/After_routing_DRC.txt').read_text();remaining=collections.Counter()
for block in re.split(r'(?=^\[)',r,flags=re.M):
 if block.startswith('[unconnected_items]'):
  m=re.search(r'@[^\n]*?\[([^]]+)\]',block)
  if m:remaining[m[1]]+=1
(p/'reports/Remaining_connections_by_net.json').write_text(json.dumps(dict(remaining.most_common()),indent=2))
(p/'history').mkdir(exist_ok=True)
shutil.copyfile(p.parent/'upload/02-ERC.rpt',p/'history/User_supplied_ERC.rpt')
shutil.copyfile(p.parent/'upload/01-DRC.rpt',p/'history/User_supplied_DRC.rpt')
parts=json.loads((p/'reports/Parts_list.json').read_text());unselected=sum(x['part']=='UNSELECTED' for x in parts)
counts='\n'.join(f'- {k}: {n}' for k,n in v['DRC_counts'].items())
(p/'README.md').write_text(f'''# Grand Marquis 1997 — R6 routing draft

**INCOMPLETE — NOT FOR FABRICATION, ASSEMBLY OR VEHICLE POWER.**

This revision does not complete the requested ECU. Native KiCad reports {v['DRC_counts'].get('unconnected_items',0)} unconnected-item findings. It is an editable engineering checkpoint; no Gerbers or assembly files are supplied.

## Changes

- Rebuilt signal routing around wider load paths on four copper layers.
- Added outer PGND pours alongside the inner return pours. Net-tie copper-pour keepouts preserve the intended joining locations.
- Added four-layer injector connector escapes and parallel via transitions. These are geometric routing provisions, **not validated 5 A ratings**. Unequal path length, current sharing, neckdowns, copper thickness, thermal rise and connector ratings still need qualification.
- Protected control-supply routing target is 1 mm, based on the planned 1 A F1. Injector, auxiliary and coil targets are unchanged. Exact fuse selection and coordination remain outstanding.
- Removed seven SGND traces that crossed net-tie copper incorrectly.
- Retained mounting geometry, factory connector pin assignments, rear connectors, MapDaddy interface and the existing circuit configuration.

## Checks on the saved board

All {v['assigned_pin_net_pairs_verified']} assigned pin/net pairs match the project's exported netlist; {v['footprints']} footprints, {v['tracks']} track segments and {v['vias']} vias. This is a project consistency check, not independent verification against the car's wiring.

{counts}

The supplied ERC report records zero errors and zero warnings; it is retained in history. No schematic connectivity was edited in this routing revision. Native ERC was not rerun here: this runtime provides KiCad 7.0.11, whose CLI has no ERC command. The 199 library mismatch warnings reported in this runtime must be compared against the embedded and library footprints; they have not been suppressed.

## Remaining work

See reports/Remaining_connections_by_net.json and reports/After_routing_DRC.txt for exact open connections. Some connector escapes are enclosed by adjacent copper and cannot take the required wider trunk without further placement or routing changes. Ground and rail connectivity also remains unfinished.

Parts_list.md and reports/Parts_list.json are reference inventories, not order-ready BOMs: {unselected} of {len(parts)} entries remain UNSELECTED. Ignition driver pinout/package, protective parts, regulator capacitor ESR/load budget, high-current returns and case thermal interfaces are not fully qualified. Q1/Q2 annular rings need correction before the proposed heavy-copper build. A clean DRC would not resolve these electrical requirements.

## Files

Open GrandMarquis97_RevA.kicad_pro in KiCad. Project-relative symbol/footprint libraries are included. mechanical/Layout_R6.png shows native plotted copper on all four layers. Source scripts and reports record routing work; do not run migration or trial scripts indiscriminately. The mechanical dimensions have not changed in this revision. Other routing reports and DSN/SES files are historical intermediate results; Routing_validation.json and After_routing_DRC.txt are the authoritative final checks for this checkpoint.
''')
partsmd=p/'Parts_list.md';partsmd.write_text(partsmd.read_text().replace('# R4 parts list','# R6 parts inventory').replace('# R5 parts list','# R6 parts inventory'))
constraints=p/'JLCPCB_constraints.md';constraints.write_text(constraints.read_text().replace('R5 default','R6 default'))
cli='/tmp/kicad_local/usr/bin/kicad-cli'
for name,layers,mirror in [('top','F.Cu,F.SilkS,Edge.Cuts',False),('bottom','B.Cu,B.SilkS,Edge.Cuts',True),('inner1','In1.Cu,Edge.Cuts',False),('inner2','In2.Cu,Edge.Cuts',False)]:
 out=p/'mechanical'/f'{name}.svg';cmd=[cli,'pcb','export','svg','--layers',layers,'--page-size-mode','2','--exclude-drawing-sheet','--output',str(out),str(p/'GrandMarquis97_RevA.kicad_pcb')]
 if mirror:cmd.insert(-1,'--mirror')
 subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
 cairosvg.svg2png(url=str(out),write_to=str(out.with_suffix('.png')),output_width=760,background_color='#ffffff')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
im=Image.new('RGB',(1620,1460),'#142331');d=ImageDraw.Draw(im)
d.text((30,20),'R6 ROUTING DRAFT — INCOMPLETE / NOT FOR FABRICATION',fill='white',font=font)
d.text((30,58),f"Native KiCad copper plots | {v['DRC_counts'].get('unconnected_items',0)} missing connections | current capacity unqualified",fill='#ffd39a',font=small)
for i,(name,title) in enumerate([('top','Front copper + silkscreen'),('bottom','Back copper + silkscreen — mirrored'),('inner1','Inner layer 1'),('inner2','Inner layer 2')]):
 x=30+(i%2)*800;y=108+(i//2)*660;d.text((x,y),title,font=small,fill='white');img=Image.open(p/'mechanical'/f'{name}.png').convert('RGB');img.thumbnail((760,880));im.paste(img,(x,y+30))
im.save(p/'mechanical/Layout_R6.png')
for old in (p/'mechanical').glob('Layout_R[45].png'):old.unlink()
(p/'GrandMarquis97_RevA.kicad_prl').unlink(missing_ok=True)
manifest={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='SHA256.json'}
(p/'SHA256.json').write_text(json.dumps(manifest,indent=2))
z=p.parent/'GrandMarquis97_R6_ROUTING_DRAFT.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 for f in p.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:out.write(f,str(Path(p.name)/f.relative_to(p)))
print(z);print(v);print('Remaining:',remaining.most_common(15));print('Unselected',unselected,'of',len(parts))
