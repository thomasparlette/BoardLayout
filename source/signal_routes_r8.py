"""Supplementary signal router. Four-layer grid search, native geometry screening.
Power nets are excluded; no new high-current paths or ratings are implied.
"""
from pathlib import Path
import pcbnew as k, numpy as np
from PIL import Image,ImageDraw
import re,json,heapq,math,time,subprocess,struct
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));cu=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.In5_Cu,k.In6_Cu,k.B_Cu]
powernames={n for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() if c['width_mm']>.25 for n in c['nets']}
powercodes={b.FindNet(n).GetNetCode() for n in powernames if b.FindNet(n)}
step=.1;W=1410;H=1634;N=W*H;obs=[];drawables=[];spatial={};cell=2000000
def mm(v):return k.ToMM(v)
def vec(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def additem(item):
 for li,l in enumerate(cu):
  if not item.IsOnLayer(l):continue
  sh=item.GetEffectiveShape(l);bb=sh.BBox();obs.append((item.GetNetCode(),li,sh,bb))
  for bx in range(bb.GetX()//cell,bb.GetRight()//cell+1):
   for by in range(bb.GetY()//cell,bb.GetBottom()//cell+1):spatial.setdefault((bx,by),[]).append(len(obs)-1)
  if isinstance(item,k.PCB_TRACK) and not isinstance(item,k.PCB_VIA):
   drawables.append((item.GetNetCode(),li,'line',(mm(item.GetStart().x),mm(item.GetStart().y),mm(item.GetEnd().x),mm(item.GetEnd().y)),mm(item.GetWidth())))
  else:
   kind='ellipse' if isinstance(item,k.PCB_VIA) or (isinstance(item,k.PAD) and item.GetShape()==k.PAD_SHAPE_CIRCLE) else 'rect'
   drawables.append((item.GetNetCode(),li,kind,(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())),0))
for fp in b.GetFootprints():
 for pd in fp.Pads():additem(pd)
for t in b.GetTracks():additem(t)
keep=[]
for z in b.Zones():
 if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
  bb=z.Outline().BBox();keep.append((mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))

def clear(shape,net,li):
 bb=shape.BBox();bb.Inflate(k.FromMM(.251))
 indices=set()
 for bx in range(bb.GetX()//cell,bb.GetRight()//cell+1):
  for by in range(bb.GetY()//cell,bb.GetBottom()//cell+1):indices.update(spatial.get((bx,by),[]))
 for ix in indices:
  n,l,o,box=obs[ix]
  if n!=net and (li is None or l==li) and bb.Intersects(box) and k.SHAPE.Collide(shape,o,k.FromMM(.251 if net in powercodes or n in powercodes else .201)):return False
 for z in b.Zones():
  if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()) and k.SHAPE.Collide(shape,z.Outline(),k.FromMM(.251)):return False
 return True
def raster(net,r):
 ims=[Image.new('1',(W,H),0) for _ in cu];ds=[ImageDraw.Draw(i) for i in ims]
 for n,l,kind,coords,width in drawables:
  if n==net:continue
  d=ds[l];x,y,xx,yy=coords;rr=r+(.05 if n in powercodes and net not in powercodes else 0)
  if kind in ['rect','ellipse']:
   method=d.ellipse if kind=='ellipse' else d.rectangle
   method((math.floor((x-rr)/step),math.floor((y-rr)/step),math.ceil((xx+rr)/step),math.ceil((yy+rr)/step)),fill=1)
  else:
   rad=width/2+rr;d.line((round(x/step),round(y/step),round(xx/step),round(yy/step)),fill=1,width=math.ceil(2*rad/step)+1)
   for a,c in [(x,y),(xx,yy)]:d.ellipse((math.floor((a-rad)/step),math.floor((c-rad)/step),math.ceil((a+rad)/step),math.ceil((c+rad)/step)),fill=1)
 for d in ds:
  for x,y,xx,yy in keep:d.rectangle((math.floor((x-r)/step),math.floor((y-r)/step),math.ceil((xx+r)/step),math.ceil((yy+r)/step)),fill=1)
  d.rectangle((0,0,W-1,H-1),outline=1,width=math.ceil((r+.3)/step)+1)
 return np.stack([np.asarray(i,dtype=bool) for i in ims])
def end_layers(desc):
 if 'PTH pad' in desc or 'Via [' in desc:return list(range(len(cu)))
 return [i for i,l in enumerate(cu) if 'on '+b.GetLayerName(l) in desc]
def island(pt,net,layers=None):
 items=[pd for fp in b.GetFootprints() for pd in fp.Pads() if pd.GetNetCode()==net]+[t for t in b.GetTracks() if t.GetNetCode()==net]
 if layers is not None:items=[it for it in items if any(it.IsOnLayer(cu[li]) for li in layers)]
 def distance(it):
  points=[it.GetPosition()]
  if isinstance(it,k.PCB_TRACK):points=[it.GetStart(),it.GetEnd()]
  return min(math.hypot(mm(q.x)-pt[0],mm(q.y)-pt[1]) for q in points)
 first=min(items,key=distance);assert distance(first)<.001,(pt,distance(first))
 conn=b.GetConnectivity();seen={};todo=[first]
 while todo:
  it=todo.pop();uid=it.m_Uuid.AsString()
  if uid in seen:continue
  seen[uid]=it
  todo.extend(x for x in list(conn.GetConnectedTracks(it))+list(conn.GetConnectedPads(it)) if x.GetNetCode()==net and x.m_Uuid.AsString() not in seen)
 return seen
def island_seeds(items,blocked,net):
 seeds={}
 for it in items.values():
  ls=[li for li,l in enumerate(cu) if it.IsOnLayer(l)];anchors=[(mm(it.GetPosition().x),mm(it.GetPosition().y))]
  if isinstance(it,k.PCB_TRACK):
   a=(mm(it.GetStart().x),mm(it.GetStart().y));z=(mm(it.GetEnd().x),mm(it.GetEnd().y));length=math.dist(a,z);steps=max(1,math.ceil(length/3));anchors=[(a[0]+(z[0]-a[0])*j/steps,a[1]+(z[1]-a[1])*j/steps) for j in range(steps+1)]
  for pt in anchors:
   cx,cy=round(pt[0]/step),round(pt[1]/step)
   for li in ls:
    for dx,dy in [(0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
     x,y=cx+dx,cy+dy
     if not(0<=x<W and 0<=y<H) or blocked[li,y,x]:continue
     sh=k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(.2))
     if clear(sh,net,li):seeds[li*N+y*W+x]=(0,pt)
 return seeds
def candidates(pt,ls,blocked,net):
 cx,cy=round(pt[0]/step),round(pt[1]/step);out={}
 for li in ls:
  for dx,dy in {(round(rad*math.cos(ang)/step),round(rad*math.sin(ang)/step)) for rad in [0,.2,.4,.6,.8,1,1.4,1.8,2.2,3,4,5] for ang in [i*math.pi/8 for i in range(16)]}:
    x,y=cx+dx,cy+dy
    if not (0<=x<W and 0<=y<H) or blocked[li,y,x]:continue
    q=(x*step,y*step);sh=k.SHAPE_SEGMENT(vec(*pt),vec(*q),k.FromMM(.2))
    if clear(sh,net,li):out[li*N+y*W+x]=(math.hypot(q[0]-pt[0],q[1]-pt[1])/step,q)
 return out
def search(starts,goals,blocked,vfree):
 data=struct.pack('<IIII',W,H,len(starts),len(goals))+blocked.astype('uint8').tobytes()+vfree.astype('uint8').tobytes()+np.array(list(starts),dtype='<u4').tobytes()+np.array(list(goals),dtype='<u4').tobytes()
 result=subprocess.run([str(p/'source/astar')],input=data,stdout=subprocess.PIPE,check=True).stdout
 size=struct.unpack('<I',result[:4])[0]
 return np.frombuffer(result[4:],dtype='<u4').astype(int).tolist() if size else None
 # The Python implementation is retained below for algorithm provenance.
 target=list(goals);gx=sum(i%N%W for i in target)/len(target);gy=sum(i%N//W for i in target)/len(target)
 def heur(idx):return max(0,abs(idx%N%W-gx)+abs(idx%N//W-gy)-15)
 heap=[];dist={};prev={};closed=set();flat=blocked.reshape(-1)
 for n,(cost,_) in starts.items():dist[n]=cost;prev[n]=None;heapq.heappush(heap,(cost+heur(n),cost,n))
 until=time.monotonic()+8
 while heap:
  _,cost,n=heapq.heappop(heap)
  if n in closed:continue
  if n in goals:
   path=[]
   while n is not None:path.append(n);n=prev[n]
   return path[::-1]
  closed.add(n)
  if len(closed)%4096==0 and time.monotonic()>until:return None
  li=n//N;y=n%N//W;x=n%W
  ns=[]
  if x>0:ns.append((n-1,1))
  if x<W-1:ns.append((n+1,1))
  if y>0:ns.append((n-W,1))
  if y<H-1:ns.append((n+W,1))
  if vfree[y,x]:ns.extend((l*N+y*W+x,25) for l in range(4) if l!=li)
  for q,w in ns:
   if flat[q] or q in closed:continue
   c=cost+w
   if c<dist.get(q,1e30):dist[q]=c;prev[q]=n;heapq.heappush(heap,(c+1.05*heur(q),c,q))
 return None
widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']}
added=[];fails=[]
blocks=re.split(r'(?=^\[)',(p/'reports/After_routing_DRC.txt').read_text(),flags=re.M)
for count,block in enumerate(blocks):
 if not block.startswith('[unconnected_items]'):continue
 ends=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.+)',block)
 if len(ends)!=2:continue
 name=re.search(r'\[([^]]+)\]',ends[0][2])[1]
 if widths.get(name,.25)>.25:continue
 print('TRY',name,flush=True)
 net=b.FindNet(name).GetNetCode();a=tuple(map(float,ends[0][:2]));z=tuple(map(float,ends[1][:2]));blocked=raster(net,.301);vfree=~raster(net,.601).any(axis=0)
 holes=Image.new('1',(W,H),0);hd=ImageDraw.Draw(holes)
 for item in [pd for fp in b.GetFootprints() for pd in fp.Pads()]+[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA)]:
  drill=mm(item.GetDrillValue()) if isinstance(item,k.PCB_VIA) else mm(max(item.GetDrillSize().x,item.GetDrillSize().y))
  if drill<=0:continue
  x,y=mm(item.GetPosition().x),mm(item.GetPosition().y);r=drill/2+.2+.251
  hd.ellipse((math.floor((x-r)/step),math.floor((y-r)/step),math.ceil((x+r)/step),math.ceil((y+r)/step)),fill=1)
 vfree &= ~np.asarray(holes,dtype=bool)
 b.BuildConnectivity();ia=island(a,net,end_layers(ends[0][2]));iz=island(z,net,end_layers(ends[1][2]))
 if set(ia)&set(iz):continue
 starts=island_seeds(ia,blocked,net);goals=island_seeds(iz,blocked,net)
 for pt,ls,dest in [(a,end_layers(ends[0][2]),starts),(z,end_layers(ends[1][2]),goals)]:
  for key,(cost,_) in candidates(pt,ls,blocked,net).items():dest.setdefault(key,(cost,pt))
 if not starts or not goals:fails.append((name,'escape'));continue
 path=search(starts,goals,blocked,vfree)
 if not path:fails.append((name,'search'));continue
 a=starts[path[0]][1];z=goals[path[-1]][1]
 points=[(n//N,(n%N%W)*step,(n%N//W)*step) for n in path]
 # Collapse straight runs without changing the path.
 compact=[points[0]]
 for i in range(1,len(points)-1):
  u,v,w=points[i-1:i+2]
  if u[0]==v[0]==w[0] and abs((v[1]-u[1])*(w[2]-v[2])-(v[2]-u[2])*(w[1]-v[1]))<1e-9:continue
  compact.append(v)
 compact.append(points[-1]);compact=[(compact[0][0],*a)]+compact+[(compact[-1][0],*z)]
 pieces=[];okay=True
 for u,v in zip(compact,compact[1:]):
  if u==v:continue
  if u[0]!=v[0]:
   sh=k.SHAPE_CIRCLE(vec(*u[1:]),k.FromMM(.4));okay &= clear(sh,net,None);pieces.append(('via',u,v))
  else:
   sh=k.SHAPE_SEGMENT(vec(*u[1:]),vec(*v[1:]),k.FromMM(.2));okay &= clear(sh,net,u[0]);pieces.append(('track',u,v))
 if not okay:fails.append((name,'native geometry'));continue
 for kind,u,v in pieces:
  if kind=='via':
   t=k.PCB_VIA(b);t.SetPosition(vec(*u[1:]));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
  else:
   t=k.PCB_TRACK(b);t.SetStart(vec(*u[1:]));t.SetEnd(vec(*v[1:]));t.SetWidth(k.FromMM(.2));t.SetLayer(cu[u[0]])
  t.SetNetCode(net);b.Add(t);additem(t)
 added.append(name);print('CONNECTED',name,'total',len(added),flush=True);k.SaveBoard(str(f),b)
 if len(added)%10==0:k.SaveBoard(str(f),b)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
(p/'reports/R8_signal_routes.json').write_text(json.dumps({'added':added,'failed':fails},indent=2));print('FINISHED',len(added),len(fails),flush=True)
