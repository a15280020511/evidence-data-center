# NOAA Climate Data Online (CDO) v2

This provider supplements the existing keyless NOAA/NCEI China historical-data connectors.

## Secret

- GitHub Actions Secret: `NOAA_CDO_TOKEN`
- Upstream request header: `token`
- The token is injected only in the backend runtime and is never written to tickets, logs, snapshots or Artifacts.

## Fixed read-only operations

- `catalog-capabilities`: local capability contract
- `datasets`: dataset discovery
- `datatypes`: weather-variable discovery
- `stations`: station discovery inside the configured China geographic envelope
- `data`: one bounded historical observation request

## Operating limits

- official host only: `www.ncei.noaa.gov`
- one upstream GET per ticket
- no redirects, retries or automatic pagination
- maximum 1,000 rows per request
- CDO official token quota: 5 requests/second and 10,000 requests/day
- GHCND data requests: maximum one year per ticket
- GSOM/GSOY requests: maximum ten years per ticket
- station discovery extent must remain inside China
- data operation accepts only `CH`-prefixed Chinese stations

The CDO layer is intended for dataset, variable, station and coverage discovery plus small validation queries. Long-period China station downloads continue to use the existing NCEI Access Data Service connectors.

The initial China validation target is Fuzhou WMO station `58847`, represented in NCEI station identifiers as `CHM00058847` and in CDO GHCND requests as `GHCND:CHM00058847`.
