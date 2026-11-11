# memo-toons

Turn a rambling voice memo of friends telling old stories into a short animated film.

You record the stories. An AI coding agent (built with Claude Code) acts as creative director: it transcribes the memo, cuts the audio so it flows, storyboards it, draws every shot, adds sound, and assembles a 16:9 video. You give notes like a producer.

The style is limited animation: held drawings, slow pans and zooms, hard punch-in cuts, and one small thing moving per shot (smoke, tears, a kicking leg). That is a deliberate choice. See [What we learned](#what-we-learned-the-hard-way).

No media is included in this repo. You bring your own memo, photos and music.

## What you need

- macOS or Linux with `ffmpeg` and [`uv`](https://docs.astral.sh/uv/)
- A [FAL](https://fal.ai) API key (paid, per image and per clip; check their pricing page before a long session)
- Claude Code, or another agent that can run shell commands and look at images
- A voice memo, ideally 5 to 10 minutes, of people telling stories
- Optional: a photo of each person, a photo of where you recorded, a song for the credits

## Quick start

```bash
git clone https://github.com/gdilla/memo-toons && cd memo-toons
cp .env.example .env          # paste your FAL key
uv run --with pillow --with numpy python scripts/selftest.py   # offline check, no cost
mkdir -p projects/my-film     # projects/ is git-ignored, your media stays private
cp ~/Downloads/my-memo.m4a projects/my-film/
claude
```

Then paste the first prompt from [PROMPTS.md](PROMPTS.md). The skill in `.claude/skills/memo-toons/` loads automatically and walks the agent through the stages below.

## The pipeline

Each stage ends at a gate where the agent shows you something and waits for a yes.

| # | Stage | Script | You approve |
|---|---|---|---|
| 1 | Transcribe with word timings and speakers | `transcribe.py` | Who each speaker is |
| 2 | Cut the audio from an edit list | `cut.py` | The trimmed story, by listening |
| 3 | Pick a look from three style tests | `gen.py` | One style |
| 4 | Character sheets, then a height lineup | `gen.py`, `lineup.py` | Each character, one at a time |
| 5 | Background plates | `gen.py`, `bars.py` | The sets |
| 6 | Storyboard and draw every shot | `gen.py`, `contact.py` | Contact sheets |
| 7 | Assemble with camera moves | `assemble.py` | A first full cut |
| 8 | Limited animation | `altframe.py`, `cyclemask.py`, `diffmap.py`, `mouthflap.py`, `animate.py` | Each moving detail |
| 9 | Sound effects and credits music | `sfx.py`, `sound_mix.py` | The mix, by listening |
| 10 | Final render and review | `assemble.py` | The film |

Run any script with `uv run --with fal-client --with pillow --with numpy python scripts/<name>.py`. Each script's first lines document its inputs.

## Project folder

Everything about one film lives in one folder. The scripts hold no story content.

```
projects/my-film/
  my-memo.m4a          your recording
  transcript/          seg.json, word.json
  edl.json             which lines to keep, in what order
  cut_sheet.csv        every kept line with its time on the new track
  style.txt            the look and the standing rules, prepended to every image prompt
  characters/          one sheet per person, plus lineup.png (the source of truth for heights)
  backgrounds/         one plate per set
  shots/               one still per shot; name.b.png is the second frame of a cycle
  cycles.json          per shot, the only regions allowed to move
  motion/              video clips, objects only
  sfx/, cues.json      sound effects and where they land
  timeline.json        the edit: cards, shots, camera moves, credits
```

`examples/demo/` has a small made-up set of these files to copy from.

## What we learned the hard way

These rules are built into the skill. They cost real money and several angry notes to find.

1. **Never let AI video touch a face.** Image-to-video distorts eyes and mouths. Use it only for objects, hands and buildings.
2. **AI lip-sync was rejected twice.** A two-frame mouth flap driven by audio level (`mouthflap.py`) worked first time.
3. **"Change only the smoke" is not obeyed.** Image edit models quietly redraw eyes and mouths. Every two-frame cycle must be masked to its intended region (`cyclemask.py`) and the change map viewed (`diffmap.py`) before rendering.
4. **A lineup image is the only reliable height control.** Stitch it from the character sheets with real ratios and check every group shot against it.
5. **One correct frame, then single-change edits.** Generating a group scene from scratch drifts. Deriving the next shot from an approved one holds.
6. **Count heads and check glasses on every frame** before the person sees it.
7. **Storyboard against the cut audio, not the raw memo.** Timings come from `cut_sheet.csv`.
8. **The agent cannot hear.** Sound levels are computed, so a person must listen before sign-off.
9. **Ask who is speaking.** Voices that are not the main narrator are characters the agent does not know exist.
10. **Skip on-screen text.** Chapter cards are fine. Floating labels got removed every time.

## Limits

- Title cards default to the macOS Helvetica font. Set `"font"` in `timeline.json` on Linux.
- Do not use copyrighted music in anything you publish. For a private watch party it is your call.
- Draw real people only with their consent, and never commit their photos.
