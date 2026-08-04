# NOAA official-data integration

This package exposes seven read-only NOAA capabilities through the Intelligence Center gateway.

- NWS point-to-grid resolution
- NWS period forecast
- NWS hourly forecast
- NWS gridpoint station discovery
- NWS latest station observation
- NWS active alerts
- NCEI historical weather/climate data discovery

No NOAA secret is required. All endpoints are fixed to official HTTPS hosts, use conservative gateway rate limits, forbid arbitrary URLs, and remain isolated from the compute and expert repositories.

Official references:

- `https://www.weather.gov/documentation/services-web-api`
- `https://api.weather.gov/openapi.json`
- `https://www.ncei.noaa.gov/support/access-search-service-api-user-documentation`

The NWS API primarily covers the United States and NWS service areas. NCEI coverage depends on the selected dataset and can be global.
