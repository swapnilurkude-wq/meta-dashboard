import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🚀 Ads Dashboard Meta ads")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

google_sheet_csv_url = (
    "https://docs.google.com/spreadsheets/d/14KA90yocZci3ZJud3XYiM2-78HZFF3fcTbHpYNr_bY8/export?format=csv&gid=838145140"
)

data_source = "Uploaded CSV"

if uploaded_file is None:
    try:
        df = pd.read_csv(google_sheet_csv_url)
        df.columns = df.columns.str.strip()
        data_source = "Google Sheet"
        st.success("✅ Loaded daily Google Sheet data")
    except Exception:
        st.warning("Could not load Google Sheet automatically. Upload a CSV to continue.")
        df = None
else:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

if df is not None:

    # =========================
    # 🧹 CLEAN DATA
    # =========================
    day_col = next((col for col in df.columns if "day" in col.lower()), None)

    if day_col is None:
        st.error("❌ Day column not found")
        st.write(df.columns)
        st.stop()

    df.rename(columns={day_col: "Day"}, inplace=True)
    df["Day"] = pd.to_datetime(df["Day"], errors="coerce")

    # Numeric Fix
    numeric_cols = ["Spends", "Total Leads DB", "Clicks", "Impression"]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("â‚¹", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df[df["Day"].notna()]

    st.sidebar.markdown("**Data source:** " + data_source)
    st.sidebar.markdown(
        f"Rows: {len(df)}  \nDate range: {df['Day'].min().date()} - {df['Day'].max().date()}"
    )

    # =========================
    # 📅 FILTERS
    # =========================
    st.sidebar.header("📅 Filters")

    start_date = st.sidebar.date_input("Start Date", df["Day"].min())
    end_date = st.sidebar.date_input("End Date", df["Day"].max())

    filtered_df = df[
        (df["Day"] >= pd.to_datetime(start_date)) &
        (df["Day"] <= pd.to_datetime(end_date))
    ]

    # Campaign Filter
    if "Campaign name" in filtered_df.columns:
        campaigns = sorted(filtered_df["Campaign name"].dropna().unique())
        selected_campaigns = st.sidebar.multiselect("Campaign", ["All"] + campaigns, default=["All"])
        if "All" not in selected_campaigns:
            filtered_df = filtered_df[filtered_df["Campaign name"].isin(selected_campaigns)]

    # Ad Set Filter
    if "Ad set name" in filtered_df.columns:
        adsets = sorted(filtered_df["Ad set name"].dropna().unique())
        selected_adsets = st.sidebar.multiselect("Ad Set", ["All"] + adsets, default=["All"])
        if "All" not in selected_adsets:
            filtered_df = filtered_df[filtered_df["Ad set name"].isin(selected_adsets)]

    # Ad Filter
    if "Ad name" in filtered_df.columns:
        ads = sorted(filtered_df["Ad name"].dropna().unique())
        selected_ads = st.sidebar.multiselect("Ad", ["All"] + ads, default=["All"])
        if "All" not in selected_ads:
            filtered_df = filtered_df[filtered_df["Ad name"].isin(selected_ads)]

    # Top Performers Ranking Metric
    ranking_metric = st.sidebar.selectbox(
        "Top Performers Ranking Metric",
        ["Leads", "CPL", "CTR", "Spend"],
        index=0,
        help="Choose how to rank top creatives and campaigns. Lower CPL is better; higher others are better."
    )

    if filtered_df.empty:
        st.warning("No data available")
        st.stop()

    # =========================
    # 📊 KEY METRICS
    # =========================
    spend = filtered_df["Spends"].sum()
    leads = filtered_df["Total Leads DB"].sum()
    clicks = filtered_df["Clicks"].sum()
    impressions = filtered_df["Impression"].sum()

    cpl = spend / leads if leads != 0 else 0
    ctr = (clicks / impressions * 100) if impressions != 0 else 0
    cpc = spend / clicks if clicks != 0 else 0
    conversion_rate = (leads / clicks * 100) if clicks != 0 else 0

    st.subheader("📊 Key Metrics")

    c1, c2, c3, c4 = st.columns(4)
    c5, c6 = st.columns(2)

    c1.metric("💰 Spend", f"{spend:.1f}")
    c2.metric("📩 Leads", int(leads))
    c3.metric("📉 CPL", f"{cpl:.1f}")
    c4.metric("📊 CTR (%)", f"{ctr:.1f}")

    c5.metric("💸 CPC", f"{cpc:.1f}")
    c6.metric("🔄 Conversion Rate (%)", f"{conversion_rate:.1f}")

    # =========================
    # 📈 LEADS TREND
    # =========================
    st.subheader("📈 Leads Trend")
    trend = filtered_df.groupby("Day")["Total Leads DB"].sum()
    st.line_chart(trend)

    # =========================
    # 📋 DATA TABLE
    # =========================
    st.subheader("📋 Data Table")

    table_df = filtered_df.copy()

    table_df["CPL"] = table_df["Spends"] / table_df["Total Leads DB"].replace(0, pd.NA)
    table_df["CPC"] = table_df["Spends"] / table_df["Clicks"].replace(0, pd.NA)
    table_df["CTR (%)"] = (table_df["Clicks"] / table_df["Impression"].replace(0, pd.NA)) * 100
    table_df["Conversion Rate (%)"] = (table_df["Total Leads DB"] / table_df["Clicks"].replace(0, pd.NA)) * 100

    table_df = table_df.replace([float("inf"), -float("inf")], 0).round(2)

    cols = [
        "Campaign name", "Ad set name", "Ad name",
        "Spends", "Total Leads DB", "Clicks", "Impression",
        "CPL", "CTR (%)", "CPC", "Conversion Rate (%)"
    ]

    cols = [c for c in cols if c in table_df.columns]
    table_df = table_df[cols]

    total_spend = table_df["Spends"].sum()
    total_leads = table_df["Total Leads DB"].sum()
    total_clicks = table_df["Clicks"].sum()
    total_impressions = table_df["Impression"].sum()

    total_row = pd.DataFrame([{
        "Campaign name": "TOTAL",
        "Ad set name": "",
        "Ad name": "",
        "Spends": round(total_spend, 2),
        "Total Leads DB": int(total_leads),
        "Clicks": int(total_clicks),
        "Impression": int(total_impressions),
        "CPL": round(total_spend / total_leads, 2) if total_leads != 0 else 0,
        "CTR (%)": round((total_clicks / total_impressions) * 100, 2) if total_impressions != 0 else 0,
        "CPC": round(total_spend / total_clicks, 2) if total_clicks != 0 else 0,
        "Conversion Rate (%)": round((total_leads / total_clicks) * 100) if total_clicks != 0 else 0
    }])

    final_df = pd.concat([table_df, total_row], ignore_index=True)
    st.dataframe(final_df)

    # =========================
    # 📊 WEEKLY TABLE (FINAL)
    # =========================
    st.subheader("📊 Current Week vs Last Week (Table)")

    weekly_df = filtered_df.sort_values("Day")
    max_date = weekly_df["Day"].max()

    current_week = weekly_df[weekly_df["Day"] >= (max_date - pd.Timedelta(days=6))]
    previous_week = weekly_df[
        (weekly_df["Day"] >= (max_date - pd.Timedelta(days=13))) &
        (weekly_df["Day"] < (max_date - pd.Timedelta(days=6)))
    ]

    def calc(df):
        spend = df["Spends"].sum()
        leads = df["Total Leads DB"].sum()
        clicks = df["Clicks"].sum()
        impressions = df["Impression"].sum()

        cpl = spend / leads if leads != 0 else 0
        ctr = (clicks / impressions * 100) if impressions != 0 else 0
        cpc = spend / clicks if clicks != 0 else 0

        return spend, leads, cpl, ctr, cpc

    cw = calc(current_week)
    pw = calc(previous_week)

    def pct(curr, prev):
        return ((curr - prev) / prev * 100) if prev != 0 else 0

    weekly_table = pd.DataFrame({
        "Metric": ["Spend", "Leads", "CPL", "CTR (%)", "CPC"],
        "Current Week": [cw[0], cw[1], cw[2], cw[3], cw[4]],
        "Last Week": [pw[0], pw[1], pw[2], pw[3], pw[4]],
        "% Change": [
            pct(cw[0], pw[0]),
            pct(cw[1], pw[1]),
            pct(cw[2], pw[2]),
            pct(cw[3], pw[3]),
            pct(cw[4], pw[4])
        ]
    }).round(2)

    # 🎯 COLOR
    def highlight(val):
        if val > 0:
            return "color: green; font-weight:bold"
        elif val < 0:
            return "color: red; font-weight:bold"
        return ""

    st.dataframe(weekly_table)

    # =========================
    # 🏆 TOP PERFORMERS
    # =========================
    st.subheader("🏆 Top Performing Creatives and Campaigns")

    # Define sorting based on metric
    def get_sort_columns(metric):
        if metric == "Leads":
            return ["Leads", "CTR"], [False, False]
        elif metric == "CPL":
            return ["CPL", "Leads"], [True, False]  # Ascending for CPL (lower better)
        elif metric == "CTR":
            return ["CTR", "Leads"], [False, False]
        elif metric == "Spend":
            return ["Spend", "Leads"], [False, False]
        else:
            return ["Leads", "CTR"], [False, False]

    sort_cols, ascending = get_sort_columns(ranking_metric)

    if "Ad name" in filtered_df.columns:
        top_creatives = (
            filtered_df
            .groupby("Ad name", dropna=False)
            .agg(
                Spend=("Spends", "sum"),
                Leads=("Total Leads DB", "sum"),
                Clicks=("Clicks", "sum"),
                Impressions=("Impression", "sum")
            )
            .assign(
                CPL=lambda d: d["Spend"] / d["Leads"].replace(0, pd.NA),
                CTR=lambda d: (d["Clicks"] / d["Impressions"].replace(0, pd.NA)) * 100
            )
            .sort_values(sort_cols, ascending=ascending)
            .head(5)
            .round(2)
        )
        st.markdown(f"**Top 5 Creatives by {ranking_metric}**")
        st.dataframe(top_creatives.reset_index())
    else:
        st.warning("Ad name column not found; top creatives cannot be calculated.")

    if "Campaign name" in filtered_df.columns:
        top_campaigns = (
            filtered_df
            .groupby("Campaign name", dropna=False)
            .agg(
                Spend=("Spends", "sum"),
                Leads=("Total Leads DB", "sum"),
                Clicks=("Clicks", "sum"),
                Impressions=("Impression", "sum")
            )
            .assign(
                CPL=lambda d: d["Spend"] / d["Leads"].replace(0, pd.NA),
                CTR=lambda d: (d["Clicks"] / d["Impressions"].replace(0, pd.NA)) * 100
            )
            .sort_values(sort_cols, ascending=ascending)
            .head(3)
            .round(2)
        )
        st.markdown(f"**Top 3 Campaigns by {ranking_metric}**")
        st.dataframe(top_campaigns.reset_index())
    else:
        st.warning("Campaign name column not found; top campaigns cannot be calculated.")

else:
    st.info("👆 Upload CSV to start")