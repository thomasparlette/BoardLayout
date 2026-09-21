from pathlib import Path
import json,math,collections
p=Path(__file__).resolve().parents[1]
widths={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']}
tr=json.loads((p/'source/routed_geometry.json').read_text())['tracks'];stats={}
for t in tr:
 n=t['net']
 if n not in widths or t['via']:continue
 d=stats.setdefault(n,{'target_width_mm':widths[n],'total_track_length_mm':0,'below_target_length_mm':0,'minimum_width_mm':t['width']})
 length=math.hypot(t['x1']-t['x2'],t['y1']-t['y2']);d['total_track_length_mm']+=length;d['minimum_width_mm']=min(d['minimum_width_mm'],t['width'])
 if t['width']<widths[n]-.0001:d['below_target_length_mm']+=length
(p/'reports/Current_path_audit_R8.json').write_text(json.dumps({'status':'NOT AMPACITY QUALIFIED. Width targets are not current ratings; neckdowns, via arrays, copper stackup, duty cycles and heating remain to be engineered.','nets':stats},indent=2))
