"""Clean NASA Global Landslide Catalog and build Power BI star-schema tables.

    python build_dataset.py <raw_csv> <out_dir>

Outputs (CSV, UTF-8): fact_landslides, dim_date, dim_country, dim_trigger, dim_size,
dim_category, dim_setting, data_quality_log. Every filled/derived value is flagged.
"""
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
log = []  # (step, detail)

df = pd.read_csv(RAW, low_memory=False)
n0 = len(df)

# ---------------------------------------------------------------- dates (US format!)
fmt = "%m/%d/%Y %I:%M:%S %p"
dt = pd.to_datetime(df["event_date"], format=fmt, errors="coerce")
sub = pd.to_datetime(df["submitted_date"], format=fmt, errors="coerce")
df["event_datetime"] = dt
df["event_date"] = dt.dt.normalize()
df["year"] = dt.dt.year
df["quarter"] = "Q" + dt.dt.quarter.astype(str)
df["month_num"] = dt.dt.month
df["month_name"] = dt.dt.strftime("%b")
df["year_month"] = dt.dt.to_period("M").dt.to_timestamp()
df["day_of_week"] = dt.dt.day_name()
df["submitted_date"] = sub.dt.normalize()
df["report_lag_days"] = (sub.dt.normalize() - dt.dt.normalize()).dt.days
df["lag_negative_flag"] = (df["report_lag_days"] < 0).astype(int)
log.append(("dates", f"parsed {dt.notna().sum()}/{n0} event dates as MM/DD/YYYY; {int(df.lag_negative_flag.sum())} rows submitted before event"))

north = df["latitude"] >= 0
seasons_n = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
             6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
flip = {"Winter": "Summer", "Summer": "Winter", "Spring": "Autumn", "Autumn": "Spring"}
s = df["month_num"].map(seasons_n)
df["season"] = np.where(north, s, s.map(flip))
df["hemisphere"] = np.where(north, "Northern", "Southern")

# ---------------------------------------------------------------- categoricals
def nice(x):
    if pd.isna(x):
        return "Unknown"
    x = str(x).replace("_", " ").strip()
    return x[:1].upper() + x[1:]

for raw, new in [("landslide_category", "category"), ("landslide_trigger", "trigger"),
                 ("landslide_size", "size"), ("landslide_setting", "setting")]:
    df[new] = df[raw].map(nice)

trig_group = {
    "Downpour": "Rainfall", "Rain": "Rainfall", "Continuous rain": "Rainfall", "Monsoon": "Rainfall",
    "Tropical cyclone": "Tropical cyclone", "Flooding": "Flooding",
    "Snowfall snowmelt": "Snow and freeze-thaw", "Freeze thaw": "Snow and freeze-thaw",
    "Earthquake": "Earthquake and volcano", "Volcano": "Earthquake and volcano",
    "Mining": "Human activity", "Construction": "Human activity", "Leaking pipe": "Human activity",
    "Vibration": "Human activity", "Dam embankment collapse": "Human activity",
    "No apparent trigger": "Other or none", "Other": "Other or none", "Unknown": "Unknown"}
df["trigger_group"] = df["trigger"].map(trig_group).fillna("Other or none")

size_rank = {"Small": 1, "Medium": 2, "Large": 3, "Very large": 4, "Catastrophic": 5, "Unknown": 0}
df["size_rank"] = df["size"].map(size_rank).fillna(0).astype(int)

cat_group = {"Landslide": "Landslide (slide)", "Translational slide": "Landslide (slide)", "Creep": "Landslide (slide)",
             "Topple": "Landslide (slide)", "Earth flow": "Flow", "Mudslide": "Flow", "Debris flow": "Flow",
             "Lahar": "Flow", "Rock fall": "Rock fall", "Complex": "Complex", "Riverbank collapse": "Other",
             "Snow avalanche": "Other", "Other": "Other", "Unknown": "Unknown"}
df["category_group"] = df["category"].map(cat_group).fillna("Other")

set_group = {"Above road": "Road-related", "Below road": "Road-related",
             "Natural slope": "Natural terrain", "Bluff": "Natural terrain", "Above river": "Natural terrain",
             "Above coast": "Natural terrain", "Burned area": "Natural terrain", "Deforested slope": "Natural terrain",
             "Urban": "Built environment", "Retaining wall": "Built environment", "Engineered slope": "Built environment",
             "Mine": "Built environment", "Other": "Other", "Unknown": "Unknown"}
