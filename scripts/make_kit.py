"""Generate Power Query M, expected-values table and FINDINGS.md from the cleaned data.
Usage: python make_kit.py <data_dir> <kit_dir> <raw_csv>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA, KIT, RAW = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
(KIT / "powerbi").mkdir(parents=True, exist_ok=True)
f = pd.read_csv(DATA / "fact_landslides.csv", low_memory=False, keep_default_na=False, na_values=[""])
raw = pd.read_csv(RAW, low_memory=False)
R = json.load(open(Path(sys.argv[1]).parent / "results.json"))

# ------------------------------------------------------------------ Power Query M (one query per table)
def mtype(s, col):
    if col in ("event_date", "year_month", "submitted_date", "date"):
        return "type date"
    if col == "event_datetime":
        return "type datetime"
    if pd.api.types.is_numeric_dtype(s):
        if col in ("latitude", "longitude", "grid_lat", "grid_lon", "nearest_place_km"):
            return "type number"
        nn = s.dropna()
        return "Int64.Type" if (nn % 1 == 0).all() else "type number"
    return "type text"

parts = ["// LandslideWatch - Power Query (M). Paste each block into Home > Transform data > New Source > Blank Query > Advanced Editor.",
         "// Change DataFolder once, in the first query (parameter), and every other query follows it.",
         "", "// ===== Query: DataFolder (make this a Parameter: Manage Parameters > New, Type Text) =====",
         '"C:\\Users\\Rehan\\Documents\\landslide-powerbi\\data\\" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]', ""]
for name in ["fact_landslides", "dim_date", "dim_country", "dim_trigger", "dim_size", "dim_category", "dim_setting", "data_quality_log"]:
    df = pd.read_csv(DATA / f"{name}.csv", low_memory=False, keep_default_na=False, na_values=[""])
    types = ",\n        ".join(f'{{"{c}", {mtype(df[c], c)}}}' for c in df.columns)
    parts += [f"// ===== Query: {name} =====", "let",
              f'    Source   = Csv.Document(File.Contents(DataFolder & "{name}.csv"), [Delimiter = ",", Columns = {df.shape[1]}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
              "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
              "    // \"en-US\" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round",
              f"    Typed    = Table.TransformColumnTypes(Promoted, {{\n        {types}\n    }}, \"en-US\")",
              "in", "    Typed", ""]
(KIT / "powerbi" / "03_power_query.m").write_text("\n".join(parts), encoding="utf-8")

# ------------------------------------------------------------------ expected values for DAX self-check
rep = f[f.fatality_reported_flag == 1]
top3 = f.nlargest(3, "fatality_count").fatality_count.sum(); top10 = f.nlargest(10, "fatality_count").fatality_count.sum()
ev = [
    ("Events", "no filter", len(f)),
    ("Fatalities", "no filter", int(f.fatality_count.sum())),
    ("Injuries", "no filter", int(f.injury_count.sum())),
    ("Fatal Events", "no filter", int(f.fatal_event_flag.sum())),
    ("Events With Fatality Reported", "no filter", int(f.fatality_reported_flag.sum())),
    ("Countries", "no filter", int(f[f.country_name != "Unknown"].country_name.nunique())),
    ("Fatal Event Rate %", "no filter", round(100 * rep.fatal_event_flag.mean(), 1)),
    ("Fatalities per Event", "no filter", round(f.fatality_count.sum() / len(f), 2)),
    ("Median Fatalities (reported)", "no filter", float(rep.fatality_count.median())),
    ("Events", "year = 2010", int((f.year == 2010).sum())),
    ("Events", "country = India", int((f.country_name == "India").sum())),
    ("Fatalities", "country = India", int(f[f.country_name == "India"].fatality_count.sum())),
    ("Events", "country = United States", int((f.country_name == "United States").sum())),
    ("Events", "trigger group = Rainfall (dim_trigger)", int((f.trigger_group == "Rainfall").sum())),
    ("Large or Bigger Events", "no filter", int((f.size_rank >= 3).sum())),
    ("Fatalities excl Top 3 Events", "no filter", int(f.fatality_count.sum() - top3)),
    ("Top 10 Events Fatalities", "no filter", int(top10)),
    ("% Country Estimated", "no filter", round(100 * (f.country_source != "Original").mean(), 1)),
    ("% Fatality Reported", "no filter", round(100 * f.fatality_reported_flag.mean(), 1)),
    ("Possible Duplicates", "no filter", int(f.possible_duplicate_flag.sum())),
    ("Jun-Sep Share %", "country = India", round(100 * f[(f.country_name == "India")].month_num.isin([6, 7, 8, 9]).mean(), 1)),
    ("Maharashtra Events", "no filter", int(((f.country_name == "India") & (f.admin_division == "Maharashtra")).sum())),
    ("Events excl Oregon DOT", "no filter", int((f.source_name != "Oregon DOT").sum())),
]
ev = pd.DataFrame(ev, columns=["measure", "filter_context", "expected_value"])
ev["expected_value"] = ev["expected_value"].map(lambda v: f"{v:g}" if float(v) != int(v) else str(int(v)))
ev.to_csv(KIT / "powerbi" / "06_expected_values.csv", index=False, encoding="utf-8-sig")

# independent check against the RAW file (not the cleaned one)
chk = {"raw_rows": len(raw), "raw_fatalities": int(raw.fatality_count.sum()), "raw_injuries": int(raw.injury_count.sum()),
       "raw_fatal_events": int((raw.fatality_count > 0).sum())}
assert chk["raw_rows"] == len(f), "row count changed"
assert chk["raw_fatalities"] == int(f.fatality_count.sum()), "fatality total changed"
assert chk["raw_injuries"] == int(f.injury_count.sum()), "injury total changed"
assert chk["raw_fatal_events"] == int(f.fatal_event_flag.sum()), "fatal event count changed"
assert f.event_id.is_unique
print("RAW vs CLEAN reconciliation OK:", chk)

# ------------------------------------------------------------------ numbers for the findings text
core = f[f.core_period_flag == 1]
yy = core.groupby("year").size()
jl_au = core[core.month_num.isin([7, 8])].shape[0] / len(core)
large_pct_events = 100 * (f.size_rank >= 3).mean()
large_pct_deaths = 100 * f[f.size_rank >= 3].fatality_count.sum() / f.fatality_count.sum()
bysize = f[f["size"] != "Unknown"].groupby("size").apply(lambda d: 100 * d[d.fatality_reported_flag == 1].fatal_event_flag.mean())
tg = {r["trigger_group"]: r for r in R["trigger_group"]}
ct = {r["country_name"]: r for r in R["top_countries"]}
ctf = {r["country_name"]: r for r in R["top_countries_fatal"]}
ind = f[f.country_name == "India"]; mh = ind[ind.admin_division == "Maharashtra"]
ukd = ind[ind.admin_division == "Uttarakhand"]
road = {r["setting_group"]: r for r in R["setting"]}
sz = {r["size"]: r for r in R["size"]}
cm = core.groupby("month_num").size()
seas = core.groupby("season").size()
summer_more = 100 * (seas['Summer'] / seas.drop('Summer').mean() - 1)
n100 = int((f.fatality_count >= 100).sum())
md = f.groupby(["hemisphere"]).size()
pre = (f.core_period_flag == 0).sum()

findings = f"""# Global Landslide Catalog: findings

