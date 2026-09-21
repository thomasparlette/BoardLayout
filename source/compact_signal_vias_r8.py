from pathlib import Path
import pcbnew as k,json,collections
p=Path(__file__).resolve().parents[1];f=p/'GrandMarquis97_RevA.kicad_pcb';b=k.LoadBoard(str(f));power={n for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() if c['width_mm']>.25 for n in c['nets']};power.update(['LEGACY_INJ1','LEGACY_INJ2']);counts=collections.Counter()
for v in b.GetTracks():
 if isinstance(v,k.PCB_VIA) and v.GetNetname() not in power and k.ToMM(v.GetWidth())>.6:
  v.SetWidth(k.FromMM(.6));v.SetDrill(k.FromMM(.3));counts[v.GetNetname()]+=1
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(f),b)
f=p/'GrandMarquis97_RevA.kicad_pro';x=json.loads(f.read_text())
for c in x['net_settings']['classes']:
 if c['name']=='Default':c['via_diameter']=.6;c['via_drill']=.3
f.write_text(json.dumps(x,indent=2))
(p/'reports/R8_signal_via_sizes.json').write_text(json.dumps({'by_net':dict(counts),'diameter_mm':.6,'drill_mm':.3,'power_nets_unchanged':sorted(power)},indent=2));print(sum(counts.values()),'signal vias resized')
