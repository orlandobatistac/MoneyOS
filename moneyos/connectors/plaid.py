from __future__ import annotations

import os
import requests

from .base import Connector
from ..models import AccountSnapshot


class PlaidConnector(Connector):
    name = "plaid"

    def __init__(self) -> None:
        env = os.getenv("PLAID_ENV", "development")
        self.base_url = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }.get(env, "https://development.plaid.com")
        self.client_id = os.getenv("PLAID_CLIENT_ID")
        self.secret = os.getenv("PLAID_SECRET")
        self.access_tokens = [x.strip() for x in os.getenv("PLAID_ACCESS_TOKENS", "").split(",") if x.strip()]

    def available(self) -> bool:
        return bool(self.client_id and self.secret and self.access_tokens)

    def _post(self, path: str, body: dict) -> dict:
        headers = {
            "PLAID-CLIENT-ID": self.client_id or "",
            "PLAID-SECRET": self.secret or "",
            "Content-Type": "application/json",
        }
        r = requests.post(self.base_url + path, headers=headers, json=body, timeout=30)
        r.raise_for_status()
        return r.json()

    def accounts(self) -> list[AccountSnapshot]:
        snapshots: list[AccountSnapshot] = []
        if not self.available():
            return snapshots
        for token in self.access_tokens:
            data = self._post("/accounts/balance/get", {"access_token": token})
            for a in data.get("accounts", []):
                b = a.get("balances", {})
                snapshots.append(AccountSnapshot(
                    source=self.name,
                    account_id=a.get("account_id", ""),
                    name=a.get("name") or a.get("official_name") or "Plaid account",
                    kind=f"{a.get('type','')}/{a.get('subtype','')}",
                    balance=float(b.get("current") or 0),
                    available=b.get("available"),
                    currency=b.get("iso_currency_code") or "USD",
                ))
        return snapshots

    def liabilities(self) -> list[dict]:
        rows = []
        if not self.available():
            return rows
        for token in self.access_tokens:
            try:
                rows.append(self._post("/liabilities/get", {"access_token": token}))
            except requests.HTTPError:
                continue
        return rows
