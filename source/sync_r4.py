from pathlib import Path
import pcbnew as k,xml.etree.ElementTree as E,json
p=Path(__file__).resolve().parents[1]
exec((p/'source/revise_schematic.py').read_text().split('# Verified against')[0])
bf=p/'GrandMarquis97_RevA.kicad_pcb';s=bf.read_text();bf.write_text(edit(s,[(a,z,'') for a,z,t in forms(s) if t.startswith(('(segment ','(via '))]))
b=k.LoadBoard(str(bf))
old=next(f for f in b.GetFootprints() if f.GetReference()=='U2')
new=k.FOOTPRINT(b);new.SetReference('J150');new.SetValue('MapDaddy wired interface');new.SetFPID(k.LIB_ID('GM97_Layout','MapDaddy_Harness_4'));new.SetPath(old.GetPath());new.SetAttributes(k.FP_THROUGH_HOLE)
for i in range(4):
 pd=k.PAD(new);pd.SetNumber(str(i+1));pd.SetShape(k.PAD_SHAPE_RECT if i==0 else k.PAD_SHAPE_CIRCLE);pd.SetAttribute(k.PAD_ATTRIB_PTH);pd.SetSize(k.VECTOR2I(k.FromMM(1.8),k.FromMM(1.8)));pd.SetDrillSize(k.VECTOR2I(k.FromMM(1),k.FromMM(1)));layers=k.LSET.AllCuMask();layers.AddLayer(k.F_Mask);layers.AddLayer(k.B_Mask);pd.SetLayerSet(layers);pd.SetPosition(k.VECTOR2I(0,k.FromMM(i*2.54)));pd.SetPos0(k.VECTOR2I(0,k.FromMM(i*2.54)));new.Add(pd)
k.FootprintSave(str(p/'GM97_Layout.pretty'),new)
new.SetPosition(old.GetPosition());new.SetOrientation(old.GetOrientation());b.Add(new);b.Remove(old)
r=E.parse(p/'source/input_netlist.xml').getroot();pins={};values={c.get('ref'):c.findtext('value') for c in r.find('components')}
for n in r.find('nets'):
 name=n.get('name')
 if name.startswith('unconnected'):continue
 ni=b.FindNet(name)
 if not ni:ni=k.NETINFO_ITEM(b,name);b.Add(ni)
 for node in n.findall('node'):pins[node.get('ref'),node.get('pin')]=ni
bottom={f'R{i}' for i in range(7,24)}|{f'C{i}' for i in range(12,28)}|{f'D{i}' for i in range(5,15)}
moved=[]
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref in values:f.SetValue(values[ref])
 for pd in f.Pads():
  n=pins.get((ref,pd.GetNumber()));pd.SetNetCode(n.GetNetCode() if n else 0)
 if ref in bottom and f.GetLayer()==k.F_Cu:f.Flip(f.GetPosition(),False);moved.append(ref)
 f.Reference().SetLayer(k.B_Fab if f.GetLayer()==k.B_Cu else k.F_Fab);f.Value().SetVisible(False)
for d in b.Drawings():
 if hasattr(d,'GetText') and ('ROUTING' in d.GetText() or 'R3 ' in d.GetText()):d.SetText('R4 REVIEW - NOT FOR FABRICATION')
ns=b.GetDesignSettings().m_NetSettings;ns.m_DefaultNetClass.SetClearance(k.FromMM(.25));ns.m_DefaultNetClass.SetTrackWidth(k.FromMM(.25));ns.m_DefaultNetClass.SetViaDiameter(k.FromMM(.8));ns.m_DefaultNetClass.SetViaDrill(k.FromMM(.4))
b.BuildConnectivity();k.SaveBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'),b)
assert k.ExportSpecctraDSN(b,str(p/'source/route_input.dsn'))
(p/'reports/Bottom_placement.json').write_text(json.dumps({'moved_to_B_Cu':sorted(moved),'case_clearance':'UNVERIFIED: verify underside component height and case/clip clearances before assembly'},indent=2))
print('Synchronized PCB; old copper removed; underside parts:',len(moved))
