from pathlib import Path
import pcbnew as k
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));old=k.LoadBoard(str(p.parent/'GrandMarquis97_Layout_R6/GrandMarquis97_RevA.kicad_pcb'))
refs={x.GetReference():x for x in b.GetFootprints()};olds={x.GetReference():x for x in old.GetFootprints()}
j=refs['J120'];before={pd.GetNumber():pd.GetPosition() for pd in j.Pads() if pd.GetNumber()};j.SetPosition(k.VECTOR2I(k.FromMM(108),k.FromMM(154.44)))
# Remove tracks terminating at old connector pads; these need routing again.
ends=[k.VECTOR2I(q.x-k.FromMM(2),q.y) for q in before.values()] if abs(k.ToMM(j.GetPosition().x)-108)<.001 else list(before.values());removed=0
for t in list(b.GetTracks()):
 if any(t.GetStart()==q or t.GetEnd()==q for q in ends):b.Delete(t);removed+=1
for r in ['Q1','Q2']:
 ps={pd.GetNumber():pd for pd in olds[r].Pads()}
 for pd in refs[r].Pads():
  op=ps[pd.GetNumber()];pd.SetSize(op.GetSize());pd.SetDrillSize(op.GetDrillSize());pd.SetLocalClearance(op.GetLocalClearance())
k.SaveBoard(str(f),b);print('Moved J120 +2mm; removed',removed,'old endpoint tracks; restored original Q1/Q2 pads')
