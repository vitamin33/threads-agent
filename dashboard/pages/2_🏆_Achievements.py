"""
Achievements Page - Track and manage professional achievements
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
import re

st.set_page_config(
    page_title="Achievements - Threads Agent", page_icon="🏆", layout="wide"
)

st.title("🏆 Achievement Management")
st.markdown("Track, analyze, and showcase your professional accomplishments")

# Import API client
from services.api_client import get_api_client

api_client = get_api_client()


# Helper function to parse business value
def parse_business_value(value: Any) -> float:
    """Parse business value from various formats"""
    if not value:
        return 0

    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # Check if it's JSON
            if value.strip().startswith("{"):
                data = json.loads(value)
                return float(data.get("total_value", 0))
            else:
                # Try to extract number
                match = re.search(r"\$?([0-9,]+(?:\.[0-9]+)?)", value)
                if match:
                    return float(match.group(1).replace(",", ""))
    except:
        pass
    return 0


# Filters
col1, col2, col3, col4 = st.columns(4)

with col1:
    date_range = st.selectbox(
        "Time Period",
        ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        index=1,
    )

    # Convert to days
    days_map = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "All time": 365 * 10,  # 10 years
    }
    days = days_map[date_range]

with col2:
    min_value = st.number_input(
        "Min Business Value ($)", min_value=0, max_value=1000000, value=0, step=5000
    )

with col3:
    achievement_type = st.multiselect(
        "Type",
        [
            "AI/ML",
            "Performance",
            "Infrastructure",
            "Feature",
            "Bug Fix",
            "Documentation",
            "Testing",
        ],
        default=[],
    )

with col4:
    status_filter = st.multiselect(
        "Status", ["Published", "Draft", "Scheduled", "Archived"], default=[]
    )


# Fetch real achievements
@st.cache_data(ttl=60)
def get_filtered_achievements(days: int, min_value: float) -> List[Dict]:
    """Get achievements with filters applied"""
    try:
        # Get all achievements (API handles pagination)
        achievements = api_client.get_achievements(days=days, min_value=min_value)

        if not achievements:
            return []

        # Process achievements
        for a in achievements:
            # Parse business value
            a["parsed_value"] = parse_business_value(a.get("business_value"))

            # Determine type based on tags/title if category is missing/generic
            if not a.get("category") or a.get("category", "").lower() in [
                "feature",
                "development",
            ]:
                title_lower = a.get("title", "").lower()
                description_lower = a.get("description", "").lower()

                # Check title and description for type indicators
                combined_text = f"{title_lower} {description_lower}"

                if any(
                    term in combined_text
                    for term in [
                        "test",
                        "testing",
                        "unit test",
                        "integration test",
                        "coverage",
                    ]
                ):
                    a["category"] = "testing"
                elif any(
                    term in combined_text
                    for term in ["fix", "bug", "issue", "error", "debug"]
                ):
                    a["category"] = "bugfix"
                elif any(
                    term in combined_text
                    for term in [
                        "optimize",
                        "optimization",
                        "performance",
                        "speed",
                        "latency",
                        "efficiency",
                    ]
                ):
                    a["category"] = "optimization"
                elif any(
                    term in combined_text
                    for term in ["business", "strategy", "value", "roi", "revenue"]
                ):
                    a["category"] = "business"
                elif any(
                    term in combined_text
                    for term in ["ai", "ml", "machine learning", "predictor", "model"]
                ):
                    a["category"] = "ai/ml"
                elif any(
                    term in combined_text
                    for term in [
                        "kubernetes",
                        "docker",
                        "infra",
                        "deploy",
                        "k8s",
                        "helm",
                    ]
                ):
                    a["category"] = "infrastructure"
                elif any(
                    term in combined_text
                    for term in ["doc", "documentation", "readme", "guide", "manual"]
                ):
                    a["category"] = "documentation"
                else:
                    a["category"] = "feature"

            # Determine status
            if a.get("source_type") == "github_pr":
                a["status"] = "Published"
            elif a.get("portfolio_ready"):
                a["status"] = "Published"
            elif a.get("impact_score", 0) > 70:
                a["status"] = "Scheduled"
            else:
                a["status"] = "Draft"

        # Apply type filter
        if achievement_type:
            achievements = [
                a for a in achievements if a.get("category") in achievement_type
            ]

        # Apply status filter
        if status_filter:
            achievements = [a for a in achievements if a.get("status") in status_filter]

        return achievements
    except Exception as e:
        st.error(f"Failed to fetch achievements: {str(e)}")
        return []


achievements = get_filtered_achievements(days, min_value)

# Calculate summary statistics
total_achievements = len(achievements)
total_value = sum(a.get("parsed_value", 0) for a in achievements)
published_count = len([a for a in achievements if a.get("status") == "Published"])
avg_value = total_value / total_achievements if total_achievements > 0 else 0

# Calculate week-over-week changes
week_ago = datetime.now() - timedelta(days=7)
this_week = [
    a
    for a in achievements
    if "created_at" in a and pd.to_datetime(a["created_at"]) > week_ago
]
this_week_value = sum(a.get("parsed_value", 0) for a in this_week)
this_week_published = len([a for a in this_week if a.get("status") == "Published"])

# Summary Cards
st.markdown("### 📊 Achievement Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Achievements", f"{total_achievements}", f"+{len(this_week)} this week"
    )
with col2:
    st.metric(
        "Total Business Value",
        f"${total_value / 1000:.0f}K",
        f"+${this_week_value / 1000:.0f}K",
    )
with col3:
    st.metric("Published Articles", f"{published_count}", f"+{this_week_published}")
with col4:
    st.metric(
        "Avg Value/Achievement",
        f"${avg_value / 1000:.1f}K",
        f"+${(this_week_value / len(this_week) if this_week else 0) / 1000:.1f}K",
    )

st.divider()

# Achievement Table
st.markdown("### 📋 Achievement List")

if achievements:
    # Prepare data for display
    display_data = []
    for a in achievements:
        # Map category to proper display type
        category = a.get("category", "feature").lower()

        # Normalize category names for display
        type_mapping = {
            "feature": "Feature",
            "testing": "Testing",
            "bugfix": "Bug Fix",
            "bug fix": "Bug Fix",
            "optimization": "Performance",
            "performance": "Performance",
            "business": "Business",
            "infrastructure": "Infrastructure",
            "ai/ml": "AI/ML",
            "ai_ml": "AI/ML",
            "documentation": "Documentation",
            "doc": "Documentation",
        }

        display_type = type_mapping.get(category, category.title())

        display_data.append(
            {
                "ID": f"ACH-{a.get('id', 0):03d}",
                "Title": a.get("title", "Untitled")[:80],
                "Business Value": a.get("parsed_value", 0),
                "Type": display_type,
                "Status": a.get("status", "Draft"),
                "Date": pd.to_datetime(a.get("created_at", datetime.now())).strftime(
                    "%Y-%m-%d"
                ),
                "Impact": "Critical"
                if a.get("impact_score", 0) > 80
                else "High"
                if a.get("impact_score", 0) > 60
                else "Medium"
                if a.get("impact_score", 0) > 40
                else "Low",
            }
        )

    achievements_df = pd.DataFrame(display_data)

    # Interactive data editor
    edited_df = st.data_editor(
        achievements_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Business Value": st.column_config.NumberColumn(
                "Business Value",
                format="$%d",
                min_value=0,
                max_value=1000000,
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Published", "Draft", "Scheduled", "Archived"],
                required=True,
            ),
            "Type": st.column_config.SelectboxColumn(
                "Type",
                options=[
                    "AI/ML",
                    "Performance",
                    "Infrastructure",
                    "Feature",
                    "Bug Fix",
                    "Documentation",
                    "Testing",
                ],
                required=True,
            ),
            "Impact": st.column_config.SelectboxColumn(
                "Impact",
                options=["Low", "Medium", "High", "Critical"],
                required=True,
            ),
        },
    )

    # Bulk Actions
    st.markdown("### 🔧 Bulk Actions")

    col1, col2, col3, col4 = st.columns(4)

    selected_ids = st.multiselect(
        "Select achievements for bulk action",
        achievements_df["ID"].tolist() if "ID" in achievements_df.columns else [],
        key="bulk_select",
    )

    with col1:
        if st.button("📝 Generate Articles", disabled=not selected_ids):
            st.success(f"Generating articles for {len(selected_ids)} achievements...")
            # TODO: Call tech doc generator API

    with col2:
        if st.button("📊 Export to PDF", disabled=not selected_ids):
            st.info("Preparing PDF export...")
            # TODO: Call export API

    with col3:
        if st.button("🚀 Publish Selected", disabled=not selected_ids):
            st.warning(f"Publishing {len(selected_ids)} achievements...")
            # TODO: Update status via API

    with col4:
        if st.button("📁 Archive Selected", disabled=not selected_ids):
            st.info(f"Archiving {len(selected_ids)} achievements...")
            # TODO: Archive via API
else:
    st.info(
        "No achievements found matching the current filters. Try adjusting your filters or add new achievements below."
    )

st.divider()

# Analytics Section
st.markdown("### 📈 Achievement Analytics")

tab1, tab2, tab3 = st.tabs(["Value Distribution", "Type Breakdown", "Timeline"])

with tab1:
    if achievements:
        # Business value distribution
        values = [
            a.get("parsed_value", 0)
            for a in achievements
            if a.get("parsed_value", 0) > 0
        ]
        if values:
            fig = px.histogram(
                x=values,
                nbins=20,
                title="Business Value Distribution",
                labels={"x": "Business Value", "y": "Count"},
            )
            fig.update_traces(marker_color="#2E86AB")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No achievements with business value to display")
    else:
        st.info("No data available for analysis")

with tab2:
    if achievements:
        # Type breakdown pie chart
        type_counts = pd.Series(
            [a.get("category", "Unknown") for a in achievements]
        ).value_counts()

        fig = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title="Achievements by Type",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for analysis")

with tab3:
    if achievements:
        # Create timeline from real data
        timeline_df = pd.DataFrame(achievements)
        if "created_at" in timeline_df.columns:
            timeline_df["created_at"] = pd.to_datetime(timeline_df["created_at"])
            timeline_df = timeline_df.sort_values("created_at")

            # Calculate cumulative value
            timeline_df["cumulative_value"] = timeline_df["parsed_value"].cumsum()

            # Group by month
            monthly = (
                timeline_df.groupby(pd.Grouper(key="created_at", freq="ME"))
                .agg({"parsed_value": "sum", "cumulative_value": "last"})
                .reset_index()
            )

            fig = px.line(
                monthly,
                x="created_at",
                y="cumulative_value",
                title="Cumulative Business Value Over Time",
                markers=True,
                labels={"created_at": "Date", "cumulative_value": "Value"},
            )
            fig.update_traces(line_color="#F18F01")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data available")
    else:
        st.info("No data available for analysis")

st.divider()

# Add New Achievement
st.markdown("### ➕ Add New Achievement")

with st.form("new_achievement"):
    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input(
            "Title", placeholder="Brief description of the achievement"
        )
        business_value = st.number_input("Business Value ($)", min_value=0, value=50000)
        achievement_type = st.selectbox(
            "Type",
            [
                "AI/ML",
                "Performance",
                "Infrastructure",
                "Feature",
                "Bug Fix",
                "Documentation",
                "Testing",
            ],
        )
        started_at = st.date_input(
            "Start Date", value=datetime.now() - timedelta(days=7)
        )
        completed_at = st.date_input("Completion Date", value=datetime.now())

    with col2:
        description = st.text_area(
            "Description", placeholder="Detailed description and impact"
        )
        metrics = st.text_area(
            "Key Metrics", placeholder='JSON format: {"metric1": "value1"}'
        )
        tags = st.multiselect(
            "Tags",
            [
                "Python",
                "Kubernetes",
                "AI",
                "Performance",
                "API",
                "Database",
                "Docker",
                "ML",
                "DevOps",
            ],
        )
        impact_score = st.slider("Impact Score", 0, 100, 70)
        complexity_score = st.slider("Complexity Score", 0, 100, 60)

    submitted = st.form_submit_button("Add Achievement", type="primary")

    if submitted and title:
        # Prepare achievement data
        new_achievement = {
            "title": title,
            "description": description,
            "category": achievement_type.lower().replace("/", "_"),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "business_value": business_value,
            "impact_score": impact_score,
            "complexity_score": complexity_score,
            "tags": tags,
            "source_type": "manual",
            "portfolio_ready": impact_score > 70,
        }

        # Add metrics if provided
        if metrics:
            try:
                new_achievement["metrics_after"] = json.loads(metrics)
            except:
                st.error("Invalid JSON format for metrics")

        # Call API to create achievement
        result = api_client.create_achievement(new_achievement)

        if "error" not in result:
            st.success("✅ Achievement added successfully!")
            st.balloons()

            # Clear cache to refresh data
            get_filtered_achievements.clear()

            # Force refresh by rerunning
            st.rerun()
        else:
            st.error(
                f"Failed to create achievement: {result.get('error', 'Unknown error')}"
            )

# Integration Section
st.markdown("### 🔗 Integrations")

col1, col2 = st.columns(2)

with col1:
    with st.expander("🐙 GitHub Integration"):
        st.info("""
        **Auto-detect from PRs**
        - Connect your GitHub account
        - Automatically analyze merged PRs
        - Extract achievements from PR descriptions
        - Calculate business value from impact
        """)

        if st.button("🔍 Scan Recent PRs"):
            with st.spinner("Analyzing GitHub activity..."):
                # TODO: Call PR analysis API
                pr_achievements = api_client.analyze_pull_requests(days=30)
                if pr_achievements:
                    st.success(
                        f"Found {len(pr_achievements)} potential achievements from recent PRs!"
                    )
                else:
                    st.info("No new achievements found in recent PRs")

with col2:
    with st.expander("📋 Linear Integration"):
        st.info("""
        **Linear Task Sync**
        - Connect with Linear API
        - Track completed epics
        - Import task descriptions
        - Link achievements to tickets
        """)

        if st.button("🔄 Sync with Linear"):
            with st.spinner("Syncing with Linear..."):
                # TODO: Call Linear sync API
                st.success("Linear integration coming soon!")

# Add help section at the bottom
with st.expander("ℹ️ Need Help?"):
    st.markdown("""
    ### Achievement Tracking Guide
    
    **What counts as an achievement?**
    - Completed features or improvements
    - Performance optimizations
    - Bug fixes with significant impact
    - Published articles or documentation
    - Infrastructure improvements
    
    **How is business value calculated?**
    - Time saved × hourly rate
    - Performance improvements × user impact
    - Cost reductions from optimizations
    - Revenue potential from new features
    
    **Tips for better tracking:**
    - Be specific about metrics and impact
    - Include before/after comparisons
    - Tag relevant technologies
    - Update status as work progresses
    """)