df["setting_group"] = df["setting"].map(set_group).fillna("Other")

acc = df["location_accuracy"].astype(str).str.lower()
df["accuracy_km"] = acc.str.extract(r"^(\d+)km$")[0].astype(float)
df.loc[acc == "exact", "accuracy_km"] = 0.0
df["location_accuracy"] = df["location_accuracy"].map(nice)
df["high_precision_flag"] = (df["accuracy_km"] <= 5).astype(int)

# ---------------------------------------------------------------- impact
df["fatality_reported_flag"] = df["fatality_count"].notna().astype(int)
df["injury_reported_flag"] = df["injury_count"].notna().astype(int)
df["fatal_event_flag"] = (df["fatality_count"].fillna(0) > 0).astype(int)
fb = pd.cut(df["fatality_count"], [-1, 0, 9, 99, 1e9], labels=["0", "1-9", "10-99", "100+"])
df["fatality_band"] = fb.astype(object).where(df["fatality_count"].notna(), "Not reported")
df["fatality_band_sort"] = df["fatality_band"].map({"Not reported": 0, "0": 1, "1-9": 2, "10-99": 3, "100+": 4})

# ---------------------------------------------------------------- country cleanup + recovery
df.loc[df["country_name"] == "Namibia", "country_code"] = "NA"
rename = {"Czech Republic": "Czechia", "Myanmar [Burma]": "Myanmar", "Macedonia": "North Macedonia",
          "Swaziland": "Eswatini", "East Timor": "Timor-Leste", "Democratic Republic of the Congo": "DR Congo",
          "Republic of the Congo": "Congo", "U.S. Virgin Islands": "US Virgin Islands"}
df["country_name"] = df["country_name"].replace(rename)
df["country_source"] = np.where(df["country_name"].notna(), "Original", "Unknown")

known = df.loc[df.country_name.notna(), "country_name"].unique()
lookup = {k.lower(): k for k in known}
lookup.update({"usa": "United States", "u.s.": "United States", "us": "United States", "united states of america": "United States",
               "uk": "United Kingdom", "burma": "Myanmar", "czech republic": "Czechia", "south korea": "South Korea",
               "republic of korea": "South Korea", "viet nam": "Vietnam", "pr china": "China", "p.r. china": "China"})

def parse_country(*texts):
    for t in texts:
        if not isinstance(t, str):
            continue
        for tok in reversed([x.strip().strip(".").lower() for x in t.replace("\n", " ").split(",")]):
            if tok in lookup:
                return lookup[tok]
    return None

miss = df["country_name"].isna()
parsed = df.loc[miss].apply(lambda r: parse_country(r["location_description"], r["event_title"]), axis=1)
df.loc[miss, "country_name"] = parsed
df.loc[miss & parsed.notna(), "country_source"] = "Parsed from location text"
log.append(("country", f"{int(miss.sum())} rows had no country; {int(parsed.notna().sum())} recovered from location text"))

def knn_fill(frame, target_mask, label_col, k, min_share, max_km, group_col=None):
    """Fill label_col for target rows by majority vote of k nearest labelled events."""
    lab = frame[frame[label_col].notna() & (frame["country_source"] == "Original")]
    tree = BallTree(np.radians(lab[["latitude", "longitude"]].to_numpy()), metric="haversine")
    labels = lab[label_col].to_numpy()
    out = {}
    tgt = frame.loc[target_mask]
    if len(tgt) == 0:
        return out
    dist, idx = tree.query(np.radians(tgt[["latitude", "longitude"]].to_numpy()), k=k)
    for row, (d, ix) in zip(tgt.index, zip(dist * 6371.0, idx)):
        vals = pd.Series(labels[ix]).value_counts()
        if d[0] <= max_km and vals.iloc[0] / k >= min_share:
            out[row] = vals.index[0]
    return out

# leave-one-out accuracy of the nearest-event method (honest estimate)
lab = df[df["country_source"] == "Original"].reset_index()
tree = BallTree(np.radians(lab[["latitude", "longitude"]].to_numpy()), metric="haversine")
dist, idx = tree.query(np.radians(lab[["latitude", "longitude"]].to_numpy()), k=8)
hit = tot = 0
for i in range(len(lab)):
    nb = idx[i][1:]; d0 = dist[i][1] * 6371.0
    v = pd.Series(lab["country_name"].to_numpy()[nb]).value_counts()
    if d0 <= 200 and v.iloc[0] / 7 >= 0.7:
        tot += 1; hit += v.index[0] == lab["country_name"].iloc[i]
