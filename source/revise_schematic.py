"""One-time R3 -> R4 schematic migration. Input is the copied R3 project."""
from pathlib import Path
import re,uuid,json
p=Path(__file__).resolve().parents[1]
def forms(s):
    depth=0; start=0; quoted=False; escape=False; out=[]
    for i,c in enumerate(s):
        if quoted:
            if escape: escape=False
            elif c=='\\': escape=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True
        elif c=='(':
            if depth==1:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1:out.append((start,i+1,s[start:i+1]))
    assert depth==0
    return out
def edit(s, changes):
    for a,b,t in sorted(changes,reverse=True):s=s[:a]+t+s[b:]
    return s
# Verified against BOTH MS3XV30 Hardware 1.5 pages 205 and 206.
# Note Spark A is pin 12, not pin 11.
jp2={1:'TABLE_LOGIC',2:'FLEX_LOGIC',3:'NITROUS_LOGIC',4:None,5:None,6:None,
     7:'SPK_D',8:None,9:'SPK_B',10:'SPK_C',11:'ADC_MAF',12:'SPK_A',
     13:'ADC_SPARE13',14:'ADC_EGO2',15:'SPARE_PT4',16:'DATALOG_LOGIC',
     17:'TACH_CMD',18:'CAM_LOGIC',19:'LAUNCH_LOGIC',20:'SPARE_PK1',
     21:'IDLE_CMD',22:'SPARE_PK3',23:'AC_CUT_CMD',24:'FAN_CMD',25:None,26:None,
     27:'SPARE_PM2',28:'DGND',29:'SPARE_PK7',30:'DGND',31:'VCC_5',32:'DGND',33:'RAW_12',34:'RAW_12'}
names=['PH6_TABLE','PE2_FLEX','PH7_NITROUS_IN','PB7_SPK_H','PB5_SPK_F','PB6_SPK_G','PB3_SPK_D','PB4_SPK_E','PB1_SPK_B','PB2_SPK_C','AN11_EXT_MAP','PB0_SPK_A','AN13_SPARE','AN12_EGO2','PT4','PT6_DATALOG','PK0_TACH_OUT','PT2_CAM','PK2_LAUNCH','PK1_SPARE','PP2_IDLE','PK3_SPARE','PP4_NITROUS1','PP3_BOOST','PP6_VVT','PP5_NITROUS2','PM2_SPARE','GND','PK7_SPARE','GND','5V','GND','12V','12V']
def pins_update(t, names_by_num):
    changes=[]
    for a,b,x in forms(t):
        if x.startswith('(pin '):
            n=int(re.search(r'\(number "(\d+)"',x)[1])
            if n not in names_by_num:changes.append((a,b,''))
            else:changes.append((a,b,re.sub(r'\(name "[^"]*"', '(name "'+names_by_num[n]+'"',x, count=1)))
        elif x.startswith('(symbol '):changes.append((a,b,pins_update(x,names_by_num)))
    return edit(t,changes)
def fix_lib(s):
    changes=[]
    for a,b,t in forms(s):
        if t.startswith('(lib_symbols'):changes.append((a,b,fix_lib(t)))
        elif re.match(r'\(symbol "(?:GM97:)?MS3_JP2_34"',t):changes.append((a,b,pins_update(t,dict(enumerate(names,1)))))
        elif re.match(r'\(symbol "(?:GM97:)?MPX4250AP"',t):
            t=pins_update(t,{1:'MAP_SIGNAL',2:'SIGNAL_GND',3:'5V_SUPPLY',4:'BARO_SIGNAL'})
            t=t.replace('MPX4250AP','MAPDADDY_HARNESS_4')
            changes.append((a,b,t))
    return edit(s,changes)
