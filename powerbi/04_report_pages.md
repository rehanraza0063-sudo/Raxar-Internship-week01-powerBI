# Report pages (11)

Canvas 1280 x 720. Theme `05_theme.json`. Fields are `table[column]`; measures are in `[brackets]` (from `02_measures.dax`). The `previews/` folder shows what each page looks like with the real numbers.

**Slicer panel (pages 1-9):** `dim_date[year]` (between slider), `dim_country[continent]` (dropdown), `dim_trigger[trigger_group]` (dropdown), `dim_size[size]` (list), and `fact_landslides[country_source]` (list, default all). Sync them across pages.

---

## 1. Overview
**Question:** how big is the problem and where is it?
- 6 cards: `[Events]`, `[Fatalities]`, `[Injuries]`, `[Countries]`, `[Fatal Event Rate %]`, `[Median Report Lag (days)]`
- Map (bubble): Latitude `latitude`, Longitude `longitude`, Size `[Events]`, Legend `dim_trigger[trigger_group]`; Tooltips `event_title`, `[Fatalities]`
- Column: Axis `dim_date[year]`, Values `[Events]`; beside it a Line: Axis `dim_date[year]`, Values `[Fatalities]` (two charts, not one dual-axis chart, because the scales differ about 10 to 1)
- Bar: Axis `dim_country[country_name]`, Values `[Events]`, Top N = 10
- Text box: `[Data Note]`

## 2. Time trends
**Question:** is it getting worse?
- Line: Axis `dim_date[year_month]`, Values `[Events]` and `[Events Rolling 12M]`; filter `core_period_flag` = 1; add **Analytics > Forecast** (12 points, 95%) but label it "indicative only"
- Column: Axis `dim_date[year]`, Values `[Events Complete Years Only]`; add a **trend line** (Analytics pane); filter year 2007-2016
- Matrix heatmap: Rows `dim_date[year]`, Columns `dim_date[month_name]`, Values `[Events]`, background colour scale (white to `#0A4248`)
- Column: `[Events YoY %]` by `dim_date[year]`, year >= 2008
- Line: `[Monthly Z-Score]` by `dim_date[year_month]` with a constant line at 2 (months above it are unusual)
- Column: `[Events]` by `dim_date[day_of_week]` (sorted by `day_of_week_num`); add a note "reporting rhythm, not geology"
- **Look for:** the rise 2007-2010 then a flat line. That is catalog build-up, not a trend.

## 3. Seasonality
**Question:** when do landslides happen?
- Column (clustered): Axis `dim_date[month_name]`, Values `[Events]`, Legend `fact_landslides[hemisphere]`
- Column: `[Seasonality Index]` by `dim_date[month_name]`, constant line at 1
- Matrix: Rows `dim_date[month_name]`, Columns `dim_trigger[trigger_group]`, Values `[Events]`, colour scale
- Donut (or 100% bar): `[Events]` by `fact_landslides[season]`
- Card: `[Jun-Sep Share %]`
- **Look for:** July peak, tropical-cyclone bump in Aug-Oct, snow/freeze-thaw in winter.

## 4. Geography
**Question:** where are the hotspots?
- Filled map: Location `dim_country[country_name]`, Colour saturation `[Events]`
- Bar: `[Events]` and `[Fatalities per Event]` (two small bars, separate visuals) by `dim_country[country_name]`, Top 15
- Treemap: Group `dim_country[subregion]`, Values `[Events]`
- Line and clustered column (Pareto): Axis `dim_country[country_name]` Top 15, Columns `[Share of Events %]`, Line `[Cumulative Events %]`. Turn the secondary axis **off** (Format > Y axis > Secondary) so both use one 0 to 100% scale
- Table: `fact_landslides[grid_1deg]`, `[Events]`, `[Fatalities]`, `nearest_place` (first), Top 12 by `[Events]`: the one-degree hotspot cells
- **Look for:** the 5 biggest countries hold 62% of events; Pacific Northwest cells are a data-source effect (Oregon DOT).

## 5. Triggers and causes
**Question:** what sets them off?
- Bar: `[Events]` by `dim_trigger[trigger_group]`
- Bar: `[Events]` by `dim_trigger[trigger]` (detail), sorted descending
- Bar: `[Fatal Event Rate %]` and `[Fatalities per Event]` by `dim_trigger[trigger_group]` (two visuals side by side)
- 100% stacked bar: Axis `dim_trigger[trigger_group]`, Legend `dim_size[size]`, Values `[Events]`
- Table: `storm_name`, `[Events]`, `[Fatalities]`, `dim_country[country_name]`; filter `storm_name` is not blank; Top 10
- Line: `[Events]` by `dim_date[year]`, Legend `dim_trigger[trigger_group]`, trigger group filter = earthquake and volcano (small multiples optional)

