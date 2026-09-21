import safe_save_r8
from pathlib import Path
import pcbnew as k,re,json,math
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));r=(p/'reports/After_routing_DRC.txt').read_text();removed=[]
widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']}
tracks=list(b.GetTracks());dead=set()
for block in re.split(r'(?=^\[)',r,flags=re.M):
 if not block.startswith(('[clearance]','[hole_clearance]','[hole_near_hole]','[copper_edge_clearance]')):continue
 candidates=[]
 for m in re.finditer(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (Track|Via) \[([^]]+)\]',block):
  x,y,q,n=float(m[1]),float(m[2]),m[3],m[4]
  for t in tracks:
   uid=t.m_Uuid.AsString()
   if t.GetNetname()!=n or ('Via' if isinstance(t,k.PCB_VIA) else 'Track')!=q:continue
   if min(math.hypot(k.ToMM(v.x)-x,k.ToMM(v.y)-y) for v in [t.GetStart(),t.GetEnd()])<.0002:candidates.append((widths.get(n,.25),uid,t))
 if any(uid in dead for w,uid,t in candidates):continue
 if candidates:
  w,uid,t=min(candidates,key=lambda c:c[0]);dead.add(uid);removed.append({'net':t.GetNetname(),'uuid':uid});
for t in tracks:
 if t.m_Uuid.AsString() in dead:b.Delete(t)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R8_collision_cleanup.json').write_text(json.dumps(removed,indent=2));print('removed',len(removed))