Source: NASA Global Landslide Catalog export. {len(f):,} events, {f.event_date.min()} to {f.event_date.max()}, {R['kpi']['countries']} countries.
Everything below was computed from the cleaned tables in `data/` and reconciles to the raw file (row count, deaths, injuries and fatal-event count all match exactly).

## Read this first: what this catalog is, and is not

It is a collection of **reported** landslides (news, agencies, user submissions), not a census. Counts show where landslides were reported and recorded, not where they happen most. Four biases shape every chart:

1. **Coverage starts in 2007.** Only {pre} events are older than 2007. Years 2007 and 2017 are partial (2017 ends 28 Sep), so trend charts use complete years only.
2. **One US source dominates.** Oregon DOT supplies {R['us_oregon']['oregon_dot']} records ({R['us_oregon']['oregon_share_of_us']}% of US events). Official agency records show a fatal-event rate of {100*R['fatal_by_source_group']['Official or agency']:.1f}%, versus about {100*R['fatal_by_source_group']['News and other media']:.0f}% for news-sourced events. This pulls down US, "road-related" and North America fatality figures.
3. **Fatality counts are missing for {100 - R['kpi']['fatality_reported_pct']:.1f}% of events**, injuries for {R['completeness']['injury_count']}%, and setting is unknown for {R['completeness']['setting unknown']}%.
4. **Deaths are extremely concentrated** (see 5 below), so means mislead; the report uses medians, totals with and without outliers, and rates.

