from pathlib import Path
import json,math
import numpy as np,trimesh
from shapely.geometry import box,Point,Polygon
from shapely.ops import unary_union
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parents[1];out=p/'mechanical';out.mkdir(exist_ok=True)
g=json.loads((p/'reports/Mechanical_geometry.json').read_text());W,H,T=g['board_mm']
holes=[]
for h in g['holes']:
 # Native project uses circular drills. Refuse to misrepresent slots.
 assert abs(h['dx']-h['dy'])<.0001,h
 holes.append(Point(h['x'],h['y']).buffer(h['dx']/2,quad_segs=24))
plate=box(0,0,W,H).difference(unary_union(holes))
bare=trimesh.creation.extrude_polygon(plate,T,engine='earcut');bare.export(out/'R8_Bare_Board_1p6mm.stl')
pieces=[bare];render=[]
for part in g['parts']:
 poly=Polygon(part['polygon']);mesh=trimesh.creation.extrude_polygon(poly,part['height']+.02,engine='earcut');mesh.apply_translation([0,0,-part['height'] if part['layer']=='B.Cu' else T-.02]);pieces.append(mesh)
 render.append((mesh,part))
assembly=trimesh.boolean.union(pieces,engine='manifold');assembly.export(out/'R8_Component_Envelopes.stl')
check={'bare_watertight':bool(bare.is_watertight),'envelopes_watertight':bool(assembly.is_watertight),'bare_bounds_mm':bare.bounds.tolist(),'envelopes_bounds_mm':assembly.bounds.tolist(),'units':'millimetres','print_scale':'100%; do not scale to fit','hole_count':len(holes),'body_envelopes':len(render),'NOT_INCLUDED':g['missing_assemblies']+[x['reason'] for x in g['excluded']]}
assert bare.is_watertight and assembly.is_watertight
(p/'reports/STL_validation.json').write_text(json.dumps(check,indent=2))
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=ImageFont.truetype(font,22);sm=ImageFont.truetype(font,13)
im=Image.new('RGB',(1500,1100),'#edf1f5');d=ImageDraw.Draw(im)
d.text((30,20),'R8 — MECHANICAL FIT TRIAL',fill='#122536',font=f)
d.text((30,55),'Package envelopes: selected footprints, not a fully qualified component assembly',fill='#933614',font=f)
scale=5.4;ox=45;oy=135
def xy(x,y):return ox+x*scale,oy+y*scale
d.rectangle([xy(0,0),xy(W,H)],fill='#d4e4de',outline='#153f31',width=2)
for part in g['parts']:
 color='#dca761' if 'PLACEHOLDER' in part['status'] or 'APPROXIMATE' in part['status'] else '#7da89c'
 d.polygon([xy(*q) for q in part['polygon']],fill=('#97bada' if part['layer']=='B.Cu' else color),outline='#254f46')
 d.text(xy(part['x'],part['y']),part['ref'],fill='#132b25',font=sm)
for h in g['holes']:
 x,y=xy(h['x'],h['y']);r=h['dx']*scale/2;d.ellipse((x-r,y-r,x+r,y+r),fill='white',outline='#355248')
for h in g['holes']:
 if h['ref'].startswith('H'):
  x,y=xy(h['x'],h['y']);d.text((x+9,y-15),h['ref'],font=sm,fill='#973111')
notes=['Board: 140.93 x 163.36 x 1.60 mm','Front / factory connector: y = 0','Rear / Micro-Fit mating face: y = 163.36','','J120: Molex 43045-2000','Locating holes: 3.00 mm nominal','20 electrical contacts; 3.00 mm pitch','','J130 moved to (62,146)','J140 moved to (90,140)','J131 retained at (62,156)','','Orange: assumed / approximate body','Green: top generic package; blue: underside','','NOT MODELLED:','MS3 daughtercard above its socket','MapDaddy module and hose fittings','Ford connector shell and bent pins','Micro-Fit cable plug and latch travel','Case thermal clips / insulation','','Seven screw holes are 3.20 mm trial sizes.','Print at 100% in millimetres.','Check the bare board before the tall model.','','ROUTING / ELECTRICAL STATUS:','See current README and native reports.','Not released for manufacturing.']
for i,t in enumerate(notes):d.text((850,140+i*25),t,font=sm if len(t)>43 else ImageFont.truetype(font,17),fill='#243849')
im.save(out/'R8_Mechanical_Layout.png')
# Isometric view rendered from the exact same solid envelopes as the STL.
im=Image.new('RGB',(1400,1100),'#edf1f5');d=ImageDraw.Draw(im)
def project(a):
 x,y,z=a;return (680+(x-y)*4.0,145+(x+y)*2.15-z*6.3)
faces=[]
for mesh,part in [(bare,{'status':'board'})]+[(m,a) for m,a in render if a['layer']=='F.Cu']:
 color=(70,131,104) if part['status']=='board' else ((207,140,62) if 'PLACEHOLDER' in part['status'] or 'APPROXIMATE' in part['status'] else (78,91,106))
 for tri,normal in zip(mesh.triangles,mesh.face_normals):
  light=.65+.3*abs(normal[2]);shade=tuple(int(c*light) for c in color)
  faces.append((float(-10000 if part['status']=='board' else tri[:,0].mean()+tri[:,1].mean()+tri[:,2].mean()),[project(a) for a in tri],shade))
for _,tri,col in sorted(faces,key=lambda a:a[0]):d.polygon(tri,fill=col)
d.text((35,30),'R8 COMPONENT ENVELOPES — TOP VIEW',font=f,fill='#162837')
d.text((35,68),'Approximate bodies — missing daughtercards, harnesses and factory shell listed in the mechanical report.',font=sm,fill='#953d19')
im.save(out/'R8_Envelope_Preview.png');print(json.dumps(check))

# Separate underside view. Reflection of x and z presents the actual back side.
im=Image.new('RGB',(1400,1100),'#edf1f5');d=ImageDraw.Draw(im);faces=[]
for mesh,part in [(bare,{'status':'board'})]+[(m,a) for m,a in render if a['layer']=='B.Cu']:
 for tri,normal in zip(mesh.triangles,mesh.face_normals):
  q=tri.copy();q[:,0]=W-q[:,0];q[:,2]=-q[:,2]
  col=(60,110,92) if part['status']=='board' else (80,115,145)
  faces.append((-10000 if part['status']=='board' else float(q[:,0].mean()+q[:,1].mean()+q[:,2].mean()),[project(x) for x in q],col))
for _,tri,col in sorted(faces,key=lambda a:a[0]):d.polygon(tri,fill=col)
d.text((35,30),'R8 COMPONENT ENVELOPES — UNDERSIDE VIEW',font=f,fill='#162837')
d.text((35,68),str(sum(a['layer']=='B.Cu' for a in g['parts']))+' underside bodies; 6.35 mm cover gap. Lead protrusions are not modelled.',font=sm,fill='#953d19')
im.save(out/'R8_Underside_Preview.png')
