from pathlib import Path
import json,pcbnew as k
p=Path(__file__).resolve().parents[1];f=p/'reports/Routing_targets.json';d=json.loads(f.read_text());protected=['RAW_12','PWR_FUSED']
for c in d['widths'].values():c['nets']=[n for n in c['nets'] if n not in protected]
d['widths']['Protected_control_supply']={'width_mm':1.0,'nets':protected}
d['protected_supply_basis']='Planned F1 is 1 A. This does not reduce injector or auxiliary load-path targets. Fuse selection and coordination are still required.'
f.write_text(json.dumps(d,indent=2))
b=k.LoadBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'))
for l in [k.F_Cu,k.B_Cu]:
 if any(z.GetLayer()==l and z.GetNetname()=='PGND' and not z.GetIsRuleArea() for z in b.Zones()):continue
 z=k.ZONE(b);z.SetLayer(l);z.SetNetCode(b.FindNet('PGND').GetNetCode());z.SetLocalClearance(k.FromMM(.25));z.SetMinThickness(k.FromMM(.5));z.SetPadConnection(k.ZONE_CONNECTION_FULL);o=z.Outline();o.NewOutline()
 for x,y in [(1,1),(139.93,1),(139.93,162.36),(1,162.36)]:o.Append(k.FromMM(x),k.FromMM(y))
 b.Add(z)
for fp in b.GetFootprints():
 if fp.GetReference() not in ['NT1','NT2']:continue
 x,y=k.ToMM(fp.GetPosition().x),k.ToMM(fp.GetPosition().y);z=k.ZONE(b);z.SetLayer(k.F_Cu);z.SetIsRuleArea(True);z.SetDoNotAllowCopperPour(True);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False);o=z.Outline();o.NewOutline()
 for xx,yy in [(x-2.3,y-1.3),(x+2.3,y-1.3),(x+2.3,y+1.3),(x-2.3,y+1.3)]:o.Append(k.FromMM(xx),k.FromMM(yy))
 b.Add(z)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'),b)
print('Added outer PGND fills and protected-supply target; verify native DRC')
