# Global Landslide Catalog: findings

Source: NASA Global Landslide Catalog export. 11,033 events, 1988-11-07 to 2017-09-28, 140 countries.
Everything below was computed from the cleaned tables in `data/` and reconciles to the raw file (row count, deaths, injuries and fatal-event count all match exactly).

## Read this first: what this catalog is, and is not

It is a collection of **reported** landslides (news, agencies, user submissions), not a census. Counts show where landslides were reported and recorded, not where they happen most. Four biases shape every chart:

1. **Coverage starts in 2007.** Only 45 events are older than 2007. Years 2007 and 2017 are partial (2017 ends 28 Sep), so trend charts use complete years only.
2. **One US source dominates.** Oregon DOT supplies 768 records (21.3% of US events). Official agency records show a fatal-event rate of 0.1%, versus about 28% for news-sourced events. This pulls down US, "road-related" and North America fatality figures.
3. **Fatality counts are missing for 12.6% of events**, injuries for 51.4%, and setting is unknown for 57.6%.
4. **Deaths are extremely concentrated** (see 5 below), so means mislead; the report uses medians, totals with and without outliers, and rates.

## Headline findings

1. **Scale.** 11,033 events caused 31,061 reported deaths and 4,029 injuries. 2,442 events (25.3% of those with a reported count) killed at least one person. The median event killed nobody.
2. **No evidence of rising frequency.** Yearly events rose from 412 (2007) to 1,536 (2010), then stayed flat: the 2010-2016 trend is -28 events a year (R² 0.06, p = 0.585). The early climb reflects the catalog being built up, not more landslides.
3. **Seasonality is strong.** July is the peak month (1,293 events); July and August together are 22% of events. 89% of events are in the Northern Hemisphere. Using hemisphere-adjusted seasons, summer has 50% more events than the average of the other three seasons.
4. **Water drives it.** Rainfall is the trigger for 73.9% of events; adding tropical cyclones and flooding, 94.3% of events with a known trigger are water-driven. Earthquakes and volcanoes account for only 0.8% of events, but they average 5.06 deaths each. Tropical cyclones peak August to October.
5. **Deaths are concentrated.** The 3 deadliest events (Kedarnath, India 2013: 5,000; Abi Barik, Afghanistan 2014: 2,100; Zhouqu, China 2010: 1,765) are 28.5% of all deaths. The top 10 are 37.4%. The top 1% of events with a reported count cause 60.8%. Only 33 events killed 100 or more.
6. **Size is the clearest physical driver of deadliness.** Fatal-event rate climbs with size: small 8%, medium 32%, large 61%, very large 72%. Large or bigger events are 7.7% of events but 69% of deaths.
7. **Geography is concentrated.** The top 5 countries hold 62.0% of events and the top 10 hold 74.1%. United States 3,604, India 1,503, Philippines 728, Nepal 549, China 459.
8. **Deadliest countries.** India 7,264 deaths, China 5,099, Afghanistan 2,344 (from only 16 events), Philippines 1,856, Indonesia 1,791, Brazil 1,765. China averages 11.11 deaths per event, India 4.83, the United States 0.03.
9. **Setting.** Road-related landslides are 30% of events but have a 4.0% fatal rate (mostly the Oregon DOT effect); built-environment settings such as mines and retaining walls have 48.1%. Human-activity triggers (mining, construction, leaking pipes, dam collapse) have the highest fatal rate of any trigger group at 66.8%.
10. **Hotspots.** Top one-degree cells outside the Oregon DOT cluster: Niteroi/Rio de Janeiro (126 events, 496 deaths), Baguio, Philippines (123, 527), Ramban, Jammu and Kashmir (113), Baglung, Nepal (100).

## India

- 1,503 events, 7,264 deaths. Uttarakhand has 5,280 of them (205 events), almost all from Kedarnath in June 2013.
- **73.2% of events fall in June to September**, the southwest monsoon. Rainfall is the trigger for 88% of events.
- Most events: Jammu and Kashmir 259, Uttarakhand 205, Himachal Pradesh 175, Assam 102, Nagaland 95.
- **Maharashtra:** 77 events, 276 deaths; 92% in June to September. The largest is the 30 July 2014 landslide (151 deaths).
- South Asia total: 2,433 events and 12,905 deaths across 7 countries.

## Associations and prediction

- Cramer's V (strength of association, 0 to 1) with "event caused a death": setting 0.444, continent 0.448, size 0.333, trigger group 0.174.
- Size rank and deaths: Spearman rho = 0.35.
- A logistic model using size, trigger, setting, category, continent and location precision predicts whether an event is fatal with a cross-validated AUC of 0.85. **Most of that skill comes from reporting differences** (continent and road-related setting), so do not read it as a hazard model.
- Fatal-event rate rises with the population of the administrative area: 20.1% under 100k people, 38.2% for 100k to 1M, 47.1% for 1M to 10M (the over-10M band has only 22 events).
- Event counts differ by weekday (more on Monday, Tuesday and Sunday, fewer on Friday and Saturday). This is a news-reporting rhythm, not geology.

## Data quality log

- Dates are US format (MM/DD/YYYY); all 11,033 parsed. `event_time` is empty in every row.
- **Country was missing for 1,562 rows** (almost all added in 2016-2017). 580 were recovered from the location text, 954 from the nearest labelled events, 28 stay "Unknown". In a leave-one-out test the nearest-events method was right 98.5% of the time. Every row carries a `country_source` flag, so you can exclude estimates with one filter.
- 1,291 missing state/province values were filled the same way (flag: `admin_source`).
- Standardised: Czech Republic/Czechia, Myanmar, North Macedonia, Eswatini, Timor-Leste, DR Congo, Congo; Namibia's code "NA" is protected from being read as null; Indian state names lost diacritics (Nagaland, Meghalaya, Arunachal Pradesh) and "Kashmir", "Bengal" and "NCT" were mapped to Jammu and Kashmir, West Bengal and Delhi.
- Flagged, not removed: 166 possible duplicates (same date and location), 90 rows imported as "test", 10 rows submitted before the event date.
- 25.8% of locations are accurate only to more than 10 km or unknown, so fine-grained spatial analysis (under 10 km) is unreliable. Use the `high_precision_flag` for it.
- Median delay between event and submission to the catalog: 407 days overall, down to 45 days in 2016. Recent months are therefore still being filled in.
