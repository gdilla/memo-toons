"""Show exactly which pixels change in every two-frame cycle. Usage: python diffmap.py <project_dir>/shots <out_dir>
Writes one dimmed frame per cycle with the changed pixels in red. Any red on a face means the cycle will read as
twitching eyes or mouths: tighten that shot's boxes in cycles.json and rerun cyclemask.py."""
import sys, glob, os
import numpy as np
from PIL import Image, ImageChops, ImageDraw
S, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
for f in sorted(glob.glob(S + "/*.b.png")):
    n = os.path.basename(f)[:-6]; a = Image.open(f"{S}/{n}.png").convert("RGB"); b = Image.open(f).convert("RGB")
    d = np.asarray(ImageChops.difference(a, b).convert("L")) > 18
    arr = (np.asarray(a) * 0.45).astype(np.uint8); arr[d] = [255, 0, 0]
    im = Image.fromarray(arr).resize((960, 540)); ImageDraw.Draw(im).text((6, 6), n, fill="yellow"); im.save(f"{O}/{n}.png")
    print(f"{n}: {d.mean():.2%} of pixels change")
