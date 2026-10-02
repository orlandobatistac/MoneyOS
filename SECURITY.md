# Security

MoneyOS handles financial metadata and must be treated as sensitive infrastructure.

- Keep the repository private before real use.
- Store credentials only in GitHub Actions Secrets or a dedicated secret manager.
- Never commit access tokens, API keys, bank account numbers, passwords, tax IDs, or raw identity documents.
- Use least-privilege API keys. Prefer read-only keys for Observer connectors.
- Use paper/sandbox environments before live trading.
- Keep `MONEYOS_EXECUTION_MODE=dry_run` until reconciliation tests pass.
- Use `MONEYOS_KILL_SWITCH=true` to stop live actions immediately.
- Rotate any secret that appears in logs, screenshots, issues, or commits.
