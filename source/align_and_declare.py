from pathlib import Path
import re,uuid,xml.etree.ElementTree as E,json
p=Path(__file__).resolve().parents[1]
exec((p/'source/revise_schematic.py').read_text().split('# Verified against')[0])
def snap(x):return round(round(float(x)/1.27)*1.27,5)
def uid():return str(uuid.uuid4())
root=E.parse(p/'source/input_netlist.xml').getroot();nets={}
for n in root.find('nets'):
 for node in n.findall('node'):nets[node.get('ref'),node.get('pin')]=None if n.get('name').startswith('unconnected-') else n.get('name')
def libgrid(s):
 changes=[]
 for a,b,t in forms(s):
  if t.startswith(('(lib_symbols','(symbol ')):changes.append((a,b,libgrid(t)))
  elif t.startswith('(pin '):
   t=re.sub(r'\(at ([^ ]+) ([^ ]+) ([^)]+)\)',lambda m:f'(at {snap(m[1]):g} {snap(m[2]):g} {m[3]})',t,count=1);changes.append((a,b,t))
 return edit(s,changes)
for f in p.glob('*.kicad_sch'):
 s=libgrid(f.read_text());ff=forms(s);libs=next((t for _,_,t in ff if t.startswith('(lib_symbols')),None)
 if not libs:continue
 syms={re.match(r'\(symbol "([^"]+)"',t)[1]:t for _,_,t in forms(libs)};changes=[]
 for i,(a,b,t) in enumerate(ff):
  if not t.startswith('(symbol (lib_id'):continue
  ref=re.search(r'\(property "Reference" "([^"]+)"',t)[1];lib=re.search(r'\(lib_id "([^"]+)"',t)[1]
  m=re.search(r'\(at ([^ ]+) ([^ ]+) ([^)]+)\)',t);assert float(m[3])==0
  x,y=snap(m[1]),snap(m[2]);t=t[:m.start()]+f'(at {x:g} {y:g} 0)'+t[m.end():]
  end=b
  for aa,bb,other in ff[i+1:]:
   if not other.startswith(('(wire ','(global_label ','(no_connect ')):break
   end=bb
  chunks=[t]
  for _,_,unit in forms(syms[lib]):
   if not unit.startswith('(symbol '):continue
   um=re.match(r'\(symbol "[^"]+_(\d+)_\d+"',unit)
   if um and int(um[1]) not in (0,int(re.search(r'\(unit (\d+)\)',t)[1])):continue
   for _,_,pin in forms(unit):
    if not pin.startswith('(pin '):continue
    pn=re.search(r'\(number "([^"]+)"',pin)[1];pm=re.search(r'\(at ([^ ]+) ([^ ]+) ([^)]+)\)',pin)
    xx,yy=x+float(pm[1]),y-float(pm[2]);ang=float(pm[3]);net=nets.get((ref,pn))
    if net is None:chunks.append(f'(no_connect (at {xx:g} {yy:g}) (uuid {uid()}))');continue
    ex=xx+(-7.62 if ang==0 else 7.62);la=180 if ang==0 else 0;just='right' if ang==0 else 'left'
    chunks += [f'(wire (pts (xy {xx:g} {yy:g}) (xy {ex:g} {yy:g})) (stroke (width 0) (type default)) (uuid {uid()}))',f'(global_label "{net}" (shape bidirectional) (at {ex:g} {yy:g} {la}) (effects (font (size 1 1)) (justify {just})) (uuid {uid()}))']
  changes.append((a,end,'\n'.join(chunks)))
 s=edit(s,changes);f.write_text(s)
f=p/'GM97.kicad_sym';f.write_text(libgrid(f.read_text()))
# Power flags describe verified external power entry and passive-filter-derived rails;
# they do not create power or establish a voltage/current rating.
f=p/'GrandMarquis97_RevA.kicad_sch';s=f.read_text();rootid=re.search(r'\(uuid ([^)]+)',s)[1]
flag='''(symbol "GM97:PWR_FLAG" (power) (pin_names (offset 0)) (in_bom no) (on_board no)
 (property "Reference" "#FLG" (at 0 2.54 0) (effects (font (size 1 1)) hide))
 (property "Value" "PWR_FLAG" (at 0 5.08 0) (effects (font (size 1 1))))
 (symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 2.54) (xy 2.54 3.81) (xy 0 5.08) (xy -2.54 3.81) (xy 0 2.54)) (stroke (width 0.254) (type default)) (fill (type none))))
 (symbol "PWR_FLAG_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1 1)))) (number "1" (effects (font (size 1 1)))))))'''
ff=forms(s);lib=next(((a,b,t) for a,b,t in ff if t.startswith('(lib_symbols')),None)
if lib:s=edit(s,[(lib[0],lib[1],lib[2][:-1]+flag+')')])
else:s=s[:-1]+'(lib_symbols '+flag+')\n)'
add=[]
for i,net in enumerate(['RAW_12','DGND','VREF_5','SGND','VCC_5','PGND']):
 ref=f'#FLG0{i+1}';x=25.4+38.1*i;y=279.4
 add.append(f'(symbol (lib_id "GM97:PWR_FLAG") (at {x:g} {y:g} 0) (unit 1) (in_bom no) (on_board no) (uuid {uid()}) (property "Reference" "{ref}" (at {x:g} {y:g} 0) (effects (font (size 1 1)) hide)) (property "Value" "PWR_FLAG" (at {x:g} {y-7.62:g} 0) (effects (font (size 1 1)))) (instances (project "GrandMarquis97_RevA" (path "/{rootid}" (reference "{ref}") (unit 1)))))')
 add.append(f'(global_label "{net}" (shape bidirectional) (at {x:g} {y:g} 0) (effects (font (size 1 1)) (justify left)) (uuid {uid()}))')
f.write_text(s.rstrip()[:-1]+'\n'+'\n'.join(add)+'\n)')
f=p/'GM97.kicad_sym';s=f.read_text();f.write_text(s.rstrip()[:-1]+'\n'+flag+'\n)')
print('Schematic pins and connection geometry aligned to 1.27 mm; six rail declarations added.')
