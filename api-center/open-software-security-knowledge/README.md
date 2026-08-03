# Open Software Security Knowledge

Governed, public, read-only access to 18 fixed sources covering source-code history, package metadata, dependency graphs, licenses, vulnerabilities, defensive prioritization and open technical standards.

## Entry point

- Provider: `open-software-security-knowledge`
- Issue prefix: `[intel-software-security]`
- Operations: 11 fixed operations from `provider-catalog.json`

## Optional free credentials

- `SWH_API_TOKEN`: optional Software Heritage token for higher limits.
- `NVD_API_KEY`: optional NVD key for higher limits.

Anonymous access remains supported for both sources at lower limits.

## Prohibited

- arbitrary URLs, hosts, paths, headers or client credentials;
- package or source-code downloads, installation or execution;
- repository archival requests, vault jobs, vulnerability submissions or curation writes;
- exploit-code retrieval, attack execution or automated enforcement;
- automatic pagination, retries, redirects or background polling;
- cross-center direct calls. GPTs remains the sole relay.

Every production ticket performs at most one bounded upstream request and records response size, SHA-256, source rights and credential names without exposing credential values.
