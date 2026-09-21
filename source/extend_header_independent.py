from pathlib import Path
exec(Path(__file__).with_name('circle_routes.py').read_text().split('widths=')[0],globals())
for name in ['INJECTOR_1','INJECTOR_5']:
 net=b.FindNet(name).GetNetCode();ras=raster(net,.501);wide=raster(net,1.51).any(axis=0);vfree=np.zeros((H,W),bool);anchor=[]
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA) and t.GetNetCode()==net and mm(t.GetPosition().y)<23:anchor.append((mm(t.GetPosition().x),mm(t.GetPosition().y)))
 candidates_goals=[(x,y) for y in range(230,450,20) for x in range(30,W-30,20) if not wide[y,x]]
 allpieces=None;until=time.monotonic()+25
 candidates_goals.sort(key=lambda q:abs(q[0]*step-100)+abs(q[1]*step-28))
 for gx,gy in candidates_goals:
  if time.monotonic()>until:break
  pieces=[];okay=True
  for li in range(4):
   blocked=np.ones_like(ras);blocked[li]=ras[li];starts={}
   for pt in anchor:
    x,y=round(pt[0]/step),round(pt[1]/step)
    if not blocked[li,y,x] and clear(k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(.5)),net,li):starts[li*N+y*W+x]=(0,pt)
   if not starts:okay=False;break
   goal=li*N+gy*W+gx;path=search(starts,{goal:(0,(gx*step,gy*step))},blocked,vfree)
   if not path:okay=False;break
   pts=[(n%N%W*step,n%N//W*step) for n in path];compact=[starts[path[0]][1],pts[0]]
   for i in range(1,len(pts)-1):
    a,c,d=pts[i-1:i+2]
    if abs((c[0]-a[0])*(d[1]-c[1])-(c[1]-a[1])*(d[0]-c[0]))>1e-9:compact.append(c)
   compact.append(pts[-1]);pieces.extend((li,a,c) for a,c in zip(compact,compact[1:]) if a!=c)
  if okay:allpieces=pieces;break
 if allpieces is None:print(name,'NO FOUR PATHS',flush=True);continue
 end=(gx*step,gy*step);vias=[(end[0]+dx,end[1]+dy) for dx in [-.6,.6] for dy in [-.6,.6]]
 allpieces += [(li,end,v) for li in range(4) for v in vias]
 if not all(clear(k.SHAPE_SEGMENT(vec(*a),vec(*c),k.FromMM(.5)),net,li) for li,a,c in allpieces) or not all(clear(k.SHAPE_CIRCLE(vec(*v),k.FromMM(.4)),net,None) for v in vias):print(name,'NATIVE REJECT',flush=True);continue
 for li,a,c in allpieces:
  t=k.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*c));t.SetWidth(k.FromMM(.5));t.SetLayer(cu[li]);t.SetNetCode(net);b.Add(t);additem(t)
 for v in vias:
  t=k.PCB_VIA(b);t.SetPosition(vec(*v));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetNetCode(net);b.Add(t);additem(t)
 print(name,'extended independently',end,flush=True);k.SaveBoard(str(f),b)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
