"""
Simple scraping dashboard, built with Streamlit -- pure Python, no
separate HTML/JS frontend needed.

Run:
    uv add streamlit
    uv run streamlit run dashboard.py

It'll open in your browser automatically (usually localhost:8501).
Click the "🔄 Refresh" button anytime to pull the latest data --
Streamlit doesn't auto-poll the database on its own.
"""

import streamlit as st
from sqlalchemy import func, desc

from db.connection import SessionLocal
from db.models import Product, ScrapeRun

st.set_page_config(page_title="Production Scraper", page_icon="🟢", layout="wide")


def load_dashboard_data():
    session = SessionLocal()
    try:
        total_products = session.query(func.count(Product.id)).scalar()

        per_site_counts = dict(
            session.query(Product.source_site, func.count(Product.id))
            .group_by(Product.source_site)
            .all()
        )

        # Latest run per site -- used for both the status row and
        # "last run" timestamp. One query, small result set (one row
        # per site), simplest correct approach at this data volume.
        latest_runs = {}
        sites = session.query(ScrapeRun.site).distinct().all()
        for (site,) in sites:
            latest = (
                session.query(ScrapeRun)
                .filter(ScrapeRun.site == site)
                .order_by(desc(ScrapeRun.started_at))
                .first()
            )
            if latest:
                latest_runs[site] = latest

        recent_jobs = (
            session.query(ScrapeRun)
            .order_by(desc(ScrapeRun.started_at))
            .limit(10)
            .all()
        )

        return total_products, per_site_counts, latest_runs, recent_jobs
    finally:
        session.close()


def status_emoji(status: str) -> str:
    return {"success": "🟢", "failed": "🔴", "running": "🟡"}.get(status, "⚪")


def status_label(status: str) -> str:
    return {"success": "Completed", "failed": "Failed", "running": "Running..."}.get(
        status, status
    )


# ---------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        "<h2 style='text-align: center;'>Production Scraper 🟢</h2>",
        unsafe_allow_html=True,
    )

if st.button("🔄 Refresh"):
    st.rerun()

total_products, per_site_counts, latest_runs, recent_jobs = load_dashboard_data()

overall_last_run = max(
    (r.finished_at or r.started_at for r in latest_runs.values()),
    default=None,
)

# ---------------------------------------------------------------
# TOP METRIC CARDS
# ---------------------------------------------------------------
metric_cols = st.columns(4)

metric_cols[0].metric("Products", f"{total_products:,}")
metric_cols[1].metric("Myntra", f"{per_site_counts.get('myntra', 0):,}")
metric_cols[2].metric("Meesho", f"{per_site_counts.get('meesho', 0):,}")
metric_cols[3].metric(
    "Last Run",
    overall_last_run.strftime("%I:%M %p") if overall_last_run else "—",
)

st.divider()

# ---------------------------------------------------------------
# SCRAPING STATUS
# ---------------------------------------------------------------
st.subheader("Scraping Status")

for site, run in latest_runs.items():
    st.write(f"{site.capitalize():<10} {status_emoji(run.status)} {status_label(run.status)}")

if not latest_runs:
    st.caption("No runs recorded yet.")

st.divider()

# ---------------------------------------------------------------
# RECENT JOBS TABLE
# ---------------------------------------------------------------
st.subheader("Recent Jobs")

if recent_jobs:
    table_rows = [
        {
            "Source": run.site.capitalize(),
            "Query": run.query,
            "Status": f"{status_emoji(run.status)} {status_label(run.status)}",
            "Products": run.product_count,
            "Time": run.started_at.strftime("%H:%M"),
        }
        for run in recent_jobs
    ]
    st.table(table_rows)
else:
    st.caption("No jobs recorded yet.")