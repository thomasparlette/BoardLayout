from pathlib import Path
import json
from shapely.geometry import Polygon
p=Path(__file__).resolve().parents[1];g=json.loads((p/'reports/Mechanical_geometry.json').read_text());parts=g['parts'];overlaps=[]
for i,a in enumerate(parts):
 for c in parts[i+1:]:
  if a['layer']!=c['layer']:continue
  ar=Polygon(a['polygon']).intersection(Polygon(c['polygon'])).area
  if ar>.01:overlaps.append({'a':a['ref'],'b':c['ref'],'area_mm2':ar})
bottom=[a for a in parts if a['layer']=='B.Cu'];height=max(a['height'] for a in bottom)
r={'envelope_overlap_count':len(overlaps),'overlaps':overlaps,'front_bodies':len(parts)-len(bottom),'back_bodies':len(bottom),'user_cover_clearance_mm':6.35,'maximum_modelled_back_height_mm':height,'nominal_body_only_margin_mm':6.35-height,'modelled_back_bodies_within_gap':height<=6.35,'qualification':'Approximate body envelopes only. Lead protrusions, solder, case hardware, thermal insulation and module assemblies remain excluded.'}
(p/'reports/Envelope_overlap_review.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
