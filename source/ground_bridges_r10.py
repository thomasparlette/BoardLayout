import safe_save_r8
"""Wide power trunks connected to existing conductive islands.
Preserves target widths; uses <=6 mm, 0.8 mm pad-escape stubs and four-via arrays.
Current and thermal qualification is still required.
"""
from pathlib import Path
exec(Path(__file__).with_name('signal_routes_r8.py').read_text().split('widths=')[0],globals())
for fp in b.GetFootprints():
 if fp.GetReference().startswith('NT'):
  x,y=mm(fp.GetPosition().x),mm(fp.GetPosition().y);pdlist=sorted(list(fp.Pads()),key=lambda pd:pd.GetNumber())
  for xmin,xmax,netid in [(x-2,x,pdlist[0].GetNetCode()),(x,x+2,pdlist[1].GetNetCode())]:
   sh=k.SHAPE_POLY_SET();sh.NewOutline()
   for aa,cc in [(xmin,y-1),(xmax,y-1),(xmax,y+1),(xmin,y+1)]:sh.Append(k.FromMM(aa),k.FromMM(cc))
   bb=sh.BBox();obs.append((netid,0,sh,bb))
   for bx in range(bb.GetX()//cell,bb.GetRight()//cell+1):
    for by in range(bb.GetY()//cell,bb.GetBottom()//cell+1):spatial.setdefault((bx,by),[]).append(len(obs)-1)
   drawables.append((netid,0,'rect',(xmin,y-1,xmax,y+1),0))
widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']}
def seeds(items,blocked,net,neck):
 anchors={}
 for it in items.values():
  ls=[i for i,l in enumerate(cu) if it.IsOnLayer(l)];points=[it.GetPosition()]
  if isinstance(it,k.PCB_TRACK):points=[it.GetStart(),it.GetEnd()]
  for point in points:anchors.setdefault((mm(point.x),mm(point.y)),set()).update(ls)
 out={}
 for pt,ls in anchors.items():
  for li in ls:
   for radius in [0,.4,.8,1.2,2,3,4,5,6]:
    found=False
    for ang in [i*math.pi/4 for i in range(8)]:
     x=round((pt[0]+radius*math.cos(ang))/step);y=round((pt[1]+radius*math.sin(ang))/step)
     if not(0<=x<W and 0<=y<H) or blocked[li,y,x]:continue
     if clear(k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(neck)),net,li):out[li*N+y*W+x]=(0,pt);found=True
    if found:break
 return out
added=[];failed=[]
import sys
name=sys.argv[1] if len(sys.argv)>1 else 'PGND';assert name in ['PGND','DGND'];net=b.FindNet(name).GetNetCode()
groups=[r for r in json.loads((p/'reports/Ground_groups_R9.json').read_text())['groups'][name] if r['pads']]
objects={it.m_Uuid.AsString():it for it in list(b.GetTracks())+[pd for fp in b.GetFootprints() for pd in fp.Pads()]}
parent=list(range(len(groups)))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
def combined(i):
 rs=[r for j,r in enumerate(groups) if root(j)==i]
 return {'ids':[u for r in rs for u in r['ids']],'zone_anchors':[a for r in rs for a in r['zone_anchors']],'pads':[a for r in rs for a in r['pads']]}
def group_seeds(g,blocked,net,neck):
 result=seeds({u:objects[u] for u in g['ids'] if u in objects},blocked,net,neck)
 for layer,x,y in g['zone_anchors']:
  li=cu.index(layer);xx=round(x/step);yy=round(y/step)
  if 0<=xx<W and 0<=yy<H and not blocked[li,yy,xx]:result[li*N+yy*W+xx]=(0,(xx*step,yy*step))
 return result
from shapely.geometry import MultiPoint
geoms=[]
for g in groups:
 coords=[a[1:] for a in g['zone_anchors']]+[(mm(objects[u].GetPosition().x),mm(objects[u].GetPosition().y)) for u in g['ids'] if u in objects]
 geoms.append(MultiPoint(coords))
pairs=sorted([(geoms[i].distance(geoms[j]),i,j) for i in range(len(groups)) for j in range(i+1,len(groups))])
for distance,i,j in pairs:
 ra,rz=root(i),root(j)
 if ra==rz:continue
 ga,gz=combined(ra),combined(rz)
 power=lambda g:any(a.startswith(('Q','J')) for a in g['pads'])
 width=4.0 if name=='PGND' and power(ga) and power(gz) else .6;neck=min(width,.6)
 print('GROUND BRIDGE',i,j,'width',width,'separation',distance,flush=True)
 blocked=raster(net,.251+width/2);vfree=~raster(net,1.51 if width>=1.2 else .651).any(axis=0);offsets=[(-.6,-.6),(-.6,.6),(.6,-.6),(.6,.6)] if width>=1.2 else [(0,0)]
 holes=Image.new('1',(W,H),0);hd=ImageDraw.Draw(holes)
 for item in [pd for fp in b.GetFootprints() for pd in fp.Pads()]+[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA)]:
  drill=mm(item.GetDrillValue()) if isinstance(item,k.PCB_VIA) else mm(max(item.GetDrillSize().x,item.GetDrillSize().y))
  if drill<=0:continue
  x,y=mm(item.GetPosition().x),mm(item.GetPosition().y);r=drill/2+.2+.251
  for dx,dy in offsets:hd.ellipse((math.floor((x-dx-r)/step),math.floor((y-dy-r)/step),math.ceil((x-dx+r)/step),math.ceil((y-dy+r)/step)),fill=1)
 vfree &= ~np.asarray(holes,dtype=bool)
 starts=group_seeds(ga,blocked,net,neck);goals=group_seeds(gz,blocked,net,neck)
 if not starts or not goals:failed.append((name,'escape'));continue
 path=search(starts,goals,blocked,vfree)
 if not path:failed.append((name,'search'));continue
 a=starts[path[0]][1];z=goals[path[-1]][1];pts=[(n//N,n%N%W*step,n%N//W*step) for n in path];compact=[pts[0]]
 for i in range(1,len(pts)-1):
  u,v,w=pts[i-1:i+2]
  if u[0]==v[0]==w[0] and abs((v[1]-u[1])*(w[2]-v[2])-(v[2]-u[2])*(w[1]-v[1]))<1e-9:continue
  compact.append(v)
 compact.append(pts[-1]);compact=[(compact[0][0],*a)]+compact+[(compact[-1][0],*z)];pieces=[];okay=True
 for i,(u,v) in enumerate(zip(compact,compact[1:])):
  if u==v:continue
  if u[0]!=v[0]:
   for dx,dy in offsets:
    q=(u[0],u[1]+dx,u[2]+dy);okay &= clear(k.SHAPE_CIRCLE(vec(*q[1:]),k.FromMM(.4)),net,None);pieces.append(('via',q,q,0))
    for l in [u[0],v[0]]:
     aa=(l,*u[1:]);zz=(l,*q[1:]);okay &= clear(k.SHAPE_SEGMENT(vec(*aa[1:]),vec(*zz[1:]),k.FromMM(neck)),net,l)
     if aa!=zz:pieces.append(('track',aa,zz,neck))
  else:
   w=neck if i in [0,len(compact)-2] else width;okay &= clear(k.SHAPE_SEGMENT(vec(*u[1:]),vec(*v[1:]),k.FromMM(w)),net,u[0]);pieces.append(('track',u,v,w))
 if not okay:failed.append((name,'native geometry'));continue
 newvias=[];merged=[]
 for kind,u,v,w in pieces:
  if kind!='via':merged.append((kind,u,v,w));continue
  near=next((q for q in newvias if math.hypot(u[1]-q[1],u[2]-q[2])<.651),None)
  if near is None:newvias.append(u);merged.append((kind,u,v,w));continue
  # Merge same-net through vias; bridge every copper layer conservatively.
  for li in range(len(cu)):
   aa=(li,*u[1:]);zz=(li,*near[1:])
   if aa==zz:continue
   if not clear(k.SHAPE_SEGMENT(vec(*aa[1:]),vec(*zz[1:]),k.FromMM(neck)),net,li):okay=False;break
   merged.append(('track',aa,zz,neck))
 if not okay:failed.append((name,'via merge geometry'));continue
 pieces=merged
 for kind,u,v,w in pieces:
  if kind=='via':
   t=k.PCB_VIA(b);t.SetPosition(vec(*u[1:]));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
  else:
   t=k.PCB_TRACK(b);t.SetStart(vec(*u[1:]));t.SetEnd(vec(*v[1:]));t.SetWidth(k.FromMM(w));t.SetLayer(cu[u[0]])
  t.SetNetCode(net);b.Add(t);additem(t)
 parent[rz]=ra;added.append({'net':name,'trunk_width_mm':width,'stub_width_mm':neck,'pieces':pieces});print('CONNECTED',name,'total',len(added),flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/('reports/Ground_bridges_R10_'+name+'.json')).write_text(json.dumps({'added':added,'failed':failed,'groups_remaining':len({root(i) for i in range(len(groups))}),'ampacity':'UNQUALIFIED'},indent=2));print('DONE GROUND',len(added),'groups',len({root(i) for i in range(len(groups))}),flush=True)
