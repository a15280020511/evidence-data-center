# Scholarly index access configuration

The three requested scholarly indexes are registered as follows.

| Source | GitHub configuration name | Access mode |
|---|---|---|
| OpenAlex | `OPENALEX_API_KEY` | Required free API key; store as an Actions secret. |
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | Free API key; store as an Actions secret. Anonymous access remains possible at lower limits. |
| BASE | `BASE_API_KEY` | Free BASE HTTP Interface key; injected only as the upstream `apikey` query parameter. |

Do not paste keys into tickets or task parameters. The runtime accepts no client-supplied credentials and injects each key only from its dedicated backend secret.
