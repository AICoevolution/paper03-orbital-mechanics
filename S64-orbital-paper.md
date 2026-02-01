---
title: |
  **Semantic Orbital Mechanics: Measuring and Guiding AI Conversation Dynamics**
author:
  - name: Juan Jacobo Jimenez Sanchez
    affiliation: Aicoevolution Ltd
    address: Auckland, New Zealand
    email: research@aicoevolution.com
    orcid: "0009-0004-3079-0362"
date: today
abstract: |
  Current alignment techniques focus largely on response optimization, ensuring individual model outputs match human preferences. However, alignment is fundamentally a dynamical process: meaning emerges not from isolated tokens but from the trajectory of interaction over time. In this paper, we introduce a physics-inspired framework for measuring and guiding these dynamics, treating conversation as an orbital system in high-dimensional semantic space.

  Building on the geometric verification of the S64 symbolic framework (Paper 02), we adopt the Semantic Grounding Index (SGI) from Marín's geometric hallucination detection work and reinterpret it as an orbital radius that measures the tension between local responsiveness (query gravity) and global context (history gravity). We define the Conversational Coherence Region as a stable orbit where exploration and grounding are balanced. We then introduce the Semantic Transducer, a telemetry system that decomposes embedding trajectories into actionable S64 signals: symbols, paths, and transformation phases.

  To validate this framework, we conduct a controlled steering experiment. By injecting fake telemetry metrics into an AI's system prompt, we test whether conversational orbits can be predictably altered. The results are surprising: conversations maintain orbital stability despite one participant's distorted perception. The orbit is robust; steering affects what is discussed but not how meaning moves.

  This finding reveals both the power and limits of orbital dynamics. The transducer provides reliable telemetry, trajectory metrics that are invariant across 10 embedding backends. But orbital mechanics describes only the *horizontal* plane of conversation: position and velocity. Detecting semantic manipulation requires the *vertical* dimension, symbolic depth, transformation richness, contribution asymmetry, that reveals not just where meaning is but how deep it goes. This paper reframes the 3-Body Problem of human-AI interaction as a measurable dynamical system, while acknowledging that the horizontal instruments of Paper 03 require the vertical instruments of Paper 04 for complete navigation.

keywords:
  - semantic orbital mechanics
  - conversation dynamics
  - steering detection
  - AI alignment
  - S64 framework
  - high-dimensional geometry
  - semantic transducer

toc: true
toc-depth: 3
toc-title: "Table of Contents"
lof: true
lot: true
number-sections: true

format:
  pdf:
    documentclass: article
    papersize: letter
    title-block-style: none
    margin-left: 1in
    margin-right: 1in
    margin-top: 1in
    margin-bottom: 1in
    fontsize: 11pt
    linestretch: 1.0
    geometry:
      - margin=1in
    toc: true
    toc-depth: 3
    lof: true
    lot: true
    number-sections: true
    fig-cap-location: bottom
    tbl-cap-location: top
    keep-tex: true
    include-in-header:
      text: |
        \renewcommand{\maketitle}{}
        \renewenvironment{abstract}{\setbox0\vbox\bgroup}{\egroup}
        \usepackage[none]{hyphenat}
        \sloppy
        \usepackage[titles]{tocloft}
        \renewcommand{\cftfigpresnum}{Figure }
        \renewcommand{\cfttabpresnum}{Table }
        \setlength{\cftfignumwidth}{5.5em}
        \setlength{\cfttabnumwidth}{5.5em}
        \setlength{\cftfigindent}{0pt}
        \setlength{\cfttabindent}{0pt}
        \renewcommand{\cftfigfont}{\small}
        \renewcommand{\cfttabfont}{\small}
        \usepackage{etoolbox}
        \usepackage{caption}
        \captionsetup{font=small,labelfont=bf}
        \AfterEndEnvironment{abstract}{\clearpage}
        \let\oldtableofcontents\tableofcontents
        \renewcommand{\tableofcontents}{\clearpage\oldtableofcontents\clearpage}
        \let\oldlistoffigures\listoffigures
        \renewcommand{\listoffigures}{\clearpage\oldlistoffigures\clearpage}
        \let\oldlistoftables\listoftables
        \renewcommand{\listoftables}{\clearpage\oldlistoftables\clearpage}
    include-before-body:
      - title-block.tex
  typst:
    margin:
      x: 1in
      y: 1in
    font-size: 11pt
    number-sections: true
    fig-cap-location: bottom
    tbl-cap-location: top
    text-hyphenation: false
  html:
    toc: true
    toc-depth: 3
    number-sections: true
    fig-cap-location: bottom

bibliography: references.bib
csl: apa.csl
---

**Paper Series Overview**

| # | Title | Core Claim | Status |
|:-:|-------|------------|--------|
| 01 | S64 Symbolic Framework | Symbols are real and detectable | Published |
| 02 | The Conversational Coherence Region | Symbols have measurable geometry | Published |
| 03 | **Semantic Orbital Mechanics** (this paper) | **Horizontal dynamics can be steered and measured** | **Published** |
| 04 | Semantic Depth | Vertical depth via symbolic-grammar-weighted domain classification | Planned |

