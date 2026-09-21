import subprocess,sys
from pathlib import Path
p=Path(__file__).parent
for ref in ['d26','d27','d28']:subprocess.run([sys.executable,str(p/f'move_{ref}_r10.py')],check=True)
