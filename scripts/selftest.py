"""Offline check that the assembler and cycle tools work on this machine. No API key, no cost.
Usage: uv run --with pillow --with numpy python scripts/selftest.py
Builds placeholder media for examples/demo in a temp folder, masks a cycle, renders the film, checks its length."""
import json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.abspath(__file__)); demo = os.path.join(here, "..", "examples", "demo")
T = tempfile.mkdtemp(); [shutil.copy(os.path.join(demo, f), T) for f in os.listdir(demo)]
os.makedirs(T + "/shots"); os.makedirs(T + "/motion")
tl = json.load(open(T + "/timeline.json")); end = tl["timeline"][-1][0]
if sys.platform != "darwin": tl["font"] = subprocess.check_output(["fc-match", "-f", "%{file}", "sans"]).decode()
json.dump(tl, open(T + "/timeline.json", "w"))
for i, e in enumerate(x for x in tl["timeline"] if x[1] == "shot"):
    im = Image.new("RGB", (1344, 768), (40 + 40 * i, 90, 120)); ImageDraw.Draw(im).rectangle((900, 80, 1100, 220), fill="white"); im.save(f"{T}/shots/{e[2]}.png")
b = Image.open(T + "/shots/s05_smoke_alarm.png"); d = ImageDraw.Draw(b)
d.rectangle((900, 80, 1100, 220), fill="red"); d.rectangle((100, 500, 200, 600), fill="red")      # second box is outside the allowed region
b.save(T + "/shots/s05_smoke_alarm.b.png")
run = lambda *a: subprocess.run(a, check=True)
run("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", str(end), T + "/mix.m4a")
run("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=1920x1080:r=30", "-t", "3", "-pix_fmt", "yuv420p", T + "/motion/s04_batter_pour.mp4")
run(sys.executable, here + "/cyclemask.py", T + "/shots")
m = Image.open(T + "/shots/s05_smoke_alarm.b.png").convert("RGB")
assert m.getpixel((150, 550)) != (255, 0, 0), "cyclemask let a change through outside its box"
assert m.getpixel((1000, 150)) == (255, 0, 0), "cyclemask removed the change inside its box"
run(sys.executable, here + "/assemble.py", T, T + "/out.mp4")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", T + "/out.mp4"]))
assert abs(dur - end) < 0.5, f"film is {dur}s, timeline says {end}s"
print(f"selftest ok: {dur:.1f}s film rendered, cycle mask held"); shutil.rmtree(T)