log.append(("country_knn_accuracy", f"leave-one-out: {hit}/{tot} = {100 * hit / max(tot, 1):.1f}% correct on {tot} of {len(lab)} labelled rows that pass the rule"))

still = df["country_name"].isna()
filled = knn_fill(df, still, "country_name", k=7, min_share=0.7, max_km=200)
for r, v in filled.items():
    df.loc[r, "country_name"] = v
    df.loc[r, "country_source"] = "Nearest labelled events (approx.)"
log.append(("country", f"{len(filled)} more filled from nearest labelled events; {int(df.country_name.isna().sum())} remain unknown"))
df["country_name"] = df["country_name"].fillna("Unknown")

code_map = df[df.country_source == "Original"].groupby("country_name")["country_code"].first().to_dict()
df["country_code"] = df["country_name"].map(code_map).fillna("")

# ---------------------------------------------------------------- admin division (state / province)
def strip_marks(x):
    if not isinstance(x, str):
        return x
    return "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c)).strip()

df["admin_division"] = df["admin_division_name"].map(strip_marks)
df["admin_division"] = df["admin_division"].replace({"Kashmir": "Jammu and Kashmir", "Bengal": "West Bengal",
                                                      "NCT": "Delhi", "Orissa": "Odisha"})
df["admin_source"] = np.where(df["admin_division"].notna(), "Original", "Unknown")
adm_missing = df["admin_division"].isna() & (df["country_name"] != "Unknown")
lab_adm = df[df["admin_division"].notna() & (df["country_source"] == "Original")].copy()
tree = BallTree(np.radians(lab_adm[["latitude", "longitude"]].to_numpy()), metric="haversine")
cn, ad = lab_adm["country_name"].to_numpy(), lab_adm["admin_division"].to_numpy()
tgt = df[adm_missing]
dist, idx = tree.query(np.radians(tgt[["latitude", "longitude"]].to_numpy()), k=5)
n_adm = 0
for row, c, d, ix in zip(tgt.index, tgt["country_name"], dist * 6371.0, idx):
    same = [j for j in ix if cn[j] == c]
    if d[0] <= 100 and len(same) >= 4:
        v = pd.Series(ad[same]).value_counts()
        if v.iloc[0] >= 4:
            df.loc[row, "admin_division"] = v.index[0]; df.loc[row, "admin_source"] = "Nearest labelled events (approx.)"; n_adm += 1
log.append(("admin_division", f"{n_adm} state/province values filled from nearest labelled events (within 100 km, 4 of 5 neighbours agree)"))
df["admin_division"] = df["admin_division"].fillna("Unknown")

pop = df["admin_division_population"].where(df["admin_division_population"] > 0)
df["admin_population"] = pop
df["population_known_flag"] = pop.notna().astype(int)
df["nearest_place"] = df["gazeteer_closest_point"]
df["nearest_place_km"] = df["gazeteer_distance"]

