from __future__ import annotations

from collections import defaultdict

from .models import ActionIntent, ExecutionResult


class Guardrails:
    def __init__(self, policy: dict) -> None:
        self.policy = policy
        self.execution = policy.get("execution", {})
        self._daily_totals = defaultdict(float)

    @property
    def mode(self) -> str:
        return str(self.execution.get("mode", "dry_run"))

    def check(self, intent: ActionIntent) -> ExecutionResult:
        if self.execution.get("kill_switch", False):
            return ExecutionResult("blocked", intent, "Kill switch is enabled.")

        if self.mode != "live":
            return ExecutionResult("planned", intent, "Dry-run mode: no money moved.")

        if intent.action_type == "payment":
            if not self.execution.get("allow_live_payments", False):
                return ExecutionResult("blocked", intent, "Live payments are disabled by policy.")
            max_single = float(self.execution.get("max_single_payment", 0))
            max_daily = float(self.execution.get("max_daily_payments", 0))
            key = "payment"
        elif intent.action_type in {"investment", "speculation"}:
            flag = "allow_live_investing" if intent.action_type == "investment" else "allow_live_speculation"
            if not self.execution.get(flag, False):
                return ExecutionResult("blocked", intent, f"Live {intent.action_type} is disabled by policy.")
            max_single = float(self.execution.get("max_single_trade", 0))
            max_daily = float(self.execution.get("max_daily_trades", 0))
            key = "trade"
        else:
            max_single = 0.0
            max_daily = 0.0
            key = intent.action_type

        if max_single and intent.amount > max_single:
            return ExecutionResult("blocked", intent, f"Amount exceeds single-action cap ({max_single:.2f}).")

        if max_daily and self._daily_totals[key] + intent.amount > max_daily:
            return ExecutionResult("blocked", intent, f"Amount exceeds daily cap ({max_daily:.2f}).")

        approval_cutoff = float(self.execution.get("require_manual_approval_above", 0))
        if approval_cutoff and intent.amount > approval_cutoff and intent.requires_approval:
            return ExecutionResult("blocked", intent, "Manual approval required above configured threshold.")

        self._daily_totals[key] += intent.amount
        return ExecutionResult("planned", intent, "Policy checks passed; connector may execute.")
