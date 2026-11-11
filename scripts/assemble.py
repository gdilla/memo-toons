"""Assemble the film. Usage: python assemble.py <project_dir> <out.mp4>
Reads <project_dir>/timeline.json. Times are seconds on the audio track; each entry runs until the next one starts.
  [t, "card", "TEXT"]                         black title card
  [t, "shot", name, move, [[label, a, b]]]    shots/<name>.png with a camera move; labels optional
  [t, "clip", name]                           motion/<name>.mp4 stretched to fit the slot
  [t, "credits"]                              crawl of the "credits" text, ending on "credits_image" if given
  [t, "end"]
Moves: hold, in, out, inL, inR, panR, punch:fx,fy (hold, then hard cut to a close-up at that point).
A shot plays motion/<name>.mp4 only if its name is listed in "motion". A shot with shots/<name>.b.png flips between the two frames."""
import subprocess, sys, os, json, concurrent.futures as cf
L, OUT = sys.argv[1], sys.argv[2]; W = f"{L}/.build"; os.makedirs(W, exist_ok=True)
P = json.load(open(f"{L}/timeline.json"))
AUDIO, CREDITS, CREDITS_IMAGE = P["audio"], P.get("credits", ""), P.get("credits_image")
MOTION, TRIM_MOTION, CYCLE = set(P.get("motion", [])), set(P.get("motion_trim", [])), P.get("cycle_seconds", {})
FONT = P.get("font", "/System/Library/Fonts/Helvetica.ttc"); FPS = 30
TL = [(e[0], None if e[1] == "end" else tuple(e[1:])) for e in P["timeline"]]
assert all(a[0] < b[0] for a, b in zip(TL, TL[1:])), "timeline times must increase"
assert TL[-1][1] is None, 'timeline must finish with [t, "end"]'


