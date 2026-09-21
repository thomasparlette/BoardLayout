from pathlib import Path
import safe_save_r8,pcbnew as k,json
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));b.SetCopperLayerCount(6)
for name,layer in [('PGND',k.In3_Cu),('DGND',k.In4_Cu)]:
 z=k.ZONE(b);z.SetLayer(layer);z.SetNetCode(b.FindNet(name).GetNetCode());z.SetLocalClearance(k.FromMM(.25));z.SetMinThickness(k.FromMM(.2));z.SetPadConnection(k.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS)
 z.Outline().NewOutline()
 for x,y in [(1,1),(139.93,1),(139.93,162.36),(1,162.36)]:z.Outline().Append(k.FromMM(x),k.FromMM(y))
 b.Add(z)
# Existing through vias span the complete layer stack. Extend mounting keepouts to new layers.
for z in b.Zones():
 if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
  ls=z.GetLayerSet();ls.AddLayer(k.In3_Cu);ls.AddLayer(k.In4_Cu);z.SetLayerSet(ls)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
(p/'reports/R9_stackup_change.json').write_text(json.dumps({'copper_layers':6,'new_inner_layers':{'In3.Cu':'PGND plane with limited routing','In4.Cu':'DGND plane with limited routing'},'board_thickness_mm':k.ToMM(b.GetDesignSettings().GetBoardThickness()),'mechanics':'outline, holes and placement preserved','status':'Provisional six-layer option; final JLC stackup and copper weights not qualified.'},indent=2));print('Six layer board saved')
