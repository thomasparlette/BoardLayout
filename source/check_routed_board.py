from pathlib import Path
import pcbnew as k,xml.etree.ElementTree as E,json,re,collections
p=Path(__file__).resolve().parents[1];b=k.LoadBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'));expected={}
for n in E.parse(p/'source/input_netlist.xml').getroot().find('nets'):
 if n.attrib['name'].startswith('unconnected'):continue
 for node in n.findall('node'):
  if node.attrib['ref']!='J121':expected[node.attrib['ref'],node.attrib['pin']]=n.attrib['name']
actual={};pads=[]
for f in b.GetFootprints():
 for pd in f.Pads():
  if pd.GetNetname():actual[f.GetReference(),pd.GetNumber()]=pd.GetNetname()
  pads.append({'ref':f.GetReference(),'pin':pd.GetNumber(),'x':k.ToMM(pd.GetPosition().x),'y':k.ToMM(pd.GetPosition().y),'w':k.ToMM(pd.GetSize().x),'h':k.ToMM(pd.GetSize().y),'drill':k.ToMM(pd.GetDrillSize().x),'net':pd.GetNetname(),'smd':pd.GetAttribute()==k.PAD_ATTRIB_SMD})
assert actual==expected,{'missing':[(q,n,actual.get(q)) for q,n in expected.items() if actual.get(q)!=n],'extra':[(q,n) for q,n in actual.items() if q not in expected]}
removed=set(json.loads((p/'source/first_board_changes.json').read_text())['removed_references']);assert not removed & {f.GetReference() for f in b.GetFootprints()}
tr=[]
for t in b.GetTracks():
 a={'x1':k.ToMM(t.GetStart().x),'y1':k.ToMM(t.GetStart().y),'x2':k.ToMM(t.GetEnd().x),'y2':k.ToMM(t.GetEnd().y),'width':k.ToMM(t.GetWidth()),'layer':b.GetLayerName(t.GetLayer()),'net':t.GetNetname(),'via':isinstance(t,k.PCB_VIA)}
 tr.append(a)
assert k.WriteDRCReport(b,str(p/'reports/After_routing_DRC.txt'),k.EDA_UNITS_MILLIMETRES,True)
s=(p/'reports/After_routing_DRC.txt').read_text();c=collections.Counter(re.findall(r'^\[([^]]+)\]',s,re.M));result={'footprints':len(list(b.GetFootprints())),'assigned_pin_net_pairs_verified':len(expected),'tracks':sum(not x['via'] for x in tr),'vias':sum(x['via'] for x in tr),'DRC_counts':dict(c),'removed_components_absent':True,'manufacturing_release':False}
(p/'reports/Routing_validation.json').write_text(json.dumps(result,indent=2));(p/'source/routed_geometry.json').write_text(json.dumps({'pads':pads,'tracks':tr}));print(json.dumps(result))
