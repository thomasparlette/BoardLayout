import safe_save_r8
from pathlib import Path
import pcbnew as k,json,collections
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));b.BuildConnectivity();conn=b.GetConnectivity();zone_nets={z.GetNetCode() for z in b.Zones() if not z.GetIsRuleArea()};seen=set();removed=[];counts=collections.Counter()
for first in list(b.GetTracks()):
 uid=first.m_Uuid.AsString()
 if uid in seen or first.GetNetCode() in zone_nets:continue
 todo=[first];group=[];haspad=False;net=first.GetNetCode()
 while todo:
  it=todo.pop();u=it.m_Uuid.AsString()
  if u in seen:continue
  seen.add(u);group.append(it)
  if any(pd.GetNetCode()==net for pd in conn.GetConnectedPads(it)):haspad=True
  todo.extend(t for t in conn.GetConnectedTracks(it) if t.GetNetCode()==net and t.m_Uuid.AsString() not in seen)
 if not haspad:
  removed.extend(group);counts[first.GetNetname()]+=len(group)
for t in removed:b.Delete(t)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
(p/'reports/R8_floating_copper_removed.json').write_text(json.dumps({'removed_items':len(removed),'by_net':dict(counts),'rule':'Only conductive components with no connected pad, on nets without copper zones. No pad net assignments changed.'},indent=2));print(len(removed),dict(counts),flush=True)
