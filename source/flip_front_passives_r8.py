"""Move selected blocked low-profile passives to B.Cu when their new pads and body fit existing copper."""
from pathlib import Path
import pcbnew as k,json,re
from shapely.geometry import Polygon
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));r=(p/'reports/After_routing_DRC.txt').read_text();refs=set()
for block in re.split(r'(?=^\[)',r,flags=re.M):
 if block.startswith('[unconnected_items]'):refs.update(re.findall(r'of ([RC]\d+) on F.Cu',block))
g=json.loads((p/'reports/Mechanical_geometry.json').read_text());models={x['ref']:x for x in g['parts']};back=[(x['ref'],Polygon(x['polygon'])) for x in g['parts'] if x['layer']=='B.Cu'];conn=b.GetConnectivity();moves=[]
for fp in list(b.GetFootprints()):
 ref=fp.GetReference()
 if ref not in refs or fp.GetLayer()!=k.F_Cu or ref not in models:continue
 m=models[ref]
 if m['height']>2 or not all(d.GetAttribute()==k.PAD_ATTRIB_SMD for d in fp.Pads()):continue
 body=Polygon(m['polygon'])
 if any(body.distance(q)<.5 for n,q in back):continue
 trial=fp.Duplicate();trial.Flip(trial.GetPosition(),False)
 okay=True
 for pd in trial.Pads():
  sh=pd.GetEffectiveShape(k.B_Cu);bb=sh.BBox();bb.Inflate(k.FromMM(.251))
  for o in [d for ff in b.GetFootprints() if ff.GetReference()!=ref for d in ff.Pads()]+list(b.GetTracks()):
   if not o.IsOnLayer(k.B_Cu) or o.GetNetCode()==pd.GetNetCode():continue
   other=o.GetEffectiveShape(k.B_Cu)
   if bb.Intersects(other.BBox()) and k.SHAPE.Collide(sh,other,k.FromMM(.251)):okay=False;break
  if not okay:break
 if not okay:continue
 old=[(pd.GetPosition(),pd.GetNetCode()) for pd in fp.Pads()]
 fp.Flip(fp.GetPosition(),False)
 # Preserve all existing routes. Removed top pads become explicit open connections to repair.
 moves.append({'reference':ref,'from':'F.Cu','to':'B.Cu','x_mm':k.ToMM(fp.GetPosition().x),'y_mm':k.ToMM(fp.GetPosition().y),'generic_body_height_mm':m['height'],'cover_clearance_mm':6.35});back.append((ref,body))
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R8_bottom_moves.json').write_text(json.dumps(moves,indent=2));print(moves)
