"""Make a safe second frame for a two-frame cycle. Usage: python altframe.py shots_dir alt_dir
For each alt_dir/<name>.png, keeps only the region that really differs from shots_dir/<name>.png and writes shots_dir/<name>.b.png.
Rejects an alt frame if more than 20% of the picture changed (the model redrew the scene instead of one detail)."""
import sys, glob, os
import numpy as np
from PIL import Image, ImageChops, ImageFilter
S, A = sys.argv[1], sys.argv[2]
for f in sorted(glob.glob(A + "/*.png")):
    n = os.path.basename(f); a = Image.open(f"{S}/{n}").convert("RGB"); raw = Image.open(f).convert("RGB")
    # the edit model may return a slightly different aspect ratio: try a plain stretch and three crops, keep the best match
    hs = raw.resize((round(raw.width * a.height / raw.height), a.height), Image.LANCZOS); ex = max(hs.width - a.width, 0)
    cands = [raw.resize(a.size, Image.LANCZOS)] + [hs.crop((o, 0, o + a.width, a.height)) for o in (0, ex // 2, ex) if hs.width >= a.width]
    diff = lambda c: ImageChops.difference(a, c).convert("L").filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 22 else 0)
    d, b = min(((diff(c), c) for c in cands), key=lambda t: np.asarray(t[0]).mean())
    frac = np.asarray(d).mean() / 255
    if frac > 0.20 or frac < 0.0005: print(f"REJECT {n} changed {frac:.1%}"); continue
    m = d.filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(6))
    Image.composite(b, a, m).save(f"{S}/{n[:-4]}.b.png"); ys, xs = np.where(np.asarray(d) > 0)
    print(f"ok {n} changed {frac:.1%} bbox x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()}")
