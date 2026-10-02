from __future__ import annotations

from ..models import ActionIntent, Allocation, Obligation, Plan


class MoneyRouter:
    def __init__(self, policy: dict) -> None:
        self.policy = policy

    def build_plan(self, *, cash_balance: float, incoming_amount: float,
                   obligations: list[Obligation]) -> Plan:
        routing = self.policy.get("routing", {})
        reserve_floor = float(routing.get("minimum_cash_reserve", 0))
        available = max(0.0, cash_balance + incoming_amount - reserve_floor)
        allocations: list[Allocation] = []
        intents: list[ActionIntent] = []
        warnings: list[str] = []

        for obligation in sorted(obligations, key=lambda x: (x.due_date, x.priority)):
            if obligation.amount <= 0:
                continue
            amount = min(available, obligation.amount)
            if amount <= 0:
                warnings.append(
                    f"Insufficient allocatable cash for {obligation.name} due {obligation.due_date}."
                )
                continue
            allocations.append(
                Allocation("obligations", round(amount, 2), f"{obligation.name} due {obligation.due_date}")
            )
            intents.append(ActionIntent(
                action_type="payment",
                amount=round(amount, 2),
                connector=obligation.payment_connector,
                target=obligation.id,
                description=f"Pay {obligation.name}",
                requires_approval=not obligation.autopay,
                metadata={"due_date": obligation.due_date.isoformat(), "priority": obligation.priority},
            ))
            available -= amount
            if amount < obligation.amount:
                warnings.append(
                    f"Only {amount:.2f} of {obligation.amount:.2f} allocated to {obligation.name}."
                )

        split = routing.get("post_obligation_split", {})
        for bucket in ("reserve", "investing", "speculation", "flexible"):
            pct = float(split.get(bucket, 0))
            amount = round(max(0.0, available * pct), 2)
            if amount > 0:
                allocations.append(Allocation(bucket, amount, f"{pct:.0%} of post-obligation cash"))

        invest_total = sum(a.amount for a in allocations if a.bucket == "investing")
        for item in self.policy.get("investing", {}).get("symbols", []):
            amount = round(invest_total * float(item.get("weight", 0)), 2)
            if amount > 0:
                intents.append(ActionIntent(
                    action_type="investment",
                    amount=amount,
                    connector="alpaca",
                    target=item.get("symbol"),
                    description=f"Invest in {item.get('symbol')}",
                    requires_approval=True,
                ))

        return Plan.now(
            cash_balance=cash_balance,
            incoming_amount=incoming_amount,
            allocations=allocations,
            intents=intents,
            warnings=warnings,
        )
