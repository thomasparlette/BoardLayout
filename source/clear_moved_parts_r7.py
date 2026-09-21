from pathlib import Path
import pcbnew as k,re,json,math
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));r=(p/'reports/After_routing_DRC.txt').read_text();targets=[]
for block in re.split(r'(?=^\[)',r,flags=re.M):
 if not block.startswith(('[clearance]','[hole_clearance]','[hole_near_hole]','[solder_mask_bridge]','[copper_edge_clearance]')):continue
 for m in re.finditer(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (Track|Via) \[([^]]+)\]',block):targets.append((float(m[1]),float(m[2]),m[3],m[4]))
removed=0
for t in list(b.GetTracks()):
 kind='Via' if isinstance(t,k.PCB_VIA) else 'Track'
 if any(kind==q and t.GetNetname()==n and min(math.hypot(k.ToMM(t.GetStart().x)-x,k.ToMM(t.GetStart().y)-y),math.hypot(k.ToMM(t.GetEnd().x)-x,k.ToMM(t.GetEnd().y)-y))<.0002 for x,y,q,n in targets):b.Delete(t);removed+=1
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);print('Removed',removed,'collision segments/vias; rerouting required')
