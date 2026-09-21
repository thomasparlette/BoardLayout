from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parents[1];g=json.loads((p/'source/routed_geometry.json').read_text());r=json.loads((p/'reports/Routing_validation.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
im=Image.new('RGB',(1600,1060),'#101c27');d=ImageDraw.Draw(im);scale=4.7
d.text((30,18),'R4 ROUTING REVIEW - INCOMPLETE / NOT FOR FABRICATION',font=font,fill='white')
d.text((30,50),'Actual copper geometry; connector at top. Both panels use the same X/Y orientation.',font=small,fill='#d1dee6')
colors={'F.Cu':'#f97564','B.Cu':'#78aefc','In1.Cu':'#d6b660','In2.Cu':'#79c997'}
for panel,layers in enumerate([['F.Cu','B.Cu'],['In1.Cu','In2.Cu']]):
 ox=35+panel*800;oy=120
 def pt(x,y):return ox+x*scale,oy+y*scale
 d.text((ox,90),' / '.join(layers),font=font,fill='white');d.rectangle((*pt(0,0),*pt(140.93,163.36)),outline='white',width=2)
 for t in g['tracks']:
  if not t['via'] and t['layer'] in layers:d.line((*pt(t['x1'],t['y1']),*pt(t['x2'],t['y2'])),fill=colors[t['layer']],width=max(1,round(t['width']*scale)))
 for pad in g['pads']:
  x,y=pt(pad['x'],pad['y']);w=pad['w']*scale/2;h=pad['h']*scale/2
  d.rectangle((x-w,y-h,x+w,y+h),outline='#cdbb7d',width=1)
  if pad['drill']:
   rad=pad['drill']*scale/2;d.ellipse((x-rad,y-rad,x+rad,y+rad),fill='#101c27',outline='#cdbb7d')
 d.text((ox,910),'Pad outlines shown on both panels for location reference.',font=small,fill='#bdc9d5')
d.text((30,955),f"{r['tracks']} track segments | {r['vias']} vias | {r['DRC_counts'].get('unconnected_items',0)} missing connections",font=font,fill='white')
d.text((30,995),'Current capability, thermal interfaces, case clearances and full component sourcing remain unqualified.',font=small,fill='#ffd39a')
im.save(p/'mechanical/Layout_R4.png')
