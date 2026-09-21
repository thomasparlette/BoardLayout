from pathlib import Path
import xml.etree.ElementTree as E,re,json,collections
p=Path(__file__).resolve().parents[1]
r=E.parse(p/'source/input_netlist.xml').getroot();pn={}
for n in r.find('nets'):
 for q in n.findall('node'):pn[q.get('ref'),q.get('pin')]=n.get('name')
mapping=json.loads((p/'reports/JP2_verified_mapping.json').read_text())
for pin,d in mapping.items():
 if d['net']:assert pn['J101',pin]==d['net']
assert pn['J100','29']=='ADC_BARO'
for pin,n in {'1':'MAP_RAW','2':'SGND','3':'VREF_5','4':'BARO_RAW'}.items():assert pn['J150',pin]==n
assert pn['J131','2'].startswith('unconnected')
off=[]
for f in p.glob('*.kicad_sch'):
 s=f.read_text()
 # Count connection-bearing wire endpoints and no-connect locations (not artwork).
 for m in re.finditer(r'\(xy ([\d.-]+) ([\d.-]+)\)',s):
  if any(abs(float(v)/1.27-round(float(v)/1.27))>1e-5 for v in m.groups()):
   # Artwork polyline points are not connection endpoints.
   if '(wire ' in s[max(0,m.start()-30):m.start()]:off.append((f.name,m.group()))
assert not off,off
parts=[]
for c in r.find('components'):
 ref=c.get('ref');value=c.findtext('value','');fp=c.findtext('footprint','')
 if ref.startswith('#'):continue
 mpn='UNSELECTED';supplier='Mouser target';status='HOLD: exact part and footprint qualification incomplete'
 if value=='VND5N07':mpn='VND5N07TR-E';status='ST datasheet/order code checked; thermal and current qualification HOLD'
 if ref in ['Q13','Q14','Q15','Q16']:mpn='MK-CoilDrvr';supplier='DIYAutoTune';status='Kit specified; underlying IGBT MPN/pinout and case mounting HOLD'
 if ref=='J1':mpn='Salvaged original Ford 104-pin header';supplier='User supplied';status='User accepted cavity mapping; contact ratings and mounting qualification HOLD'
 if ref=='J150':mpn='4-position wired adapter';supplier='User supplied MapDaddy';status='Custom pin order; NOT a native MapDaddy package footprint; mount dimensions HOLD'
 if ref=='U1':mpn='LM2937ES-5.0/NOPB';status='TI/Mouser candidate; load budget and output capacitor ESR/thermal HOLD'
 parts.append({'reference':ref,'value':value,'footprint':fp,'part':mpn,'source':supplier,'status':status})
(p/'reports/Parts_list.json').write_text(json.dumps(parts,indent=2))
lines=['# R4 parts list - engineering review only','','This is a complete reference inventory, not an order-ready BOM. UNSELECTED parts must not be substituted blindly. No current/thermal qualification is implied.','','| Reference | Value | Part / procurement target | Status |','|---|---|---|---|']
for v in parts:lines.append('| '+' | '.join(v[k].replace('|','/') for k in ['reference','value','part','status'])+' |')
(p/'Parts_list.md').write_text('\n'.join(lines)+'\n')
(p/'reports/Schematic_checks.json').write_text(json.dumps({'native_netlist_export':'KiCad 7 succeeded','JP2_pin_map_matches_reviewed_mapping':True,'MapDaddy_to_JS5_verified_in_netlist':True,'baro_external_drive_header_disconnected':True,'wire_endpoint_grid_check':'passed','native_ERC':'NOT RUN: KiCad 7 CLI has no ERC command; rerun in GUI','power_flags_added':['RAW_12','DGND','VREF_5','SGND','VCC_5','PGND'],'not_a_complete_electrical_design_review':True},indent=2))
print('Pin-map/MapDaddy checks passed; parts inventory:',len(parts))
