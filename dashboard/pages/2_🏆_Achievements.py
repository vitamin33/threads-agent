"""
Achievements Page - Track and manage professional achievements
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

st.set_page_config(
    page_title="Achievements - Threads Agent",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 Achievement Management")
st.markdown("Track, analyze, and showcase your professional accomplishments")

# Filters
col1, col2, col3, col4 = st.columns(4)

with col1:
    date_range = st.selectbox(
        "Time Period",
        ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        index=1
    )

with col2:
    min_value = st.number_input(
        "Min Business Value ($)",
        min_value=0,
        max_value=1000000,
        value=10000,
        step=5000
    )

with col3:
    achievement_type = st.multiselect(
        "Type",
        ["AI/ML", "Performance", "Infrastructure", "Feature", "Bug Fix"],
        default=["AI/ML", "Performance"]
    )

with col4:
    status_filter = st.multiselect(
        "Status",
        ["Published", "Draft", "Scheduled", "Archived"],
        default=["Published", "Draft"]
    )

# Summary Cards
st.markdown("### 📊 Achievement Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Achievements", "47", "+5 this week")
with col2:
    st.metric("Total Business Value", "$892K", "+$125K")
with col3:
    st.metric("Published Articles", "23", "+3")
with col4:
    st.metric("Avg Value/Achievement", "$18.9K", "+$2.1K")

st.divider()

# Achievement Table
st.markdown("### 📋 Achievement List")

# Sample data
achievements_data = {
    'ID': ['ACH-047', 'ACH-046', 'ACH-045', 'ACH-044', 'ACH-043'],
    'Title': [
        'Implemented Real-time Engagement Predictor with 94% Accuracy',
        'Reduced API Latency by 78% with Intelligent Caching',
        'Built Kubernetes Auto-scaling for 10x Traffic Spikes',
        'Created AI-Powered Content Generation Pipeline',
        'Optimized Database Queries - 5x Performance Boost'
    ],
    'Business Value': [75000, 120000, 95000, 85000, 65000],
    'Type': ['AI/ML', 'Performance', 'Infrastructure', 'AI/ML', 'Performance'],
    'Status': ['Published', 'Draft', 'Scheduled', 'Published', 'Draft'],
    'Date': pd.date_range(end=datetime.now(), periods=5).strftime('%Y-%m-%d'),
    'Impact': ['High', 'Critical', 'High', 'Medium', 'High']
}

achievements_df = pd.DataFrame(achievements_data)

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
            options=["AI/ML", "Performance", "Infrastructure", "Feature", "Bug Fix"],
            required=True,
        ),
        "Impact": st.column_config.SelectboxColumn(
            "Impact",
            options=["Low", "Medium", "High", "Critical"],
            required=True,
        )
    }
)

# Bulk Actions
st.markdown("### 🔧 Bulk Actions")

col1, col2, col3, col4 = st.columns(4)

selected_ids = st.multiselect(
    "Select achievements for bulk action",
    achievements_df['ID'].tolist(),
    key="bulk_select"
)

with col1:
    if st.button("📝 Generate Articles", disabled=not selected_ids):
        st.success(f"Generating articles for {len(selected_ids)} achievements...")

with col2:
    if st.button("📊 Export to PDF", disabled=not selected_ids):
        st.info("Preparing PDF export...")

with col3:
    if st.button("🚀 Publish Selected", disabled=not selected_ids):
        st.warning(f"Publishing {len(selected_ids)} achievements...")

with col4:
    if st.button("📁 Archive Selected", disabled=not selected_ids):
        st.info(f"Archiving {len(selected_ids)} achievements...")

st.divider()

# Analytics Section
st.markdown("### 📈 Achievement Analytics")

tab1, tab2, tab3 = st.tabs(["Value Distribution", "Type Breakdown", "Timeline"])

with tab1:
    # Business value distribution
    fig = px.histogram(
        achievements_df,
        x='Business Value',
        nbins=10,
        title="Business Value Distribution",
        labels={'count': 'Number of Achievements'}
    )
    fig.update_traces(marker_color='#2E86AB')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Type breakdown pie chart
    type_counts = achievements_df['Type'].value_counts()
    fig = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Achievements by Type"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Timeline chart
    timeline_data = pd.DataFrame({
        'Date': pd.date_range(start='2024-01-01', periods=12, freq='M'),
        'Count': [3, 5, 4, 7, 6, 8, 9, 11, 10, 12, 15, 14],
        'Value': [45000, 67000, 58000, 89000, 95000, 112000, 
                  125000, 145000, 158000, 178000, 195000, 210000]
    })
    
    fig = px.line(
        timeline_data,
        x='Date',
        y='Value',
        title="Cumulative Business Value Over Time",
        markers=True
    )
    fig.update_traces(line_color='#F18F01')
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Add New Achievement
st.markdown("### ➕ Add New Achievement")

with st.form("new_achievement"):
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("Title", placeholder="Brief description of the achievement")
        business_value = st.number_input("Business Value ($)", min_value=0, value=50000)
        achievement_type = st.selectbox("Type", ["AI/ML", "Performance", "Infrastructure", "Feature", "Bug Fix"])
    
    with col2:
        description = st.text_area("Description", placeholder="Detailed description and impact")
        metrics = st.text_area("Key Metrics", placeholder="JSON format: {\"metric1\": \"value1\"}")
        tags = st.multiselect("Tags", ["Python", "Kubernetes", "AI", "Performance", "API", "Database"])
    
    submitted = st.form_submit_button("Add Achievement", type="primary")
    
    if submitted:
        st.success("✅ Achievement added successfully!")
        st.balloons()

# GitHub Integration
st.markdown("### 🔗 GitHub Integration")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Auto-detect from PRs**
    - Connect your GitHub account
    - Automatically analyze merged PRs
    - Extract achievements from PR descriptions
    - Calculate business value from impact
    """)
    
    if st.button("🔍 Scan Recent PRs"):
        with st.spinner("Analyzing GitHub activity..."):
            # Simulate PR scanning
            st.success("Found 3 potential achievements from recent PRs!")

with col2:
    st.info("""
    **Linear Integration**
    - Sync with Linear tasks
    - Track completed epics
    - Import task descriptions
    - Link achievements to tickets
    """)
    
    if st.button("🔄 Sync with Linear"):
        with st.spinner("Syncing with Linear..."):
            st.success("Synced 5 completed tasks!")