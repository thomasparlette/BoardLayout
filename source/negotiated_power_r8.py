"""Route blocked signals, allowing obstructing track/via removal. Native DRC and subsequent repair of displaced nets are mandatory."""
from pathlib import Path
exec(Path(__file__).with_name('signal_smallvia_r8.py').read_text().split('widths=')[0],globals())
historyfile=p/'reports/R8_rip_history.json';history=json.loads(historyfile.read_text()) if historyfile.exists() else {};pads=[pd for fp in b.GetFootprints() for pd in fp.Pads()];hard=[]
for pd in pads:
 for li,l in enumerate(cu):
  if pd.IsOnLayer(l):hard.append((pd.GetNetCode(),li,pd.GetEffectiveShape(l)))
nt=[]
for fp in b.GetFootprints():
 if fp.GetReference().startswith('NT'):
  x,y=mm(fp.GetPosition().x),mm(fp.GetPosition().y);nt.append((x-2,y-1,x+2,y+1))
def clear(shape,net,li):
 bb=shape.BBox();bb.Inflate(k.FromMM(.251))
 for n,l,o in hard:
  if n==net or (li is not None and l!=li):continue
  if bb.Intersects(o.BBox()) and k.SHAPE.Collide(shape,o,k.FromMM(.251 if n in powercodes or net in powercodes else .201)):return False
 for z in b.Zones():
  if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and k.SHAPE.Collide(shape,z.Outline(),k.FromMM(.251)):return False
 if li is None or li==0:
  for x,y,xx,yy in nt:
   q=k.SHAPE_POLY_SET();q.NewOutline()
   for a,c in [(x,y),(xx,y),(xx,yy),(x,yy)]:q.Append(k.FromMM(a),k.FromMM(c))
   if k.SHAPE.Collide(shape,q,k.FromMM(.251)):return False
 return True

def masks(net,r):
 ims=[Image.new('L',(W,H),0) for _ in cu];ds=[ImageDraw.Draw(i) for i in ims]
 for pd in pads:
  if pd.GetNetCode()==net:continue
  for li,l in enumerate(cu):
   if not pd.IsOnLayer(l):continue
   bb=pd.GetEffectiveShape(l).BBox();rr=r+(.05 if pd.GetNetCode() in powercodes and net not in powercodes else 0);x,y,xx,yy=mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom());method=ds[li].ellipse if pd.GetShape()==k.PAD_SHAPE_CIRCLE else ds[li].rectangle
   method((math.floor((x-rr)/step),math.floor((y-rr)/step),math.ceil((xx+rr)/step),math.ceil((yy+rr)/step)),fill=1)
 for d in ds:
  for x,y,xx,yy in keep:d.rectangle((math.floor((x-r)/step),math.floor((y-r)/step),math.ceil((xx+r)/step),math.ceil((yy+r)/step)),fill=1)
  d.rectangle((0,0,W-1,H-1),outline=1,width=math.ceil((r+.3)/step)+1)
 for x,y,xx,yy in nt:ds[0].rectangle((math.floor((x-r)/step),math.floor((y-r)/step),math.ceil((xx+r)/step),math.ceil((yy+r)/step)),fill=1)
 costs=[Image.new('L',(W,H),0) for _ in cu];cd=[ImageDraw.Draw(i) for i in costs]
 def cost(t):return 230 if t.GetNetCode() in powercodes else min(210,20+history.get(t.GetNetname(),0)*25)
 for t in sorted(list(b.GetTracks()),key=cost):
  if t.GetNetCode()==net:continue
  rr=r+(.05 if t.GetNetCode() in powercodes and net not in powercodes else 0);rad=mm(t.GetWidth())/2+rr;value=cost(t)
  for li,l in enumerate(cu):
   if not t.IsOnLayer(l):continue
   d=cd[li];x,y,xx,yy=mm(t.GetStart().x),mm(t.GetStart().y),mm(t.GetEnd().x),mm(t.GetEnd().y)
   if not isinstance(t,k.PCB_VIA):d.line((round(x/step),round(y/step),round(xx/step),round(yy/step)),fill=value,width=math.ceil(2*rad/step)+1)
   for a,c in [(x,y),(xx,yy)]:d.ellipse((math.floor((a-rad)/step),math.floor((c-rad)/step),math.ceil((a+rad)/step),math.ceil((c+rad)/step)),fill=value)
 return np.stack([np.asarray(i,dtype=np.uint8) for i in ims]),np.stack([np.asarray(i,dtype=np.uint8) for i in costs])

def search(starts,goals,blocked,vfree):
 data=struct.pack('<IIII',W,H,len(starts),len(goals))+blocked.astype('uint8').tobytes()+vfree.astype('uint8').tobytes()+soft.tobytes()+vsoft.tobytes()+np.array(list(starts),dtype='<u4').tobytes()+np.array(list(goals),dtype='<u4').tobytes()
 result=subprocess.run([str(p/'source/astar_soft')],input=data,stdout=subprocess.PIPE,check=True).stdout
 size=struct.unpack('<I',result[:4])[0];return np.frombuffer(result[4:],dtype='<u4').tolist() if size else None
