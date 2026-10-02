from __future__ import annotations

from datetime import date

from .agents.auditor import AuditorAgent
from .agents.observer import ObserverAgent
from .agents.router import MoneyRouter
from .config import load_policy, load_yaml
from .connectors.alpaca import AlpacaConnector
from .connectors.crypto import CCXTCryptoConnector
from .connectors.plaid import PlaidConnector
from .connectors.stripe import StripeConnector
from .models import Obligation
from .policy import Guardrails
from .storage import JsonStore


class MoneyOS:
    def __init__(self, policy_path: str = "config/policy.yaml", runtime_dir: str = "runtime") -> None:
        self.policy = load_policy(policy_path)
        self.store = JsonStore(runtime_dir)
        self.connectors = {
            "plaid": PlaidConnector(),
            "stripe": StripeConnector(),
            "alpaca": AlpacaConnector(),
            "crypto": CCXTCryptoConnector(),
        }
        self.observer = ObserverAgent(list(self.connectors.values()))
        self.router = MoneyRouter(self.policy)
        self.guardrails = Guardrails(self.policy)
        self.auditor = AuditorAgent()

    def load_obligations(self, path: str = "config/obligations.yaml") -> list[Obligation]:
        raw = load_yaml(path)
        if not raw:
            raw = load_yaml("config/obligations.example.yaml")
        rows = []
        for x in raw.get("obligations", []):
            rows.append(Obligation(
                id=str(x["id"]),
                name=str(x["name"]),
                amount=float(x["amount"]),
                due_date=date.fromisoformat(str(x["due_date"])),
                priority=int(x.get("priority", 100)),
                autopay=bool(x.get("autopay", False)),
                payment_connector=str(x.get("payment_connector", "manual")),
                metadata=dict(x.get("metadata", {})),
            ))
        return rows

    def refresh(self) -> dict:
        accounts, warnings = self.observer.snapshot()
        payload = {"accounts": [a.__dict__ for a in accounts], "warnings": warnings}
        self.store.write("snapshot.json", payload)
        return payload

    def plan(self, incoming_amount: float = 0.0) -> dict:
        snapshot = self.store.read("snapshot.json", {"accounts": [], "warnings": []})
        cash = sum(
            float(a.get("available") if a.get("available") is not None else a.get("balance", 0))
            for a in snapshot.get("accounts", [])
            if "checking" in str(a.get("kind", "")) or "savings" in str(a.get("kind", ""))
        )
        obligations = self.load_obligations()
        plan = self.router.build_plan(
            cash_balance=cash,
            incoming_amount=incoming_amount,
            obligations=obligations,
        )
        plan.warnings.extend(snapshot.get("warnings", []))
        self.store.write("plan.json", plan.to_dict())
        return plan.to_dict()

    def execute(self, plan: dict) -> dict:
        from .models import ActionIntent, ExecutionResult

        results = []
        for raw in plan.get("intents", []):
            intent = ActionIntent(**raw)
            check = self.guardrails.check(intent)

            if check.status == "blocked":
                results.append(check)
                continue

            if self.guardrails.mode != "live":
                results.append(check)
                continue

            connector = self.connectors.get(intent.connector)
            if connector is None:
                results.append(
                    ExecutionResult("blocked", intent, f"No connector named {intent.connector}.")
                )
                continue
            results.append(connector.execute(intent))

        audit = self.auditor.summarize(results)
        self.store.write("audit.json", audit)
        return audit

    def run(self, incoming_amount: float = 0.0) -> dict:
        snapshot = self.refresh()
        plan = self.plan(incoming_amount=incoming_amount)
        audit = self.execute(plan)
        result = {"snapshot": snapshot, "plan": plan, "audit": audit}
        self.store.write("latest.json", result)
        return result
