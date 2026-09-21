import safe_save_r8
from pathlib import Path
import pcbnew as k,json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));b.BuildConnectivity();cn=b.GetConnectivity();power={n for c in json.load(open(p/'reports/Routing_targets.json'))['widths'].values() if c['width_mm']>.25 for n in c['nets']};removed=[]
for t in list(b.GetTracks()):
 if not isinstance(t,k.PCB_VIA) or t.IsLocked() or t.GetNetname() in power:continue
 if list(cn.GetConnectedPads(t)):continue
 other=[o for o in cn.GetConnectedTracks(t) if o.m_Uuid!=t.m_Uuid]
 if any(isinstance(o,k.PCB_VIA) for o in other):continue
 if len({o.GetLayer() for o in other})>1:continue
 if not all(k.SHAPE.Collide(o.GetEffectiveShape(o.GetLayer()),k.SHAPE_CIRCLE(t.GetPosition(),1),0) for o in other):continue
 removed.append(t)
for t in removed:b.Delete(t)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);print('Removed',len(removed),'redundant signal vias')