## Headline findings

1. **Scale.** {len(f):,} events caused {R['kpi']['fatalities']:,} reported deaths and {R['kpi']['injuries']:,} injuries. {R['kpi']['fatal_events']:,} events ({R['kpi']['fatal_rate_pct_of_reported']}% of those with a reported count) killed at least one person. The median event killed nobody.
2. **No evidence of rising frequency.** Yearly events rose from {yy[2007]} (2007) to {yy[2010]:,} (2010), then stayed flat: the 2010-2016 trend is {R['trend_2010_2016']['slope']:+.0f} events a year (R² {R['trend_2010_2016']['r2']}, p = {R['trend_2010_2016']['p']}). The early climb reflects the catalog being built up, not more landslides.
3. **Seasonality is strong.** July is the peak month ({cm[7]:,} events); July and August together are {100*jl_au:.0f}% of events. {100*md['Northern']/len(f):.0f}% of events are in the Northern Hemisphere. Using hemisphere-adjusted seasons, summer has {summer_more:.0f}% more events than the average of the other three seasons.
4. **Water drives it.** Rainfall is the trigger for {tg['Rainfall']['share_pct']}% of events; adding tropical cyclones and flooding, {R['water_share_pct']}% of events with a known trigger are water-driven. Earthquakes and volcanoes account for only {tg['Earthquake and volcano']['share_pct']}% of events, but they average {tg['Earthquake and volcano']['fatalities_per_event']} deaths each. Tropical cyclones peak August to October.
5. **Deaths are concentrated.** The 3 deadliest events (Kedarnath, India 2013: 5,000; Abi Barik, Afghanistan 2014: 2,100; Zhouqu, China 2010: 1,765) are {R['fat_concentration']['top3_pct']}% of all deaths. The top 10 are {R['fat_concentration']['top10_pct']}%. The top 1% of events with a reported count cause {R['fat_concentration']['top1pct_events_share']}%. Only {n100} events killed 100 or more.
6. **Size is the clearest physical driver of deadliness.** Fatal-event rate climbs with size: small {bysize['Small']:.0f}%, medium {bysize['Medium']:.0f}%, large {bysize['Large']:.0f}%, very large {bysize['Very large']:.0f}%. Large or bigger events are {large_pct_events:.1f}% of events but {large_pct_deaths:.0f}% of deaths.
7. **Geography is concentrated.** The top 5 countries hold {R['conc_countries']['top5']}% of events and the top 10 hold {R['conc_countries']['top10']}%. United States {ct['United States']['events']:,}, India {ct['India']['events']:,}, Philippines {ct['Philippines']['events']}, Nepal {ct['Nepal']['events']}, China {ct['China']['events']}.
8. **Deadliest countries.** India {ctf['India']['fatalities']:,.0f} deaths, China {ctf['China']['fatalities']:,.0f}, Afghanistan {ctf['Afghanistan']['fatalities']:,.0f} (from only {ctf['Afghanistan']['events']} events), Philippines {ctf['Philippines']['fatalities']:,.0f}, Indonesia {ctf['Indonesia']['fatalities']:,.0f}, Brazil {ctf['Brazil']['fatalities']:,.0f}. China averages {ct['China']['fatalities_per_event']} deaths per event, India {ct['India']['fatalities_per_event']}, the United States {ct['United States']['fatalities_per_event']}.
9. **Setting.** Road-related landslides are {100*road['Road-related']['events']/len(f):.0f}% of events but have a {road['Road-related']['fatal_rate_pct']}% fatal rate (mostly the Oregon DOT effect); built-environment settings such as mines and retaining walls have {road['Built environment']['fatal_rate_pct']}%. Human-activity triggers (mining, construction, leaking pipes, dam collapse) have the highest fatal rate of any trigger group at {tg['Human activity']['fatal_rate_pct']}%.
10. **Hotspots.** Top one-degree cells outside the Oregon DOT cluster: Niteroi/Rio de Janeiro ({R['hotspots'][4]['events']} events, {R['hotspots'][4]['fatalities']:.0f} deaths), Baguio, Philippines ({R['hotspots'][5]['events']}, {R['hotspots'][5]['fatalities']:.0f}), Ramban, Jammu and Kashmir ({R['hotspots'][6]['events']}), Baglung, Nepal ({R['hotspots'][7]['events']}).

