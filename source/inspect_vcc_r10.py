from pathlib import Path
exec(Path(__file__).with_name('signal_smallvia_r8.py').read_text().split('widths=')[0],globals())
seen=set()
for fp in b.GetFootprints():
 for pd in fp.Pads():
  if pd.GetNetname()!='VCC_5' or pd.m_Uuid.AsString() in seen:continue
  group=island((mm(pd.GetPosition().x),mm(pd.GetPosition().y)),pd.GetNetCode(),[i for i,l in enumerate(cu) if pd.IsOnLayer(l)]);seen.update(group)
  print([(it.GetParent().GetReference(),it.GetNumber(),mm(it.GetPosition().x),mm(it.GetPosition().y)) for it in group.values() if isinstance(it,k.PAD)])
