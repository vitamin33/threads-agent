"""
Content Pipeline Page - Manage content creation and publishing
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

st.set_page_config(
    page_title="Content Pipeline - Threads Agent",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Content Pipeline Management")
st.markdown("Create, schedule, and publish content across multiple platforms")

# Pipeline Overview
st.markdown("### 🔄 Pipeline Status")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📋 Drafts", "8", "+2 today")
with col2:
    st.metric("⏰ Scheduled", "5", "Next in 2h")
with col3:
    st.metric("✅ Published", "23", "+3 this week")
with col4:
    st.metric("🔄 In Progress", "2", delta_color="off")
with col5:
    st.metric("📊 Engagement Avg", "7.8%", "+0.5%")

st.divider()

# Content Generation
st.markdown("### 🤖 AI Content Generation")

col1, col2 = st.columns([2, 1])

with col1:
    with st.form("content_generation"):
        st.subheader("Generate New Content")
        
        # Source selection
        source = st.selectbox(
            "Content Source",
            ["Recent Achievements", "Custom Topic", "Trending Topics", "PR Analysis"]
        )
        
        if source == "Recent Achievements":
            timeframe = st.slider("Days to look back", 1, 30, 7)
            min_value = st.number_input("Min business value", 0, 1000000, 50000)
        elif source == "Custom Topic":
            topic = st.text_input("Topic", placeholder="e.g., MLOps best practices")
            angle = st.selectbox("Angle", ["Technical Deep Dive", "Tutorial", "Opinion", "Case Study"])
        
        # Platform selection
        platforms = st.multiselect(
            "Target Platforms",
            ["Dev.to", "LinkedIn", "Threads", "Medium", "GitHub"],
            default=["Dev.to", "LinkedIn"]
        )
        
        # Options
        col_a, col_b = st.columns(2)
        with col_a:
            test_mode = st.checkbox("Test Mode (Draft Only)", value=True)
            optimize_engagement = st.checkbox("Optimize for Engagement", value=True)
        with col_b:
            include_code = st.checkbox("Include Code Examples", value=True)
            add_visuals = st.checkbox("Generate Visuals", value=False)
        
        generate_btn = st.form_submit_button("🚀 Generate Content", type="primary")
        
        if generate_btn:
            with st.spinner("🧠 AI is creating your content..."):
                # Simulate content generation
                progress = st.progress(0)
                for i in range(100):
                    progress.progress(i + 1)
                
                st.success("✅ Content generated successfully!")
                st.info("**Generated:** How I Reduced API Latency by 78% Using Smart Caching")

with col2:
    st.info("""
    **🎯 Pro Tips**
    
    - Best posting times:
      - Dev.to: Tue-Thu 9-11 AM EST
      - LinkedIn: Mon-Wed 8-10 AM
      - Threads: Daily 12-3 PM
    
    - Engagement boosters:
      - Use numbers in titles
      - Add code snippets
      - Include visuals
      - Ask questions
    
    - Content types that perform:
      - How-to tutorials
      - Performance improvements
      - Lessons learned
      - Tool comparisons
    """)

st.divider()

# Content Calendar
st.markdown("### 📅 Content Calendar")

# Calendar view
current_month = datetime.now().month
current_year = datetime.now().year
month_name = calendar.month_name[current_month]

st.subheader(f"{month_name} {current_year}")

# Create calendar data
cal = calendar.monthcalendar(current_year, current_month)
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# Sample scheduled content
scheduled_content = {
    5: ["Dev.to: API Performance"],
    12: ["LinkedIn: MLOps Guide", "Threads: Quick tip"],
    18: ["Dev.to: K8s Tutorial"],
    23: ["LinkedIn: Career Update"],
    28: ["Dev.to: Year Review"]
}

# Display calendar
cols = st.columns(7)
for i, day in enumerate(days):
    cols[i].markdown(f"**{day}**")

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.write("")
            else:
                if day == datetime.now().day:
                    st.markdown(f"**📍 {day}**")
                else:
                    st.write(day)
                
                if day in scheduled_content:
                    for content in scheduled_content[day]:
                        platform = content.split(":")[0]
                        if "Dev.to" in platform:
                            st.caption(f"🟦 {content}")
                        elif "LinkedIn" in platform:
                            st.caption(f"🔵 {content}")
                        else:
                            st.caption(f"⚫ {content}")

st.divider()

# Content Performance
st.markdown("### 📊 Content Performance")

tab1, tab2, tab3 = st.tabs(["By Platform", "By Type", "Trending"])

with tab1:
    # Platform performance comparison
    platform_data = pd.DataFrame({
        'Platform': ['Dev.to', 'LinkedIn', 'Threads', 'Medium'],
        'Posts': [12, 15, 8, 5],
        'Avg Views': [450, 320, 580, 290],
        'Avg Engagement': [7.2, 5.8, 9.1, 4.5],
        'Top Post Views': [1250, 890, 1450, 650]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Posts', x=platform_data['Platform'], y=platform_data['Posts']))
    fig.add_trace(go.Bar(name='Avg Engagement %', x=platform_data['Platform'], y=platform_data['Avg Engagement']))
    fig.update_layout(barmode='group', title="Platform Performance Comparison")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Content type performance
    type_data = pd.DataFrame({
        'Type': ['Tutorial', 'Case Study', 'Opinion', 'News', 'Guide'],
        'Engagement': [8.5, 6.2, 9.8, 4.1, 7.3]
    })
    
    fig = px.bar(type_data, x='Type', y='Engagement', 
                 title="Average Engagement by Content Type (%)",
                 color='Engagement', color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Trending content
    st.subheader("🔥 Top Performing Content")
    
    trending = pd.DataFrame({
        'Title': [
            '🥇 How I Built an AI System That Measures Developer Impact',
            '🥈 The Hidden Cost of Microservices Nobody Talks About',
            '🥉 5 MLOps Mistakes That Cost Me $50K'
        ],
        'Platform': ['Dev.to', 'LinkedIn', 'Dev.to'],
        'Views': [2450, 1890, 1560],
        'Engagement': ['9.2%', '7.8%', '8.5%'],
        'Published': ['3 days ago', '1 week ago', '2 weeks ago']
    })
    
    st.dataframe(trending, use_container_width=True, hide_index=True)

st.divider()

# Content Queue
st.markdown("### 📋 Content Queue")

queue_data = pd.DataFrame({
    'Status': ['Draft', 'Review', 'Scheduled', 'Draft', 'Scheduled'],
    'Title': [
        'Building Resilient Microservices with Circuit Breakers',
        'My Journey from Engineer to Tech Lead',
        'Real-time Data Pipelines with Apache Kafka',
        'Kubernetes Cost Optimization Strategies',
        'The Future of AI in Software Development'
    ],
    'Platform': ['Dev.to', 'LinkedIn', 'Dev.to', 'Medium', 'LinkedIn'],
    'Schedule': ['Not set', 'Tomorrow', 'Dec 5, 2pm', 'Not set', 'Dec 8, 10am'],
    'Quality Score': [8.5, 7.2, 9.1, 7.8, 8.3]
})

# Color code by status
def color_status(val):
    if val == 'Draft':
        return 'background-color: #FFE5B4'
    elif val == 'Review':
        return 'background-color: #B4E5FF'
    elif val == 'Scheduled':
        return 'background-color: #B4FFB4'
    return ''

styled_queue = queue_data.style.map(color_status, subset=['Status'])
st.dataframe(styled_queue, use_container_width=True, hide_index=True)

# Quick Actions
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝 Edit Selected", use_container_width=True):
        st.info("Opening content editor...")

with col2:
    if st.button("⏰ Schedule Selected", use_container_width=True):
        st.info("Opening scheduler...")

with col3:
    if st.button("🚀 Publish Now", use_container_width=True):
        st.warning("Publishing selected content...")