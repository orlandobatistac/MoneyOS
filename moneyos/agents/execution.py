from __future__ import annotations

from ..models import ActionIntent, ExecutionResult


class ExecutionAgent:
    action_types: set[str] = set()

    def __init__(self, guardrails, connectors: dict) -> None:
        self.guardrails = guardrails
        self.connectors = connectors

    def handles(self, intent: ActionIntent) -> bool:
        return intent.action_type in self.action_types

    def run(self, intent: ActionIntent) -> ExecutionResult:
        check = self.guardrails.check(intent)
        if check.status == "blocked":
            return check

        if self.guardrails.mode != "live":
            return check

        connector = self.connectors.get(intent.connector)
        if connector is None:
            return ExecutionResult(
                "blocked",
                intent,
                f"No connector named {intent.connector}.",
            )

        return connector.execute(intent)


class PayAgent(ExecutionAgent):
    action_types = {"payment", "transfer"}


class CollectionAgent(ExecutionAgent):
    action_types = {"collection"}


class InvestAgent(ExecutionAgent):
    action_types = {"investment"}


class StrategyAgent(ExecutionAgent):
    action_types = {"speculation"}
