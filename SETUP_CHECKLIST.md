# MoneyOS Setup Checklist

MoneyOS is already committed in dry-run mode. Complete these steps before any real financial data or live execution.

## 1. Make the repository private

This repository is currently public. Change its visibility to **Private** before adding any account credentials.

The GitHub Action intentionally refuses to run while the repository is public.

## 2. Configure your policy

Copy:

```text
config/policy.example.yaml -> config/policy.yaml
```

Choose these values:

- minimum cash reserve
- reserve target
- maximum single payment
- maximum daily payments
- maximum single trade
- maximum daily trades
- manual approval threshold
- percentage for reserve
- percentage for long-term investing
- percentage for speculation
- percentage left flexible
- investment symbols and weights
- allowed crypto symbols

Keep all `allow_live_*` flags set to `false` during testing.

## 3. Connect bank observation with Plaid

GitHub Actions secrets:

```text
PLAID_CLIENT_ID
PLAID_SECRET
PLAID_ACCESS_TOKENS
```

`PLAID_ACCESS_TOKENS` can contain multiple tokens separated by commas.

The first Transactions sync only establishes a cursor. Historical deposits are not treated as newly received money. Later runs can detect newly posted inflows automatically.

## 4. Connect collections with Stripe

Secret:

```text
STRIPE_SECRET_KEY
```

Receivables live in:

```text
config/receivables.yaml
```

MoneyOS can create idempotent Stripe payment links for eligible collection intents after live collections are explicitly enabled.

## 5. Connect long-term investing

For the initial implementation, use an Alpaca paper account first.

Secrets:

```text
ALPACA_API_KEY
ALPACA_API_SECRET
```

Variable:

```text
ALPACA_PAPER=true
```

Only switch paper mode off after reconciliation and guardrail testing.

## 6. Connect crypto/speculation

Secrets:

```text
CRYPTO_API_KEY
CRYPTO_API_SECRET
CRYPTO_API_PASSPHRASE
```

Variable example:

```text
CRYPTO_EXCHANGE=coinbase
```

Use an API key that can trade but **cannot withdraw funds** whenever the exchange supports separate permissions.

## 7. Add real obligations and receivables

Copy:

```text
config/obligations.example.yaml -> config/obligations.yaml
config/receivables.example.yaml -> config/receivables.yaml
```

Do not commit files containing sensitive account credentials or identity data.

## 8. Test from GitHub

Once the repository is private and secrets are configured, open an issue titled:

```text
[MoneyOS] Run
```

The Action will:

1. run tests
2. read configured accounts
3. detect new inflows
4. build a routing plan
5. prepare collections, payments, investments, and speculation intents
6. apply guardrails
7. run only what the execution policy permits
8. upload the private runtime artifact
9. comment a summary on the triggering issue

## 9. Live rollout order

Use this sequence:

1. observation only
2. automatic inflow detection
3. dry-run routing
4. Stripe collections
5. paper investing
6. small live investing
7. small crypto allocation
8. provider-specific bill-payment connectors
9. autonomous routine execution

Do not enable all live flags at once.

## Payment execution note

The current code intentionally does not pretend that one universal payment API can pay every bill. Payment execution needs a supported rail for the specific account/provider. We can add an approved Plaid Transfer integration or provider-specific connectors as each rail becomes available.
