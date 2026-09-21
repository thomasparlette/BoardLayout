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
for name,layers,mirror in [('top','F.Cu,F.SilkS,Edge.Cuts',False),('bottom','B.Cu,B.SilkS,Edge.Cuts',True),('inner1','In1.Cu,Edge.Cuts',False),('inner2','In2.Cu,Edge.Cuts',False),('inner3','In3.Cu,Edge.Cuts',False),('inner4','In4.Cu,Edge.Cuts',False),('inner5','In5.Cu,Edge.Cuts',False),('inner6','In6.Cu,Edge.Cuts',False)]:
 out=p/'mechanical'/f'{name}.svg';cmd=[cli,'pcb','export','svg','--layers',layers,'--page-size-mode','2','--exclude-drawing-sheet','--output',str(out),str(p/'GrandMarquis97_RevA.kicad_pcb')]
 if mirror:cmd.insert(-1,'--mirror')
 subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
 cairosvg.svg2png(url=str(out),write_to=str(out.with_suffix('.png')),output_width=700,background_color='#ffffff')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25);sm=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
im=Image.new('RGB',(1500,2750),'#142331');d=ImageDraw.Draw(im)
d.text((30,20),'R10 EIGHT-LAYER OPTION — ENGINEERING PROTOTYPE',fill='white',font=font)
d.text((30,62),str(v['DRC_counts'].get('unconnected_items',0))+' open-connection findings | Not for fabrication',fill='#ffd39a',font=sm)
for i,(name,title) in enumerate([('top','Front copper + silkscreen'),('bottom','Back copper + silkscreen — mirrored'),('inner1','Inner copper 1'),('inner2','Inner copper 2'),('inner3','Inner copper 3 — PGND'),('inner4','Inner copper 4 — DGND'),('inner5','Inner copper 5 — PGND'),('inner6','Inner copper 6 — DGND')]):
 x=25+(i%2)*745;y=115+(i//2)*645;d.text((x,y),title,font=sm,fill='white');img=Image.open(p/'mechanical'/f'{name}.png').convert('RGB');img.thumbnail((700,580));im.paste(img,(x,y+32))
im.save(p/'mechanical/Layout_R10.png')