# ---------------------------------------------------------------- continent / subregion
CONT = {
 "Afghanistan": ("Asia", "South Asia"), "Albania": ("Europe", "Southern Europe"), "Algeria": ("Africa", "Northern Africa"),
 "American Samoa": ("Oceania", "Polynesia"), "Angola": ("Africa", "Central Africa"), "Argentina": ("South America", "South America"),
 "Armenia": ("Asia", "Western Asia"), "Australia": ("Oceania", "Australia and New Zealand"), "Austria": ("Europe", "Western Europe"),
 "Azerbaijan": ("Asia", "Western Asia"), "Bangladesh": ("Asia", "South Asia"), "Barbados": ("North America", "Caribbean"),
 "Belize": ("North America", "Central America"), "Bermuda": ("North America", "Northern America"), "Bhutan": ("Asia", "South Asia"),
 "Bolivia": ("South America", "South America"), "Bosnia and Herzegovina": ("Europe", "Southern Europe"), "Brazil": ("South America", "South America"),
 "Brunei": ("Asia", "Southeast Asia"), "Bulgaria": ("Europe", "Eastern Europe"), "Burkina Faso": ("Africa", "Western Africa"),
 "Burundi": ("Africa", "Eastern Africa"), "Cambodia": ("Asia", "Southeast Asia"), "Cameroon": ("Africa", "Central Africa"),
 "Canada": ("North America", "Northern America"), "Chile": ("South America", "South America"), "China": ("Asia", "East Asia"),
 "Colombia": ("South America", "South America"), "Costa Rica": ("North America", "Central America"), "Croatia": ("Europe", "Southern Europe"),
 "Cuba": ("North America", "Caribbean"), "Czechia": ("Europe", "Eastern Europe"), "DR Congo": ("Africa", "Central Africa"),
 "Dominica": ("North America", "Caribbean"), "Dominican Republic": ("North America", "Caribbean"), "Timor-Leste": ("Asia", "Southeast Asia"),
 "Ecuador": ("South America", "South America"), "Egypt": ("Africa", "Northern Africa"), "El Salvador": ("North America", "Central America"),
 "Ethiopia": ("Africa", "Eastern Africa"), "Fiji": ("Oceania", "Melanesia"), "France": ("Europe", "Western Europe"),
 "Gabon": ("Africa", "Central Africa"), "Georgia": ("Asia", "Western Asia"), "Germany": ("Europe", "Western Europe"),
 "Ghana": ("Africa", "Western Africa"), "Greece": ("Europe", "Southern Europe"), "Grenada": ("North America", "Caribbean"),
 "Guam": ("Oceania", "Micronesia"), "Guatemala": ("North America", "Central America"), "Guinea": ("Africa", "Western Africa"),
 "Haiti": ("North America", "Caribbean"), "Honduras": ("North America", "Central America"), "Hong Kong": ("Asia", "East Asia"),
 "Iceland": ("Europe", "Northern Europe"), "India": ("Asia", "South Asia"), "Indonesia": ("Asia", "Southeast Asia"),
 "Iran": ("Asia", "Western Asia"), "Ireland": ("Europe", "Northern Europe"), "Isle of Man": ("Europe", "Northern Europe"),
 "Israel": ("Asia", "Western Asia"), "Italy": ("Europe", "Southern Europe"), "Ivory Coast": ("Africa", "Western Africa"),
 "Jamaica": ("North America", "Caribbean"), "Japan": ("Asia", "East Asia"), "Jersey": ("Europe", "Northern Europe"),
 "Jordan": ("Asia", "Western Asia"), "Kazakhstan": ("Asia", "Central Asia"), "Kenya": ("Africa", "Eastern Africa"),
 "Kyrgyzstan": ("Asia", "Central Asia"), "Laos": ("Asia", "Southeast Asia"), "Lebanon": ("Asia", "Western Asia"),
 "Liberia": ("Africa", "Western Africa"), "Luxembourg": ("Europe", "Western Europe"), "North Macedonia": ("Europe", "Southern Europe"),
 "Madagascar": ("Africa", "Eastern Africa"), "Malawi": ("Africa", "Eastern Africa"), "Malaysia": ("Asia", "Southeast Asia"),
 "Mauritius": ("Africa", "Eastern Africa"), "Mexico": ("North America", "Central America"), "Mongolia": ("Asia", "East Asia"),
 "Montenegro": ("Europe", "Southern Europe"), "Morocco": ("Africa", "Northern Africa"), "Myanmar": ("Asia", "Southeast Asia"),
 "Namibia": ("Africa", "Southern Africa"), "Nepal": ("Asia", "South Asia"), "New Zealand": ("Oceania", "Australia and New Zealand"),
 "Nicaragua": ("North America", "Central America"), "Nigeria": ("Africa", "Western Africa"), "North Korea": ("Asia", "East Asia"),
 "Norway": ("Europe", "Northern Europe"), "Oman": ("Asia", "Western Asia"), "Pakistan": ("Asia", "South Asia"),
 "Panama": ("North America", "Central America"), "Papua New Guinea": ("Oceania", "Melanesia"), "Paraguay": ("South America", "South America"),
 "Peru": ("South America", "South America"), "Philippines": ("Asia", "Southeast Asia"), "Poland": ("Europe", "Eastern Europe"),
 "Portugal": ("Europe", "Southern Europe"), "Puerto Rico": ("North America", "Caribbean"), "Congo": ("Africa", "Central Africa"),
 "Romania": ("Europe", "Eastern Europe"), "Russia": ("Europe", "Eastern Europe"), "Rwanda": ("Africa", "Eastern Africa"),
 "Saint Kitts and Nevis": ("North America", "Caribbean"), "Saint Lucia": ("North America", "Caribbean"),
 "Saint Vincent and the Grenadines": ("North America", "Caribbean"), "Saudi Arabia": ("Asia", "Western Asia"),
 "Serbia": ("Europe", "Southern Europe"), "Sierra Leone": ("Africa", "Western Africa"), "Singapore": ("Asia", "Southeast Asia"),
 "Slovakia": ("Europe", "Eastern Europe"), "Slovenia": ("Europe", "Southern Europe"), "Solomon Islands": ("Oceania", "Melanesia"),
 "South Africa": ("Africa", "Southern Africa"), "South Korea": ("Asia", "East Asia"), "Spain": ("Europe", "Southern Europe"),
 "Sri Lanka": ("Asia", "South Asia"), "Sudan": ("Africa", "Northern Africa"), "Eswatini": ("Africa", "Southern Africa"),
 "Switzerland": ("Europe", "Western Europe"), "Taiwan": ("Asia", "East Asia"), "Tajikistan": ("Asia", "Central Asia"),
 "Tanzania": ("Africa", "Eastern Africa"), "Thailand": ("Asia", "Southeast Asia"), "Trinidad and Tobago": ("North America", "Caribbean"),
 "Turkey": ("Asia", "Western Asia"), "US Virgin Islands": ("North America", "Caribbean"), "Uganda": ("Africa", "Eastern Africa"),
 "Ukraine": ("Europe", "Eastern Europe"), "United Arab Emirates": ("Asia", "Western Asia"), "United Kingdom": ("Europe", "Northern Europe"),
 "United States": ("North America", "Northern America"), "Uzbekistan": ("Asia", "Central Asia"), "Vanuatu": ("Oceania", "Melanesia"),
 "Venezuela": ("South America", "South America"), "Vietnam": ("Asia", "Southeast Asia"), "Yemen": ("Asia", "Western Asia"),
 "Zambia": ("Africa", "Eastern Africa"), "Unknown": ("Unknown", "Unknown"),
}
missing_c = sorted(set(df.country_name) - set(CONT))
assert not missing_c, f"countries without continent: {missing_c}"
df["continent"] = df["country_name"].map(lambda c: CONT[c][0])
df["subregion"] = df["country_name"].map(lambda c: CONT[c][1])
df["is_india_flag"] = (df["country_name"] == "India").astype(int)

