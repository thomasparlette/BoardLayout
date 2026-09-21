"""Wide power trunks connected to existing conductive islands.
Preserves target widths; uses <=6 mm, 0.8 mm pad-escape stubs and four-via arrays.
Current and thermal qualification is still required.
"""
from pathlib import Path
exec(Path(__file__).with_name('circle_routes.py').read_text().split('widths=')[0],globals())
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
for block in re.split(r'(?=^\[)',(p/'reports/After_routing_DRC.txt').read_text(),flags=re.M):
 if not block.startswith('[unconnected_items]') or ': Zone ' in block:continue
 ends=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.+)',block)
 if len(ends)!=2:continue
 name=re.search(r'\[([^]]+)\]',ends[0][2])[1];width=widths.get(name,.25)
 if width<=.25 or name=='PGND':continue
 neck=min(width,.8);net=b.FindNet(name).GetNetCode();a=tuple(map(float,ends[0][:2]));z=tuple(map(float,ends[1][:2]));b.BuildConnectivity();ia=island(a,net);iz=island(z,net)
 if set(ia)&set(iz):continue
 blocked=raster(net,.251+width/2);vfree=~raster(net,1.51 if width>=1.2 else .651).any(axis=0);offsets=[(-.6,-.6),(-.6,.6),(.6,-.6),(.6,.6)] if width>=1.2 else [(0,0)]
 holes=Image.new('1',(W,H),0);hd=ImageDraw.Draw(holes)
 for item in [pd for fp in b.GetFootprints() for pd in fp.Pads()]+[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA)]:
  drill=mm(item.GetDrillValue()) if isinstance(item,k.PCB_VIA) else mm(max(item.GetDrillSize().x,item.GetDrillSize().y))
  if drill<=0:continue
  x,y=mm(item.GetPosition().x),mm(item.GetPosition().y);r=drill/2+.2+.251
  for dx,dy in offsets:hd.ellipse((math.floor((x-dx-r)/step),math.floor((y-dy-r)/step),math.ceil((x-dx+r)/step),math.ceil((y-dy+r)/step)),fill=1)
 vfree &= ~np.asarray(holes,dtype=bool)
 starts=seeds(ia,blocked,net,neck);goals=seeds(iz,blocked,net,neck)
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
 for kind,u,v,w in pieces:
  if kind=='via':
   t=k.PCB_VIA(b);t.SetPosition(vec(*u[1:]));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
  else:
   t=k.PCB_TRACK(b);t.SetStart(vec(*u[1:]));t.SetEnd(vec(*v[1:]));t.SetWidth(k.FromMM(w));t.SetLayer(cu[u[0]])
  t.SetNetCode(net);b.Add(t);additem(t)
 added.append({'net':name,'trunk_width_mm':width,'stub_width_mm':neck,'pieces':pieces});print('CONNECTED',name,'total',len(added),flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/Power_islands.json').write_text(json.dumps({'added':added,'failed':failed,'ampacity':'UNQUALIFIED'},indent=2));print('FINISHED',len(added),len(failed),flush=True)
