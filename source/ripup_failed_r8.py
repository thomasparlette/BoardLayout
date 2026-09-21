from pathlib import Path
import pcbnew as k,json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));report=json.loads((p/'reports/R8_signal_routes.json').read_text());names={n for n,reason in report['failed']};counts={}
for t in list(b.GetTracks()):
 if t.GetNetname() in names:counts[t.GetNetname()]=counts.get(t.GetNetname(),0)+1;b.Delete(t)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/R8_signal_ripup.json').write_text(json.dumps(counts,indent=2));print('Removed',sum(counts.values()),'items on',len(counts),'unfinished nets')
