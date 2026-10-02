from __future__ import annotations

import os
import ccxt

from .base import Connector
from ..models import AccountSnapshot, ActionIntent, ExecutionResult


class CCXTCryptoConnector(Connector):
    name = "crypto"

    def __init__(self) -> None:
        exchange_id = os.getenv("CRYPTO_EXCHANGE", "coinbase")
        exchange_cls = getattr(ccxt, exchange_id, None)
        self.exchange = None
        if exchange_cls:
            params = {
                "apiKey": os.getenv("CRYPTO_API_KEY", ""),
                "secret": os.getenv("CRYPTO_API_SECRET", ""),
                "enableRateLimit": True,
            }
            passphrase = os.getenv("CRYPTO_API_PASSPHRASE")
            if passphrase:
                params["password"] = passphrase
            self.exchange = exchange_cls(params)
            if os.getenv("CRYPTO_SANDBOX", "false").lower() in {"1", "true", "yes", "on"}:
                try:
                    self.exchange.set_sandbox_mode(True)
                except Exception:
                    pass

    def available(self) -> bool:
        return bool(self.exchange and os.getenv("CRYPTO_API_KEY") and os.getenv("CRYPTO_API_SECRET"))

    def accounts(self) -> list[AccountSnapshot]:
        if not self.available():
            return []
        balance = self.exchange.fetch_balance()
        total = balance.get("total", {})
        rows = []
        for currency, amount in total.items():
            if amount:
                rows.append(AccountSnapshot(
                    source=self.name,
                    account_id=f"crypto-{currency}",
                    name=f"Crypto {currency}",
                    kind="crypto",
                    balance=float(amount),
                    currency=currency,
                ))
        return rows

    def execute(self, intent: ActionIntent) -> ExecutionResult:
        if not self.available():
            return ExecutionResult("failed", intent, "Crypto exchange credentials are missing.")
        symbol = intent.target or ""
        if not symbol:
            return ExecutionResult("failed", intent, "Crypto symbol is missing.")
        side = intent.metadata.get("side", "buy")
        order_type = intent.metadata.get("order_type", "market")
        amount = intent.metadata.get("base_amount")
        if amount is None:
            return ExecutionResult("failed", intent, "base_amount is required for crypto execution.")
        try:
            order = self.exchange.create_order(
                symbol,
                order_type,
                side,
                float(amount),
                intent.metadata.get("price"),
            )
            return ExecutionResult("executed", intent, "Crypto order submitted.", external_id=str(order.get("id")))
        except Exception as e:
            return ExecutionResult("failed", intent, f"Crypto order failed: {e}")
