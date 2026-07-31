# Miaoxiang managed provider

Read-only adapter for Dongfang Caifu Miaoxiang financial APIs.

## Repository Secret

- `MX_APIKEY`: Miaoxiang API key.

## Ticket prefix

`[api-mx]`

## Exposed operations

- `financial-search`: financial news, announcements, research, policy and market-event search.
- `financial-data`: market, valuation, capital-flow, financial statement and business-data query.
- `stock-screen`: natural-language stock screening.
- `catalog-capabilities`: local capability catalog; no upstream call and no key required.

The adapter does not expose watchlist mutation, simulated trading, order submission, cancellation, account funds, arbitrary URLs or arbitrary code. Secret values are never written to tickets, logs, comments or Artifacts.
