"""Connector escape experiment: four parallel copper paths per load pin.
Keep original drill and pin coordinates. Branch width/thermal rating is unqualified.
"""
from pathlib import Path
exec(Path(__file__).with_name('circle_routes.py').read_text().split('widths=')[0],globals())
step=.05;W=2818;H=480;N=W*H
widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']}
j=next(fp for fp in b.GetFootprints() if fp.GetReference()=='J1')
pins=sorted([pd for pd in j.Pads() if pd.GetNetname().startswith('INJECTOR_')],key=lambda pd:(-pd.GetPosition().y,-pd.GetPosition().x))
prior=json.loads((p/'reports/Parallel_header.json').read_text())['pins'] if (p/'reports/Parallel_header.json').exists() else []
done={x['pin'] for x in prior if x['status']=='routed'}
results=[x for x in prior if x['status']=='routed']
for pd in pins:
 if pd.GetNumber() in done:continue
 name=pd.GetNetname();net=pd.GetNetCode();width=min(.75,widths[name]/4);a=(mm(pd.GetPosition().x),mm(pd.GetPosition().y))
 mask=raster(net,.251+width/2).any(axis=0);blocked=np.stack([mask]*4);vfree=np.zeros((H,W),dtype=bool);anchor_free=~raster(net,1.51).any(axis=0)
 starts={}
 for dx in [-1,0,1]:
  for dy in [-1,0,1]:
   x=round(a[0]/step)+dx;y=round(a[1]/step)+dy
   if blocked[0,y,x]:continue
   if clear(k.SHAPE_SEGMENT(vec(*a),vec(x*step,y*step),k.FromMM(width)),net,None):starts[y*W+x]=(0,a)
 goals={}
 for yv in [15,17,19,21]:
  y=round(yv/step)
  for xv in np.arange(max(15,a[0]-25),min(127,a[0]+25),.5):
   x=round(xv/step)
   if anchor_free[y,x] and not blocked[0,y,x]:goals[y*W+x]=(0,(x*step,y*step))
 if not starts or not goals:results.append({'pin':pd.GetNumber(),'net':name,'status':'no escape'});continue
 path=search(starts,goals,blocked,vfree)
 if not path:results.append({'pin':pd.GetNumber(),'net':name,'status':'no path'});continue
 pts=[a]+[(n%W*step,n//W*step) for n in path]
 # Collapse straight runs and then use native-screened line-of-sight shortening.
 corners=[pts[0]]
 for i in range(1,len(pts)-1):
  u,v,w=pts[i-1:i+2]
  if u[0]==v[0]==w[0] or u[1]==v[1]==w[1]:continue
  corners.append(v)
 corners.append(pts[-1]);smooth=[corners[0]];i=0
 while i<len(corners)-1:
  found=i+1
  for jj in range(len(corners)-1,i,-1):
   if clear(k.SHAPE_SEGMENT(vec(*corners[i]),vec(*corners[jj]),k.FromMM(width)),net,None):found=jj;break
  smooth.append(corners[found]);i=found
 q=smooth[-1];offsets=[(-.6,-.6),(-.6,.6),(.6,-.6),(.6,.6)]
 if not all(clear(k.SHAPE_CIRCLE(vec(q[0]+dx,q[1]+dy),k.FromMM(.4)),net,None) for dx,dy in offsets):results.append({'pin':pd.GetNumber(),'net':name,'status':'array collision'});continue
 if not all(clear(k.SHAPE_SEGMENT(vec(*u),vec(*v),k.FromMM(width)),net,None) for u,v in zip(smooth,smooth[1:])):results.append({'pin':pd.GetNumber(),'net':name,'status':'track collision'});continue
 for l in cu:
  for u,v in list(zip(smooth,smooth[1:]))+[(q,(q[0]+dx,q[1]+dy)) for dx,dy in offsets]:
   if u==v:continue
   t=k.PCB_TRACK(b);t.SetStart(vec(*u));t.SetEnd(vec(*v));t.SetWidth(k.FromMM(width));t.SetLayer(l);t.SetNetCode(net);b.Add(t);additem(t)
 for dx,dy in offsets:
  t=k.PCB_VIA(b);t.SetPosition(vec(q[0]+dx,q[1]+dy));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetNetCode(net);b.Add(t);additem(t)
 results.append({'pin':pd.GetNumber(),'net':name,'status':'routed','width_per_layer':width,'parallel_layers':4,'anchor':q,'path':smooth});print('ESCAPED',pd.GetNumber(),name,flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/Parallel_header.json').write_text(json.dumps({'status':'CURRENT AND THERMAL QUALIFICATION REQUIRED','pad_diameter_mm':2,'drill_mm':1.4,'pins':results},indent=2));print('FINISHED',sum(x['status']=='routed' for x in results),len(results),flush=True)
