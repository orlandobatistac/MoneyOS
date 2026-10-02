from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_policy(path: str = "config/policy.yaml") -> dict[str, Any]:
    policy = load_yaml(path)
    if not policy:
        policy = load_yaml("config/policy.example.yaml")

    execution = policy.setdefault("execution", {})
    if os.getenv("MONEYOS_EXECUTION_MODE"):
        execution["mode"] = os.getenv("MONEYOS_EXECUTION_MODE")
    if "MONEYOS_KILL_SWITCH" in os.environ:
        execution["kill_switch"] = env_bool("MONEYOS_KILL_SWITCH")

    return policy
