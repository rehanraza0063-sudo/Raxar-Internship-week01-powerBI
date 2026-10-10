# Global Landslide Catalog: Power BI analysis kit

Start with `FINDINGS.md` (what the data says and how far to trust it), then `powerbi/01_BUILD_GUIDE.md` (build the report in about 30 minutes).

| Folder / file | What it is |
|---|---|
| `FINDINGS.md` | All findings with numbers, the biases to know about, and the data-quality log |
| `data/` | Cleaned star schema: `fact_landslides` (11,033 rows, 60 columns) and 6 dimension tables, plus `dim_date` and a quality log |
| `powerbi/01_BUILD_GUIDE.md` | Load, model, measures, theme, steps |
| `powerbi/02_measures.dax` | 50+ DAX measures (counts, rates, time intelligence, seasonality, outliers, Pareto, India, data quality) |
| `powerbi/03_power_query.m` | Power Query code for every table (fixes the US date format trap) |
| `powerbi/04_report_pages.md` | 11 report pages: visuals, fields and what to look for |
| `powerbi/05_theme.json` | Colour-blind-checked theme |
| `powerbi/06_expected_values.csv` | Numbers your measures should return, to check your model |
| `previews/` | Images of 10 pages with the real numbers |
| `scripts/` | Python used to clean the data, run the analysis and draw previews (re-runnable) |

Not included: a finished `.pbix`. That file can only be made inside Power BI Desktop. The DAX and report pages have not been run in Desktop, so use `06_expected_values.csv` to check them.
