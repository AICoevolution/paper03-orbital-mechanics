# AICoevolution Semantic Telemetry

**Measure conversational dynamics in real-time.**

This open-source script demonstrates the core capabilities of the AICoevolution SDK for measuring semantic dynamics in human-AI conversations.

## What It Measures

| Metric | Description | Range |
|--------|-------------|-------|
| **SGI (Orbital Radius)** | How balanced between query responsiveness and context grounding | ~0.5-1.5 |
| **Velocity** | Rate of semantic movement per turn | 0-180° |
| **Context Phase** | Topic coherence state | stable / protostar / split |
| **Context Mass** | Accumulated turns in current topic | 0-N |
| **Attractor Count** | Number of competing topic centers | 1+ |

## Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Get an API Key

Get a free API key by loging in and generate it from the User settings/API Keys [https://aicoevolution.com](https://aicoevolution.com)

### 3. Run the standalone script

```bash
# With cloud API
python semantic_telemetry.py --api-key YOUR_API_KEY

# Optional: custom SDK URL (e.g. local self-hosted)
python semantic_telemetry.py --api-key YOUR_API_KEY --url http://localhost:8001

# Custom turns
python semantic_telemetry.py --api-key YOUR_API_KEY --turns 20
```

## Minimal thin-client example (PyPI)

If you prefer integrating the SDK via a Python dependency:

```bash
pip install aicoevolution
set AIC_SDK_API_KEY=aic_.....
python hello_aicoevolution.py
```

## Example Output

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     SEMANTIC TELEMETRY - AICoevolution SDK                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

──────────────────────────────────────────────────
Turn 5/10
──────────────────────────────────────────────────

[YOU]: I'm trying to understand how meaning emerges in conversation
  [SDK] <- OK | SGI=0.952, Velocity=34.2°

[AI]: Meaning emerges through the dynamic interplay between what's said and the accumulated context...
  [SDK] <- OK | SGI=0.891, Velocity=28.7°

────────────────────────────── SEMANTIC METRICS ──────────────────────────────
  SGI (Orbital Radius):     0.891
  Velocity (degrees):       28.7°
  Context ID:               ctx_1
  Context State:            stable
  Attractor Count:          1
  Active Context Mass:      5 turns
──────────────────────────────────────────────────────────────────────
```

## Understanding the Metrics

### Coherence Region
Productive conversations tend to occupy:
- **SGI**: 0.7 - 1.3 (balanced orbit)
- **Velocity**: 15° - 60° (productive movement)

### Context Phases
- **stable** (🟢): Conversation anchored to current topic
- **protostar** (🟠): New topic forming, may switch soon
- **split** (🔴): Topic changed, new context promoted

### Orbital Energy
`E_orb = SGI × Velocity`
- Higher = more dynamic, potentially unstable
- Lower = more grounded, potentially stagnant

## Under Development

The following metrics are planned for future releases:

- **Domain Distribution**: Cognitive / Somatic / Emotional / Volitional balance
- **Symbolic Depth (S64)**: Transformation path detection
- **Mass Contribution**: Who is steering the conversation?
- **Grammatical Hierarchy**: Geometric grammar detection

## Learn More

- **Paper**: "Semantic Orbital Mechanics" (Jimenez Sanchez, 2026)
- **Website**: [https://aicoevolution.com](https://aicoevolution.com)
- **SDK Documentation**: [https://docs.aicoevolution.com](https://docs.aicoevolution.com)

## License

MIT License - Use freely for research and commercial applications.

## Citation

If you use this in research, please cite:

```bibtex
@article{jimenez2026orbital,
  title={Semantic Orbital Mechanics: Measuring and Guiding AI Conversation Dynamics},
  author={Jimenez Sanchez, Juan Jacobo},
  journal={arXiv preprint},
  year={2026}
}
```