from PIL import Image, ImageDraw, ImageFont
def text_png(path, text, size, bg=None, pad=40, border=0, line_gap=18):
    """Render text to a PNG. bg=None gives a transparent label sized to the text; bg='black' gives a full 1920x1080 card."""
    font = ImageFont.truetype(FONT, size); lines = text.split("\n")
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths = [d0.textlength(l, font=font) for l in lines]; lh = size + line_gap
    tw, th = int(max(widths)) + 2 * pad, lh * len(lines) + 2 * pad
    im = Image.new("RGBA", (1920, 1080) if bg else (tw, th), bg or (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy = ((1920 - tw) // 2, (1080 - th) // 2) if bg else (0, 0)
    for i, (l, w) in enumerate(zip(lines, widths)):
        x, y = ox + pad + (tw - 2 * pad - w) / 2, oy + pad + i * lh
        d.text((x, y), l, font=font, fill="white", stroke_width=border, stroke_fill="black")
    im.save(path); return im.size

def credits_png(path):
    """Crawl text, then the optional closing image. Returns (total height, height of the closing image that stays on screen)."""
    text_png(path + ".a.png", CREDITS.strip(), 56, line_gap=22)
    A = Image.open(path + ".a.png")
    if not CREDITS_IMAGE: A.save(path); return A.height, 0
    F = Image.open(f"{L}/{CREDITS_IMAGE}").convert("RGBA"); F = F.resize((F.width * 220 // F.height, 220), Image.LANCZOS)
    gap = 500; w = max(A.width, F.width); tail = F.height
    im = Image.new("RGBA", (w, A.height + gap + tail), (0, 0, 0, 0)); y = 0
    for part, g in ((A, gap), (F, 0)): im.paste(part, ((w - part.width) // 2, y)); y += part.height + g
    im.save(path); return im.height, tail

def zoom(move, frames):
    if move.startswith("punch:"):                        # hold the full frame, then hard cut to a close-up at (fx, fy)
        fx, fy = move[6:].split(","); n = int(frames * 0.5); zz = f"if(lt(on,{n}),1,1.7)"
        return (zz, f"if(lt(on,{n}),0,max(0,min(iw-iw/zoom,{fx}*iw-iw/zoom/2)))", f"if(lt(on,{n}),0,max(0,min(ih-ih/zoom,{fy}*ih-ih/zoom/2)))")
    z_in, z_out = f"1+0.12*on/{frames}", f"1.12-0.12*on/{frames}"
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    return {
        "hold": (f"1.02", cx, cy),
        "in":   (z_in, cx, cy),
        "out":  (z_out, cx, cy),
        "inR":  (z_in, "iw-(iw/zoom)", cy),             # push toward the right side of frame
        "inL":  (z_in, "0", cy),
        "panR": ("1.15", f"(iw-iw/zoom)*on/{frames}", cy),
    }[move]

def render(i, t0, entry, t1):
    dur = t1 - t0; out = f"{W}/seg_{i:03d}.mp4"; frames = int(dur * FPS)
    common = ["-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", out]
    if entry[0] == "card":
        png = f"{W}/card_{i:03d}.png"; text_png(png, entry[1], 88, bg="black")
        vf = f"fade=t=in:d=0.3,fade=t=out:st={dur-0.3:.2f}:d=0.3"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-t", f"{dur:.3f}", "-vf", vf] + common
    elif entry[0] == "shot":
        z, x, y = zoom(entry[2] if len(entry) > 2 else "in", frames); nin = 1
        mp4 = f"{L}/motion/{entry[1]}.mp4"
        if entry[1] in MOTION and os.path.exists(mp4):
            sd = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",mp4]))
            inputs = ["-i", mp4]
            k = 1.0 if entry[1] in TRIM_MOTION else dur/sd
            fc = f"[0:v]setpts=PTS*{k:.4f},scale=1920:1080:flags=lanczos,fps={FPS}[v0]"; last = "v0"
        else:
            alt = f"{L}/shots/{entry[1]}.b.png"
            if os.path.exists(alt):                      # two-frame cycle: only the changed detail flips, the rest of the drawing holds
                p = CYCLE.get(entry[1], 0.5); nin = 2
                inputs = ["-loop", "1", "-framerate", str(FPS), "-i", f"{L}/shots/{entry[1]}.png", "-loop", "1", "-framerate", str(FPS), "-i", alt]
                fc = (f"[0:v]scale=3840:2160:flags=lanczos[a];[1:v]scale=3840:2160:flags=lanczos[b];[a][b]overlay=enable='gte(mod(t,{p}),{p/2})'[c];"
                      f"[c]zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1920x1080:fps={FPS}[v0]"); last = "v0"
            else:
                inputs = ["-loop", "1", "-i", f"{L}/shots/{entry[1]}.png"]
                fc = f"[0:v]scale=3840:2160:flags=lanczos,zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s=1920x1080:fps={FPS}[v0]"; last = "v0"
        for k, (label, a, b) in enumerate(entry[3] if len(entry) > 3 else ()):
            png = f"{W}/label_{i:03d}_{k}.png"; text_png(png, label, 120, border=6)
            inputs += ["-loop", "1", "-i", png]
            fc += f";[{last}][{k+nin}:v]overlay=x='-w+((W-w)/2+w)*min(1,(t-{a-t0:.2f})/0.2)':y=H*0.12:enable='between(t,{a-t0:.2f},{b-t0:.2f})'[v{k+1}]"; last = f"v{k+1}"   # labels slide in from the left
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-t", f"{dur:.3f}", "-filter_complex", fc, "-map", f"[{last}]"] + common
    elif entry[0] == "clip":
        src = f"{L}/motion/{entry[1]}.mp4"
        sd = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",src]))
        vf = f"setpts=PTS*{dur/sd:.4f},scale=1920:1080:flags=lanczos,fps={FPS}"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", f"{dur:.3f}", "-vf", vf] + common
    else:
        png = f"{W}/credits.png"; th, tail = credits_png(png)
        stop = 540 - (th - tail / 2) if tail else -th   # with a closing image the crawl stops on it and holds 5s; otherwise it scrolls off
        speed = (1080 - stop) / (dur - 5 if tail else dur)
        fc = f"[0:v][1:v]overlay=x=(W-w)/2:y='max(H-t*{speed:.1f},{stop:.0f})'[v];[v]fade=t=out:st={dur-3:.2f}:d=3[out]"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r={FPS}", "-loop", "1", "-i", png,
               "-t", f"{dur:.3f}", "-filter_complex", fc, "-map", "[out]"] + common
    subprocess.run(cmd, check=True); return out

jobs = [(i, TL[i][0], TL[i][1], TL[i+1][0]) for i in range(len(TL) - 1)]
with cf.ThreadPoolExecutor(6) as ex: segs = list(ex.map(lambda j: render(*j), jobs))
open(f"{W}/list.txt", "w").write("".join(f"file '{s}'\n" for s in segs))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{W}/list.txt", "-i", f"{L}/{AUDIO}",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", len(segs), "segments")
