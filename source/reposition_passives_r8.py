"""Relocate blocked low-profile passives to an underside site with a screened via escape for each pad."""
from pathlib import Path
import pcbnew as k,json,re,math
from shapely.geometry import Polygon,box
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));r=(p/'reports/After_routing_DRC.txt').read_text();refs=set()
for block in re.split(r'(?=^\[)',r,flags=re.M):
 if block.startswith('[unconnected_items]'):refs.update(re.findall(r'of ([RC]\d+) on [FB].Cu',block))
models={q['ref']:q for q in json.loads((p/'reports/Mechanical_geometry.json').read_text())['parts']};power={n for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() if c['width_mm']>.25 for n in c['nets']};cell=2000000;obs=[];grid={};drills=[]
def vec(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def add(it,ref=''):
 for layer in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]:
  if not it.IsOnLayer(layer):continue
  sh=it.GetEffectiveShape(layer);bb=sh.BBox();idx=len(obs);obs.append((it.GetNetCode(),layer,sh,bb,ref))
  for x in range(bb.GetX()//cell,bb.GetRight()//cell+1):
   for y in range(bb.GetY()//cell,bb.GetBottom()//cell+1):grid.setdefault((x,y),[]).append(idx)
for fp in b.GetFootprints():
 for pd in fp.Pads():
  add(pd,fp.GetReference())
  if pd.GetDrillSize().x:drills.append((pd.GetPosition(),k.ToMM(pd.GetDrillSize().x)/2))
for t in b.GetTracks():
 add(t)
 if isinstance(t,k.PCB_VIA):drills.append((t.GetPosition(),k.ToMM(t.GetDrillValue())/2))
keep=[z for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()];retired=set()
def clear(sh,net,layer,ref,extras=[]):
 bb=sh.BBox();bb.Inflate(k.FromMM(.251));ids=set()
 for x in range(bb.GetX()//cell,bb.GetRight()//cell+1):
  for y in range(bb.GetY()//cell,bb.GetBottom()//cell+1):ids.update(grid.get((x,y),[]))
 for i in ids:
  n,l,o,ob,r=obs[i]
  if r==ref or r in retired or n==net or (layer is not None and l!=layer):continue
  if bb.Intersects(ob) and k.SHAPE.Collide(sh,o,k.FromMM(.251)):return False
 for n,l,o in extras:
  if n!=net and (layer is None or l==layer) and k.SHAPE.Collide(sh,o,k.FromMM(.251)):return False
 for z in keep:
  if k.SHAPE.Collide(sh,z.Outline(),k.FromMM(.251)):return False
 return True
bodies=[]
for fp in b.GetFootprints():
 if fp.GetLayer()==k.B_Cu and fp.GetReference() in models:
  m=models[fp.GetReference()];x,y=k.ToMM(fp.GetPosition().x),k.ToMM(fp.GetPosition().y);q=Polygon(m['polygon']);cx,cy=m['x'],m['y'];from shapely.affinity import translate
  bodies.append((fp.GetReference(),translate(q,x-cx,y-cy)))
changes=[]
for fp in sorted(list(b.GetFootprints()),key=lambda f:f.GetReference()):
 ref=fp.GetReference()
 if ref not in refs or ref not in models or models[ref]['height']>2 or not all(d.GetAttribute()==k.PAD_ATTRIB_SMD for d in fp.Pads()):continue
 original=(k.ToMM(fp.GetPosition().x),k.ToMM(fp.GetPosition().y));side=b.GetLayerName(fp.GetLayer());trial=fp.Duplicate()
 if trial.GetLayer()!=k.B_Cu:trial.Flip(trial.GetPosition(),False)
 accepted=None
 for rad in [0,2,4,6,8,10,12,16,20]:
  for angle in range(0,360,45):
   x,y=original[0]+rad*math.cos(math.radians(angle)),original[1]+rad*math.sin(math.radians(angle))
   if not(4<x<136 and 17<y<158):continue
   body=box(x-1.6,y-1.35,x+1.6,y+1.35)
   if any(n!=ref and body.distance(q)<.5 for n,q in bodies):continue
   if any(body.distance(box(k.ToMM(q.x)-rr,k.ToMM(q.y)-rr,k.ToMM(q.x)+rr,k.ToMM(q.y)+rr))<.35 for q,rr in drills):continue
   trial.SetPosition(vec(x,y));ps=list(trial.Pads());extras=[(d.GetNetCode(),k.B_Cu,d.GetEffectiveShape(k.B_Cu)) for d in ps]
   if not all(clear(pd.GetEffectiveShape(k.B_Cu),pd.GetNetCode(),k.B_Cu,ref,extras) for pd in ps):continue
   plans=[];ok=True
   for pd in ps:
    n=pd.GetNetCode();width=.6 if pd.GetNetname() in power else .2;diam=.8 if pd.GetNetname() in power else .6;drill=.4 if diam==.8 else .3;start=pd.GetPosition();found=None
    for radius in [1.6,2,2.4,2.8,3.2]:
     for a in range(0,360,45):
      end=vec(k.ToMM(start.x)+radius*math.cos(math.radians(a)),k.ToMM(start.y)+radius*math.sin(math.radians(a)));ex,ey=k.ToMM(end.x),k.ToMM(end.y)
      if not(1<ex<139.9 and 1<ey<162.3):continue
      if any(math.hypot(ex-k.ToMM(q.x),ey-k.ToMM(q.y))<rr+drill/2+.251 for q,rr in drills):continue
      if any(math.hypot(ex-k.ToMM(e.x),ey-k.ToMM(e.y))<(drill+d)/2+.251 for _,e,_,_,d,_ in plans):continue
      circle=k.SHAPE_CIRCLE(end,k.FromMM(diam/2));seg=k.SHAPE_SEGMENT(start,end,k.FromMM(width))
      if clear(circle,n,None,ref,extras) and clear(seg,n,k.B_Cu,ref,extras):found=(start,end,width,diam,drill,n);break
     if found:break
    if not found:ok=False;break
    plans.append(found)
    extras.extend([(n,l,k.SHAPE_CIRCLE(found[1],k.FromMM(diam/2))) for l in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]])
    extras.append((n,k.B_Cu,k.SHAPE_SEGMENT(start,found[1],k.FromMM(width))))
   if ok:accepted=(x,y,body,plans);break
  if accepted:break
 if not accepted:continue
 x,y,body,plans=accepted
 if fp.GetLayer()!=k.B_Cu:fp.Flip(fp.GetPosition(),False)
 fp.SetPosition(vec(x,y));retired.add(ref)
 # New pads are added under a distinct index reference so they remain obstacles.
 for pd in fp.Pads():add(pd,ref+'@new')
 bodies=[q for q in bodies if q[0]!=ref]+[(ref,body)]
 for start,end,w,diam,drill,n in plans:
  t=k.PCB_TRACK(b);t.SetStart(start);t.SetEnd(end);t.SetWidth(k.FromMM(w));t.SetLayer(k.B_Cu);t.SetNetCode(n);b.Add(t);add(t)
  v=k.PCB_VIA(b);v.SetPosition(end);v.SetWidth(k.FromMM(diam));v.SetDrill(k.FromMM(drill));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNetCode(n);b.Add(v);add(v);drills.append((end,drill/2))
 changes.append({'ref':ref,'old_xy':original,'new_xy':[x,y],'old_side':side,'new_side':'B.Cu','model_body_height_mm':models[ref]['height'],'cover_gap_mm':6.35});print('MOVED',ref,original,'->',x,y,flush=True)
 k.SaveBoard(str(f),b)
 if len(changes)>=16:break
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R8_repositioned_passives.json').write_text(json.dumps(changes,indent=2));print('DONE',len(changes))
