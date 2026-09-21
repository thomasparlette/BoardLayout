from pathlib import Path
import safe_save_r8
import pcbnew as k,json,collections,math
from shapely.geometry import Polygon,Point,LineString,box
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));cu=[0,1,2,3,4,5,6,31];mm=k.ToMM
allreports={};removed=[];padrefs={pd.m_Uuid.AsString():fp.GetReference() for fp in b.GetFootprints() for pd in fp.Pads()}
for netname in ['PGND','DGND']:
 net=b.FindNet(netname).GetNetCode();objects={};shapes=[];parent={};cell=4;bucket=collections.defaultdict(list)
 def root(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 def add(uid,obj,layer,shape):
  objects[uid]=obj;parent.setdefault(uid,uid)
  if obj is None:
   out=shape.Outline(0);coords=[(mm(out.CPoint(j).x),mm(out.CPoint(j).y)) for j in range(out.PointCount())];holes=[]
   for h in range(shape.HoleCount(0)):
    q=shape.Hole(0,h);holes.append([(mm(q.CPoint(j).x),mm(q.CPoint(j).y)) for j in range(q.PointCount())])
   geom=Polygon(coords,holes).buffer(0)
  elif isinstance(obj,k.PCB_TRACK):
   a=(mm(obj.GetStart().x),mm(obj.GetStart().y));z=(mm(obj.GetEnd().x),mm(obj.GetEnd().y))
   geom=(Point(a) if isinstance(obj,k.PCB_VIA) or a==z else LineString([a,z])).buffer(mm(obj.GetWidth())/2,quad_segs=24)
  else:
   bb=shape.BBox();coords=(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))
   geom=Point(mm(obj.GetPosition().x),mm(obj.GetPosition().y)).buffer(mm(obj.GetSize().x)/2,quad_segs=24) if obj.GetShape()==k.PAD_SHAPE_CIRCLE else box(*coords)
  x,y,xx,yy=geom.bounds;keys=[(layer,a,c) for a in range(math.floor(x/cell),math.floor(xx/cell)+1) for c in range(math.floor(y/cell),math.floor(yy/cell)+1)]
  candidates={i for key in keys for i in bucket[key]}
  for i in candidates:
   other,g,_=shapes[i]
   if root(uid)==root(other):continue
   if geom.intersects(g):parent[root(uid)]=root(other)
  ix=len(shapes);shapes.append((uid,geom,layer))
  for key in keys:bucket[key].append(ix)
 for fp in b.GetFootprints():
  for pd in fp.Pads():
   if pd.GetNetCode()!=net:continue
   for layer in cu:
    if pd.IsOnLayer(layer):add(pd.m_Uuid.AsString(),pd,layer,pd.GetEffectiveShape(layer))
 for t in b.GetTracks():
  if t.GetNetCode()!=net:continue
  for layer in cu:
   if t.IsOnLayer(layer):add(t.m_Uuid.AsString(),t,layer,t.GetEffectiveShape(layer))
 for z in b.Zones():
  if z.GetIsRuleArea() or z.GetNetCode()!=net:continue
  ps=z.GetFilledPolysList(z.GetLayer())
  for i in range(ps.OutlineCount()):add(z.m_Uuid.AsString()+':'+str(i),None,z.GetLayer(),ps.UnitSet(i))
 groups=collections.defaultdict(list)
 for uid in objects:groups[root(uid)].append(uid)
 reports=[]
 for ids in groups.values():
  pads=[objects[u] for u in ids if isinstance(objects[u],k.PAD)];tracks=[objects[u] for u in ids if isinstance(objects[u],k.PCB_TRACK)]
  record={'pads':[padrefs[pd.m_Uuid.AsString()]+'.'+pd.GetNumber() for pd in pads],'copper_items':len(tracks),'polygons':sum(objects[u] is None for u in ids),'anchors':[[mm(t.GetPosition().x),mm(t.GetPosition().y)] for t in tracks[:4]]}
  record['ids']=ids;record['zone_anchors']=[]
  for uid,geom,layer in shapes:
   if uid not in ids or objects[uid] is not None:continue
   inset=geom.buffer(-.1)
   if inset.is_empty:continue
   x,y,xx,yy=inset.bounds;rp=inset.representative_point();record['zone_anchors'].append([layer,round(rp.x,1),round(rp.y,1)])
   for a in range(math.ceil(x/2),math.floor(xx/2)+1):
    for c in range(math.ceil(y/2),math.floor(yy/2)+1):
     if inset.contains(Point(a*2,c*2)):record['zone_anchors'].append([layer,a*2,c*2])
  reports.append(record)
  if not pads:
   for t in tracks:removed.append({'net':netname,'uuid':t.m_Uuid.AsString()});b.Delete(t)
 allreports[netname]=reports
 print(netname,len(groups),'groups',[(r['pads'],len(r['zone_anchors'])) for r in reports],flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/Ground_groups_R9.json').write_text(json.dumps({'groups':allreports,'removed_padless_items':removed},indent=2))
