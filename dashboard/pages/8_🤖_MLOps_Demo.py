"""
MLOps Lifecycle Demo Dashboard
Real-time visualization of ML model lifecycle management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import time
import sys
import os
from pathlib import Path
import subprocess

# Add paths for imports
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

st.set_page_config(page_title="MLOps Demo Dashboard", page_icon="🤖", layout="wide")

# Custom CSS for demo styling
st.markdown(
    """
<style>
    .demo-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .demo-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 25px;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
<div class="demo-header">
    <h1>🤖 MLOps Lifecycle Demo Dashboard</h1>
    <p>Real-time visualization of production ML model lifecycle management</p>
    <p><strong>Portfolio Demonstration • Production-Ready Infrastructure</strong></p>
</div>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "demo_running" not in st.session_state:
    st.session_state.demo_running = False
if "demo_results" not in st.session_state:
    st.session_state.demo_results = None
if "demo_logs" not in st.session_state:
    st.session_state.demo_logs = []


def run_demo_sync():
    """Run the MLflow demo synchronously."""
    try:
        # Change to project root directory
        project_root = Path(__file__).parent.parent.parent
        os.chdir(project_root)

        # Run the demo with absolute paths
        venv_path = project_root / ".venv" / "bin" / "activate"
        demo_path = project_root / "services" / "achievement_collector"

        # Check if real logs mode is enabled
        real_logs_mode = st.sidebar.checkbox(
            "Real Logs Only Mode",
            value=False,
            help="Show only real operations, no simulations",
        )
        real_logs_env = "REAL_LOGS_ONLY=true" if real_logs_mode else ""

        cmd = [
            "bash",
            "-c",
            f"source {venv_path} && cd {demo_path} && MLFLOW_TRACKING_URI=http://localhost:5001 {real_logs_env} python -m mlops.demo_script --quick-demo",
        ]

        # Add progress message
        st.session_state.demo_logs.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "message": "🚀 Starting MLOps demo execution...",
            }
        )

        # Run process and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=60,  # 60 second timeout
        )

        # Add output to logs
        if result.stdout:
            for line in result.stdout.split("\n"):
                if line.strip():
                    st.session_state.demo_logs.append(
                        {
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "message": line.strip(),
                        }
                    )

        if result.stderr:
            for line in result.stderr.split("\n"):
                if line.strip():
                    # Filter out just timestamp and message, remove ERROR prefix for INFO logs
                    clean_message = line.strip()
                    if " - INFO - " in clean_message:
                        clean_message = clean_message.split(" - INFO - ", 1)[-1]
                    st.session_state.demo_logs.append(
                        {
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "message": clean_message,
                        }
                    )

        # Try to load results
        try:
            output_dir = (
                project_root / "services" / "achievement_collector" / "demo_output"
            )
            if output_dir.exists():
                json_files = list(output_dir.glob("demo_results_*.json"))
                if json_files:
                    latest_file = max(json_files, key=os.path.getctime)
                    with open(latest_file, "r") as f:
                        st.session_state.demo_results = json.load(f)
                        st.session_state.demo_logs.append(
                            {
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "message": "✅ Demo completed successfully! Results loaded.",
                            }
                        )
        except Exception as e:
            st.session_state.demo_logs.append(
                {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"⚠️ Error loading results: {e}",
                }
            )

        # Mark as completed
        st.session_state.demo_running = False

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        st.session_state.demo_logs.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "message": "⚠️ Demo timed out after 60 seconds",
            }
        )
        st.session_state.demo_running = False
        return False
    except Exception as e:
        st.session_state.demo_logs.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "message": f"❌ Demo execution error: {e}",
            }
        )
        st.session_state.demo_running = False
        return False


# Demo Controls
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("### 🎯 MLOps Demo Controls")
    st.markdown(
        "Execute the complete ML lifecycle demonstration with real infrastructure integration."
    )

