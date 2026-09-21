import safe_save_r8
from pathlib import Path
import pcbnew as k,collections,json,math
p=Path(__file__).resolve().parents[1];fn=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(fn));fresh=k.LoadBoard(str(p.parent/'GrandMarquis97_Layout_R10/source/fanouts_only_r10.kicad_pcb'))
skip={'AC_WOT_CUTOUT','COIL_1','COIL_2','COIL_3','COIL_4','FAN_CONTROL','FUEL_PUMP_CONTROL','IAC','TRANS_EPC','TRANS_TCC','VPWR','WB1_RELAY_LOW','WB2_RELAY_LOW'}
names={t.GetNetname() for t in fresh.GetTracks()}-skip-{'INJECTOR_6','INJECTOR_7'}
old=list(b.GetTracks());bucket=collections.defaultdict(list);cell=k.FromMM(3);cu=[0,1,2,3,4,31]
for t in old:
 bb=t.GetBoundingBox();bb.Inflate(k.FromMM(.26))
 for l in cu:
  if not t.IsOnLayer(l):continue
  for x in range(bb.GetX()//cell,bb.GetRight()//cell+1):
   for y in range(bb.GetY()//cell,bb.GetBottom()//cell+1):bucket[l,x,y].append(t)
remove={};added=[]
for t in old:
 if t.GetNetname() in names and max(t.GetStart().y,t.GetEnd().y)<k.FromMM(22):remove[t.m_Uuid.AsString()]=t
for a in fresh.GetTracks():
 if a.GetNetname() not in names:continue
 for l in cu:
  if not a.IsOnLayer(l):continue
  sh=a.GetEffectiveShape(l);bb=sh.BBox();bb.Inflate(k.FromMM(.251));candidates={}
  for x in range(bb.GetX()//cell,bb.GetRight()//cell+1):
   for y in range(bb.GetY()//cell,bb.GetBottom()//cell+1):
    for t in bucket[l,x,y]:candidates[t.m_Uuid.AsString()]=t
  for uid,t in candidates.items():
   if t.GetNetname()!=a.GetNetname() and k.SHAPE.Collide(sh,t.GetEffectiveShape(l),k.FromMM(.251)):remove[uid]=t
   if isinstance(t,k.PCB_VIA) and isinstance(a,k.PCB_VIA):
    d=math.hypot(t.GetPosition().x-a.GetPosition().x,t.GetPosition().y-a.GetPosition().y)
    if d<(t.GetDrillValue()+a.GetDrillValue())/2+k.FromMM(.251):remove[uid]=t
 if isinstance(a,k.PCB_VIA):
  t=k.PCB_VIA(b);t.SetPosition(a.GetPosition());t.SetWidth(a.GetWidth());t.SetDrill(a.GetDrillValue());t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
 else:
  t=k.PCB_TRACK(b);t.SetStart(a.GetStart());t.SetEnd(a.GetEnd());t.SetWidth(a.GetWidth());t.SetLayer(a.GetLayer())
 t.SetNetCode(b.FindNet(a.GetNetname()).GetNetCode());t.SetLocked(True);b.Add(t);added.append(t)
counts=collections.Counter(t.GetNetname() for t in remove.values())
for t in remove.values():b.Delete(t)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(fn),b);print('added',len(added),'removed',len(remove),dict(counts),flush=True)
