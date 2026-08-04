# NOAA/NCEI China historical-weather integration

This package intentionally excludes U.S.-only NWS forecast, observation, and alert endpoints.

It exposes four read-only China historical-data capabilities:

- discover NCEI records and CH-prefixed stations inside a fixed China bounding box;
- retrieve daily station observations from `daily-summaries`;
- retrieve monthly summaries from `global-summary-of-the-month`;
- retrieve yearly summaries from `global-summary-of-the-year`.

No NOAA key is required. Data retrieval is limited to one to ten CH-prefixed station identifiers, JSON output, metric units, fixed official HTTPS hosts, and bounded ticket execution. NCEI coverage is global-source archival coverage and is not equivalent to the complete China Meteorological Administration station network.

Official references:

- `https://www.ncei.noaa.gov/access/search/documentation/data-service/`
- `https://www.ncei.noaa.gov/access/search/documentation/search-service/`
- `https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily`
