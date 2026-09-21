from pathlib import Path
import re,json
p=Path(__file__).resolve().parents[1];ns={'__file__':str(p/'source/revise_schematic.py')};exec((p/'source/revise_schematic.py').read_text().split('# Verified against')[0],ns);f=p/'GrandMarquis97_RevA.kicad_pcb';s=f.read_text();seen=set();changes=[];counts={'segment':0,'via':0}
for a,z,t in ns['forms'](s):
 kind='segment' if t.startswith('(segment ') else 'via' if t.startswith('(via ') else None
 if not kind:continue
 def field(k):
  m=re.search(r'\('+k+r' ([^)]+)\)',t);return m[1] if m else ''
 if kind=='segment':key=(kind,*sorted([field('start'),field('end')]),field('width'),field('layer'),field('net'))
 else:key=(kind,field('at'),field('size'),field('drill'),field('layers'),field('net'),'blind' in t,'micro' in t)
 if key in seen:changes.append((a,z,''));counts[kind]+=1
 else:seen.add(key)
f.write_text(ns['edit'](s,changes));(p/'reports/Deduplicated_copper.json').write_text(json.dumps(counts,indent=2));print(counts)
