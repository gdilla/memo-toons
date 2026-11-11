import sys, glob, os
from PIL import Image
import numpy as np
for f in sorted(glob.glob(sys.argv[1]+"/*.png")):
    a = np.asarray(Image.open(f).convert("L")); rows = a.mean(axis=1)
    top = int(np.argmax(rows > 20)); bot = int(np.argmax(rows[::-1] > 20))
    if top + bot > 10: print(f"{os.path.basename(f)} top={top} bottom={bot} of {a.shape[0]}")
