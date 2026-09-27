import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Lebanon Food Prices 2000-2023", layout="wide")

FOOD, GEN, INFL = "Food CPI (2015=100)", "General CPI (2015=100)", "Food price inflation (%)"
RED, BLUE, GREY = "#d62728", "#1f77b4", "#9a9a9a"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@st.cache_data
def load():
    df = pd.read_csv("data/lebanon_cpi.csv", parse_dates=["date"])
    wide = df.pivot_table(index="date", columns="item", values="value").reset_index()
    wide["year"] = wide["date"].dt.year
    wide["month"] = wide["date"].dt.month
    return wide


data = load()

# ---------------- Context ----------------
st.title("Lebanon's food prices: from stable to out of control")
st.markdown(
    "For almost twenty years, food prices in Lebanon rose a few percent a year. "
    "Then the banking and currency crisis that started in **October 2019** broke that pattern. "
    "This page uses FAO's monthly consumer price data for Lebanon (via AUB's PKGCubes portal) "
    "to show how big the shock was, when it hit, and how much harder it hit food than everything else."
)
with st.expander("About the data"):
    st.markdown(
        "- **Source:** AUB PKGCubes portal, Economical Data > consumer-price-indices. Original publisher: FAO (FAOSTAT).\n"
        "- **Coverage:** monthly, January 2000 to September 2023 (843 observations).\n"
        "- **Food CPI / General CPI:** price level indexed to 2015 = 100. A value of 1,000 means prices are 10x their 2015 level.\n"
        "- **Food price inflation:** % change in food prices vs the same month a year earlier.\n"
        "- **Caveat:** 2000-2006 values rise almost linearly, which suggests the source interpolated them."
    )

# ---------------- Linked controls ----------------
st.subheader("Explore")
c1, c2 = st.columns([3, 2])
with c1:
    start, end = st.slider(
        "1. Choose the period to look at",
        min_value=2000, max_value=2023, value=(2010, 2023),
        help="Narrow the window to compare calm years with crisis years.",
    )
window = data[(data.year >= start) & (data.year <= end)]

# Widget 2 depends on widget 1: only years inside the window are offered,
# and the default is the worst year for food inflation in that window.
annual = window.groupby("year", as_index=False)[INFL].mean().dropna()
years_in_window = list(range(start, end + 1))
worst_year = int(annual.loc[annual[INFL].idxmax(), "year"]) if not annual.empty else end
with c2:
    focus = st.selectbox(
        "2. Drill into one year (options follow your period)",
        options=years_in_window,
        index=years_in_window.index(worst_year),
        help="Defaults to the year with the highest food inflation in your period.",
    )

# ---------------- Headline numbers for the selection ----------------
first, last = window.dropna(subset=[FOOD, GEN]).iloc[0], window.dropna(subset=[FOOD, GEN]).iloc[-1]
food_x, gen_x = last[FOOD] / first[FOOD], last[GEN] / first[GEN]
focus_infl = annual.loc[annual.year == focus, INFL]
m1, m2, m3 = st.columns(3)
m1.metric(f"Food prices, {first.date:%b %Y} to {last.date:%b %Y}", f"{food_x:,.1f}x")
m2.metric("General prices, same period", f"{gen_x:,.1f}x")
m3.metric(f"Average food inflation in {focus}",
          f"{focus_infl.iloc[0]:,.0f}%" if not focus_infl.empty else "n/a")

# ---------------- Chart 1: line ----------------
long = window.melt(id_vars=["date"], value_vars=[GEN, FOOD], var_name="series", value_name="index").dropna()
fig1 = px.line(long, x="date", y="index", color="series",
               color_discrete_map={GEN: BLUE, FOOD: RED},
               labels={"index": "Index, 2015 = 100 (log scale)", "date": "", "series": ""})
use_log = (window[FOOD].max() / window[FOOD].min()) > 5  # log only when the range is wide
fig1.update_yaxes(type="log" if use_log else "linear", dtick=1 if use_log else None)
if not use_log:
    fig1.update_yaxes(title="Index, 2015 = 100")
fig1.add_vrect(x0=f"{focus}-01-01", x1=f"{focus}-12-31", fillcolor=RED, opacity=0.08, line_width=0,
               annotation_text=str(focus), annotation_position="top left")
if start <= 2019 <= end:
    fig1.add_vline(x="2019-10-01", line_dash="dot", line_color=GREY)
fig1.update_layout(template="plotly_white", legend=dict(orientation="h", y=1.1, x=0),
                   margin=dict(t=30, b=10), height=420)

