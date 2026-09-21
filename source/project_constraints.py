from pathlib import Path
import json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pro';d=json.loads(f.read_text())
t=json.loads((p/'reports/Routing_targets.json').read_text())['widths'];base=d['net_settings']['classes'][0];classes=[base];patterns=[]
for name,v in t.items():
 if name=='Signal':continue
 c=base.copy();c['name']=name;c['track_width']=v['width_mm'];c['clearance']=.25;c['via_diameter']=.8;c['via_drill']=.4;classes.append(c)
 for net in v['nets']:patterns.append({'netclass':name,'pattern':net})
d['net_settings']['classes']=classes;d['net_settings']['netclass_patterns']=patterns;f.write_text(json.dumps(d,indent=2))
print('Saved current-target net classes in native project.')
