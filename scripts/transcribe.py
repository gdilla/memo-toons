"""Transcribe a voice memo with word timestamps and speaker labels. Usage: python transcribe.py <audio> <project_dir>
Writes <project_dir>/transcript/seg.json (sentences, for reading) and word.json (per-word times, for cutting)."""
import json, sys, os, concurrent.futures as cf
import fal_client
src, out = sys.argv[1], sys.argv[2] + "/transcript"; os.makedirs(out, exist_ok=True)
url = fal_client.upload_file(src)
def run(level):
    return fal_client.subscribe("fal-ai/whisper", arguments={
        "audio_url": url, "task": "transcribe", "language": os.environ.get("LANGUAGE", "en"),
        "chunk_level": level, "diarize": True, "num_speakers": None, "version": "3"})
with cf.ThreadPoolExecutor() as ex:
    seg, word = ex.map(run, ["segment", "word"])
json.dump(seg, open(out + "/seg.json", "w"), indent=1); json.dump(word, open(out + "/word.json", "w"), indent=1)
for c in seg["chunks"]:
    print(f"[{c['timestamp'][0]:6.1f}-{c['timestamp'][1]:6.1f}] {c.get('speaker','')}: {c['text']}")
