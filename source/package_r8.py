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
cli='/tmp/kicad_local/usr/bin/kicad-cli'
for name,layers,mirror in [('top','F.Cu,F.SilkS,Edge.Cuts',False),('bottom','B.Cu,B.SilkS,Edge.Cuts',True),('inner1','In1.Cu,Edge.Cuts',False),('inner2','In2.Cu,Edge.Cuts',False)]:
 out=p/'mechanical'/f'{name}.svg';cmd=[cli,'pcb','export','svg','--layers',layers,'--page-size-mode','2','--exclude-drawing-sheet','--output',str(out),str(p/'GrandMarquis97_RevA.kicad_pcb')]
 if mirror:cmd.insert(-1,'--mirror')
 subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
 cairosvg.svg2png(url=str(out),write_to=str(out.with_suffix('.png')),output_width=700,background_color='#ffffff')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25);sm=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
im=Image.new('RGB',(1500,1450),'#142331');d=ImageDraw.Draw(im)
d.text((30,20),'R8 FIT-TEST REVISION — ELECTRICAL ROUTING INCOMPLETE',fill='white',font=font)
d.text((30,62),str(v['DRC_counts'].get('unconnected_items',0))+' open-connection findings | Not for fabrication',fill='#ffd39a',font=sm)
for i,(name,title) in enumerate([('top','Front copper + silkscreen'),('bottom','Back copper + silkscreen — mirrored'),('inner1','Inner copper 1'),('inner2','Inner copper 2')]):
 x=25+(i%2)*745;y=115+(i//2)*645;d.text((x,y),title,font=sm,fill='white');img=Image.open(p/'mechanical'/f'{name}.png').convert('RGB');img.thumbnail((700,580));im.paste(img,(x,y+32))
im.save(p/'mechanical/Layout_R8.png')
(p/'GrandMarquis97_RevA.kicad_prl').unlink(missing_ok=True)
for q in (p/'mechanical').glob('*R7*'):q.unlink()
manifest={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='SHA256.json'}
(p/'SHA256.json').write_text(json.dumps(manifest,indent=2))
z=p.parent/'GrandMarquis97_R8_ROUTING_CHECKPOINT.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 for f in p.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:out.write(f,str(Path(p.name)/f.relative_to(p)))
print(z, z.stat().st_size, v, 'UNSELECTED',unselected)
