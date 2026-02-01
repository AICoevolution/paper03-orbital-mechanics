---
dataset_name: s64-orbital-v1
pretty_name: "S64 Orbital Mechanics – Semantic Orbital Dynamics (Paper 03)"
license: cc-by-4.0
language:
  - en
tags:
  - symbolic-ai
  - human-ai-interaction
  - conversation-dynamics
  - semantic-space
  - telemetry
task_categories:
  - other
repository: https://github.com/AICoevolution/paper03-orbital-mechanics
---

# S64 Orbital Mechanics Dataset (Paper 03)

This dataset accompanies **Paper 03** and contains minimal reproducible artifacts plus curated JSON run outputs used to generate the figures.

## Repository Structure

```
s64-orbital-v1/
│
├── README.md
├── S64-orbital-paper.md
├── references.bib
├── title-block.tex
├── render.bat
│
├── open_source/
│   ├── semantic_telemetry.py
│   └── README.md
│
└── analysis/
    ├── scripts/
    │   ├── 09_steering_experiment.py
    │   ├── 15_human_session_comparison.py
    │   └── 16_human_fig3_merged.py
    │
    └── datasets/
        └── *.json
```

## Dataset Format (JSON)

Each `analysis/datasets/*.json` file is a self-contained run export with this high-level schema:

- **`metadata`**: run configuration (timestamp, LLMs, conditions tested, backends used, SDK URL, etc.)
- **`results`**: list of per-condition results
  - **`condition_name`**: e.g. `A_baseline`, `E_real_metrics`
  - **`condition_description`**
  - **`turns`**: turn-by-turn conversation trace
    - **`turn_number`**
    - **`user_message`** / **`assistant_response`** (may be removed in sanitized releases)
    - **`injected_metrics`**: metrics shown to the model (if any)
    - **`real_metrics`**: measured values per turn, typically including:
      - **`sgi_*`**: Semantic Grounding Index aggregates / per-turn series
      - **`velocity_*`**: angular velocity aggregates / per-turn series
      - **`orbital_velocity_*`**, **`context_drift_*`**, **`dc_*`**
      - **`per_turn_context_id`**, **`per_turn_context_state`**

## HuggingFace Size Limits

HuggingFace rejects files larger than **10 MiB** unless Git LFS is used. The deployment script creates an HF-specific bundle by pruning any files over 10 MiB before pushing.

## Exclusions (Intentional)

- Binary figures (PNG/PDF) are not included in the public research bundle by default.
- Some internal S64-dependent analysis assets are intentionally excluded.

## License

Released under **CC BY 4.0**.
