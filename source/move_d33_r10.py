import safe_save_r8
from pathlib import Path
import pcbnew as k,json,math,collections
p=Path(__file__).resolve().parents[1];fn=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(fn));mm=k.ToMM;vec=lambda x,y:k.VECTOR2I(k.FromMM(x),k.FromMM(y));f=next(x for x in b.GetFootprints() if x.GetReference()=='D33');old=(mm(f.GetPosition().x),mm(f.GetPosition().y));power={n for d in json.load(open(p/'reports/Routing_targets.json'))['widths'].values() if d['width_mm']>.25 for n in d['nets']};cell=k.FromMM(3);bins=collections.defaultdict(list);holes=[]
for obj in [pd for fp in b.GetFootprints() if fp!=f for pd in fp.Pads()]+list(b.GetTracks()):
 if not obj.IsOnLayer(k.B_Cu):continue
 shape=obj.GetEffectiveShape(k.B_Cu);bb=shape.BBox()
 if isinstance(obj,k.PAD) and max(obj.GetDrillSize().x,obj.GetDrillSize().y)>0:holes.append(shape)
 for x in range(bb.GetX()//cell,bb.GetRight()//cell+1):
  for y in range(bb.GetY()//cell,bb.GetBottom()//cell+1):bins[x,y].append((obj,shape,bb))
f.Flip(f.GetPosition(),False);assert f.GetLayer()==k.B_Cu
chosen=None
for dx,dy in sorted([(x,y) for x in range(-15,16) for y in range(-5,21)],key=lambda a:a[0]*a[0]+a[1]*a[1]):
 pos=(old[0]+dx,old[1]+dy);f.SetPosition(vec(*pos));remove={};valid=True
 body=k.SHAPE_POLY_SET();body.NewOutline()
 for x,y in [(pos[0]-3,pos[1]-2),(pos[0]+3,pos[1]-2),(pos[0]+3,pos[1]+2),(pos[0]-3,pos[1]+2)]:body.Append(k.FromMM(x),k.FromMM(y))
 if any(k.SHAPE.Collide(body,h,k.FromMM(.25)) for h in holes):continue
 for pd in f.Pads():
  sh=pd.GetEffectiveShape(k.B_Cu);bb=sh.BBox();bb.Inflate(k.FromMM(.251));seen=set()
  for x in range(bb.GetX()//cell,bb.GetRight()//cell+1):
   for y in range(bb.GetY()//cell,bb.GetBottom()//cell+1):
    for obj,osh,obb in bins[x,y]:
     uid=obj.m_Uuid.AsString()
     if uid in seen or obj.GetNetCode()==pd.GetNetCode():continue
     seen.add(uid)
     if bb.Intersects(obb) and k.SHAPE.Collide(sh,osh,k.FromMM(.251)):
      if isinstance(obj,k.PAD) or obj.IsLocked() or obj.GetNetname() in power:valid=False;break
      remove[uid]=obj
    if not valid:break
   if not valid:break
  if not valid:break
 if valid:chosen=(pos,remove);break
assert chosen,'No clear underside placement found'
pos,remove=chosen
for obj in remove.values():b.Delete(obj)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(fn),b)
report={'ref':'D33','from':{'side':'F.Cu','xy':old},'to':{'side':'B.Cu','xy':pos},'displaced_signal_tracks':len(remove),'reason':'Provide access to the EPC clamp diode pads without reducing the EPC current-path width. Package and thermal rating remain unqualified.'};(p/'reports/D33_placement_R10.json').write_text(json.dumps(report,indent=2));print(report)
