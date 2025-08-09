"""
Achievement Analytics Dashboard - Comprehensive achievement tracking and analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Achievement Analytics - Threads Agent", page_icon="🎯", layout="wide"
)

st.title("🎯 Achievement Analytics")
st.markdown("Deep insights into your achievements with full calculation transparency")

# Import API client and theme
from services.api_client import get_api_client
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme_config import apply_plotly_theme, inject_dark_theme_css

# Inject dark theme CSS
inject_dark_theme_css()

api_client = get_api_client()


# Fetch achievement data
@st.cache_data(ttl=60)
def get_achievement_stats():
    """Get achievement statistics from API"""
    try:
        # Get achievements list
        achievements = api_client.get_achievements(days=30)

        # Get stats summary using API client
        stats = api_client.get_achievement_stats()

        return achievements, stats
    except Exception as e:
        st.error(f"Failed to fetch achievement data: {str(e)}")
        return [], None


achievements, stats = get_achievement_stats()

# Summary Stats Section
st.markdown("### 📊 Achievement Summary")

if stats:
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Achievements", f"{stats.get('total_achievements', 0):,}", delta=None
        )

    with col2:
        total_value = stats.get("total_value_generated", 0)
        st.metric("Business Value Generated", f"${total_value:,.0f}", delta=None)

    with col3:
        time_saved = stats.get("total_time_saved_hours", 0)
        st.metric("Time Saved", f"{time_saved:,.1f} hrs", delta=None)

    with col4:
        avg_impact = stats.get("average_impact_score", 0)
        st.metric("Avg Impact Score", f"{avg_impact:.1f}/100", delta=None)

    with col5:
        avg_complexity = stats.get("average_complexity_score", 0)
        st.metric("Avg Complexity", f"{avg_complexity:.1f}/100", delta=None)

st.divider()

# Category Breakdown
if stats and stats.get("by_category"):
    st.markdown("### 📈 Achievements by Category")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Category data
        category_data = stats["by_category"]
        if category_data:
            df_category = pd.DataFrame(
                list(category_data.items()), columns=["Category", "Count"]
            )

            # Pie chart
            fig = px.pie(
                df_category,
                values="Count",
                names="Category",
                title="Distribution by Category",
            )
            fig = apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Calculate value by category
        if achievements:
            df_achievements = pd.DataFrame(achievements)
            if (
                "category" in df_achievements.columns
                and "business_value" in df_achievements.columns
            ):
                value_by_category = (
                    df_achievements.groupby("category")["business_value"]
                    .sum()
                    .reset_index()
                )
                value_by_category.columns = ["Category", "Total Value"]

                fig = px.bar(
                    value_by_category,
                    x="Category",
                    y="Total Value",
                    title="Business Value by Category",
                    text_auto=".2s",
                )
                fig = apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

st.divider()

# Calculation Transparency Section
st.markdown("### 🔍 Calculation Transparency")

# Achievement selector
if achievements:
    achievement_titles = [
        f"{a.get('title', 'Unknown')} (ID: {a.get('id', 'N/A')})" for a in achievements
    ]
    selected_achievement = st.selectbox(
        "Select an achievement to see calculation details:",
        options=range(len(achievements)),
        format_func=lambda x: achievement_titles[x],
    )

    if selected_achievement is not None:
        achievement = achievements[selected_achievement]
        achievement_id = achievement.get("id")

        # Fetch calculation transparency data
        if achievement_id:
            try:
                import httpx

                with httpx.Client(timeout=5.0) as client:
                    response = client.get(
                        f"http://localhost:8000/achievements/{achievement_id}/calculation-transparency"
                    )
                    if response.status_code == 200:
                        calc_data = response.json()

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("#### 📐 Calculation Details")
                            st.json(calc_data.get("enhanced_calculations", {}))

                        with col2:
                            st.markdown("#### 📊 Confidence Scores")
                            confidence = calc_data.get("confidence_scores", {})
                            if confidence:
                                for metric, score in confidence.items():
                                    st.progress(score, text=f"{metric}: {score:.0%}")

                        # Formulas used
                        if calc_data.get("formulas_used"):
                            st.markdown("#### 🧮 Formulas Applied")
                            for formula in calc_data["formulas_used"]:
                                st.code(formula, language="python")

                        # Methodology notes
                        if calc_data.get("methodology_notes"):
                            st.markdown("#### 📝 Methodology Notes")
                            for note in calc_data["methodology_notes"]:
                                st.info(note)
                    else:
                        st.warning(
                            "Calculation transparency data not available for this achievement"
                        )
            except Exception as e:
                st.error(f"Failed to fetch calculation data: {str(e)}")

st.divider()

# Time Series Analysis
st.markdown("### 📈 Achievement Trends")

if achievements:
    df = pd.DataFrame(achievements)

    # Ensure we have required columns
    if "completed_at" in df.columns:
        df["completed_at"] = pd.to_datetime(df["completed_at"])
        df["date"] = df["completed_at"].dt.date

        tab1, tab2, tab3 = st.tabs(
            ["Impact Over Time", "Value Generation", "Complexity Trends"]
        )

        with tab1:
            # Impact score over time
            if "impact_score" in df.columns:
                daily_impact = df.groupby("date")["impact_score"].mean().reset_index()

                fig = px.line(
                    daily_impact,
                    x="date",
                    y="impact_score",
                    title="Average Impact Score Trend",
                    markers=True,
                )
                fig.add_hline(
                    y=70,
                    line_dash="dash",
                    line_color="green",
                    annotation_text="High Impact Threshold",
                )
                fig = apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            # Cumulative value generation
            if "business_value" in df.columns:
                df_sorted = df.sort_values("completed_at")
                df_sorted["cumulative_value"] = df_sorted["business_value"].cumsum()

                fig = px.area(
                    df_sorted,
                    x="completed_at",
                    y="cumulative_value",
                    title="Cumulative Business Value Generated",
                    labels={"cumulative_value": "Total Value ($)"},
                )
                fig = apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            # Complexity vs time saved scatter
            if "complexity_score" in df.columns and "time_saved_hours" in df.columns:
                fig = px.scatter(
                    df,
                    x="complexity_score",
                    y="time_saved_hours",
                    color="impact_score",
                    size="business_value",
                    hover_data=["title"],
                    title="Complexity vs Time Saved Analysis",
                    labels={
                        "complexity_score": "Complexity Score",
                        "time_saved_hours": "Time Saved (hours)",
                        "impact_score": "Impact Score",
                    },
                )
                fig = apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

st.divider()

# PR Achievement Tracker
st.markdown("### 🔗 GitHub PR Achievements")

# Fetch PR achievements
try:
    pr_achievements = api_client.analyze_pull_requests()

    if pr_achievements:
        # Create PR timeline
        pr_df = pd.DataFrame(pr_achievements)

        col1, col2 = st.columns([2, 1])

        with col1:
            # PR Impact Timeline
            if "completed_at" in pr_df.columns and "impact_score" in pr_df.columns:
                pr_df["completed_at"] = pd.to_datetime(pr_df["completed_at"])

                fig = px.scatter(
                    pr_df,
                    x="completed_at",
                    y="impact_score",
                    size="business_value",
                    color="complexity_score",
                    hover_data=["title", "source_url"],
                    title="PR Impact Timeline",
                )
                fig = apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # PR Stats
            st.markdown("#### PR Statistics")
            total_prs = len(pr_df)
            high_impact_prs = (
                len(pr_df[pr_df["impact_score"] > 70])
                if "impact_score" in pr_df.columns
                else 0
            )
            avg_pr_value = (
                pr_df["business_value"].mean()
                if "business_value" in pr_df.columns
                else 0
            )

            st.metric("Total PR Achievements", total_prs)
            st.metric("High Impact PRs", high_impact_prs)
            st.metric("Avg PR Value", f"${avg_pr_value:,.0f}")

            # PR conversion rate
            if total_prs > 0:
                conversion_rate = (high_impact_prs / total_prs) * 100
                st.metric("High Impact Rate", f"{conversion_rate:.1f}%")
    else:
        st.info(
            "No PR achievements found. Start tracking your pull requests to see analytics here!"
        )

except Exception as e:
    st.warning(f"PR achievement tracking not available: {str(e)}")

st.divider()

# Quick Stats Footer
st.markdown("### 💡 Insights & Recommendations")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **🎯 Top Performing Categories**
    - Based on your data, focus on categories with highest ROI
    - Consider increasing efforts in high-value areas
    """)

with col2:
    st.success("""
    **📈 Growth Opportunities**
    - Track more detailed metrics for better insights
    - Set goals for impact scores > 80
    """)

with col3:
    st.warning("""
    **⚡ Quick Actions**
    - Log today's achievements
    - Review low-impact items for improvement
    """)

# Auto-refresh
st.markdown(
    """
    <script>
    setTimeout(function(){
        window.location.reload();
    }, 60000);
    </script>
    """,
    unsafe_allow_html=True,
)