# ---------------------------------------------------------------- source + quality flags
src = df["source_name"].fillna("Unknown").astype(str)
official = src.str.contains(r"\bDOT\b|USGS|Department|Ministry|Government|NASA|Survey|Geological|Authority|Police", case=False, regex=True)
df["source_group"] = np.select([official, src.str.contains("google", case=False)], ["Official or agency", "Google Maps / Earth"], "News and other media")
df["source_name"] = src
df["is_test_import_flag"] = (df["event_import_source"] == "test").astype(int)
dupkey = [df["event_date"].dt.date, df["latitude"].round(2), df["longitude"].round(2)]
df["possible_duplicate_flag"] = pd.DataFrame({"a": dupkey[0], "b": dupkey[1], "c": dupkey[2]}).duplicated(keep="first").astype(int).to_numpy()
log.append(("duplicates", f"{int(df.possible_duplicate_flag.sum())} rows share date + location (2 dp) with an earlier row; flagged, not removed"))

# trend-safe years: 2007 and 2017 are partial
mm = df.groupby("year")["month_num"].nunique()
df["complete_year_flag"] = df["year"].map(lambda y: int(mm.get(y, 0) == 12)).astype(int)
df["core_period_flag"] = df["year"].between(2007, 2017).astype(int)
log.append(("coverage", f"months with data per year: {mm.to_dict()}"))

# 1-degree grid cell for hotspot analysis
df["grid_1deg"] = np.floor(df["latitude"]).astype(int).astype(str) + "," + np.floor(df["longitude"]).astype(int).astype(str)
df["grid_lat"] = np.floor(df["latitude"]) + 0.5
df["grid_lon"] = np.floor(df["longitude"]) + 0.5

