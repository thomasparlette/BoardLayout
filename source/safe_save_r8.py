"""Atomic native-save wrapper with parse verification and bounded retries."""
import pcbnew as k,os
_original=k.SaveBoard
def save(path,b):
 tmp=str(path)+'.writing.kicad_pcb'
 for attempt in range(5):
  result=_original(tmp,b)
  try:
   with open(tmp,'rb') as stream:os.fsync(stream.fileno())
   verified=k.LoadBoard(tmp)
   assert len(list(verified.GetFootprints()))==len(list(b.GetFootprints()))
   assert len(list(verified.GetTracks()))==len(list(b.GetTracks()))
  except (OSError,AssertionError) as error:
   print('Native save retry',attempt+1,'result',result,flush=True)
   if attempt==4:raise
   continue
  os.replace(tmp,path);return result
k.SaveBoard=save
