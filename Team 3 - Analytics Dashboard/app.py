import io
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SCE Transmission Findings | Team 3", page_icon="⚡", layout="wide")
st.title("SCE Transmission Planning Findings")
st.caption("Team 3 · Analytics Dashboard · Module 2")
st.markdown("Analyze normalized findings supplied by Team 2, with source details extracted by Team 1. Upload a CSV or use the clearly labeled illustrative data below.")

REQUIRED = ["report", "report_date", "facility", "contingency", "scenario", "loading_pct", "severity", "mitigation", "source_page"]
DEMO = pd.DataFrame([
    ["2026-2027 Preliminary", "2026-01-15", "Mesa 500 kV", "N-1: Line 1-2", "Summer Peak", 119.0, "High", "Series compensation / reconductoring under study", 24],
    ["2026-2027 Preliminary", "2026-01-15", "Mesa 500 kV", "N-1: Line 1-2", "Summer Peak Sensitivity", 112.0, "High", "Series compensation / reconductoring under study", 24],
    ["2026-2027 Preliminary", "2026-01-15", "Valley 230 kV", "N-1: Transformer A", "Summer Peak", 107.0, "Medium", "Transformer replacement evaluated", 38],
    ["2026-2027 Preliminary", "2026-01-15", "Canyon 500 kV", "N-1: Line 4-5", "Summer Peak", 103.0, "Low", "Not specified", 51],
    ["2025-2026 Final", "2025-01-10", "Mesa 500 kV", "N-1: Line 1-2", "Summer Peak", 116.0, "High", "Reconductoring recommended", 29],
    ["2025-2026 Final", "2025-01-10", "Valley 230 kV", "N-1: Transformer A", "Summer Peak", 101.0, "Low", "Transformer replacement evaluated", 44],
    ["2025-2026 Final", "2025-01-10", "Harbor 230 kV", "N-1: Line 8-9", "Summer Peak", 105.0, "Medium", "Not specified", 63],
], columns=REQUIRED)

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload normalized findings CSV", type=["csv"])
    use_demo = st.toggle("Use illustrative sample data", value=uploaded is None)
    st.caption("The built-in sample is illustrative only; it is not asserted to be extracted from the SCE PDF.")

if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        st.stop()
    source_label = uploaded.name
elif use_demo:
    raw = DEMO.copy()
    source_label = "Illustrative sample data"
else:
    st.info("Upload a normalized findings CSV or enable the illustrative sample data.")
    st.stop()

missing = sorted(set(REQUIRED) - set(raw.columns))
if missing:
    st.error("CSV is missing required columns: " + ", ".join(missing))
    st.markdown("Required: `" + "`, `".join(REQUIRED) + "`.")
    st.stop()

df = raw.copy()
df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
# Preserve raw loading values (including <100 and NotConv) while deriving a numeric metric when possible.
df["loading_raw"] = df["loading_pct"].astype(str).str.strip()
df["loading_numeric"] = pd.to_numeric(df["loading_raw"].str.replace("%", "", regex=False), errors="coerce")
df["loading_status"] = np.where(df["loading_numeric"].notna(), "Numeric", df["loading_raw"].replace("", "Unknown"))
df["severity"] = df["severity"].fillna("Unclassified").astype(str)
for col in ["report", "facility", "contingency", "scenario", "mitigation"]:
    df[col] = df[col].fillna("Unknown").astype(str)
df["source_page"] = df["source_page"].astype(str)
df["overload"] = df["loading_numeric"].gt(100)

with st.sidebar:
    reports = sorted(df["report"].unique())
    chosen_reports = st.multiselect("Reports", reports, default=reports)
    facilities = sorted(df.loc[df.report.isin(chosen_reports), "facility"].unique())
    chosen_facilities = st.multiselect("Facilities", facilities, default=facilities)
    severity_vals = sorted(df["severity"].unique())
    chosen_severity = st.multiselect("Severity", severity_vals, default=severity_vals)
    threshold = st.slider("Overload threshold (%)", min_value=80, max_value=120, value=100)

view = df[df.report.isin(chosen_reports) & df.facility.isin(chosen_facilities) & df.severity.isin(chosen_severity)].copy()
view["overload"] = view.loading_numeric.gt(threshold)
if view.empty:
    st.warning("No findings match these filters.")
    st.stop()
st.caption(f"Data source: {source_label} · {len(view):,} findings shown · Raw loading values are retained for traceability.")

