"""
Real-time updates client for dashboard using Server-Sent Events (SSE)
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import threading
import queue


class RealtimeClient:
    """Client for receiving real-time updates from services via SSE"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.event_queue = queue.Queue()
        self.listeners = {}
        self.is_running = False
        self.thread = None

    def connect_sse(self, endpoint: str, event_handler: Callable[[Dict], None]):
        """Connect to SSE endpoint and handle events"""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                stream=True,
                headers={"Accept": "text/event-stream"},
            )

            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            event_handler(data)
                        except json.JSONDecodeError:
                            pass

        except Exception as e:
            st.error(f"SSE connection error: {e}")

    def subscribe(self, event_type: str, callback: Callable[[Dict], None]):
        """Subscribe to specific event types"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all listeners"""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    st.error(f"Event handler error: {e}")

    def start_polling(self, endpoints: Dict[str, int]):
        """Start polling multiple endpoints for updates"""

        def poll():
            while self.is_running:
                for endpoint, interval in endpoints.items():
                    try:
                        response = requests.get(f"{self.base_url}{endpoint}")
                        if response.status_code == 200:
                            data = response.json()
                            self.event_queue.put(
                                {
                                    "endpoint": endpoint,
                                    "data": data,
                                    "timestamp": datetime.now(),
                                }
                            )
                    except:
                        pass
                    time.sleep(interval)

        self.is_running = True
        self.thread = threading.Thread(target=poll, daemon=True)
        self.thread.start()

    def stop_polling(self):
        """Stop polling threads"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)

    def get_updates(self) -> Optional[Dict]:
        """Get latest update from queue"""
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None


class DashboardUpdater:
    """Helper class for updating dashboard components in real-time"""

    def __init__(self):
        self.client = RealtimeClient()
        self.update_callbacks = {}

    def register_metric(self, key: str, container, update_fn: Callable):
        """Register a metric for real-time updates"""
        self.update_callbacks[key] = {"container": container, "update_fn": update_fn}

    def update_metric(self, key: str, value: Any, delta: Optional[str] = None):
        """Update a specific metric"""
        if key in self.update_callbacks:
            callback = self.update_callbacks[key]
            with callback["container"]:
                callback["update_fn"](value, delta)

    def create_activity_feed(self, container, max_items: int = 10):
        """Create a real-time activity feed"""
        activities = []

        def add_activity(activity: Dict):
            activities.insert(
                0,
                {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "message": activity.get("message", "Unknown activity"),
                    "type": activity.get("type", "info"),
                },
            )

            # Keep only latest items
            if len(activities) > max_items:
                activities.pop()

            # Update display
            with container:
                st.empty()  # Clear previous content
                for act in activities:
                    icon = {
                        "success": "✅",
                        "warning": "⚠️",
                        "error": "❌",
                        "info": "ℹ️",
                    }.get(act["type"], "📌")

                    st.markdown(f"{icon} **{act['time']}** - {act['message']}")

        return add_activity

    def create_progress_tracker(self, container):
        """Create a real-time progress tracker"""

        def update_progress(data: Dict):
            with container:
                st.empty()  # Clear previous

                progress = data.get("progress", 0)
                status = data.get("status", "Processing...")

                st.progress(progress / 100)
                st.caption(f"{status} ({progress}%)")

                if progress >= 100:
                    st.success("✅ Complete!")

        return update_progress

    def create_notification_handler(self):
        """Create notification handler for important events"""

        def handle_notification(data: Dict):
            notification_type = data.get("type", "info")
            message = data.get("message", "")

            if notification_type == "success":
                st.success(message)
            elif notification_type == "warning":
                st.warning(message)
            elif notification_type == "error":
                st.error(message)
            else:
                st.info(message)

            # Also show as toast if available
            if hasattr(st, "toast"):
                st.toast(message, icon=data.get("icon", "📢"))

        return handle_notification


def create_realtime_dashboard_section():
    """Create a section with real-time updates"""
    st.markdown("### 🔄 Real-Time Updates")

    # Initialize updater
    if "updater" not in st.session_state:
        st.session_state.updater = DashboardUpdater()

    updater = st.session_state.updater

    # Create layout
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("#### 📊 Live Metrics")
        metrics_container = st.container()

        # Register metrics for updates
        metric1 = st.empty()
        metric2 = st.empty()
        metric3 = st.empty()

        updater.register_metric(
            "active_tasks", metric1, lambda v, d: metric1.metric("Active Tasks", v, d)
        )
        updater.register_metric(
            "success_rate",
            metric2,
            lambda v, d: metric2.metric("Success Rate", f"{v}%", d),
        )
        updater.register_metric(
            "response_time",
            metric3,
            lambda v, d: metric3.metric("Avg Response", f"{v}ms", d),
        )

    with col2:
        st.markdown("#### 📈 Progress")
        progress_container = st.container()
        progress_updater = updater.create_progress_tracker(progress_container)

    with col3:
        st.markdown("#### 🔔 Status")
        status_container = st.container()
        with status_container:
            st.info("🟢 All systems operational")

    # Activity feed
    st.markdown("#### 📰 Activity Feed")
    feed_container = st.container()
    activity_updater = updater.create_activity_feed(feed_container)

    # Notification handler
    notification_handler = updater.create_notification_handler()

    # Subscribe to events
    updater.client.subscribe(
        "metric_update",
        lambda d: updater.update_metric(d["metric"], d["value"], d.get("delta")),
    )
    updater.client.subscribe("activity", activity_updater)
    updater.client.subscribe("progress", progress_updater)
    updater.client.subscribe("notification", notification_handler)

    # Start polling for updates
    if not updater.client.is_running:
        updater.client.start_polling(
            {
                "/metrics": 5,  # Poll metrics every 5 seconds
                "/health": 10,  # Poll health every 10 seconds
            }
        )

    # Simulate some events for demo
    if st.button("🎯 Simulate Events"):
        activity_updater(
            {
                "message": 'New achievement created: "Optimized API Performance"',
                "type": "success",
            }
        )

        progress_updater({"progress": 75, "status": "Processing content generation..."})

        notification_handler(
            {
                "type": "success",
                "message": "🎉 New milestone reached: 100 achievements!",
                "icon": "🏆",
            }
        )

        updater.update_metric("active_tasks", 5, "+2")
        updater.update_metric("success_rate", 95.5, "+1.2%")
        updater.update_metric("response_time", 42, "-3ms")

    return updater


# Example usage in a Streamlit page
if __name__ == "__main__":
    st.title("Real-Time Dashboard Demo")
    create_realtime_dashboard_section()
