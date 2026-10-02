from __future__ import annotations

from datetime import date

from ..config import load_yaml
from ..models import ActionIntent


class RevenueAgent:
    def __init__(self, plaid_connector, store) -> None:
        self.plaid = plaid_connector
        self.store = store

    def detect_new_inflows(self) -> tuple[list[dict], list[str]]:
        warnings: list[str] = []
        if not self.plaid.available():
            return [], ["revenue: Plaid inflow detection not configured"]

        state = self.store.read("revenue_state.json", {"plaid_cursors": {}})
        try:
            inflows, cursors = self.plaid.sync_posted_inflows(state.get("plaid_cursors", {}))
            self.store.write("revenue_state.json", {"plaid_cursors": cursors})
            return inflows, warnings
        except Exception as e:
            warnings.append(f"revenue: {type(e).__name__}: {e}")
            return [], warnings

    def collection_intents(self, path: str = "config/receivables.yaml") -> list[ActionIntent]:
        raw = load_yaml(path)
        if not raw:
            raw = load_yaml("config/receivables.example.yaml")

        intents: list[ActionIntent] = []
        today = date.today()
        for item in raw.get("receivables", []):
            if str(item.get("status", "open")).lower() != "open":
                continue
            due = date.fromisoformat(str(item["due_date"]))
            if due > today and not item.get("collect_before_due", False):
                continue
            intents.append(ActionIntent(
                action_type="collection",
                amount=float(item["amount"]),
                connector=str(item.get("connector", "stripe")),
                target=str(item["id"]),
                description=str(item.get("description") or item.get("name") or item["id"]),
                requires_approval=bool(item.get("requires_approval", True)),
                metadata={
                    "currency": str(item.get("currency", "USD")),
                    "customer_label": item.get("customer_label"),
                    "due_date": due.isoformat(),
                },
            ))
        return intents
