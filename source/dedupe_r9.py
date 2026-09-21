from pathlib import Path
import safe_save_r8
import pcbnew as k,json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));seen={};removed=0
for t in list(b.GetTracks()):
 pts=tuple(sorted([(t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)]));key=(isinstance(t,k.PCB_VIA),t.GetNetCode(),t.GetLayer(),t.GetWidth(),pts,t.GetDrillValue() if isinstance(t,k.PCB_VIA) else 0)
 if key in seen:b.Delete(t);removed+=1
 else:seen[key]=t
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b);(p/'reports/Duplicate_copper_R9.json').write_text(json.dumps({'exact_duplicate_tracks_or_vias_removed':removed},indent=2));print('EXACT DUPLICATES',removed,flush=True)
