from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, UTC
from typing import Any, Literal


@dataclass
class AccountSnapshot:
    source: str
    account_id: str
    name: str
    kind: str
    balance: float
    currency: str = "USD"
    available: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Obligation:
    id: str
    name: str
    amount: float
    due_date: date
    priority: int = 100
    autopay: bool = False
    payment_connector: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Allocation:
    bucket: str
    amount: float
    reason: str


@dataclass
class ActionIntent:
    action_type: Literal["payment", "investment", "speculation", "transfer", "collection"]
    amount: float
    currency: str = "USD"
    connector: str = "manual"
    target: str | None = None
    description: str = ""
    requires_approval: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    status: Literal["planned", "blocked", "executed", "failed"]
    intent: ActionIntent
    message: str
    external_id: str | None = None


@dataclass
class Plan:
    generated_at: str
    cash_balance: float
    incoming_amount: float
    allocations: list[Allocation]
    intents: list[ActionIntent]
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def now(cls, *, cash_balance: float, incoming_amount: float,
            allocations: list[Allocation], intents: list[ActionIntent],
            warnings: list[str] | None = None) -> "Plan":
        return cls(
            generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            cash_balance=cash_balance,
            incoming_amount=incoming_amount,
            allocations=allocations,
            intents=intents,
            warnings=warnings or [],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
