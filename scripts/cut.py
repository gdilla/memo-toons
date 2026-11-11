"""Cut the narration from an edit decision list. Usage: python cut.py <project_dir> <source_audio>
Reads edl.json and transcript/word.json. Writes the cut audio (edl "out") and cut_sheet.csv, which gives every line's
time on the new track. Storyboard against cut_sheet.csv, never against the raw memo.
edl.json: {"out": "cut.m4a", "pre": 0.06, "post": 0.14, "chapter_gaps": {"ch2": 1.5},
           "cuts": [{"chapter": "ch1", "from": 12.3, "to": 15.9, "text": "what is said"}]}
"from" is the start time of the first word to keep, "to" the START time of the last word to keep. Cuts play in list
order, so lines can be reordered. A chapter listed in chapter_gaps gets that much silence before it, for a title card."""
import json, subprocess, sys, csv
P, SRC = sys.argv[1], sys.argv[2]
E = json.load(open(f"{P}/edl.json")); words = json.load(open(f"{P}/transcript/word.json"))["chunks"]
PRE, POST, GAP = E.get("pre", 0.06), E.get("post", 0.14), E.get("chapter_gaps", {})
def end_of(t):   # whisper stretches word ends into the following silence: cap by the next word and a sane max length
    i = min(range(len(words)), key=lambda i: abs(words[i]["timestamp"][0] - t))
    s0, e0 = words[i]["timestamp"]; nxt = words[i + 1]["timestamp"][0] if i + 1 < len(words) else e0
    return min(e0, nxt - 0.03, s0 + 0.9)
parts, rows, t, prev = [], [], 0.0, None
for i, c in enumerate(E["cuts"]):
    ch = c["chapter"]; s, e = max(0, c["from"] - PRE), end_of(c["to"]) + POST
    assert e > s, f"cut {i} ({c['text'][:30]}) has no length"
    if ch != prev and ch in GAP:
        parts.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{GAP[ch]}[g{i}]"); t += GAP[ch]
    parts.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={e-s-0.015:.3f}:d=0.015[s{i}]")
    rows.append((ch, f"{t:.2f}", f"{t+e-s:.2f}", f"{s:.2f}", f"{e:.2f}", c["text"])); t += e - s; prev = ch
labels = "".join(f"[{p.split('[')[-1][:-1]}]" for p in parts)
open(f"{P}/.fc.txt", "w").write(";".join(parts) + f";{labels}concat=n={len(parts)}:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11[out]")
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", SRC, "-filter_complex_script", f"{P}/.fc.txt", "-map", "[out]", "-c:a", "aac", "-b:a", "192k", f"{P}/{E['out']}"], check=True)
with open(f"{P}/cut_sheet.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["chapter", "new_start", "new_end", "src_start", "src_end", "text"]); w.writerows(rows)
print(f"cuts={len(rows)} duration={t:.1f}s")
for r in rows: print(f"{r[0]:8} {r[1]:>6} {r[2]:>6}  {r[5][:70]}")
