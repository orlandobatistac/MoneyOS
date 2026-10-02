from __future__ import annotations

import os
import requests

from .base import Connector
from ..models import AccountSnapshot, ActionIntent, ExecutionResult


class StripeConnector(Connector):
    name = "stripe"
    base_url = "https://api.stripe.com/v1"

    def __init__(self) -> None:
        self.key = os.getenv("STRIPE_SECRET_KEY")

    def available(self) -> bool:
        return bool(self.key)

    def _get(self, path: str) -> dict:
        r = requests.get(self.base_url + path, auth=(self.key or "", ""), timeout=30)
        r.raise_for_status()
        return r.json()

    def accounts(self) -> list[AccountSnapshot]:
        if not self.available():
            return []
        data = self._get("/balance")
        rows = []
        for group_name in ("available", "pending"):
            for item in data.get(group_name, []):
                rows.append(AccountSnapshot(
                    source=self.name,
                    account_id=f"stripe-{group_name}-{item.get('currency')}",
                    name=f"Stripe {group_name}",
                    kind="processor_balance",
                    balance=float(item.get("amount", 0)) / 100.0,
                    currency=str(item.get("currency", "usd")).upper(),
                ))
        return rows

    def execute(self, intent: ActionIntent) -> ExecutionResult:
        return ExecutionResult(
            "blocked",
            intent,
            "Stripe collection execution is separated from cash movement. Use invoices/payment links with explicit customer context."
        )
