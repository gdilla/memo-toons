"""Generate the sound effects named in <project_dir>/cues.json "effects". Usage: python sfx.py <project_dir> ; tries several endpoints, first that works wins."""
import sys, os, json, urllib.request, concurrent.futures as cf
import fal_client
P = sys.argv[1]; OUT = P + "/sfx"; os.makedirs(OUT, exist_ok=True)
FX = {k: (v["prompt"], v["seconds"]) for k, v in json.load(open(P + "/cues.json"))["effects"].items()}
ENDPOINTS = [
 ("fal-ai/elevenlabs/sound-effects/v2", lambda p, d: {"text": p, "duration_seconds": d, "prompt_influence": 0.5}),
 ("fal-ai/elevenlabs/sound-effects", lambda p, d: {"text": p, "duration_seconds": d}),
 ("cassetteai/sound-effects-generator", lambda p, d: {"prompt": p, "duration": max(1, int(round(d)))}),
 ("fal-ai/stable-audio", lambda p, d: {"prompt": p, "seconds_total": max(1, int(round(d)))}),
]
def find_url(r):
    for k in ("audio", "audio_file", "audio_url"):
        v = r.get(k)
        if isinstance(v, dict) and v.get("url"): return v["url"]
        if isinstance(v, str): return v
    raise KeyError(str(list(r))[:100])
def run(name):
    p, d = FX[name]; err = ""
    for ep, mk in ENDPOINTS:
        try:
            url = find_url(fal_client.subscribe(ep, arguments=mk(p, d)))
            ext = url.split("?")[0].rsplit(".", 1)[-1][:4]
            urllib.request.urlretrieve(url, f"{OUT}/{name}.{ext}"); return f"ok {name}.{ext} via {ep}"
        except Exception as e: err += f" [{ep}: {str(e)[:80]}]"
    return f"FAILED {name}{err}"
with cf.ThreadPoolExecutor(4) as ex:
    for n in ex.map(run, FX): print(n, flush=True)