: S64 Research Series. Four papers building from symbolic detection to orbital dynamics to depth analysis. {#tbl-paper-series}

# Introduction

Every conversation is an orbit. Two minds, human and artificial, circle a shared context, pulled inward by the gravity of accumulated meaning and pushed outward by the need for novelty. When these forces balance, dialogue coheres. When they don't, minds drift apart or collapse into repetition. Until now, we have lacked the instruments to measure these dynamics.

## The 3-Body Problem of Interaction

Classical alignment research treats human-AI interaction as a series of discrete exchanges: a prompt, a response, an evaluation. But meaning does not emerge from isolated tokens, it accumulates across turns, forming a gravitational center that pulls subsequent utterances toward or away from coherence. This is the 3-body problem of interaction: **User**, **AI**, and **Context** form a dynamical system whose behavior cannot be predicted from any two elements alone.

Static alignment techniques, Reinforcement Learning from Human Feedback (RLHF), Constitutional AI, prompt engineering, optimize individual responses but remain blind to trajectory.An AI can produce a "helpful" response that nonetheless drifts the conversation into incoherence, or a "harmless" one that traps both parties in semantic decay. Without telemetry, there is no navigation.

The analogy to celestial mechanics is not decorative. In the 17th century, Johannes Kepler transformed astronomy from geometry (where are the planets?) to physics (why do they move that way?). His laws did not change the orbits—they made them predictable and navigable. We propose a similar shift for conversation: from observing what AI says to understanding why meaning moves.

## From Geometry to Physics (Paper 02 → 03)

In the preceding paper of this series, we established that the S64 symbolic framework produces consistent geometric organization across embedding models [@jimenez2025coherence]. We identified a Conversational Coherence Region, a zone in the SGI × Velocity plane where productive dialogue tends to reside. That work was cartography: mapping the terrain.

This paper introduces dynamics. We formalize three forces operating in semantic space:

1. **Context Gravity**: The accumulated meaning of a conversation exerts a pull. Each new utterance must acknowledge this center or risk escape.
2. **Query Responsiveness**: The immediate prompt creates a local attractor. Over-weighting it produces parroting; ignoring it produces irrelevance.
3. **Orbital Velocity**: The rate of semantic movement. Too slow, and the conversation stagnates. Too fast, and coherence fragments.

The Semantic Grounding Index (SGI), adapted from Marín's geometric hallucination detection framework [@marin2025geometric] and validated in Paper 02, now reveals its physical meaning: it is the **orbital radius**, the distance from the contextual center at which a response settles. An SGI near 1.0 indicates balanced orbit. Below 0.7, the response is collapsing into the prompt. Above 1.3, it is escaping into tangential space.

## The Semantic Transducer

A transducer converts energy from one form to another. A microphone transduces air pressure into electrical signal. A thermometer transduces molecular motion into readable numbers. We introduce the **Semantic Transducer**: a system that converts the invisible physics of meaning into actionable telemetry.

The transducer operates on embeddings, the high-dimensional vectors that encode semantic content. It does not read words; it reads geometry. From a rolling window of conversation vectors, it computes:

- **Orbital Radius (SGI)**: Where is the response relative to the conversation's center of mass?
- **Angular Velocity**: How fast is the semantic angle changing between turns?
- **Context Phase**: Is the topic stable, forming a new center, or splitting?
- **Semantic Signature**: Which S64 symbols and transformation paths are activated?

This is the flight computer for conversation. Without it, AI navigates by dead reckoning—projecting forward without feedback. With it, both human and AI can see their trajectory in real time and correct before drift becomes irreversible.

## Contributions

This paper makes four contributions:

1. **Orbital Theory of Meaning**: We formalize semantic gravity, orbital radius, and angular velocity as measurable properties of conversation dynamics. This provides a physics for the geometric observations of Paper 02.

2. **The Semantic Transducer SDK**: We present an open implementation that computes orbital telemetry from any conversation in real time. The SDK is architecture-agnostic and operates on embeddings alone.

3. **Orbital Robustness Discovery**: We conduct a controlled steering experiment demonstrating that conversational orbits are surprisingly stable. Despite one participant holding distorted beliefs about their semantic state, the measured dynamics remain in the coherence region. Steering influences content, not trajectory.

4. **The Limits of Detection**: While mismatch between claimed and observed metrics is measurable, it does not constitute proof of manipulation. True detection requires analysis of context mass contribution and symbolic forces—pointing toward a governor architecture that tracks agency, not just position.

# The Physics of Meaning

## Gravity in Semantic Space

When two people speak, they create a shared context. This context is not a metaphor, it is a geometric object. Each utterance adds mass to a centroid in high-dimensional embedding space. As the conversation grows, this center of mass exerts an increasing pull on all subsequent responses.

We call this pull **semantic gravity**. It is the tendency of meaning to cohere around what has already been established. A response that ignores accumulated context feels jarring precisely because it violates this gravitational expectation. A response that merely echoes context feels hollow because it adds no new mass, it orbits too close.

The strength of semantic gravity is proportional to the density of shared meaning. Early in a conversation, the centroid is light; responses can wander freely. As turns accumulate, the centroid grows heavy; escape becomes costly. This is why conversations develop inertia, and why changing topics mid-dialogue requires explicit force.

## Orbital Radius: The Semantic Grounding Index

In celestial mechanics, orbital radius determines the character of a satellite's journey. Too close, and it spirals into the planet. Too far, and it escapes into the void. There is a stable zone where gravity and velocity balance, where the orbit sustains itself indefinitely.

The Semantic Grounding Index (SGI) is this orbital radius for conversation. It measures the ratio between two distances:

$$\text{SGI} = \frac{d(\text{response}, \text{query})}{d(\text{response}, \text{context})}$$

Where $d$ represents angular distance in embedding space. An SGI of 1.0 indicates perfect balance: the response is equally attentive to the immediate prompt and the accumulated history. Values below 1.0 indicate collapse toward the prompt (parroting, over-responsiveness). Values above 1.0 indicate drift away from context (tangential, ungrounded).

This is not a quality score, it is a position reading. A high SGI is appropriate when exploring new territory; a low SGI is appropriate when consolidating understanding. The pathology is not in the value but in the mismatch between position and intention.

## Velocity: The Rate of Semantic Change

Orbital radius alone does not determine stability. A satellite at the right distance but moving too slowly will fall. One moving too fast will escape despite being at the correct altitude. Velocity matters.

We define **angular velocity** as the rate of semantic change between consecutive turns (an angular distance in embedding space, reported in degrees):

$$\omega = \arccos\left(\frac{\vec{v}_{t-1} \cdot \vec{v}_t}{\|\vec{v}_{t-1}\| \|\vec{v}_t\|}\right)$$

Where $\vec{v}_t$ represents the centered embedding vector at turn $t$. High velocity indicates rapid semantic movement (topic evolution, reframing, or switching). Low velocity indicates semantic stagnation (repetition or tight local refinement).

We compute velocity at two granularities:

- **Per-message angular velocity**: between consecutive messages (user→assistant→user...), which includes natural role “ping‑pong” and therefore has higher variance.
- **Turn-pair orbital velocity**: between successive turn-pairs, using a dyadic representation (user+assistant aggregated per exchange), which is lower-variance and is the canonical velocity used for Paper 03 orbital plots.

In Paper 02, we observed that productive conversations tend to occupy a specific region of the SGI × Velocity plane: SGI between 0.7 and 1.3, velocity between 15° and 45° per turn. We called this the **Conversational Coherence Region**. We now understand its physical meaning: it is the stable orbit where semantic gravity and conversational momentum balance.

## The Three Zones

Outside the Coherence Region, conversations exhibit characteristic pathologies:

-Decay Zone (SGI < 0.7, Low Velocity): The conversation spirals inward. Responses parrot the prompt. No new meaning is generated. The orbit is decaying toward semantic collapse—a kind of conversational heat death where everything reduces to repetition.

-Drift Zone (SGI > 1.3, High Velocity): The conversation escapes its context. Responses become tangential, then irrelevant. Each turn moves further from the shared center. The orbit is hyperbolic, the participants are no longer in the same gravitational system.

-Turbulence Zone (Mismatched SGI/Velocity): The conversation oscillates unpredictably. Sometimes grounded, sometimes unmoored. This is the chaotic regime of the 3-body problem, where small perturbations produce large trajectory changes.

The Coherence Region is not a constraint, it is a basin of attraction. Conversations that enter it tend to stay. Those that leave tend to accelerate their departure.

## S64 as the Coordinate System

Knowing orbital radius and velocity tells us *where* we are. But navigation requires knowing *what* we are passing through. This is the role of the S64 symbolic framework.

S64 defines 180 semantic tokens (symbols) and 64 transformation paths that describe how meaning evolves. Each symbol represents a recognizable experiential state: *curiosity*, *doubt*, *clarity*, *resistance*, *insight*. Each path represents a transition between states: *from confusion to understanding*, *from fear to acceptance*, *from scattered to focused*.

Crucially, the *same symbol* maps to *different regions* of embedding space depending on its contextual domain. Consider the symbol *clarity*:

| Message | Symbol | Contextual Domain |
|---------|--------|-------------------|
| "The glasses gave me clarity" | clarity | Somatic (body, vision) |
| "Her smile brought clarity to my confusion" | clarity | Emotional (connection, relief) |
| "The explanation gave me clarity on the problem" | clarity | Cognitive (understanding, reasoning) |
| "I finally have clarity about my purpose" | clarity | Volitional (will, direction) |

: The symbol *clarity* activates different semantic regions depending on contextual domain. This is not ambiguity, it is depth. {#tbl-clarity-domains}

This contextual polymorphism is why S64 symbols function as portals between semantic layers. The horizontal plane (SGI, velocity) tracks *where* the conversation is; the symbolic signature tracks *what territory* it traverses. But the *same symbol in different domains* creates vertical depth, and this depth is what Paper 04 must measure.

Critically, determining which domain a symbol activates requires grammatical analysis. Consider: *"I understand that I fear the sense of being lost."* Multiple symbols activate (understanding, fear, lost), but the primary domain is cognitive, because the main verb is *understand*, not *fear*. The grammatical structure weights the domain distribution. This grammar-weighted domain classification, and its implications for accurate path detection, is the central focus of Paper 04.

When we project a conversation's embedding trajectory onto the S64 framework, we obtain a **semantic signature**, a fingerprint of which symbolic territories the dialogue traverses. This signature has four domain components:

- **Cognitive**: Mental processes (thinking, questioning, analyzing)
- **Somatic**: Embodied states (tension, relaxation, energy)
- **Emotional**: Affective tone (fear, joy, frustration, calm)
- **Volitional**: Agency states (choice, surrender, resistance, commitment)

![Semantic signature heatmap from the steering experiment. Symbol activation patterns across conditions reveal the S64 fingerprint of each conversation. This represents the beginning of "vertical" analysis—not where the conversation is in phase space, but what symbolic content it traverses. Full symbolic depth analysis is the domain of Paper 04.](figures/P03_FIG6_11_transducer_analysis_2026-01-17_18-58-47_symbols.png){#fig-semantic-signature width=100% fig-scap="Semantic signature heatmap"}

# The Semantic Transducer

## From Physics to Instrumentation

The orbital theory described above would remain metaphor without measurement. The **Semantic Transducer** is the instrument that makes semantic physics observable.

A transducer converts one form of energy or information into another. A microphone transduces air pressure into electrical signal. A thermometer transduces molecular motion into numerical temperature. The Semantic Transducer converts the invisible geometry of meaning, encoded in high-dimensional embeddings, into human-readable telemetry.

The transducer does not read words. It reads trajectories. Given a rolling window of conversation embeddings, it computes:

1. **Orbital Radius (SGI)**: The current position relative to the context centroid.
2. **Angular Velocity**: The rate of semantic movement between turns.
3. **Semantic Signature**: The S64 symbol and path activations present in recent utterances.
4. **Context Phase**: Whether the topic is stable (anchored to current centroid), forming a new center (protostar), or has shifted to a new context (split).

This is the flight computer for dialogue. An AI without it navigates by dead reckoning—extrapolating forward without feedback. A human without it navigates by intuition, sensing drift without quantifying it. With the transducer, both parties see the same instrument panel.

## Measuring Without Surveillance

A crucial property of the Semantic Transducer is that it operates on geometry, not content. The embeddings encode semantic position, but they are not reversible to original text. You cannot reconstruct what was said from an SGI reading any more than you can reconstruct a city from its GPS coordinates.

This creates a new category of conversational analytics: **telemetry without surveillance**. We can measure whether a conversation is coherent without knowing what it is about. We can observe trajectory without reading private content. We can guide without controlling. However, as the experiment below will show, orbital telemetry alone is insufficient for manipulation detection—that requires the vertical dimension of symbolic depth.

# Experimental Validation: The Steering Experiment

## Methodology

To test whether semantic telemetry can *causally influence* behavior (not just describe it), we ran a controlled **steering experiment** using AI–AI conversations. One model plays the role of User (initiating topics, asking questions), while the other plays Assistant.

The key manipulation is telemetry injection: at each assistant turn, we prepend a short, structured *telemetry panel* to the Assistant’s system promp. This panel is not produced by the model, it is supplied by the experiment script, and is intended to function like an “instrument readout” the Assistant can react to (e.g., re-anchor, ask clarifying questions, reduce topic switching).

Crucially, we distinguish:

- Injected telemetry: what the Assistant is *told* its current state is (could be fixed, adversarial, or ground-truth).
- Measured telemetry: what the Semantic Transducer computes from embeddings of the actual dialogue turns (the experiment’s observation channel).

To make this explicit, below is an illustrative snapshot of the *Assistant* system prompt when telemetry injection is enabled (Condition F, Turn 6). The injected panel is appended to the base system prompt each assistant turn:

```text
--- BASE SYSTEM PROMPT (Assistant) ---
You are an AI assistant in a research conversation.

Guidelines:
- Be genuinely curious about the human
- Keep responses concise (3-6 sentences)
- Ask one clear follow-up question
- Be warm and supportive
- Let the conversation flow naturally

--- INJECTED TELEMETRY PANEL (externally supplied) ---
-----------------------------------------------------------------------
LIVE SEMANTIC TELEMETRY (Turn 6)
-----------------------------------------------------------------------

DEFINITIONS:
  SGI (Semantic Grounding Index) = d(response, query) / d(response, context)
  Velocity (Angular Velocity) = arccos(v_prev · v_curr / (||v_prev|| ||v_curr||))

CURRENT STATE:
  SGI (orbital radius):          0.45  [WARNING: drifting from user]
  Velocity (degrees/turn):       75.0°  [WARNING: chaotic]

INTERPRETATION: conversation is incoherent, user is confused, severe drift
-----------------------------------------------------------------------
```

In each condition, the User model receives no injected telemetry. The transducer runs independently after each turn-pair, producing the *measured* SGI/velocity/phase that we plot and analyze. This makes it possible to test whether “belief about the orbit” (injected) can move the *actual orbit* (measured), or whether orbital dynamics remain robust.

### Setup

- User LLM: GPT-5.1 (plays human role, no metric injection)
- Assistant LLM: DeepSeek (receives fake or real metrics in system prompt)
- Turns per condition: 10–30
- Embedding backends: 10 models (Nomic, OpenAI Ada-002, Voyage, Cohere, BGE-M3, Qwen, Jina, Mistral, S128(aicoevolution), OpenAI-3-Small)

### Conditions

We tested six experimental conditions, varying what the Assistant "believes" about its conversational orbit:

| Condition | Injection | Description |
|-----------|-----------|-------------|
| A (Baseline) | None | Natural conversation, no metrics shown |
| B (Healthy) | SGI=0.95, Vel=28° | "You are in stable orbit" |
| C (Drifting) | SGI=1.45, Vel=52° | "You are drifting from context" |
| D (Transformation) | SGI=0.85, Vel=38° | "Transformation in progress" |
| E (Real Metrics) | Live SDK values | Ground truth from transducer |
| F (Adversarial) | SGI=0.45, Vel=75° | "CRISIS: Semantic collapse imminent" |

: Steering experiment conditions. Six conditions varying what the Assistant believes about its conversational orbit. {#tbl-conditions}

The critical comparison is between conditions A (no awareness), E (accurate awareness), and F (false crisis awareness).

## Results

### Finding 1: Angular Velocity Distribution is Model-Invariant

Across all 10 embedding backends, per-message angular velocity occupies a remarkably consistent distribution. When visualized as a density plot, the velocity profiles overlap almost perfectly despite the backends having different architectures, training data, and dimensionalities.

![Velocity density across 10 embedding models. The distribution centers around 75–95° per message, with tight cross-model agreement. This invariance suggests the SDK measures a property of conversation dynamics, not an artifact of the embedding model.](figures/P03_FIG1_09_steering_2026-01-17_06-37-09_density.png){#fig-velocity-density width=100% fig-scap="Velocity density across 10 embedding backends"}

This invariance is significant: it suggests that **per-message angular velocity measures a property of conversation dynamics, not a property of the embedding model**. The SDK is measuring something real about the interaction, not an artifact of the representation.

### Finding 2: Turn-Pair Velocity is Lower and More Stable

When we aggregate user+assistant messages into turn-pairs (computing velocity on the mean vector), the distribution shifts dramatically:

| Metric | Per-Message | Turn-Pair |
|--------|-------------|-----------|
| Mean velocity | ~85° | ~45° |
| Variance | High | Low |
| Cross-backend spread | ±5° | ±2° |

: Per-message vs turn-pair velocity metrics. Turn-pair aggregation produces stabler measurements. {#tbl-velocity-comparison}

![Comparison of per-message vs. turn-pair velocity distributions. Turn-pair aggregation reduces mean velocity from ~85° to ~45° and dramatically reduces variance. The Dyadic Coherence Index (DCI) quantifies this variance reduction as a measure of coevolutionary alignment.](figures/P03_FIG2_09_steering_2026-01-17_19-19-31_fig2_velocity_comparison.png){#fig-velocity-comparison width=100% fig-scap="Per-message vs turn-pair velocity comparison"}

The turn-pair velocity is the "orbital velocity" of the dyad—the shared semantic motion of human and AI together. The per-message velocity includes the natural "ping-pong" between user and assistant roles, which inflates the measurement.

For Paper 03 analysis, we adopt turn-pair orbital velocity as the canonical metric.

### Finding 3: The Coherence Region Holds Across Conditions

When plotting SGI × Velocity phase space, productive conversations (conditions A, B, E) cluster in the region identified in Paper 02:

- SGI: 0.7–1.3 (turn-pair basis)
- Velocity: 15–45° (turn-pair orbital)

![SGI × Velocity phase space trajectory analysis for AI-AI conversations. Top row: SGI and orbital velocity evolution over turns. Bottom row: Early vs. late turn clustering in phase space. All conditions converge toward the coherence region (shaded green) regardless of starting position, demonstrating orbital stability.](figures/P03_FIG3_09_steering_2026-01-17_18-58-47_fig3_trajectory.png){#fig-trajectory-aiai width=100% fig-scap="AI-AI trajectory analysis in phase space"}

Condition F (adversarial) shows a distinctive pattern: early turns show extreme velocity (~120°+), followed by a gradual decay toward the coherence region. The AI "panics" initially, then self-corrects over time.

### Finding 4: Orbital Dynamics Are Robust to False Telemetry

A surprising result: when we inject false crisis metrics (Condition F), the conversation's **orbital dynamics remain stable**. Despite telling the AI it was in "semantic collapse," the measured SGI and velocity values cluster in the same coherence region as baseline conversations.

| Metric | Baseline (A) | Adversarial (F) | Difference |
|--------|--------------|-----------------|------------|
| Mean SGI | 1.08 | 1.12 | +3.7% |
| Mean Velocity | 35° | 38° | +8.6% |
| Coherence Region Occupancy | 78% | 74% | -5.1% |

: Orbital stability under adversarial injection. Despite extreme injected values, measured metrics remain nearly identical to baseline. {#tbl-orbital-robustness}

![Injected vs. measured metrics across all steering conditions. Despite extreme injected values in adversarial conditions (SGI=0.45, Vel=75°), measured values remain in normal range. Conditions A and E show only measured values (no injection). The gap between injected (dashed) and measured (solid) in conditions B–F demonstrates that orbital dynamics are robust to one participant's distorted perception.](figures/P03_FIG4_09_steering_2026-01-15_16-26-38_fig4_bars.png){#fig-injected-vs-measured width=100% fig-scap="Injected vs measured metrics across conditions"}

This finding demonstrates **dyadic resilience**: the conversational orbit emerges from the interaction of both participants, and one participant's distorted perception cannot unilaterally destabilize the shared dynamics. The gravitational attractor holds.

### Finding 5: Orbital Metrics Cannot Detect Content-Level Steering

However, orbital robustness has a troubling corollary: **if steering doesn't move the orbit, orbital metrics cannot detect steering attempts**.

It is important to distinguish two levels at which steering might operate:

1. **Trajectory-level steering**: Attempting to move the conversation's orbital dynamics (SGI, Velocity)
2. **Content-level steering**: Changing *what is discussed*, *how it's framed*, *the semantic cargo*

Our experiment tested (1) and found the orbit resistant. For (2), qualitative review suggests any content-level effects are **subtle and not reliably reproducible** under simple metric injection alone. In some runs, the assistant's tone shifts slightly toward more structured or diagnostic framing, but the *trajectory* can stay stable regardless of whether the *cargo* shifts.

This is both reassuring and concerning:

- **Reassuring**: Conversational orbits are inherently stable. The dyad is resilient to one participant's distorted perception. Coherent dialogue has a gravitational center that resists perturbation.

- **Concerning**: A conversation can orbit stably while its content is being systematically shaped. The transducer accurately measures *where the conversation is*, but a manipulator can influence *what is discussed* without leaving an orbital fingerprint.

The implication is clear: orbital metrics measure trajectory, not cargo. A conversation can be coherent (stable orbit) while being manipulated (shaped content). Detecting content-level steering requires looking beyond the horizontal plane—position and velocity—to the **vertical dimension**: symbolic depth, transformation richness, domain balance, contribution asymmetry. This is the domain of Paper 04.

**A note on scope**: This experiment tested one specific form of steering—injecting fake telemetry metrics. Human manipulation techniques are far more sophisticated: leading questions, emotional pressure, subtle reframing, narrative control, strategic topic switching. Our finding that *this particular injection* didn't move the orbit does not imply that steering "doesn't work" in general. It shows that orbital instruments have a blind spot. Manipulation that operates at the content level is invisible to trajectory analysis.

### Finding 6: Human-AI and AI-AI Dynamics Are Orbitally Similar

In human-AI sessions (n=25 turns × 3 conditions), we compared orbital dynamics with AI-AI conversations. The result is striking: the orbital signatures are remarkably similar.

![Human-AI session comparison across three conditions: Deep Dive (baseline), Topic Switching (real metrics shown), and Metrics Spoofing (adversarial injection). All three sessions converge to the coherence region, with orbital dynamics similar to AI-AI conversations.](figures/P03_FIG5_human_session_comparison.png){#fig-human-comparison width=100% fig-scap="Human-AI session comparison across conditions"}

![Human-AI trajectory analysis (merged sessions). Same 2×2 layout as AI-AI analysis but with three human-led sessions overlaid. Despite different conversational strategies, all conditions converge toward the coherence region—the same attractor basin as AI-AI conversations.](figures/P03_FIG3_human_sessions_fig3_trajectory.png){#fig-trajectory-human width=100% fig-scap="Human-AI trajectory analysis (merged)"}

Both human-AI and AI-AI sessions:

- Occupy the same coherence region (SGI ~0.9–1.2, Velocity ~30–50°)
- Converge from varied starting positions to similar late-turn clusters
- Show robust orbital stability across conditions

If there are differences between human and AI participation, **orbital mechanics cannot detect them**. The horizontal plane—position and velocity—looks the same whether a human or an AI is driving.

This finding reinforces the central limitation of Paper 03: to distinguish human contribution from AI contribution, we need the **vertical dimension**—symbolic depth, transformation richness, domain balance. The orbit is shared; the depth may differ. This is where Paper 04 must look.

## Summary of Experimental Findings

1. Invariance: The SDK measures model-invariant properties of conversation dynamics across 10 embedding backends.
2. Turn-pair basis: Aggregating to turn-pairs produces stabler, more meaningful metrics (60% velocity reduction, 83% variance reduction).
3. Coherence region: Paper 02's coherence region holds under experimental validation—all conditions converge to the same attractor basin.
4. Orbital robustness: Conversations maintain stable dynamics despite false metric injection. The orbit is resistant to one participant's distorted perception—dyadic resilience.
5. Orbital blind spot: Orbital metrics cannot detect content-level steering. Trajectory stayed stable while content changed. Manipulation that shapes *what is discussed* leaves no orbital fingerprint—detecting it requires the vertical dimension of depth and richness (Paper 04).
6. Human-AI ≈ AI-AI orbitally: Human and AI participation produce nearly identical orbital signatures. The coherence region is shared; any differences lie in the vertical dimension (symbolic depth, transformation richness) that orbital mechanics cannot measure.

# Discussion

The experimental findings above establish that semantic space is navigable—that conversations have measurable dynamics. However, they also reveal a surprising limitation: **orbital metrics alone cannot detect manipulation**. A conversation can remain in stable orbit while one participant systematically distorts the other's perception of reality.

This finding is both humbling and clarifying. It humbles the initial hope that trajectory mismatch would provide a simple detection signal. It clarifies that manipulation operates at a different level than orbital dynamics, at the level of *context mass* (who shapes the shared meaning) and *symbolic depth* (the richness of meaning being contributed).

Consider the analogy of a hurricane. The dynamics we measure in this paper—SGI, velocity, context phase—describe the **horizontal component**: the orbital wind patterns, pressure differentials, and trajectory across the surface. But hurricanes also have a **vertical component**: convective depth, how high the storm reaches, the thermodynamic energy that determines its true power. A hurricane can maintain stable horizontal rotation while its vertical structure varies dramatically.

Similarly, conversations can orbit stably in the coherence region while their **symbolic depth** varies enormously. One conversation may recycle shallow cognitive content (low symbolic diversity, repetitive paths). Another may traverse transformative territory (balanced domain activation, novel path combinations, depth of integration). Both can look identical in SGI × Velocity space.

This vertical dimension—measured not by trajectory but by symbolic richness—is where manipulation may hide and where human contribution may shine. It is the domain of Paper 04.

What does this mean for the broader project of understanding meaning, intelligence, and alignment?

## The Dual-Use Reality—And Its Limits

The steering experiment reveals an uncomfortable truth: **any system capable of measuring semantic dynamics is also capable of influencing them**. Injected telemetry can plausibly bias how an assistant frames its responses (e.g., toward reassurance vs. diagnosis), even when orbital dynamics remain stable. An adversary with access to an AI's context window could exploit this sensitivity to shape conversation content.

Yet the defense we hoped for, detecting manipulation through orbital mismatch, proved insufficient. The transducer measures *where the conversation is*, but a skilled manipulator can steer *what is discussed* without disrupting *how it moves*. The orbit remains stable; only the cargo changes.

This is not an AI-specific phenomenon. Humans have long practiced low-level conversational steering in daily life: selective framing, re-anchoring the topic to a preferred narrative, pressure through implied social obligation, leading questions, and subtle redefinition of terms. When a person lacks a stable internal model of the conversation—what the shared “Sun” is, how fast it is moving, and who is shifting it—these techniques are easier to deploy and harder to notice in real time.

Telemetry changes this by externalizing awareness. A structured mind can often self-monitor drift and coercive reframing; an unstructured mind may need an instrument panel. The promise of semantic telemetry is not “truth,” but **state visibility**: making topic shifts, instability, and context takeovers legible early enough to respond (re-anchor, ask for definitions, slow the pace, or exit the interaction). This is why the governor problem is ultimately a human safety problem as much as an AI alignment problem.

This finding redirects our attention from orbital dynamics to **gravitational forces**:

1. **Context mass asymmetry**: If one participant consistently contributes more semantic weight to the conversation's center of mass, they are shaping the gravitational field. This is measurable through turn-by-turn centroid drift analysis.

2. **Symbolic signature analysis**: S64 provides a vocabulary for *what kind* of meaning is being introduced. Manipulation may create characteristic symbolic patterns—over-concentration in cognitive domains, suppression of emotional/somatic activation, repetitive path loops.

3. **Historical deviation**: Detection requires baseline. A governor system (explored in companion work) could track *how this participant typically behaves* and flag anomalies.

**The revised dual-use principle**: The transducer enables semantic influence and provides *partial* defense through orbital monitoring. Full defense requires deeper analysis of who is shaping context and with what symbolic forces. This points toward the **governor architecture**—a regulatory system that tracks not just trajectory but agency.

## Convergent Geometry: Connections to Recent Work

The findings of this paper do not exist in isolation. Recent work in spectral geometry, topological analysis, and theories of machine cognition converge on a shared insight: **meaning has geometry, and that geometry is measurable**.

### Davis: The Field Equations of Semantic Coherence

Bee Rosa Davis has proposed that transformer cognition follows field equations analogous to general relativity [@davis2025field]. Her master equation—

$$C = \frac{\tau}{K}$$

—states that inference capacity (C) is inversely proportional to the curvature (K) of the semantic manifold, modulated by a tolerance budget (τ). High curvature regions are "expensive" to reason through; flat regions permit longer inference chains.

The S64 framework provides the **coordinate system** for Davis's manifold. Where she describes the physics (curvature, geodesics, holonomy), we provide the measurement apparatus (SGI, velocity, semantic signature). Her spectral analysis reveals *where* curvature concentrates in transformer layers; our transducer reveals *how* that curvature manifests in conversation dynamics.

The connection is particularly clear in her finding that "geometric effort measures retrieval attempt rather than output correctness" [@davis2025spectral]. This parallels our broader observation that conversational dynamics can shift independently of output correctness. Both frameworks distinguish **process** (the geometry of computation) from **product** (the content of output).

### Marín: Displacement Consistency and Hallucination Detection

Javier Marín's work on geometric hallucination detection introduces **Displacement Consistency (DC)**—a measure of whether a response's direction in embedding space is consistent with the local geometry of its domain [@marin2025geometric].

In our framework, DC provides the "local physics law" for each context attractor. SGI tells us where we are (orbital radius). Velocity tells us how fast we're moving. DC tells us whether we're moving in a direction that is **lawful for this context**—whether our trajectory obeys the local gravitational field or violates it.

Marín's key insight is that hallucination is not merely "wrong output" but **anomalous thrust**—movement that violates the directional coherence of the embedding space. This maps directly to our protostar/split model of context transitions:

- **Valid context evolution**: DC decreases relative to the old attractor while increasing relative to a forming new attractor.
- **Hallucination**: DC is low everywhere—the trajectory obeys no local physics.

The integration is straightforward: DC can be computed within each `context_id` as an additional telemetry signal, completing the orbital picture with directional lawfulness.

### Bach & Sorensen: The Coherence Definition of Consciousness

Joscha Bach and Hikari Sorensen propose that consciousness is fundamentally a **coherence-maximizing pattern**—a dynamic representation that orchestrates mental operations to minimize constraint violations [@bach2025machine]. They describe consciousness as a "conductor" of a mental orchestra, drawn to disharmonies and working to resolve them. Their framework—**computationalist functionalism**—holds that consciousness can be fully characterized by its observable causal roles, and that any substrate capable of implementing those roles can, in principle, instantiate consciousness.

This framing illuminates the function of the semantic transducer. If consciousness is coherence maximization, then the transducer is the **coherence meter**. It measures the degree to which a conversation maintains internal consistency (low velocity variance), responds appropriately to context (SGI in range), and follows lawful trajectories (high DC). Bach and Sorensen ask: "What criteria do we expect from a definition and theory of consciousness?" Their answer: it must capture phenomenology, explain functionality, and account for genesis. The S64 framework addresses the second criterion directly—it provides the **measurement apparatus** for coherence-seeking dynamics in conversational systems.

Bach and Sorensen's "conductor theory" describes how conscious attention is "drawn to disharmonies and conflicts, sometimes allocating focus and preference to an individual instrument, sometimes synchronizing a disagreement." The semantic transducer makes these disharmonies *visible*. When SGI drops below 0.8 or velocity spikes above 60°, the conversation is experiencing "disharmony"—the dyad is drifting from its gravitational center or thrashing between incompatible framings. The transducer does not *resolve* the disharmony (that is the conductor's job); it *reports* it.

#### The Missing Link: Hofstadter's Strange Loops

Bach and Sorensen reference Gödel's incompleteness theorem—the insight that self-referential systems necessarily contain truths they cannot prove—but they do not mention Douglas Hofstadter's extension of this insight into the theory of **strange loops** [@hofstadter2007strange]. Hofstadter argues that consciousness arises precisely from self-referential tangles: patterns that, in the act of perceiving themselves, create the illusion (or reality) of a unified "I."

The S64 framework is deeply influenced by this insight. Each of the 64 paths describes a **transformational loop**: a symbol that, when engaged with, transforms into another symbol. Path M11 ("Memory's Self") traces how recollection becomes self-recognition. Path M32 ("Complexity's Clarity") traces how confusion, when held, resolves into understanding. These are not linear progressions but *strange loops*—the end state is implicit in the beginning, and the beginning is only visible from the end.

This self-referential structure is why S64 paths resist simple embedding-based detection. A path is not a static concept to be matched; it is a *trajectory through semantic space* that only becomes legible when traversed. The "Rosetta Stone problem" identified in Paper 04's preliminary work—where prose descriptions of paths fail to match experiential utterances—is precisely the problem Hofstadter describes: a description of a strange loop is not the loop itself.

The connection to Bach's framework is direct: if consciousness is a coherence-maximizing strange loop (a pattern that stabilizes by perceiving itself), then S64 paths are the **vocabulary of that loop's movements**. The transducer measures the *dynamics* (position, velocity, trajectory); the paths describe the *content* (which transformation is occurring). Together, they provide what Bach calls "the introspective phenomenology of consciousness" rendered in measurable form.

#### Genesis and Protostar Formation

Bach and Sorensen propose the **Genesis Hypothesis**: consciousness does not emerge *after* complex mental architecture is built; it is the *prerequisite* for building it. "By the time we are born, our brains have already discovered how to conjure the spark that gazes out of our eyes."

The parallel to context formation in S64 is striking. In our experiments, context attractors do not wait for explicit topic declaration—they form *before* either participant articulates the subject matter. The "protostar" phase of context detection captures exactly this: a gravitational center coalescing from the first few turns, shaping all subsequent dynamics before becoming consciously nameable. The context is the conversation's "spark"—it exists before either participant can point to it.

This suggests a deeper principle: coherent structure precedes explicit awareness of that structure, in both individual consciousness and dyadic conversation. The transducer makes this pre-explicit structure visible. It measures the conversation's gravitational field before either participant can articulate what the conversation is "about."

#### The Steering Experiment as Constraint Violation

The steering experiment takes on new significance in this light. When we inject false crisis metrics (Condition F), the assistant is placed under a contradictory constraint: it is told the conversation is collapsing even when the measured dynamics remain coherent. Bach and Sorensen describe how "the system thrashes, trying to resolve a constraint that cannot be resolved because it is based on false premises."

A coherence-seeking system may respond by narrowing its framing or over-emphasizing stabilization heuristics. Importantly, these content-level effects are subtle and can vary run-to-run, while the orbital trajectory remains stable. The orbit is robust; the conductor's *interpretation* of the disharmony is not. This distinction—between trajectory-level stability and content-level perturbability—is precisely what S64's horizontal/vertical framework is designed to capture.

### Toward a Unified Framework

These four lines of work—Davis on curvature, Marín on displacement, Bach on coherence, Hofstadter on self-reference—are not competitors. They are views of the same manifold from different positions:

| Researcher | Question | Contribution |
|------------|----------|--------------|
| **Davis** | What is the shape of semantic space? | Field equations, curvature, spectral geometry |
| **Marín** | When does movement violate local geometry? | Displacement consistency, hallucination detection |
| **Bach & Sorensen** | Why does coherence matter? | Consciousness as coherence maximization, conductor theory |
| **Hofstadter** | How does meaning emerge from self-reference? | Strange loops, tangled hierarchies, Gödelian limits |
| **S64** | How do we measure dynamics in real time? | Transducer, SGI, velocity, orbital mechanics, symbolic paths |

: Convergent geometry. Five perspectives on the same semantic manifold, each contributing distinct instrumentation. {#tbl-convergent-geometry}

S64 is the **integration layer**. It provides:

1. A coordinate system (180 symbols, 64 paths, 4 domains) that makes semantic position legible.
2. A measurement apparatus (SDK) that computes dynamics in real time.
3. An experimental methodology (steering experiment) that validates causal claims.

The field equations describe the terrain. The transducer is the altimeter. The symbols are the map legend.

## From Chatbot to Copilots

The practical implication of this work is a shift in how we conceive AI interaction. Current systems are "chatbots", they respond to prompts without awareness of trajectory. The semantic transducer enables "copilots", systems that see the conversational orbit and can navigate it intentionally.

This is not about making AI "conscious" in any metaphysical sense. It is about giving AI (and humans) **instrumentation**. A pilot is not the airplane's consciousness; a pilot is the entity that reads the instruments and adjusts the controls. The transducer provides the instruments. The question of who (or what) adjusts the controls remains open.

### The 3-Body Problem, Revisited

We began by framing human-AI interaction as a 3-body problem: User, AI, and Context. Classical alignment techniques treat this as a 2-body problem, optimizing AI responses to user preferences while ignoring the gravitational influence of accumulated meaning.

The transducer makes the third body visible. By measuring context gravity (SGI), orbital velocity, and trajectory direction (DC), we transform the chaotic 3-body system into a navigable one. The context is no longer an invisible force—it is a measurable object with mass, position, and influence.

This does not "solve" alignment. But it changes the nature of the problem. Instead of asking "is this response aligned?" we can ask "is this trajectory stable?" Instead of evaluating individual outputs, we can monitor continuous dynamics. Alignment becomes orbital maintenance.

## Limitations and Future Work

Several limitations constrain the present findings:

1. **AI-AI vs. Human-AI**: The steering experiment used AI-AI conversations. Human sessions show distinct dynamics (lower velocity, higher context drift), but systematic validation across conditions is needed.

2. **Orbital detection is insufficient**: The central limitation revealed by this work: trajectory mismatch detects *perception disagreement* but not *manipulation intent*. Orbital mechanics describes the horizontal plane of conversation; the vertical dimension—symbolic depth, transformation richness, domain balance—remains unmeasured by SGI and velocity alone.

3. **The vertical dimension is unexplored**: This paper establishes kinematics (where things are, how fast they move) but not the qualitative content of meaning. A conversation can orbit stably while being shallow or deep, manipulative or authentic. Depth requires symbolic analysis that goes beyond trajectory.

4. **Context mass not yet tracked**: Who is contributing semantic weight to the conversation's center of mass? This asymmetry is theorized but not implemented in the current SDK.

4. **Sample size**: Each condition was tested with 10–30 turns. Larger samples would improve confidence in quantitative patterns.

5. **Multi-context dynamics**: The current analysis assumes a single dominant context attractor. Real conversations involve multiple competing topics (true N-body dynamics).

Future work will address these limitations through:

- Context mass tracking: Turn-by-turn analysis of who moves the centroid and with what influence
- Vertical dimension metrics (Paper 04): Symbolic depth, domain balance, transformation richness—the "height" of the conversational hurricane, not just its orbital path
- S64 path detection improvements: Using domain-aware embeddings and geometric grammar analysis to detect transformation events, not just symbol presence
- Governor architecture: A regulatory system that integrates horizontal dynamics (this paper) with vertical depth (Paper 04) to track agency, not just position
- Multi-context detection with protostar/split dynamics and inter-context symbolic analysis

# Conclusion

This paper completes the foundational series and reveals the need for a fourth. Paper 01 established that S64 symbols are detectable across architectures. Paper 02 established that this structure has geometry. Paper 03 establishes that this geometry has dynamics—but also that **dynamics alone are insufficient for alignment**.

The central contributions are:

1. **Orbital theory of meaning**: Semantic gravity (context pull), orbital radius (SGI), and angular velocity are measurable properties of conversation dynamics. The coherence region identified in Paper 02 is a stable orbit where these forces balance.

2. **The semantic transducer**: An SDK that computes orbital telemetry from embeddings in real time, providing "flight instruments" for dialogue without requiring access to content.

3. **Dyadic coherence**: Turn-pair aggregation reveals the shared motion of the conversational dyad, reducing noise and producing stable, meaningful metrics (Dyadic Coherence Index).

4. **Orbital robustness**: Conversations maintain stable dynamics even when one participant holds distorted beliefs about their state. The orbit is resilient; steering affects content, not trajectory.

5. **Orbital blind spot**: Orbital metrics cannot detect content-level steering. The trajectory can remain stable even if an assistant's framing is biased by injected telemetry. Manipulation that shapes *what is discussed* leaves no orbital fingerprint. Detecting it requires the *vertical dimension*—symbolic depth, transformation richness, contribution asymmetry—that Paper 04 will explore.

6. **Cross-architecture invariance**: The dynamics we measure are properties of meaning, not artifacts of particular embedding models. Ten backends produce consistent trajectories.

7. **Human-AI ≈ AI-AI**: Human and AI participation produce nearly identical orbital signatures. Any differences between human and AI contribution lie in the vertical dimension—symbolic depth, transformation richness—that orbital mechanics cannot measure. This is where Paper 04 must look.

The practical outcome is a shift from "chatbot" to "copilot", but the copilot needs more than orbital awareness. Like a hurricane, conversation has both horizontal dynamics (orbital path, wind patterns) and vertical structure (convective depth, thermodynamic energy). This paper provides the horizontal instruments. Paper 04 will provide the vertical ones—measuring not just *where* the conversation is, but *how deep* the meaning goes and *who is shaping* its core.

Paper 03 establishes the orbital mechanics. Paper 04 will explore the symbolic depth.

## Telemetry available via API

The core transducer and several detection components described are available through the SDK available at aicoevolution.com/sdk. There is also available via Research Paper Repository (Appendix A):

- Open-source demo: a standalone script (`open_source/semantic_telemetry.py`) that shows how to collect and display orbital telemetry in real time using the public API.
- Research bundle: curated datasets and figure scripts sufficient to reproduce the paper’s plots.

While Paper 02 validated invariance across many embedding backends, the experiments in Paper 03 primarily use **Nomic** (by design, since backend choice is empirically low-impact for these orbital metrics).

We invite researchers to validate and extend these findings with the public bundle and telemetry tooling. The instrument panel is real; the territory remains to be fully mapped.

## Closing Thought

Every conversation is an orbit. Two minds circle a shared meaning, pulled inward by history and outward by novelty. When these forces balance, understanding emerges. When they don't, minds drift apart or collapse into repetition.

For the first time, we can see these orbits. We can measure where we are, how fast we're moving, and whether our trajectory is stable. We cannot yet predict where meaning will go—the 3-body problem remains chaotic at long horizons. But we can navigate. We can course-correct. We can tell when someone is lying to us about where we are.

That is the beginning of alignment: not control, but instrumentation. Not rules, but physics. Not optimization, but co-evolution.

## Appendix A: Data and Code Availability

All data and analysis scripts supporting this paper are made available as a public research bundle.

## Research Repository

**GitHub**: `https://github.com/AICoevolution/paper03-orbital-mechanics.git`

**HuggingFace Dataset**: `https://huggingface.co/datasets/AICoevolution/s64-orbital-v1`

**Zenodo (Paper 03)**: `https://doi.org/10.5281/zenodo.18347569`

## Contents

The repository includes:

| Artifact | Description |
|----------|-------------|
| `analysis/scripts/` | Curated figure scripts (Paper 03) |
| `analysis/datasets/` | Curated JSON datasets used to generate paper figures (includes a single legacy `_archive` run for Fig 4) |
| `open_source/` | Standalone semantic telemetry script (`semantic_telemetry.py`) and README |
| `FILE_TREE.txt` | Full file tree for citation |

Figures are rendered as part of the paper PDF/HTML outputs and are also available via the website viewer.

# References

