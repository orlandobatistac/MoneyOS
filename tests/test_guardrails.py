from moneyos.models import ActionIntent
from moneyos.policy import Guardrails


def test_dry_run_never_executes():
    g = Guardrails({"execution": {"mode": "dry_run", "kill_switch": False}})
    r = g.check(ActionIntent("payment", 50, connector="manual"))
    assert r.status == "planned"
    assert "no money moved" in r.message.lower()


def test_kill_switch_blocks_everything():
    g = Guardrails({"execution": {"mode": "live", "kill_switch": True}})
    r = g.check(ActionIntent("investment", 10, connector="alpaca"))
    assert r.status == "blocked"
