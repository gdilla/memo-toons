"""Contact sheets for review. Usage: python contact.py <image_dir> <out_prefix>   -> <out_prefix>0.jpg, 1.jpg ... (9 per sheet)
Look at every sheet before showing anything to the person. Check head count, heights against the lineup, glasses, hair, clothes."""
import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(f for f in glob.glob(sys.argv[1] + "/*.png") if not f.endswith(".b.png")); O = sys.argv[2]
for k in range(0, len(fs), 9):
    S = Image.new("RGB", (3 * 640, 3 * 380), "black"); d = ImageDraw.Draw(S)
    for j, f in enumerate(fs[k:k + 9]):
        x, y = (j % 3) * 640, (j // 3) * 380
        S.paste(Image.open(f).convert("RGB").resize((640, 360)), (x, y)); d.text((x + 4, y + 362), os.path.basename(f), fill="white")
    S.save(f"{O}{k // 9}.jpg", quality=85)
print(len(fs), "images")
