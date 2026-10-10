"""Render PNG previews of each report page from the cleaned data (matplotlib)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

DATA, OUT, RES = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
f = pd.read_csv(DATA / "fact_landslides.csv", low_memory=False, keep_default_na=False, na_values=[""])
R = json.load(open(RES))
core = f[f.core_period_flag == 1]

BLUE, MAG, VIO, AQUA, TEAL = "#2a78d6", "#e87ba4", "#6250d6", "#1baf7a", "#0F5C63"
INK, SOFT, MUTED, GRID, BG, PANEL = "#17202A", "#3C4753", "#5B6672", "#E1E4E8", "#E9ECEF", "#FFFFFF"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": "#C3C2B7", "axes.facecolor": PANEL,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": BG})
nf = lambda v: f"{int(round(v)):,}"


def page(name, title, subtitle, rows, cols):
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    fig.text(0.02, 0.955, title, fontsize=17, fontweight="bold", va="center")
    fig.text(0.02, 0.918, subtitle, fontsize=10, color=MUTED, va="center")
    fig.text(0.98, 0.955, "Preview of Power BI page", fontsize=8, color=MUTED, ha="right", va="center")
    gs = GridSpec(rows, cols, figure=fig, left=0.14, right=0.985, top=0.80, bottom=0.075, hspace=0.62, wspace=0.62)
    return fig, gs


def ax_title(ax, t, sub=None):
    ax.set_title(t, loc="left", fontsize=10.5, fontweight="bold", color=INK, pad=14 if sub else 8)
    if sub:
        ax.annotate(sub, (0, 1), xycoords="axes fraction", xytext=(0, 3), textcoords="offset points", fontsize=8, color=MUTED, va="bottom")
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)


def hbar(ax, labels, vals, color=BLUE, fmt=nf, colors=None, xlim=None):
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, color=colors if colors is not None else color, height=0.62 if len(labels) > 4 else 0.34)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8.5, color=INK)
    mx = max(vals) if len(vals) else 1
    for yi, v in zip(y, vals):
        ax.text(v + mx * 0.012, yi, fmt(v), va="center", fontsize=8, color=INK)
    ax.set_xlim(0, xlim or mx * 1.18); ax.grid(axis="x", color=GRID, lw=0.8); ax.grid(axis="y", visible=False)
    ax.tick_params(axis="x", labelsize=8); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)


def cards(fig, items, y=0.775, h=0.09):
    n = len(items); w = 0.95 / n
    for i, (lab, val) in enumerate(items):
        ax = fig.add_axes([0.03 + i * w, y, w - 0.012, h]); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_color("#D3D8DD")
        ax.text(0.06, 0.64, val, fontsize=19, fontweight="bold", transform=ax.transAxes, va="center")
        ax.text(0.06, 0.18, lab, fontsize=8.5, color=MUTED, transform=ax.transAxes, va="center")


def save(fig, name):
    fig.savefig(OUT / name, dpi=100, facecolor=BG); plt.close(fig); print("saved", name)


# ================================================================ 1 overview
fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
fig.text(0.02, 0.955, "Overview", fontsize=17, fontweight="bold", va="center")
fig.text(0.02, 0.918, "11,033 reported landslides, 1988 to Sep 2017. Counts show where landslides were reported, not where they occur most.", fontsize=10, color=MUTED, va="center")
fig.text(0.98, 0.955, "Preview of Power BI page", fontsize=8, color=MUTED, ha="right", va="center")
k = R["kpi"]
cards(fig, [("Events", nf(k["events"])), ("Deaths reported", nf(k["fatalities"])), ("Injuries reported", nf(k["injuries"])), ("Countries", str(k["countries"])),
            ("Fatal event rate", f"{k['fatal_rate_pct_of_reported']}%"), ("Median report lag", f"{int(f.report_lag_days.median())} d")])
gs = GridSpec(2, 3, figure=fig, left=0.06, right=0.985, top=0.67, bottom=0.075, hspace=0.62, wspace=0.62, width_ratios=[1.5, 1, 1])
ax = fig.add_subplot(gs[:, 0]); ax_title(ax, "Where events were reported", "Magenta rings: events with 100 or more deaths"); ax.grid(color=GRID, lw=0.5)
ax.scatter(f.longitude, f.latitude, s=4, color=BLUE, alpha=0.28, lw=0)
big = f[f.fatality_count >= 100]; ax.scatter(big.longitude, big.latitude, s=46, facecolors="none", edgecolors=MAG, lw=1.5)
ax.set_xlim(-180, 180); ax.set_ylim(-60, 78); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Events by year", "2007 and 2017 are partial years")
y = core.groupby("year").size(); ax.bar(y.index, y.values, color=BLUE, width=0.7); ax.set_xticks(y.index[::2]); ax.tick_params(labelsize=8)
for xx, v in zip(y.index, y.values):
    if xx in (2007, 2010, 2017): ax.text(xx, v + 25, nf(v), ha="center", fontsize=8)
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Deaths by year", "Kedarnath drives 2013")
d = core.groupby("year").fatality_count.sum(); ax.plot(d.index, d.values, color=MAG, lw=2.2, marker="o", ms=4); ax.set_xticks(d.index[::2]); ax.tick_params(labelsize=8)
ax.text(2013, d.loc[2013] + 250, nf(d.loc[2013]), ha="center", fontsize=8); ax.set_ylim(0, 7200)
ax = fig.add_subplot(gs[1, 1]); ax_title(ax, "Top 10 countries by events")
t = pd.DataFrame(R["top_countries"]).head(10); hbar(ax, t.country_name, t.events, BLUE)
ax = fig.add_subplot(gs[1, 2]); ax_title(ax, "Trigger group share of events")
t = pd.DataFrame(R["trigger_group"]).sort_values("events", ascending=False)
hbar(ax, t.trigger_group, t.share_pct, AQUA, fmt=lambda v: f"{v:.1f}%")
save(fig, "01_overview.png")

# ================================================================ 2 time
fig, gs = page("02", "Time trends", "Is it getting worse? Events rose to 2010, then stayed flat. The early rise is catalog build-up.", 2, 3)
ax = fig.add_subplot(gs[0, :2]); ax_title(ax, "Events per month with rolling 12 months", "2007 to Sep 2017")
m = core.groupby("year_month").size(); m.index = pd.to_datetime(m.index)
ax.bar(m.index, m.values, width=22, color=BLUE, alpha=0.55); r12 = m.rolling(12).mean(); ax.plot(r12.index, r12.values, color=INK, lw=2)
ax.annotate("12-month average", (r12.index[26], r12.values[26]), xytext=(r12.index[8], 215), fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED))
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Annual events, complete years", "Trend line 2010 to 2016 is flat")
yy = core[core.complete_year_flag == 1].groupby("year").size(); ax.bar(yy.index, yy.values, color=BLUE, width=0.7)
x2 = yy.loc[2010:2016]; z = np.polyfit(x2.index, x2.values, 1); ax.plot(x2.index, np.polyval(z, x2.index), color=MAG, lw=2, ls="--")
ax.set_ylim(0, 1900); ax.text(2010.6, 1720, f"2010-2016 slope {R['trend_2010_2016']['slope']:+.0f} per year (p = {R['trend_2010_2016']['p']})", fontsize=8, color=INK); ax.set_xticks(yy.index[::2])
ax = fig.add_subplot(gs[1, :2]); ax_title(ax, "Events by year and month", "Darker is more events")
pv = core[core.year.between(2007, 2016)].pivot_table(index="year", columns="month_num", values="event_id", aggfunc="count", fill_value=0)
im = ax.imshow(pv.values, aspect="auto", cmap=matplotlib.colors.LinearSegmentedColormap.from_list("t", ["#E6F1F2", "#7FB7BD", "#0A4248"]))
ax.set_xticks(range(12)); ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], fontsize=8); ax.set_yticks(range(len(pv))); ax.set_yticklabels(pv.index, fontsize=8)
ax.grid(False)
for i in range(pv.shape[0]):
    for j in range(pv.shape[1]):
        v = pv.values[i, j]; ax.text(j, i, v, ha="center", va="center", fontsize=7, color="white" if v > pv.values.max() * 0.55 else INK)
ax = fig.add_subplot(gs[1, 2]); ax_title(ax, "Events by weekday", "A reporting rhythm, not geology")
d = core.groupby("day_of_week").size().reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
ax.bar([s[:3] for s in d.index], d.values, color=BLUE, width=0.65); ax.tick_params(labelsize=8)
save(fig, "02_time_trends.png")

# ================================================================ 3 seasonality
fig, gs = page("03", "Seasonality", "July is the peak month. Northern Hemisphere summer dominates; cyclones add an Aug to Oct bump.", 2, 3)
mn = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
hm = core.groupby(["month_num", "hemisphere"]).size().unstack(1).fillna(0)
ax = fig.add_subplot(gs[0, :2]); ax_title(ax, "Events by month and hemisphere", "Core period 2007 to 2017")
xx = np.arange(12); ax.bar(xx - 0.2, hm["Northern"], 0.4, color=BLUE, label="Northern"); ax.bar(xx + 0.2, hm["Southern"], 0.4, color=MAG, label="Southern")
ax.set_xticks(xx); ax.set_xticklabels(mn, fontsize=8); ax.legend(frameon=False, fontsize=8, loc="upper left")
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Seasonality index", "1.0 = an average month")
tot = core.groupby("month_num").size(); si = tot / tot.mean(); ax.bar(mn, si.values, color=[VIO if v > 1 else "#B7B1D8" for v in si.values], width=0.7); ax.axhline(1, color=INK, lw=1)
ax.tick_params(axis="x", labelsize=7)
ax = fig.add_subplot(gs[1, :2]); ax_title(ax, "Trigger group by month", "Stacked events; rainfall is the base")
tm = core.pivot_table(index="month_num", columns="trigger_group", values="event_id", aggfunc="count", fill_value=0)
order = ["Rainfall", "Tropical cyclone", "Snow and freeze-thaw", "Earthquake and volcano", "Human activity"]
cols = [BLUE, VIO, AQUA, MAG, "#898781"]; bot = np.zeros(12)
for c, col in zip(order, cols):
    ax.bar(xx, tm[c].values, bottom=bot, color=col, width=0.7, label=c, edgecolor=PANEL, lw=1.5); bot += tm[c].values
ax.set_ylim(0, 1550); ax.set_xticks(xx); ax.set_xticklabels(mn, fontsize=8); ax.legend(frameon=False, fontsize=7.5, ncol=3, loc="upper left")
ax = fig.add_subplot(gs[1, 2]); ax_title(ax, "Events by season", "Hemisphere-adjusted")
se = core.groupby("season").size().reindex(["Winter", "Spring", "Summer", "Autumn"]); hbar(ax, se.index, se.values, BLUE, colors=[BLUE if s == "Summer" else "#9DBFE9" for s in se.index])
save(fig, "03_seasonality.png")

# ================================================================ 4 geography
fig, gs = page("04", "Geography", "Five countries hold 62% of events. The US share is inflated by one agency (Oregon DOT).", 2, 3)
ax = fig.add_subplot(gs[0, 0]); ax_title(ax, "Events by country, top 12")
t = pd.DataFrame(R["top_countries"]).head(12); hbar(ax, t.country_name, t.events, BLUE)
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Deaths per event, top 12 countries", "Averages are driven by a few huge events")
hbar(ax, t.country_name, t.fatalities_per_event, MAG, fmt=lambda v: f"{v:.2f}")
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Pareto: cumulative share", "One axis, % of all events")
a = f[f.country_name != "Unknown"].groupby("country_name").size().sort_values(ascending=False).head(15); share = a / len(f) * 100; cum = share.cumsum()
ax.bar(range(15), share.values, color=BLUE, width=0.7); ax.plot(range(15), cum.values, color=INK, lw=2, marker="o", ms=3)
codes = f.drop_duplicates("country_name").set_index("country_name").country_code; ax.set_xticks(range(15)); ax.set_xticklabels([codes[c] for c in a.index], fontsize=7); ax.set_ylim(0, 100); ax.set_ylabel("% of all events")
ax.text(14, cum.values[-1] + 3, f"{cum.values[-1]:.0f}%", ha="right", fontsize=8); ax.annotate(f"top 5 = {cum.values[4]:.0f}%", (4, cum.values[4]), xytext=(5.5, cum.values[4] - 22), fontsize=8, arrowprops=dict(arrowstyle="-", color=MUTED))
ax = fig.add_subplot(gs[1, 0]); ax_title(ax, "Events by subregion, top 10")
t = pd.DataFrame(R["subregion"]); hbar(ax, t.subregion, t.events, AQUA)
ax = fig.add_subplot(gs[1, 1:]); ax.axis("off"); ax.set_title("Hotspot cells (1 degree squares), top 12 by events", loc="left", fontsize=10.5, fontweight="bold", pad=14)
ax.text(0, 1.015, "The first four rows are the Oregon DOT cluster", transform=ax.transAxes, fontsize=8, color=MUTED)
h = pd.DataFrame(R["hotspots"]); yy = 0.9
ax.text(0.0, yy, "Nearest place", fontweight="bold", fontsize=8.5, transform=ax.transAxes); ax.text(0.42, yy, "Country", fontweight="bold", fontsize=8.5, transform=ax.transAxes)
ax.text(0.72, yy, "Events", fontweight="bold", fontsize=8.5, transform=ax.transAxes, ha="right"); ax.text(0.9, yy, "Deaths", fontweight="bold", fontsize=8.5, transform=ax.transAxes, ha="right")
for i, r in h.iterrows():
    yy = 0.81 - i * 0.068
    ax.text(0.0, yy, str(r.place), fontsize=8.5, transform=ax.transAxes); ax.text(0.42, yy, r.country, fontsize=8.5, transform=ax.transAxes)
    ax.text(0.72, yy, nf(r.events), fontsize=8.5, transform=ax.transAxes, ha="right"); ax.text(0.9, yy, nf(r.fatalities), fontsize=8.5, transform=ax.transAxes, ha="right")
save(fig, "04_geography.png")

# ================================================================ 5 triggers
fig, gs = page("05", "Triggers and causes", "Water drives 94% of events with a known trigger. Earthquakes are rare but deadly per event.", 2, 3)
tg = pd.DataFrame(R["trigger_group"]).sort_values("events", ascending=False)
ax = fig.add_subplot(gs[0, 0]); ax_title(ax, "Events by trigger group"); hbar(ax, tg.trigger_group, tg.events, BLUE)
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Fatal event rate", "Among events with a reported death count"); hbar(ax, tg.trigger_group, tg.fatal_rate_pct, MAG, fmt=lambda v: f"{v:.0f}%")
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Deaths per event"); hbar(ax, tg.trigger_group, tg.fatalities_per_event, VIO, fmt=lambda v: f"{v:.2f}")
ax = fig.add_subplot(gs[1, 0]); ax_title(ax, "Trigger detail, top 8")
td = pd.DataFrame(R["trigger_detail"]).head(8); hbar(ax, td.trigger, td.events, AQUA)
ax = fig.add_subplot(gs[1, 1]); ax_title(ax, "Size mix by trigger group", None)
ts = pd.DataFrame(R["trigger_size"]).set_index("trigger_group"); sizes = ["Small", "Medium", "Large", "Very large"]; cs = ["#9DBFE9", BLUE, VIO, MAG]
left = np.zeros(len(ts)); yv = np.arange(len(ts))[::-1]
for s, c in zip(sizes, cs):
    ax.barh(yv, ts[s].values, left=left, color=c, height=0.62, label=s, edgecolor=PANEL, lw=1.5); left += ts[s].values
ax.set_yticks(yv); ax.set_yticklabels(ts.index, fontsize=8); ax.legend(frameon=False, fontsize=7.5, ncol=4, loc="lower left", bbox_to_anchor=(-0.02, 1.0)); ax.set_xlim(0, 100); ax.tick_params(axis="y", length=0); ax.grid(False)
ax = fig.add_subplot(gs[1, 2]); ax_title(ax, "Named storms with most landslides", "Top 8, events (deaths)")
st = pd.DataFrame(R["storms"]).head(8); hbar(ax, st.storm_name.str.replace("Tropical ", "Trop. ").str.slice(0, 24), st.events, VIO)
save(fig, "05_triggers.png")

# ================================================================ 6 type size setting
fig, gs = page("06", "Type, size and setting", "Fatal rate climbs steeply with size. Road-related events are common but rarely fatal (Oregon DOT effect).", 2, 3)
sz = pd.DataFrame(R["size"]); sz = sz[sz["size"] != "Unknown"]; sz["rank"] = sz["size"].map({"Small": 1, "Medium": 2, "Large": 3, "Very large": 4, "Catastrophic": 5}); sz = sz.sort_values("rank")
ax = fig.add_subplot(gs[0, 0]); ax_title(ax, "Events by size"); ax.bar(sz["size"], sz.events, color=BLUE, width=0.65); ax.tick_params(axis="x", labelsize=7.5, rotation=20)
for i, v in enumerate(sz.events): ax.text(i, v + 80, nf(v), ha="center", fontsize=8)
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Fatal event rate by size", "Reported counts only; Catastrophic is 3 events"); ax.bar(sz["size"], sz.fatal_rate_pct, color=MAG, width=0.65); ax.tick_params(axis="x", labelsize=7.5, rotation=20)
for i, v in enumerate(sz.fatal_rate_pct): ax.text(i, v + 2, f"{v:.0f}%", ha="center", fontsize=8)
ax.set_ylim(0, 115)
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Events vs deaths by size", "Large or bigger = 7.7% of events")
tot_e = sz.events.sum(); tot_d = sz.fatalities.sum(); xs = np.arange(len(sz))
ax.bar(xs - 0.2, 100 * sz.events / tot_e, 0.4, color=BLUE, label="% of events"); ax.bar(xs + 0.2, 100 * sz.fatalities / tot_d, 0.4, color=VIO, label="% of deaths")
ax.set_xticks(xs); ax.set_xticklabels(sz["size"], fontsize=7.5, rotation=20); ax.legend(frameon=False, fontsize=8); ax.set_ylabel("% of total")
ax = fig.add_subplot(gs[1, 0]); ax_title(ax, "Events by category"); cg = pd.DataFrame(R["category"]).sort_values("events", ascending=False); hbar(ax, cg.category_group, cg.events, AQUA)
ax = fig.add_subplot(gs[1, 1]); ax_title(ax, "Events by setting group"); sg = pd.DataFrame(R["setting"]).sort_values("events", ascending=False); hbar(ax, sg.setting_group, sg.events, BLUE)
ax = fig.add_subplot(gs[1, 2]); ax_title(ax, "Fatal rate by setting"); sg2 = sg[sg.setting_group != "Unknown"]; hbar(ax, sg2.setting_group, sg2.fatal_rate_pct, MAG, fmt=lambda v: f"{v:.0f}%")
save(fig, "06_type_size_setting.png")

# ================================================================ 7 fatalities
fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
fig.text(0.02, 0.955, "Fatalities and impact", fontsize=17, fontweight="bold", va="center")
fig.text(0.02, 0.918, "Three events cause 28.5% of all deaths. Show totals with and without outliers.", fontsize=10, color=MUTED, va="center")
fig.text(0.98, 0.955, "Preview of Power BI page", fontsize=8, color=MUTED, ha="right", va="center")
fc = R["fat_concentration"]
cards(fig, [("Deaths", nf(fc["total"])), ("Deaths excl. top 3 events", nf(fc["total"] - fc["top3"])), ("Top 10 events' share", f"{fc['top10_pct']}%"),
            ("Large or bigger: share of deaths", f"{100 * f[f.size_rank >= 3].fatality_count.sum() / f.fatality_count.sum():.0f}%")])
gs = GridSpec(2, 3, figure=fig, left=0.14, right=0.985, top=0.67, bottom=0.075, hspace=0.62, wspace=0.62)
ax = fig.add_subplot(gs[0, 0]); ax_title(ax, "Deaths by year, with and without top 3", "Kedarnath (2013), Zhouqu (2010), Abi Barik (2014)")
yy = core.groupby("year").fatality_count.sum(); wo = pd.Series({int(k): v for k, v in R["fatal_by_year_wo"].items()}).reindex(yy.index)
ax.bar(yy.index, yy.values, color="#B7B1D8", width=0.7, label="all events"); ax.bar(wo.index, wo.values, color=VIO, width=0.7, label="excluding top 3"); ax.legend(frameon=False, fontsize=8); ax.set_xticks(yy.index[::2]); ax.tick_params(labelsize=8)
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Events by deaths per event", "Most events killed nobody")
fb = pd.DataFrame(R["fatality_band"]).sort_values("fatality_band_sort"); ax.bar(fb.fatality_band, fb.events, color=BLUE, width=0.65); ax.tick_params(axis="x", labelsize=8)
for i, v in enumerate(fb.events): ax.text(i, v + 90, nf(v), ha="center", fontsize=8)
ax.set_ylim(0, 8200)
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Deaths vs events by country", "Log scales; the six deadliest labelled")
cc = f[f.country_name != "Unknown"].groupby("country_name").agg(e=("event_id", "count"), d=("fatality_count", "sum")); cc = cc[cc.d > 0]
ax.scatter(cc.e, cc.d, s=18, color=BLUE, alpha=0.7, lw=0); ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("events"); ax.set_ylabel("deaths")
ax.set_xlim(0.8, 1.2e4); ax.set_ylim(0.8, 4e4)
offs = {"India": (6, 4), "China": (-34, 6), "Afghanistan": (6, 3), "Philippines": (8, -11), "Indonesia": (8, 2), "Brazil": (-34, -12)}
for n, o in offs.items():
    r = cc.loc[n]; ax.annotate(n, (r.e, r.d), fontsize=7.5, xytext=o, textcoords="offset points")
ax = fig.add_subplot(gs[1, :]); ax_title(ax, "15 deadliest events"); ax.axis("off"); ax.set_title("15 deadliest events", loc="left", fontsize=10.5, fontweight="bold")
dd = pd.DataFrame(R["deadliest"]).head(15); hd = ["Date", "Place", "Country", "Trigger", "Size", "Deaths"]; xs = [0.0, 0.1, 0.5, 0.64, 0.8, 0.95]
for x, h_ in zip(xs, hd): ax.text(x, 0.93, h_, fontweight="bold", fontsize=8, transform=ax.transAxes, ha="right" if h_ == "Deaths" else "left")
for i, r in dd.iterrows():
    yy = 0.84 - i * 0.058; vals = [str(r.event_date)[:10], str(r.event_title)[:38], r.country_name, r.trigger, r["size"], nf(r.fatality_count)]
    for x, v, h_ in zip(xs, vals, hd): ax.text(x, yy, v, fontsize=7.8, transform=ax.transAxes, ha="right" if h_ == "Deaths" else "left")
save(fig, "07_fatalities_impact.png")

# ================================================================ 8 India
ind = f[f.country_name == "India"]
fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
fig.text(0.02, 0.955, "India focus", fontsize=17, fontweight="bold", va="center")
fig.text(0.02, 0.918, f"{R['india_jjas_pct']}% of India's landslides fall in June to September, the southwest monsoon.", fontsize=10, color=MUTED, va="center")
fig.text(0.98, 0.955, "Preview of Power BI page", fontsize=8, color=MUTED, ha="right", va="center")
mh = ind[ind.admin_division == "Maharashtra"]
cards(fig, [("India events", nf(len(ind))), ("India deaths", nf(ind.fatality_count.sum())), ("Jun to Sep share", f"{R['india_jjas_pct']}%"),
            ("Maharashtra events", str(len(mh))), ("Maharashtra deaths", nf(mh.fatality_count.sum()))])
gs = GridSpec(2, 3, figure=fig, left=0.14, right=0.985, top=0.67, bottom=0.075, hspace=0.62, wspace=0.62)
ax = fig.add_subplot(gs[0, 0]); ax_title(ax, "Events by state, top 10"); st = pd.DataFrame(R["india_states"]).head(10); hbar(ax, st.admin_division, st.events, BLUE)
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Deaths by state, top 10", "Uttarakhand = Kedarnath 2013"); s2 = pd.DataFrame(R["india_states"]).sort_values("fatalities", ascending=False).head(10); hbar(ax, s2.admin_division, s2.fatalities, MAG)
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "India events by month"); im = ind[ind.core_period_flag == 1].groupby("month_num").size().reindex(range(1, 13), fill_value=0)
ax.bar(mn, im.values, color=[BLUE if m in (6, 7, 8, 9) else "#9DBFE9" for m in range(1, 13)], width=0.7); ax.tick_params(axis="x", labelsize=7)
ax = fig.add_subplot(gs[1, 0]); ax_title(ax, "India events by year"); iy = pd.Series({int(k): v for k, v in R["india_year"].items()}); ax.bar(iy.index, iy.values, color=BLUE, width=0.7); ax.set_xticks(iy.index[::2]); ax.tick_params(labelsize=8)
ax = fig.add_subplot(gs[1, 1]); ax_title(ax, "South Asia: events and deaths"); sa = pd.DataFrame(R["south_asia"]); xs = np.arange(len(sa))
ax.bar(xs - 0.2, sa.events, 0.4, color=BLUE, label="events"); ax.bar(xs + 0.2, sa.fatalities, 0.4, color=MAG, label="deaths"); ax.set_xticks(xs); ax.set_xticklabels([{"India": "IN", "Nepal": "NP", "Pakistan": "PK", "Sri Lanka": "LK", "Bangladesh": "BD", "Bhutan": "BT", "Afghanistan": "AF"}[c] for c in sa.country_name], fontsize=8); ax.legend(frameon=False, fontsize=8)
ax = fig.add_subplot(gs[1, 2]); ax_title(ax, "Maharashtra by month", f"{len(mh)} events, {int(mh.fatality_count.sum())} deaths")
mm = mh.groupby("month_num").size().reindex(range(1, 13), fill_value=0); ax.bar(mn, mm.values, color=[AQUA if m in (6, 7, 8, 9) else "#9ADBC3" for m in range(1, 13)], width=0.7); ax.tick_params(axis="x", labelsize=7)
save(fig, "08_india_focus.png")

# ================================================================ 9 data quality
fig, gs = page("09", "Data quality and bias", "How far can the numbers be trusted? Fatalities and settings have gaps, and one agency supplies 7% of all rows.", 2, 3)
ax = fig.add_subplot(gs[0, 0]); ax_title(ax, "Missing, unknown or estimated, % of events")
cp = {"Injuries missing": R["completeness"]["injury_count"], "Setting unknown": R["completeness"]["setting unknown"], "Location > 10 km / unknown": R["completeness"]["location accuracy > 10 km or unknown"],
      "Trigger unknown": R["completeness"]["trigger unknown"], "Country estimated": 100 * (f.country_source != "Original").mean(), "Size unknown": R["completeness"]["size unknown"], "Deaths missing": R["completeness"]["fatality_count"]}
cp = dict(sorted(cp.items(), key=lambda kv: -kv[1])); hbar(ax, list(cp), list(cp.values()), MAG, fmt=lambda v: f"{v:.1f}%")
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Events by source type"); sg = f.groupby("source_group").size().sort_values(ascending=False); hbar(ax, sg.index, sg.values, BLUE)
ax = fig.add_subplot(gs[0, 2]); ax_title(ax, "Top 8 sources"); ss = pd.Series(R["sources"]).head(8); hbar(ax, [s[:22] for s in ss.index], ss.values, AQUA)
ax = fig.add_subplot(gs[1, 0]); ax_title(ax, "Median days from event to submission", "Newer events are still being added"); lg = pd.Series({int(k): v for k, v in R["lag_by_year"].items()}); ax.bar(lg.index, lg.values, color=VIO, width=0.7); ax.set_xticks(lg.index[::2]); ax.tick_params(labelsize=8)
ax = fig.add_subplot(gs[1, 1]); ax_title(ax, "Location accuracy"); ac = pd.Series({k: v for k, v in R["accuracy"].items()}); ac.index = ["Unknown" if k == "-1.0" else ("Exact" if k == "0.0" else f"{int(float(k))} km") for k in ac.index]
ax.bar(ac.index, ac.values, color=BLUE, width=0.65); ax.tick_params(axis="x", labelsize=7, rotation=30)
ax = fig.add_subplot(gs[1, 2]); ax_title(ax, "Fatal event rate by source type", "Official records are rarely fatal"); fr = pd.Series(R["fatal_by_source_group"]) * 100; hbar(ax, fr.index, fr.values, MAG, fmt=lambda v: f"{v:.1f}%")
save(fig, "09_data_quality.png")

# ================================================================ 10 drivers
fig, gs = page("10", "Drivers of fatal events", "Logistic model, AUC 0.85. Most of the skill is reporting differences, not geology. Read with care.", 1, 2)
gs.update(left=0.25, wspace=0.4)
co = pd.Series(R["model_coef"]); co = co[~co.index.str.contains("infrequent")]; co = pd.concat([co.sort_values().head(8), co.sort_values().tail(8)]).sort_values()
ax = fig.add_subplot(gs[0, 0]); ax_title(ax, "Strongest drivers (log-odds of a fatal event)", "Negative = less likely to be fatal")
lab = [c.replace("_", " ").replace("setting group ", "setting: ").replace("size ", "size: ").replace("continent ", "continent: ").replace("trigger group ", "trigger: ").replace("category group ", "type: ") for c in co.index]
y = np.arange(len(co)); ax.barh(y, co.values, color=[MAG if v < 0 else BLUE for v in co.values], height=0.65); ax.set_yticks(y); ax.set_yticklabels(lab, fontsize=8); ax.axvline(0, color=INK, lw=1)
ax.grid(axis="x", color=GRID); ax.grid(axis="y", visible=False)
ax = fig.add_subplot(gs[0, 1]); ax_title(ax, "Fatal event rate by population of the area", "Rises with population, but the largest band has only 22 events")
pb = pd.DataFrame(R["pop_band"]); ax.bar(pb.pop_band, pb.fatal_rate, color=VIO, width=0.6)
for i, (v, n) in enumerate(zip(pb.fatal_rate, pb.events)): ax.text(i, v + 2, f"{v:.0f}%\nn={nf(n)}", ha="center", fontsize=8)
ax.set_ylim(0, 100)
save(fig, "10_drivers.png")
