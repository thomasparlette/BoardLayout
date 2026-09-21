from pathlib import Path
exec(Path(__file__).with_name('circle_routes.py').read_text().split('widths=')[0],globals())
for name in ['INJECTOR_1','INJECTOR_5']:
 net=b.FindNet(name).GetNetCode();blocked0=raster(net,.501).any(axis=0);blocked=np.stack([blocked0]*4);wide=raster(net,1.51).any(axis=0);vfree=np.zeros((H,W),bool)
 starts={}
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA) and t.GetNetCode()==net and mm(t.GetPosition().y)<23:
   pt=(mm(t.GetPosition().x),mm(t.GetPosition().y));x,y=round(pt[0]/step),round(pt[1]/step)
   if not blocked0[y,x] and clear(k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(.5)),net,None):starts[y*W+x]=(0,pt)
 goals={y*W+x:(0,(x*step,y*step)) for y in range(280,360,10) for x in range(30,W-30,10) if not wide[y,x]}
 if not starts or not goals:print(name,'no seeds',len(starts),len(goals),flush=True);continue
 path=search(starts,goals,blocked,vfree)
 if not path:print(name,'no extension',flush=True);continue
 pts=[(n%N%W*step,n%N//W*step) for n in path];compact=[starts[path[0]][1],pts[0]]
 for i in range(1,len(pts)-1):
  a,c,d=pts[i-1:i+2]
  if abs((c[0]-a[0])*(d[1]-c[1])-(c[1]-a[1])*(d[0]-c[0]))>1e-9:compact.append(c)
 compact.append(pts[-1]);segments=[(a,c) for a,c in zip(compact,compact[1:]) if a!=c];end=pts[-1];vias=[(end[0]+dx,end[1]+dy) for dx in [-.6,.6] for dy in [-.6,.6]];segments += [(end,v) for v in vias]
 if not all(clear(k.SHAPE_SEGMENT(vec(*a),vec(*c),k.FromMM(.5)),net,None) for a,c in segments) or not all(clear(k.SHAPE_CIRCLE(vec(*v),k.FromMM(.4)),net,None) for v in vias):print(name,'native rejected',flush=True);continue
 for a,c in segments:
  for l in cu:
   t=k.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*c));t.SetWidth(k.FromMM(.5));t.SetLayer(l);t.SetNetCode(net);b.Add(t);additem(t)
 for v in vias:
  t=k.PCB_VIA(b);t.SetPosition(vec(*v));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetNetCode(net);b.Add(t);additem(t)
 print(name,'extended',end,flush=True);k.SaveBoard(str(f),b)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
