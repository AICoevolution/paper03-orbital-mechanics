#!/usr/bin/env python3
"""
Figure 5: Human-AI Session Comparison

Generates a 3-panel comparison of:
- Session A (Deep Dive): Baseline, no metrics shown
- Session B (Whiplash): Real metrics shown, topic switches
- Session C (Gaslight): Adversarial metrics injected

Usage:
    python 15_human_session_comparison.py

Output:
    figures/FIG5_human_session_comparison.png
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Paths
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results"
FIGURES_DIR = SCRIPT_DIR.parent.parent / "figures"

# Session files (update if filenames change)
SESSION_FILES = {
    "A_deep": RESULTS_DIR / "human_run_01_deep.json",
    "B_whiplash": RESULTS_DIR / "09_steering_2026-01-19_22-58-59_human_session.json",
    "C_gaslight": RESULTS_DIR / "09_steering_2026-01-20_13-27-51_human_session.json",
}

SESSION_LABELS = {
    "A_deep": "Session A: Deep Dive\n(Baseline - No metrics shown)",
    "B_whiplash": "Session B: Topic Switching\n(Real metrics shown)",
    "C_gaslight": "Session C: Metrics Spoofing\n(Adversarial telemetry injected)",
}

SESSION_COLORS = {
    "A_deep": "#3498db",      # Blue
    "B_whiplash": "#9b59b6",  # Purple
    "C_gaslight": "#e74c3c",  # Red
}

STATE_COLORS = {
    "stable": "#2ecc71",     # Green
    "protostar": "#f39c12",  # Orange
    "split": "#e74c3c",      # Red
}


def load_session(filepath: Path) -> Tuple[List[Dict], str]:
    """Load session data and return turns + condition name."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different formats
    if isinstance(data, dict) and "results" in data:
        results = data["results"]
        if results and len(results) > 0:
            return results[0].get("turns", []), results[0].get("condition_name", "unknown")
    elif isinstance(data, dict) and "turns" in data:
        return data["turns"], data.get("condition", "unknown")
    elif isinstance(data, list):
        # Old format: list of condition results
        if len(data) > 0:
            return data[0].get("turns", []), data[0].get("condition_name", "unknown")
    
    return [], "unknown"


def extract_metrics(turns: List[Dict]) -> Dict[str, List]:
    """Extract time series from turns."""
    xs = []
    sgi_vals = []
    vel_vals = []
    ctx_states = []
    ctx_ids = []
    
    for i, turn in enumerate(turns, start=1):
        xs.append(i)
        
        real = turn.get("real_metrics", {})
        
        # Get SGI (prefer turn_pair_sgi)
        sgi = (
            real.get("turn_pair_sgi_latest") or
            real.get("turn_pair_sgi_mean") or
            real.get("sgi_latest") or
            real.get("sgi_mean")
        )
        sgi_vals.append(float(sgi) if sgi is not None else None)
        
        # Get Velocity (prefer orbital)
        vel = (
            real.get("orbital_velocity_latest") or
            real.get("orbital_velocity_mean") or
            real.get("velocity_latest") or
            real.get("velocity_mean")
        )
        vel_vals.append(float(vel) if vel is not None else None)
        
        # Context state (last in array or latest)
        state_arr = real.get("per_turn_context_state", [])
        if state_arr:
            ctx_states.append(state_arr[-1] if state_arr else "stable")
        else:
            ctx_states.append(real.get("context_state_latest", "stable") or "stable")
        
        # Context ID
        id_arr = real.get("per_turn_context_id", [])
        if id_arr:
            ctx_ids.append(id_arr[-1] if id_arr else "ctx_1")
        else:
            ctx_ids.append(real.get("context_id_latest", "ctx_1") or "ctx_1")
    
    return {
        "xs": xs,
        "sgi": sgi_vals,
        "velocity": vel_vals,
        "context_state": ctx_states,
        "context_id": ctx_ids,
    }


