# BabiMind Source Confidence

Confidence is operational trust, not truth probability.

| Source | Status | Confidence | Tier | Primary Eligible |
|---|---|---:|---|---|
| IMF Data API | ok | 0.600 | C | no |
| World Bank API | ok | 0.600 | C | no |
| ECB Data API | ok | 0.600 | C | no |
| FRED | ok | 0.600 | C | no |
| EIA | ok | 0.600 | C | no |
| World Gold Council | ok | 0.600 | C | no |
| CFTC | ok | 0.600 | C | no |
| FAOSTAT | ok | 0.600 | C | no |
| WHO | ok | 0.600 | C | no |
| LBMA | ok | 0.540 | C | no |
| UNCTAD | ok | 0.540 | C | no |
| IMF SDMX Central | error | 0.060 | D | no |
| BIS | error | 0.060 | D | no |
| OECD | error | 0.060 | D | no |
| IEA | error | 0.060 | D | no |
| SEC EDGAR | error | 0.060 | D | no |
| UN Comtrade | error | 0.060 | D | no |
| ILO | error | 0.060 | D | no |
| Reuters | error | 0.060 | D | no |
| USGS Minerals | error | 0.045 | D | no |

## Routing

Primary selection uses the highest-confidence healthy source in each topic/type group; lower-confidence sources remain fallbacks.
- **official/api** → primary: `IMF Data API`; fallback: World Bank API, ECB Data API, EIA
- **official/site** → primary: `FRED`; fallback: CFTC, WHO, UNCTAD
- **industry/report** → primary: `World Gold Council`; fallback: -
- **market/site** → primary: `LBMA`; fallback: -
- **trusted-news** → primary: `Reuters`; fallback: -
