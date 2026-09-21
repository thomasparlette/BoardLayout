import safe_save_r8
"""Trim unused dangling branches back to their first pad, plane, or branch junction."""
from pathlib import Path
import pcbnew as k,re,math,json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));conn=b.GetConnectivity();tracks=list(b.GetTracks());report=(p/'reports/After_routing_DRC.txt').read_text();removed={};lookup={t.m_Uuid.AsString():t for t in tracks};zones=[z for z in b.Zones() if not z.GetIsRuleArea()]
def uid(t):return t.m_Uuid.AsString()
def same(a,c):return abs(a.x-c.x)<100 and abs(a.y-c.y)<100
def on(shape,pt,r):return k.SHAPE.Collide(shape,k.SHAPE_CIRCLE(pt,r),0)
def zone_at(it,pt):
 for z in zones:
  if z.GetNetCode()==it.GetNetCode() and it.IsOnLayer(z.GetLayer()) and z.GetFilledPolysList(z.GetLayer()).Contains(pt):return True
 return False
def neighbors(it,pt):
 out=[]
 for t in conn.GetConnectedTracks(it):
  if uid(t)==uid(it) or uid(t) in removed:continue
  if t.GetNetCode()!=it.GetNetCode():continue
  if isinstance(t,k.PCB_VIA) or isinstance(it,k.PCB_VIA):layer=it.GetLayer() if not isinstance(it,k.PCB_VIA) else t.GetLayer()
  else:
   if t.GetLayer()!=it.GetLayer():continue
   layer=it.GetLayer()
  if on(t.GetEffectiveShape(layer),pt,max(1,it.GetWidth()//2)):out.append(t)
 return out
def anchored(it,pt):
 if zone_at(it,pt):return True
 for pd in conn.GetConnectedPads(it):
  if pd.GetNetCode()==it.GetNetCode() and (isinstance(it,k.PCB_VIA) or pd.IsOnLayer(it.GetLayer())) and pd.HitTest(pt,max(1,it.GetWidth()//2)):return True
 return False
power={n for c in json.load(open(p/'reports/Routing_targets.json'))['widths'].values() if c['width_mm']>.25 for n in c['nets']}
starts=[t for t in tracks if not isinstance(t,k.PCB_VIA) and not t.IsLocked() and t.GetNetname() not in power]
for t in starts:
 if uid(t) in removed:continue
 free=[q for q in [t.GetStart(),t.GetEnd()] if not anchored(t,q) and not neighbors(t,q)]
 if not free:continue
 end=free[0]
 while True:
  if uid(t) in removed:break
  other=t.GetEnd() if same(end,t.GetStart()) else t.GetStart()
  endpoint_neighbors={uid(q) for q in neighbors(t,other)}
  if any(uid(q) not in removed and uid(q) not in endpoint_neighbors and uid(q)!=uid(t) for q in conn.GetConnectedTracks(t)):break
  if any(not pd.HitTest(other,max(1,t.GetWidth()//2)) for pd in conn.GetConnectedPads(t)):break
  removed[uid(t)]=t
  if anchored(t,other):break
  ns=neighbors(t,other)
  if len(ns)!=1 or isinstance(ns[0],k.PCB_VIA):break
  nt=ns[0]
  if not(same(other,nt.GetStart()) or same(other,nt.GetEnd())):break
  t=nt;end=other
for t in removed.values():b.Delete(t)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R10_all_signal_stub_pruning.json').write_text(json.dumps({'removed_segments':len(removed),'starting_warnings':len(starts)},indent=2));print('Trimmed',len(removed),'segments from',len(starts),'dangling branches')