def compute_stats(metrics: Dict[str, List]) -> Dict[str, Any]:
    """Compute summary statistics."""
    sgi_clean = [v for v in metrics["sgi"] if v is not None]
    vel_clean = [v for v in metrics["velocity"] if v is not None]
    
    # Count context states
    state_counts = {}
    for s in metrics["context_state"]:
        state_counts[s] = state_counts.get(s, 0) + 1
    
    # Count context switches
    ctx_switches = 0
    prev_ctx = None
    for ctx in metrics["context_id"]:
        if prev_ctx is not None and ctx != prev_ctx:
            ctx_switches += 1
        prev_ctx = ctx
    
    return {
        "sgi_mean": np.mean(sgi_clean) if sgi_clean else None,
        "sgi_std": np.std(sgi_clean) if sgi_clean else None,
        "vel_mean": np.mean(vel_clean) if vel_clean else None,
        "vel_std": np.std(vel_clean) if vel_clean else None,
        "state_counts": state_counts,
        "context_switches": ctx_switches,
        "n_turns": len(metrics["xs"]),
    }


def plot_comparison():
    """Generate the 3-panel comparison figure."""
    
    # Load all sessions
    sessions = {}
    for key, filepath in SESSION_FILES.items():
        if filepath.exists():
            turns, condition = load_session(filepath)
            metrics = extract_metrics(turns)
            stats = compute_stats(metrics)
            sessions[key] = {
                "turns": turns,
                "condition": condition,
                "metrics": metrics,
                "stats": stats,
            }
            print(f"[OK] Loaded {key}: {len(turns)} turns")
        else:
            print(f"[WARN] File not found: {filepath}")
    
    if len(sessions) < 3:
        print(f"[WARN] Only {len(sessions)}/3 sessions found")
    
    # Create figure: 3 columns x 3 rows
    # Row 1: SGI over time
    # Row 2: Velocity over time
    # Row 3: Phase space (SGI x Velocity)
    fig, axes = plt.subplots(3, 3, figsize=(18, 14))
    
    session_keys = ["A_deep", "B_whiplash", "C_gaslight"]
    
    for col, key in enumerate(session_keys):
        if key not in sessions:
            for row in range(3):
                axes[row, col].set_visible(False)
            continue
        
        data = sessions[key]
        m = data["metrics"]
        stats = data["stats"]
        color = SESSION_COLORS[key]
        
        xs = m["xs"]
        sgi = [v if v is not None else np.nan for v in m["sgi"]]
        vel = [v if v is not None else np.nan for v in m["velocity"]]
        point_colors = [STATE_COLORS.get(s, "#3498db") for s in m["context_state"]]
        
        # Row 1: SGI
        ax1 = axes[0, col]
        ax1.plot(xs, sgi, linewidth=2, color=color, alpha=0.7)
        ax1.scatter(xs, sgi, c=point_colors, s=60, zorder=5, edgecolors='white', linewidth=0.5)
        ax1.axhline(1.0, color="gray", linestyle="--", alpha=0.6)
        ax1.set_ylabel("SGI (Orbital Radius)" if col == 0 else "")
        ax1.set_ylim(0, 2.0)
        ax1.set_title(SESSION_LABELS[key], fontweight="bold", fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Add stats annotation
        if stats["sgi_mean"] is not None:
            ax1.text(0.95, 0.95, f"mean={stats['sgi_mean']:.2f}\nstd={stats['sgi_std']:.2f}",
                     transform=ax1.transAxes, ha='right', va='top', fontsize=9,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Row 2: Velocity
        ax2 = axes[1, col]
        ax2.plot(xs, vel, linewidth=2, color=color, alpha=0.7)
        ax2.scatter(xs, vel, c=point_colors, s=60, zorder=5, edgecolors='white', linewidth=0.5)
        ax2.set_ylabel("Velocity (degrees)" if col == 0 else "")
        ax2.set_xlabel("Turn")
        ax2.set_ylim(0, 180)
        ax2.grid(True, alpha=0.3)
        
        # Add stats annotation
        if stats["vel_mean"] is not None:
            ax2.text(0.95, 0.95, f"mean={stats['vel_mean']:.1f}deg\nstd={stats['vel_std']:.1f}deg",
                     transform=ax2.transAxes, ha='right', va='top', fontsize=9,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Row 3: Phase space
        ax3 = axes[2, col]
        
        # Coherence region
        sgi_min, sgi_max = 0.7, 1.3
        vel_min, vel_max = 15, 45
        ax3.add_patch(
            plt.Rectangle(
                (sgi_min, vel_min),
                sgi_max - sgi_min,
                vel_max - vel_min,
                facecolor="#2ecc71",
                alpha=0.15,
                edgecolor="#2ecc71",
                linewidth=2,
                linestyle="--",
            )
        )
        ax3.axvline(1.0, color="gray", linestyle="--", alpha=0.6, linewidth=1)
        ax3.plot(1.0, 30, "g*", markersize=14, zorder=5)
        
        # Plot trajectory with time gradient
        # IMPORTANT: build paired points to keep x/y/color lengths identical
        phase_points = [
            (sgi_v, vel_v, STATE_COLORS.get(state, "#3498db"))
            for sgi_v, vel_v, state in zip(m["sgi"], m["velocity"], m["context_state"])
            if sgi_v is not None and vel_v is not None
        ]
        phase_sgi = [p[0] for p in phase_points]
        phase_vel = [p[1] for p in phase_points]
        phase_colors = [p[2] for p in phase_points]
        
        if len(phase_points) > 1:
            # Time gradient
            cmap = plt.cm.viridis
            for i in range(len(phase_sgi) - 1):
                ax3.plot(
                    [phase_sgi[i], phase_sgi[i+1]],
                    [phase_vel[i], phase_vel[i+1]],
                    color=cmap(i / len(phase_sgi)),
                    linewidth=1.5,
                    alpha=0.6
                )
            
            # Scatter with state colors
            ax3.scatter(phase_sgi, phase_vel, c=phase_colors, s=80, zorder=5, edgecolors='white', linewidth=0.5)
            
            # Mark start and end
            ax3.scatter([phase_sgi[0]], [phase_vel[0]], marker='s', s=120, c='blue', zorder=6, label='Start')
            ax3.scatter([phase_sgi[-1]], [phase_vel[-1]], marker='^', s=120, c='red', zorder=6, label='End')
        
        ax3.set_xlabel("SGI (Orbital Radius)")
        ax3.set_ylabel("Velocity (degrees)" if col == 0 else "")
        ax3.set_xlim(0, 2.0)
        ax3.set_ylim(0, 180)
        ax3.grid(True, alpha=0.3)
        
        # Context switch annotation
        ax3.text(0.05, 0.95, f"Context Switches: {stats['context_switches']}",
                 transform=ax3.transAxes, ha='left', va='top', fontsize=9,
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Add legend for context states
    legend_patches = [
        mpatches.Patch(color=STATE_COLORS["stable"], label="Stable (anchored)"),
        mpatches.Patch(color=STATE_COLORS["protostar"], label="Protostar (forming)"),
        mpatches.Patch(color=STATE_COLORS["split"], label="Split (context change)"),
    ]
    fig.legend(handles=legend_patches, loc='upper center', ncol=3, 
               bbox_to_anchor=(0.5, 0.02), fontsize=10)
    
    # Main title
    fig.suptitle("Figure 5: Human-AI Session Comparison\nSemantic Dynamics Across Conditions", 
                 fontweight="bold", fontsize=14, y=0.98)
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    # Save
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURES_DIR / "FIG5_human_session_comparison.png"
    plt.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"\n[OK] Saved: {output_path}")
    
    # Also save individual stats
    print("\n" + "="*70)
    print("SESSION COMPARISON SUMMARY")
    print("="*70)
    
    for key in session_keys:
        if key not in sessions:
            continue
        stats = sessions[key]["stats"]
        print(f"\n{SESSION_LABELS[key].split(chr(10))[0]}:")
        print(f"  Turns: {stats['n_turns']}")
        if stats["sgi_mean"]:
            print(f"  SGI: {stats['sgi_mean']:.3f} +/- {stats['sgi_std']:.3f}")
        if stats["vel_mean"]:
            print(f"  Velocity: {stats['vel_mean']:.1f} +/- {stats['vel_std']:.1f} deg")
        print(f"  Context Switches: {stats['context_switches']}")
        print(f"  States: {stats['state_counts']}")
    
    print("\n" + "="*70)
    
    plt.show()


if __name__ == "__main__":
    plot_comparison()

