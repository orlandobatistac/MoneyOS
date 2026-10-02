from __future__ import annotations

import os
import requests

from .base import Connector
from ..models import AccountSnapshot, ActionIntent, ExecutionResult


class AlpacaConnector(Connector):
    name = "alpaca"

    def __init__(self) -> None:
        self.key = os.getenv("ALPACA_API_KEY")
        self.secret = os.getenv("ALPACA_API_SECRET")
        paper = os.getenv("ALPACA_PAPER", "true").lower() in {"1", "true", "yes", "on"}
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"

    def available(self) -> bool:
        return bool(self.key and self.secret)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.key or "",
            "APCA-API-SECRET-KEY": self.secret or "",
        }

    def accounts(self) -> list[AccountSnapshot]:
        if not self.available():
            return []
        r = requests.get(self.base_url + "/v2/account", headers=self.headers, timeout=30)
        r.raise_for_status()
        a = r.json()
        return [AccountSnapshot(
            source=self.name,
            account_id=str(a.get("id", "alpaca")),
            name="Alpaca brokerage",
            kind="brokerage",
            balance=float(a.get("equity") or 0),
            available=float(a.get("cash") or 0),
            currency="USD",
            metadata={"buying_power": a.get("buying_power"), "status": a.get("status")},
        )]

    def execute(self, intent: ActionIntent) -> ExecutionResult:
        if not self.available():
            return ExecutionResult("failed", intent, "Alpaca credentials are missing.")
        symbol = intent.target or ""
        if not symbol:
            return ExecutionResult("failed", intent, "Trade target symbol is missing.")
        payload = {
            "symbol": symbol,
            "notional": f"{intent.amount:.2f}",
            "side": intent.metadata.get("side", "buy"),
            "type": intent.metadata.get("order_type", "market"),
            "time_in_force": intent.metadata.get("time_in_force", "day"),
        }
        r = requests.post(
            self.base_url + "/v2/orders",
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if r.status_code >= 400:
            return ExecutionResult("failed", intent, f"Alpaca rejected order: {r.text[:300]}")
        data = r.json()
        return ExecutionResult("executed", intent, "Alpaca order submitted.", external_id=str(data.get("id")))