with col2:
    if st.button("🚀 Run Demo", disabled=st.session_state.demo_running):
        st.session_state.demo_running = True
        st.session_state.demo_results = None
        st.session_state.demo_logs = []

        # Run demo synchronously with progress indicator
        with st.spinner("Running MLOps demo..."):
            success = run_demo_sync()

        if success:
            st.success("✅ Demo completed successfully!")
        else:
            st.error("❌ Demo execution failed. Check logs below.")

        st.rerun()

with col3:
    if st.button("🔄 Reset"):
        st.session_state.demo_running = False
        st.session_state.demo_results = None
        st.session_state.demo_logs = []
        st.rerun()

# Status indicator
if st.session_state.demo_results:
    st.markdown(
        '<p class="status-success">✅ Demo Completed Successfully!</p>',
        unsafe_allow_html=True,
    )
elif st.session_state.demo_logs:
    st.markdown(
        '<p class="status-success">✅ Demo execution finished. Check logs below.</p>',
        unsafe_allow_html=True,
    )
else:
    st.markdown("<p>⚪ Ready to run demo</p>")

# Results Dashboard
if st.session_state.demo_results:
    results = st.session_state.demo_results

    # Key Metrics
    st.markdown("### 📊 Demo Results Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Count models from MLOps features or stages
        models_trained = (
            3
            if "Multi-algorithm model training"
            in results.get("mlops_features_demonstrated", [])
            else 0
        )
        st.metric(
            "Models Trained",
            models_trained,
            help="Number of ML models trained in demo",
        )

    with col2:
        duration = results.get("demo_metadata", {}).get("duration_seconds", 0)
        st.metric(
            "Duration (seconds)", f"{duration:.1f}", help="Total demo execution time"
        )

    with col3:
        infrastructure = (
            "MLflow + PostgreSQL"
            if results.get("demo_metadata", {}).get("success", False)
            else "Unknown"
        )
        st.metric("Infrastructure", infrastructure, help="MLflow backend used")

    with col4:
        # Calculate SLO compliance rate from slo_compliance object
        slo_data = results.get("slo_compliance", {})
        slo_passed = sum(1 for v in slo_data.values() if v is True)
        slo_total = len(slo_data)
        compliance_rate = slo_passed / slo_total if slo_total > 0 else 0
        st.metric(
            "SLO Compliance",
            f"{compliance_rate:.1%}",
            help="Percentage of models meeting production SLOs",
        )

    # Model Performance Chart
    if "training_results" in results:
        st.markdown("### 📈 Model Performance Comparison")

        training_data = []
        for model in results["training_results"]:
            training_data.append(
                {
                    "Model": model["name"],
                    "Accuracy": model["metrics"]["accuracy"],
                    "P95 Latency (ms)": model["metrics"]["p95_inference_latency_ms"],
                    "SLO Compliant": "✅ Pass" if model["slo_compliant"] else "❌ Fail",
                }
            )

        df = pd.DataFrame(training_data)

        col1, col2 = st.columns(2)

        with col1:
            # Accuracy chart
            fig_acc = px.bar(
                df,
                x="Model",
                y="Accuracy",
                title="Model Accuracy Comparison",
                color="SLO Compliant",
                color_discrete_map={"✅ Pass": "#28a745", "❌ Fail": "#dc3545"},
            )
            fig_acc.add_hline(
                y=0.75,
                line_dash="dash",
                line_color="red",
                annotation_text="SLO Threshold (75%)",
            )
            st.plotly_chart(fig_acc, use_container_width=True)

        with col2:
            # Latency chart
            fig_lat = px.bar(
                df,
                x="Model",
                y="P95 Latency (ms)",
                title="P95 Latency Comparison",
                color="SLO Compliant",
                color_discrete_map={"✅ Pass": "#28a745", "❌ Fail": "#dc3545"},
            )
            fig_lat.add_hline(
                y=100,
                line_dash="dash",
                line_color="red",
                annotation_text="SLO Threshold (100ms)",
            )
            st.plotly_chart(fig_lat, use_container_width=True)

        # Performance table
        st.markdown("### 📋 Detailed Model Results")
        st.dataframe(df, use_container_width=True)

    # Lifecycle Management
    if "lifecycle_results" in results:
        st.markdown("### 🔄 Model Lifecycle Management")

        lifecycle = results["lifecycle_results"]["lifecycle_results"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎯 Best Model Selection")
            best = lifecycle["best_model"]
            st.markdown(f"""
            - **Model**: {best["name"]}
            - **Accuracy**: {best["accuracy"]:.3f}
            - **P95 Latency**: {best["latency_p95"]:.1f}ms
            - **SLO Status**: {best["slo_status"]}
            """)

        with col2:
            st.markdown("#### 🚀 Promotion Decision")
            promotion = lifecycle["promotion_decision"]
            st.markdown(f"""
            - **Can Promote**: {promotion["can_promote"]}
            - **Target Stage**: {promotion["promotion_stage"]}
            - **Reason**: {promotion["reason"]}
            """)

        # Rollback demonstration
        if "rollback_demo" in results["lifecycle_results"]:
            st.markdown("#### ⚡ Automated Rollback Demo")
            rollback = results["lifecycle_results"]["rollback_demo"]

            st.info(f"""
            **Scenario**: {rollback["trigger"]}
            
            **Response**: {rollback["action"]}
            
            **Recovery Time**: {rollback["rollback_time"]}
            
            **Status**: {rollback["status"]}
            """)

# Real-time Logs
if st.session_state.demo_logs:
    st.markdown("### 📝 Demo Execution Logs")

    # Show recent logs
    log_container = st.container()
    with log_container:
        # Show last 20 log entries
        recent_logs = st.session_state.demo_logs[-20:]
        for log in reversed(recent_logs):
            timestamp = log["timestamp"]
            message = log["message"]

            # Color code different types of messages
            if "ERROR" in message or "❌" in message:
                st.markdown(
                    f'<span style="color: #dc3545">[{timestamp}] {message}</span>',
                    unsafe_allow_html=True,
                )
            elif "INFO" in message or "✅" in message:
                st.markdown(
                    f'<span style="color: #28a745">[{timestamp}] {message}</span>',
                    unsafe_allow_html=True,
                )
            elif "WARNING" in message or "⚠️" in message:
                st.markdown(
                    f'<span style="color: #ffc107">[{timestamp}] {message}</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"[{timestamp}] {message}")

# Portfolio Information
st.markdown("---")
st.markdown("### 🎯 Portfolio Demo Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 🛠️ Technical Stack
    - **ML Frameworks**: scikit-learn, XGBoost
    - **Tracking**: MLflow experiment management
    - **Infrastructure**: Kubernetes + PostgreSQL + MinIO
    - **Monitoring**: Real-time performance metrics
    - **Automation**: SLO-based promotion and rollback
    """)

with col2:
    st.markdown("""
    #### 🎥 For Loom Recording
    1. Click "🚀 Run Demo" button
    2. Watch real-time logs and metrics
    3. Explain SLO validation process
    4. Show model performance charts
    5. Highlight automated lifecycle management
    """)

# Instructions
with st.expander("📖 Demo Instructions"):
    st.markdown("""
    ### How to Use This Dashboard for Your Portfolio Demo
    
    1. **Preparation**:
       - Ensure MLflow virtual environment is set up
       - Have your Loom recording software ready
       - Open this dashboard in full-screen mode
    
    2. **Recording Script**:
       - Start recording
       - Click "Run Demo" and explain what's happening
       - Point out the real-time metrics and SLO validation
       - Show the model performance charts
       - Highlight the automated lifecycle decisions
    
    3. **Key Talking Points**:
       - "This demonstrates my MLflow lifecycle management system"
       - "Notice the real-time SLO validation - models must meet accuracy and latency thresholds"
       - "The system shows automated promotion and rollback capabilities"
       - "All metrics are tracked with production-ready infrastructure"
    
    4. **Portfolio Value**:
       - Shows real MLOps engineering skills
       - Demonstrates production infrastructure knowledge
       - Highlights automated quality gates and monitoring
       - Perfect for MLOps Engineer interviews
    """)

# Auto-refresh for real-time updates
if st.session_state.demo_running:
    time.sleep(2)
    st.rerun()