## 6. Type, size and setting
**Question:** what kind of landslide is deadly?
- Column: `[Events]` by `dim_size[size]` (sorted by rank)
- Column: `[Fatal Event Rate %]` by `dim_size[size]`, Unknown excluded
- Bar: `[Events]` by `dim_category[category_group]`
- Bar: `[Events]` and `[Fatal Event Rate %]` by `dim_setting[setting_group]`
- Scatter: X `[Events]`, Y `[Fatalities per Event]`, Details `dim_category[category]`
- **Decomposition tree** (AI): Analyze `[Fatalities]`, Explain by `dim_trigger[trigger_group]`, `dim_setting[setting_group]`, `dim_size[size]`, `dim_country[continent]`
- **Look for:** fatal rate climbs steeply with size; road-related is high-count but low-fatality (Oregon DOT effect).

## 7. Fatalities and impact
**Question:** how concentrated is the harm?
- Cards: `[Fatalities]`, `[Fatalities excl Top 3 Events]`, `[Top 10 Share %]`, `[Large or Bigger Fatalities Share %]`
- Slicer: `'Outlier Switch'[Option]` (single select)
- Column: `[Fatalities (selected view)]` by `dim_date[year]`
- Column: `[Events]` by `fact_landslides[fatality_band]` (sorted by `fatality_band_sort`)
- Table: Top 15 `event_title`, `event_date`, `country_name`, `trigger`, `size`, `fatality_count`, `source_link` (Web URL button); Top N by `fatality_count`
- Scatter: X `[Events]`, Y `[Fatalities]`, Details `dim_country[country_name]`, log axes
- Bar: `[Injuries]` by `dim_country[country_name]` Top 10
- **Look for:** 2013 drops from 6,361 to 1,361 deaths when the top 3 events are excluded.

## 8. India focus
**Question:** how does India look, by state and month?
- Filter the whole page: `dim_country[country_name]` = India
- Cards: `[India Events]`, `[India Fatalities]`, `[Jun-Sep Share %]`, `[Maharashtra Events]`, `[Maharashtra Fatalities]`
- Map (filled, State or Province): Location `fact_landslides[admin_division]`, Saturation `[Events]`
- Bar: `[Events]` and `[Fatalities]` by `fact_landslides[admin_division]`, Top 15
- Column: `[Events]` by `dim_date[month_name]` (monsoon peak)
- Bar: `[Events]` by `dim_trigger[trigger_group]` and by `dim_setting[setting_group]`
- Table: top 8 deadliest, with `source_link`
- Bar: South Asia comparison: remove the India filter on a copy of this visual, filter `dim_country[subregion]` = South Asia
- Optional: a second page-level bookmark with `admin_division` = Maharashtra

## 9. Data quality and bias
**Question:** how far can I trust the numbers?
- Bar: `[% Fatality Reported]`, `[% Trigger Unknown]`, `[% Size Unknown]`, `[% Setting Unknown]`, `[% Country Estimated]`, `[% High Precision Location]` (a multi-row card works too)
- Donut: `[Events]` by `fact_landslides[source_group]`
- Bar: Top 10 `fact_landslides[source_name]` by `[Events]`
- Column: `[Median Report Lag (days)]` by `dim_date[year]`
- Column: `[Events]` by `fact_landslides[location_accuracy]`
- Cards: `[Possible Duplicates]`, `[Events excl Oregon DOT]`
- Table: `data_quality_log` (step, detail)
- Text box: "Counts show where landslides were reported, not where they occur most."

## 10. Drivers (AI visuals)
**Question:** what goes with a fatal landslide?
- **Key influencers:** Analyze `fatal_event_flag` (set the field to "Don't summarize", analyze as category: 1), Explain by `dim_size[size]`, `dim_setting[setting_group]`, `dim_trigger[trigger_group]`, `dim_category[category_group]`, `dim_country[continent]`, `fact_landslides[high_precision_flag]`, `fact_landslides[source_group]`
- **Decomposition tree** on `[Events]` by `dim_country[continent]` > `dim_trigger[trigger_group]` > `dim_size[size]`
- **Read with care:** continent and source group will rank high because of reporting differences (Oregon DOT records are rarely fatal), not because of geology. Size and trigger are the physical drivers.

## 11. Event detail (drill-through)
**Question:** what happened in this country or state?
- Drill-through field: `dim_country[country_name]`
- Table: `event_date`, `event_title`, `location_description`, `trigger`, `size`, `setting`, `fatality_count`, `injury_count`, `event_description_short`, `source_link`
- Cards: `[Events]`, `[Fatalities]`, `[Median Fatalities (reported)]`
- Back button
- Add a **tooltip page** (hidden, 320 x 240) showing `event_title`, `event_date`, `[Fatalities]`, and use it on the page-1 map.
