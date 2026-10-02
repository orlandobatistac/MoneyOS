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
        r = requests.get(
            self.base_url + path,
            auth=(self.key or "", ""),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def _post(
        self,
        path: str,
        data: dict,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        r = requests.post(
            self.base_url + path,
            auth=(self.key or "", ""),
            data=data,
            headers=headers,
            timeout=30,
        )
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
                    account_id=(
                        f"stripe-{group_name}-"
                        f"{item.get('currency')}"
                    ),
                    name=f"Stripe {group_name}",
                    kind="processor_balance",
                    balance=(
                        float(item.get("amount", 0))
                        / 100.0
                    ),
                    currency=str(
                        item.get("currency", "usd")
                    ).upper(),
                ))
        return rows

    def execute(
        self,
        intent: ActionIntent,
    ) -> ExecutionResult:
        if intent.action_type != "collection":
            return ExecutionResult(
                "blocked",
                intent,
                "Stripe connector only executes collection intents.",
            )

        if not self.available():
            return ExecutionResult(
                "failed",
                intent,
                "Stripe credentials are missing.",
            )

        currency = str(
            intent.metadata.get(
                "currency",
                intent.currency,
            )
        ).lower()

        cents = int(round(intent.amount * 100))
        base_key = (
            f"moneyos-{intent.target or 'collection'}"
        )

        try:
            product = self._post(
                "/products",
                {
                    "name": (
                        intent.description
                        or intent.target
                        or "MoneyOS collection"
                    )
                },
                base_key + "-product",
            )

            price = self._post(
                "/prices",
                {
                    "unit_amount": str(cents),
                    "currency": currency,
                    "product": product["id"],
                },
                base_key + "-price",
            )

            link = self._post(
                "/payment_links",
                {
                    "line_items[0][price]": price["id"],
                    "line_items[0][quantity]": "1",
                },
                base_key + "-link",
            )

            return ExecutionResult(
                "executed",
                intent,
                (
                    "Stripe payment link ready: "
                    f"{link.get('url')}"
                ),
                external_id=str(
                    link.get("id")
                    or link.get("url")
                ),
            )
        except Exception as e:
            return ExecutionResult(
                "failed",
                intent,
                f"Stripe collection failed: {e}",
            )