# ---------------- Chart 2: bar (annual) ----------------
annual["color"] = annual.year.apply(lambda y: "Selected year" if y == focus else ("Crisis" if y >= 2020 else "Before crisis"))
fig2 = px.bar(annual, x="year", y=INFL, color="color",
              color_discrete_map={"Selected year": RED, "Crisis": "#f2a0a1", "Before crisis": GREY},
              text=annual[INFL].round(0).astype(int),
              labels={INFL: "Average food inflation (%)", "year": "", "color": ""})
fig2.update_traces(textposition="outside", cliponaxis=False)
fig2.update_layout(template="plotly_white", legend=dict(orientation="h", y=1.1, x=0),
                   margin=dict(t=30, b=10), height=420, xaxis=dict(dtick=1 if end - start <= 12 else 2))

left, right = st.columns(2)
left.markdown("**Price level: food vs everything else**")
left.plotly_chart(fig1, width="stretch")
right.markdown("**Food inflation per year** (selected year in dark red)")
right.plotly_chart(fig2, width="stretch")

# ---------------- Chart 3: drill-down into the chosen year ----------------
yr = data[data.year == focus].sort_values("month")
fig3 = go.Figure()
fig3.add_bar(x=[MONTHS[m - 1] for m in yr.month], y=yr[INFL], marker_color=RED, name="Food inflation (%)",
             text=yr[INFL].round(0), textposition="outside", cliponaxis=False)
fig3.update_layout(template="plotly_white", height=320, margin=dict(t=40, b=10),
                   title=f"{focus}, month by month: food inflation vs same month a year earlier",
                   yaxis_title="Food inflation (%)")
if yr[INFL].notna().any():
    st.plotly_chart(fig3, width="stretch")
else:
    st.info(f"No inflation figures for {focus}: inflation compares each month with the year before, and the data starts in 2000.")

# ---------------- Insights ----------------
st.subheader("What the data says")
i1, i2 = st.columns(2)
with i1:
    st.markdown(
        "**1. Food took the hardest hit.** From September 2019 to September 2023, food prices rose about "
        "**208x** while general prices rose about **46x**. By 2023 the food index was over 4x the general index. "
        "Set the period to 2019-2023 to see the gap open up."
    )
with i2:
    st.markdown(
        "**2. The shock did not fade.** Food inflation averaged about 6% a year from 2001 to 2019, then "
        "**254% in 2020, 317% in 2021, 292% in 2022 and 275% in 2023**. Drill into 2020 to see the break: "
        "38% in March, 150% in April, over 400% by October."
    )

# ---------------- Design justifications ----------------
st.subheader("Design notes")
with st.expander("Why a period slider (control 1)"):
    st.markdown(
        "**User question:** How do prices during the crisis compare with the years before it, and how big was the change over a period I care about?\n\n"
        "**Why this widget:** A range slider fits a continuous, ordered variable like years: one drag sets both ends, and the user always sees where the window sits in the full 2000-2023 span. "
        "I considered a multiselect of years, but it allows gaps (e.g. 2005, 2017, 2022), which breaks the time series and makes the line chart misleading. "
        "Two date pickers were also an option, but they are slower and hide the overall span.\n\n"
        "**Course concept:** *Providing context and reducing clutter.* The full series runs from 37 to 22,000, so pre-crisis movements are invisible next to the crisis. "
        "Narrowing the window rescales both charts (the line chart switches to a linear axis when the range allows it), so the calm years become readable. "
        "The headline numbers above the charts recompute for the chosen window, giving the reader the context in plain terms."
    )
with st.expander("Why a linked year drill-down (control 2)"):
    st.markdown(
        "**User question:** What happened inside a specific year, and when exactly did things turn?\n\n"
        "**Why this widget:** A single-choice dropdown fits because the drill-down shows one year at a time. Its options are generated from the period slider, "
        "so you can only pick years inside your window, and it defaults to the worst year in that window, which points the user to the most important year first. "
        "I considered radio buttons, but 24 options would clutter the page, and a second slider would look like it controls the same thing as the first.\n\n"
        "**Course concept:** *Focusing attention and overview first, details on demand.* The chosen year is highlighted in the line chart (shaded band) and the bar chart (the only saturated bar), "
        "and the monthly chart below gives the detail. The user moves from overview (period) to detail (year to months) instead of filtering two things separately."
    )

st.caption("Data: FAO via AUB PKGCubes (linked.aub.edu.lb). Built with Streamlit and Plotly for MSBA 325.")
