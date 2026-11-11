"""Image generator. Usage: python gen.py <project_dir> jobs.json   (MODEL=fal-ai/nano-banana-pro for the stronger model)
jobs.json: [{"out": "path.png", "prompt": "...", "refs": ["local image paths"]}]  (refs optional)
Every prompt gets <project_dir>/style.txt prepended, so the look and the standing rules live in one place. Refs are uploaded once and passed to nano-banana/edit."""
import os, sys, json, concurrent.futures as cf, urllib.request, functools
import fal_client
STYLE = open(sys.argv[1] + "/style.txt").read().strip() + " "
@functools.cache
def up(p): return fal_client.upload_file(p)
def run(job):
    refs = [up(p) for p in job.get("refs", [])]
    M = os.environ.get("MODEL", "fal-ai/nano-banana")
    ep, args = (M + "/edit", {"image_urls": refs}) if refs else (M, {})
    args.update(prompt=STYLE + job["prompt"], num_images=1, aspect_ratio="16:9", output_format="png")
    for attempt in range(3):
        try:
            r = fal_client.subscribe(ep, arguments=args)
            urllib.request.urlretrieve(r["images"][0]["url"], job["out"]); return "ok " + job["out"].split("/")[-1]
        except Exception as e: err = str(e)[:120]
    return "FAILED " + job["out"] + " " + err
jobs = json.load(open(sys.argv[2]))
with cf.ThreadPoolExecutor(6) as ex:
    for n in ex.map(run, jobs): print(n, flush=True)
