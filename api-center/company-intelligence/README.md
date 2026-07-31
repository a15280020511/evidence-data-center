# Company Intelligence managed provider

Read-only adapter for the official Tianyancha open platform.

## Repository Secret

- `TIANYANCHA_API_TOKEN`: Tianyancha Open Platform Authorization token.

Secret values are injected only at runtime and are never written to tickets, logs, catalogs, comments, or Artifacts.

## Ticket prefix

`[api-company]`

Only public, non-personal business data is accepted. Direct contact and personal identity fields are removed from returned payloads. Qichacha is not registered or executable in the API center.
