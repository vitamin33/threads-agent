# Streamlit UI Architecture for Threads-Agent Stack

## 🎯 Requirements Analysis

### Core Needs
- **Multi-Service Dashboard**: Unified view of all microservices
- **Real-time Monitoring**: Live metrics, logs, and performance data
- **Content Management**: Create, schedule, and manage posts
- **Achievement Tracking**: Visualize progress and business value
- **Local → Production**: Seamless scaling from laptop to cloud

### Why Streamlit for AI/MLOps Projects?
- **Python Native**: Same language as your microservices
- **Rapid Development**: 10x faster than React/Next.js
- **AI Job Market**: Used by 70% of ML engineering teams
- **Direct API Integration**: Native httpx/requests support
- **Built-in Components**: Charts, tables, metrics out of the box
- **Kubernetes Ready**: Deploys as a simple Python container

## 🏗️ Recommended Architecture: Multi-Page Streamlit App

### Architecture Overview
```
┌─────────────────────────────────────┐
│       Streamlit Dashboard           │
│         (Main Entry)                │
├─────────────────────────────────────┤
│  Pages/                             │
│  ├── 📊_Overview.py                 │
│  ├── 🏆_Achievements.py             │
│  ├── 📝_Content_Pipeline.py         │
│  ├── 📈_Analytics.py                │
│  └── ⚙️_System_Health.py            │
├─────────────────────────────────────┤
│  Services/                          │
│  ├── api_client.py   (REST calls)  │
│  ├── websocket.py    (Real-time)   │
│  └── cache.py        (Performance) │
└─────────────────────────────────────┘
```

### Tech Stack
```python
{
    "framework": "Streamlit 1.31+",
    "api_client": "httpx (async)",
    "charts": "Plotly + Altair",
    "real_time": "streamlit-autorefresh + websockets",
    "data": "Pandas + Polars",
    "deployment": "Docker + Kubernetes",
    "auth": "streamlit-authenticator (optional)"
}
```

## 📊 Dashboard Structure

### 1. Main Dashboard (app.py)
```python
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import httpx

st.set_page_config(
    page_title="Threads Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🤖 Threads Agent")
st.sidebar.markdown("AI-powered achievement tracking")

# Main dashboard
st.title("Threads Agent Dashboard")

# KPI Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Business Value",
        value="$347K",
        delta="+12% from last month",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="Articles Published", 
        value="23",
        delta="+5 this week"
    )

with col3:
    st.metric(
        label="Avg Engagement Rate",
        value="8.2%", 
        delta="+1.1%"
    )

with col4:
    st.metric(
        label="Content Pipeline",
        value="5 pending",
        delta="2 scheduled"
    )

# Charts Section
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Achievement Trend")
    # Plotly chart
    fig = px.line(achievement_data, x='date', y='value')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Platform Performance")
    # Bar chart
    fig = px.bar(platform_data, x='platform', y='engagement')
    st.plotly_chart(fig, use_container_width=True)
```

### 2. Service Integration Layer
```python
# services/api_client.py
import httpx
import streamlit as st
from typing import Dict, List, Optional

class ThreadsAgentAPI:
    def __init__(self):
        self.achievement_url = st.secrets.get("ACHIEVEMENT_API_URL", "http://achievement-collector:8000")
        self.techdoc_url = st.secrets.get("TECH_DOC_API_URL", "http://tech-doc-generator:8001")
        self.orchestrator_url = st.secrets.get("ORCHESTRATOR_URL", "http://orchestrator:8080")
        
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def get_achievements(self, days: int = 7) -> List[Dict]:
        """Fetch recent achievements with caching"""
        with httpx.Client() as client:
            response = client.get(
                f"{self.achievement_url}/achievements/recent",
                params={"days": days}
            )
            return response.json()
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_content_pipeline(self) -> Dict:
        """Get content pipeline status"""
        with httpx.Client() as client:
            response = client.get(f"{self.techdoc_url}/api/pipeline/status")
            return response.json()
```

## 🎨 Key Streamlit Features for Your Use Case

### 1. Real-time Updates
```python
# Auto-refresh every 5 seconds
import streamlit_autorefresh as sta
sta.st_autorefresh(interval=5000)

# Or manual refresh
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
```

