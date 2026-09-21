import safe_save_r8
from pathlib import Path
import pcbnew as k,json,math
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));cu=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]
def v(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def mm(x):return k.ToMM(x)
added=[]
for ref,pin,sgn in [('NT1','1',-1),('NT1','2',1),('NT2','1',-1),('NT2','2',1)]:
 fp=b.FindFootprintByReference(ref);pd=next(a for a in fp.Pads() if a.GetNumber()==pin);n=pd.GetNetCode();x,y=mm(pd.GetPosition().x),mm(pd.GetPosition().y)
 for length in [2,2.5,3,3.5,4]:
  xx=x+sgn*length;sh=k.SHAPE_SEGMENT(v(x,y),v(xx,y),k.FromMM(.6));vs=k.SHAPE_CIRCLE(v(xx,y),k.FromMM(.4));okay=True
  for f2 in b.GetFootprints():
   for p2 in f2.Pads():
    if p2.GetNetCode()!=n:
     if p2.IsOnLayer(k.F_Cu) and k.SHAPE.Collide(sh,p2.GetEffectiveShape(k.F_Cu),k.FromMM(.251)):okay=False
     for layer in cu:
      if p2.IsOnLayer(layer) and k.SHAPE.Collide(vs,p2.GetEffectiveShape(layer),k.FromMM(.251)):okay=False
    if p2.GetDrillSize().x and math.hypot(mm(p2.GetPosition().x)-xx,mm(p2.GetPosition().y)-y)<mm(max(p2.GetDrillSize().x,p2.GetDrillSize().y))/2+.451:okay=False
  for t in b.GetTracks():
   if isinstance(t,k.PCB_VIA) and math.hypot(mm(t.GetPosition().x)-xx,mm(t.GetPosition().y)-y)<mm(t.GetDrillValue())/2+.451:okay=False
  if not okay:continue
  targets=[]
  for t in b.GetTracks():
   if t.GetNetCode()==n:continue
   hit=t.IsOnLayer(k.F_Cu) and k.SHAPE.Collide(sh,t.GetEffectiveShape(k.F_Cu),k.FromMM(.251))
   hit=hit or any(t.IsOnLayer(l) and k.SHAPE.Collide(vs,t.GetEffectiveShape(l),k.FromMM(.251)) for l in cu)
   if hit:targets.append(t)
  for t in targets:b.Delete(t)
  t=k.PCB_TRACK(b);t.SetStart(v(x,y));t.SetEnd(v(xx,y));t.SetWidth(k.FromMM(.6));t.SetLayer(k.F_Cu);t.SetNetCode(n);b.Add(t)
  t=k.PCB_VIA(b);t.SetPosition(v(xx,y));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetNetCode(n);b.Add(t)
  added.append({'ref':ref,'pin':pin,'net':pd.GetNetname(),'via':[xx,y],'displaced':len(targets)});break
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R8_nettie_fanouts.json').write_text(json.dumps(added,indent=2));print(added)
