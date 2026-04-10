import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AutoLog — Car Maintenance Tracker",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

/* Background */
.stApp { background-color: #0e0f11; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #141519 !important;
    border-right: 1px solid #2a2c34;
}

/* Cards */
.metric-card {
    background: linear-gradient(135deg, #1a1c23 0%, #1f2129 100%);
    border: 1px solid #2a2c34;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: #f0f0f0;
}
.metric-sub {
    font-size: 11px;
    color: #4b5563;
    margin-top: 4px;
}

/* Category badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    letter-spacing: 0.5px;
}

/* Record row */
.record-card {
    background: #1a1c23;
    border: 1px solid #2a2c34;
    border-left: 3px solid #e8854d;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.record-card:hover { border-left-color: #f5a76c; }

/* Section header */
.section-tag {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #e8854d;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-bottom: 4px;
}

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] select {
    background-color: #1a1c23 !important;
    border: 1px solid #2a2c34 !important;
    color: #e5e7eb !important;
    font-family: 'DM Mono', monospace !important;
    border-radius: 8px !important;
}

/* Buttons */
[data-testid="stFormSubmitButton"] button,
.stButton button {
    background: #e8854d !important;
    color: #0e0f11 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    letter-spacing: 1px !important;
}
[data-testid="stFormSubmitButton"] button:hover,
.stButton button:hover {
    background: #f5a76c !important;
    transform: translateY(-1px);
}

/* Streamlit default overrides */
.stSelectbox > div > div { background-color: #1a1c23 !important; }
div[data-testid="stMarkdownContainer"] p { color: #9ca3af; }

/* Table */
[data-testid="stDataFrame"] { border: 1px solid #2a2c34; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Data persistence ──────────────────────────────────────────────────────────
DATA_FILE = "maintenance_data.json"

CATEGORIES = [
    "🛢️  Oil Change",
    "🔋 Battery",
    "🔴 Brakes",
    "🌡️  Coolant",
    "💨 Air Filter",
    "🌀 Transmission",
    "🔩 Suspension",
    "💡 Lights / Electrical",
    "🚗 Tires / Rotation",
    "🔍 Inspection / Diagnostics",
    "⚙️  Engine Repair",
    "🧴 Fluid Top-Off",
    "🪟 Wipers / Belts",
    "📋 Other",
]

CAT_COLORS = {
    "Oil Change":       "#f59e0b",
    "Battery":          "#3b82f6",
    "Brakes":           "#ef4444",
    "Coolant":          "#06b6d4",
    "Air Filter":       "#10b981",
    "Transmission":     "#8b5cf6",
    "Suspension":       "#ec4899",
    "Lights / Electrical": "#fbbf24",
    "Tires / Rotation": "#6366f1",
    "Inspection / Diagnostics": "#14b8a6",
    "Engine Repair":    "#f97316",
    "Fluid Top-Off":    "#84cc16",
    "Wipers / Belts":   "#a78bfa",
    "Other":            "#6b7280",
}


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            raw = json.load(f)
        return raw
    return {"vehicles": {}, "records": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_cat_clean(cat_str):
    """Strip emoji prefix for dict lookups."""
    return cat_str.split("  ")[-1].strip() if "  " in cat_str else cat_str.split(" ", 1)[-1].strip()


# ── Init session state ────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<p class='section-tag'>AutoLog</p>", unsafe_allow_html=True)
    st.markdown("## 🔧 Car Tracker")
    st.markdown("---")

    st.markdown("<p class='section-tag'>Add Vehicle</p>", unsafe_allow_html=True)
    with st.form("add_vehicle_form"):
        v_name = st.text_input("Vehicle Name", placeholder="e.g. My Honda Civic")
        v_year = st.number_input("Year", min_value=1950, max_value=2030, value=2020, step=1)
        v_make = st.text_input("Make", placeholder="e.g. Honda")
        v_model = st.text_input("Model", placeholder="e.g. Civic")
        v_submit = st.form_submit_button("ADD VEHICLE")
        if v_submit and v_name:
            data["vehicles"][v_name] = {
                "year": v_year, "make": v_make, "model": v_model
            }
            save_data(data)
            st.success(f"Added {v_name}!")

    st.markdown("---")

    # Vehicle selector
    vehicles = list(data["vehicles"].keys())
    if vehicles:
        selected_vehicle = st.selectbox("📌 Active Vehicle", vehicles)
    else:
        selected_vehicle = None
        st.info("Add a vehicle above to get started.")

    st.markdown("---")
    st.markdown("<p style='color:#4b5563;font-size:11px;'>Data saved locally as JSON.</p>", unsafe_allow_html=True)

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("<p class='section-tag'>Dashboard</p>", unsafe_allow_html=True)
st.markdown("# AutoLog — Maintenance Tracker")
st.markdown("---")

# Filter records for selected vehicle
all_records = data.get("records", [])
if selected_vehicle:
    vehicle_records = [r for r in all_records if r["vehicle"] == selected_vehicle]
    vinfo = data["vehicles"].get(selected_vehicle, {})
else:
    vehicle_records = all_records

# ── KPI row ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_cost = sum(r.get("cost", 0) for r in vehicle_records)
total_services = len(vehicle_records)
last_service = max((r["date"] for r in vehicle_records), default="—")
avg_cost = total_cost / total_services if total_services else 0

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Services</div>
        <div class='metric-value'>{total_services}</div>
        <div class='metric-sub'>all time</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Spent</div>
        <div class='metric-value'>${total_cost:,.0f}</div>
        <div class='metric-sub'>cumulative</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Avg Cost / Service</div>
        <div class='metric-value'>${avg_cost:,.0f}</div>
        <div class='metric-sub'>per visit</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Last Service</div>
        <div class='metric-value' style='font-size:20px'>{last_service}</div>
        <div class='metric-sub'>most recent</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
if vehicle_records:
    df = pd.DataFrame(vehicle_records)
    df["date"] = pd.to_datetime(df["date"])
    df["cat_clean"] = df["category"].apply(get_cat_clean)
    df["cost"] = df["cost"].fillna(0).astype(float)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<p class='section-tag'>Spending by Category</p>", unsafe_allow_html=True)
        cat_spend = df.groupby("cat_clean")["cost"].sum().reset_index()
        colors = [CAT_COLORS.get(c, "#6b7280") for c in cat_spend["cat_clean"]]
        fig = go.Figure(go.Bar(
            x=cat_spend["cat_clean"], y=cat_spend["cost"],
            marker_color=colors, marker_line_width=0,
            text=[f"${v:,.0f}" for v in cat_spend["cost"]],
            textposition="outside", textfont=dict(color="#9ca3af", size=11),
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9ca3af", family="DM Mono"),
            xaxis=dict(tickangle=-30, gridcolor="#1f2129", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="#1f2129", tickprefix="$"),
            margin=dict(t=10, b=10, l=10, r=10), height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("<p class='section-tag'>Cost Over Time</p>", unsafe_allow_html=True)
        df_sorted = df.sort_values("date")
        df_sorted["cumulative"] = df_sorted["cost"].cumsum()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_sorted["date"], y=df_sorted["cumulative"],
            fill="tozeroy", line=dict(color="#e8854d", width=2),
            fillcolor="rgba(232,133,77,0.12)",
            mode="lines+markers", marker=dict(color="#e8854d", size=6),
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9ca3af", family="DM Mono"),
            xaxis=dict(gridcolor="#1f2129"),
            yaxis=dict(gridcolor="#1f2129", tickprefix="$"),
            margin=dict(t=10, b=10, l=10, r=10), height=300,
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Add record form ───────────────────────────────────────────────────────────
st.markdown("<p class='section-tag'>Log Service</p>", unsafe_allow_html=True)
st.markdown("### ➕ Add Maintenance Record")

if not selected_vehicle:
    st.warning("Select or add a vehicle in the sidebar first.")
else:
    with st.form("add_record_form", clear_on_submit=True):
        r1, r2, r3 = st.columns([2, 2, 1])
        with r1:
            r_category = st.selectbox("Category", CATEGORIES)
        with r2:
            r_date = st.date_input("Date", value=date.today())
        with r3:
            r_cost = st.number_input("Cost ($)", min_value=0.0, step=0.01, format="%.2f")

        r4, r5 = st.columns([2, 1])
        with r4:
            r_shop = st.text_input("Shop / Mechanic", placeholder="e.g. Jiffy Lube, DIY")
        with r5:
            r_mileage = st.number_input("Mileage", min_value=0, step=100)

        r_notes = st.text_area("Notes", placeholder="Details about the service, parts used, etc.", height=80)

        r_submit = st.form_submit_button("LOG SERVICE ›")
        if r_submit:
            record = {
                "vehicle": selected_vehicle,
                "category": r_category,
                "date": str(r_date),
                "cost": r_cost,
                "shop": r_shop,
                "mileage": r_mileage,
                "notes": r_notes,
                "created_at": str(datetime.now()),
            }
            data["records"].append(record)
            save_data(data)
            st.success("✅ Service logged!")
            st.rerun()

st.markdown("---")

# ── Records table ─────────────────────────────────────────────────────────────
st.markdown("<p class='section-tag'>History</p>", unsafe_allow_html=True)
st.markdown("### 📋 Service History")

if not vehicle_records:
    st.info("No records yet. Log your first service above.")
else:
    # Filters
    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        cat_options = ["All"] + sorted(set(get_cat_clean(r["category"]) for r in vehicle_records))
        filter_cat = st.selectbox("Filter by Category", cat_options)
    with f2:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Cost (High)", "Cost (Low)"])
    with f3:
        search_term = st.text_input("Search Notes / Shop", placeholder="Search...")

    # Apply filters
    filtered = vehicle_records.copy()
    if filter_cat != "All":
        filtered = [r for r in filtered if get_cat_clean(r["category"]) == filter_cat]
    if search_term:
        term = search_term.lower()
        filtered = [r for r in filtered if
                    term in r.get("notes", "").lower() or
                    term in r.get("shop", "").lower()]

    # Sort
    key_map = {
        "Date (Newest)": lambda r: r["date"],
        "Date (Oldest)": lambda r: r["date"],
        "Cost (High)":   lambda r: r.get("cost", 0),
        "Cost (Low)":    lambda r: r.get("cost", 0),
    }
    reverse_map = {"Date (Newest)": True, "Date (Oldest)": False,
                   "Cost (High)": True, "Cost (Low)": False}
    filtered.sort(key=key_map[sort_by], reverse=reverse_map[sort_by])

    st.markdown(f"<p style='color:#4b5563;font-size:12px;margin-bottom:12px'>{len(filtered)} record(s)</p>",
                unsafe_allow_html=True)

    # Render each record
    for i, rec in enumerate(filtered):
        cat_clean = get_cat_clean(rec["category"])
        color = CAT_COLORS.get(cat_clean, "#6b7280")
        cost_str = f"${rec.get('cost', 0):,.2f}" if rec.get("cost") else "—"
        mileage_str = f"{rec.get('mileage', 0):,} mi" if rec.get("mileage") else "—"
        shop_str = rec.get("shop", "—") or "—"
        notes_str = rec.get("notes", "") or ""

        with st.container():
            cols = st.columns([3, 2, 1.5, 1.5, 0.5])
            with cols[0]:
                st.markdown(
                    f"<span class='badge' style='background:{color}22;color:{color};border:1px solid {color}44'>{rec['category']}</span>"
                    f"<span style='margin-left:10px;font-size:13px;color:#e5e7eb;font-family:Syne,sans-serif;font-weight:600'>{shop_str}</span>",
                    unsafe_allow_html=True)
                if notes_str:
                    st.markdown(f"<p style='font-size:12px;color:#6b7280;margin:4px 0 0 0'>{notes_str[:120]}{'…' if len(notes_str)>120 else ''}</p>",
                                unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<p style='font-size:13px;color:#9ca3af;margin:0'>{rec['date']}</p>"
                            f"<p style='font-size:12px;color:#4b5563;margin:2px 0 0 0'>📍 {mileage_str}</p>",
                            unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<p style='font-size:16px;font-weight:700;color:#e8854d;font-family:Syne,sans-serif;margin:0'>{cost_str}</p>",
                            unsafe_allow_html=True)
            with cols[3]:
                pass
            with cols[4]:
                if st.button("🗑", key=f"del_{i}", help="Delete record"):
                    original_idx = data["records"].index(rec)
                    data["records"].pop(original_idx)
                    save_data(data)
                    st.rerun()
            st.markdown("<hr style='border:none;border-top:1px solid #1f2129;margin:8px 0'>", unsafe_allow_html=True)

    # Export
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬇️  Export as CSV"):
        df_export = pd.DataFrame(filtered)
        csv = df_export.to_csv(index=False)
        st.download_button("Download CSV", csv, "maintenance_log.csv", "text/csv")
