# BRS API integration

## Security
- The API key is never stored in source code.
- Runtime configuration uses `BRS_API_KEY`.
- Do not print the key or include it in logs, fixtures, screenshots, or commits.
- Use a GitHub Actions / deployment secret named `BRS_API_KEY`.

## Data flow

`BRS API -> raw market snapshot -> option/underlying feature extraction -> Decision Engine`

The option scanner keeps the following targets together for comparative analysis:

- ضملی7070
- ضملی7071
- ضخود8059
- فملی
- خودرو

Snapshots should retain the source timestamp so intraday changes in price, volume, order-book depth and open interest can be compared without look-ahead bias.
