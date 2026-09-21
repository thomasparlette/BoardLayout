from pathlib import Path
import re,json
p=Path(__file__).resolve().parents[1]
exec((p/'source/revise_schematic.py').read_text().split('# Verified against')[0])
f=p/'source/route_input.dsn';s=f.read_text().replace('(string_quote ")','(string_quote doublequote)');a,b,net=next(x for x in forms(s) if x[2].startswith('(network'))
classes={'Injector_5A_target':(2.0,[f'INJECTOR_{i}' for i in range(1,9)]),'Aux_3A_target':(1.2,['IAC','FAN_CONTROL','FUEL_PUMP_CONTROL','AC_WOT_CUTOUT','MIL','AUX_TACH','WB1_RELAY_LOW','WB2_RELAY_LOW','TRANS_SS1','TRANS_SS2','TRANS_TCC','TRANS_EPC']), 'Coil_peak_unverified':(3.0,[f'COIL_{i}' for i in range(1,5)]),'Shared_power_unverified':(4.0,['PGND','ACTUATOR_12','VPWR']),'Rails_unverified':(.6,['DGND','SGND','VCC_5','REG_5','VREF_5','VDDA_5','VREF_FILTER','CASE_GND']),'Protected_control_supply':(1.0,['RAW_12','PWR_FUSED'])}
allnets=[re.match(r'\(net ([^\s)]+)',t)[1] for _,_,t in forms(net) if t.startswith('(net ')]
used={n for _,ns in classes.values() for n in ns};classes['Signal']=(.25,[n for n in allnets if n not in used])
entries=[]
for name,(width,ns) in classes.items():
 ns=[n for n in ns if n in allnets]
 entries.append(f'(class {name} '+ ' '.join(ns)+f' (circuit (use_via Via[0-3]_800:400_um)) (rule (width {width*1000:g}) (clearance 250.1)))')
net=edit(net,[(aa,bb,'') for aa,bb,t in forms(net) if t.startswith('(class ')])
net=net[:-1]+'\n'+'\n'.join(entries)+'\n)';f.write_text((s[:a]+net+s[b:]).replace('(string_quote doublequote)','(string_quote ")'))
widths={n:{'width_mm':w,'nets':ns} for n,(w,ns) in classes.items()}
widths['Injector_5A_target']['basis']='Conservative legacy geometry retained pending complete-path review. Branch basis is 0.7 A maximum RMS and 1.2 A design peak with one injector active. Key name is retained for compatibility and does not mean 5 A per branch.'
widths['Coil_peak_unverified']['basis']='Conservative legacy geometry retained pending complete-path review. Branch design peak is 1.5 A with one ignition channel active; 1.5 A is also used as a conservative continuous sizing case until dwell is measured.'
(p/'reports/Routing_targets.json').write_text(json.dumps({'status':'UNQUALIFIED ENGINEERING TARGETS; not current ratings','copper_assumption_um_by_layer':{'F.Cu':35,'In1.Cu-In6.Cu':17.5,'B.Cu':35},'branch_current_basis':{'maximum_simultaneous_injector_channels':1,'injector_rms_A_each':.7,'injector_peak_A_each_design':1.2,'injector_all_eight_hypothetical_rms_A':5.6,'injector_aggregate_budget_A':6.0,'maximum_simultaneous_ignition_channels':1,'ignition_peak_A_each_design':1.5,'ignition_continuous_sizing_A_each':1.5,'source':'User-supplied design basis, 2026-09-21; bench verification pending'},'widths':widths,'holds':['via transitions need parallel-via sizing','pad escape neckdowns need assessment','shared ground total current unknown','thermal/connector limits unverified'],'protected_supply_basis':'Planned F1 is 1 A. This does not reduce injector or auxiliary load-path targets. Fuse selection and coordination are still required.'},indent=2))
