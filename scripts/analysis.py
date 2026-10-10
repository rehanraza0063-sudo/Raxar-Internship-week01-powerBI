"""All analyses on the cleaned fact table. Prints results and writes results.json."""
import json
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings("ignore")
f = pd.read_csv(sys.argv[1], low_memory=False, keep_default_na=False, na_values=[""])
R = {}
pd.set_option("display.width", 200)

def show(title, obj):
    print(f"\n=== {title} ===")
    print(obj.to_string() if hasattr(obj, "to_string") else obj)

# ---------------------------------------------------------------- A. overview
rep = f[f.fatality_reported_flag == 1]
R["kpi"] = dict(events=len(f), countries=int(f[f.country_name != "Unknown"].country_name.nunique()),
                fatalities=int(f.fatality_count.sum()), injuries=int(f.injury_count.sum()),
                fatal_events=int(f.fatal_event_flag.sum()), fatality_reported_pct=round(100 * f.fatality_reported_flag.mean(), 1),
                fatal_rate_pct_of_reported=round(100 * rep.fatal_event_flag.mean(), 1),
                mean_fatalities_per_reported=round(rep.fatality_count.mean(), 2), median_fatalities_reported=float(rep.fatality_count.median()),
                date_min=f.event_date.min(), date_max=f.event_date.max())
show("A. KPIs", pd.Series(R["kpi"]))

# ---------------------------------------------------------------- B. time
core = f[f.core_period_flag == 1]
yr = core.groupby("year").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum"), fatal_events=("fatal_event_flag", "sum"))
yr["yoy_pct"] = (yr.events.pct_change() * 100).round(1)
show("B1. Events by year (core 2007-2017; 2017 ends 28 Sep)", yr)
R["by_year"] = yr.reset_index().to_dict("records")

full = core[core.complete_year_flag == 1]
x = full.groupby("year").size()
slope, icpt, r, p, se = stats.linregress(x.index, x.values)
R["trend_2007_2016"] = dict(slope_per_year=round(slope, 1), r2=round(r * r, 2), p=round(p, 3))
print("\nTrend on complete years 2007-2016: slope", round(slope, 1), "events/yr, R2", round(r * r, 2), "p", round(p, 3))
x2 = full[full.year >= 2010].groupby("year").size()
s2 = stats.linregress(x2.index, x2.values); R["trend_2010_2016"] = dict(slope=round(s2.slope, 1), r2=round(s2.rvalue ** 2, 2), p=round(s2.pvalue, 3))
print("Trend 2010-2016: slope", round(s2.slope, 1), "R2", round(s2.rvalue ** 2, 2), "p", round(s2.pvalue, 3))

mon = core.groupby("month_num").size()
show("B2. Events by calendar month (core)", mon)
R["by_month"] = {int(k): int(v) for k, v in mon.items()}
hm = core.groupby(["hemisphere", "month_num"]).size().unstack(0).fillna(0).astype(int)
show("B3. Month x hemisphere", hm)
R["month_hemi"] = hm.reset_index().to_dict("records")
show("B4. By season (hemisphere-adjusted)", core.groupby("season").size())
ym = core.groupby("year_month").size()
z = (ym - ym.rolling(12, min_periods=6, center=True).mean()) / ym.rolling(12, min_periods=6, center=True).std()
spk = ym[(z > 2.2)].sort_values(ascending=False).head(8)
show("B5. Monthly spikes (z>2.2 vs 12-month centred mean)", spk)
R["spikes"] = {k: int(v) for k, v in spk.items()}
dow = core.groupby("day_of_week").size().reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
show("B6. Day of week", dow)
chi_dow = stats.chisquare(dow.values)
print("chi-square uniform day-of-week p =", round(chi_dow.pvalue, 3))

# ---------------------------------------------------------------- C. geography
c = f[f.country_name != "Unknown"]
ct = c.groupby("country_name").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum"),
                                   fatal_events=("fatal_event_flag", "sum"), reported=("fatality_reported_flag", "sum"))
