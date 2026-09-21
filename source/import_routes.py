from pathlib import Path
import pcbnew as k,re,json,xml.etree.ElementTree as E,collections
p=Path(__file__).resolve().parents[1]
def parse(s):
 s=s.replace('(string_quote ")','(string_quote doublequote)');stack=[];root=None
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s):
  if t=='(':
   n=[]
   if stack:stack[-1].append(n)
   else:root=n
   stack.append(n)
  elif t==')':stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 assert not stack
 return root
def find(n,key):
 if isinstance(n,list):
  if n and n[0]==key:return n
  for c in n:
   r=find(c,key)
   if r is not None:return r
 return None
s=parse((p/'source/r7_route_final.ses').read_text());routes=find(s,'routes');res=find(routes,'resolution');assert res[1]=='um',res;factor=float(res[2])*1000
b=k.LoadBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'));assert len(list(b.GetTracks()))==0
layers={'F.Cu':k.F_Cu,'In1.Cu':k.In1_Cu,'In2.Cu':k.In2_Cu,'B.Cu':k.B_Cu}
def vec(x,y):return k.VECTOR2I(k.FromMM(float(x)/factor),k.FromMM(-float(y)/factor))
counts=collections.Counter()
for net in find(routes,'network_out')[1:]:
 if not isinstance(net,list) or net[0]!='net':continue
 ni=b.FindNet(net[1]);assert ni,net[1]
 for item in net[2:]:
  if item[0]=='wire':
   path=find(item,'path');assert path and path[1] in layers,item
   w=float(path[2])/factor;pts=path[3:];assert len(pts)%2==0
   for i in range(0,len(pts)-2,2):
    t=k.PCB_TRACK(b);t.SetStart(vec(*pts[i:i+2]));t.SetEnd(vec(*pts[i+2:i+4]));t.SetWidth(k.FromMM(w));t.SetLayer(layers[path[1]]);t.SetNetCode(ni.GetNetCode());b.Add(t);counts['tracks']+=1
  elif item[0]=='via':
   # The DSN defines only 0.8 mm / 0.4 mm through vias; names encode physical dimensions in um.
   assert '800:400' in item[1],item[1]
   v=k.PCB_VIA(b);v.SetPosition(vec(item[2],item[3]));v.SetWidth(k.FromMM(.8));v.SetDrill(k.FromMM(.4));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNetCode(ni.GetNetCode());b.Add(v);counts['vias']+=1
# Existing TO-92 pads have 0.22 mm edge spacing: local 0.20 mm low-voltage pad clearance.
for f in b.GetFootprints():
 if f.GetReference() in ['Q1','Q2']:
  for pd in f.Pads():pd.SetLocalClearance(k.FromMM(.2))
b.BuildConnectivity();k.SaveBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'),b)
(p/'reports/Imported_routing_counts.json').write_text(json.dumps(dict(counts),indent=2));print(dict(counts),'session coordinate scale',factor)
