# Browserless managed API provider

Browserless is integrated as a bounded, read-only web-rendering provider.

- Ticket prefix: `[api-browserless]`
- Repository Secret: `BROWSERLESS_TOKEN`
- Fixed REST origin: `https://production-sfo.browserless.io`
- Operations: `catalog-capabilities`, `content`, `scrape`, `screenshot`, `pdf`, `performance`, `search`, `map`

The provider accepts only public HTTPS targets. It does not expose BrowserQL, BaaS/WebSocket sessions, `/function`, `/download`, `/export`, `/unblock`, profiles, arbitrary JavaScript, cookies, Authorization headers, custom headers, proxy configuration, geo-proxy configuration, form submission, or write operations.

`search` and `map` may require a Browserless Cloud plan. Actual quota, concurrency and availability are controlled by the Browserless account.