ct["fatal_rate_pct"] = (100 * ct.fatal_events / ct.reported.replace(0, np.nan)).round(1)
ct["fatalities_per_event"] = (ct.fatalities / ct.events).round(2)
ct["share_events_pct"] = (100 * ct.events / len(f)).round(1)
top = ct.sort_values("events", ascending=False).head(15)
show("C1. Top 15 countries by events", top)
R["top_countries"] = top.reset_index().to_dict("records")
topf = ct.sort_values("fatalities", ascending=False).head(10)
show("C2. Top 10 countries by fatalities", topf)
R["top_countries_fatal"] = topf.reset_index().to_dict("records")
cum = ct.sort_values("events", ascending=False).events.cumsum() / len(f)
print("\nTop 5 countries share of events: %.1f%%, top 10: %.1f%%" % (100 * cum.iloc[4], 100 * cum.iloc[9]))
R["conc_countries"] = dict(top5=round(100 * cum.iloc[4], 1), top10=round(100 * cum.iloc[9], 1))
show("C3. Continent", f.groupby("continent").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum")).sort_values("events", ascending=False))
R["continent"] = f.groupby("continent").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum")).reset_index().to_dict("records")
sr = f.groupby("subregion").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum")).sort_values("events", ascending=False).head(10)
show("C4. Top subregions", sr)
R["subregion"] = sr.reset_index().to_dict("records")
g = f.groupby("grid_1deg").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum"), lat=("grid_lat", "first"), lon=("grid_lon", "first"),
                               place=("nearest_place", lambda s: s.mode().iat[0] if s.notna().any() else ""),
                               country=("country_name", lambda s: s.mode().iat[0])).sort_values("events", ascending=False)
show("C5. Top 12 one-degree hotspot cells", g.head(12))
R["hotspots"] = g.head(12).reset_index().to_dict("records")

# ---------------------------------------------------------------- India
ind = f[f.country_name == "India"]
print("\n=== INDIA ===", len(ind), "events;", int(ind.fatality_count.sum()), "fatalities")
ist = ind.groupby("admin_division").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum"), fatal_events=("fatal_event_flag", "sum")).sort_values("events", ascending=False)
show("I1. India by state (top 15)", ist.head(15))
R["india_states"] = ist.head(15).reset_index().to_dict("records")
im = ind[ind.core_period_flag == 1].groupby("month_num").size()
show("I2. India by month", im)
R["india_month"] = {int(k): int(v) for k, v in im.items()}
jjas = ind[ind.month_num.isin([6, 7, 8, 9])].shape[0] / len(ind)
print("India share of events in Jun-Sep: %.1f%%" % (100 * jjas)); R["india_jjas_pct"] = round(100 * jjas, 1)
show("I3. India trigger group", ind.groupby("trigger_group").size().sort_values(ascending=False))
show("I4. India setting group", ind.groupby("setting_group").size().sort_values(ascending=False))
show("I5. India size", ind.groupby("size").size())
R["india_trigger"] = ind.groupby("trigger_group").size().sort_values(ascending=False).to_dict()
R["india_year"] = ind[ind.core_period_flag == 1].groupby("year").size().to_dict()
show("I6. India deadliest 8", ind.nlargest(8, "fatality_count")[["event_date", "admin_division", "trigger", "size", "fatality_count"]])
R["india_deadliest"] = ind.nlargest(8, "fatality_count")[["event_date", "event_title", "admin_division", "trigger", "fatality_count"]].to_dict("records")
mh = ind[ind.admin_division == "Maharashtra"]
print("\nMaharashtra:", len(mh), "events,", int(mh.fatality_count.sum()), "fatalities; months:", mh.groupby("month_num").size().to_dict())
R["maharashtra"] = dict(events=len(mh), fatalities=int(mh.fatality_count.sum()), by_month=mh.groupby("month_num").size().to_dict(),
                        by_trigger=mh.groupby("trigger_group").size().to_dict(), by_setting=mh.groupby("setting_group").size().to_dict())
