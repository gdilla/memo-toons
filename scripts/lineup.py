"""Stitch the first (front-view) figure from each character sheet into one labelled lineup. No AI involved.
Usage: python lineup.py <characters_dir> Name[:relative_height] ...   e.g.  Ana:1.0 Ben:1.0 Cal:1.15
Reads <characters_dir>/<Name>.png, writes <characters_dir>/lineup.png."""
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
C = sys.argv[1]; spec = [a.split(":") for a in sys.argv[2:]]; names = [s[0] for s in spec]; rel = {s[0]: float(s[1]) if len(s) > 1 else 1.0 for s in spec}
figs = []
for n in names:
    im = Image.open(f"{C}/{n}.png").convert("RGB"); a = np.asarray(im)
    h = a.shape[0]; body = a[: int(h * 0.85)]                      # ignore the label row at the bottom
    ink = (body < 235).any(axis=2).any(axis=0)                     # columns with non-white pixels
    cols = np.where(ink)[0]; x0 = cols[0]
    gaps = np.where(np.diff(cols) > 15)[0]                         # first big gap ends the first figure
    x1 = cols[gaps[0]] if len(gaps) else cols[-1]
    rows = np.where((body[:, x0:x1 + 1] < 235).any(axis=2).any(axis=1))[0]
    figs.append(im.crop((x0 - 10, rows[0] - 10, x1 + 10, rows[-1] + 10)))
# heights: every figure is scaled relative to the first one, so the lineup is the single source of truth for who is taller
base = figs[0].height / rel[names[0]]
figs = [f.resize((int(f.width * base * rel[n] / f.height), int(base * rel[n])), Image.LANCZOS) for f, n in zip(figs, names)]
H = max(f.height for f in figs); pad = 60
W = sum(f.width for f in figs) + pad * (len(figs) + 1)
out = Image.new("RGB", (W, H + 120), "white"); d = ImageDraw.Draw(out)
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
x = pad
for f, n in zip(figs, names):
    out.paste(f, (x, H - f.height)); d.text((x + f.width / 2, H + 30), n.upper(), fill="black", font=font, anchor="mt"); x += f.width + pad
out.save(f"{C}/lineup.png"); print(out.size)
