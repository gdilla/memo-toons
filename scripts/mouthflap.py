"""Two-frame cartoon mouth flap. Usage: python mouthflap.py closed.png open.png audio.wav out.mp4
Mouth is open on frames where the audio is louder than 35% of its 90th-percentile level. Only pixels that differ between the two stills change."""
import sys, subprocess, os, tempfile
import numpy as np
from PIL import Image
closed, opened, wav, out = sys.argv[1:5]; FPS = 30
pcm = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", "48000", "-f", "s16le", "-"], capture_output=True, check=True).stdout, dtype=np.int16).astype(float)
n = 48000 // FPS; rms = np.array([np.sqrt((pcm[i:i + n] ** 2).mean()) for i in range(0, len(pcm) - n + 1, n)])
flap = rms > 0.35 * np.percentile(rms, 90)
for i in range(1, len(flap) - 1):                       # no single-frame flickers
    if flap[i - 1] == flap[i + 1] != flap[i]: flap[i] = flap[i - 1]
assert 0.15 < flap.mean() < 0.9, f"mouth open {flap.mean():.0%} of frames: threshold is off"
d = tempfile.mkdtemp(); size = (1920, 1080)
def prep(p): im = Image.open(p).convert("RGB"); s = max(size[0] / im.width, size[1] / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS); x, y = (im.width - size[0]) // 2, (im.height - size[1]) // 2; return im.crop((x, y, x + size[0], y + size[1]))
prep(closed).save(f"{d}/0.png"); prep(opened).save(f"{d}/1.png")
with open(f"{d}/l.txt", "w") as f:
    for v in flap: f.write(f"file '{d}/{int(v)}.png'\nduration {1 / FPS}\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{d}/l.txt", "-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "16", out], check=True)
print(f"{len(flap)} frames, mouth open {flap.mean():.0%}")