sa = f[f.subregion == "South Asia"].groupby("country_name").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum")).sort_values("events", ascending=False)
show("I7. South Asia countries", sa)
R["south_asia"] = sa.reset_index().to_dict("records")

# ---------------------------------------------------------------- D. triggers
tg = f.groupby("trigger_group").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum"), fatal_events=("fatal_event_flag", "sum"),
                                    reported=("fatality_reported_flag", "sum")).sort_values("events", ascending=False)
tg["share_pct"] = (100 * tg.events / len(f)).round(1)
tg["fatal_rate_pct"] = (100 * tg.fatal_events / tg.reported).round(1)
tg["fatalities_per_event"] = (tg.fatalities / tg.events).round(2)
show("D1. Trigger group", tg)
R["trigger_group"] = tg.reset_index().to_dict("records")
t_det = f.groupby("trigger").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum")).sort_values("events", ascending=False)
R["trigger_detail"] = t_det.reset_index().to_dict("records")
tm = pd.crosstab(f[f.core_period_flag == 1].month_num, f[f.core_period_flag == 1].trigger_group)
show("D2. Trigger group by month", tm)
R["trigger_month"] = tm.reset_index().to_dict("records")
known = f[(f.trigger_group != "Unknown")]
rainfall_share = 100 * known.trigger_group.isin(["Rainfall", "Tropical cyclone", "Flooding"]).mean()
print("Share of known-trigger events that are water-driven (rain, cyclone, flooding): %.1f%%" % rainfall_share); R["water_share_pct"] = round(rainfall_share, 1)
ts = pd.crosstab(known.trigger_group, known["size"], normalize="index").round(3) * 100
show("D3. Trigger group x size (row %)", ts.round(1))
R["trigger_size"] = ts.round(1).reset_index().to_dict("records")

# ---------------------------------------------------------------- E. type / size / setting
for col, key in [("category_group", "category"), ("size", "size"), ("setting_group", "setting")]:
    t = f.groupby(col).agg(events=("event_id", "count"), fatalities=("fatality_count", "sum"), fatal_events=("fatal_event_flag", "sum"), reported=("fatality_reported_flag", "sum"))
    t["fatal_rate_pct"] = (100 * t.fatal_events / t.reported).round(1); t["fatalities_per_event"] = (t.fatalities / t.events).round(2)
    show(f"E. by {col}", t.sort_values("events", ascending=False)); R[key] = t.reset_index().to_dict("records")
sz = f[f["size"] != "Unknown"].groupby("size").agg(events=("event_id", "count"), fatal_rate=("fatal_event_flag", "mean"), med=("fatality_count", "median"), mean=("fatality_count", "mean"))
cat_detail = f.groupby("category").size().sort_values(ascending=False); R["category_detail"] = cat_detail.to_dict()
st_detail = f.groupby("setting").size().sort_values(ascending=False); R["setting_detail"] = st_detail.to_dict()

# ---------------------------------------------------------------- F. fatalities
fb = f.groupby(["fatality_band", "fatality_band_sort"]).size().reset_index(name="events").sort_values("fatality_band_sort")
show("F1. Fatality bands", fb); R["fatality_band"] = fb.to_dict("records")
dead = f.nlargest(15, "fatality_count")[["event_date", "event_title", "country_name", "trigger", "size", "fatality_count"]]
dead["event_title"] = dead.event_title.str.slice(0, 55)
show("F2. Top 15 deadliest events", dead)
R["deadliest"] = f.nlargest(15, "fatality_count")[["event_date", "event_title", "country_name", "trigger", "size", "fatality_count"]].to_dict("records")
tot = f.fatality_count.sum(); t3 = f.nlargest(3, "fatality_count").fatality_count.sum(); t10 = f.nlargest(10, "fatality_count").fatality_count.sum()
t1pct = f.fatality_count.sort_values(ascending=False).head(int(len(rep) * 0.01)).sum()
print("\nTotal fatalities %d | top 3 events = %d (%.1f%%) | top 10 = %d (%.1f%%) | top 1%% of reported events = %.1f%%" % (tot, t3, 100 * t3 / tot, t10, 100 * t10 / tot, 100 * t1pct / tot))
R["fat_concentration"] = dict(total=int(tot), top3=int(t3), top3_pct=round(100 * t3 / tot, 1), top10=int(t10), top10_pct=round(100 * t10 / tot, 1), top1pct_events_share=round(100 * t1pct / tot, 1))
wo = f[~f.event_id.isin(f.nlargest(3, "fatality_count").event_id)]
print("Fatalities without top 3: %d" % wo.fatality_count.sum())
y_f = core.groupby("year").fatality_count.sum(); R["fatal_by_year"] = y_f.to_dict()
y_f_wo = wo[wo.core_period_flag == 1].groupby("year").fatality_count.sum(); show("F3. Fatalities by year (all vs without top 3)", pd.DataFrame({"all": y_f, "without_top3": y_f_wo}))
R["fatal_by_year_wo"] = y_f_wo.to_dict()

