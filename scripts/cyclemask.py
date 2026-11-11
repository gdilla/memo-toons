"""Confine every two-frame cycle to the detail it is meant to animate. Usage: python cyclemask.py <project_dir>/shots
The edit model quietly redraws eyes and mouths in second frames, which reads as darting eyes when cycled.
<project_dir>/cycles.json lists, per shot, the only regions [x0, y0, x1, y1] (fractions of the frame) allowed to differ from the base still.
A .b.png with no entry here is deleted. Run after altframe.py, then look at diffmap.py output before rendering."""
import sys, glob, os, json
from PIL import Image, ImageDraw, ImageFilter
S = sys.argv[1]; BOXES = json.load(open(S + "/../cycles.json"))
for f in sorted(glob.glob(S + "/*.b.png")):
    n = os.path.basename(f)[:-6]
    if n not in BOXES: os.remove(f); print("removed", n); continue
    a, b = Image.open(f"{S}/{n}.png").convert("RGB"), Image.open(f).convert("RGB")
    m = Image.new("L", a.size, 0); d = ImageDraw.Draw(m)
    for x0, y0, x1, y1 in BOXES[n]: d.rectangle((x0 * a.width, y0 * a.height, x1 * a.width, y1 * a.height), fill=255)
    Image.composite(b, a, m.filter(ImageFilter.GaussianBlur(4))).save(f); print("masked", n)
