# Copernicus Marine Provider

Managed access to the officially supported Copernicus Marine Toolbox.

## Operations

- `catalog-capabilities`: local contract.
- `describe`: bounded anonymous catalogue search and compact metadata output.
- `subset-csv`: credentialed, tightly bounded spatial/temporal/variable subset exported as CSV.

## Safety

- No `get`/whole-dataset download.
- No arbitrary dataset loops, file filters, output paths or service URLs.
- At most one high-level Toolbox operation per ticket.
- Subset bounding box span is at most 2 degrees, time span at most 7 days, depth span at most 500 m, variables at most 5, and output at most 20 MB.
- Credentials are backend-only GitHub Secrets.

## Required secrets for subset

- `COPERNICUSMARINE_SERVICE_USERNAME`
- `COPERNICUSMARINE_SERVICE_PASSWORD`
