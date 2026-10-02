from __future__ import annotations

from abc import ABC

from ..models import AccountSnapshot, ActionIntent, ExecutionResult


class Connector(ABC):
    name = "base"

    def available(self) -> bool:
        return True

    def accounts(self) -> list[AccountSnapshot]:
        return []

    def execute(self, intent: ActionIntent) -> ExecutionResult:
        return ExecutionResult("blocked", intent, f"{self.name} does not support execution.")
