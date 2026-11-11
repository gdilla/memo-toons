"""Image-to-video. Usage: python animate.py jobs.json
USE ONLY ON SHOTS WITH NO READABLE FACE (objects, hands, buildings). On faces it distorts eyes and mouths.
jobs: [{"image": png, "out": mp4, "prompt": "...", "duration": "5"}]"""
import sys, json, urllib.request, concurrent.futures as cf
import fal_client
def run(j):
    url = fal_client.upload_file(j["image"])
    for attempt in range(2):
        try:
            r = fal_client.subscribe("fal-ai/kling-video/v2.1/standard/image-to-video", arguments={
                "prompt": j["prompt"] + " 2D cel animation style, flat colors, clean lines, the background stays perfectly still, camera locked off.",
                "image_url": url, "duration": j.get("duration", "5"), "negative_prompt": "blur, distortion, morphing, extra limbs, text, realistic, 3d, camera movement"})
            urllib.request.urlretrieve(r["video"]["url"], j["out"]); return "ok " + j["out"].split("/")[-1]
        except Exception as e: err = str(e)[:200]
    return "FAILED " + j["out"] + " " + err
jobs = json.load(open(sys.argv[1]))
with cf.ThreadPoolExecutor(4) as ex:
    for n in ex.map(run, jobs): print(n, flush=True)
