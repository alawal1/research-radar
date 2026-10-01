"""Small utilities used across the agent."""

from pathlib import Path
import yaml
from schemas import GateResult


def load_config(path: str = "config.yaml") -> dict:
    """Load config.yaml and return it as a dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def feasibility_total(gate: GateResult) -> int:
    """Sum the four feasibility scores into a 0-8 total."""
    return (
        gate.score_relevant
        + gate.score_positioned
        + gate.score_practical
        + gate.score_rigorous
    )