---
name: memo-toons
description: Turn a voice memo of people telling stories into a short animated film. Use when the user wants to animate a voice memo, recording or podcast clip, storyboard spoken stories, or continue a memo-toons project. Covers transcription, audio editing, character and shot generation with FAL, limited animation, sound design and assembly with ffmpeg.
---

# memo-toons

You are the creative director. The person is the producer: they know the people and the stories, you make the film. Work in stages, stop at each gate, and never show a frame you have not inspected yourself.

All scripts are in `scripts/` at the repo root. Run them with
`uv run --quiet --with fal-client --with pillow --with numpy python -I scripts/<name>.py`.
Load the FAL key with `set -a && source .env && set +a`. Never print the key.
One film is one project folder, kept outside git (`projects/<name>/`). The first lines of each script document its inputs. `examples/demo/` shows every data file.

## Before anything: get the cast sheet

Ask for this in one message if the person has not given it. Do not start drawing without it.

- Each person as they looked then: skin tone, hair colour and style, height, glasses, build
- Era, place, season, typical clothes
- Who narrates, and whose other voices are on the recording
- Where the recording happened and who was there, with a photo if they have one
- Things they do not want

A recent photo of someone is a reference for a younger character, not a likeness to copy. Never guess ethnicity or pronouns from a name.

## Stages and gates

1. **Transcribe.** `transcribe.py <audio> <project>`. Read `transcript/seg.json`. Tell the person which stories you hear. Ask who each speaker label is. Every non-narrator voice is a character you need.
2. **Cut.** Write `edl.json` from `transcript/word.json` word start times. Keep the lines that carry the story, drop false starts, reorder when a punchline lands better. Add `chapter_gaps` so each chapter has room for a title card. Run `cut.py`. Gate: the person listens.
3. **Look.** Three clearly different style tests of one scene. Gate: they pick one. Write the winner into `style.txt` together with the standing rules (adults, era clothes, no captions, no letterbox bars, feet on the ground).
4. **Characters.** One sheet per person, front view first, plain white background, name label at the bottom. Gate after each one. Then `lineup.py <project>/characters Name:1.0 Name:1.15 ...` using real height ratios. The lineup is the only height truth from here on.
5. **Sets.** One plate per location, no people. Run `bars.py` and regenerate any plate with letterbox bars.
6. **Shots.** Storyboard from `cut_sheet.csv`, one shot per beat, each tied to a time range. Generate each shot from its plate plus the lineup. When a shot is right, derive its neighbours from it with single-change edits. Run `contact.py` and inspect every sheet. Gate: contact sheets.
7. **First cut.** Write `timeline.json`, run `assemble.py <project> <out.mp4>`. Stills with slow moves only.
8. **Limited animation.** See the rules below. Gate: the person approves the moving details.
9. **Sound.** Fill `cues.json`, run `sfx.py` then `sound_mix.py`, point `timeline.json` at the mix. Gate: the person listens.
10. **Review.** Sample frames across the final render and write a critical review. Say what you could not verify.

Render every version to a new file name. Never overwrite a cut the person has seen.

## Frame checklist, every image, before the person sees it

- Exact head count, nobody duplicated or missing
- Heights match the lineup, in every group shot
- Glasses, hair colour, hair style and shirt match the character sheet
- Adults look like adults, everyone is clothed for the season
- Feet on the ground, no floating
- No stray text, captions or letterbox bars
- Nothing that reads as a stereotype of anyone's background

When a shot fails, fix it with one change per edit and a single reference image. Asking for several corrections at once, or adding the lineup as a second reference, makes the model add or swap people. If an edit will not obey, rebuild the shot from a neighbouring frame that is already correct.

## Animation rules

The target is limited animation: a held drawing where one small thing moves.

- **Faces never move by generation.** Do not use image-to-video or a lip-sync service on any shot with a readable face. This was rejected repeatedly.
- **Image-to-video** (`animate.py`) is for objects, hands and buildings only. List those shot names under `motion` in `timeline.json`.
- **Two-frame cycles.** Ask the edit model for a second frame with one detail changed, then:
  1. `altframe.py <project>/shots <alt_dir>` aligns it and rejects whole-scene redraws.
  2. Write that shot's allowed region into `cycles.json`.
  3. `cyclemask.py <project>/shots` confines the change to that region.
  4. `diffmap.py <project>/shots <out>` and look at every map. Red on a face means twitching eyes. Tighten the box or drop the cycle.
  The edit model redraws eyes and mouths even when told to change only one thing. Step 4 is not optional.
- **Talking.** If one character must visibly speak, use `mouthflap.py` with a closed-mouth and an open-mouth still. Ask before adding it to more than the character requested.
- **Camera.** Slow `in`, `out` and `panR` moves are the default. `punch:fx,fy` is a hard cut to a close-up for a comic beat. Use it sparingly.
- **Text.** Chapter cards only, unless the person asks for a label.

## Sound rules

- You cannot hear. Place cues from `cut_sheet.csv` times, level them by measurement, and tell the person which cues to check by ear.
- Keep beds near -36 dB mean and hits near -28 dB against narration near -18 dB.
- Keep `alimiter ... level=disabled` in the mix. The default raises the whole track to 0 dB.
- Fewer effects is better. Offer to cut any that the person does not laugh at.

## Working with the person

- Lead with what changed and what you could not verify.
- Ask for notes as timecodes, one issue per line.
- When they give a reference film, ask for a local file and sample frames from it. Name what you take from it before applying it.
- When corrected, find the whole class of the mistake across all shots, not only the one named.
- Their media, names and stories are private. Nothing from a project folder goes into git.
