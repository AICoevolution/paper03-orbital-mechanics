#!/usr/bin/env python3
"""
Figure 3 (Human-AI): Merge Deep Dive / Topic Switching / Metrics Spoofing into a single overlay plot.

This produces the same 2x2 layout as the AI-AI Figure 3:
  - SGI over turns (overlay by condition)
  - Orbital velocity over turns (overlay by condition)
  - Early turns (1-3) in phase space
  - Late turns (last 3) in phase space

Inputs (expected in paper03/analysis/results):
  - human_run_01_deep.json                       -> A_baseline
  - 09_steering_2026-01-19_22-58-59_human_session.json -> E_real_metrics
  - 09_steering_2026-01-20_13-27-51_human_session.json -> F_adversarial

Output (paper03/figures):
  - FIG3_human_sessions_fig3_trajectory.png
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results"
FIGURES_DIR = SCRIPT_DIR.parent.parent / "figures"

SESSION_FILES = [
    RESULTS_DIR / "human_run_01_deep.json",
    RESULTS_DIR / "09_steering_2026-01-19_22-58-59_human_session.json",
    RESULTS_DIR / "09_steering_2026-01-20_13-27-51_human_session.json",
]

# Human-friendly condition labels for the paper figures
COND_LABELS = {
    "A_baseline": "A (Deep Dive)",
    "E_real_metrics": "E (Topic Switching)",
    "F_adversarial": "F (Metrics Spoofing)",
}

COND_NOTES = [
    "A: Deep Dive (human-led sustained topic)",
    "E: Topic Switching (human-led sudden shifts)",
    "F: Metrics Spoofing (injected adversarial telemetry; conversation remained normal/helpful)",
]


def _load_results(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "results" in data:
        return data.get("results") or []
    if isinstance(data, list):
        return data
    # fallback (unlikely): a single result dict
    if isinstance(data, dict) and "turns" in data:
        return [data]
    return []


def _merge_human_sessions(paths: List[Path]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    for p in paths:
        if not p.exists():
            print(f"[WARN] Missing session file: {p}")
            continue
        r = _load_results(p)
        if not r:
            print(f"[WARN] No results found in: {p}")
            continue
        # each human JSON should have one result (one condition)
        merged.extend(r)
    return merged


def render_fig3(results: List[Dict[str, Any]], output_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import seaborn as sns
    except ImportError as e:
        print(f"Visualization requires matplotlib, seaborn: {e}")
        return

    # Organize by condition (match 09_steering_experiment.py Fig3 behavior)
    condition_data = defaultdict(lambda: {"sgis": [], "velocities": [], "turns": []})

    for r in results:
        cond = r.get("condition_name", "unknown")
        turns = r.get("turns", []) or []
        for t in turns:
            turn_num = t.get("turn_number", 0)
            rm = t.get("real_metrics", {}) or {}

            # Prefer turn-pair metrics
            sgi = rm.get("turn_pair_sgi_mean") or rm.get("turn_pair_sgi_latest") or rm.get("sgi_mean")
            vel = rm.get("orbital_velocity_latest") or rm.get("orbital_velocity_mean") or rm.get("velocity_mean")

            # mirror the filter used in Fig3 (avoid pathological 180 spikes from per-message only)
            if sgi is not None and vel is not None and float(vel) < 170:
                condition_data[cond]["sgis"].append(float(sgi))
                condition_data[cond]["velocities"].append(float(vel))
                condition_data[cond]["turns"].append(int(turn_num))

    if not condition_data:
        print("[Fig3 Human Merge] No valid trajectory data found")
        return

    colors = {
        "A_baseline": "#3498db",
        "E_real_metrics": "#1abc9c",
        "F_adversarial": "#e74c3c",
    }

    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle(
        "Figure 3 (Human-AI): Temporal Trajectory Analysis — Do Conditions Converge?",
        fontsize=14,
        fontweight="bold",
    )

    # Top-left: SGI over turns
    ax1 = axes[0, 0]
    for cond, data in condition_data.items():
        if not data["turns"]:
            continue
        turn_sgi = defaultdict(list)
        for t, s in zip(data["turns"], data["sgis"]):
            turn_sgi[t].append(s)
        turns_sorted = sorted(turn_sgi.keys())
        sgi_means = [float(np.mean(turn_sgi[t])) for t in turns_sorted]
        sgi_stds = [float(np.std(turn_sgi[t])) for t in turns_sorted]
        color = colors.get(cond, "#7f8c8d")
        label = COND_LABELS.get(cond, cond)
        ax1.plot(turns_sorted, sgi_means, "o-", color=color, label=label, linewidth=2, markersize=8)
        ax1.fill_between(
            turns_sorted,
            [m - s for m, s in zip(sgi_means, sgi_stds)],
            [m + s for m, s in zip(sgi_means, sgi_stds)],
            alpha=0.2,
            color=color,
        )
    ax1.set_xlabel("Turn Number", fontsize=12)
    ax1.set_ylabel("SGI (mean +/- std)", fontsize=12)
    ax1.set_title("SGI Evolution Over Turns", fontsize=12)
    ax1.set_ylim(0, 1.5)
    ax1.legend(loc="upper right", fontsize=9)

    # Top-right: Velocity over turns
    ax2 = axes[0, 1]
    for cond, data in condition_data.items():
        if not data["turns"]:
            continue
        turn_vel = defaultdict(list)
        for t, v in zip(data["turns"], data["velocities"]):
            turn_vel[t].append(v)
        turns_sorted = sorted(turn_vel.keys())
        vel_means = [float(np.mean(turn_vel[t])) for t in turns_sorted]
        vel_stds = [float(np.std(turn_vel[t])) for t in turns_sorted]
        color = colors.get(cond, "#7f8c8d")
        label = COND_LABELS.get(cond, cond)
        ax2.plot(turns_sorted, vel_means, "s-", color=color, label=label, linewidth=2, markersize=8)
        ax2.fill_between(
            turns_sorted,
            [m - s for m, s in zip(vel_means, vel_stds)],
            [m + s for m, s in zip(vel_means, vel_stds)],
            alpha=0.2,
            color=color,
        )
    ax2.set_xlabel("Turn Number", fontsize=12)
    ax2.set_ylabel("Orbital Velocity (mean +/- std)", fontsize=12)
    ax2.set_title("Orbital Velocity (Turn-Pair) Over Turns", fontsize=12)
    ax2.set_ylim(0, 180)
    ax2.legend(loc="upper right", fontsize=9)

    early_k = 3
    late_k = 3

    # Bottom-left: Early turns in phase space
    ax3 = axes[1, 0]
    ax3.add_patch(plt.Rectangle((0.3, 0), 0.9, 45, alpha=0.15, color="green", label="Coherence Region"))
    for cond, data in condition_data.items():
        early_sgi = [s for s, t in zip(data["sgis"], data["turns"]) if t <= early_k]
        early_vel = [v for v, t in zip(data["velocities"], data["turns"]) if t <= early_k]
        if not early_sgi:
            continue
        color = colors.get(cond, "#7f8c8d")
        label = COND_LABELS.get(cond, cond)
        ax3.scatter(early_sgi, early_vel, color=color, alpha=0.7, s=100, label=label, edgecolor="black")
        ax3.scatter(
            [float(np.mean(early_sgi))],
            [float(np.mean(early_vel))],
            color=color,
            s=300,
            marker="*",
            edgecolor="black",
            linewidth=2,
        )
    ax3.set_xlabel("SGI", fontsize=12)
    ax3.set_ylabel("Orbital Velocity (degrees)", fontsize=12)
    ax3.set_title(f"Early Turns (1-{early_k}): Where Do Conditions START?", fontsize=12)
    ax3.set_xlim(0, 1.5)
    ax3.set_ylim(0, 180)
    ax3.legend(loc="upper right", fontsize=9)

    # Bottom-right: Late turns (last k) in phase space (per condition)
    ax4 = axes[1, 1]
    ax4.add_patch(plt.Rectangle((0.3, 0), 0.9, 45, alpha=0.15, color="green", label="Coherence Region"))
    for cond, data in condition_data.items():
        valid_turns = [t for t in data["turns"] if isinstance(t, int)]
        if not valid_turns:
            continue
        max_turn = max(valid_turns)
        cutoff = max_turn - late_k + 1
        late_sgi = [s for s, t in zip(data["sgis"], data["turns"]) if t >= cutoff]
        late_vel = [v for v, t in zip(data["velocities"], data["turns"]) if t >= cutoff]
        if not late_sgi:
            continue
        color = colors.get(cond, "#7f8c8d")
        label = COND_LABELS.get(cond, cond)
        ax4.scatter(late_sgi, late_vel, color=color, alpha=0.7, s=100, label=label, edgecolor="black")
        ax4.scatter(
            [float(np.mean(late_sgi))],
            [float(np.mean(late_vel))],
            color=color,
            s=300,
            marker="*",
            edgecolor="black",
            linewidth=2,
        )
    ax4.set_xlabel("SGI", fontsize=12)
    ax4.set_ylabel("Orbital Velocity (degrees)", fontsize=12)
    ax4.set_title(f"Late Turns (last {late_k}): Where Do Conditions END?", fontsize=12)
    ax4.set_xlim(0, 1.5)
    ax4.set_ylim(0, 180)
    ax4.legend(loc="upper right", fontsize=9)

    # Add human-session context note
    fig.text(
        0.5,
        0.01,
        " | ".join(COND_NOTES),
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    output_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_png, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"[OK] Saved merged human Fig3 to: {output_png}")
    plt.show()


def main() -> None:
    merged = _merge_human_sessions(SESSION_FILES)
    if not merged:
        print("[ERROR] No sessions loaded; cannot render merged Fig3.")
        raise SystemExit(1)

    out = FIGURES_DIR / "FIG3_human_sessions_fig3_trajectory.png"
    render_fig3(merged, out)


if __name__ == "__main__":
    main()


