#!/usr/bin/env python3
"""
AICoevolution Semantic Telemetry (Production)
=============================================
A lightweight tool to measure semantic dynamics in human-AI conversations.
This version is optimized for production use with the AICoevolution Cloud SDK.

Usage:
    python semantic_telemetry_prod.py --api-key aic_...
    python semantic_telemetry_prod.py --api-key aic_... --hosted-ai

Requirements:
    pip install requests
"""

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_SDK_URL = "https://sdk.aicoevolution.com"

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _disable_colors():
    """Disable ANSI colors (prints become plain text)."""
    for k in list(Colors.__dict__.keys()):
        if k.isupper():
            setattr(Colors, k, "")

def _init_console_colors(enable: bool) -> None:
    """
    Ensure colors render on Windows terminals.
    If color support isn't available, fall back to plain text.
    """
    if not enable or os.getenv("NO_COLOR") or os.getenv("AIC_NO_COLOR"):
        _disable_colors()
        return

    if os.name == "nt":
        try:
            import colorama  # type: ignore
            # Translates ANSI escapes for Windows consoles.
            try:
                colorama.just_fix_windows_console()
            except Exception:
                colorama.init()
        except Exception:
            _disable_colors()

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TelemetryMetrics:
    """Standardized metrics from SDK response."""
    sgi: Optional[float]
    velocity: Optional[float]
    context_phase: str
    context_mass: int
    attractor_count: int
    context_drift: float
    processing_time_ms: int

@dataclass
class CoevolutionIndex:
    """Computed Coevolution Index (CI)."""
    coevolution_index: float
    tier: str  # BASIC | ELEVATED | HIGH
    horizontal_score: float
    vertical_score: float
    
    # Components
    coherence_region_occupancy: float
    dyadic_coherence_index: float
    context_stability: float
    symbolic_entropy: float
    path_transformation_density: float
    domain_balance_index: float

# =============================================================================
# SDK CLIENT
# =============================================================================

