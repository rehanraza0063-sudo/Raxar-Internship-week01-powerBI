# Build the report in Power BI Desktop (about 30 minutes)

You need Power BI Desktop (free, Windows). The data is already cleaned, so there is no transformation work.

## 1. Load the data

1. Copy the `data` folder somewhere stable, for example `C:\Users\Rehan\Documents\landslide-powerbi\data\`.
2. Open Power BI Desktop > **Transform data** > Power Query Editor opens.
3. **Home > Manage Parameters > New Parameter.** Name `DataFolder`, Type Text, Current value = your folder path **ending with a backslash**.
4. For each block in `03_power_query.m` (one per table): **New Source > Blank Query > Advanced Editor**, paste the block, rename the query to the name in its heading comment (`fact_landslides`, `dim_date`, and so on).
   - Or the quick route: **Get data > Text/CSV** for each file, then in Power Query set each column's type. The M route is better because it fixes dates and decimals with the `en-US` culture. This matters: a Power BI set to an Indian or UK region can read some date strings the wrong way round.
5. **Close & Apply.**

`data_quality_log` is optional; load it if you want a data-notes table on page 9.

## 2. Model (Model view)

Create these relationships (many-to-one, single direction, dimension filters fact):

| From (fact_landslides) | To |
|---|---|
| `event_date` | `dim_date[date]` |
| `country_name` | `dim_country[country_name]` |
| `trigger` | `dim_trigger[trigger]` |
| `size` | `dim_size[size]` |
| `category` | `dim_category[category]` |
| `setting` | `dim_setting[setting]` |

Then:

- Select `dim_date` > **Table tools > Mark as date table** > Date column = `date`.
- **Sort by column:** `dim_date[month_name]` by `month_num`; `dim_size[size]` by `size_rank`; `fact_landslides[month_name]` by `month_num`; `fact_landslides[fatality_band]` by `fatality_band_sort`.
- **Data categories:** `latitude` = Latitude, `longitude` = Longitude, `country_name` = Country/Region, `admin_division` = State or Province, `source_link` = Web URL.
- **Hide** from Report view: the columns on the fact table that duplicate a dimension (`trigger_group`, `category_group`, `setting_group`, `continent`, `subregion`, `month_name`, `quarter`), plus the `_flag`, `_sort` and `grid_*` columns. Use the dimension and date tables for axes and slicers.
- **Default summarisation:** set all numeric columns to "Don't summarize" except through measures.

## 3. Measures

Create the `_Measures` table and paste each measure from `02_measures.dax`. Format: `%` measures as Percentage with 1 decimal; `Events`, `Fatalities` and `Injuries` as Whole number with thousands separator.

**Check your work:** compare against `06_expected_values.csv`. If a card disagrees with the expected value for the same filter, a relationship or type is wrong. The most common cause is a date column loaded as text.

## 4. Theme and pages

1. **View > Themes > Browse for themes** > pick `05_theme.json`.
2. Build the 11 pages in `04_report_pages.md`. Each page lists the visuals, the fields and what to look for.
3. **View > Page view > Fit to page**, and use the same slicer panel (copy the slicer group with Ctrl+C / Ctrl+V on each page, or **View > Sync slicers**).

## 5. Tips

- Turn on **Edit interactions** for the KPI cards so they react to every slicer but not to each other.
- For maps, if Bing maps are blocked by your organisation's settings, use the Filled map on `country_name` or switch the bubble map to a scatter chart of `longitude` vs `latitude`.
- Add a **bookmark** named "Exclude estimated countries" that sets slicer `country_source` = Original, to see results using only the originally labelled rows.
- Publish to the Power BI service if you want to share it. The `data` folder must then be reachable by a gateway, or switch to importing a copy.
