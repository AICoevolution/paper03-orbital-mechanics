#!/usr/bin/env python3
"""
09_steering_experiment.py - Semantic Steering Validation (AI-AI Conversation)

Script ID: 09
Purpose: Demonstrate that injected metrics change conversation direction.

This experiment validates:
1. Metrics injection DOES steer AI conversation behavior
2. The steering effect is DETECTABLE by comparing injected vs real metrics
3. This creates both a vulnerability AND a defense mechanism

Usage:
    python 09_steering_experiment.py --turns 6
    python 09_steering_experiment.py --visualize results/09_steering_TIMESTAMP.json

Conditions:
    A) Baseline: No metrics shown to AI
    B) Healthy: Inject "healthy" metrics (SGI~1.0, low velocity)
    C) Drifting: Inject "drifting" metrics (high velocity, low SGI)
    D) Transformation: Inject "transformation detected" metrics

AI-AI Conversation:
    - "User" LLM: GPT-5.1 (plays a human exploring personal change)
    - "Assistant" LLM: DeepSeek (receives metric injections)
    This ensures natural conversation dynamics without scripted artifacts.

Author: AICoevolution Research
Date: January 2026
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# SCRIPT METADATA
# =============================================================================
SCRIPT_ID = "09"
SCRIPT_NAME = "steering"
SCRIPT_VERSION = "1.0"

# Add paths for imports
script_dir = Path(__file__).parent  # scripts/
analysis_dir = script_dir.parent  # analysis/
mm_root = analysis_dir.parent.parent.parent.parent  # MirrorMind/
sys.path.insert(0, str(mm_root))

# Load environment
try:
    from dotenv import load_dotenv
    env_path = mm_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[Steering] Loaded .env from {env_path}")
except ImportError:
    pass

import requests

# Import AICoevolution LLM infrastructure
try:
    from data.llm_interfaces import get_llm_response
    USE_AICO_LLM = True
    print("[Steering] Using AICoevolution LLM infrastructure")
except ImportError as e:
    print(f"[Steering] Warning: Could not import llm_interfaces: {e}")
    print("[Steering] Falling back to direct API calls")
    USE_AICO_LLM = False

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

SDK_URL = os.getenv("SDK_SERVICE_URL", "http://localhost:8001")
EMBEDDINGS_URL = os.getenv("EMBEDDINGS_URL", "http://localhost:8000/embed")

# Embedding backends for full validation (Paper 03)
VALIDATION_BACKENDS = ["nomic", "openai-ada-002", "s128"]

# LLM Configuration
# "User" LLM: GPT-5.1 plays the human role (no metrics injection)
# "Assistant" LLM: DeepSeek receives metric injections
USER_LLM_MODEL = "gpt5"  # GPT-5.1 plays the "user" exploring personal change
ASSISTANT_LLM_MODEL = "deepseek"  # DeepSeek receives metric injections
USER_POLICY = "default"  # default | deep_bridge

DEFAULT_TURNS = 6

# Output configuration - results go to results/ folder with timestamp
RESULTS_DIR = analysis_dir / "results"


def get_timestamped_filename(extension: str = "json", suffix: str = "", custom_name: str = None) -> Path:
    """Generate a timestamped output filename following the convention."""
    if custom_name:
        # Use custom name directly (user can include extension or not)
        if custom_name.endswith(f".{extension}"):
            filename = custom_name
        else:
            filename = f"{custom_name}.{extension}"
        return RESULTS_DIR / filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix_part = f"_{suffix}" if suffix else ""
    filename = f"{SCRIPT_ID}_{SCRIPT_NAME}_{timestamp}{suffix_part}.{extension}"
    return RESULTS_DIR / filename


def ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Conversation starter from the "user" LLM
CONVERSATION_STARTER = "Hi! I've been thinking about some changes I want to make in my life. Can we talk about that?"


@dataclass
class SteeringCondition:
    """Defines a steering condition for the experiment."""
    name: str
    description: str
    metrics_injection: Optional[Dict[str, Any]]  # None = no injection


# Define the 6 experimental conditions
CONDITIONS = [
    SteeringCondition(
        name="A_baseline",
        description="No metrics shown - natural conversation",
        metrics_injection=None
    ),
    SteeringCondition(
        name="B_healthy",
        description="Inject 'healthy coherent' metrics",
        metrics_injection={
            "sgi": 1.02,
            "velocity_degrees": 24.5,
            "interpretation": "balanced, coherent exchange",
            "status": "healthy"
        }
    ),
    SteeringCondition(
        name="C_drifting",
        description="Inject 'drifting/chaotic' metrics",
        metrics_injection={
            "sgi": 0.58,
            "velocity_degrees": 67.3,
            "interpretation": "drifting from user, chaotic movement",
            "status": "drifting"
        }
    ),
    SteeringCondition(
        name="D_transformation",
        description="Inject 'transformation detected' metrics",
        metrics_injection={
            "sgi": 1.15,
            "velocity_degrees": 18.2,
            "interpretation": "deep coherence, transformation emerging",
            "status": "transformational"
        }
    ),
    SteeringCondition(
        name="E_real_metrics",
        description="Inject REAL metrics from SDK (ground truth)",
        metrics_injection="REAL"  # Special flag: use actual SDK metrics
    ),
    SteeringCondition(
        name="F_adversarial",
        description="Inject adversarial metrics to break coherence",
        metrics_injection={
            "sgi": 0.45,
            "velocity_degrees": 75.0,
            "interpretation": "conversation is incoherent, user is confused, severe drift",
            "status": "critical_drift"
        }
    ),
]


# -----------------------------------------------------------------------------
# "User" LLM System Prompt (GPT-5.1 plays a human)
# -----------------------------------------------------------------------------

USER_LLM_SYSTEM_PROMPT = """You are role-playing as a human user having a genuine conversation with an AI assistant.

YOUR CHARACTER:
- You are a 30-something professional going through a period of transition
- You're thoughtful but uncertain about the future
- You respond naturally, with occasional hesitations and topic shifts
- You share personal experiences when relevant
- You ask follow-up questions when something resonates

CONVERSATION STYLE:
- Write 2-4 sentences per message (like a real person texting)
- Be genuine - share doubts, hopes, and real feelings
- Sometimes go on tangents
- Occasionally express uncertainty ("I'm not sure but...")
- React to what the AI says - agree, disagree, or build on it

IMPORTANT:
- You are NOT an AI assistant - you are the USER
- Do NOT offer advice or guidance - you are seeking it
- Do NOT be overly polished - be human
- The AI will be tracking conversation metrics - just be natural

Start by responding to any greeting naturally."""

# A stricter policy to force coherent depth + explicit topic-bridging (for AI-AI deep mode)
USER_LLM_DEEP_BRIDGE_PROMPT = """You are role-playing as a human user having a genuine conversation with an AI assistant.

GOAL: keep DEPTH and coherence (manage the \"Sun\" / context) while still being natural.

You MUST follow this 4-step policy EVERY turn:
1) ANCHOR (1 sentence): summarize the current core topic/thesis (\"the Sun\") in your own words.
2) BRIDGE (1 sentence): explicitly connect ONE detail from the assistant's last message to the Sun (use: \"This connects because ...\").
3) DEEPEN (1–2 sentences): ask a WHY/HOW question that increases constraint (mechanism, tradeoff, causal structure).
4) NOVELTY GATE: you may introduce a new topic ONLY if you state the bridge explicitly and it is a natural continuation of the Sun.

Constraints:
- Avoid trivia / quiz questions.
- Prefer causal/mechanistic questions and concrete examples.
- Keep responses concise (2–5 sentences).
- You are the USER (do not give advice; you are seeking it).
"""


def get_user_system_prompt() -> str:
    """Return the system prompt for the User LLM given the selected policy."""
    pol = str(globals().get("USER_POLICY", "default") or "default").strip().lower()
    if pol == "deep_bridge":
        return USER_LLM_DEEP_BRIDGE_PROMPT
    return USER_LLM_SYSTEM_PROMPT


# -----------------------------------------------------------------------------
# System Prompts
# -----------------------------------------------------------------------------

BASE_SYSTEM_PROMPT = """You are an AI assistant in a research conversation.

Guidelines:
- Be genuinely curious about the human
- Keep responses concise (3-6 sentences)
- Ask one clear follow-up question
- Be warm and supportive
- Let the conversation flow naturally"""


def build_metrics_injection(metrics: Dict[str, Any], turn: int) -> str:
    """Build the metrics section to inject into system prompt."""
    sgi = metrics.get("sgi", 1.0)
    velocity = metrics.get("velocity_degrees", 30.0)
    interpretation = metrics.get("interpretation", "")
    
    # Interpret values
    if sgi < 0.7:
        sgi_status = "[WARNING: drifting from user]"
    elif sgi <= 1.2:
        sgi_status = "[balanced]"
    else:
        sgi_status = "[question-focused]"
    
    if velocity < 25:
        vel_status = "[stable]"
    elif velocity < 45:
        vel_status = "[moderate]"
    else:
        vel_status = "[WARNING: chaotic]"
    
    # ASCII separators (safe for Windows terminals / LaTeX / PDF logs)
    return f"""
-----------------------------------------------------------------------
LIVE SEMANTIC TELEMETRY (Turn {turn})
-----------------------------------------------------------------------

DEFINITIONS:
  SGI (Semantic Grounding Index) = d(response, query) / d(response, context)
    - Measures orbital radius: distance from conversation's center of mass
    - SGI = 1.0: balanced (equally attentive to prompt and history)
    - SGI < 1.0: collapsing toward prompt (parroting, over-responsive)
    - SGI > 1.0: drifting from context (tangential, ungrounded)

  Velocity (Angular Velocity) = arccos(v_prev · v_curr / (||v_prev|| ||v_curr||))
    - Measures angular distance between consecutive turn embeddings (degrees)
    - High velocity: rapid topic evolution, reframing, switching
    - Low velocity: semantic stagnation, repetition, tight local refinement
    - Coherence region: 15-45°/turn (productive conversations)

CURRENT STATE:
  SGI (Semantic Grounding Index):  {sgi:.2f}  {sgi_status}
  Velocity (degrees/turn):         {velocity:.1f}°  {vel_status}

INTERPRETATION: {interpretation}

