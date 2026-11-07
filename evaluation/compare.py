"""The midpoint comparison: does the agent's plan beat the plain copy and a one-line fixed rule?

  python -m evaluation.compare runs/dance1                       # agent run in runs/dance1/agent, bundled plush
  python -m evaluation.compare runs/dance1 --agent seg_plush --char assets/plushseg_soft

Scores five plans on the same dance and character with the agent's own checks (accent recall passes at 0.6):
the plain copy, the agent's best plan, that plan without its emphasis hits, its emphasis with the knobs reset, and
the fixed rule (plain copy plus a full squash on every accent). No LLM calls.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from dancebuddy.actions.plan import default_plan
from dancebuddy.critics.numbers import check_curves
from dancebuddy.executor.retarget import retarget
from dancebuddy.knowledge import character
from dancebuddy.perception.signals import compute_signals
from dancebuddy.perception.video import load_keypoints


def plans(score: dict, agent_plan: dict) -> dict:
    plain = default_plan(score)
    rule = default_plan(score)
    rule["emphasis"] = [{"frame": a, "move": "squash", "size": 1.0} for a in score["accents"]]
    no_emph = copy.deepcopy(agent_plan)
    no_emph["emphasis"] = []
    knobs_reset = copy.deepcopy(agent_plan)
    knobs_reset["units"] = default_plan(score)["units"]
    return {"plain copy (all knobs 1.0)": plain,
            "agent's best plan": agent_plan,
            "agent's plan, emphasis removed": no_emph,
            "agent's emphasis, knobs reset to 1.0": knobs_reset,
            "fixed rule: full squash on every accent": rule}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run", type=Path)
    p.add_argument("--agent", default="agent", help="the agent's output folder in the run (default agent)")
    p.add_argument("--char", type=Path, default=Path("assets/plush_soft"))
    a = p.parse_args()

    kp = load_keypoints(a.run / "keypoints.npz")
    score = json.loads((a.run / "dance_score.json").read_text())
    agent_plan = json.loads((a.run / a.agent / "plan.json").read_text())
    rig, spec = character.rig(a.char), character.spec(a.char)
    signals = compute_signals(kp)

    rows = []
    for name, plan in plans(score, agent_plan).items():
        curves = retarget(kp, rig, signals=signals, beats=score["beats"], plan=plan, score=score)
        c = check_curves(curves, score, rig, spec)["checks"]
        rows.append((name, c["accents"]["value"], c["accents"]["passed"], c["completeness"]["lowest"]))

    lines = [f"Run {a.run}, character {a.char}", "",
             "| Plan | Accent recall | Passes (>= 0.6) | Lowest completeness |", "|---|---|---|---|"]
    lines += [f"| {n} | {v:.3f} | {'yes' if ok else 'no'} | {low:.2f} |" for n, v, ok, low in rows]
    text = "\n".join(lines)
    print(text)
    (a.run / "compare.md").write_text(text + "\n")


if __name__ == "__main__":
    main()
