# Scholarly index access configuration

The three requested scholarly indexes are registered as follows.

| Source | GitHub configuration name | Access mode |
|---|---|---|
| OpenAlex | `OPENALEX_API_KEY` | Required free API key; store as an Actions secret. |
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | Free API key; store as an Actions secret. Anonymous access remains possible at lower limits. |
| BASE | No API key | BASE approves the caller public egress IP. The HTTPS Search API is registered, while the HTTP-only OAI harvesting endpoint remains disabled. |

BASE live execution fails closed until BASE has approved a stable public egress IP used by the execution platform. Do not create a fake `BASE_API_KEY` secret.
