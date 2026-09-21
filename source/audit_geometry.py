from pathlib import Path
import pcbnew as k,json,collections,math
p=Path(__file__).resolve().parents[1];b=k.LoadBoard(str(p/'GrandMarquis97_RevA.kicad_pcb'));targets={n:c['width_mm'] for c in json.loads((p/'reports/Routing_targets.json').read_text())['widths'].values() for n in c['nets']};rings=[];lengths=collections.defaultdict(float);necks=collections.defaultdict(lambda:{'count':0,'length_mm':0})
for f in b.GetFootprints():
 for pad in f.Pads():
  if pad.GetAttribute()!=k.PAD_ATTRIB_PTH:continue
  ring=k.ToMM(min(pad.GetSize().x-pad.GetDrillSize().x,pad.GetSize().y-pad.GetDrillSize().y))/2
  if ring<.254-1e-6:rings.append({'reference':f.GetReference(),'pad':pad.GetNumber(),'estimated_min_ring_mm':ring})
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):continue
 n=t.GetNetname();l=k.ToMM(t.GetLength());w=k.ToMM(t.GetWidth());lengths[f'{n} / {b.GetLayerName(t.GetLayer())} / {w:.3f} mm']+=l
 if w<targets.get(n,.2)-1e-6:
  a=necks[n];a['count']+=1;a['length_mm']+=l
(p/'reports/Geometry_current_review.json').write_text(json.dumps({'status':'NOT an ampacity calculation or thermal qualification','copper_assumption_um':70,'pth_ring_screen_threshold_mm':.254,'pth_ring_candidates_below_threshold':rings,'track_lengths_by_net_layer_width_mm':dict(lengths),'segments_below_nominal_trunk_target':dict(necks),'notes':['Parallel traces must be reviewed as complete networks; simply adding their widths does not establish current sharing.','Signal traces use the separately stated 0.20 mm default; 0.25 mm inventory target is not a current rating.','The hole screen is conservative; verify actual package lead dimensions and manufacturer stackup-specific rules.']},indent=2))
print('PTH ring candidates',len(rings),rings)
