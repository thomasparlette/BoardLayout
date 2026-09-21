"""Selective signal-track rip-up support. Pads, holes, vias and load tracks stay fixed."""
import struct,subprocess
raw_raster=raster
collect=False
rip_ids=set()
def eligible(item):
 return isinstance(item,k.PCB_TRACK) and not isinstance(item,k.PCB_VIA) and widths.get(item.GetNetname(),.25)<=.25
def hard_raster(net,r):
 global drawables
 old=drawables;drawables=[d for d in old if not(d[2]=='line' and widths.get(b.FindNet(d[0]).GetNetname(),.25)<=.25)]
 try:return raw_raster(net,r)
 finally:drawables=old
def soft_raster(net,r):
 global drawables
 old=drawables;drawables=[d for d in old if d[2]=='line' and widths.get(b.FindNet(d[0]).GetNetname(),.25)<=.25]
 try:return raw_raster(net,r)
 finally:drawables=old
def clear(shape,net,li):
 bb=shape.BBox();bb.Inflate(k.FromMM(.251))
 for n,l,o,box in obs:
  if n==net or (li is not None and l!=li) or not bb.Intersects(box):continue
  if not k.SHAPE.Collide(shape,o,k.FromMM(.251)):continue
  owner=obowners.get(id(o))
  if owner is not None and eligible(owner):
   if collect:rip_ids.add(owner.m_Uuid.AsString())
  else:return False
 for z in b.Zones():
  if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()) and k.SHAPE.Collide(shape,z.Outline(),k.FromMM(.251)):return False
 for fp in b.GetFootprints():
  if fp.GetReference() not in ['NT1','NT2'] or (li is not None and li!=0):continue
  x,y=mm(fp.GetPosition().x),mm(fp.GetPosition().y);poly=k.SHAPE_POLY_SET();poly.NewOutline()
  for xx,yy in [(x-2,y-1),(x+2,y-1),(x+2,y+1),(x-2,y+1)]:poly.Append(k.FromMM(xx),k.FromMM(yy))
  if k.SHAPE.Collide(shape,poly,k.FromMM(.251)):return False
 return True
def search(starts,goals,blocked,vfree):
 data=struct.pack('<IIII',W,H,len(starts),len(goals))+blocked.astype('uint8').tobytes()+soft_map.astype('uint8').tobytes()+vfree.astype('uint8').tobytes()+via_soft.astype('uint8').tobytes()+np.array(list(starts),dtype='<u4').tobytes()+np.array(list(goals),dtype='<u4').tobytes()
 result=subprocess.run([str(p/'source/astar_soft')],input=data,stdout=subprocess.PIPE,check=True).stdout
 size=struct.unpack('<I',result[:4])[0]
 return np.frombuffer(result[4:],dtype='<u4').astype(int).tolist() if size else None
def save_ripup(netname,width,neck,pieces):
 k.SaveBoard(str(f),b)
 ns={'__file__':str(p/'source/revise_schematic.py')};exec((p/'source/revise_schematic.py').read_text().split('# Verified against')[0],ns)
 s=f.read_text();changes=[]
 for aa,zz,t in ns['forms'](s):
  if t.startswith('(segment ') and re.search(r'\(tstamp ([^)]+)\)',t)[1] in rip_ids:changes.append((aa,zz,''))
 assert len(changes)==len(rip_ids)
 f.write_text(ns['edit'](s,changes));report=p/'reports/Selective_ripup.json';history=json.loads(report.read_text()) if report.exists() else []
 history.append({'net':netname,'trunk_width_mm':width,'stub_width_mm':neck,'removed_signal_track_uuids':sorted(rip_ids),'pieces':pieces});report.write_text(json.dumps(history,indent=2))
 print('ROUTED',netname,'removed',len(changes),'blocking signal segments',flush=True)
