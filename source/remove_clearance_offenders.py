from pathlib import Path
import re,math,json
p=Path(__file__).resolve().parents[1]
exec((p/'source/revise_schematic.py').read_text().split('# Verified against')[0])
r=(p/'reports/After_routing_DRC.txt').read_text();targets=[]
for block in re.split(r'(?=^\[)',r,flags=re.M):
 if not block.startswith('[clearance]'):continue
 for m in re.finditer(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): Track \[([^]]+)\] on ([^,]+), length ([-\d.]+) mm',block):targets.append((float(m[1]),float(m[2]),m[3],m[4],float(m[5])))
f=p/'GrandMarquis97_RevA.kicad_pcb';s=f.read_text();names={int(m[1]):m[2] for m in re.finditer(r'\(net (\d+) "([^"]*)"\)',s)};changes=[]
for a,b,t in forms(s):
 if not t.startswith('(segment '):continue
 x,y=map(float,re.search(r'\(start ([^ ]+) ([^)]+)\)',t).groups());xx,yy=map(float,re.search(r'\(end ([^ ]+) ([^)]+)\)',t).groups());net=names[int(re.search(r'\(net (\d+)\)',t)[1])];layer=re.search(r'\(layer "([^"]+)"\)',t)[1]
 if any(net==n and layer==l and min(math.hypot(x-u,y-v),math.hypot(xx-u,yy-v))<.0002 and abs(math.hypot(x-xx,y-yy)-length)<.0002 for u,v,n,l,length in targets):changes.append((a,b,''))
f.write_text(edit(s,changes));(p/'reports/Clearance_cleanup.json').write_text(json.dumps({'removed_segments':len(changes),'reason':'Router crossed net-tie bridge copper; affected paths remain open'},indent=2));print('Removed',len(changes),'clearance offenders')