# ---------------------------------------------------------------- storms
sto = f[f.storm_name.notna()].groupby("storm_name").agg(events=("event_id", "count"), fatalities=("fatality_count", "sum"), country=("country_name", lambda s: s.mode().iat[0])).sort_values("events", ascending=False).head(10)
show("S. Named storms with most triggered landslides", sto); R["storms"] = sto.reset_index().to_dict("records")

# ---------------------------------------------------------------- G. data quality
dq = {}
raw_missing = {"fatality_count": 100 - 100 * f.fatality_reported_flag.mean(), "injury_count": 100 - 100 * f.injury_reported_flag.mean(),
               "trigger unknown": 100 * (f.trigger == "Unknown").mean(), "size unknown": 100 * (f["size"] == "Unknown").mean(),
               "setting unknown": 100 * (f.setting == "Unknown").mean(), "country original?": 100 * (f.country_source != "Original").mean(),
               "location accuracy > 10 km or unknown": 100 * ((f.accuracy_km > 10) | f.accuracy_km.isna()).mean()}
show("G1. Completeness (% missing/unknown/derived)", pd.Series({k: round(v, 1) for k, v in raw_missing.items()}))
R["completeness"] = {k: round(v, 1) for k, v in raw_missing.items()}
srcs = f.groupby("source_name").size().sort_values(ascending=False)
print("\nTop sources:", srcs.head(8).to_dict(), "| distinct sources:", len(srcs), "| top source share %.1f%%" % (100 * srcs.iloc[0] / len(f)))
R["sources"] = srcs.head(10).to_dict(); R["source_group"] = f.groupby("source_group").size().to_dict()
us_share = 100 * (f.country_name == "United States").mean(); od = (f.source_name == "Oregon DOT").sum()
print("US share %.1f%%; Oregon DOT rows: %d (%.1f%% of US events)" % (us_share, od, 100 * od / (f.country_name == "United States").sum()))
R["us_oregon"] = dict(us_pct=round(us_share, 1), oregon_dot=int(od), oregon_share_of_us=round(100 * od / (f.country_name == "United States").sum(), 1))
lag = f.groupby("year").report_lag_days.median(); show("G2. Median days between event and submission, by year", lag); R["lag_by_year"] = {int(k): float(v) for k, v in lag.items() if k >= 2007}
acc = f.groupby(f.accuracy_km.fillna(-1)).size(); show("G3. Location accuracy (km; -1 = unknown)", acc)
R["accuracy"] = {str(k): int(v) for k, v in acc.items()}
print("Possible duplicates:", int(f.possible_duplicate_flag.sum()), "| test imports:", int(f.is_test_import_flag.sum()), "| negative lag:", int(f.lag_negative_flag.sum()))
R["flags"] = dict(duplicates=int(f.possible_duplicate_flag.sum()), test=int(f.is_test_import_flag.sum()), neg_lag=int(f.lag_negative_flag.sum()))
fatal_by_precision = f[f.fatality_reported_flag == 1].groupby("high_precision_flag").fatal_event_flag.mean().round(3); print("Fatal rate by precise location:", fatal_by_precision.to_dict())
res_rate = rep.groupby("source_group").fatal_event_flag.mean().round(3); print("Fatal rate by source group:", res_rate.to_dict()); R["fatal_by_source_group"] = res_rate.to_dict()

