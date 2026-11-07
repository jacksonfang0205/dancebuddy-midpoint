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

Why commands and not a chat? Once started, the agent works on its own: it chooses its tools, checks and revises until it is done, so it needs no turns from you. Running it as a command keeps every run reproducible (same inputs, cached LLM calls, full trace saved) and easy to evaluate. A chat mode, where you can ask for changes like "spin the whole time", is planned.

This uses the plush that ships with the repo (`assets/plush_soft`). Use your own video the same way, with a new run
folder. The agent's full conversation is saved in `runs/dance1/agent/trace.json`, every attempt in `attempt_N/`, and
cost in `summary.json`.

## 3. Your own character

Use our segmented plush (`plush.glb` in the sample folder) or any GLB of a plush-like character:

```bash
uv run python -m dancebuddy character model path/to/plush.glb assets/plushseg   # add --yaw 90 if it faces sideways
cp assets/plush_motion_spec.json assets/plushseg_motion_spec.json
uv run python -m dancebuddy character rig assets/plushseg assets/plushseg_soft
```

Then add `--char assets/plushseg_soft` to `agent` and `render`.

## 4. Reproduce the evaluation

The midpoint report compares the agent's plan with the plain copy and a one-line fixed rule (a full squash on every
accent). After running the agent as in Section 2:

```bash
uv run python -m evaluation.compare runs/dance1                                         # bundled plush
uv run python -m evaluation.compare runs/dance1 --agent seg --char assets/plushseg_soft # segmented plush (Section 3)
```

For the second line, run the agent first with `--char assets/plushseg_soft --name seg`. Each prints the accent table
and saves it to `runs/dance1/compare.md`. The agent's numbers vary a little between runs (the LLM is
nondeterministic); the plain copy and fixed rule are exact.

The full evaluation module (all baselines and ablations over the dances in `evaluation/data/dances.json`):

```bash
uv run python -m evaluation prepare && uv run python -m evaluation run && uv run python -m evaluation metrics --arms
```

## Notes

- Agent options: `--no-moves` / `--no-looks` / `--no-geometry` turn a capability off; `--name X` writes to
  `runs/<clip>/X` (then pass `--systems X` to `render` and `compose`); `render --preview` is a fast grey preview.
- Offline tests (no keys): `uv run pytest`.
- Have the Blender app instead of `bpy`? Run `uv sync` and set `BLENDER=/path/to/blender`.
- Code map: `perception/` (MediaPipe, beats), `planner/loop.py` (agent loop), `tools.py` (the agent's tools),
  `executor/` (motion copy, rendering), `critics/` (checks, vision review), `characters/` (Tripo, import),
  `blender/` (scripts run in Blender), `evaluation/`.
