import safe_save_r8
from pathlib import Path
import pcbnew as k,json,collections
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));j=json.load(open(p/'reports/R10_priority_rail.json'));power={n for c in json.load(open(p/'reports/Routing_targets.json'))['widths'].values() if c['width_mm']>.25 for n in c['nets']};needed={r['uuid'] for r in j['displaced_items'] if r['net'] in power};found={}
for path in [p.parent/'GrandMarquis97_Layout_R10_manual/GrandMarquis97_RevA.kicad_pcb',p.parent/'GrandMarquis97_Layout_R9/GrandMarquis97_RevA.kicad_pcb']:
 old=k.LoadBoard(str(path))
 for t in old.GetTracks():
  if t.m_Uuid.AsString() in needed and t.m_Uuid.AsString() not in found:found[t.m_Uuid.AsString()]=t.Duplicate()
print('Missing source IDs requiring width-preserving repair:',needed-set(found))
remove={}
for t in found.values():
 for o in b.GetTracks():
  if o.GetNetname()==t.GetNetname():continue
  for l in [0,1,2,3,4,5,6,31]:
   if t.IsOnLayer(l) and o.IsOnLayer(l) and k.SHAPE.Collide(t.GetEffectiveShape(l),o.GetEffectiveShape(l),k.FromMM(.251)):
    assert o.GetNetname()=='VCC_5' and not o.IsLocked(),o.GetNetname()
    remove[o.m_Uuid.AsString()]=o;break
for o in remove.values():b.Delete(o)
for t in found.values():t.SetNetCode(b.FindNet(t.GetNetname()).GetNetCode());b.Add(t)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
print('Restored',len(found),'power segments; removed',len(remove),'rail pieces')
