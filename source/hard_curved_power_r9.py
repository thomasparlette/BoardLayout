"""Route blocked signals, allowing obstructing track/via removal. Native DRC and subsequent repair of displaced nets are mandatory."""
from pathlib import Path
exec(Path(__file__).with_name('signal_smallvia_r8.py').read_text().split('widths=')[0],globals())
def masks(net,r):
 a=raster(net,r).astype(np.uint8)
 return a,np.zeros_like(a)
from collections import deque
escape_paths={}
def power_seeds(items,blocked,net):
 seeds={};queue=deque();prev={};orig={};dist={}
 for it in items.values():
  layers=[li for li,l in enumerate(cu) if it.IsOnLayer(l)];points=[it.GetPosition()] if not isinstance(it,k.PCB_TRACK) else [it.GetStart(),it.GetEnd()]
  for q in points:
   pt=(mm(q.x),mm(q.y));x,y=round(pt[0]/step),round(pt[1]/step)
   for li in layers:
    if not(0<=x<W and 0<=y<H) or neckblocked[li,y,x]:continue
    node=li*N+y*W+x
    if node in prev:continue
    if not clear(k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(neck)),net,li):continue
    prev[node]=None;orig[node]=pt;dist[node]=0;queue.append(node)
 while queue:
  node=queue.popleft();li=node//N;local=node%N;x=local%W;y=local//W
  if reachable[node] and not blocked[li,y,x]:
   path=[];n=node
   while n is not None:path.append(n);n=prev[n]
   path.reverse();anchor=orig[path[0]];pts=[(path[0]//N,*anchor)]+[(q//N,q%N%W*step,q%N//W*step) for q in path];escape_paths[node]=pts;seeds[node]=(0,anchor)
   # All accepted points belong to the same wide-routing region.
   return seeds
  if dist[node]>=200:continue
  if vfree[y,x]:
   for ll in range(len(cu)):
    n=ll*N+y*W+x
    if n in prev or neckblocked[ll,y,x]:continue
    prev[n]=node;dist[n]=dist[node]+10;queue.append(n)
  for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1),(x-1,y-1),(x+1,y-1),(x-1,y+1),(x+1,y+1)]:
   if not(0<=xx<W and 0<=yy<H) or neckblocked[li,yy,xx]:continue
   n=li*N+yy*W+xx
   if n in prev:continue
   prev[n]=node;dist[n]=dist[node]+1;queue.append(n)
 return seeds

widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']};added=[];failed=[];ripped=[]
historyfile=p/'reports/R9_hard_history.json';history={};pads=[pd for fp in b.GetFootprints() for pd in fp.Pads()]
blocks=re.split(r'(?=^\[)',(p/'reports/After_routing_DRC.txt').read_text(),flags=re.M)
for block in blocks:
 if not block.startswith('[unconnected_items]'):continue
 ends=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.+)',block)
 if len(ends)!=2 or any(': Zone' in d for d in [block]):continue
 name=re.search(r'\[([^]]+)\]',ends[0][2])[1]
 width=widths.get(name,.25)
 if width<=.25 or name=='PGND':continue
 neck=.25 if width<=1 else .6;offsets=[(-.6,-.6),(-.6,.6),(.6,-.6),(.6,.6)] if width>=1.2 else [(0,0)]
 net=b.FindNet(name).GetNetCode();a=tuple(map(float,ends[0][:2]));z=tuple(map(float,ends[1][:2]));b.BuildConnectivity()
 try:ia=island(a,net,end_layers(ends[0][2]));iz=island(z,net,end_layers(ends[1][2]))
 except (AssertionError,ValueError):continue
 if set(ia)&set(iz):continue
 print('NEGOTIATE',name,flush=True)
 blocked,soft=masks(net,width/2+.251);hv,sv=masks(net,.651);vfree=~hv.any(axis=0);vsoft=sv.max(axis=0)
 # No new via-in-pad; preserve spacing from all component drills.
 hi=Image.new('L',(W,H),0);hd=ImageDraw.Draw(hi)
 for pd in pads:
  x,y=mm(pd.GetPosition().x),mm(pd.GetPosition().y);dr=mm(max(pd.GetDrillSize().x,pd.GetDrillSize().y))
  if dr>0:
   rr=dr/2+.2+.251;hd.ellipse((math.floor((x-rr)/step),math.floor((y-rr)/step),math.ceil((x+rr)/step),math.ceil((y+rr)/step)),fill=1)
  elif pd.GetNetCode()==net:
   bb=pd.GetBoundingBox();hd.rectangle((math.floor((mm(bb.GetX())-.4)/step),math.floor((mm(bb.GetY())-.4)/step),math.ceil((mm(bb.GetRight())+.4)/step),math.ceil((mm(bb.GetBottom())+.4)/step)),fill=1)
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA) and t.GetNetCode()==net:
   x,y=mm(t.GetPosition().x),mm(t.GetPosition().y);rr=mm(t.GetDrillValue())/2+.2+.251;hd.ellipse((math.floor((x-rr)/step),math.floor((y-rr)/step),math.ceil((x+rr)/step),math.ceil((y+rr)/step)),fill=1)
 vfree &= ~np.asarray(hi,dtype=bool)
 base=vfree.copy();basecost=vsoft.copy()
 for dx,dy in offsets:
  vfree &= np.roll(np.roll(base,round(dx/step),axis=1),round(dy/step),axis=0)
  vsoft=np.maximum(vsoft,np.roll(np.roll(basecost,round(dx/step),axis=1),round(dy/step),axis=0))
 neckblocked,_=masks(net,neck/2+.251)
 data=struct.pack('<II',W,H)+blocked.astype('uint8').tobytes()+vfree.astype('uint8').tobytes();reachable=np.frombuffer(subprocess.run([str(p/'source/reachable')],input=data,stdout=subprocess.PIPE,check=True).stdout,dtype=np.uint8)
 escape_paths={};starts=power_seeds(ia,blocked,net);goals=power_seeds(iz,blocked,net)
 if not starts or not goals:failed.append((name,'hard escape'));continue
 path=search(starts,goals,blocked,vfree)
 if not path:failed.append((name,'hard search'));continue
 pts=[(n//N,n%N%W*step,n%N//W*step) for n in path];compact=[pts[0]]
 for i in range(1,len(pts)-1):
  u,v,w=pts[i-1:i+2]
  if u[0]==v[0]==w[0] and abs((v[1]-u[1])*(w[2]-v[2])-(v[2]-u[2])*(w[1]-v[1]))<1e-9:continue
  compact.append(v)
 compact.append(pts[-1]);prefixpath=escape_paths[path[0]];suffixpath=list(reversed(escape_paths[path[-1]]));trunkbegin=len(prefixpath);trunkend=trunkbegin+len(compact)-1;compact=prefixpath+compact+suffixpath;pieces=[];okay=True
 for i,(u,v) in enumerate(zip(compact,compact[1:])):
  if u==v:continue
  if u[0]!=v[0]:
   for dx,dy in offsets:
    q=(u[0],u[1]+dx,u[2]+dy);sh=k.SHAPE_CIRCLE(vec(*q[1:]),k.FromMM(.4));okay &= clear(sh,net,None);pieces.append((q,q,sh,None,0))
    for li in [u[0],v[0]]:
     aa=(li,*u[1:]);zz=(li,*q[1:]);sh=k.SHAPE_SEGMENT(vec(*aa[1:]),vec(*zz[1:]),k.FromMM(neck));okay &= clear(sh,net,li)
     if aa!=zz:pieces.append((aa,zz,sh,li,neck))
  else:
   w=neck if i<trunkbegin or i>=trunkend else width;sh=k.SHAPE_SEGMENT(vec(*u[1:]),vec(*v[1:]),k.FromMM(w));okay &= clear(sh,net,u[0]);pieces.append((u,v,sh,u[0],w))
 if not okay:failed.append((name,'native hard geometry'));continue
 # Reject new via drills that overlap one another within this route.
 newvia=[];cleanpieces=[]
 for piece in pieces:
  u,v,sh,li,w=piece
  if li is None:
   if any(math.hypot(u[1]-q[1],u[2]-q[2])<.01 for q in newvia):continue
   if any(math.hypot(u[1]-q[1],u[2]-q[2])<.651 for q in newvia):okay=False;break
   newvia.append(u)
  cleanpieces.append(piece)
 if not okay:failed.append((name,'in-route via spacing'));continue
 pieces=cleanpieces;targets={}
 for u,v,sh,li,w in pieces:
  if li is None:
   t=k.PCB_VIA(b);t.SetPosition(vec(*u[1:]));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
  else:
   t=k.PCB_TRACK(b);t.SetStart(vec(*u[1:]));t.SetEnd(vec(*v[1:]));t.SetWidth(k.FromMM(w));t.SetLayer(cu[li])
  t.SetNetCode(net);b.Add(t);additem(t)
 added.append(name);print('ROUTED',name,'displaced',len(targets),'items',flush=True);k.SaveBoard(str(f),b);historyfile.write_text(json.dumps(history,indent=2))
 if len(added)>=40:break
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R9_hard_curved_power.json').write_text(json.dumps({'added':added,'failed':failed,'displaced_items':ripped},indent=2));print('DONE',len(added),'displaced',len(ripped),flush=True)