def power_seeds(items,blocked,net):
 out={}
 for it in items.values():
  layers=[li for li,l in enumerate(cu) if it.IsOnLayer(l)];points=[it.GetPosition()] if not isinstance(it,k.PCB_TRACK) else [it.GetStart(),it.GetEnd()]
  for point in points:
   pt=(mm(point.x),mm(point.y))
   for li in layers:
    for radius in [0,.4,.8,1.2,2,3,4,5,6,8,10,12]:
     found=False
     for ang in range(0,360,45):
      x=round((pt[0]+radius*math.cos(math.radians(ang)))/step);y=round((pt[1]+radius*math.sin(math.radians(ang)))/step)
      if not(0<=x<W and 0<=y<H) or blocked[li,y,x]:continue
      if clear(k.SHAPE_SEGMENT(vec(*pt),vec(x*step,y*step),k.FromMM(neck)),net,li):out[li*N+y*W+x]=(0,pt);found=True
     if found:break
 return out

widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']};added=[];failed=[];ripped=[]
blocks=re.split(r'(?=^\[)',(p/'reports/After_routing_DRC.txt').read_text(),flags=re.M)
for block in blocks:
 if not block.startswith('[unconnected_items]'):continue
 ends=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.+)',block)
 if len(ends)!=2 or any(': Zone' in d for d in [block]):continue
 name=re.search(r'\[([^]]+)\]',ends[0][2])[1]
 width=widths.get(name,.25)
 if width<=.25 or name=='PGND':continue
 neck=min(width,.8);offsets=[(-.6,-.6),(-.6,.6),(.6,-.6),(.6,.6)] if width>=1.2 else [(0,0)]
 net=b.FindNet(name).GetNetCode();a=tuple(map(float,ends[0][:2]));z=tuple(map(float,ends[1][:2]));b.BuildConnectivity()
 try:ia=island(a,net);iz=island(z,net)
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
 starts=power_seeds(ia,blocked,net);goals=power_seeds(iz,blocked,net)
 if not starts or not goals:failed.append((name,'hard escape'));continue
 path=search(starts,goals,blocked,vfree)
 if not path:failed.append((name,'hard search'));continue
 pts=[(n//N,n%N%W*step,n%N//W*step) for n in path];compact=[pts[0]]
 for i in range(1,len(pts)-1):
  u,v,w=pts[i-1:i+2]
  if u[0]==v[0]==w[0] and abs((v[1]-u[1])*(w[2]-v[2])-(v[2]-u[2])*(w[1]-v[1]))<1e-9:continue
  compact.append(v)
 compact.append(pts[-1]);compact=[(compact[0][0],*starts[path[0]][1])]+compact+[(compact[-1][0],*goals[path[-1]][1])];pieces=[];okay=True
 for i,(u,v) in enumerate(zip(compact,compact[1:])):
  if u==v:continue
  if u[0]!=v[0]:
   for dx,dy in offsets:
    q=(u[0],u[1]+dx,u[2]+dy);sh=k.SHAPE_CIRCLE(vec(*q[1:]),k.FromMM(.4));okay &= clear(sh,net,None);pieces.append((q,q,sh,None,0))
    for li in [u[0],v[0]]:
     aa=(li,*u[1:]);zz=(li,*q[1:]);sh=k.SHAPE_SEGMENT(vec(*aa[1:]),vec(*zz[1:]),k.FromMM(neck));okay &= clear(sh,net,li)
     if aa!=zz:pieces.append((aa,zz,sh,li,neck))
  else:
   w=neck if i in [0,len(compact)-2] else width;sh=k.SHAPE_SEGMENT(vec(*u[1:]),vec(*v[1:]),k.FromMM(w));okay &= clear(sh,net,u[0]);pieces.append((u,v,sh,u[0],w))
 if not okay:failed.append((name,'native hard geometry'));continue
 targets={}
 for u,v,sh,li,w in pieces:
  bb=sh.BBox();bb.Inflate(k.FromMM(.251))
  for t in b.GetTracks():
   if t.GetNetCode()==net:continue
   ls=cu if li is None else [cu[li]]
   for l in ls:
    if not t.IsOnLayer(l):continue
    other=t.GetEffectiveShape(l)
    if bb.Intersects(other.BBox()) and k.SHAPE.Collide(sh,other,k.FromMM(.251 if net in powercodes or t.GetNetCode() in powercodes else .201)):targets[t.m_Uuid.AsString()]=t;break
 for t in targets.values():
  ripped.append({'for':name,'net':t.GetNetname(),'uuid':t.m_Uuid.AsString()});history[t.GetNetname()]=history.get(t.GetNetname(),0)+1;b.Delete(t)
 for u,v,sh,li,w in pieces:
  if li is None:
   t=k.PCB_VIA(b);t.SetPosition(vec(*u[1:]));t.SetWidth(k.FromMM(.8));t.SetDrill(k.FromMM(.4));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
  else:
   t=k.PCB_TRACK(b);t.SetStart(vec(*u[1:]));t.SetEnd(vec(*v[1:]));t.SetWidth(k.FromMM(w));t.SetLayer(cu[li])
  t.SetNetCode(net);b.Add(t)
 added.append(name);print('ROUTED',name,'displaced',len(targets),'items',flush=True);k.SaveBoard(str(f),b);historyfile.write_text(json.dumps(history,indent=2))
 if len(added)>=8:break
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R8_negotiated_power.json').write_text(json.dumps({'added':added,'failed':failed,'displaced_items':ripped},indent=2));print('DONE',len(added),'displaced',len(ripped),flush=True)
