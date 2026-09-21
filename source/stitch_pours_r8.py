"""Join overlapping ground-pour pieces with screened through vias. Not an ampacity certification."""
from pathlib import Path
import pcbnew as k,json,math
from shapely.geometry import Polygon,Point,LineString,box
from shapely.strtree import STRtree
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));mm=k.ToMM
cu=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]
def poly(ps,i):
 o=ps.Outline(i);outer=[(mm(o.CPoint(j).x),mm(o.CPoint(j).y)) for j in range(o.PointCount())];holes=[]
 for n in range(ps.HoleCount(i)):
  h=ps.Hole(i,n);holes.append([(mm(h.CPoint(j).x),mm(h.CPoint(j).y)) for j in range(h.PointCount())])
 return Polygon(outer,holes).buffer(0)
added=[]
for name in ['PGND','DGND']:
 net=b.FindNet(name).GetNetCode();polys=[]
 for z in b.Zones():
  if z.GetIsRuleArea() or z.GetNetCode()!=net:continue
  ps=z.GetFilledPolysList(z.GetLayer())
  for i in range(ps.OutlineCount()):
   q=poly(ps,i)
   if q.area>.05:polys.append((z.GetLayer(),q))
 forbidden=[]
 for pd in [d for fp in b.GetFootprints() for d in fp.Pads()]:
  if pd.GetNetCode()!=net:
   bb=pd.GetBoundingBox();forbidden.append(box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())).buffer(.652))
  drill=max(pd.GetDrillSize().x,pd.GetDrillSize().y)
  if drill:forbidden.append(Point(mm(pd.GetPosition().x),mm(pd.GetPosition().y)).buffer(mm(drill)/2+.452))
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):
   rad=mm(t.GetWidth())/2+.652 if t.GetNetCode()!=net else mm(t.GetDrillValue())/2+.452
   forbidden.append(Point(mm(t.GetPosition().x),mm(t.GetPosition().y)).buffer(rad))
  elif t.GetNetCode()!=net:
   forbidden.append(LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2+.652))
 for z in b.Zones():
  if z.GetIsRuleArea() and z.GetDoNotAllowVias():
   for i in range(z.Outline().OutlineCount()):forbidden.append(poly(z.Outline(),i).buffer(.652))
 tree=STRtree(forbidden);placed=[]
 def safe(q):
  if not(.901<q.x<140.029 and .901<q.y<162.459):return False
  if any(forbidden[int(i)].intersects(q) for i in tree.query(q)):return False
  if any(q.distance(t)<.66 for t in placed):return False
  return True
 # One or two vias per polygon overlap; exact connectivity checked after refill.
 for i,(layer,a) in enumerate(polys):
  found=0
  others=[q for l,q in polys if l!=layer and q.intersects(a)]
  for other in sorted(others,key=lambda q:q.intersection(a).area,reverse=True):
   overlap=a.intersection(other).buffer(-.08)
   if overlap.is_empty:continue
   center=overlap.representative_point();x,y,xx,yy=overlap.bounds
   points=[center]
   points += [Point(u/2,v/2) for u in range(math.ceil(x*2),math.floor(xx*2)+1) for v in range(math.ceil(y*2),math.floor(yy*2)+1)]
   points.sort(key=lambda t:t.distance(center))
   for q in points:
    if not overlap.contains(q) or not safe(q):continue
    via=k.PCB_VIA(b);via.SetPosition(k.VECTOR2I(k.FromMM(q.x),k.FromMM(q.y)));via.SetWidth(k.FromMM(.8));via.SetDrill(k.FromMM(.4));via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNetCode(net);b.Add(via)
    placed.append(q);added.append({'net':name,'x':q.x,'y':q.y,'polygon':i});found+=1
    if found>=2:break
   if found>=2:break
 print(name,'polygons',len(polys),'added',len(placed),flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
(p/'reports/R8_pour_stitching.json').write_text(json.dumps({'vias':added,'via_mm':[.8,.4],'status':'Connectivity stitching only; aggregate current and thermal qualification remains open'},indent=2))