df["event_description_short"] = df["event_description"].fillna("").str.replace(r"\s+", " ", regex=True).str.slice(0, 250)
df["event_title"] = df["event_title"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
df["location_description"] = df["location_description"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip().str.slice(0, 200)

fact_cols = ["event_id", "event_date", "event_datetime", "year", "quarter", "month_num", "month_name", "year_month", "day_of_week",
             "season", "hemisphere", "event_title", "location_description", "event_description_short", "source_name", "source_group", "source_link",
             "country_name", "country_code", "country_source", "continent", "subregion", "is_india_flag", "admin_division", "admin_source",
             "latitude", "longitude", "grid_1deg", "grid_lat", "grid_lon", "location_accuracy", "accuracy_km", "high_precision_flag",
             "category", "category_group", "trigger", "trigger_group", "size", "size_rank", "setting", "setting_group", "storm_name",
             "fatality_count", "fatality_reported_flag", "fatal_event_flag", "fatality_band", "fatality_band_sort",
             "injury_count", "injury_reported_flag", "admin_population", "population_known_flag", "nearest_place", "nearest_place_km",
             "submitted_date", "report_lag_days", "lag_negative_flag", "is_test_import_flag", "possible_duplicate_flag",
             "complete_year_flag", "core_period_flag"]
fact = df[fact_cols].copy()
fact["event_date"] = fact["event_date"].dt.strftime("%Y-%m-%d")
fact["event_datetime"] = fact["event_datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
fact["year_month"] = fact["year_month"].dt.strftime("%Y-%m-%d")
fact["submitted_date"] = fact["submitted_date"].dt.strftime("%Y-%m-%d")
for c in ["fatality_count", "injury_count", "accuracy_km", "report_lag_days"]:
    fact[c] = fact[c].astype("Int64")
fact["admin_population"] = fact["admin_population"].astype("Int64")
fact.to_csv(OUT / "fact_landslides.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- dimensions
dmin, dmax = df["event_date"].min().normalize(), df["event_date"].max().normalize()
cal = pd.DataFrame({"date": pd.date_range(dmin.replace(month=1, day=1), dmax.replace(month=12, day=31))})
cal["year"] = cal.date.dt.year; cal["quarter"] = "Q" + cal.date.dt.quarter.astype(str)
cal["month_num"] = cal.date.dt.month; cal["month_name"] = cal.date.dt.strftime("%b")
cal["year_month"] = cal.date.dt.to_period("M").dt.to_timestamp().dt.strftime("%Y-%m-%d")
cal["day_of_week"] = cal.date.dt.day_name(); cal["day_of_week_num"] = cal.date.dt.dayofweek + 1
cal["week_of_year"] = cal.date.dt.isocalendar().week.astype(int)
cal["date"] = cal.date.dt.strftime("%Y-%m-%d")
cal.to_csv(OUT / "dim_date.csv", index=False, encoding="utf-8-sig")

dc = df[["country_name", "country_code", "continent", "subregion", "is_india_flag"]].drop_duplicates("country_name").sort_values("country_name")
dc.to_csv(OUT / "dim_country.csv", index=False, encoding="utf-8-sig")
dt_ = df[["trigger", "trigger_group"]].drop_duplicates().sort_values(["trigger_group", "trigger"]); dt_.to_csv(OUT / "dim_trigger.csv", index=False, encoding="utf-8-sig")
ds = pd.DataFrame({"size": list(size_rank), "size_rank": list(size_rank.values())}).sort_values("size_rank"); ds.to_csv(OUT / "dim_size.csv", index=False, encoding="utf-8-sig")
dg = df[["category", "category_group"]].drop_duplicates().sort_values(["category_group", "category"]); dg.to_csv(OUT / "dim_category.csv", index=False, encoding="utf-8-sig")
dse = df[["setting", "setting_group"]].drop_duplicates().sort_values(["setting_group", "setting"]); dse.to_csv(OUT / "dim_setting.csv", index=False, encoding="utf-8-sig")

pd.DataFrame(log, columns=["step", "detail"]).to_csv(OUT / "data_quality_log.csv", index=False, encoding="utf-8-sig")
fact.to_pickle(OUT.parent / "fact.pkl") if (OUT.parent).exists() else None
print(f"rows in: {n0}  rows out: {len(fact)}  columns: {fact.shape[1]}")
for a, b in log:
    print(f"[{a}] {b}")
print("country_source:", df.country_source.value_counts().to_dict())
print("admin_source:", df.admin_source.value_counts().to_dict())
print("source_group:", df.source_group.value_counts().to_dict())
