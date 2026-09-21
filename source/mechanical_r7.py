"""Export board holes and package envelopes. Never labels envelopes as qualified parts."""
from pathlib import Path
import pcbnew as k, json, re, math
p=Path(__file__).resolve().parents[1]; b=k.LoadBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'))
sources={x['footprint']:x for x in json.loads((p/'reports/Model_sources.json').read_text())}
def mm(a): return k.ToMM(a)
def box_wrl(path,bb):
 x,y,z,xx,yy,zz=bb
 pts=[(a/2.54,c/2.54,d/2.54) for d in (z,zz) for c in (y,yy) for a in (x,xx)]
 path.write_text('#VRML V2.0 utf8\n# APPROXIMATE ENVELOPE - NOT A MANUFACTURER MODEL\nShape { appearance Appearance { material Material { diffuseColor 0.7 0.35 0.08 } } geometry IndexedFaceSet { coord Coordinate { point [ '+','.join(' '.join(map(str,q)) for q in pts)+' ] } coordIndex [ 0,2,3,1,-1,4,5,7,6,-1,0,1,5,4,-1,2,6,7,3,-1,0,4,6,2,-1,1,3,7,5,-1 ] } }')
parts=[];holes=[];skipped=[]
for fp in b.GetFootprints():
 ref=fp.GetReference();name=str(fp.GetFPID().GetLibItemName());pads=list(fp.Pads())
 for pad in pads:
  if pad.GetDrillSize().x:
   holes.append(dict(ref=ref,pin=pad.GetNumber(),x=mm(pad.GetPosition().x),y=mm(pad.GetPosition().y),dx=mm(pad.GetDrillSize().x),dy=mm(pad.GetDrillSize().y),angle=pad.GetOrientationDegrees()))
 if ref.startswith('H') or ref.startswith('NT'):continue
 source=sources.get(name,{});model=p/'models'/source.get('model','missing')
 status='GENERIC PACKAGE: exact purchased part not qualified'
 if model.is_file():
  s=model.read_text();pts=[]
  for match in re.findall(r'point\s*\[([^]]+)\]',s,re.S):
   a=[float(v) for v in re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',match)]
   pts.extend([tuple(2.54*v for v in a[i:i+3]) for i in range(0,len(a)-2,3)])
  if not pts:raise ValueError(model)
  bb=[min(q[i] for q in pts) for i in range(3)]+[max(q[i] for q in pts) for i in range(3)]
 else:
  if ref=='J1':skipped.append({'ref':ref,'reason':'Factory connector body and bent-pin envelope not verified; holes included.'});continue
  if ref=='J120':bb=[-3.575,-.99,0,30.575,8.92,10.29];status='APPROXIMATE Micro-Fit envelope: KiCad fab outline and Molex mated-height specification; latch/cable mate excluded'
  elif ref.startswith('RV'):bb=[-2.5,-2.5,0,2.5,2.5,5];status='PLACEHOLDER potentiometer envelope; verify actual selected part'
  else:
   coords=[(mm(d.GetPos0().x),-mm(d.GetPos0().y)) for d in pads]
   if not coords:continue
   bb=[min(q[0] for q in coords)-1.27,min(q[1] for q in coords)-1.27,0,max(q[0] for q in coords)+1.27,max(q[1] for q in coords)+1.27,9]
   status='PLACEHOLDER header envelope; 9 mm assumed, excludes cables and daughtercards'
  model=p/'models'/(ref+'_ENVELOPE.wrl');box_wrl(model,bb)
 fp.Models().clear();m=k.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/models/'+model.name;fp.Add3DModel(m)
 x,y=mm(fp.GetPosition().x),mm(fp.GetPosition().y);a=-math.radians(fp.GetOrientationDegrees())
 corners=[]
 for u,v in [(bb[0],-bb[1]),(bb[3],-bb[1]),(bb[3],-bb[4]),(bb[0],-bb[4])]:
  corners.append([x+u*math.cos(a)-v*math.sin(a),y+u*math.sin(a)+v*math.cos(a)])
 parts.append(dict(ref=ref,value=fp.GetValue(),footprint=name,x=x,y=y,angle=fp.GetOrientationDegrees(),layer=b.GetLayerName(fp.GetLayer()),height=max(.2,bb[5]),polygon=corners,local_model_bounds=bb,status=status,model=model.name))
k.SaveBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'),b)
result={'board_mm':[140.93,163.36,1.6],'origin':'front left, component-side view; x right, y towards rear','parts':parts,'holes':holes,'excluded':skipped,'missing_assemblies':['MS3 daughtercard and its connectors above the socket','MapDaddy module and hose fittings','MicroSquirt cable mate, latch travel, wire bends','Factory case, thermal clips and insulating pads'],'status':'MECHANICAL TRIAL ONLY; package models do not qualify unselected components'}
(p/'reports/Mechanical_geometry.json').write_text(json.dumps(result,indent=2));print(len(parts),'component models;',len(holes),'holes;',len(skipped),'excluded bodies')
