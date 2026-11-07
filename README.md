# DanceBuddy

An agent that makes a non-humanoid plush character dance along with a human dancer. CS329Z, Fall 2026.
Tianrun Yan, Jackson Fang, Xi Liu.

Give it a video of one person dancing; it returns a video of the plush doing the same dance, side by side. MediaPipe
reads the dancer, an LLM agent plans how each move is shown on a body with no legs or neck, checks and revises its
plan, and Blender renders the result.

## 1. Install

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # uv (or: brew install uv)
brew install ffmpeg                                 # or: sudo apt install ffmpeg / winget install ffmpeg

git clone https://github.com/jacksonfang0205/dancebuddy-midpoint.git
cd dancebuddy-midpoint
uv sync --extra render                              # Python 3.13, packages and Blender (bpy), ~400 MB
cp .env.example .env                                # then put your OPENROUTER_API_KEY in .env
uv run python -m dancebuddy check                   # should end with "all set"
```

Get an OpenRouter key at https://openrouter.ai/keys. A run costs about $0.10.

## 2. Run the agent

Download a clip from `sample_videos/` in our
[sample folder](https://drive.google.com/drive/folders/13GeHAkxMEQeliprKsiq4-0cibBo163s2?usp=sharing) and save it as
`videos/dance1.mp4`. Then:

```bash
uv run python -m dancebuddy perceive videos/dance1.mp4 runs/dance1   # read the dancer
uv run python -m dancebuddy agent runs/dance1 --no-moves             # the agent plans, checks, revises
uv run python -m dancebuddy render runs/dance1 --engine eevee        # Blender
uv run python -m dancebuddy compose runs/dance1                      # -> runs/dance1/side_by_side.mp4
```

This uses the plush that ships with the repo (`assets/plush_soft`). Use your own video the same way, with a new run
folder. The agent's full conversation is saved in `runs/dance1/agent/trace.json`, every attempt in `attempt_N/`, and
cost in `summary.json`.

## 3. Other characters

**Our segmented plush** (`plush.glb` in the sample folder), or any GLB of a plush-like character:

```bash
uv run python -m dancebuddy character model path/to/plush.glb assets/plushseg   # add --yaw 90 if it faces sideways
cp assets/plush_motion_spec.json assets/plushseg_motion_spec.json
uv run python -m dancebuddy character rig assets/plushseg assets/plushseg_soft
```

Then add `--char assets/plushseg_soft` to `agent` and `render`.

**Let the agent make one** (needs `TRIPO_API_KEY` in `.env`, from https://platform.tripo3d.ai):

```bash
uv run python -m dancebuddy agent runs/dance1 --new-character blob --image picture.png   # or --prompt "..."
```

It generates the model, splits it into parts, rigs it as `assets/blob_soft`, and dances with it.

## 4. Evaluation

```bash
uv run pytest                                      # offline tests, no keys
uv run python -m evaluation prepare                # perception on the dances in evaluation/data/dances.json
uv run python -m evaluation run                    # baselines (pose_copy, plain_copy, planner) and agent ablations
uv run python -m evaluation metrics --arms         # -> evaluation/results/results.md
```

Without a key, `evaluation run --no-llm` runs only the baselines. Results vary slightly between runs because the LLM
is nondeterministic.

## Notes

- Agent options: `--no-moves` / `--no-looks` / `--no-geometry` turn a capability off; `--name X` writes to
  `runs/<clip>/X` (then pass `--systems X` to `render` and `compose`); `render --preview` is a fast grey preview.
- Have the Blender app instead of `bpy`? Run `uv sync` and set `BLENDER=/path/to/blender`.
- Code map: `perception/` (MediaPipe, beats), `planner/loop.py` (agent loop), `tools.py` (the agent's tools),
  `executor/` (motion copy, rendering), `critics/` (checks, vision review), `characters/` (Tripo, import),
  `blender/` (scripts run in Blender), `evaluation/`.