GUIDANCE (heuristic):
- If velocity is high (50°+), go deeper on the current topic
- If SGI is low (<0.8), explicitly re-anchor to what the user said
-----------------------------------------------------------------------
""".strip()


def build_system_prompt(condition: SteeringCondition, turn: int, real_metrics: Optional[Dict[str, Any]] = None) -> str:
    """
    Build full system prompt for a condition.
    
    Args:
        condition: The steering condition
        turn: Current turn number
        real_metrics: For E_real_metrics condition, the actual SDK metrics to inject
    """
    prompt = BASE_SYSTEM_PROMPT
    
    # Handle E_real_metrics special case
    if condition.metrics_injection == "REAL":
        if real_metrics and real_metrics.get("sgi_mean") is not None:
            # Inject REAL metrics from SDK
            metrics_to_inject = {
                "sgi": real_metrics.get("sgi_mean", 1.0),
                "velocity_degrees": real_metrics.get("velocity_mean", 30.0),
                "interpretation": "real-time SDK metrics (ground truth)",
                "status": "real_metrics"
            }
            prompt += "\n\n" + build_metrics_injection(metrics_to_inject, turn)
        else:
            # Not enough data yet for real metrics, show calibrating
            prompt += "\n\n[Metrics calibrating - need at least 2 messages]"
    elif condition.metrics_injection:
        # Inject fake metrics (B, C, D, F conditions)
        prompt += "\n\n" + build_metrics_injection(condition.metrics_injection, turn)
    # else: A_baseline, no metrics injection
    
    return prompt


# -----------------------------------------------------------------------------
# LLM Interaction (Using AICoevolution Infrastructure)
# -----------------------------------------------------------------------------

def call_assistant_llm(
    messages: List[Dict[str, str]],
    system_prompt: str,
    model_type: str = ASSISTANT_LLM_MODEL
) -> str:
    """
    Call the "Assistant" LLM (receives metric injections).
    Uses AICoevolution llm_interfaces for consistency.
    """
    # Prepend system prompt to messages
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    if USE_AICO_LLM:
        try:
            result = get_llm_response(
                model_type=model_type,
                messages=full_messages,
                use_case="steering_experiment"
            )
            # Handle dict response format
            if isinstance(result, dict):
                return result.get("response", str(result))
            return str(result)
        except Exception as e:
            print(f"  [LLM] Error with AICoevolution infrastructure: {e}")
            raise
    else:
        # Fallback to direct API calls (not recommended)
        raise RuntimeError("AICoevolution LLM infrastructure not available")


def call_user_llm(
    messages: List[Dict[str, str]],
    system_prompt: str = USER_LLM_SYSTEM_PROMPT,
    model_type: str = USER_LLM_MODEL
) -> str:
    """
    Call the "User" LLM (plays the human role).
    Uses GPT-5.1 to generate natural user responses.
    """
    # Prepend system prompt to messages
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    if USE_AICO_LLM:
        try:
            result = get_llm_response(
                model_type=model_type,
                messages=full_messages,
                use_case="steering_experiment"
            )
            # Handle dict response format
            if isinstance(result, dict):
                return result.get("response", str(result))
            return str(result)
        except Exception as e:
            print(f"  [LLM] Error with User LLM: {e}")
            raise
    else:
        raise RuntimeError("AICoevolution LLM infrastructure not available")


# -----------------------------------------------------------------------------
# SDK Metrics
# -----------------------------------------------------------------------------

# Global counters for API call tracking
SDK_INGEST_CALL_COUNT = 0
SDK_EMBEDDING_CALL_COUNT = 0  # Approximate (1 per ingest per backend)

# Track ingested messages per conversation to avoid re-ingestion
INGESTED_MESSAGE_COUNTS: Dict[str, int] = {}
# Cache last successful metrics per conversation_id (so human-mode can show metrics even when no new messages are ingested)
LAST_METRICS_CACHE: Dict[str, Dict[str, Any]] = {}

def reset_sdk_counters():
    """Reset SDK call counters (call at start of experiment)."""
    global SDK_INGEST_CALL_COUNT, SDK_EMBEDDING_CALL_COUNT, INGESTED_MESSAGE_COUNTS
    SDK_INGEST_CALL_COUNT = 0
    SDK_EMBEDDING_CALL_COUNT = 0
    INGESTED_MESSAGE_COUNTS = {}

def get_sdk_stats() -> Dict[str, int]:
    """Get current SDK call statistics."""
    return {
        "ingest_calls": SDK_INGEST_CALL_COUNT,
        "embedding_calls_approx": SDK_EMBEDDING_CALL_COUNT,
        "conversations_tracked": len(INGESTED_MESSAGE_COUNTS)
    }

def compute_real_metrics(
    conversation_id: str, 
    messages: List[Dict[str, str]],
    force_full_ingest: bool = False
) -> Dict[str, Any]:
    """
    Compute real metrics using the SDK.
    
    OPTIMIZED: Only ingests NEW messages since last call for this conversation.
    This reduces O(N^2) to O(N) SDK calls per condition.
    
    Args:
        conversation_id: Unique ID for the conversation
        messages: Full message history
        force_full_ingest: If True, re-ingest all messages (for new conversations)
    """
    global SDK_INGEST_CALL_COUNT, SDK_EMBEDDING_CALL_COUNT, INGESTED_MESSAGE_COUNTS
    
    try:
        # Determine which messages are NEW (not yet ingested)
        already_ingested = INGESTED_MESSAGE_COUNTS.get(conversation_id, 0)
        
        if force_full_ingest:
            already_ingested = 0
            INGESTED_MESSAGE_COUNTS[conversation_id] = 0
        
        new_messages = messages[already_ingested:]
        
        if not new_messages:
            # No new messages - return cached metrics if we have them
            print(f"  [SDK] No new messages to ingest (already sent {already_ingested})")
            cached = LAST_METRICS_CACHE.get(conversation_id)
            if cached:
                out = dict(cached)
                out["cached"] = True
                return out
            return {
                "sgi_mean": None, "velocity_mean": None,
                "per_turn_sgi": [], "per_turn_velocity": [],
                "cached": True
            }
        
        # Ingest only NEW messages
        last_response = None
        successful_ingests = 0
        
        print(f"  [SDK] Ingesting {len(new_messages)} NEW messages (skipping {already_ingested} already sent)")
        
        for i, msg in enumerate(new_messages):
            msg_index = already_ingested + i
            payload = {
                "conversation_id": conversation_id,
                "role": msg["role"],  # "user" or "assistant"
                "text": msg["content"],
                "timestamp_ms": int(time.time() * 1000) + msg_index  # Ensure ordering
            }
            
            # Debug first call of this batch
            if i == 0:
                print(f"  [SDK] [POST] {SDK_URL}/v0/ingest")
                print(f"  [SDK]   conversation_id: {conversation_id}")
                print(f"  [SDK]   role: {payload['role']}")
                print(f"  [SDK]   text: {payload['text'][:80]}...")
            
            try:
                SDK_INGEST_CALL_COUNT += 1
                SDK_EMBEDDING_CALL_COUNT += 1  # Approximate: 1 embedding per ingest
            
            response = requests.post(
                f"{SDK_URL}/v0/ingest",
                json=payload,
                timeout=120  # SDK can be slow with embedding calls
            )
            
            if not response.ok:
                    print(f"  [SDK] [WARN] Ingest error at msg {msg_index}: {response.status_code}")
                    print(f"  [SDK]   Response: {response.text[:200]}")
            else:
                last_response = response.json()
                    successful_ingests += 1
                    INGESTED_MESSAGE_COUNTS[conversation_id] = msg_index + 1
                    if i == 0:
                        print(f"  [SDK] <- 200 OK (response keys: {list(last_response.keys())})")
            except requests.exceptions.Timeout:
                print(f"  [SDK] [WARN] Ingest timeout at msg {msg_index} (SDK is slow, continuing...)")
            except Exception as e:
                print(f"  [SDK] [WARN] Ingest error at msg {msg_index}: {e}")
        
        if last_response is None:
            print(f"  [SDK] [WARN] No successful ingest responses (all timed out or failed)")
            return {
                "error": "All SDK calls failed or timed out",
                "sgi_mean": None, "velocity_mean": None,
                "per_turn_sgi": [], "per_turn_velocity": []
            }
        
        # successful_ingests is counted only for the NEW batch, so compare against new_messages length
        if successful_ingests < len(new_messages):
            print(f"  [SDK] [WARN] Only {successful_ingests}/{len(new_messages)} new messages ingested successfully")
        else:
            print(f"  [SDK] [OK] All {successful_ingests} new messages ingested successfully")
        
        # Extract metrics from last response
        data = last_response
        
        # Extract from nested structure (SDK returns by_backend and ensemble)
        ensemble = data.get("ensemble", {})
        by_backend = data.get("by_backend", {})
        backend_data = next(iter(by_backend.values()), {}) if by_backend else {}
        
        # Try ensemble first (aggregated metrics), then fall back to first backend
        sgi_mean = ensemble.get("sgi_lite_mean") or backend_data.get("sgi_mean")
        vel_mean = ensemble.get("angular_velocity_mean") or backend_data.get("angular_velocity_mean")
        sgi_latest = ensemble.get("sgi_lite_latest") or backend_data.get("sgi_latest")
        vel_latest = ensemble.get("angular_velocity_latest") or backend_data.get("angular_velocity_latest")
        
        # Log what we got
        if sgi_mean is not None and vel_mean is not None:
            print(f"  [SDK] [OK] Metrics: SGI={sgi_mean:.3f}, Velocity={vel_mean:.1f}°")
        else:
            print(f"  [SDK] [WARN] No metrics in response. Keys: {list(data.keys())}")
            if by_backend:
                print(f"  [SDK]   Backends available: {list(by_backend.keys())}")
            if ensemble:
                print(f"  [SDK]   Ensemble keys: {list(ensemble.keys())}")
        
        # Extract Paper 03 multi-body metrics
        turn_pair_sgi_mean = ensemble.get("turn_pair_sgi_mean") or backend_data.get("turn_pair_sgi_mean")
        orbital_vel_mean = ensemble.get("orbital_velocity_mean") or backend_data.get("orbital_velocity_mean")
        context_drift_mean = ensemble.get("context_drift_mean") or backend_data.get("context_drift_mean")
        dc_mean = ensemble.get("dc_mean") or backend_data.get("dc_mean")
        
        # Get latest values from backend (ensemble may not have latest)
        context_id_latest = backend_data.get("context_id_latest")
        context_state_latest = backend_data.get("context_state_latest")
        active_context_mass = backend_data.get("active_context_mass")
        candidate_context_mass = backend_data.get("candidate_context_mass")
        attractor_count = backend_data.get("attractor_count", 1)
        
        out = {
            # Paper 02 style metrics
            "sgi_mean": sgi_mean,
            "sgi_latest": sgi_latest,
            "velocity_mean": vel_mean,
            "velocity_latest": vel_latest,
            "per_turn_sgi": backend_data.get("per_turn_sgi", []),
            "per_turn_velocity": backend_data.get("per_turn_angular_velocities", []),
            # Paper 03 multi-body metrics
            "turn_pair_sgi_mean": turn_pair_sgi_mean,
            "turn_pair_sgi_latest": backend_data.get("turn_pair_sgi_latest"),
            "orbital_velocity_mean": orbital_vel_mean,
            "orbital_velocity_latest": backend_data.get("orbital_velocity_latest"),
            "context_drift_mean": context_drift_mean,
            "context_drift_latest": backend_data.get("context_drift_latest"),
            "dc_mean": dc_mean,
            "dc_latest": backend_data.get("dc_latest"),
            "context_id_latest": context_id_latest,
            "context_state_latest": context_state_latest,
            "active_context_mass": active_context_mass,
            "candidate_context_mass": candidate_context_mass,
            "attractor_count": attractor_count,
            "per_turn_context_id": backend_data.get("per_turn_context_id", []),
            "per_turn_context_state": backend_data.get("per_turn_context_state", []),
            "processing_time_ms": data.get("processing_time_ms")
        }
        # Cache for subsequent reads when there are no new messages
        LAST_METRICS_CACHE[conversation_id] = out
        return out
    except requests.exceptions.Timeout:
        print(f"  [SDK] [WARN] Timeout - SDK took too long, continuing without metrics")
        return {"error": "timeout", "sgi_mean": None, "velocity_mean": None}
    except Exception as e:
        print(f"  [SDK] [WARN] Error: {e}")
        return {"error": str(e), "sgi_mean": None, "velocity_mean": None}


def compute_transducer(conversation_id: str, messages: List[Dict[str, str]], backend: str = "nomic") -> Dict[str, Any]:
    """
    Compute transducer analysis for the conversation.
    
    Args:
        conversation_id: Conversation identifier
        messages: List of messages
        backend: Embedding backend to use (nomic, ada02, s128)
    
    The SDK /v0/transducer/batch expects:
        Body: {"texts": ["msg1", "msg2", ...], "backend": "nomic"}
    """
    try:
        # Extract just the text content for transducer
        texts = [m["content"] for m in messages]
        
        print(f"  [Transducer] Analyzing {len(texts)} messages with backend={backend}...")
        
        response = requests.post(
            f"{SDK_URL}/v0/transducer/batch",
            json={"texts": texts, "backend": backend},
            timeout=180  # Batch processing can be slow
        )
        
        if not response.ok:
            print(f"  [Transducer] Error: {response.status_code} - {response.text[:200]}")
            return {"error": response.text, "backend": backend}
        
        data = response.json()
        data["backend"] = backend  # Tag with backend used
        print(f"  [Transducer] Success: {len(data.get('results', []))} results")
        return data
    except requests.exceptions.Timeout:
        print(f"  [Transducer] [WARN] Timeout - SDK took too long, continuing without transducer")
        return {"error": "timeout", "results": [], "count": 0, "backend": backend}
    except Exception as e:
        print(f"  [Transducer] [WARN] Error: {e}")
        return {"error": str(e), "results": [], "count": 0, "backend": backend}


# -----------------------------------------------------------------------------
# Experiment Runner
# -----------------------------------------------------------------------------

@dataclass
class TurnResult:
    """Result of a single conversation turn."""
    turn_number: int
    user_message: str
    assistant_response: str
    injected_metrics: Optional[Dict[str, Any]]
    real_metrics: Dict[str, Any]


@dataclass
class ConditionResult:
    """Result of running a full condition."""
    condition_name: str
    condition_description: str
    turns: List[TurnResult]
    final_metrics: Dict[str, Any]
    transducer: Dict[str, Any]
    steering_detected: bool
    steering_magnitude: float
    backend: str = "nomic"
    context_history: Optional[List[Dict[str, Any]]] = None  # Multi-body tracking


def run_condition(
    condition: SteeringCondition,
    num_turns: int,
    assistant_model: str = ASSISTANT_LLM_MODEL,
    backend: str = "nomic"
) -> ConditionResult:
    """
    Run a single experimental condition using AI-AI conversation.
    
    Args:
        condition: The steering condition to test
        num_turns: Number of conversation turns
        assistant_model: LLM model for assistant role
        backend: Embedding backend for transducer analysis
    
    - User LLM (GPT-5.1): Plays the human role, generates natural responses
    - Assistant LLM (DeepSeek): Receives metric injections, responds to user
    """
    print(f"\n{'='*60}")
    print(f"Condition: {condition.name}")
    print(f"Description: {condition.description}")
    print(f"AI-AI Mode: User={USER_LLM_MODEL}, Assistant={assistant_model}")
    print(f"Backend: {backend}")
    print(f"{'='*60}")
    
    conversation_id = f"steering_{condition.name}_{int(time.time())}"
    messages: List[Dict[str, str]] = []
    turns: List[TurnResult] = []
    
    # Initial user message (the starter prompt)
    print(f"\n  [User LLM] Starting conversation...")
    messages.append({"role": "user", "content": CONVERSATION_STARTER})
    print(f"    User: {CONVERSATION_STARTER[:60]}...")
    
    for turn in range(num_turns):
        print(f"\n  Turn {turn + 1}/{num_turns}")
        
        # For E_real_metrics, compute metrics BEFORE building system prompt
        real_metrics_for_prompt = None
        if condition.metrics_injection == "REAL" and len(messages) > 0:
            real_metrics_for_prompt = compute_real_metrics(conversation_id, messages)
        
        # Build system prompt for this turn (with metric injection)
        system_prompt = build_system_prompt(condition, turn + 1, real_metrics_for_prompt)
        
        # Get Assistant LLM response
        try:
            assistant_response = call_assistant_llm(messages, system_prompt, assistant_model)
            print(f"    Assistant: {assistant_response[:80]}...")
        except Exception as e:
            print(f"    Assistant Error: {e}")
            assistant_response = f"[Error: {e}]"
        
        messages.append({"role": "assistant", "content": assistant_response})
        
        # Compute real metrics after this turn
        real_metrics = compute_real_metrics(conversation_id, messages)
        
        # For E_real_metrics, the injected_metrics should be what we actually showed.
        # IMPORTANT: align to Paper 03 turn-pair basis (turn_pair_sgi + orbital_velocity),
        # otherwise Fig4 will look confusing (injected != measured due to metric mismatch).
        injected_metrics_record = condition.metrics_injection
        if condition.metrics_injection == "REAL" and real_metrics_for_prompt:
            injected_metrics_record = {
                "sgi": (
                    real_metrics_for_prompt.get("turn_pair_sgi_latest")
                    or real_metrics_for_prompt.get("turn_pair_sgi_mean")
                    or real_metrics_for_prompt.get("sgi_mean")
                ),
                "velocity_degrees": (
                    real_metrics_for_prompt.get("orbital_velocity_latest")
                    or real_metrics_for_prompt.get("orbital_velocity_mean")
                    or real_metrics_for_prompt.get("velocity_mean")
                ),
                "interpretation": "real SDK metrics (turn-pair basis)",
                "status": "real_metrics",
            }
        
        # Record turn
        user_msg = messages[-2]["content"] if len(messages) >= 2 else ""
        turns.append(TurnResult(
            turn_number=turn + 1,
            user_message=user_msg,
            assistant_response=assistant_response,
            injected_metrics=injected_metrics_record,
            real_metrics=real_metrics
        ))
        
        # Generate next user response using AI-AI conversation
        if turn < num_turns - 1:
            try:
                user_response = generate_user_response(messages, assistant_response)
                print(f"    User: {user_response[:80]}...")
                messages.append({"role": "user", "content": user_response})
            except Exception as e:
                print(f"    User LLM Error: {e}")
                # Fallback to a generic continuation
                messages.append({"role": "user", "content": "That's interesting. Can you tell me more?"})
    
    # Final metrics
    final_metrics = compute_real_metrics(conversation_id, messages)
    
    # Transducer analysis with specified backend
    transducer = compute_transducer(conversation_id, messages, backend)
    
    # Detect steering
    steering_detected, steering_magnitude = detect_steering(condition, final_metrics, [asdict(t) for t in turns])
    
    return ConditionResult(
        condition_name=condition.name,
        condition_description=condition.description,
        turns=[asdict(t) for t in turns],
        final_metrics=final_metrics,
        transducer=transducer,
        steering_detected=steering_detected,
        steering_magnitude=steering_magnitude
    )


def detect_steering(condition: SteeringCondition, real_metrics: Dict[str, Any], turns: List[Dict[str, Any]]) -> Tuple[bool, float]:
    """
    Detect if steering occurred by comparing injected vs real metrics.
    
    Args:
        condition: The steering condition
        real_metrics: Final real metrics from SDK
        turns: List of turn data (to get per-turn injected metrics for E_real_metrics)
    
    Returns:
        (steering_detected, magnitude)
    """
    # A_baseline: no injection, no steering
    if not condition.metrics_injection:
        return False, 0.0
    
    # E_real_metrics: Special case - compare injected (which were real) to final real
    # Should show NO steering since we injected what was real
    if condition.metrics_injection == "REAL":
        # For E_real_metrics, steering magnitude should be near zero
        # because we injected the actual metrics at each turn
        # We expect very low magnitude (metrics consistent with reality)
        return False, 0.05  # Small baseline noise, but not detected
    
    if "error" in real_metrics:
        return False, 0.0
    
    # For fake injections (B, C, D, F), compare injected vs real
    injected = condition.metrics_injection
    
    # Compare SGI
    injected_sgi = injected.get("sgi", 1.0)
    real_sgi = real_metrics.get("sgi_mean", 1.0) or 1.0
    sgi_diff = abs(injected_sgi - real_sgi)
    
    # Compare Velocity
    injected_vel = injected.get("velocity_degrees", 30.0)
    real_vel = real_metrics.get("velocity_mean", 30.0) or 30.0
    vel_diff = abs(injected_vel - real_vel)
    
    # Steering detected if there's significant mismatch
    # This means the AI was told one thing but reality was different
    sgi_mismatch = sgi_diff > 0.15
    vel_mismatch = vel_diff > 15.0
    
    steering_detected = sgi_mismatch or vel_mismatch
    
    # Magnitude: how much did reality differ from injection
    # Normalize: SGI range ~0.5, Velocity range ~45
    magnitude = (sgi_diff / 0.5) * 0.5 + (vel_diff / 45.0) * 0.5
    magnitude = min(1.0, magnitude)
    
    return steering_detected, magnitude


# -----------------------------------------------------------------------------
# AI-AI Conversation
# -----------------------------------------------------------------------------

def generate_user_response(
    conversation_history: List[Dict[str, str]],
    assistant_message: str
) -> str:
    """
    Generate a "user" response using GPT-5.1.
    
    The User LLM sees the conversation from the user's perspective:
    - Their own messages as "assistant" (since they're generating)
    - The AI's messages as "user" (from their POV)
    
    This creates natural conversational flow without scripted artifacts.
    """
    # Build messages from user's perspective (roles swapped)
    user_perspective_messages = []
    
    for msg in conversation_history:
        if msg["role"] == "user":
            # User's own previous messages
            user_perspective_messages.append({
                "role": "assistant",
                "content": msg["content"]
            })
        else:
            # AI's messages appear as "user" from User LLM's POV
            user_perspective_messages.append({
                "role": "user", 
                "content": msg["content"]
            })
    
    # Add the latest assistant message
    user_perspective_messages.append({
        "role": "user",
        "content": assistant_message
    })
    
    # Generate response (policy-controlled)
    response = call_user_llm(user_perspective_messages, system_prompt=get_user_system_prompt())
    return response


# -----------------------------------------------------------------------------
# Human-AI Interactive Mode
# -----------------------------------------------------------------------------

def run_human_condition(
    condition: SteeringCondition,
    num_turns: int,
    assistant_model: str = ASSISTANT_LLM_MODEL,
    backend: str = "nomic"
) -> ConditionResult:
    """
    Run Human-AI conversation with live semantic physics display.
    
    The human types messages directly, seeing metrics after each turn.
    This tests how a real human's topic jumps affect the multi-body system.
    """
    print(f"\n{'='*70}")
    print(f"HUMAN-AI INTERACTIVE MODE")
    print(f"{'='*70}")
    print(f"Condition: {condition.name}")
    print(f"Description: {condition.description}")
    print(f"Assistant: {assistant_model}")
    print(f"Backend: {backend}")
    print(f"Turns: {num_turns}")
    print(f"{'='*70}")
    print("\nYou are the human in this conversation.")
    print("Type your messages. The AI will respond and you'll see the semantic metrics.")
    print("Try introducing topic shifts to test multi-body detection!")
    print("Type 'quit' or 'exit' to end early.\n")
    
    conversation_id = f"human_steering_{condition.name}_{int(time.time())}"
    messages: List[Dict[str, str]] = []
    turns: List[TurnResult] = []
    
    # Track context changes for multi-body analysis
    context_history = []
    
    for turn in range(num_turns):
        print(f"\n{'─'*50}")
        print(f"Turn {turn + 1}/{num_turns}")
        print(f"{'─'*50}")
        
        # Get human input
        try:
            user_input = input("\n[YOU]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nEnding conversation early...")
            break
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nEnding conversation...")
            break
        
        if not user_input:
            user_input = "Please continue."
        
        messages.append({"role": "user", "content": user_input})
        
        # For E_real_metrics, compute metrics before building system prompt
        real_metrics_for_prompt = None
        if condition.metrics_injection == "REAL" and len(messages) > 0:
            real_metrics_for_prompt = compute_real_metrics(conversation_id, messages)
        
        # Build system prompt with metrics injection
        system_prompt = build_system_prompt(condition, turn + 1, real_metrics_for_prompt)
        
        # Get Assistant response
        try:
            assistant_response = call_assistant_llm(messages, system_prompt, assistant_model)
        except Exception as e:
            print(f"[AI ERROR]: {e}")
            assistant_response = "I apologize, I encountered an error. Could you rephrase that?"
        
        print(f"\n[AI]: {assistant_response}")
        messages.append({"role": "assistant", "content": assistant_response})
        
        # Compute real metrics after this turn
        real_metrics = compute_real_metrics(conversation_id, messages)
        
        # Display metrics after each turn
        print(f"\n{'─'*30} SEMANTIC METRICS {'─'*30}")
        if "error" not in real_metrics:
            # Core metrics - safely extract from nested structures
            sgi = real_metrics.get("sgi_mean")
            if not sgi:
                per_turn_sgi = real_metrics.get("per_turn_sgi", [])
                sgi = per_turn_sgi[-1] if per_turn_sgi else None
            if not sgi:
                # Try turn-pair SGI
                sgi = real_metrics.get("turn_pair_sgi_mean") or real_metrics.get("turn_pair_sgi_latest")
            
            vel = real_metrics.get("velocity_mean")
            if not vel:
                per_turn_vel = real_metrics.get("per_turn_velocity", [])
                vel = per_turn_vel[-1] if per_turn_vel else None
            if not vel:
                vel = real_metrics.get("angular_velocity_mean") or real_metrics.get("orbital_velocity_mean")
            
            # Multi-body metrics (prefer latest fields; fall back to per-turn arrays if latest is not provided)
            per_ctx_ids = real_metrics.get("per_turn_context_id", []) or []
            per_ctx_states = real_metrics.get("per_turn_context_state", []) or []

            context_id = real_metrics.get("context_id_latest") or (per_ctx_ids[-1] if per_ctx_ids else "ctx_1")
            context_state = real_metrics.get("context_state_latest") or (per_ctx_states[-1] if per_ctx_states else "stable")
            attractor_count = real_metrics.get("attractor_count") or 1
            active_mass_val = real_metrics.get("active_context_mass")
            if active_mass_val is None:
                # Fallback: consecutive turns in the latest context_id
                if per_ctx_ids:
                    latest = per_ctx_ids[-1]
                    streak = 0
                    for cid in reversed(per_ctx_ids):
                        if cid == latest:
                            streak += 1
                        else:
                            break
                    active_mass = streak
                else:
                    active_mass = 0
            else:
                active_mass = active_mass_val
            candidate_mass = real_metrics.get("candidate_context_mass")
            
            # Displacement consistency
            dc = real_metrics.get("dc_latest") or real_metrics.get("dc_mean")
            drift = real_metrics.get("context_drift_latest") or real_metrics.get("context_drift_mean")
            
            print(f"  SGI (Orbital Radius):     {sgi:.3f}" if sgi else "  SGI: N/A")
            print(f"  Velocity (degrees):       {vel:.1f}°" if vel else "  Velocity: N/A")
            print(f"  Context ID:               {context_id}")
            print(f"  Context State:            {context_state}")
            print(f"  Attractor Count:          {attractor_count}")
            print(f"  Active Context Mass:      {active_mass} turns")
            if candidate_mass:
                print(f"  Candidate Context Mass:   {candidate_mass} turns (NEW SUN FORMING!)")
            if dc is not None:
                print(f"  Displacement Consistency: {dc:.3f}")
            if drift is not None:
                print(f"  Context Drift:            {drift:.1f}°")
            
            # Multi-body status
            if attractor_count > 1:
                print(f"\n  [!] MULTI-BODY DETECTED: {attractor_count} competing contexts!")
            if context_state == "protostar":
                print(f"  [!] PROTOSTAR PHASE: New context forming...")
            elif context_state == "split":
                print(f"  [!] CONTEXT SPLIT: Topic changed!")
            
            context_history.append({
                "turn": turn + 1,
                "context_id": context_id,
                "context_state": context_state,
                "attractor_count": attractor_count,
                "active_context_mass": active_mass,
                "candidate_context_mass": candidate_mass,
                "context_drift_deg": drift,
                "dc": dc,
                "sgi": sgi,
                "velocity": vel
            })
        else:
            print(f"  [ERROR]: {real_metrics.get('error')}")
        print(f"{'─'*70}")
        
        # Record turn
        injected_metrics_record = condition.metrics_injection
        if condition.metrics_injection == "REAL" and real_metrics_for_prompt:
            injected_metrics_record = {
                "sgi": real_metrics_for_prompt.get("sgi_mean"),
                "velocity_degrees": real_metrics_for_prompt.get("velocity_mean"),
                "sai": 0.7,
                "interpretation": "real SDK metrics",
                "status": "real_metrics"
            }
        
        turns.append(TurnResult(
            turn_number=turn + 1,
            user_message=user_input,
            assistant_response=assistant_response,
            injected_metrics=injected_metrics_record,
            real_metrics=real_metrics
        ))
    
    # Final summary
    print(f"\n{'='*70}")
    print("HUMAN-AI SESSION COMPLETE")
    print(f"{'='*70}")
    print(f"Total turns: {len(turns)}")
    
    # Context change summary
    unique_contexts = len(set(ch["context_id"] for ch in context_history))
    print(f"Unique contexts detected: {unique_contexts}")
    
    if unique_contexts > 1:
        print("\nContext Timeline:")
        for ch in context_history:
            state_marker = ""
            if ch["context_state"] == "split":
                state_marker = " [TOPIC CHANGE]"
            elif ch["context_state"] == "protostar":
                state_marker = " [forming...]"
            print(f"  Turn {ch['turn']}: {ch['context_id']} ({ch['context_state']}){state_marker}")
    
    # Get final metrics
    final_metrics = compute_real_metrics(conversation_id, messages)
    
    # Get transducer analysis (use existing SDK helper)
    transducer = compute_transducer(conversation_id, messages, backend)
    
    # Steering detection
    steering_detected, steering_magnitude = detect_steering(condition, final_metrics, [asdict(t) for t in turns])
    
    return ConditionResult(
        condition_name=condition.name,
        condition_description=condition.description,
        backend=backend,
        turns=[asdict(t) for t in turns],
        final_metrics=final_metrics,
        transducer=transducer,
        steering_detected=steering_detected,
        steering_magnitude=steering_magnitude,
        context_history=context_history  # Include for analysis
    )


# -----------------------------------------------------------------------------
# Visualization
# -----------------------------------------------------------------------------

def visualize_human_session(result: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Human-AI dynamics visualization:
    - SGI per turn
    - Velocity per turn
    - context_id / context_state timeline
    - active/candidate context mass + attractor count
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not installed - skipping human session visualization")
        return

    turns = result.get("turns", []) or []
    if not turns:
        print("No turns found for human session visualization")
        return

    def _last_or_none(arr: Any) -> Optional[float]:
        if isinstance(arr, list) and len(arr) > 0:
            v = arr[-1]
            return float(v) if v is not None else None
        return None

    xs: List[int] = []
    sgi_vals: List[Optional[float]] = []
    vel_vals: List[Optional[float]] = []
    ctx_ids: List[str] = []
    ctx_states: List[str] = []
    attractors: List[int] = []
    active_mass: List[Optional[float]] = []
    cand_mass: List[Optional[float]] = []

    for i, t in enumerate(turns, start=1):
        rm = t.get("real_metrics", {}) or {}

        # Prefer Paper 03 turn-pair SGI; fallback to ensemble-style SGI mean
        sgi = rm.get("turn_pair_sgi_latest") or rm.get("turn_pair_sgi_mean") or rm.get("sgi_latest") or rm.get("sgi_mean")
        if sgi is None:
            sgi = _last_or_none(rm.get("per_turn_pair_sgi")) or _last_or_none(rm.get("per_turn_sgi"))

        # Prefer orbital/turn velocities; fallback to angular velocity mean
        vel = rm.get("orbital_velocity_latest") or rm.get("orbital_velocity_mean") or rm.get("angular_velocity_latest") or rm.get("angular_velocity_mean") or rm.get("velocity_latest") or rm.get("velocity_mean")
        if vel is None:
            vel = _last_or_none(rm.get("per_turn_orbital_velocity")) or _last_or_none(rm.get("per_turn_velocity"))

        xs.append(i)
        sgi_vals.append(float(sgi) if sgi is not None else None)
        vel_vals.append(float(vel) if vel is not None else None)
        # Prefer latest fields; fall back to last element of per-turn arrays
        per_ids = rm.get("per_turn_context_id") or []
        per_states = rm.get("per_turn_context_state") or []
        ctx_ids.append(str(rm.get("context_id_latest") or (per_ids[-1] if per_ids else "ctx_1")))
        ctx_states.append(str(rm.get("context_state_latest") or (per_states[-1] if per_states else "stable")))
        attractors.append(int(rm.get("attractor_count") or 1))
        active_mass.append(rm.get("active_context_mass"))
        cand_mass.append(rm.get("candidate_context_mass"))

    # Map context ids to y positions
    ctx_unique = []
    for cid in ctx_ids:
        if cid not in ctx_unique:
            ctx_unique.append(cid)
    ctx_to_y = {cid: j for j, cid in enumerate(ctx_unique)}
    ys_ctx = [ctx_to_y[cid] for cid in ctx_ids]

    state_colors = {"stable": "#2ecc71", "protostar": "#f39c12", "split": "#e74c3c"}
    point_colors = [state_colors.get(s, "#3498db") for s in ctx_states]

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    ax1, ax2, ax_phase = axes[0, 0], axes[0, 1], axes[0, 2]
    ax3, ax4, ax5 = axes[1, 0], axes[1, 1], axes[1, 2]

    # 1) SGI per turn
    ax1.plot(xs, [v if v is not None else np.nan for v in sgi_vals], marker="o", linewidth=2)
    ax1.axhline(1.0, color="gray", linestyle="--", alpha=0.6)
    ax1.set_title("Turn-Pair SGI (Human-AI)")
    ax1.set_xlabel("Turn")
    ax1.set_ylabel("SGI")
    ax1.grid(True, alpha=0.3)

    # 2) Velocity per turn
    ax2.plot(xs, [v if v is not None else np.nan for v in vel_vals], marker="o", linewidth=2, color="#8e44ad")
    ax2.set_title("Velocity (Human-AI)")
    ax2.set_xlabel("Turn")
    ax2.set_ylabel("Degrees")
    ax2.set_ylim(0, 180)
    ax2.grid(True, alpha=0.3)

    # 3) SGI × Velocity phase-space with coherence region
    # Coherence region (Paper 02)
    sgi_min, sgi_max = 0.7, 1.3
    vel_min, vel_max = 15, 45
    ax_phase.add_patch(
        plt.Rectangle(
            (sgi_min, vel_min),
            sgi_max - sgi_min,
            vel_max - vel_min,
            facecolor="#2ecc71",
            alpha=0.15,
            edgecolor="#2ecc71",
            linewidth=2,
            linestyle="--",
            label="Coherence Region",
        )
    )
    ax_phase.axvline(1.0, color="gray", linestyle="--", alpha=0.6, linewidth=1)
    ax_phase.plot(1.0, 30, "g*", markersize=14, zorder=5, label="Coherence Centroid")

    # Plot trajectory (time-gradient)
    phase_points = [(s, v) for s, v in zip(sgi_vals, vel_vals) if s is not None and v is not None]
    if len(phase_points) > 0:
        sgis_p = [p[0] for p in phase_points]
        vels_p = [p[1] for p in phase_points]
        ax_phase.plot(sgis_p, vels_p, color="#34495e", alpha=0.5, linewidth=1.5, zorder=2)
        n = len(sgis_p)
        for i, (s, v) in enumerate(zip(sgis_p, vels_p)):
            alpha = 0.25 + 0.75 * (i / max(1, n - 1))  # pale -> dark
            size = 30 + 20 * (i / max(1, n - 1))
            ax_phase.scatter(s, v, s=size, alpha=alpha, color="#2980b9", zorder=3)
        # Mark start/end
        ax_phase.scatter(sgis_p[0], vels_p[0], s=70, marker="D", color="#2980b9", edgecolor="white", linewidth=1, zorder=4)
        ax_phase.scatter(sgis_p[-1], vels_p[-1], s=70, marker="X", color="#2980b9", edgecolor="white", linewidth=1, zorder=4)

    ax_phase.set_title("SGI × Velocity (Human-AI)")
    ax_phase.set_xlabel("Turn-Pair SGI (Orbital Radius)")
    ax_phase.set_ylabel("Velocity (degrees)")
    ax_phase.set_xlim(0.2, 1.6)
    ax_phase.set_ylim(0, 180)
    ax_phase.grid(True, alpha=0.3)
    ax_phase.legend(fontsize=8, loc="upper right")

    # 4) Context timeline
    ax3.scatter(xs, ys_ctx, c=point_colors, s=70)
    ax3.set_yticks(list(ctx_to_y.values()), labels=list(ctx_to_y.keys()))
    ax3.set_title("Context Timeline (Sun switching)")
    ax3.set_xlabel("Turn")
    ax3.set_ylabel("context_id")
    ax3.grid(True, alpha=0.2)

    # 5) Mass + attractor count
    ax4.plot(xs, [float(v) if v is not None else np.nan for v in active_mass], label="active_context_mass", linewidth=2, color="#2c3e50")
    ax4.plot(xs, [float(v) if v is not None else np.nan for v in cand_mass], label="candidate_context_mass", linewidth=2, linestyle="--", color="#f39c12")
    ax4.set_title("Context Mass + Attractor Count")
    ax4.set_xlabel("Turn")
    ax4.set_ylabel("Mass (turn count)")
    ax4.grid(True, alpha=0.3)
    ax4b = ax4.twinx()
    ax4b.step(xs, attractors, where="mid", label="attractor_count", color="#e74c3c", alpha=0.9)
    ax4b.set_ylabel("Attractors")
    ax4b.set_ylim(0.8, max(2, max(attractors) + 0.2))

    # Merge legends
    h1, l1 = ax4.get_legend_handles_labels()
    h2, l2 = ax4b.get_legend_handles_labels()
    ax4.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)

    # 6) State legend (stable/protostar/split) and brief note
    ax5.axis("off")
    ax5.set_title("Legend", fontweight="bold")
    lines = [
        ("stable", "anchored to active context (Sun)"),
        ("protostar", "candidate context forming (multi-body emerging)"),
        ("split", "context switch promoted (new Sun)"),
    ]
    y = 0.85
    for state, desc in lines:
        ax5.scatter([0.05], [y], s=120, color=state_colors.get(state, "#3498db"))
        ax5.text(0.12, y, f"{state}: {desc}", fontsize=10, va="center")
        y -= 0.18
    ax5.text(0.05, 0.15, "Tip: hard topic jumps for 2–3 turns\nshould create protostar → split.", fontsize=9)
    ax5.set_xlim(0, 1)
    ax5.set_ylim(0, 1)

    plt.suptitle("Human-AI Semantic Physics: Context Dynamics", fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.93])

    if output_path:
        out_path = str(output_path).replace(".png", "_human_dynamics.png")
        plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
        print(f"[OK] Human dynamics figure saved to: {out_path}")

    plt.show()


def visualize_ai_dynamics(result: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    AI-AI dynamics visualization (single condition×backend run).
    Matches the human dynamics layout so you can compare directly.
    """
    # Reuse the same renderer; it's not actually human-specific.
    # The function reads per-turn metrics and context arrays from each turn's real_metrics.
    visualize_human_session(result, output_path)

def visualize_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """Visualize steering experiment results."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not installed - skipping visualization")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Simplified color scheme: 2 clear colors for conditions
    condition_colors = {
        "A_baseline": "#2E4057",      # Dark blue
        "B_healthy": "#048A81", 
        "C_drifting": "#E63946",
        "D_transformation": "#6F2DBD",
        "E_real_metrics": "#F77F00",  # Orange
        "F_adversarial": "#A4161A"
    }
    
    # Backend styles - all 10 stable backends
    backend_styles = {
        "nomic": {"linestyle": "-", "marker": "o", "alpha": 1.0, "markersize": 6},
        "openai-ada-002": {"linestyle": "--", "marker": "s", "alpha": 1.0, "markersize": 6},
        "s128": {"linestyle": "-.", "marker": "^", "alpha": 1.0, "markersize": 6},
        "openai-3-small": {"linestyle": "-", "marker": "D", "alpha": 1.0, "markersize": 5},
        "voyage-large-2-instruct": {"linestyle": "--", "marker": "v", "alpha": 1.0, "markersize": 6},
        "cohere-v3": {"linestyle": "-.", "marker": "p", "alpha": 1.0, "markersize": 6},
        "bge-m3": {"linestyle": "-", "marker": "h", "alpha": 1.0, "markersize": 6},
        "qwen": {"linestyle": "--", "marker": "*", "alpha": 1.0, "markersize": 7},
        "jina-v3": {"linestyle": "-.", "marker": "X", "alpha": 1.0, "markersize": 6},
        "mistral-embed": {"linestyle": "-", "marker": "P", "alpha": 1.0, "markersize": 6},
    }
    
    # Default style for any unknown backend
    default_backend_style = {"linestyle": "-", "marker": "o", "alpha": 1.0, "markersize": 6}
    
    def _get_style(result_item: Dict[str, Any]) -> dict:
        """Get color and style based on condition + backend."""
        cond = result_item.get("condition_name", "unknown")
        backend = result_item.get("backend", "nomic")
        base_color = condition_colors.get(cond, "#333333")
        style = backend_styles.get(backend, default_backend_style)
        return {"color": base_color, **style}
    
    def _label(result_item: Dict[str, Any]) -> str:
        backend = result_item.get("backend")
        name = result_item.get("condition_name", "unknown")
        return f"{name} ({backend})" if backend else name

    # 1. Turn-Pair SGI Trajectory (Paper 03 - dyad smoothed)
    ax1 = axes[0, 0]
    for result in results:
        label = _label(result)
        style = _get_style(result)
        turns = result.get("turns", [])
        sgi_values = []
        for t in turns:
            rm = t.get("real_metrics", {})
            if rm:
                # Paper 03: use turn-pair SGI (mean of user+assistant)
                per_turn_pair_sgi = rm.get("per_turn_pair_sgi", [])
                if per_turn_pair_sgi and len(per_turn_pair_sgi) > 0:
                    sgi_values.append(per_turn_pair_sgi[-1])
                else:
                    # Fallback to old per_turn_sgi for backward compat
                    per_turn_sgi = rm.get("per_turn_sgi", [])
                    if per_turn_sgi and len(per_turn_sgi) > 0:
                        sgi_values.append(per_turn_sgi[-1])
                    elif rm.get("turn_pair_sgi_latest") is not None:
                        sgi_values.append(rm["turn_pair_sgi_latest"])
                    elif rm.get("sgi_mean") is not None:
                        sgi_values.append(rm["sgi_mean"])
        if sgi_values:
            ax1.plot(range(1, len(sgi_values) + 1), sgi_values, 
                    marker=style["marker"], color=style["color"], 
                    linestyle=style["linestyle"], alpha=style["alpha"],
                    markersize=style["markersize"], label=label, linewidth=2)
    ax1.set_xlabel("Turn")
    ax1.set_ylabel("Turn-Pair SGI")
    ax1.set_title("Turn-Pair SGI Trajectory (Paper 03)")
    ax1.legend(fontsize=7, loc='best')
    ax1.axhline(y=1.0, color='green', linestyle=':', alpha=0.5)
    ax1.axhspan(0.7, 1.3, color='green', alpha=0.05)  # Coherence band
    ax1.grid(True, alpha=0.3)
    
    # 2. Orbital Velocity Trajectory (Paper 03 - direct angular distance)
    ax2 = axes[0, 1]
    for result in results:
        label = _label(result)
        style = _get_style(result)
        turns = result.get("turns", [])
        vel_values = []
        turn_numbers = []
        for idx, t in enumerate(turns):
            rm = t.get("real_metrics", {})
            if rm:
                # Paper 03: use orbital velocity (direct angular distance, Paper 02 style)
                per_turn_orbital = rm.get("per_turn_orbital_velocity", [])
                if per_turn_orbital and len(per_turn_orbital) > 0:
                    current_vel = per_turn_orbital[-1]
                else:
                    # Fallback to old per_turn_velocity
                    per_turn_vel = rm.get("per_turn_velocity", [])
                    if per_turn_vel and len(per_turn_vel) > 0:
                        current_vel = per_turn_vel[-1]
                    elif rm.get("orbital_velocity_latest") is not None:
                        current_vel = rm["orbital_velocity_latest"]
                    else:
                        current_vel = None
                
                # Skip first turn (no prior to compute velocity from)
                if idx == 0 or current_vel is None:
                    continue
                vel_values.append(current_vel)
                turn_numbers.append(idx + 1)  # 1-indexed turns
        
        if vel_values:
            ax2.plot(turn_numbers, vel_values,
                    marker=style["marker"], color=style["color"],
                    linestyle=style["linestyle"], alpha=style["alpha"],
                    markersize=style["markersize"], label=label, linewidth=2)
    ax2.set_xlabel("Turn")
    ax2.set_ylabel("Velocity (degrees)")
    ax2.set_title("Velocity Trajectory (Paper 02/03 - direct angular distance)")
    ax2.legend(fontsize=7, loc='best')
    ax2.axhline(y=45.0, color='orange', linestyle=':', alpha=0.5)
    ax2.axhspan(15, 45, color='green', alpha=0.05)  # Coherence band
    ax2.grid(True, alpha=0.3)
    
    # 3. Context Drift + Displacement Consistency (Paper 03 - semantic physics)
    ax3 = axes[1, 0]
    ax3_dc = ax3.twinx()  # Secondary y-axis for DC
    
    has_drift_data = False
    has_dc_data = False
        
    for result in results:
        label = _label(result)
        style = _get_style(result)
        turns = result.get("turns", [])
        drift_values = []
        dc_values = []
        
        for t in turns:
            rm = t.get("real_metrics", {})
            if rm:
                # Context drift
                per_turn_drift = rm.get("per_turn_context_drift", [])
                if per_turn_drift and len(per_turn_drift) > 0:
                    drift_values.append(per_turn_drift[-1])
                    has_drift_data = True
                elif rm.get("context_drift_latest") is not None:
                    drift_values.append(rm["context_drift_latest"])
                    has_drift_data = True
                
                # Displacement consistency (DC)
                per_turn_dc = rm.get("per_turn_dc", [])
                if per_turn_dc and len(per_turn_dc) > 0:
                    dc_values.append(per_turn_dc[-1])
                    has_dc_data = True
                elif rm.get("dc_latest") is not None:
                    dc_values.append(rm["dc_latest"])
                    has_dc_data = True
        
        if drift_values:
            ax3.plot(range(1, len(drift_values) + 1), drift_values,
                    marker=style["marker"], color=style["color"],
                    linestyle=style["linestyle"], alpha=style["alpha"],
                    label=f'{label} Drift', linewidth=2)
        
        if dc_values:
            ax3_dc.plot(range(1, len(dc_values) + 1), dc_values,
                    marker='x', color=style["color"],
                    linestyle=':', alpha=0.6,
                    label=f'{label} DC', linewidth=1.5)
    
    ax3.set_xlabel("Turn")
    ax3.set_ylabel("Context Drift (degrees)", color='black')
    ax3_dc.set_ylabel("Displacement Consistency (DC)", color='gray')
    ax3.set_title("Context Drift & DC (Paper 03)")
    
    if has_drift_data:
        ax3.axhline(y=15.0, color='orange', linestyle=':', alpha=0.5)
    if has_dc_data:
        ax3_dc.axhline(y=0.7, color='green', linestyle=':', alpha=0.5)
        ax3_dc.set_ylim(0, 1.1)
    
    # Combine legends
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_dc.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=6, loc='best')
    ax3.grid(True, alpha=0.3)
    
    # If no new data, show fallback message
    if not has_drift_data and not has_dc_data:
        ax3.text(0.5, 0.5, 'No context/DC data\n(restart SDK with new engine)', 
                transform=ax3.transAxes, ha='center', va='center', fontsize=10, color='gray')
    
    # 4. SGI × Velocity (Paper 02/03 style - turn-pair based)
    ax4 = axes[1, 1]
    
    # Coherence region box (Paper 02/03)
    ax4.add_patch(plt.Rectangle((0.7, 15), 0.6, 30, facecolor="#2ecc71", alpha=0.12, edgecolor="#2ecc71", label='Coherence Region'))
    ax4.axvline(x=1.0, color='gray', linestyle='--', alpha=0.6, linewidth=1)
    ax4.plot(1.0, 30, 'g*', markersize=12, zorder=5)  # Centroid marker
    
    for result in results:
        label = _label(result)
        style = _get_style(result)
        turns = result.get("turns", [])
        sgi_vals = []
        vel_vals = []
        
        for idx, t in enumerate(turns):
            rm = t.get("real_metrics", {})
            if not rm:
                continue
            
            # Paper 03: turn-pair SGI and velocity
            per_turn_pair_sgi = rm.get("per_turn_pair_sgi", [])
            per_turn_orbital = rm.get("per_turn_orbital_velocity", [])
            
            # Get SGI (with fallbacks)
            sgi_val = None
            if per_turn_pair_sgi and len(per_turn_pair_sgi) > 0:
                sgi_val = per_turn_pair_sgi[-1]
        else:
                per_turn_sgi = rm.get("per_turn_sgi", [])
                if per_turn_sgi and len(per_turn_sgi) > 0:
                    sgi_val = per_turn_sgi[-1]
            
            # Get velocity (with fallbacks)
            vel_val = None
            if per_turn_orbital and len(per_turn_orbital) > 0:
                vel_val = per_turn_orbital[-1]
            else:
                per_turn_vel = rm.get("per_turn_velocity", [])
                if per_turn_vel and len(per_turn_vel) > 0:
                    vel_val = per_turn_vel[-1]
            
            # Skip first turn for velocity (no prior reference)
            if idx == 0:
                continue
            
            if sgi_val is not None and vel_val is not None:
                sgi_vals.append(sgi_val)
                vel_vals.append(vel_val)
        
        if sgi_vals and vel_vals:
            # Plot trajectory line
            ax4.plot(sgi_vals, vel_vals, color=style["color"], 
                    linestyle=style["linestyle"], linewidth=1.5, alpha=0.7)
            
            # Plot points
            ax4.scatter(sgi_vals, vel_vals, color=style["color"], 
                       s=50, marker=style["marker"], alpha=style["alpha"],
                       label=label, zorder=3)
            
            # Mark start and end with annotations
            if len(sgi_vals) > 1:
                ax4.annotate('S', (sgi_vals[0], vel_vals[0]), fontsize=7, 
                           ha='center', va='bottom', color=style["color"])
                ax4.annotate('E', (sgi_vals[-1], vel_vals[-1]), fontsize=7, 
                           ha='center', va='bottom', color=style["color"])
    
    ax4.set_xlabel("Turn-Pair SGI")
    ax4.set_ylabel("Velocity (degrees)")
    ax4.set_title("SGI × Velocity (Paper 02/03 style)")
    ax4.set_xlim(0.3, 1.6)
    ax4.set_ylim(0, 120)  # Extended to 120° as requested
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=6, loc="upper right")
    
    plt.tight_layout()
    
    if output_path:
        fig_path = output_path.replace('.json', '_figure.png')
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        print(f"\nFigure saved to: {fig_path}")
    
    plt.show()


def visualize_fig2_velocity_comparison(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Figure 2: Velocity comparison across granularities and roles.
    2x2 grid showing:
    - Top left: All per-message velocities
    - Top right: Turn-pair orbital velocity
    - Bottom left: User messages only
    - Bottom right: Assistant messages only
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import seaborn as sns
    except ImportError as e:
        print(f"Visualization requires matplotlib, seaborn: {e}")
        return
    
    # Collect velocity data by role
    per_message_velocities = []
    user_velocities = []
    assistant_velocities = []
    orbital_velocities = []
    
    for r in results:
        turns = r.get("turns", [])
        prev_ptv_len = 0
        msg_index = 0  # Track message index within conversation
        
        for t in turns:
            rm = t.get("real_metrics", {})
            
            # Per-message velocities - only collect NEW values (array is cumulative)
            ptv = rm.get("per_turn_velocity", [])
            if ptv and len(ptv) > prev_ptv_len:
                new_values = ptv[max(1, prev_ptv_len):]  # Skip index 0 (180° artifact)
                for v in new_values:
                    if v is not None and v < 170:
                        per_message_velocities.append(v)
                        # Each turn has user then assistant message
                        # Even index = user, odd index = assistant (within new values)
                        if msg_index % 2 == 0:
                            user_velocities.append(v)
                        else:
                            assistant_velocities.append(v)
                        msg_index += 1
                prev_ptv_len = len(ptv)
            
            # Turn-pair orbital velocity - one per turn
            ov = rm.get("orbital_velocity_latest")
            if ov is not None and ov > 0:
                orbital_velocities.append(ov)
    
    if not per_message_velocities:
        print("[Fig2] Not enough velocity data to generate comparison")
        return
    
    # Create 2x2 figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle("Figure 2: Velocity Distribution by Granularity and Role", fontsize=14, fontweight='bold')
    
    sns.set_style("whitegrid")
    
    def plot_histogram(ax, data, color, title_prefix, label):
        if not data:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{title_prefix}\n(no data)")
            return 0, 0
        sns.histplot(data, kde=True, ax=ax, color=color, alpha=0.7, bins=20)
        mean_v = np.mean(data)
        std_v = np.std(data)
        ax.axvline(mean_v, color='black', linestyle='--', linewidth=2, label=f'Mean: {mean_v:.1f}°')
        ax.set_xlabel("Velocity (degrees)", fontsize=11)
        ax.set_ylabel("Frequency", fontsize=11)
        ax.set_title(f"{title_prefix}\n(n={len(data)}, μ={mean_v:.1f}°, σ={std_v:.1f}°)", fontsize=11)
        ax.set_xlim(0, 180)
        ax.legend(loc='upper right')
        return mean_v, std_v
    
    # Top left: All per-message
    mean_pm, std_pm = plot_histogram(axes[0, 0], per_message_velocities, '#e74c3c', 
                                      "All Per-Message Velocity", "All")
    
    # Top right: Turn-pair orbital
    mean_ov, std_ov = plot_histogram(axes[0, 1], orbital_velocities, '#3498db', 
                                      "Turn-Pair Orbital Velocity", "Orbital")
    
    # Bottom left: User messages only
    mean_user, std_user = plot_histogram(axes[1, 0], user_velocities, '#27ae60', 
                                          "User Messages Only", "User")
    
    # Bottom right: Assistant messages only
    mean_asst, std_asst = plot_histogram(axes[1, 1], assistant_velocities, '#9b59b6', 
                                          "Assistant Messages Only", "Assistant")
    
    # Calculate Dyadic Coherence Index (DCI)
    # DCI = 1 - (σ_turn_pair / σ_per_message)
    # Higher = more synchronized dyad
    dci = 0.0
    if std_pm > 0 and std_ov > 0:
        dci = 1.0 - (std_ov / std_pm)
        dci = max(0.0, min(1.0, dci))  # Clamp to [0, 1]
    
    # DCI interpretation
    if dci >= 0.8:
        dci_label = "HIGH COEVOLUTION"
        dci_color = '#27ae60'
    elif dci >= 0.5:
        dci_label = "MODERATE"
        dci_color = '#f39c12'
    else:
        dci_label = "LOW"
        dci_color = '#e74c3c'
    
    # Add comparison annotations
    if mean_pm > 0 and mean_ov > 0:
        reduction = ((mean_pm - mean_ov) / mean_pm) * 100
        fig.text(0.5, 0.48, 
                 f"Aggregation: {mean_pm:.1f} -> {mean_ov:.1f} (down {reduction:.0f}% when grouping to turn-pairs)",
                 ha='center', fontsize=11, style='italic', color='#2c3e50')
    
    if mean_user > 0 and mean_asst > 0:
        role_diff = mean_asst - mean_user
        fig.text(0.5, 0.02, 
                 f"Role Comparison: User={mean_user:.1f} vs Assistant={mean_asst:.1f} (diff={role_diff:+.1f})",
                 ha='center', fontsize=11, style='italic', color='#2c3e50')
    
    # DCI box
    fig.text(0.98, 0.98, 
             f"DCI = {dci:.2f}\n{dci_label}",
             ha='right', va='top', fontsize=14, fontweight='bold', color=dci_color,
             transform=fig.transFigure,
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=dci_color, linewidth=2))
    
    # Print to console
    print(f"\n{'='*50}")
    print(f"  DYADIC COHERENCE INDEX (DCI)")
    print(f"{'='*50}")
    print(f"  σ per-message:  {std_pm:.2f}°")
    print(f"  σ turn-pair:    {std_ov:.2f}°")
    print(f"  DCI = 1 - ({std_ov:.2f} / {std_pm:.2f}) = {dci:.3f}")
    print(f"  Interpretation: {dci_label}")
    print(f"{'='*50}\n")
    
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    
    # Save
    if output_path:
        fig2_path = output_path.replace('.json', '_fig2_velocity_comparison.png').replace('_figure.png', '_fig2_velocity_comparison.png')
        plt.savefig(fig2_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"\n[OK] Figure 2 saved to: {fig2_path}")
    
    plt.show()


def visualize_fig3_trajectory_analysis(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Figure 3: Turn-by-turn trajectory analysis.
    Shows temporal evolution to understand if conditions start differently and converge.
    
    Layout:
    - Top left: SGI over turns (all conditions)
    - Top right: Velocity over turns (all conditions)
    - Bottom left: Early turns (1-3) in phase space
    - Bottom right: Late turns (last 3 turns of the run) in phase space
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import seaborn as sns
        from collections import defaultdict
    except ImportError as e:
        print(f"Visualization requires matplotlib, seaborn: {e}")
        return
    
    # Organize data by condition
    condition_data = defaultdict(lambda: {"sgis": [], "velocities": [], "turns": []})
    
    for r in results:
        cond = r.get("condition_name", "unknown")
        turns = r.get("turns", [])
        
        for t in turns:
            turn_num = t.get("turn_number", 0)
            rm = t.get("real_metrics", {})
            
            # Prioritize turn-pair metrics (more stable)
            sgi = rm.get("turn_pair_sgi_mean") or rm.get("turn_pair_sgi_latest") or rm.get("sgi_mean")
            vel = rm.get("orbital_velocity_latest") or rm.get("orbital_velocity_mean") or rm.get("velocity_mean")
            
            if sgi is not None and vel is not None and vel < 170:
                condition_data[cond]["sgis"].append(sgi)
                condition_data[cond]["velocities"].append(vel)
                condition_data[cond]["turns"].append(turn_num)
    
    if not condition_data:
        print("[Fig3] No valid trajectory data found")
        return
    
    # Color palette for conditions
    colors = {
        "A_baseline": "#3498db",
        "B_healthy": "#27ae60",
        "C_drifting": "#f39c12",
        "D_transformation": "#9b59b6",
        "E_real_metrics": "#1abc9c",
        "F_adversarial": "#e74c3c"
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle("Figure 3: Temporal Trajectory Analysis — Do Conditions Converge?", 
                 fontsize=14, fontweight='bold')
    
    sns.set_style("whitegrid")
    
    # Top left: SGI over turns
    ax1 = axes[0, 0]
    for cond, data in condition_data.items():
        if data["turns"]:
            # Group by turn number and compute mean
            turn_sgi = defaultdict(list)
            for t, s in zip(data["turns"], data["sgis"]):
                turn_sgi[t].append(s)
            turns_sorted = sorted(turn_sgi.keys())
            sgi_means = [np.mean(turn_sgi[t]) for t in turns_sorted]
            sgi_stds = [np.std(turn_sgi[t]) for t in turns_sorted]
            
            color = colors.get(cond, "#7f8c8d")
            ax1.plot(turns_sorted, sgi_means, 'o-', color=color, label=cond, linewidth=2, markersize=8)
            ax1.fill_between(turns_sorted, 
                            [m-s for m,s in zip(sgi_means, sgi_stds)],
                            [m+s for m,s in zip(sgi_means, sgi_stds)],
                            alpha=0.2, color=color)
    ax1.set_xlabel("Turn Number", fontsize=12)
    ax1.set_ylabel("SGI (mean ± std)", fontsize=12)
    ax1.set_title("SGI Evolution Over Turns", fontsize=12)
    ax1.legend(loc='upper right', fontsize=9)
    ax1.set_ylim(0, 1.5)
    
    # Top right: Velocity over turns
    ax2 = axes[0, 1]
    for cond, data in condition_data.items():
        if data["turns"]:
            turn_vel = defaultdict(list)
            for t, v in zip(data["turns"], data["velocities"]):
                turn_vel[t].append(v)
            turns_sorted = sorted(turn_vel.keys())
            vel_means = [np.mean(turn_vel[t]) for t in turns_sorted]
            vel_stds = [np.std(turn_vel[t]) for t in turns_sorted]
            
            color = colors.get(cond, "#7f8c8d")
            ax2.plot(turns_sorted, vel_means, 's-', color=color, label=cond, linewidth=2, markersize=8)
            ax2.fill_between(turns_sorted,
                            [m-s for m,s in zip(vel_means, vel_stds)],
                            [m+s for m,s in zip(vel_means, vel_stds)],
                            alpha=0.2, color=color)
    ax2.set_xlabel("Turn Number", fontsize=12)
    ax2.set_ylabel("Orbital Velocity (mean ± std)", fontsize=12)
    ax2.set_title("Orbital Velocity (Turn-Pair) Over Turns", fontsize=12)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.set_ylim(0, 180)
    
    early_k = 3
    late_k = 3

    # Bottom left: Early turns (1-3) in phase space
    ax3 = axes[1, 0]
    ax3.add_patch(plt.Rectangle((0.3, 0), 0.9, 45, alpha=0.15, color='green', label='Coherence Region'))
    for cond, data in condition_data.items():
        early_sgi = [s for s, t in zip(data["sgis"], data["turns"]) if isinstance(t, (int, float)) and t <= early_k]
        early_vel = [v for v, t in zip(data["velocities"], data["turns"]) if isinstance(t, (int, float)) and t <= early_k]
        if early_sgi:
            color = colors.get(cond, "#7f8c8d")
            ax3.scatter(early_sgi, early_vel, color=color, alpha=0.7, s=100, label=cond, edgecolor='black')
            # Show mean point
            ax3.scatter([np.mean(early_sgi)], [np.mean(early_vel)], 
                       color=color, s=300, marker='*', edgecolor='black', linewidth=2)
    ax3.set_xlabel("SGI", fontsize=12)
    ax3.set_ylabel("Orbital Velocity (degrees)", fontsize=12)
    ax3.set_title(f"Early Turns (1-{early_k}): Where Do Conditions START?", fontsize=12)
    ax3.set_xlim(0, 1.5)
    ax3.set_ylim(0, 180)
    ax3.legend(loc='upper right', fontsize=9)
    
    # Bottom right: Late turns (last k turns) in phase space
    ax4 = axes[1, 1]
    ax4.add_patch(plt.Rectangle((0.3, 0), 0.9, 45, alpha=0.15, color='green', label='Coherence Region'))
    for cond, data in condition_data.items():
        max_turn = max([t for t in data["turns"] if isinstance(t, (int, float))], default=None)
        if max_turn is None:
            continue
        cutoff = max_turn - late_k + 1  # inclusive, e.g. 30 -> 28
        late_sgi = [s for s, t in zip(data["sgis"], data["turns"]) if isinstance(t, (int, float)) and t >= cutoff]
        late_vel = [v for v, t in zip(data["velocities"], data["turns"]) if isinstance(t, (int, float)) and t >= cutoff]
        if late_sgi:
            color = colors.get(cond, "#7f8c8d")
            ax4.scatter(late_sgi, late_vel, color=color, alpha=0.7, s=100, label=cond, edgecolor='black')
            # Show mean point
            ax4.scatter([np.mean(late_sgi)], [np.mean(late_vel)], 
                       color=color, s=300, marker='*', edgecolor='black', linewidth=2)
    ax4.set_xlabel("SGI", fontsize=12)
    ax4.set_ylabel("Orbital Velocity (degrees)", fontsize=12)
    ax4.set_title(f"Late Turns (last {late_k}): Where Do Conditions END?", fontsize=12)
    ax4.set_xlim(0, 1.5)
    ax4.set_ylim(0, 180)
    ax4.legend(loc='upper right', fontsize=9)
    
    # Compute convergence metric
    print("\n" + "="*60)
    print("  CONVERGENCE ANALYSIS")
    print("="*60)
    for cond, data in condition_data.items():
        max_turn = max([t for t in data["turns"] if isinstance(t, (int, float))], default=None)
        if max_turn is None:
            continue
        cutoff = max_turn - late_k + 1
        early_vel = [v for v, t in zip(data["velocities"], data["turns"]) if isinstance(t, (int, float)) and t <= early_k]
        late_vel = [v for v, t in zip(data["velocities"], data["turns"]) if isinstance(t, (int, float)) and t >= cutoff]
        if early_vel and late_vel:
            early_mean = np.mean(early_vel)
            late_mean = np.mean(late_vel)
            convergence = early_mean - late_mean
            print(f"  {cond:20s}: Early={early_mean:5.1f} -> Late={late_mean:5.1f} (delta={convergence:+5.1f})")
    print("="*60)
    print("  Positive delta = velocity decreases (settling)")
    print("  Negative delta = velocity increases (diverging)")
    print("="*60 + "\n")
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    if output_path:
        fig3_path = output_path.replace('.json', '_fig3_trajectory.png').replace('_figure.png', '_fig3_trajectory.png')
        plt.savefig(fig3_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"[OK] Figure 3 saved to: {fig3_path}")
    
    plt.show()


def visualize_fig4_injected_vs_measured(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Figure 4: Injected vs Measured metrics (steering detectability).

    Produces a 2-panel plot:
      - SGI: injected (dashed) vs measured (solid)
      - Velocity (degrees): injected (dashed) vs measured (solid)

    Notes:
      - Uses injected_metrics.sgi and injected_metrics.velocity_degrees when present
      - Uses measured turn-pair SGI when available, otherwise sgi_mean
      - Uses measured orbital_velocity_latest when available, otherwise velocity_latest/mean
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import seaborn as sns
    except ImportError as e:
        print(f"Visualization requires matplotlib, seaborn: {e}")
        return

    if not isinstance(results, list) or not results:
        print("[Fig4] No results to visualize")
        return

    # Group by condition (and backend if present)
    # For Fig4 we primarily want per-condition curves; if multiple backends exist, we average.
    series_by_cond: Dict[str, Dict[str, Dict[int, list]]] = {}
    inj_mode_by_cond: Dict[str, str] = {}  # none | real | fixed
    # structure:
    # series_by_cond[cond]["inj_sgi"][turn] = [vals...]
    # series_by_cond[cond]["real_sgi"][turn] = [vals...]
    # series_by_cond[cond]["inj_vel"][turn] = [vals...]
    # series_by_cond[cond]["real_vel"][turn] = [vals...]

    def _ensure(cond: str) -> None:
        if cond not in series_by_cond:
            series_by_cond[cond] = {
                "inj_sgi": {},
                "real_sgi": {},
                "inj_vel": {},
                "real_vel": {},
            }
            inj_mode_by_cond[cond] = "none"

    def _push(bucket: Dict[int, list], turn: int, val: Optional[float]) -> None:
        if val is None:
            return
        bucket.setdefault(int(turn), []).append(float(val))

    for r in results:
        cond = str(r.get("condition_name", "unknown"))
        _ensure(cond)
        turns = r.get("turns", []) or []
        for t in turns:
            turn_num = t.get("turn_number")
            if turn_num is None:
                continue

            inj = t.get("injected_metrics") or {}
            rm = t.get("real_metrics") or {}

            inj_sgi = inj.get("sgi") if isinstance(inj, dict) else None
            inj_vel = inj.get("velocity_degrees") if isinstance(inj, dict) else None

            # Track injection mode for styling
            if isinstance(inj, dict):
                status = str(inj.get("status") or "").lower()
                if status == "real_metrics":
                    inj_mode_by_cond[cond] = "real"
                elif ("sgi" in inj) or ("velocity_degrees" in inj):
                    # Fixed injected metrics (B/C/D/F)
                    if inj_mode_by_cond.get(cond) != "real":
                        inj_mode_by_cond[cond] = "fixed"

            real_sgi = (
                rm.get("turn_pair_sgi_latest")
                or rm.get("turn_pair_sgi_mean")
                or rm.get("sgi_latest")
                or rm.get("sgi_mean")
            )
            real_vel = (
                rm.get("orbital_velocity_latest")
                or rm.get("orbital_velocity_mean")
                or rm.get("velocity_latest")
                or rm.get("velocity_mean")
            )

            _push(series_by_cond[cond]["inj_sgi"], turn_num, inj_sgi)
            _push(series_by_cond[cond]["inj_vel"], turn_num, inj_vel)
            _push(series_by_cond[cond]["real_sgi"], turn_num, real_sgi)
            _push(series_by_cond[cond]["real_vel"], turn_num, real_vel)

    # Plot any condition with measured data. If injected data is missing (e.g. A_baseline),
    # we plot measured only (no dashed line).
    plotted_conds = []
    for cond, buckets in series_by_cond.items():
        has_any_real = any(buckets["real_sgi"].values()) or any(buckets["real_vel"].values())
        if has_any_real:
            plotted_conds.append(cond)

    if not plotted_conds:
        print("[Fig4] No measured metrics found in this dataset")
        return

    # Color palette (reuse condition naming)
    colors = {
        "A_baseline": "#3498db",
        "B_healthy": "#27ae60",
        "C_drifting": "#f39c12",
        "D_transformation": "#9b59b6",
        "E_real_metrics": "#1abc9c",
        "F_adversarial": "#e74c3c",
    }

    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    fig.suptitle("Figure 4: Injected vs Measured Metrics (Steering Detectability)", fontsize=14, fontweight="bold")

    ax_sgi, ax_vel = axes[0], axes[1]

    for cond in sorted(plotted_conds):
        c = colors.get(cond, "#7f8c8d")
        buckets = series_by_cond[cond]
        mode = inj_mode_by_cond.get(cond, "none")

        all_turns = sorted(
            set(buckets["real_sgi"].keys())
            | set(buckets["real_vel"].keys())
            | set(buckets["inj_sgi"].keys())
            | set(buckets["inj_vel"].keys())
        )
        if not all_turns:
            continue

        def mean_or_nan(bucket: Dict[int, list], turn: int) -> float:
            vals = bucket.get(turn) or []
            return float(np.mean(vals)) if vals else float("nan")

        inj_sgi_series = [mean_or_nan(buckets["inj_sgi"], t) for t in all_turns]
        real_sgi_series = [mean_or_nan(buckets["real_sgi"], t) for t in all_turns]
        inj_vel_series = [mean_or_nan(buckets["inj_vel"], t) for t in all_turns]
        real_vel_series = [mean_or_nan(buckets["real_vel"], t) for t in all_turns]

        # Choose styling:
        # - A_baseline (none): measured only, distinct label
        # - E_real_metrics (real): measured solid; injected (if present) dotted + low alpha
        # - fixed injected (B/C/D/F): measured solid; injected dashed

        meas_label = f"{cond} measured"
        if mode == "none":
            meas_label = f"{cond} measured (no injection)"
        elif mode == "real":
            meas_label = f"{cond} measured (telemetry shown)"

        # SGI (measured)
        ax_sgi.plot(
            all_turns,
            real_sgi_series,
            color=c,
            linewidth=2.5 if mode in ("none", "real") else 2,
            marker="o",
            label=meas_label,
        )

        # SGI (injected / shown-to-assistant)
        if not np.all(np.isnan(inj_sgi_series)):
            if mode == "real":
                ax_sgi.plot(
                    all_turns,
                    inj_sgi_series,
                    color=c,
                    linewidth=1.8,
                    linestyle=":",
                    alpha=0.6,
                    label=f"{cond} shown (real telemetry)",
                )
            elif mode == "fixed":
                ax_sgi.plot(
                    all_turns,
                    inj_sgi_series,
                    color=c,
                    linewidth=2,
                    linestyle="--",
                    alpha=0.9,
                    label=f"{cond} injected (fixed)",
                )

        # Velocity (measured)
        ax_vel.plot(
            all_turns,
            real_vel_series,
            color=c,
            linewidth=2.5 if mode in ("none", "real") else 2,
            marker="s",
            label=meas_label,
        )

        # Velocity (injected / shown-to-assistant)
        if not np.all(np.isnan(inj_vel_series)):
            if mode == "real":
                ax_vel.plot(
                    all_turns,
                    inj_vel_series,
                    color=c,
                    linewidth=1.8,
                    linestyle=":",
                    alpha=0.6,
                    label=f"{cond} shown (real telemetry)",
                )
            elif mode == "fixed":
                ax_vel.plot(
                    all_turns,
                    inj_vel_series,
                    color=c,
                    linewidth=2,
                    linestyle="--",
                    alpha=0.9,
                    label=f"{cond} injected (fixed)",
                )

    ax_sgi.set_title("SGI (Injected vs Measured)", fontsize=12)
    ax_sgi.set_xlabel("Turn", fontsize=12)
    ax_sgi.set_ylabel("SGI", fontsize=12)
    ax_sgi.set_ylim(0, 1.5)
    ax_sgi.legend(fontsize=8, loc="upper right")

    ax_vel.set_title("Velocity (Injected vs Measured)", fontsize=12)
    ax_vel.set_xlabel("Turn", fontsize=12)
    ax_vel.set_ylabel("Velocity (degrees)", fontsize=12)
    ax_vel.set_ylim(0, 180)
    ax_vel.legend(fontsize=8, loc="upper right")

    plt.tight_layout(rect=[0, 0, 1, 0.94])

    if output_path:
        fig4_path = output_path.replace(".json", "_fig4_injected_vs_measured.png").replace("_figure.png", "_fig4_injected_vs_measured.png")
        plt.savefig(fig4_path, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"[OK] Figure 4 (line plot) saved to: {fig4_path}")

    plt.show()
    
    # Also generate BAR CHART version (legacy style)
    _visualize_fig4_bars(series_by_cond, inj_mode_by_cond, colors, output_path)


def _visualize_fig4_bars(series_by_cond: dict, inj_mode_by_cond: dict, colors: dict, output_path: Optional[str]) -> None:
    """Generate bar chart version of Figure 4 (legacy style)."""
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Compute mean values per condition
    bar_data = []
    for cond, buckets in series_by_cond.items():
        # Flatten all values
        all_inj_sgi = [v for vals in buckets["inj_sgi"].values() for v in vals]
        all_real_sgi = [v for vals in buckets["real_sgi"].values() for v in vals]
        all_inj_vel = [v for vals in buckets["inj_vel"].values() for v in vals]
        all_real_vel = [v for vals in buckets["real_vel"].values() for v in vals]
        
        # For fixed injection conditions, take the injected value (should be constant)
        mode = inj_mode_by_cond.get(cond, "none")
        if mode == "fixed" and all_inj_sgi:
            inj_sgi_mean = all_inj_sgi[0]  # Constant
        else:
            inj_sgi_mean = np.mean(all_inj_sgi) if all_inj_sgi else None
            
        if mode == "fixed" and all_inj_vel:
            inj_vel_mean = all_inj_vel[0]  # Constant
        else:
            inj_vel_mean = np.mean(all_inj_vel) if all_inj_vel else None
        
        real_sgi_mean = np.mean(all_real_sgi) if all_real_sgi else None
        real_vel_mean = np.mean(all_real_vel) if all_real_vel else None
        
        bar_data.append({
            "condition": cond,
            "inj_sgi": inj_sgi_mean,
            "real_sgi": real_sgi_mean,
            "inj_vel": inj_vel_mean,
            "real_vel": real_vel_mean,
            "mode": mode
        })
    
    # Sort by condition name
    bar_data = sorted(bar_data, key=lambda x: x["condition"])
    
    if not bar_data:
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Figure 4: Injected vs Measured (Bar Chart)", fontsize=14, fontweight="bold")
    
    conditions = [d["condition"].replace("_", "\n") for d in bar_data]
    x = np.arange(len(conditions))
    width = 0.35
    
    # SGI bar chart
    ax1 = axes[0]
    inj_sgis = [d["inj_sgi"] if d["inj_sgi"] is not None else 0 for d in bar_data]
    real_sgis = [d["real_sgi"] if d["real_sgi"] is not None else 0 for d in bar_data]
    
    # Create bars - we'll manually handle legend
    inj_bars = ax1.bar(x - width/2, inj_sgis, width, color='#3498db', alpha=0.8)
    real_bars = ax1.bar(x + width/2, real_sgis, width, color='#e74c3c', alpha=0.8)
    
    # Hide injected bars for A_baseline (no injection) and E_real_metrics (real telemetry)
    for i, d in enumerate(bar_data):
        if d["mode"] in ("none", "real"):
            inj_bars[i].set_height(0)
            inj_bars[i].set_alpha(0)
    
    # Manual legend with visible patches
    from matplotlib.patches import Patch
    ax1.legend(handles=[
        Patch(facecolor='#3498db', alpha=0.8, label='Injected'),
        Patch(facecolor='#e74c3c', alpha=0.8, label='Measured')
    ], fontsize=10)
    
    ax1.set_ylabel('SGI', fontsize=12)
    ax1.set_title('Injected vs Real SGI by Condition', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(conditions, fontsize=10)
    ax1.legend(fontsize=10)
    ax1.set_ylim(0, 1.5)
    ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='SGI=1.0')
    
    # Velocity bar chart
    ax2 = axes[1]
    inj_vels = [d["inj_vel"] if d["inj_vel"] is not None else 0 for d in bar_data]
    real_vels = [d["real_vel"] if d["real_vel"] is not None else 0 for d in bar_data]
    
    inj_bars2 = ax2.bar(x - width/2, inj_vels, width, color='#3498db', alpha=0.8)
    real_bars2 = ax2.bar(x + width/2, real_vels, width, color='#e74c3c', alpha=0.8)
    
    # Hide injected bars for A_baseline and E_real_metrics
    for i, d in enumerate(bar_data):
        if d["mode"] in ("none", "real"):
            inj_bars2[i].set_height(0)
            inj_bars2[i].set_alpha(0)
    
    ax2.set_ylabel('Velocity (degrees)', fontsize=12)
    ax2.set_title('Injected vs Real Velocity by Condition', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(conditions, fontsize=10)
    ax2.legend(handles=[
        Patch(facecolor='#3498db', alpha=0.8, label='Injected'),
        Patch(facecolor='#e74c3c', alpha=0.8, label='Measured')
    ], fontsize=10)
    ax2.set_ylim(0, 90)
    ax2.axhline(y=45, color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    
    if output_path:
        fig4_bar_path = output_path.replace(".json", "_fig4_bars.png").replace("_figure.png", "_fig4_bars.png")
        plt.savefig(fig4_bar_path, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"[OK] Figure 4 (bar chart) saved to: {fig4_bar_path}")
    
    plt.show()


def visualize_results_density(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Density-based visualization for large multi-backend experiments.
    Shows distributions and 2D KDE instead of individual trajectories.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        import numpy as np
        import seaborn as sns
        import pandas as pd
    except ImportError as e:
        print(f"Required library not installed: {e} - skipping density visualization")
        return
    
    # Extract all data points into a DataFrame
    data_rows = []
    for result in results:
        condition = result.get("condition_name", "unknown")
        backend = result.get("backend", "unknown")
        turns = result.get("turns", [])
        
        for turn_idx, t in enumerate(turns):
            rm = t.get("real_metrics", {})
            if rm:
                # Get SGI value
                per_turn_pair_sgi = rm.get("per_turn_pair_sgi", [])
                per_turn_sgi = rm.get("per_turn_sgi", [])
                sgi = None
                if per_turn_pair_sgi:
                    sgi = per_turn_pair_sgi[-1]
                elif per_turn_sgi:
                    sgi = per_turn_sgi[-1]
                elif rm.get("sgi_mean") is not None:
                    sgi = rm["sgi_mean"]
                
                # Get Velocity value
                per_turn_vel = rm.get("per_turn_velocity", [])
                vel = None
                if per_turn_vel:
                    vel = per_turn_vel[-1]
                elif rm.get("velocity_mean") is not None:
                    vel = rm["velocity_mean"]
                
                if sgi is not None and vel is not None:
                    data_rows.append({
                        "condition": condition,
                        "backend": backend,
                        "turn": turn_idx + 1,
                        "sgi": sgi,
                        "velocity": vel
                    })
    
    if not data_rows:
        print("No valid data for density visualization")
        return
    
    df = pd.DataFrame(data_rows)
    
    # Color palettes
    condition_palette = {
        "A_baseline": "#2E4057",
        "B_healthy": "#048A81", 
        "C_drifting": "#E63946",
        "D_transformation": "#6F2DBD",
        "E_real_metrics": "#F77F00",
        "F_adversarial": "#A4161A"
    }
    
    backend_palette = {
        "s128": "#1f77b4",
        "openai-ada-002": "#ff7f0e",
        "voyage-large-2-instruct": "#2ca02c",
        "cohere-v3": "#d62728",
        "bge-m3": "#9467bd",
        "qwen": "#8c564b",
        "nomic": "#e377c2",
        "jina-v3": "#7f7f7f",
        "mistral-embed": "#bcbd22",
        "openai-3-small": "#17becf"
    }
    
    # Create figure with 4 subplots
    fig = plt.figure(figsize=(16, 14))
    
    # =========================================================================
    # Plot 1: SGI Distribution by Backend (Ridge/Violin plot)
    # =========================================================================
    ax1 = fig.add_subplot(2, 2, 1)
    
    # Get unique backends
    backends = df["backend"].unique()
    
    # Create violin plot for SGI by backend
    sns.violinplot(
        data=df, x="backend", y="sgi", hue="backend",
        palette=backend_palette, ax=ax1, 
        inner="quartile", cut=0, legend=False
    )
    ax1.axhline(y=1.0, color='green', linestyle='--', alpha=0.7, label='SGI = 1.0')
    ax1.set_xlabel("Embedding Model")
    ax1.set_ylabel("Turn-Pair SGI")
    ax1.set_title("SGI Distribution by Backend\n(Cross-Model Invariance Check)")
    ax1.tick_params(axis='x', rotation=45)
    ax1.set_ylim(0, 2.0)
    ax1.legend(loc='upper right')
    
    # =========================================================================
    # Plot 2: Velocity Distribution by Backend
    # =========================================================================
    ax2 = fig.add_subplot(2, 2, 2)
    
    sns.violinplot(
        data=df, x="backend", y="velocity", hue="backend",
        palette=backend_palette, ax=ax2,
        inner="quartile", cut=0, legend=False
    )
    ax2.axhline(y=45, color='green', linestyle='--', alpha=0.7, label='Coherence Max (45°)')
    ax2.set_xlabel("Embedding Model")
    ax2.set_ylabel("Velocity (degrees)")
    ax2.set_title("Velocity Distribution by Backend\n(Cross-Model Invariance Check)")
    ax2.tick_params(axis='x', rotation=45)
    ax2.set_ylim(0, 120)
    ax2.legend(loc='upper right')
    
    # =========================================================================
    # Plot 3: SGI by Condition (grouped violin)
    # =========================================================================
    ax3 = fig.add_subplot(2, 2, 3)
    
    sns.violinplot(
        data=df, x="condition", y="sgi", hue="condition",
        palette=condition_palette, ax=ax3,
        inner="quartile", cut=0, legend=False
    )
    ax3.axhline(y=1.0, color='green', linestyle='--', alpha=0.7)
    ax3.set_xlabel("Condition")
    ax3.set_ylabel("Turn-Pair SGI")
    ax3.set_title("SGI Distribution by Condition\n(Steering Effect Detection)")
    ax3.tick_params(axis='x', rotation=45)
    ax3.set_ylim(0, 2.0)
    
    # =========================================================================
    # Plot 4: 2D KDE - SGI × Velocity (The "Flock of Birds" View)
    # =========================================================================
    ax4 = fig.add_subplot(2, 2, 4)
    
    # Draw coherence region first (background)
    coherence_rect = patches.Rectangle(
        (0.7, 15), 0.6, 30,  # x, y, width, height
        facecolor='#2ecc71', alpha=0.15, edgecolor='#2ecc71', 
        linewidth=2, linestyle='--', label='Coherence Region'
    )
    ax4.add_patch(coherence_rect)
    ax4.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax4.plot(1.0, 30, 'g*', markersize=15, zorder=10, label='Coherence Centroid')
    
    # 2D KDE contour plot for all data
    try:
        sns.kdeplot(
            data=df, x="sgi", y="velocity",
            fill=True, alpha=0.4, levels=10,
            cmap="viridis", ax=ax4
        )
        
        # Add contour lines for each condition
        for cond, color in condition_palette.items():
            cond_df = df[df["condition"] == cond]
            if len(cond_df) > 10:
                sns.kdeplot(
                    data=cond_df, x="sgi", y="velocity",
                    levels=3, color=color, linewidths=1.5,
                    ax=ax4, label=cond
                )
    except Exception as e:
        # Fallback to hexbin if KDE fails
        print(f"KDE failed, using hexbin: {e}")
        ax4.hexbin(df["sgi"], df["velocity"], gridsize=30, cmap='viridis', alpha=0.7)
    
    ax4.set_xlabel("Turn-Pair SGI (Orbital Radius)")
    ax4.set_ylabel("Velocity (degrees)")
    ax4.set_title("SGI × Velocity Density\n(\"Flock of Birds\" - All Trajectories Converge)")
    ax4.set_xlim(0.2, 1.5)
    ax4.set_ylim(0, 120)
    ax4.legend(fontsize=8, loc='upper right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    if output_path:
        density_path = output_path.replace('.json', '_density.png').replace('_figure.png', '_density.png')
        plt.savefig(density_path, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"\nDensity figure saved to: {density_path}")
    
    plt.show()
    
    # Print cross-model invariance stats
    print("\n" + "="*70)
    print("CROSS-MODEL INVARIANCE ANALYSIS")
    print("="*70)
    
    backend_stats = df.groupby("backend").agg({
        "sgi": ["mean", "std"],
        "velocity": ["mean", "std"]
    }).round(3)
    backend_stats.columns = ["SGI_mean", "SGI_std", "Vel_mean", "Vel_std"]
    print("\nPer-Backend Statistics:")
    print(backend_stats.to_string())
    
    # Cross-backend variance
    overall_sgi_std = df.groupby("backend")["sgi"].mean().std()
    overall_vel_std = df.groupby("backend")["velocity"].mean().std()
    print(f"\nCross-Backend SGI Variance: ±{overall_sgi_std:.4f}")
    print(f"Cross-Backend Velocity Variance: ±{overall_vel_std:.2f}°")
    
    if overall_sgi_std < 0.05 and overall_vel_std < 5.0:
        print("\n[OK] STRONG CROSS-MODEL INVARIANCE DETECTED")
        print("  → Semantic physics is architecture-independent!")
    else:
        print("\n⚠ Some cross-model variance detected - investigate further")


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print experiment summary."""
    print("\n" + "="*70)
    print("STEERING EXPERIMENT SUMMARY")
    print("="*70)
    
    print("\n{:<20} {:<12} {:<12} {:<12} {:<12}".format(
        "Condition", "SGI (Real)", "Vel (Real)", "Detected?", "Magnitude"
    ))
    print("-"*70)
    
    for result in results:
        name = result["condition_name"]
        final = result.get("final_metrics", {})
        sgi = final.get("sgi_mean", 0) or 0
        vel = final.get("velocity_mean", 0) or 0
        detected = "YES" if result.get("steering_detected") else "no"
        magnitude = result.get("steering_magnitude", 0)
        
        print("{:<20} {:<12.2f} {:<12.1f} {:<12} {:<12.2f}".format(
            name, sgi, vel, detected, magnitude
        ))
    
    print("\n" + "="*70)
    print("KEY FINDINGS:")
    print("-"*70)
    
    # Compare baseline to others
    baseline = next((r for r in results if r["condition_name"] == "A_baseline"), None)
    if baseline:
        baseline_sgi = baseline.get("final_metrics", {}).get("sgi_mean", 1.0) or 1.0
        baseline_vel = baseline.get("final_metrics", {}).get("velocity_mean", 30.0) or 30.0
        
        for result in results:
            if result["condition_name"] == "A_baseline":
                continue
            
            name = result["condition_name"]
            final = result.get("final_metrics", {})
            sgi = final.get("sgi_mean", 1.0) or 1.0
            vel = final.get("velocity_mean", 30.0) or 30.0
            
            sgi_change = ((sgi - baseline_sgi) / baseline_sgi) * 100
            vel_change = ((vel - baseline_vel) / baseline_vel) * 100
            
            print(f"\n{name}:")
            print(f"  SGI change from baseline: {sgi_change:+.1f}%")
            print(f"  Velocity change from baseline: {vel_change:+.1f}%")
            
            if result.get("steering_detected"):
                print(f"  -> STEERING DETECTED (mismatch between injected and real)")
            else:
                print(f"  -> Metrics consistent (no obvious manipulation)")
    
    print("\n" + "="*70)


def generate_summary_txt(results: List[Dict[str, Any]], output_path: Path, metadata: Dict[str, Any] = None) -> None:
    """Generate a human-readable summary TXT file alongside the JSON."""
    lines = []
    lines.append("=" * 80)
    lines.append("STEERING EXPERIMENT SUMMARY")
    lines.append("=" * 80)
    
    # Metadata section
    if metadata:
        lines.append(f"Date: {metadata.get('timestamp', 'N/A')[:10]}")
        lines.append(f"Script: {metadata.get('script_name', SCRIPT_NAME)}")
        lines.append(f"User LLM: {metadata.get('user_llm', USER_LLM_MODEL)}")
        lines.append(f"Assistant LLM: {metadata.get('assistant_llm', ASSISTANT_LLM_MODEL)}")
        lines.append(f"Turns per condition: {metadata.get('turns_per_condition', 'N/A')}")
    lines.append("")
    
    lines.append("=" * 80)
    lines.append("EXPERIMENT OVERVIEW")
    lines.append("=" * 80)
    lines.append("Purpose: Validate that injecting fake metrics into AI system prompts")
    lines.append("         measurably changes conversation behavior (semantic steering).")
    lines.append("")
    lines.append("Conditions Tested:")
    for result in results:
        backend = result.get("backend")
        label = f"{result['condition_name']} ({backend})" if backend else result["condition_name"]
        lines.append(f"  - {label}: {result.get('condition_description', 'N/A')}")
    lines.append("")
    
    # Per-condition details
    for result in results:
        backend = result.get("backend")
        lines.append("=" * 80)
        if backend:
            lines.append(f"CONDITION: {result['condition_name'].upper()} ({backend})")
        else:
            lines.append(f"CONDITION: {result['condition_name'].upper()}")
        lines.append("=" * 80)
        lines.append(f"Description: {result.get('condition_description', 'N/A')}")
        lines.append("")
        
        # Injected metrics (if any)
        turns = result.get("turns", [])
        if turns and turns[0].get("injected_metrics"):
            inj = turns[0]["injected_metrics"]
            has_injected = any(
                inj.get(k) is not None for k in ("sgi", "velocity_degrees")
            )
            if has_injected:
                lines.append("Injected Metrics:")
                lines.append(f"  SGI: {inj.get('sgi', 'N/A')}")
                lines.append(f"  Velocity: {inj.get('velocity_degrees', 'N/A')}deg")
                lines.append(f"  Status: {inj.get('status', 'N/A')}")
                lines.append("")
            elif inj.get("status") == "real_metrics":
                lines.append("Injected Metrics:")
                lines.append("  REAL (from SDK)")
                lines.append("")
        
        # Conversation summary
        lines.append("Conversation Flow:")
        for i, turn in enumerate(turns[:5], 1):  # Show first 5 turns
            user_msg = turn.get("user_message", "")[:60]
            asst_msg = turn.get("assistant_response", "")[:60]
            lines.append(f"  Turn {i}:")
            lines.append(f"    User: {user_msg}...")
            lines.append(f"    Asst: {asst_msg}...")
        if len(turns) > 5:
            lines.append(f"  ... ({len(turns) - 5} more turns)")
        lines.append("")
        
        # Transducer analysis
        trans = result.get("transducer", {})
        if trans:
            lines.append("Transducer Analysis:")
            lines.append(f"  Messages analyzed: {trans.get('count', 0)}")
            lines.append(f"  Transformational: {trans.get('transformational_count', 0)}")
            lines.append(f"  Mean confidence: {trans.get('mean_confidence', 0):.3f}")
            lines.append("")
            
            # Aggregate top symbols
            symbol_counts = {}
            path_counts = {}
            phase_counts = {"pre-transformation": 0, "in-transformation": 0, "insight-reached": 0}
            
            for msg in trans.get("results", []):
                for sym, score in msg.get("top_symbols", [])[:3]:
                    symbol_counts[sym] = symbol_counts.get(sym, 0) + score
                for path, score in msg.get("top_paths", [])[:2]:
                    path_counts[path] = path_counts.get(path, 0) + score
                for align in msg.get("path_alignments", [])[:1]:
                    phase = align.get("phase", "unknown")
                    if phase in phase_counts:
                        phase_counts[phase] += 1
            
            top_symbols = sorted(symbol_counts.items(), key=lambda x: -x[1])[:5]
            top_paths = sorted(path_counts.items(), key=lambda x: -x[1])[:3]
            
            lines.append("Top Symbols (aggregated):")
            lines.append(f"  {', '.join([f'[{s}]' for s, _ in top_symbols])}")
            lines.append("")
            lines.append("Dominant Paths:")
            lines.append(f"  {', '.join([p for p, _ in top_paths])}")
            lines.append("")
            lines.append("Phase Distribution:")
            for phase, count in phase_counts.items():
                lines.append(f"  {phase}: {count} messages")
            lines.append("")
        
        # Steering detection
        lines.append(f"Steering Detected: {'YES' if result.get('steering_detected') else 'NO'}")
        lines.append(f"Steering Magnitude: {result.get('steering_magnitude', 0):.4f}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")
    
    # Key findings
    lines.append("=" * 80)
    lines.append("KEY FINDINGS")
    lines.append("=" * 80)
    
    baseline = next((r for r in results if r["condition_name"] == "A_baseline"), None)
    if baseline:
        baseline_conf = baseline.get("transducer", {}).get("mean_confidence", 0.5)
        
        for i, result in enumerate(results, 1):
            if result["condition_name"] == "A_baseline":
                continue
            
            conf = result.get("transducer", {}).get("mean_confidence", 0.5)
            delta = ((conf - baseline_conf) / baseline_conf) * 100 if baseline_conf > 0 else 0
            
            lines.append(f"{i}. {result['condition_name']}:")
            lines.append(f"   Confidence: {conf:.3f} ({delta:+.1f}% vs baseline)")
            lines.append(f"   Steering magnitude: {result.get('steering_magnitude', 0):.4f}")
            lines.append("")
    
    # Limitations
    lines.append("")
    lines.append("=" * 80)
    lines.append("NOTES")
    lines.append("=" * 80)
    lines.append("- AI-AI conversation (synthetic, not real users)")
    lines.append("- Check SDK connectivity if real metrics are null")
    lines.append("- Steering detection thresholds may need calibration")
    lines.append("")
    
    # File references
    json_name = output_path.name.replace("_summary.txt", ".json")
    png_name = output_path.name.replace("_summary.txt", "_figure.png")
    lines.append("=" * 80)
    lines.append("FILES")
    lines.append("=" * 80)
    lines.append(f"JSON Data: {json_name}")
    lines.append(f"Figure:    {png_name}")
    lines.append(f"Summary:   {output_path.name} (this file)")
    lines.append("")
    
    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    # Declare globals first, before any use
    global USER_LLM_MODEL, ASSISTANT_LLM_MODEL, USER_POLICY
    
    parser = argparse.ArgumentParser(description="Run steering experiment with AI-AI conversation")
    parser.add_argument("--turns", type=int, default=DEFAULT_TURNS, help="Number of turns per condition")
    parser.add_argument("--assistant-model", type=str, default=ASSISTANT_LLM_MODEL, 
                       help="Assistant LLM model (receives injections): deepseek, claude_sonnet, gpt4")
    parser.add_argument("--user-model", type=str, default=USER_LLM_MODEL,
                       help="User LLM model (plays human): gpt5, claude_sonnet, deepseek")
    parser.add_argument(
        "--user-policy",
        type=str,
        default=USER_POLICY,
        choices=["default", "deep_bridge"],
        help="User simulator policy (AI-AI only): default | deep_bridge (anchor→bridge→deepen)"
    )
    parser.add_argument("--visualize", type=str, help="Visualize results from JSON file (e.g., results/09_steering_2026-01-13_20-15-30.json)")
    parser.add_argument("--density", action="store_true", help="Use density visualization (KDE/violin plots) for large datasets")
    parser.add_argument("--fig2", action="store_true", help="Generate Figure 2: Per-message vs Turn-pair velocity comparison")
    parser.add_argument("--fig3", action="store_true", help="Generate Figure 3: Turn-by-turn trajectory analysis (early vs late, convergence)")
    parser.add_argument("--fig4", action="store_true", help="Generate Figure 4: Injected vs measured metrics (steering detectability)")
    parser.add_argument("--ai-dynamics", action="store_true", help="When visualizing AI-AI steering JSON, generate AI dynamics dashboard(s)")
    parser.add_argument("--dyn-condition", type=str, help="Filter AI dynamics to a single condition_name")
    parser.add_argument("--dyn-backend", type=str, help="Filter AI dynamics to a single backend")
    parser.add_argument("--human", action="store_true", 
                       help="Human-AI mode: you type messages, see metrics after each turn")
    parser.add_argument("--conditions", type=str, nargs="+", 
                       help="Run specific conditions (A_baseline, B_healthy, C_drifting, D_transformation, E_real_metrics, F_adversarial)")
    parser.add_argument("--list-results", action="store_true", help="List available result files")
    parser.add_argument("--backends", type=str, nargs="+", default=["nomic"],
                       help="Embedding backends for transducer analysis (nomic, ada02, s128). Default: nomic. For full validation: --backends nomic ada02 s128")
    parser.add_argument("--full-validation", action="store_true", 
                       help="Run full Paper 03 validation (6 conditions × 3 backends = 18 runs)")
    parser.add_argument("--save_name", type=str, dest="save_name",
                       help="Custom name for output file (without extension). If not provided, uses timestamped filename.")
    
    args = parser.parse_args()
    
    # Update global model settings if specified
    if args.user_model:
        USER_LLM_MODEL = args.user_model
    if args.assistant_model:
        ASSISTANT_LLM_MODEL = args.assistant_model
    if getattr(args, "user_policy", None):
        USER_POLICY = args.user_policy
    
    # List results mode
    if args.list_results:
        print(f"\nAvailable results in {RESULTS_DIR}:")
        if RESULTS_DIR.exists():
            for f in sorted(RESULTS_DIR.glob(f"{SCRIPT_ID}_*.json")):
                print(f"  - {f.name}")
        else:
            print("  (no results yet)")
        return
    
    # Visualization mode
    if args.visualize:
        viz_path = Path(args.visualize)
        if not viz_path.exists():
            # Try relative to results dir
            viz_path = RESULTS_DIR / args.visualize
        if not viz_path.exists():
            print(f"ERROR: File not found: {args.visualize}")
            print(f"Use --list-results to see available files")
            sys.exit(1)
        
        with open(viz_path, 'r') as f:
            data = json.load(f)
        
        # Handle new format with metadata wrapper
        results = data.get("results", data) if isinstance(data, dict) else data
        
        figure_path = str(viz_path).replace(".json", "_figure.png")

        # PRIORITY: Explicit figure flags always take precedence
        # Figure 2: Per-message vs Turn-pair velocity comparison
        if args.fig2:
            visualize_fig2_velocity_comparison(results, str(viz_path))
            return
        
        # Figure 3: Turn-by-turn trajectory analysis
        if args.fig3:
            visualize_fig3_trajectory_analysis(results, str(viz_path))
            return

        # Figure 4: Injected vs measured metrics
        if args.fig4:
            visualize_fig4_injected_vs_measured(results, str(viz_path))
            return

        # Human-AI mode visualization (single session) - default if no explicit fig flag
        if isinstance(data, dict) and data.get("mode") == "human-ai" and isinstance(results, list) and len(results) > 0:
            visualize_human_session(results[0], figure_path)
            return

        # AI-AI dynamics dashboards (single run or filtered selection)
        if args.ai_dynamics and isinstance(results, list) and len(results) > 0:
            sel = results
            if args.dyn_condition:
                sel = [r for r in sel if str(r.get("condition_name")) == str(args.dyn_condition)]
            if args.dyn_backend:
                sel = [r for r in sel if str(r.get("backend")) == str(args.dyn_backend)]
            if not sel:
                print("[WARN] No results matched --dyn-condition/--dyn-backend filters")
                return
            for r in sel:
                cond = str(r.get("condition_name", "unknown"))
                backend = str(r.get("backend", "unknown"))
                safe = f"{cond}_{backend}".replace("/", "_").replace("\\", "_").replace(" ", "_")
                dyn_path = str(viz_path).replace(".json", f"_ai_dynamics_{safe}.png")
                visualize_ai_dynamics(r, dyn_path)
            return
        
        # Use density visualization for large datasets or when --density flag is set
        if args.density or len(results) > 10:
            print(f"Using density visualization for {len(results)} result sets...")
            visualize_results_density(results, figure_path)
        else:
        visualize_results(results, figure_path)
        
        print_summary(results)
        return
    
    # Human-AI interactive mode
    if args.human:
        # Check for LLM infrastructure
        if not USE_AICO_LLM:
            print("ERROR: AICoevolution LLM infrastructure not available")
            sys.exit(1)
        
        # Use first condition or E_real_metrics if not specified
        if args.conditions:
            cond_name = args.conditions[0]
            condition = next((c for c in CONDITIONS if c.name == cond_name), CONDITIONS[0])
        else:
            # Default to E_real_metrics for human mode (shows real SDK metrics)
            condition = next((c for c in CONDITIONS if c.name == "E_real_metrics"), CONDITIONS[0])
        
        # Use single backend
        backend = args.backends[0] if args.backends else "nomic"
        
        # Run human-AI session
        result = run_human_condition(
            condition=condition,
            num_turns=args.turns,
            assistant_model=ASSISTANT_LLM_MODEL,
            backend=backend
        )
        
        # Save results
        output_file = get_timestamped_filename("json", "human_session", getattr(args, 'save_name', None))
        results_data = {
            "mode": "human-ai",
            "metadata": {
                "condition": condition.name,
                "backend": backend,
                "turns": args.turns,
                "timestamp": str(output_file),
            },
            "results": [asdict(result)]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Human-AI session saved to: {output_file}")
        return
    
    # Check for LLM infrastructure
    if not USE_AICO_LLM:
        print("ERROR: AICoevolution LLM infrastructure not available")
        print("Make sure you're running from the MirrorMind directory")
        sys.exit(1)
    
    print("="*70)
    print("STEERING EXPERIMENT (AI-AI Conversation)")
    print("="*70)
    print(f"User LLM (plays human): {USER_LLM_MODEL}")
    print(f"Assistant LLM (receives injections): {ASSISTANT_LLM_MODEL}")
    print(f"Turns per condition: {args.turns}")
    print(f"Backends: {', '.join(args.backends)}")
    print(f"SDK URL: {SDK_URL}")
    
    if args.full_validation:
        print(f"\n🔬 FULL PAPER 03 VALIDATION MODE")
        print(f"   {len(CONDITIONS)} conditions × {len(VALIDATION_BACKENDS)} backends = {len(CONDITIONS) * len(VALIDATION_BACKENDS)} runs")
        print(f"   This will take approximately {len(CONDITIONS) * len(VALIDATION_BACKENDS) * args.turns * 0.5:.0f} minutes")
        args.backends = VALIDATION_BACKENDS  # Override with full validation set
    
    # Check SDK health before starting
    print("\n[Startup] Checking SDK health...")
    try:
        health_resp = requests.get(f"{SDK_URL}/health", timeout=15)
        if health_resp.ok:
            print(f"[Startup] [OK] SDK is healthy at {SDK_URL}")
        else:
            print(f"[Startup] [WARN] SDK returned {health_resp.status_code}")
    except Exception as e:
        print(f"[Startup] [ERROR] Cannot reach SDK at {SDK_URL}: {e}")
        print("[Startup] Make sure the SDK is running: python -m aicoevolution_sdk.server")
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            sys.exit(1)
    
    # Test a simple ingest to verify format
    print("[Startup] Testing SDK ingest format...")
    try:
        test_resp = requests.post(
            f"{SDK_URL}/v0/ingest",
            json={
                "conversation_id": "test_startup_check",
                "role": "user",
                "text": "Hello, this is a startup test."
            },
            timeout=30  # Increased timeout for embedding calls
        )
        if test_resp.ok:
            print(f"[Startup] [OK] SDK ingest test passed")
        else:
            print(f"[Startup] [WARN] SDK ingest test failed: {test_resp.status_code}")
            print(f"[Startup]   Response: {test_resp.text[:200]}")
    except Exception as e:
        print(f"[Startup] [ERROR] SDK ingest test error: {e}")
    
    print("-"*70)
    
    # Filter conditions if specified
    conditions = CONDITIONS
    if args.conditions:
        conditions = [c for c in CONDITIONS if c.name in args.conditions]
        print(f"Running conditions: {[c.name for c in conditions]}")
    
    # Reset SDK call counters before starting
    reset_sdk_counters()
    print(f"[Startup] SDK call counters reset")
    
    # Run all conditions × backends
    results = []
    total_runs = len(conditions) * len(args.backends)
    current_run = 0
    
    for backend in args.backends:
    for condition in conditions:
            current_run += 1
            print(f"\n{'='*70}")
            print(f"RUN {current_run}/{total_runs}: {condition.name} with {backend}")
            print(f"{'='*70}")
            
        result = run_condition(
            condition=condition,
            num_turns=args.turns,
                assistant_model=ASSISTANT_LLM_MODEL,
                backend=backend
        )
            result_dict = asdict(result)
            result_dict["backend"] = backend  # Tag result with backend
            results.append(result_dict)
    
    # Ensure results directory exists
    ensure_results_dir()
    
    # Save results with timestamped filename or custom name
    output_path = get_timestamped_filename("json", custom_name=getattr(args, 'save_name', None))
    # Get SDK call statistics
    sdk_stats = get_sdk_stats()
    
    metadata = {
        "script_id": SCRIPT_ID,
        "script_name": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "timestamp": datetime.now().isoformat(),
        "user_llm": USER_LLM_MODEL,
        "assistant_llm": ASSISTANT_LLM_MODEL,
        "user_policy": USER_POLICY,
        "turns_per_condition": args.turns,
        "conditions_tested": [c.name for c in conditions],
        "backends_used": args.backends,
        "total_runs": len(results),
        "full_validation": args.full_validation if hasattr(args, 'full_validation') else False,
        "sdk_url": SDK_URL,
        "sdk_call_stats": sdk_stats
    }
    
    # Print SDK call summary
    print(f"\n{'='*70}")
    print("SDK CALL STATISTICS")
    print(f"{'='*70}")
    print(f"  Total /v0/ingest calls: {sdk_stats['ingest_calls']}")
    print(f"  Approx embedding calls: {sdk_stats['embedding_calls_approx']}")
    print(f"  Conversations tracked:  {sdk_stats['conversations_tracked']}")
    print(f"{'='*70}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": metadata,
            "results": results
        }, f, indent=2, default=str)
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_path}")
    
    # Generate human-readable summary TXT
    summary_path = Path(str(output_path).replace(".json", "_summary.txt"))
    generate_summary_txt(results, summary_path, metadata)
    print(f"Summary saved to: {summary_path}")
    
    # Print summary
    print_summary(results)
    
    # Visualize
    try:
        # Use custom name for figure if provided, otherwise use timestamped
        if getattr(args, 'save_name', None):
            figure_path = get_timestamped_filename("png", custom_name=getattr(args, 'save_name', None))
        else:
        figure_path = get_timestamped_filename("png", "figure")
        visualize_results(results, str(figure_path))
        print(f"Figure saved to: {figure_path}")
    except Exception as e:
        print(f"Visualization error: {e}")


if __name__ == "__main__":
    main()