# ---------------------------------------------------------------- H. associations
def cramers(a, b):
    ct_ = pd.crosstab(a, b); ct_ = ct_.loc[ct_.sum(1) > 0, ct_.sum(0) > 0]
    chi2 = stats.chi2_contingency(ct_)[0]; n = ct_.values.sum(); k = min(ct_.shape) - 1
    return round(float(np.sqrt(chi2 / (n * k))), 3), float(stats.chi2_contingency(ct_)[1])

repk = rep.copy()
assoc = {}
for a, b in [("trigger_group", "size"), ("trigger_group", "setting_group"), ("size", "fatal_event_flag"), ("trigger_group", "fatal_event_flag"),
             ("setting_group", "fatal_event_flag"), ("category_group", "fatal_event_flag"), ("continent", "fatal_event_flag"), ("source_group", "fatal_event_flag")]:
    d = repk if "fatal_event_flag" in (a, b) else f
    d = d[(d[a] != "Unknown") & (d[b] != "Unknown")] if b != "fatal_event_flag" else d[d[a] != "Unknown"]
    v, p_ = cramers(d[a], d[b]); assoc[f"{a} x {b}"] = dict(cramers_v=v, p=float(f"{p_:.2g}"))
show("H1. Associations (Cramer's V)", pd.DataFrame(assoc).T); R["assoc"] = assoc
sr_ = repk[repk["size"] != "Unknown"]; rho = stats.spearmanr(sr_.size_rank, sr_.fatality_count)
print("Spearman size rank vs fatalities: rho=%.2f p=%.1e" % (rho.statistic, rho.pvalue)); R["spearman_size_fatal"] = round(float(rho.statistic), 2)

# logistic regression: P(fatal | features)
m = repk[["size", "trigger_group", "setting_group", "category_group", "continent", "high_precision_flag", "fatal_event_flag"]].copy()
X = OneHotEncoder(handle_unknown="ignore", min_frequency=30).fit(m.drop(columns="fatal_event_flag"))
Xm = X.transform(m.drop(columns="fatal_event_flag")); y = m.fatal_event_flag.values
lr = LogisticRegression(max_iter=2000, C=1.0)
pred = cross_val_predict(lr, Xm, y, cv=StratifiedKFold(5, shuffle=True, random_state=0), method="predict_proba")[:, 1]
auc = roc_auc_score(y, pred); print("\nLogistic model AUC (5-fold CV) for 'event caused >=1 death': %.3f" % auc)
lr.fit(Xm, y); names = X.get_feature_names_out(); co = pd.Series(lr.coef_[0], index=names).sort_values()
show("H2. Strongest odds drivers (log-odds)", pd.concat([co.head(6), co.tail(8)]).round(2))
R["model_auc"] = round(float(auc), 3); R["model_coef"] = co.round(2).to_dict()
base = y.mean(); print("Base fatal rate among reported:", round(base, 3))

# population exposure
pk = f[(f.population_known_flag == 1) & (f.fatality_reported_flag == 1)].copy()
pk["pop_band"] = pd.cut(pk.admin_population, [0, 1e5, 1e6, 1e7, 1e10], labels=["<100k", "100k-1M", "1M-10M", ">10M"])
pb = pk.groupby("pop_band", observed=True).agg(events=("event_id", "count"), fatal_rate=("fatal_event_flag", "mean")); pb["fatal_rate"] = (100 * pb.fatal_rate).round(1)
show("H3. Fatal-event rate by population of admin division", pb); R["pop_band"] = pb.reset_index().to_dict("records")

json.dump(R, open(sys.argv[2], "w"), default=lambda o: o.item() if hasattr(o, "item") else str(o), indent=1)
print("\nresults written")