class SemanticTelemetryClient:
    """Client for interacting with the AICoevolution SDK."""
    
    def __init__(self, api_key: str, base_url: str = DEFAULT_SDK_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.conversation_id = str(uuid.uuid4())
        self.message_count = 0
        self.messages = []  # Local history for hosted AI context
        
        # Validate connection on init
        try:
            import requests
            self.session = requests.Session()
            if api_key:
                self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        except ImportError:
            print("Error: 'requests' library not found.")
            print("Please install it: pip install requests")
            sys.exit(1)

    def ingest_message(self, role: str, text: str) -> Optional[Dict[str, Any]]:
        """Send a message to the SDK for telemetry analysis."""
        url = f"{self.base_url}/v0/ingest"
        payload = {
            "conversation_id": self.conversation_id,
            "role": role,
            "text": text,
            "timestamp_ms": int(time.time() * 1000)
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            if response.status_code == 401:
                # FastAPI typically returns JSON {"detail": ...}; include body when present.
                body = (response.text or "").strip()
                if body:
                    body = body[:800] + ("..." if len(body) > 800 else "")
                    print(f"\n{Colors.RED}[SDK Error] Invalid API Key :: {body}{Colors.ENDC}")
                else:
                    print(f"\n{Colors.RED}[SDK Error] Invalid API Key.{Colors.ENDC}")
                return None
            response.raise_for_status()
            self.message_count += 1
            return response.json()
        except Exception as e:
            # Surface server-provided details where possible.
            resp = getattr(e, "response", None)
            if resp is not None:
                body = (resp.text or "").strip()
                body = body[:800] + ("..." if len(body) > 800 else "")
                if body:
                    print(f"\n{Colors.RED}[SDK Error] Connection failed: {e} :: {body}{Colors.ENDC}")
                    return None
            print(f"\n{Colors.RED}[SDK Error] Connection failed: {e}{Colors.ENDC}")
            return None

    def hosted_chat(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Send message to hosted AI endpoint (paid tier only)."""
        url = f"{self.base_url}/v0/chat"
        payload = {
            "message": user_message,
            "conversation_id": self.conversation_id,
            "messages": self.messages[-10:]  # Send recent context
        }
        
        try:
            # Hosted AI can take longer (LLM generation)
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 401:
                body = (response.text or "").strip()
                if body:
                    body = body[:800] + ("..." if len(body) > 800 else "")
                    print(f"\n{Colors.RED}[SDK Error] Unauthorized :: {body}{Colors.ENDC}")
                else:
                    print(f"\n{Colors.RED}[SDK Error] Unauthorized. Hosted AI requires a paid API key.{Colors.ENDC}")
                return None
            elif response.status_code == 402:
                body = (response.text or "").strip()
                if body:
                    body = body[:800] + ("..." if len(body) > 800 else "")
                    print(f"\n{Colors.RED}[SDK Error] Payment required :: {body}{Colors.ENDC}")
                else:
                    print(f"\n{Colors.RED}[SDK Error] Payment required. Upgrade to a paid tier for Hosted AI.{Colors.ENDC}")
                return None
                
            response.raise_for_status()
            self.message_count += 2  # User + Assistant
            return response.json()
        except Exception as e:
            resp = getattr(e, "response", None)
            if resp is not None:
                body = (resp.text or "").strip()
                body = body[:800] + ("..." if len(body) > 800 else "")
                if body:
                    print(f"\n{Colors.RED}[SDK Error] Chat request failed: {e} :: {body}{Colors.ENDC}")
                    return None
            print(f"\n{Colors.RED}[SDK Error] Chat request failed: {e}{Colors.ENDC}")
            return None

    def extract_metrics(self, response: Dict[str, Any]) -> TelemetryMetrics:
        """Extract standardized metrics from SDK response.
        
        Paper 03 canonical metrics:
        - SGI: turn_pair_sgi_latest (or fallback to sgi_latest)
        - Velocity: orbital_velocity_latest (turn-pair, ~25-45°)
          Fallback: angular_velocity_latest (per-message, ~75-180°)
        
        Turn-pair metrics have lower variance and are the canonical choice.
        The SDK now exposes these at top level for easy access.
        """
        # Paper 03: Prefer turn-pair SGI when available (now at top level)
        sgi = (
            response.get("turn_pair_sgi_latest")
            or response.get("sgi_latest")
        )
        
        # Paper 03: Prefer orbital velocity (turn-pair, ~25-45°) over angular (per-message, ~75-180°)
        velocity = (
            response.get("orbital_velocity_latest")
            or response.get("angular_velocity_latest")
        )
        
        return TelemetryMetrics(
            sgi=sgi,
            velocity=velocity,
            context_phase=response.get("context_phase", "stable"),
            context_mass=response.get("context_mass", 0),
            attractor_count=response.get("attractor_count", 1),
            context_drift=response.get("context_drift", 0.0),
            processing_time_ms=response.get("processing_time_ms", 0)
        )

# =============================================================================
# COEVOLUTION TRACKER (Client-Side Logic)
# =============================================================================

class CoevolutionTracker:
    """Tracks session dynamics to compute the Coevolution Index."""
    
    def __init__(self):
        self.turns: List[TelemetryMetrics] = []
        self.sgi_history: List[float] = []
        self.velocity_history: List[float] = []
        
    def add_turn(self, metrics: TelemetryMetrics):
        self.turns.append(metrics)
        if metrics.sgi is not None:
            self.sgi_history.append(metrics.sgi)
        if metrics.velocity is not None:
            self.velocity_history.append(metrics.velocity)
            
    def compute_index(self) -> CoevolutionIndex:
        """Compute the Coevolution Index based on accumulated history."""
        if not self.turns:
            return CoevolutionIndex(0, "BASIC", 0, 0, 0, 0, 0, 0, 0, 0)
            
        # 1. Horizontal Score (Hs) - Dynamics
        # Coherence Region: SGI > 0.6 AND Velocity < 30 deg
        coherence_count = sum(1 for s, v in zip(self.sgi_history, self.velocity_history) 
                            if s > 0.6 and v < 30.0)
        coherence_occupancy = coherence_count / len(self.turns) if self.turns else 0
        
        # Dyadic Coherence: Mean SGI
        dyadic_coherence = sum(self.sgi_history) / len(self.sgi_history) if self.sgi_history else 0
        
        # Context Stability: 1.0 - normalized drift
        avg_drift = sum(t.context_drift for t in self.turns) / len(self.turns) if self.turns else 0
        context_stability = max(0.0, 1.0 - (avg_drift / 100.0))
        
        hs = (coherence_occupancy * 0.4) + (dyadic_coherence * 0.4) + (context_stability * 0.2)
        
        # 2. Vertical Score (Vs) - Depth (Simplified for Prod)
        # In production script without S64/Stage1, we use placeholders or simplified proxies
        # For now, we fix these to baseline values as full S64 is in the Dev script
        symbolic_entropy = 0.5 
        path_density = 0.0
        domain_balance = 0.5
        
        vs = (symbolic_entropy * 0.3) + (path_density * 0.4) + (domain_balance * 0.3)
        
        # 3. Coevolution Index
        ci = (hs * 0.6) + (vs * 0.4)
        
        # Tier
        if ci >= 0.7: tier = "HIGH"
        elif ci >= 0.4: tier = "ELEVATED"
        else: tier = "BASIC"
        
        return CoevolutionIndex(
            coevolution_index=ci,
            tier=tier,
            horizontal_score=hs,
            vertical_score=vs,
            coherence_region_occupancy=coherence_occupancy,
            dyadic_coherence_index=dyadic_coherence,
            context_stability=context_stability,
            symbolic_entropy=symbolic_entropy,
            path_transformation_density=path_density,
            domain_balance_index=domain_balance
        )

# =============================================================================
# UI HELPERS
# =============================================================================

def print_header():
    print(f"\n{Colors.CYAN}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           AICoevolution Semantic Telemetry (v1.0)            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

def print_metrics(m: TelemetryMetrics):
    print(f"{Colors.BLUE}  Metrics:{Colors.ENDC}")
    
    # SGI
    sgi_color = Colors.GREEN if (m.sgi or 0) > 0.7 else Colors.YELLOW if (m.sgi or 0) > 0.4 else Colors.RED
    print(f"    SGI:           {sgi_color}{m.sgi:.3f}{Colors.ENDC}" if m.sgi is not None else "    SGI:           N/A")
    
    # Velocity
    vel_color = Colors.GREEN if (m.velocity or 0) < 15 else Colors.YELLOW if (m.velocity or 0) < 45 else Colors.RED
    print(f"    Velocity:      {vel_color}{m.velocity:.1f}°{Colors.ENDC}" if m.velocity is not None else "    Velocity:      N/A")
    
    # Context
    print(f"    Context Phase: {m.context_phase}")
    print(f"    Context Mass:  {m.context_mass}")

def print_ci(ci: CoevolutionIndex):
    tier_color = Colors.GREEN if ci.tier == "HIGH" else Colors.YELLOW if ci.tier == "ELEVATED" else Colors.RED
    print(f"\n{Colors.BOLD}──────────────────────── COEVOLUTION INDEX ─────────────────────────{Colors.ENDC}")
    print(f"  CI: {tier_color}{ci.coevolution_index:.3f} [{ci.tier}]{Colors.ENDC}")
    print(f"  Horizontal Score: {ci.horizontal_score:.3f}")
    print(f"  Vertical Score:   {ci.vertical_score:.3f} (Limited in Prod)")
    print(f"{Colors.BOLD}────────────────────────────────────────────────────────────────────{Colors.ENDC}")

# =============================================================================
# MAIN LOOP
# =============================================================================

def run_session(client: SemanticTelemetryClient, turns: int, hosted_ai: bool):
    print_header()
    print(f"Session ID: {client.conversation_id}")
    print(f"Target:     {client.base_url}")
    print(f"Mode:       {'Hosted AI' if hosted_ai else 'Manual Entry'}")
    print("\nType 'quit' to exit.\n")
    
    tracker = CoevolutionTracker()
    
    for i in range(turns):
        print(f"\n{Colors.BOLD}--- Turn {i+1}/{turns} ---{Colors.ENDC}")
        
        # User Input
        try:
            user_text = input(f"{Colors.GREEN}[YOU]:{Colors.ENDC} ").strip()
        except (KeyboardInterrupt, EOFError):
            break
            
        if user_text.lower() in ('quit', 'exit'):
            break
        if not user_text:
            continue
            
        # Process Turn
        if hosted_ai:
            print(f"{Colors.CYAN}  ... generating response ...{Colors.ENDC}")
            client.messages.append({"role": "user", "content": user_text})
            
            data = client.hosted_chat(user_text)
            if not data: continue
            
            reply = data.get("reply", "")
            sdk_data = data.get("sdk", {})
            quota = data.get("quota") if isinstance(data, dict) else None
            turns_left = None
            try:
                if isinstance(quota, dict) and isinstance(quota.get("remaining"), int):
                    turns_left = max(0, int(quota["remaining"]) // 2)
            except Exception:
                turns_left = None
            client.messages.append({"role": "assistant", "content": reply})
            
            print(f"{Colors.BLUE}[AI]:{Colors.ENDC} {reply}\n")
            
            metrics = client.extract_metrics(sdk_data)
            print_metrics(metrics)
            tracker.add_turn(metrics)
            print_ci(tracker.compute_index())
            if turns_left is not None:
                print(f"{Colors.CYAN}  Turns left this week: {turns_left}{Colors.ENDC}")
            
        else:
            # Manual Mode
            print(f"{Colors.CYAN}  ... ingesting ...{Colors.ENDC}")
            resp = client.ingest_message("user", user_text)
            if resp:
                m = client.extract_metrics(resp)
                sgi_str = f"{m.sgi:.2f}" if m.sgi is not None else "N/A"
                print(f"  [SDK] User turn ingested (SGI={sgi_str})")
            
            try:
                ai_text = input(f"{Colors.BLUE}[AI]:{Colors.ENDC} ").strip()
            except (KeyboardInterrupt, EOFError):
                break
                
            if not ai_text: ai_text = "(no response)"
            
            print(f"{Colors.CYAN}  ... ingesting ...{Colors.ENDC}")
            resp = client.ingest_message("assistant", ai_text)
            if resp:
                metrics = client.extract_metrics(resp)
                print_metrics(metrics)
                tracker.add_turn(metrics)
                print_ci(tracker.compute_index())

# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AICoevolution Semantic Telemetry (Production)")
    parser.add_argument("--api-key", required=True, help="Your AICoevolution API Key")
    parser.add_argument("--url", help=f"Custom SDK URL (default: {DEFAULT_SDK_URL})")
    parser.add_argument("--hosted-ai", action="store_true", help="Use Hosted AI for responses")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    
    args = parser.parse_args()
    _init_console_colors(enable=not args.no_color)
    
    client = SemanticTelemetryClient(args.api_key, base_url=(args.url or DEFAULT_SDK_URL))
    run_session(client, args.turns, args.hosted_ai)

