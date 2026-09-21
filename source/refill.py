from pathlib import Path
import pcbnew as k
p=Path(__file__).resolve().parents[1]/'GrandMarquis97_RevA.kicad_pcb'
b=k.LoadBoard(str(p));k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(p),b)
