"""Wide power trunks connected to existing conductive islands.
Preserves target widths; uses <=6 mm, 0.8 mm pad-escape stubs and four-via arrays.
Current and thermal qualification is still required.
"""
from pathlib import Path
if Path("/tmp/pause_power").exists(): raise SystemExit(2)
obowners={}
code=Path(__file__).with_name('circle_routes.py').read_text().split('widths=')[0]
code=code.replace('obs.append((item.GetNetCode(),li,sh,bb))','obs.append((item.GetNetCode(),li,sh,bb));obowners[id(sh)]=item')
exec(code,globals())
widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']}
exec(Path(__file__).with_name('soft_support.py').read_text(),globals())
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
     key=li*N+y*W+x
     if clear(k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(neck)),net,li):
      out[key]=(0,pt);parallel_entries.discard((pt,key));found=True
     elif pt[1]<23 and len(ls)==4 and width<=3 and vfree[y,x] and clear(k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(width/4)),net,None):
      if key not in out:out[key]=(0,pt);parallel_entries.add((pt,key));found=True
    if found and radius>=6:break
 return out
added=[];failed=[]
for block in sorted(re.split(r'(?=^\[)',(p/'reports/After_routing_DRC.txt').read_text(),flags=re.M),key=lambda v:0 if '[INJECTOR_' in v else 1):
 if not block.startswith('[unconnected_items]') or ': Zone ' in block:continue
 ends=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.+)',block)
 if len(ends)!=2:continue
 name=re.search(r'\[([^]]+)\]',ends[0][2])[1];width=widths.get(name,.25)
 if width<1 or name=='PGND':continue
 collect=False;rip_ids=set();parallel_entries=set()
 neck=min(width,.8);net=b.FindNet(name).GetNetCode();a=tuple(map(float,ends[0][:2]));z=tuple(map(float,ends[1][:2]));b.BuildConnectivity();ia=island(a,net);iz=island(z,net)
 if set(ia)&set(iz):continue
 blocked=hard_raster(net,.251+width/2);soft_map=soft_raster(net,.251+width/2);via_soft=soft_raster(net,1.51 if width>=1.2 else .651).sum(axis=0);vfree=~hard_raster(net,1.51 if width>=1.2 else .651).any(axis=0);offsets=[(-.6,-.6),(-.6,.6),(.6,-.6),(.6,.6)] if width>=1.2 else [(0,0)]
 holes=Image.new('1',(W,H),0);hd=ImageDraw.Draw(holes)
 for item in [pd for fp in b.GetFootprints() for pd in fp.Pads()]+[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA)]:
  drill=mm(item.GetDrillValue()) if isinstance(item,k.PCB_VIA) else mm(max(item.GetDrillSize().x,item.GetDrillSize().y))
  if drill<=0:continue
  x,y=mm(item.GetPosition().x),mm(item.GetPosition().y);r=drill/2+.2+.251
  for dx,dy in offsets:hd.ellipse((math.floor((x-dx-r)/step),math.floor((y-dy-r)/step),math.ceil((x-dx+r)/step),math.ceil((y-dy+r)/step)),fill=1)
 vfree &= ~np.asarray(holes,dtype=bool)
 starts=seeds(ia,blocked,net,neck);goals=seeds(iz,blocked,net,neck)
 if not starts or not goals:failed.append((name,'escape'));print('FAILED',name,'escape',len(starts),len(goals),flush=True);continue
 path=search(starts,goals,blocked,vfree)
 if not path:
  failed.append((name,'search'));print('FAILED',name,'search',len(starts),len(goals),flush=True)
  if name=='INJECTOR_1':
   print('SEEDS',list({v[1] for v in starts.values()}),list({v[1] for v in goals.values()}),flush=True)
   np.savez_compressed(p/'reports/injector1_search.npz',blocked=blocked,vfree=vfree,starts=np.array(list(starts)),goals=np.array(list(goals)))
  continue
 a=starts[path[0]][1];z=goals[path[-1]][1];parallel_start=(a,path[0]) in parallel_entries;parallel_end=(z,path[-1]) in parallel_entries;pts=[(n//N,n%N%W*step,n%N//W*step) for n in path];compact=[pts[0]]
 for i in range(1,len(pts)-1):
  u,v,w=pts[i-1:i+2]
  if u[0]==v[0]==w[0] and abs((v[1]-u[1])*(w[2]-v[2])-(v[2]-u[2])*(w[1]-v[1]))<1e-9:continue
  compact.append(v)
 compact.append(pts[-1]);compact=[(compact[0][0],*a)]+compact+[(compact[-1][0],*z)];pieces=[];okay=True
 collect=True;rip_ids=set()
 for i,(u,v) in enumerate(zip(compact,compact[1:])):
  if u==v:continue
  if (i==0 and parallel_start) or (i==len(compact)-2 and parallel_end):
   ww=width/4;center=v if i==0 else u
   for ll in range(4):
    aa=(ll,*u[1:]);zz=(ll,*v[1:]);okay &= clear(k.SHAPE_SEGMENT(vec(*aa[1:]),vec(*zz[1:]),k.FromMM(ww)),net,ll);pieces.append(('track',aa,zz,ww))
    for dx,dy in offsets:
     aa=(ll,*center[1:]);zz=(ll,center[1]+dx,center[2]+dy)
     if aa!=zz:okay &= clear(k.SHAPE_SEGMENT(vec(*aa[1:]),vec(*zz[1:]),k.FromMM(ww)),net,ll);pieces.append(('track',aa,zz,ww))
   for dx,dy in offsets:
    q=(center[0],center[1]+dx,center[2]+dy);okay &= clear(k.SHAPE_CIRCLE(vec(*q[1:]),k.FromMM(.4)),net,None);pieces.append(('via',q,q,0))
  elif u[0]!=v[0]:
   for dx,dy in offsets:
    q=(u[0],u[1]+dx,u[2]+dy);okay &= clear(k.SHAPE_CIRCLE(vec(*q[1:]),k.FromMM(.4)),net,None);pieces.append(('via',q,q,0))
    for l in [u[0],v[0]]:
     aa=(l,*u[1:]);zz=(l,*q[1:]);okay &= clear(k.SHAPE_SEGMENT(vec(*aa[1:]),vec(*zz[1:]),k.FromMM(neck)),net,l)
     if aa!=zz:pieces.append(('track',aa,zz,neck))
  else:
   w=neck if i in [0,len(compact)-2] else width;okay &= clear(k.SHAPE_SEGMENT(vec(*u[1:]),vec(*v[1:]),k.FromMM(w)),net,u[0]);pieces.append(('track',u,v,w))
 if not okay:failed.append((name,'native geometry'));print('FAILED',name,'native geometry',flush=True);continue
 for kind,u,v,w in pieces:
  if kind=='via':
   t=k.PCB_VIA(b);t.SetPosition(vec(*u[1:]));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
  else:
   t=k.PCB_TRACK(b);t.SetStart(vec(*u[1:]));t.SetEnd(vec(*v[1:]));t.SetWidth(k.FromMM(w));t.SetLayer(cu[u[0]])
  t.SetNetCode(net);b.Add(t);additem(t)
 save_ripup(name,width,neck,pieces)
 raise SystemExit(0)
print('NO ROUTE',failed,flush=True)
raise SystemExit(2)
