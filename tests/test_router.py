from datetime import date

from moneyos.agents.router import MoneyRouter
from moneyos.models import Obligation


def test_obligations_before_investing():
    policy = {
        "routing": {
            "minimum_cash_reserve": 100,
            "post_obligation_split": {
                "reserve": 0.5,
                "investing": 0.5,
                "speculation": 0,
                "flexible": 0,
            },
        },
        "investing": {
            "symbols": [
                {
                    "symbol": "VTI",
                    "weight": 1.0,
                }
            ]
        },
        "speculation": {
            "crypto_symbols": []
        },
    }

    router = MoneyRouter(policy)

    plan = router.build_plan(
        cash_balance=1000,
        incoming_amount=0,
        obligations=[
            Obligation(
                "bill",
                "Bill",
                200,
                date(
                    2026,
                    10,
                    2,
                ),
                priority=1,
            )
        ],
    )

    assert (
        plan.allocations[0].bucket
        == "obligations"
    )

    assert (
        plan.allocations[0].amount
        == 200
    )

    assert any(
        i.action_type
        == "investment"
        for i in plan.intents
    )


def test_speculation_creates_crypto_intents():
    policy = {
        "routing": {
            "minimum_cash_reserve": 0,
            "post_obligation_split": {
                "reserve": 0,
                "investing": 0,
                "speculation": 0.10,
                "flexible": 0.90,
            },
        },
        "investing": {
            "symbols": []
        },
        "speculation": {
            "crypto_symbols": [
                "BTC/USD",
                "ETH/USD",
            ]
        },
    }

    router = MoneyRouter(policy)

    plan = router.build_plan(
        cash_balance=1000,
        incoming_amount=0,
        obligations=[],
    )

    spec = [
        i
        for i in plan.intents
        if i.action_type
        == "speculation"
    ]

    assert len(spec) == 2

    assert sum(
        i.amount
        for i in spec
    ) == 100
