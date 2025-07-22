"""
Real-time development dashboard with AI insights
Shows live metrics, trends, and AI-powered recommendations
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()


class MetricsCollector:
    """Collect and analyze metrics in real-time"""

    def __init__(self):
        self.metrics_history = []
        self.alerts = []

    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current metrics from all services"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "business": {},
            "trends": {},
        }

        # Collect from Prometheus
        try:
            async with aiohttp.ClientSession() as session:
                # Service health
                for service in ["orchestrator", "celery-worker", "persona-runtime"]:
                    async with session.get(f"http://{service}:9090/metrics") as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            metrics["services"][service] = self.parse_metrics(text)

                # Business metrics
                async with session.get("http://orchestrator:9090/metrics") as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        metrics["business"] = {
                            "engagement_rate": self.extract_metric(
                                text, "posts_engagement_rate"
                            ),
                            "posts_per_hour": self.extract_metric(
                                text, "posts_generated_total"
                            ),
                            "cost_per_follow": self.extract_metric(
                                text, "cost_per_follow_dollars"
                            ),
                            "revenue_projection": self.extract_metric(
                                text, "revenue_projection_monthly"
                            ),
                        }
        except Exception as e:
            print(f"Error collecting metrics: {e}")

        # Get trending topics from Redis
        try:
            # Use Redis MCP to get trends
            metrics["trends"] = await self.get_trending_topics()
        except Exception:
            metrics["trends"] = {}

        self.metrics_history.append(metrics)
        return metrics

    def parse_metrics(self, prometheus_text: str) -> Dict[str, float]:
        """Parse Prometheus metrics text"""
        metrics = {}
        for line in prometheus_text.split("\n"):
            if line and not line.startswith("#"):
                parts = line.split(" ")
                if len(parts) == 2:
                    metric_name = parts[0].split("{")[0]
                    try:
                        metrics[metric_name] = float(parts[1])
                    except Exception:
                        pass
        return metrics

    def extract_metric(self, text: str, metric_name: str) -> float:
        """Extract specific metric value"""
        for line in text.split("\n"):
            if metric_name in line and not line.startswith("#"):
                parts = line.split(" ")
                if len(parts) == 2:
                    try:
                        return float(parts[1])
                    except Exception:
                        pass
        return 0.0

    async def get_trending_topics(self) -> List[Dict[str, Any]]:
        """Get trending topics from Redis"""
        # Mock data for demo
        return [
            {"topic": "AI productivity", "score": 95},
            {"topic": "Mental health tech", "score": 87},
            {"topic": "Future of work", "score": 82},
        ]

    def analyze_performance(self) -> Dict[str, Any]:
        """AI-powered performance analysis"""
        if len(self.metrics_history) < 2:
            return {"status": "insufficient_data"}

        latest = self.metrics_history[-1]
        previous = self.metrics_history[-2]

        analysis = {
            "engagement_trend": (
                "improving"
                if latest["business"]["engagement_rate"]
                > previous["business"]["engagement_rate"]
                else "declining"
            ),
            "cost_efficiency": (
                "optimal"
                if latest["business"]["cost_per_follow"] < 0.01
                else "needs_optimization"
            ),
            "recommendations": [],
        }

        # Generate recommendations
        if latest["business"]["engagement_rate"] < 0.06:
            analysis["recommendations"].append(
                {
                    "priority": "high",
                    "action": "Increase trend alignment",
                    "reason": f"Engagement rate {latest['business']['engagement_rate']:.2%} below 6% target",
                }
            )

        if latest["business"]["cost_per_follow"] > 0.01:
            analysis["recommendations"].append(
                {
                    "priority": "medium",
                    "action": "Optimize targeting",
                    "reason": f"Cost per follow ${latest['business']['cost_per_follow']:.3f} above $0.01 target",
                }
            )

        return analysis


@app.get("/")
async def dashboard():
    """Serve the real-time dashboard"""
    return HTMLResponse(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Threads-Agent Real-Time Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px;
                background: #1a1a1a;
                color: #fff;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }
            .metric-card {
                background: #2a2a2a;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #4CAF50;
            }
            .metric-label {
                color: #888;
                font-size: 0.9em;
                margin-top: 5px;
            }
            .chart {
                background: #2a2a2a;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .trends {
                background: #2a2a2a;
                border-radius: 8px;
                padding: 20px;
            }
            .trend-item {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #444;
            }
            .recommendations {
                background: #2a2a2a;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
            }
            .rec-item {
                padding: 10px;
                margin: 10px 0;
                border-left: 3px solid #ff9800;
                background: #333;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 5px;
            }
            .status-ok { background: #4CAF50; }
            .status-warning { background: #ff9800; }
            .status-error { background: #f44336; }
        </style>
    </head>
    <body>
        <h1>🚀 Threads-Agent Real-Time Dashboard</h1>
        
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value" id="engagement-rate">--%</div>
                <div class="metric-label">Engagement Rate (Target: 6%+)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="cost-per-follow">$-.--</div>
                <div class="metric-label">Cost per Follow (Target: $0.01)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="revenue-projection">$-</div>
                <div class="metric-label">Monthly Revenue Projection</div>
            </div>
        </div>
        
        <div class="chart">
            <h3>Performance Trends</h3>
            <div id="performance-chart"></div>
        </div>
        
        <div class="grid">
            <div class="trends">
                <h3>🔥 Trending Topics</h3>
                <div id="trending-topics"></div>
            </div>
            <div class="metric-card">
                <h3>Service Health</h3>
                <div id="service-health"></div>
            </div>
            <div class="metric-card">
                <h3>Active Personas</h3>
                <div id="active-personas"></div>
            </div>
        </div>
        
        <div class="recommendations">
            <h3>🤖 AI Recommendations</h3>
            <div id="recommendations"></div>
        </div>
        
        <script>
            const ws = new WebSocket('ws://localhost:8002/ws');
            
            let metricsHistory = {
                timestamps: [],
                engagement: [],
                cost: [],
                posts: []
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function updateDashboard(data) {
                // Update metric cards
                document.getElementById('engagement-rate').textContent = 
                    (data.business.engagement_rate * 100).toFixed(2) + '%';
                document.getElementById('cost-per-follow').textContent = 
                    '$' + data.business.cost_per_follow.toFixed(3);
                document.getElementById('revenue-projection').textContent = 
                    '$' + Math.round(data.business.revenue_projection).toLocaleString();
                
                // Update history
                metricsHistory.timestamps.push(new Date(data.timestamp));
                metricsHistory.engagement.push(data.business.engagement_rate * 100);
                metricsHistory.cost.push(data.business.cost_per_follow);
                metricsHistory.posts.push(data.business.posts_per_hour);
                
                // Keep last 50 points
                if (metricsHistory.timestamps.length > 50) {
                    Object.keys(metricsHistory).forEach(key => {
                        metricsHistory[key] = metricsHistory[key].slice(-50);
                    });
                }
                
                // Update chart
                updateChart();
                
                // Update trends
                updateTrends(data.trends);
                
                // Update service health
                updateServiceHealth(data.services);
                
                // Update recommendations
                if (data.analysis && data.analysis.recommendations) {
                    updateRecommendations(data.analysis.recommendations);
                }
            }
            
            function updateChart() {
                const traces = [
                    {
                        x: metricsHistory.timestamps,
                        y: metricsHistory.engagement,
                        name: 'Engagement %',
                        type: 'scatter',
                        line: { color: '#4CAF50' }
                    },
                    {
                        x: metricsHistory.timestamps,
                        y: metricsHistory.cost.map(c => c * 100),
                        name: 'Cost per Follow (cents)',
                        type: 'scatter',
                        yaxis: 'y2',
                        line: { color: '#ff9800' }
                    }
                ];
                
                const layout = {
                    paper_bgcolor: '#2a2a2a',
                    plot_bgcolor: '#2a2a2a',
                    font: { color: '#fff' },
                    showlegend: true,
                    yaxis: { title: 'Engagement %', side: 'left' },
                    yaxis2: { title: 'Cost (cents)', side: 'right', overlaying: 'y' }
                };
                
                Plotly.newPlot('performance-chart', traces, layout);
            }
            
            function updateTrends(trends) {
                const container = document.getElementById('trending-topics');
                container.innerHTML = trends.map(t => `
                    <div class="trend-item">
                        <span>${t.topic}</span>
                        <span>${t.score}</span>
                    </div>
                `).join('');
            }
            
            function updateServiceHealth(services) {
                const container = document.getElementById('service-health');
                container.innerHTML = Object.entries(services).map(([name, status]) => `
                    <div style="margin: 5px 0;">
                        <span class="status-indicator status-${status.healthy ? 'ok' : 'error'}"></span>
                        ${name}
                    </div>
                `).join('');
            }
            
            function updateRecommendations(recommendations) {
                const container = document.getElementById('recommendations');
                container.innerHTML = recommendations.map(rec => `
                    <div class="rec-item">
                        <strong>${rec.action}</strong><br/>
                        <small>${rec.reason}</small>
                    </div>
                `).join('');
            }
        </script>
    </body>
    </html>
    """
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    collector = MetricsCollector()

    try:
        while True:
            # Collect metrics
            metrics = await collector.collect_metrics()

            # Analyze performance
            analysis = collector.analyze_performance()
            metrics["analysis"] = analysis

            # Send to client
            await websocket.send_json(metrics)

            # Update every 5 seconds
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
