# Company Intelligence managed providers

Read-only adapters for the official Qichacha and Tianyancha open platforms.

## Repository Secrets

- `QICHACHA_CREDENTIALS_JSON`: one JSON object containing `app_key` and `secret_key`.
- `TIANYANCHA_API_TOKEN`: the Tianyancha Open Platform Authorization token.

Secret values are injected only at runtime and are never written to tickets, logs, catalogs, comments, or Artifacts.

## Ticket prefix

`[api-company]`

The provider and operation are selected in the JSON ticket. Only public, non-personal business data is accepted. Direct contact and personal identity fields are removed from returned payloads.
