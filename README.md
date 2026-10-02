# MoneyOS

MoneyOS is a policy-driven financial automation framework. It is designed to observe money, route new cash, prepare obligations, automate long-term investing, isolate speculative capital, and keep an auditable record of every proposed or executed action.

**Default behavior is dry-run.** Nothing should move unless live execution is explicitly enabled, credentials exist, policy allows the action, and guardrails pass.

## Architecture

```text
Banks / loans / processors / brokerages / crypto
                  |
             ObserverAgent
                  |
            current snapshot
                  |
              MoneyRouter
      obligations -> reserve -> investing -> speculation
                  |
               intents
                  |
              Guardrails
       caps / kill switch / approval threshold
                  |
      PayAgent / InvestAgent / StrategyAgent
                  |
               Auditor
```

## Included connectors

- Plaid: read bank balances; optional liabilities retrieval.
- Stripe: read processor balances for revenue visibility.
- Alpaca: brokerage account read + order submission capability.
- CCXT: crypto account read + generic exchange order capability.

Payment execution is intentionally connector-based because bill-pay/ACH access depends on the provider and account type. Plaid Transfer can be added when the account and production access support it; it is not assumed to be a universal personal bill-pay rail.

## First run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config/policy.example.yaml config/policy.yaml
cp config/obligations.example.yaml config/obligations.yaml
python -m moneyos.cli run
```

Then inspect:

```text
runtime/latest.json
runtime/latest.md
runtime/audit.json
```

## GitHub Actions

The workflow can be triggered manually or by opening an issue titled:

```text
[MoneyOS] Run
```

That makes it possible for ChatGPT to request a run through GitHub. The workflow refuses to process financial data while the repository is public.

## Required setup

### Repository

Make this repository **private before connecting real accounts**.

### GitHub Actions secrets

Add only the integrations you use:

```text
PLAID_CLIENT_ID
PLAID_SECRET
PLAID_ACCESS_TOKENS      # comma-separated access tokens
STRIPE_SECRET_KEY
ALPACA_API_KEY
ALPACA_API_SECRET
CRYPTO_API_KEY
CRYPTO_API_SECRET
CRYPTO_API_PASSPHRASE   # only if your exchange requires it
```

### GitHub Actions variables

```text
PLAID_ENV=development
MONEYOS_EXECUTION_MODE=dry_run
MONEYOS_KILL_SWITCH=false
ALPACA_PAPER=true
CRYPTO_EXCHANGE=coinbase
```

Do not put secrets in files, commits, issues, screenshots, or chat messages.

## Going live

The recommended rollout is:

1. **Observe only** — connect accounts and compare MoneyOS snapshots to provider portals.
2. **Dry-run routing** — MoneyOS decides what it would pay/invest, but moves nothing.
3. **Paper investing** — Alpaca paper account and/or exchange sandbox.
4. **Limited live execution** — enable one connector at a time with small caps.
5. **Autonomous routine actions** — only after repeated reconciliation tests pass.

The policy file includes a kill switch, single-action caps, daily caps, approval thresholds, and separate flags for payments, investing, and speculation.

## Current boundary

MoneyOS contains the orchestration, policy engine, bank/revenue/broker/crypto adapters, GitHub trigger, tests, audit log, and safety controls. Real payment execution still requires a supported payment rail (for example an approved Plaid Transfer integration or a provider-specific API) plus its authorization/credentials.
