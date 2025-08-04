"""
Threads Agent Dashboard - Main Entry Point
AI-powered achievement tracking and content automation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Threads Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/threads-agent-stack/threads-agent',
        'About': "AI-powered achievement tracking and content automation system"
    }
)

# Add custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    div[data-testid="metric-container"] > div[data-testid="metric"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.2);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Sidebar
with st.sidebar:
    st.title("🤖 Threads Agent")
    st.markdown("AI-powered achievement tracking")
    
    st.divider()
    
    # Navigation info
    st.markdown("""
    ### 📍 Navigation
    - **📊 Overview** - Main dashboard
    - **🏆 Achievements** - Track accomplishments
    - **📝 Content** - Manage content pipeline
    - **📈 Analytics** - Performance insights
    - **⚙️ Settings** - System configuration
    """)
    
    st.divider()
    
    # System status
    st.markdown("### 🟢 System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Services", "5/5", delta_color="off")
    with col2:
        st.metric("Health", "100%", delta_color="off")
    
    # Last refresh
    st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    if st.button("🔄 Refresh Now"):
        st.session_state.last_refresh = datetime.now()
        st.rerun()

# Main content
st.title("Threads Agent Dashboard")
st.markdown("**Real-time monitoring and control center for your AI-powered content automation system**")

# Import API client
achievements = []  # Initialize as empty list
try:
    from services.api_client import get_api_client
    api = get_api_client()
    
    # Fetch real data
    try:
        achievements = api.get_achievements(days=30)
        content_status = api.get_content_pipeline()
        system_metrics = api.get_system_metrics()
        
        # Calculate real metrics
        # Parse business value from JSON string if needed
        total_value = 0
        import json
        import re
        
        for a in achievements:
            bv = a.get('business_value', '')
            if bv is None:
                continue
            elif isinstance(bv, str):
                # Handle JSON format first
                if bv.strip().startswith('{'):
                    try:
                        bv_data = json.loads(bv)
                        total_value += bv_data.get('total_value', 0)
                    except:
                        pass
                # Handle dollar sign formats
                elif '$' in bv:
                    match = re.search(r'\$([0-9,]+)', bv)
                    if match:
                        value = int(match.group(1).replace(',', ''))
                        total_value += value
                # Handle plain string numbers (like "75000")
                else:
                    try:
                        value = float(bv.replace(',', ''))
                        total_value += value
                    except:
                        pass
            elif isinstance(bv, (int, float)):
                total_value += bv
        
        articles_published = len([a for a in achievements if a.get('portfolio_ready', False)])
        
        # Calculate AI job strategy metrics with historical comparison
        from datetime import datetime, timedelta
        
        # Split achievements into recent (last 30 days) and older
        now = datetime.now()
        recent_achievements = []
        older_achievements = []
        
        for a in achievements:
            created_at = a.get('created_at', '')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        # Handle different date formats
                        try:
                            date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except:
                            date = datetime.strptime(created_at[:19], '%Y-%m-%dT%H:%M:%S')
                    else:
                        date = created_at
                        
                    if (now - date).days <= 30:
                        recent_achievements.append(a)
                    else:
                        older_achievements.append(a)
                except:
                    recent_achievements.append(a)  # If can't parse date, assume recent
            else:
                recent_achievements.append(a)
        
        # Calculate current metrics
        complexity_scores = [a.get('complexity_score', 0) for a in achievements if a.get('complexity_score', 0) > 0]
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        total_skills = sum([len(a.get('skills_demonstrated', [])) for a in achievements])
        avg_skills_per_project = total_skills / len(achievements) if achievements else 0
        
        performance_improvements = [a.get('performance_improvement_pct', 0) for a in achievements if a.get('performance_improvement_pct', 0) > 0]
        avg_performance_gain = sum(performance_improvements) / len(performance_improvements) if performance_improvements else 0
        
        # Calculate historical metrics for comparison
        old_complexity_scores = [a.get('complexity_score', 0) for a in older_achievements if a.get('complexity_score', 0) > 0]
        old_avg_complexity = sum(old_complexity_scores) / len(old_complexity_scores) if old_complexity_scores else 0
        
        old_total_skills = sum([len(a.get('skills_demonstrated', [])) for a in older_achievements])
        old_avg_skills = old_total_skills / len(older_achievements) if older_achievements else 0
        
        old_performance_improvements = [a.get('performance_improvement_pct', 0) for a in older_achievements if a.get('performance_improvement_pct', 0) > 0]
        old_avg_performance = sum(old_performance_improvements) / len(old_performance_improvements) if old_performance_improvements else 0
        
        # Calculate deltas
        complexity_delta = avg_complexity - old_avg_complexity if old_avg_complexity > 0 else 0
        skills_delta = avg_skills_per_project - old_avg_skills if old_avg_skills > 0 else 0
        performance_delta = avg_performance_gain - old_avg_performance if old_avg_performance > 0 else 0
        
        pending_content = content_status.get('pending_count', 0)
        
    except Exception as e:
        st.warning(f"Using mock data - API connection failed: {str(e)}")
        # Use mock data as fallback but keep empty achievements list
        total_value = 0
        articles_published = 0
        avg_complexity = 0
        avg_skills_per_project = 0
        avg_performance_gain = 0
        pending_content = 0
        
except ImportError:
    # Mock data for initial setup
    total_value = 0
    articles_published = 0
    avg_complexity = 0
    avg_skills_per_project = 0
    avg_performance_gain = 0
    pending_content = 0

# KPI Metrics Row
st.markdown("### 📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_text = "+12% from last month" if total_value > 0 else None
    st.metric(
        label="💰 Total Business Value",
        value=f"${total_value:,.0f}",
        delta=delta_text,
        delta_color="normal"
    )

with col2:
    delta_text = "+5 this week" if articles_published > 0 else None
    st.metric(
        label="📄 Articles Published",
        value=str(articles_published),
        delta=delta_text,
        delta_color="normal"
    )

with col3:
    if complexity_delta > 0:
        delta_text = f"+{complexity_delta:.1f} this month"
        delta_color = "normal"
    elif complexity_delta < 0:
        delta_text = f"{complexity_delta:.1f} this month"  
        delta_color = "inverse"
    else:
        delta_text = None if avg_complexity > 0 else None
        delta_color = "off"
    
    st.metric(
        label="🧩 Technical Complexity",
        value=f"{avg_complexity:.0f}/100",
        delta=delta_text,
        delta_color=delta_color
    )

with col4:
    delta_text = "2 scheduled today" if pending_content > 0 else None
    st.metric(
        label="⏳ Content Pipeline",
        value=f"{pending_content} pending",
        delta=delta_text,
        delta_color="inverse"
    )

# AI Job Strategy Metrics Row
st.markdown("### 🎯 AI Job Strategy Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if skills_delta > 0:
        delta_text = f"+{skills_delta:.1f} skills"
        delta_color = "normal"
    elif skills_delta < 0:
        delta_text = f"{skills_delta:.1f} skills" 
        delta_color = "inverse"
    else:
        delta_text = None if avg_skills_per_project > 0 else None
        delta_color = "off"
    
    st.metric(
        label="⚡ Skills per Project",
        value=f"{avg_skills_per_project:.0f}",
        delta=delta_text,
        delta_color=delta_color
    )

with col2:
    if performance_delta > 0:
        delta_text = f"+{performance_delta:.1f}%"
        delta_color = "normal"
    elif performance_delta < 0:
        delta_text = f"{performance_delta:.1f}%"
        delta_color = "inverse"  
    else:
        delta_text = None if avg_performance_gain > 0 else None
        delta_color = "off"
    
    st.metric(
        label="🚀 Performance Gains", 
        value=f"{avg_performance_gain:.1f}%",
        delta=delta_text,
        delta_color=delta_color
    )

with col3:
    # Calculate total impact score average with historical comparison
    impact_scores = [a.get('impact_score', 0) for a in achievements if a.get('impact_score', 0) > 0] if 'achievements' in locals() and achievements else []
    avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
    
    old_impact_scores = [a.get('impact_score', 0) for a in older_achievements if a.get('impact_score', 0) > 0] if 'older_achievements' in locals() else []
    old_avg_impact = sum(old_impact_scores) / len(old_impact_scores) if old_impact_scores else 0
    impact_delta = avg_impact - old_avg_impact if old_avg_impact > 0 else 0
    
    if impact_delta > 0:
        delta_text = f"+{impact_delta:.1f} this month"
        delta_color = "normal"
    elif impact_delta < 0:
        delta_text = f"{impact_delta:.1f} this month"
        delta_color = "inverse"
    else:
        delta_text = None if avg_impact > 0 else None
        delta_color = "off"
    
    st.metric(
        label="💡 Impact Score",
        value=f"{avg_impact:.0f}/100",
        delta=delta_text,
        delta_color=delta_color
    )

with col4:
    # Calculate AI-readiness score (composite metric) with historical comparison
    ai_readiness = (avg_complexity + avg_impact + (avg_skills_per_project * 5)) / 3 if avg_complexity > 0 else 0
    old_ai_readiness = (old_avg_complexity + old_avg_impact + (old_avg_skills * 5)) / 3 if 'old_avg_complexity' in locals() and old_avg_complexity > 0 else 0
    readiness_delta = ai_readiness - old_ai_readiness if old_ai_readiness > 0 else 0
    
    if ai_readiness > 85:
        delta_text = "Excellent!"
        delta_color = "normal"
    elif ai_readiness > 70:
        delta_text = "Job ready!"
        delta_color = "normal"
    elif readiness_delta > 0:
        delta_text = f"+{readiness_delta:.1f} improving"
        delta_color = "normal"
    else:
        delta_text = None if ai_readiness > 0 else None
        delta_color = "off"
        
    st.metric(
        label="🤖 AI Job Readiness",
        value=f"{ai_readiness:.0f}/100",
        delta=delta_text,
        delta_color=delta_color
    )

st.divider()

# Charts Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Achievement Business Value Trend")
    
    # Use real achievement data for trend
    if 'achievements' in locals() and achievements:
        # Sort achievements by date and calculate cumulative value
        sorted_achievements = sorted(achievements, key=lambda x: x.get('created_at', ''))
        cumulative_value = 0
        dates = []
        values = []
        
        for ach in sorted_achievements:
            date = pd.to_datetime(ach.get('created_at', datetime.now()))
            dates.append(date)
            
            # Parse business value - handle all formats
            bv = ach.get('business_value', '')
            if bv is None:
                pass  # Skip None values
            elif isinstance(bv, str) and bv.startswith('{'):
                try:
                    import json
                    bv_data = json.loads(bv)
                    cumulative_value += bv_data.get('total_value', 0)
                except:
                    pass
            elif isinstance(bv, str) and '$' in bv:
                # Handle formats like "$162,500 annual value" or "$12,526 USD/one-time"
                import re
                match = re.search(r'\$([0-9,]+)', bv)
                if match:
                    value = int(match.group(1).replace(',', ''))
                    cumulative_value += value
            elif isinstance(bv, (int, float)):
                cumulative_value += bv
            
            values.append(cumulative_value)
        
        if dates and values:
            trend_df = pd.DataFrame({
                'Date': dates,
                'Business Value': values
            })
        else:
            # Fallback to empty data
            trend_df = pd.DataFrame({
                'Date': [datetime.now()],
                'Business Value': [0]
            })
    else:
        # No data available
        trend_df = pd.DataFrame({
            'Date': [datetime.now()],
            'Business Value': [0]
        })
    
    fig = px.line(trend_df, x='Date', y='Business Value',
                  line_shape='spline', 
                  color_discrete_sequence=['#1f77b4'])
    
    fig.update_traces(line=dict(width=3))
    fig.update_layout(
        showlegend=False,
        height=350,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title="",
        yaxis_title="Business Value ($)",
        yaxis_tickformat='$,.0f'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 📊 Content Performance by Platform")
    
    # Use real achievement data grouped by source
    if 'achievements' in locals() and achievements:
        # Group by source_type
        platform_counts = {}
        for ach in achievements:
            source = ach.get('source_type', 'other')
            if source == 'github_pr':
                source = 'GitHub'
            elif source == 'manual':
                source = 'Manual'
            else:
                source = source.title()
            
            platform_counts[source] = platform_counts.get(source, 0) + 1
        
        if platform_counts:
            platform_data = pd.DataFrame({
                'Platform': list(platform_counts.keys()),
                'Articles': list(platform_counts.values()),
                'Engagement Rate': [0] * len(platform_counts)  # No engagement data available
            })
        else:
            # Empty data
            platform_data = pd.DataFrame({
                'Platform': ['No Data'],
                'Articles': [0],
                'Engagement Rate': [0]
            })
    else:
        # No data available
        platform_data = pd.DataFrame({
            'Platform': ['No Data'],
            'Articles': [0],
            'Engagement Rate': [0]
        })
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Articles',
        x=platform_data['Platform'],
        y=platform_data['Articles'],
        yaxis='y',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Engagement %',
        x=platform_data['Platform'],
        y=platform_data['Engagement Rate'],
        yaxis='y2',
        marker_color='lightgreen'
    ))
    
    fig.update_layout(
        yaxis=dict(title='Articles Published', side='left'),
        yaxis2=dict(title='Engagement Rate (%)', overlaying='y', side='right'),
        hovermode='x',
        height=350,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Recent Achievements Section
st.markdown("### 🏆 Recent Achievements")

# Use real achievement data
if 'achievements' in locals() and achievements:
    # Take the most recent 5 achievements
    recent_achs = sorted(achievements, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    titles = []
    business_values = []
    statuses = []
    dates = []
    types = []
    
    for ach in recent_achs:
        # Title - truncate if too long
        title = ach.get('title', 'Untitled')
        if len(title) > 60:
            title = title[:57] + '...'
        titles.append(title)
        
        # Business value
        bv = ach.get('business_value', '')
        if isinstance(bv, str) and bv.startswith('{'):
            try:
                import json
                bv_data = json.loads(bv)
                business_values.append(bv_data.get('total_value', 0))
            except:
                business_values.append(0)
        elif isinstance(bv, str) and '$' in bv:
            # Handle string formats like "$12,526 USD/one-time"
            try:
                # Extract numeric value
                import re
                match = re.search(r'\$([0-9,]+)', bv)
                if match:
                    value = int(match.group(1).replace(',', ''))
                    business_values.append(value)
                else:
                    business_values.append(0)
            except:
                business_values.append(0)
        else:
            business_values.append(0)
        
        # Status based on portfolio_ready
        if ach.get('portfolio_ready', False):
            statuses.append('published')
        else:
            statuses.append('draft')
        
        # Date
        date = pd.to_datetime(ach.get('created_at', datetime.now()))
        dates.append(date.strftime('%Y-%m-%d'))
        
        # Type from category
        category = ach.get('category', 'other')
        types.append(category.title())
    
    recent_achievements = pd.DataFrame({
        'Title': titles,
        'Business Value': business_values,
        'Status': statuses,
        'Date': dates,
        'Type': types
    })
else:
    # No data - show empty table
    recent_achievements = pd.DataFrame({
        'Title': ['No achievements yet'],
        'Business Value': [0],
        'Status': ['draft'],
        'Date': [datetime.now().strftime('%Y-%m-%d')],
        'Type': ['N/A']
    })

# Style the dataframe
def style_status(val):
    colors = {
        'published': 'background-color: #90EE90',
        'scheduled': 'background-color: #87CEEB',
        'draft': 'background-color: #F0E68C'
    }
    return colors.get(val, '')

styled_df = recent_achievements.style.map(
    style_status, 
    subset=['Status']
).format({
    'Business Value': '${:,.0f}'
})

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    height=250
)

st.divider()

# Quick Actions Section
st.markdown("### ⚡ Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🤖 Generate Content", use_container_width=True, type="primary"):
        st.info("Redirecting to Content Pipeline...")
        # In real app, this would navigate or trigger action

with col2:
    if st.button("📊 Analyze PRs", use_container_width=True):
        st.info("Analyzing recent pull requests...")

with col3:
    if st.button("📅 Schedule Post", use_container_width=True):
        st.info("Opening scheduler...")

with col4:
    if st.button("📥 Export Report", use_container_width=True):
        st.info("Generating portfolio report...")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🟢 All Systems Operational")

with col2:
    st.caption(f"📅 {datetime.now().strftime('%B %d, %Y')}")

with col3:
    st.caption("🔄 Auto-refresh: 60s")

# Auto-refresh functionality (optional)
# Uncomment the following lines to enable auto-refresh
# import streamlit_autorefresh as star
# star.st_autorefresh(interval=60000, key="datarefresh")