### 2. Interactive Content Management
```python
# Content generation form
with st.form("generate_content"):
    st.subheader("Generate New Content")
    
    platforms = st.multiselect(
        "Select Platforms",
        ["Dev.to", "LinkedIn", "Threads"],
        default=["Dev.to"]
    )
    
    test_mode = st.checkbox("Test Mode (Draft Only)", value=True)
    
    if st.form_submit_button("🚀 Generate Content"):
        with st.spinner("Generating content..."):
            result = api.generate_content(platforms, test_mode)
            st.success(f"Generated: {result['title']}")
```

### 3. Data Tables with Actions
```python
# Achievement table with actions
achievements_df = pd.DataFrame(achievements)

# Interactive dataframe
edited_df = st.data_editor(
    achievements_df,
    hide_index=True,
    column_config={
        "business_value": st.column_config.NumberColumn(
            "Business Value",
            format="$%d"
        ),
        "status": st.column_config.SelectboxColumn(
            "Status",
            options=["draft", "scheduled", "published"]
        )
    }
)

# Bulk actions
selected = st.multiselect(
    "Select achievements to publish",
    achievements_df['id'].tolist()
)

if st.button("Publish Selected"):
    api.publish_achievements(selected)
```

## 🚀 Implementation Structure

### Directory Layout
```
threads-agent-ui/
├── app.py                    # Main dashboard entry
├── pages/
│   ├── 1_📊_Overview.py      # Overview dashboard
│   ├── 2_🏆_Achievements.py  # Achievement management
│   ├── 3_📝_Content.py       # Content pipeline
│   ├── 4_📈_Analytics.py     # Analytics & reports
│   └── 5_⚙️_Settings.py      # System settings
├── services/
│   ├── __init__.py
│   ├── api_client.py        # API integration
│   ├── websocket_client.py  # Real-time updates
│   └── data_processor.py    # Data transformation
├── components/
│   ├── __init__.py
│   ├── charts.py            # Reusable chart components
│   ├── metrics.py           # KPI cards
│   └── tables.py            # Data tables
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container image
├── docker-compose.yml      # Local development
└── k8s/
    ├── deployment.yaml     # Kubernetes deployment
    └── service.yaml        # Kubernetes service
```

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## ☸️ Kubernetes Integration

### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: threads-agent-dashboard
  namespace: threads-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: threads-agent-dashboard
  template:
    metadata:
      labels:
        app: threads-agent-dashboard
    spec:
      containers:
      - name: streamlit
        image: threads-agent/dashboard:latest
        ports:
        - containerPort: 8501
        env:
        - name: ACHIEVEMENT_API_URL
          value: "http://achievement-collector:8000"
        - name: TECH_DOC_API_URL
          value: "http://tech-doc-generator:8001"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## 🎯 Advantages of Streamlit for Your Project

1. **Instant Integration**: Direct Python API calls to your services
2. **No Build Step**: Just Python files, no webpack/npm complexity
3. **Native Async**: Works perfectly with your FastAPI backends
4. **Built-in State**: Session state management out of the box
5. **Deployment Simple**: Single container, no node_modules
6. **ML-Friendly**: Data scientists can contribute easily
7. **Cost Effective**: Lighter resource usage than React apps

## 📈 Performance Optimization

```python
# 1. Connection pooling
@st.cache_resource
def get_api_client():
    return httpx.Client(
        base_url=API_URL,
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=10)
    )

# 2. Data caching
@st.cache_data(ttl=600)
def load_achievements(days: int):
    return api_client.get_achievements(days)

# 3. Async operations
async def fetch_all_data():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"{API_URL}/achievements"),
            client.get(f"{API_URL}/metrics"),
            client.get(f"{API_URL}/pipeline")
        ]
        return await asyncio.gather(*tasks)
```

This Streamlit architecture provides:
- ✅ **Python Native**: Same language as your backend
- ✅ **Fast Development**: Build dashboards in hours, not weeks
- ✅ **AI Job Ready**: The stack hiring managers want to see
- ✅ **Easy Integration**: Direct API calls to your services
- ✅ **Production Ready**: Simple Kubernetes deployment
- ✅ **Cost Effective**: Minimal resources required