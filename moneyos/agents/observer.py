from __future__ import annotations

from ..models import AccountSnapshot


class ObserverAgent:
    def __init__(self, connectors: list) -> None:
        self.connectors = connectors

    def snapshot(self) -> tuple[list[AccountSnapshot], list[str]]:
        accounts: list[AccountSnapshot] = []
        warnings: list[str] = []
        for connector in self.connectors:
            if not connector.available():
                warnings.append(f"{connector.name}: not configured")
                continue
            try:
                accounts.extend(connector.accounts())
            except Exception as e:
                warnings.append(f"{connector.name}: {type(e).__name__}: {e}")
        return accounts, warnings
