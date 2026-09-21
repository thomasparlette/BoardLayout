"""Attempt same-layer open connections using DRC endpoints and screened bends.
No width reduction, no net reassignment, and no exemption of clearance errors.
Native refill and DRC must follow; net-tie graphics are checked by native DRC.
"""
from pathlib import Path
import pcbnew as k,re,json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f))
cu=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu];obs=[]
for item in [pd for fp in b.GetFootprints() for pd in fp.Pads()]+list(b.GetTracks()):
 for layer in cu:
  if item.IsOnLayer(layer):obs.append((item.GetNetCode(),layer,item.GetEffectiveShape(layer)))
zones=[z for z in b.Zones() if z.GetIsRuleArea()]
def v(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def clear(shape,net,layer):
 box=shape.BBox();box.Inflate(k.FromMM(.251))
 for n,l,o in obs:
  if n!=net and l==layer and box.Intersects(o.BBox()) and k.SHAPE.Collide(shape,o,k.FromMM(.251)):return False
 for z in zones:
  if z.GetDoNotAllowTracks() and k.SHAPE.Collide(shape,z.Outline(),k.FromMM(.251)):return False
 return True
def layers(desc):
 if 'PTH pad' in desc or 'Via [' in desc:return cu
 return [l for l in cu if 'on '+b.GetLayerName(l) in desc]
added=[]
widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']}
for block in re.split(r'(?=^\[)',(p/'reports/After_routing_DRC.txt').read_text(),flags=re.M):
 if not block.startswith('[unconnected_items]'):continue
 ends=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.+)',block)
 if len(ends)!=2:continue
 name=re.search(r'\[([^]]+)\]',ends[0][2])[1];net=b.FindNet(name)
 # Existing netclass width targets apply, including power nets.
 width=widths.get(name,.25)
 a=tuple(map(float,ends[0][:2]));c=tuple(map(float,ends[1][:2]));choices=[[],[(a[0],c[1])],[(c[0],a[1])]]
 for offset in [-5,-3,-1,1,3,5]:
  choices += [[(a[0]+offset,a[1]),(a[0]+offset,c[1])],[(a[0],a[1]+offset),(c[0],a[1]+offset)]]
 done=False
 for layer in set(layers(ends[0][2])) & set(layers(ends[1][2])):
  for mid in choices:
   pts=[a]+mid+[c]
   if any(not(.6<x<140.33 and .6<y<162.76) for x,y in pts):continue
   shapes=[k.SHAPE_SEGMENT(v(*u),v(*w),k.FromMM(width)) for u,w in zip(pts,pts[1:]) if u!=w]
   if not all(clear(s,net.GetNetCode(),layer) for s in shapes):continue
   for u,w in zip(pts,pts[1:]):
    if u==w:continue
    t=k.PCB_TRACK(b);t.SetStart(v(*u));t.SetEnd(v(*w));t.SetWidth(k.FromMM(width));t.SetLayer(layer);t.SetNetCode(net.GetNetCode());b.Add(t)
   obs.extend((net.GetNetCode(),layer,s) for s in shapes);added.append({'net':name,'layer':b.GetLayerName(layer),'width':width,'points':pts});done=True;break
  if done:break
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
(p/'reports/Short_routes.json').write_text(json.dumps(added,indent=2));print('Added',len(added),'screened endpoint paths')
