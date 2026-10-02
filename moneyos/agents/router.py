from __future__ import annotations

from ..models import ActionIntent, Allocation, Obligation, Plan


class MoneyRouter:
    def __init__(self, policy: dict) -> None:
        self.policy = policy

    def build_plan(
        self,
        *,
        cash_balance: float,
        incoming_amount: float,
        obligations: list[Obligation],
    ) -> Plan:
        routing = self.policy.get(
            "routing",
            {},
        )

        reserve_floor = float(
            routing.get(
                "minimum_cash_reserve",
                0,
            )
        )

        available = max(
            0.0,
            cash_balance
            + incoming_amount
            - reserve_floor,
        )

        allocations: list[Allocation] = []
        intents: list[ActionIntent] = []
        warnings: list[str] = []

        for obligation in sorted(
            obligations,
            key=lambda x: (
                x.due_date,
                x.priority,
            ),
        ):
            if obligation.amount <= 0:
                continue

            amount = min(
                available,
                obligation.amount,
            )

            if amount <= 0:
                warnings.append(
                    (
                        "Insufficient allocatable cash "
                        f"for {obligation.name} due "
                        f"{obligation.due_date}."
                    )
                )
                continue

            allocations.append(
                Allocation(
                    "obligations",
                    round(amount, 2),
                    (
                        f"{obligation.name} "
                        f"due {obligation.due_date}"
                    ),
                )
            )

            intents.append(
                ActionIntent(
                    action_type="payment",
                    amount=round(
                        amount,
                        2,
                    ),
                    connector=(
                        obligation.payment_connector
                    ),
                    target=obligation.id,
                    description=(
                        f"Pay {obligation.name}"
                    ),
                    requires_approval=(
                        not obligation.autopay
                    ),
                    metadata={
                        "due_date": (
                            obligation.due_date
                            .isoformat()
                        ),
                        "priority": (
                            obligation.priority
                        ),
                    },
                )
            )

            available -= amount

            if amount < obligation.amount:
                warnings.append(
                    (
                        f"Only {amount:.2f} of "
                        f"{obligation.amount:.2f} "
                        f"allocated to "
                        f"{obligation.name}."
                    )
                )

        split = routing.get(
            "post_obligation_split",
            {},
        )

        for bucket in (
            "reserve",
            "investing",
            "speculation",
            "flexible",
        ):
            pct = float(
                split.get(
                    bucket,
                    0,
                )
            )

            amount = round(
                max(
                    0.0,
                    available * pct,
                ),
                2,
            )

            if amount > 0:
                allocations.append(
                    Allocation(
                        bucket,
                        amount,
                        (
                            f"{pct:.0%} of "
                            "post-obligation cash"
                        ),
                    )
                )

        invest_total = sum(
            a.amount
            for a in allocations
            if a.bucket == "investing"
        )

        for item in self.policy.get(
            "investing",
            {},
        ).get(
            "symbols",
            [],
        ):
            amount = round(
                invest_total
                * float(
                    item.get(
                        "weight",
                        0,
                    )
                ),
                2,
            )

            if amount > 0:
                intents.append(
                    ActionIntent(
                        action_type="investment",
                        amount=amount,
                        connector="alpaca",
                        target=item.get(
                            "symbol"
                        ),
                        description=(
                            "Invest in "
                            f"{item.get('symbol')}"
                        ),
                        requires_approval=True,
                    )
                )

        spec_total = sum(
            a.amount
            for a in allocations
            if a.bucket == "speculation"
        )

        crypto_symbols = self.policy.get(
            "speculation",
            {},
        ).get(
            "crypto_symbols",
            [],
        )

        if (
            spec_total > 0
            and crypto_symbols
        ):
            each = round(
                spec_total
                / len(crypto_symbols),
                2,
            )

            for symbol in crypto_symbols:
                if each > 0:
                    intents.append(
                        ActionIntent(
                            action_type=(
                                "speculation"
                            ),
                            amount=each,
                            connector="crypto",
                            target=symbol,
                            description=(
                                "Speculative "
                                f"allocation to {symbol}"
                            ),
                            requires_approval=True,
                            metadata={
                                "side": "buy",
                                "order_type": (
                                    "market"
                                ),
                            },
                        )
                    )

        return Plan.now(
            cash_balance=cash_balance,
            incoming_amount=incoming_amount,
            allocations=allocations,
            intents=intents,
            warnings=warnings,
        )
