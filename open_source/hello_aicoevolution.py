#!/usr/bin/env python3
"""
hello_aicoevolution.py
======================

Minimal working example for the PyPI package:

    pip install aicoevolution

Usage (recommended):
    # Windows PowerShell:
    #   $env:AIC_SDK_API_KEY="aic_..."
    # cmd.exe:
    #   set AIC_SDK_API_KEY=aic_...

    python hello_aicoevolution.py

Optional:
    set AIC_SDK_URL=https://sdk.aicoevolution.com
"""

from __future__ import annotations

import os
import time
import uuid

# This script is intended to be run on any machine after:
#   pip install aicoevolution
#
# Note: If you run this file *inside the MirrorMind monorepo*, Python may import
# the local `aicoevolution_sdk/` package instead of the PyPI thin client module.
# For end users, copy this file into a normal folder (or a fresh venv) and run it there.
from aicoevolution_sdk import AICoevolutionClient, SDKAuth


def _print_metrics(label: str, resp: dict) -> None:
    """Print SDK metrics with Paper 03 canonical extraction.
    
    Paper 03 metrics:
    - SGI: turn_pair_sgi_latest (or fallback to sgi_latest)
    - Velocity: orbital_velocity_latest (turn-pair, ~25-45°)
      Fallback: angular_velocity_latest (per-message, ~75-180°)
    
    The SDK now exposes these at top level for easy access.
    """
    print(f"\n[{label}]")
    print("conversation_id:", resp.get("conversation_id"))
    print("message_count:", resp.get("message_count"))

    # Paper 03: Prefer turn-pair SGI when available (now at top level)
    sgi = resp.get("turn_pair_sgi_latest") or resp.get("sgi_latest")
    
    # Paper 03: Prefer orbital velocity (turn-pair, ~25-45°) over angular (per-message, ~75-180°)
    velocity = resp.get("orbital_velocity_latest") or resp.get("angular_velocity_latest")
    
    # Core telemetry fields (may be None early in a conversation)
    print("sgi_latest:", sgi)
    print("orbital_velocity_latest:", velocity)
    print("context_phase:", resp.get("context_phase"))
    print("context_mass:", resp.get("context_mass"))
    print("attractor_count:", resp.get("attractor_count"))

    quota = resp.get("quota")
    if isinstance(quota, dict):
        remaining_units = quota.get("remaining")
        try:
            remaining_units_int = int(remaining_units)
            turns_left = max(0, remaining_units_int // 2)  # ~2 ingest calls per Q/A turn
            print("turns_left_this_week:", turns_left)
        except Exception:
            # If quota is unlimited (-1) or missing, just print the raw object.
            print("quota:", quota)


def main() -> None:
    api_key = (os.getenv("AIC_SDK_API_KEY") or "").strip()
    if not api_key:
        raise SystemExit("Missing AIC_SDK_API_KEY. Set it to your aic_... key and retry.")

    base_url = (os.getenv("AIC_SDK_URL") or "https://sdk.aicoevolution.com").strip()

    sdk = AICoevolutionClient(
        base_url=base_url,
        auth=SDKAuth(user_api_key=api_key),
        timeout_s=30.0,
    )

    conversation_id = f"hello_{uuid.uuid4().hex[:8]}"
    now_ms = lambda: int(time.time() * 1000)

    # 1) Ingest user message
    r1 = sdk.ingest(
        conversation_id=conversation_id,
        role="user",
        text="Hello — I'm testing AICoevolution semantic telemetry.",
        timestamp_ms=now_ms(),
    )
    _print_metrics("USER INGEST", r1)

    # 2) Ingest assistant message (this is when SGI/velocity typically becomes meaningful)
    r2 = sdk.ingest(
        conversation_id=conversation_id,
        role="assistant",
        text="Great. Tell me what topic you'd like to explore and I’ll respond concisely.",
        timestamp_ms=now_ms(),
    )
    _print_metrics("ASSISTANT INGEST", r2)


if __name__ == "__main__":
    main()


