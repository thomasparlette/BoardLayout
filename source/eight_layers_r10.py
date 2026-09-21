import safe_save_r8
from pathlib import Path
import pcbnew as k,json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));b.SetCopperLayerCount(8);k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
(p/'reports/R10_stackup_change.json').write_text(json.dumps({'copper_layers':8,'new_inner_layers':['In5.Cu','In6.Cu'],'board_thickness_mm':k.ToMM(b.GetDesignSettings().GetBoardThickness()),'mechanics':'Outline, mounting holes and component positions unchanged','qualification':'Provisional eight-layer routing candidate; no production copper weights or ampacity qualification.'},indent=2));print('Eight layers',b.GetCopperLayerCount())
