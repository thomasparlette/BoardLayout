"""Add explicit DGND/PGND inner-layer return pours, then refill and save.
This does not establish current/thermal qualification or stitch surface pads.
"""
from pathlib import Path
import pcbnew as k,sys
f=Path(sys.argv[1]);b=k.LoadBoard(str(f))
for name,layer in [('DGND',k.In1_Cu),('PGND',k.In2_Cu)]:
 z=k.ZONE(b);z.SetLayer(layer);z.SetNetCode(b.FindNet(name).GetNetCode());z.SetLocalClearance(k.FromMM(.25));z.SetMinThickness(k.FromMM(.25));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
 outline=z.Outline();outline.NewOutline()
 for x,y in [(1,1),(139.93,1),(139.93,162.36),(1,162.36)]:outline.Append(k.FromMM(x),k.FromMM(y))
 b.Add(z)
assert k.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity();k.SaveBoard(str(f),b)
assert k.WriteDRCReport(b,str(f.with_suffix('.drc.txt')),k.EDA_UNITS_MILLIMETRES,True)
print('Return planes filled; inspect isolation, stitching and DRC before use.')