numeric = view.loading_numeric.dropna()
recurrence = view.groupby(["facility", "contingency"], dropna=False).agg(
    recurrence_reports=("report", "nunique"), occurrences=("report", "size"),
    peak_loading=("loading_numeric", "max"), mean_loading=("loading_numeric", "mean"),
    high_severity=("severity", lambda s: s.str.lower().isin(["high", "critical"]).sum()),
    mitigation=("mitigation", "first")
).reset_index()
recurrence["persistence_score"] = recurrence.recurrence_reports * (recurrence.peak_loading.fillna(0).clip(lower=0) / 100) * (1 + recurrence.high_severity)
recurrence = recurrence.sort_values(["persistence_score", "peak_loading"], ascending=False)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Findings", f"{len(view):,}")
m2.metric(f"Above {threshold}%", f"{int(view.overload.sum()):,}")
m3.metric("Facilities", f"{view.facility.nunique():,}")
m4.metric("Peak numeric loading", f"{numeric.max():.1f}%" if not numeric.empty else "N/A")

tab_overview, tab_findings, tab_recurrence, tab_compare = st.tabs(["Overview", "Findings", "Recurrence & ranking", "Comparisons"])
with tab_overview:
    left, right = st.columns(2)
    with left:
        chart_df = view.dropna(subset=["loading_numeric"])
        if chart_df.empty:
            st.info("No numeric loading values to chart.")
        else:
            fig = px.bar(chart_df, x="facility", y="loading_numeric", color="report", hover_data=["contingency", "scenario", "severity"], barmode="group", labels={"loading_numeric": "Loading (%)"}, title="Loading by facility and report")
            fig.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Threshold {threshold}%")
            st.plotly_chart(fig, use_container_width=True)
    with right:
        counts = view.groupby("severity", as_index=False).size().rename(columns={"size": "findings"})
        st.plotly_chart(px.pie(counts, names="severity", values="findings", title="Findings by severity", hole=.35), use_container_width=True)
    st.subheader("Most common mitigation descriptions")
    mitigation_counts = view.groupby("mitigation", as_index=False).size().sort_values("size", ascending=False).head(10)
    st.plotly_chart(px.bar(mitigation_counts, x="size", y="mitigation", orientation="h", labels={"size": "Findings"}), use_container_width=True)
with tab_findings:
    cols = ["report", "report_date", "facility", "contingency", "scenario", "loading_raw", "severity", "mitigation", "source_page"]
    st.dataframe(view[cols].sort_values(["report", "facility", "contingency"]), use_container_width=True, hide_index=True)
    st.download_button("Download filtered findings CSV", view[cols].to_csv(index=False).encode("utf-8"), "filtered_findings.csv", "text/csv")
with tab_recurrence:
    st.caption("Persistence ranks facility/contingency pairs using report recurrence, peak loading, and count of high/critical findings. Use as a screening aid; it is not an engineering risk score.")
    st.dataframe(recurrence, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(recurrence.head(15).sort_values("persistence_score"), x="persistence_score", y="facility", color="recurrence_reports", orientation="h", hover_data=["contingency", "peak_loading", "occurrences"], title="Highest persistence scores"), use_container_width=True)
with tab_compare:
    st.subheader("Baseline vs sensitivity")
    scenarios = sorted(view.scenario.unique())
    base = st.selectbox("Baseline scenario", scenarios, key="base")
    sensitivity = st.selectbox("Sensitivity scenario", scenarios, index=min(1, len(scenarios)-1), key="sens")
    paired = view[view.scenario.isin([base, sensitivity])].pivot_table(index=["facility", "contingency"], columns="scenario", values="loading_numeric", aggfunc="max").reset_index()
    if base in paired and sensitivity in paired:
        paired["change_pct_points"] = paired[sensitivity] - paired[base]
        st.dataframe(paired, use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(paired.dropna(subset=["change_pct_points"]), x="facility", y="change_pct_points", color="change_pct_points", title=f"Change: {sensitivity} minus {base}", labels={"change_pct_points": "Loading change (percentage points)"}), use_container_width=True)
    else:
        st.info("Both scenarios need numeric readings for a paired comparison.")
    st.subheader("Cross-report comparison")
    cross = view.pivot_table(index=["facility", "contingency"], columns="report", values="loading_numeric", aggfunc="max").reset_index()
    st.dataframe(cross, use_container_width=True, hide_index=True)

st.divider()
st.caption("Traceability: each row retains report, scenario, and source page fields. Confirm extracted values against the cited source before engineering use.")
