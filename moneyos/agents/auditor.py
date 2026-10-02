from __future__ import annotations

from ..models import ExecutionResult


class AuditorAgent:
    def summarize(self, results: list[ExecutionResult]) -> dict:
        counts = {"planned": 0, "blocked": 0, "executed": 0, "failed": 0}
        for result in results:
            counts[result.status] = counts.get(result.status, 0) + 1
        return {
            "counts": counts,
            "results": [
                {
                    "status": r.status,
                    "action_type": r.intent.action_type,
                    "amount": r.intent.amount,
                    "target": r.intent.target,
                    "connector": r.intent.connector,
                    "message": r.message,
                    "external_id": r.external_id,
                }
                for r in results
            ],
        }
