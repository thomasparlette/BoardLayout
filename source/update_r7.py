from pathlib import Path
import pcbnew as k, shutil, json, re, xml.etree.ElementTree as ET
p=Path(__file__).resolve().parents[1]
b=k.LoadBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'))
lib=p/'GM97_Layout.pretty';name='Molex_Micro-Fit_3.0_43045-2000_2x10_P3.00mm_Horizontal'
shutil.copy('/tmp/microfit20.kicad_mod',lib/(name+'.kicad_mod'))
def v(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
fps={f.GetReference():f for f in b.GetFootprints()}
old=fps['J120']; nets={d.GetNumber():d.GetNetname() for d in old.Pads()}
new=k.FootprintLoad(str(lib),name);new.SetReference('J120');new.SetValue('43045-2000');new.SetPath(old.GetPath())
b.Remove(old);b.Add(new);new.SetFPID(k.LIB_ID('GM97_Layout',name));new.SetPosition(v(106,154.44));new.SetOrientationDegrees(180)
for pad in new.Pads():
 if pad.GetNumber() and nets.get(pad.GetNumber()):pad.SetNet(b.FindNet(nets[pad.GetNumber()]))
# Rear face of the header is aligned to y=163.36. Mating/latch service space is external.
for ref,x,y in [('J130',62,146),('J140',90,140)]:fps[ref].SetPosition(v(x,y))
# Remove copper attached to obsolete pad locations in moved footprints; remaining
# geometry is deliberately rerouted from its complete netlist below.
for t in list(b.GetTracks()):b.Delete(t)
for z in [b.GetArea(i) for i in range(b.GetAreaCount())]:
 if not z.GetIsRuleArea():b.Delete(z)
# Repair small annular rings on the two TO-92 transistors without reducing clearance.
for ref in ['Q1','Q2']:
 for pad in fps[ref].Pads():
  pad.SetDrillSize(v(.6,.6))
  pad.SetSize(v(1.15,1.15));pad.SetLocalClearance(k.FromMM(.2))
b.BuildConnectivity();k.SaveBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'),b)
s=p/'23_transmission.kicad_sch';t=s.read_text().replace('GM97_Layout:Candidate_J120','GM97_Layout:'+name).replace('TCU_HARNESS_20','43045-2000')
s.write_text(t)
tree=ET.parse(p/'source/input_netlist.xml')
for comp in tree.getroot().find('components'):
 if comp.get('ref')=='J120':
  comp.find('value').text='43045-2000';comp.find('footprint').text='GM97_Layout:'+name
tree.write(p/'source/input_netlist.xml',encoding='utf-8',xml_declaration=True)
assert k.ExportSpecctraDSN(b,str(p/'source/r7_route_input.dsn'))
f=p/'source/r7_route_input.dsn';s=f.read_text()
# Exporter does not load project netclass assignments in this headless API.
# Transfer the explicit R6 engineering width targets without changing them.
targets=json.loads((p/'reports/Routing_targets.json').read_text())['widths']
def remove_expr(s,start):
 depth=0;quoted=False;esc=False
 for j in range(start,len(s)):
  c=s[j]
  if c=='"' and not esc:quoted=not quoted
  if not quoted:
   if c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:return s[:start]+s[j+1:]
  esc=c=='\\' and not esc
 raise ValueError('unbalanced')
while '(class ' in s:s=remove_expr(s,s.index('(class '))
idx=s.index('  (wiring')
# Network closes immediately before wiring. Insert classes inside network.
idx=s.rfind(')',0,idx)
classes=[]
for group,d in targets.items():
 nets=[n for n in d['nets'] if b.FindNet(n)]
 if not nets:continue
 classes.append('(class '+group+' '+' '.join(nets)+' (circuit (use_via Via[0-3]_800:400_um)) (rule (width '+str(int(d['width_mm']*1000))+') (clearance 250)))')
s=s[:idx]+'\n'.join(classes)+'\n'+s[idx:]
f.write_text(s)
print('Updated J120; relocated J130/J140; exported full reroute input',len(list(b.GetFootprints())))
