from pathlib import Path
import subprocess,sys
p=Path(__file__).parent
for name in ['prune_floating_r8.py','prune_all_signal_stubs_r10.py','prune_signal_vias_r10.py','check_routed_board.py']:
 print('RUN',name,flush=True);subprocess.run([sys.executable,str(p/name)],check=True)
