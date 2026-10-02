from __future__ import annotations


def markdown_report(result: dict) -> str:
    plan = result.get("plan", {})
    audit = result.get("audit", {})
    lines = [
        "# MoneyOS run",
        "",
        f"Generated: {plan.get('generated_at', 'unknown')}",
        f"Detected cash: ${plan.get('cash_balance', 0):,.2f}",
        f"Incoming amount used for planning: ${plan.get('incoming_amount', 0):,.2f}",
        "",
        "## Allocations",
    ]
    for a in plan.get("allocations", []):
        lines.append(f"- **{a['bucket']}**: ${a['amount']:,.2f} — {a['reason']}")
    if not plan.get("allocations"):
        lines.append("- None")

    lines += ["", "## Actions"]
    for r in audit.get("results", []):
        lines.append(
            f"- {r['status'].upper()}: {r['action_type']} ${r['amount']:,.2f} -> "
            f"{r.get('target') or '-'} ({r['message']})"
        )
    if not audit.get("results"):
        lines.append("- None")

    warnings = plan.get("warnings", [])
    if warnings:
        lines += ["", "## Warnings"] + [f"- {w}" for w in warnings]

    lines += [
        "",
        "> MoneyOS defaults to dry-run. A live action requires explicit policy flags, "
        "credentials, limits, and passing guardrails.",
    ]
    return "\n".join(lines) + "\n"