def reconnect(s, ref, assignment):
    ff=forms(s); index=next(i for i,(_,_,t) in enumerate(ff) if t.startswith('(symbol (lib_id') and f'(property "Reference" "{ref}"' in t)
    a,b,inst=ff[index]; lib=re.search(r'\(lib_id "([^"]+)"',inst)[1]
    sx,sy=map(float,re.search(r'\(at ([^ ]+) ([^ ]+) 0\)',inst).groups())
    libs=next(t for _,_,t in ff if t.startswith('(lib_symbols'))
    sym=next(t for _,_,t in forms(libs) if t.startswith('(symbol "'+lib+'"'))
    coords={}
    for _,_,unit in forms(sym):
        if not unit.startswith('(symbol '):continue
        for _,_,pin in forms(unit):
            if pin.startswith('(pin '):
                n=int(re.search(r'\(number "(\d+)"',pin)[1]); x,y,ang=map(float,re.search(r'\(at ([^ ]+) ([^ ]+) ([^)]+)\)',pin).groups())
                coords[n]=(sx+x,sy-y,ang)
    end=b
    for aa,bb,t in ff[index+1:]:
        if not t.startswith(('(wire ','(global_label ','(no_connect ')):break
        end=bb
    new=[]
    for n,(x,y,ang) in coords.items():
        net=assignment.get(n)
        if net is None:new.append(f'(no_connect (at {x:g} {y:g}) (uuid {uuid.uuid4()}))');continue
        ex=x+(-7.62 if ang==0 else 7.62); la=180 if ang==0 else 0;just='right' if ang==0 else 'left'
        new.append(f'(wire (pts (xy {x:g} {y:g}) (xy {ex:g} {y:g})) (stroke (width 0) (type default)) (uuid {uuid.uuid4()}))')
        new.append(f'(global_label "{net}" (shape bidirectional) (at {ex:g} {y:g} {la}) (effects (font (size 1 1)) (justify {just})) (uuid {uuid.uuid4()}))')
    return s[:b]+'\n'+'\n'.join(new)+s[end:]
for f in [*p.glob('*.kicad_sch'),p/'GM97.kicad_sym']:
    s=fix_lib(f.read_text())
    s=s.replace('"AUX_AN6"','"BARO_RAW"').replace('"ADC_SPARE6"','"ADC_BARO"')
    if f.name=='04_ms3_expansion.kicad_sch':s=reconnect(s,'J101',jp2)
    if f.name=='09_map_battery.kicad_sch':
        s=s.replace('"GM97:MPX4250AP"','"GM97:MAPDADDY_HARNESS_4"').replace('"U2"','"J150"').replace('"MPX4250AP"','"MapDaddy wired interface - user supplied module"').replace('"GM97_Layout:Candidate_U2"','"GM97_Layout:MapDaddy_Harness_4"')
        s=s.replace('250 kPa absolute sensor, original V3.0 family; package geometry to verify','Custom adapter pin numbering, NOT sensor native pinout. MAP plus baro to JS5; module geometry/calibration HOLD.')
        s=reconnect(s,'J150',{1:'MAP_RAW',2:'SGND',3:'VREF_5',4:'BARO_RAW'})
    if f.name=='24_service.kicad_sch':
        # Remove external drive access to the repurposed dedicated barometric input.
        ff=forms(s);changes=[]
        for i,(a,b,t) in enumerate(ff):
            if t.startswith('(global_label "BARO_RAW"'):
                aa,bb,wire=ff[i-1]; xy=re.search(r'\(xy ([^ ]+) ([^)]+)',wire)
                changes += [(aa,bb,f'(no_connect (at {xy[1]} {xy[2]}) (uuid {uuid.uuid4()}))'),(a,b,'')]
        s=edit(s,changes)
    s=s.replace('"BIP373"','"MK-CoilDrvr IGBT - PINOUT HOLD"')
    s=s.replace('(rev "R2 WASTED SPARK - REVIEW")','(rev "R4 CURRENT-TARGET REVIEW")')
    f.write_text(s)
(p/'reports/JP2_verified_mapping.json').write_text(json.dumps({str(i):{'hardware_function':names[i-1],'net':jp2[i]} for i in range(1,35)},indent=2))
print('R4 schematic changes applied. Export native netlist next.')
