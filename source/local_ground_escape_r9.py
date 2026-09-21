from pathlib import Path
exec(Path(__file__).with_name('signal_smallvia_r8.py').read_text().split('widths=')[0],globals())
pads=[pd for fp in b.GetFootprints() for pd in fp.Pads()];refs={fp.GetReference():fp for fp in b.GetFootprints()};done=[];failed=[]
for ref,pin,name in [('R80','2','PGND'),('U6','3','PGND'),('U7','3','PGND'),('NT1','1','PGND'),('U5','19','DGND')]:
 pd=next(p for p in refs[ref].Pads() if p.GetNumber()==pin);net=pd.GetNetCode();pos=pd.GetPosition();origin=(mm(pos.x),mm(pos.y));layer=pd.GetLayer();target=k.In3_Cu if name=='PGND' else k.In4_Cu
 nearbox=k.BOX2I(vec(origin[0]-4,origin[1]-4),vec(8,8));neartracks=[t for t in b.GetTracks() if nearbox.Intersects(t.GetBoundingBox())];nearpads=[q for q in pads if nearbox.Intersects(q.GetBoundingBox())]
 zones=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetCode()==net and z.GetLayer()==target];best=None
 for dx in range(-30,31,2):
  for dy in range(-30,31,2):
   if dx==dy==0:continue
   x=round(origin[0]+dx*.1,2);y=round(origin[1]+dy*.1,2)
   if ref=='NT1' and (x>origin[0] or abs(y-origin[1])>.1):continue
   v=vec(x,y)
   if not any(z.HitTestFilledArea(target,v) for z in zones):continue
   via=k.SHAPE_CIRCLE(v,k.FromMM(.3));track=k.SHAPE_SEGMENT(pos,v,k.FromMM(.25));shapes=[(via,None),(track,layer)];bad=False;cuts={}
   for shape,l in shapes:
    bb=shape.BBox();bb.Inflate(k.FromMM(.251))
    for q in nearpads:
     if q.GetNetCode()==net:continue
     for ll in (cu if l is None else [l]):
      if q.IsOnLayer(ll) and bb.Intersects(q.GetBoundingBox()) and k.SHAPE.Collide(shape,q.GetEffectiveShape(ll),k.FromMM(.251)):bad=True;break
     if bad:break
    if bad:break
    for z in b.Zones():
     if z.GetIsRuleArea() and k.SHAPE.Collide(shape,z.Outline(),k.FromMM(.251)):bad=True;break
    if bad:break
    for t in neartracks:
     if t.GetNetCode()==net:continue
     for ll in (cu if l is None else [l]):
      if t.IsOnLayer(ll) and bb.Intersects(t.GetBoundingBox()) and k.SHAPE.Collide(shape,t.GetEffectiveShape(ll),k.FromMM(.251)):
       if t.GetNetCode() in powercodes:bad=True
       else:cuts[t.m_Uuid.AsString()]=t
       break
     if bad:break
    if bad:break
   if bad:continue
   for q in nearpads+[t for t in neartracks if isinstance(t,k.PCB_VIA) and t.GetNetCode()==net]:
    drill=mm(q.GetDrillValue()) if isinstance(q,k.PCB_VIA) else mm(max(q.GetDrillSize().x,q.GetDrillSize().y))
    if drill and math.hypot(x-mm(q.GetPosition().x),y-mm(q.GetPosition().y))<drill/2+.15+.251:bad=True;break
   if bad:continue
   score=len(cuts)*100+math.hypot(dx,dy)
   if best is None or score<best[0]:best=(score,x,y,cuts)
 if best is None:failed.append(ref+'.'+pin);print('BLOCKED',ref,pin,flush=True);continue
 _,x,y,cuts=best;displaced=[t.GetNetname() for t in cuts.values()]
 for t in cuts.values():b.Delete(t)
 t=k.PCB_TRACK(b);t.SetStart(pos);t.SetEnd(vec(x,y));t.SetWidth(k.FromMM(.25));t.SetLayer(layer);t.SetNetCode(net);b.Add(t)
 t=k.PCB_VIA(b);t.SetPosition(vec(x,y));t.SetWidth(k.FromMM(.6));t.SetDrill(k.FromMM(.3));t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetNetCode(net);b.Add(t)
 done.append({'pad':ref+'.'+pin,'net':name,'via_mm':[x,y],'displaced':displaced});print('STITCHED',ref,pin,'displaced',displaced,flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/Local_ground_escape_R9.json').write_text(json.dumps({'added':done,'failed':failed},indent=2))
