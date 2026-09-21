"""Geometrically screened short ground fanouts. Native DRC remains mandatory.
Power-ground fanouts are preliminary; this script does not qualify their ampacity.
"""
from pathlib import Path
import pcbnew as k,sys,math,json
f=Path(sys.argv[1]);b=k.LoadBoard(str(f));pads=[pd for fp in b.GetFootprints() for pd in fp.Pads()];refs={pd.m_Uuid.AsString():fp.GetReference() for fp in b.GetFootprints() for pd in fp.Pads()};tracks=list(b.GetTracks());cu=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]
obstacles=[]
for pd in pads:
 for layer in cu:
  if pd.IsOnLayer(layer):obstacles.append((pd.GetNetCode(),layer,pd.GetEffectiveShape(layer)))
for t in tracks:
 for layer in cu:
  if t.IsOnLayer(layer):obstacles.append((t.GetNetCode(),layer,t.GetEffectiveShape(layer)))
zones=[z for z in b.Zones() if z.GetIsRuleArea()]
def collision(shape,net,layers):
 for n,l,other in obstacles:
  if n!=net and l in layers and k.SHAPE.Collide(shape,other,k.FromMM(.251)):return True
 for z in zones:
  if z.GetDoNotAllowVias() and k.SHAPE.Collide(shape,z.Outline(),k.FromMM(.251)):return True
 return False
added=[]
for pd in pads:
 name=pd.GetNetname()
 if refs[pd.m_Uuid.AsString()] in ['NT1','NT2']:continue
 if name not in ['PGND','DGND'] or pd.GetAttribute()!=k.PAD_ATTRIB_SMD:continue
 layer=k.F_Cu if pd.IsOnLayer(k.F_Cu) else k.B_Cu;net=pd.GetNetCode();start=pd.GetPosition();width=.8 if name=='PGND' else .25
 # Only short local fanouts; wider shared returns are supplied by the plane.
 found=False
 for radius in [1.2,1.6,2,2.4,2.8,3.2]:
  for angle in range(0,360,45):
   dx=radius*math.cos(math.radians(angle));dy=radius*math.sin(math.radians(angle));end=k.VECTOR2I(start.x+k.FromMM(dx),start.y+k.FromMM(dy));x,y=k.ToMM(end.x),k.ToMM(end.y)
   if not(1<x<139.93 and 1<y<162.36):continue
   circ=k.SHAPE_CIRCLE(end,k.FromMM(.4));seg=k.SHAPE_SEGMENT(start,end,k.FromMM(width))
   if collision(circ,net,cu) or collision(seg,net,[layer]):continue
   via=k.PCB_VIA(b);via.SetPosition(end);via.SetWidth(k.FromMM(.8));via.SetDrill(k.FromMM(.4));via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNetCode(net);b.Add(via)
   tr=k.PCB_TRACK(b);tr.SetStart(start);tr.SetEnd(end);tr.SetWidth(k.FromMM(width));tr.SetLayer(layer);tr.SetNetCode(net);b.Add(tr)
   for l in cu:obstacles.append((net,l,circ))
   obstacles.append((net,layer,seg));added.append({'ref':refs[pd.m_Uuid.AsString()],'pad':pd.GetNumber(),'net':name,'x':x,'y':y,'length_mm':radius,'width_mm':width});found=True;break
  if found:break
assert k.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();k.SaveBoard(str(f),b)
assert k.WriteDRCReport(b,str(f.with_suffix('.drc.txt')),k.EDA_UNITS_MILLIMETRES,True)
f.with_suffix('.fanouts.json').write_text(json.dumps({'added':added,'ampacity':'UNQUALIFIED; power-current via arrays and thermal review remain required'},indent=2))
print('Added',len(added),'screened ground fanouts')