## India

- {len(ind):,} events, {int(ind.fatality_count.sum()):,} deaths. Uttarakhand has {int(ukd.fatality_count.sum()):,} of them ({len(ukd)} events), almost all from Kedarnath in June 2013.
- **{R['india_jjas_pct']}% of events fall in June to September**, the southwest monsoon. Rainfall is the trigger for {100*R['india_trigger']['Rainfall']/len(ind):.0f}% of events.
- Most events: Jammu and Kashmir {R['india_states'][0]['events']}, Uttarakhand {R['india_states'][1]['events']}, Himachal Pradesh {R['india_states'][2]['events']}, Assam {R['india_states'][3]['events']}, Nagaland {R['india_states'][4]['events']}.
- **Maharashtra:** {len(mh)} events, {int(mh.fatality_count.sum())} deaths; {100*mh.month_num.isin([6,7,8,9]).mean():.0f}% in June to September. The largest is the 30 July 2014 landslide (151 deaths).
- South Asia total: {sum(r['events'] for r in R['south_asia']):,} events and {sum(r['fatalities'] for r in R['south_asia']):,.0f} deaths across 7 countries.

## Associations and prediction

- Cramer's V (strength of association, 0 to 1) with "event caused a death": setting {R['assoc']['setting_group x fatal_event_flag']['cramers_v']}, continent {R['assoc']['continent x fatal_event_flag']['cramers_v']}, size {R['assoc']['size x fatal_event_flag']['cramers_v']}, trigger group {R['assoc']['trigger_group x fatal_event_flag']['cramers_v']}.
- Size rank and deaths: Spearman rho = {R['spearman_size_fatal']}.
- A logistic model using size, trigger, setting, category, continent and location precision predicts whether an event is fatal with a cross-validated AUC of {R['model_auc']}. **Most of that skill comes from reporting differences** (continent and road-related setting), so do not read it as a hazard model.
- Fatal-event rate rises with the population of the administrative area: {R['pop_band'][0]['fatal_rate']}% under 100k people, {R['pop_band'][1]['fatal_rate']}% for 100k to 1M, {R['pop_band'][2]['fatal_rate']}% for 1M to 10M (the over-10M band has only {R['pop_band'][3]['events']} events).
- Event counts differ by weekday (more on Monday, Tuesday and Sunday, fewer on Friday and Saturday). This is a news-reporting rhythm, not geology.

## Data quality log

- Dates are US format (MM/DD/YYYY); all {len(f):,} parsed. `event_time` is empty in every row.
- **Country was missing for 1,562 rows** (almost all added in 2016-2017). 580 were recovered from the location text, 954 from the nearest labelled events, 28 stay "Unknown". In a leave-one-out test the nearest-events method was right 98.5% of the time. Every row carries a `country_source` flag, so you can exclude estimates with one filter.
- 1,291 missing state/province values were filled the same way (flag: `admin_source`).
- Standardised: Czech Republic/Czechia, Myanmar, North Macedonia, Eswatini, Timor-Leste, DR Congo, Congo; Namibia's code "NA" is protected from being read as null; Indian state names lost diacritics (Nagaland, Meghalaya, Arunachal Pradesh) and "Kashmir", "Bengal" and "NCT" were mapped to Jammu and Kashmir, West Bengal and Delhi.
- Flagged, not removed: {R['flags']['duplicates']} possible duplicates (same date and location), {R['flags']['test']} rows imported as "test", {R['flags']['neg_lag']} rows submitted before the event date.
- {R['completeness']['location accuracy > 10 km or unknown']}% of locations are accurate only to more than 10 km or unknown, so fine-grained spatial analysis (under 10 km) is unreliable. Use the `high_precision_flag` for it.
- Median delay between event and submission to the catalog: {int(f.report_lag_days.median())} days overall, down to {R['lag_by_year']['2016']:.0f} days in 2016. Recent months are therefore still being filled in.
"""
(KIT / "FINDINGS.md").write_text(findings, encoding="utf-8")
print("kit docs written;", len(findings.split()), "words in FINDINGS")
