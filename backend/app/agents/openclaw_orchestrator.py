"""
NemoClaw Orchestrator (OpenClaw alias) — identical to nemoclaw_orchestrator.

This module re-exports the NemoClaw orchestrator for backward compatibility.
"""
from app.agents.nemoclaw_orchestrator import (  # type: ignore  # noqa: F401
    NemoClawOrchestrator,
    ProcessingResult,
)

# Alias for code that references OpenClaw naming
OpenClawOrchestrator = NemoClawOrchestrator
