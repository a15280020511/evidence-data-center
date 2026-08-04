# Reality Observation Provider

This managed provider exposes fixed, read-only reality-data operations for the Intelligence Center.

## Covered layers

- High-resolution and ground imagery metadata: Microsoft Planetary Computer/NAIP, Element84 Earth Search, OpenAerialMap, KartaView.
- Earth and disaster observation: NASA FIRMS, NASA EONET, CelesTrak.
- Ocean, aviation and geophysics: IOOS ERDDAP, AviationWeather.gov, EarthScope, NOAA NDBC and CO-OPS.
- Space weather and environmental sensors: NOAA SWPC, Safecast, openSenseMap.
- Footfall: City of Melbourne minute-level and historical pedestrian sensors.
- Power grids: NESO Carbon Intensity, Elexon, Fingrid and ENTSO-E.

## Safety and governance

- One bounded upstream request per ticket.
- Fixed official or public-interest hosts only.
- No arbitrary URL, browser script, device control, continuous stream, write operation or individual tracking.
- Credentials are injected only by GitHub Actions and are never written to artifacts.
- Community sensors are supporting evidence, not sole authority.
- There is no globally complete, recent, free, sub-meter overhead imagery API. NAIP is US-only; OpenAerialMap and KartaView depend on community coverage.

## Optional secrets

- `FIRMS_MAP_KEY`
- `FINGRID_API_KEY`
- `ENTSOE_API_TOKEN`
