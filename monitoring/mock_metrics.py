#!/usr/bin/env python3
"""Mock metrics generator for interview demo"""

import random
from http.server import HTTPServer, BaseHTTPRequestHandler

# Mock Prometheus metrics
METRICS_TEMPLATE = """# HELP posts_engagement_rate Current engagement rate of posts
# TYPE posts_engagement_rate gauge
posts_engagement_rate{{persona_id="techie"}} {engagement_rate}
posts_engagement_rate{{persona_id="entrepreneur"}} {engagement_rate2}

# HELP cost_per_follow_dollars Cost per follower in USD  
# TYPE cost_per_follow_dollars gauge
cost_per_follow_dollars{{persona_id="techie"}} {cost_per_follow}
cost_per_follow_dollars{{persona_id="entrepreneur"}} {cost_per_follow2}

# HELP revenue_projection_monthly Monthly revenue projection in USD
# TYPE revenue_projection_monthly gauge
revenue_projection_monthly {revenue}

# HELP request_latency_seconds Request latency in seconds
# TYPE request_latency_seconds histogram
request_latency_seconds_bucket{{service="orchestrator",endpoint="/task",le="0.05"}} {bucket_50ms}
request_latency_seconds_bucket{{service="orchestrator",endpoint="/task",le="0.1"}} {bucket_100ms}
request_latency_seconds_bucket{{service="orchestrator",endpoint="/task",le="0.5"}} {bucket_500ms}
request_latency_seconds_bucket{{service="orchestrator",endpoint="/task",le="+Inf"}} {bucket_inf}
request_latency_seconds_sum{{service="orchestrator",endpoint="/task"}} {latency_sum}
request_latency_seconds_count{{service="orchestrator",endpoint="/task"}} {latency_count}

# HELP token_usage_total Total tokens used by model and service
# TYPE token_usage_total counter
token_usage_total{{model="gpt-4o",service="persona_runtime"}} {tokens_4o}
token_usage_total{{model="gpt-3.5-turbo",service="conversation_engine"}} {tokens_35}

# HELP active_conversations Number of active DM conversations
# TYPE active_conversations gauge
active_conversations {active_convos}

# HELP cache_hit_rate Cache hit rate percentage
# TYPE cache_hit_rate gauge
cache_hit_rate {cache_rate}

# HELP error_rate_total Total errors by service
# TYPE error_rate_total counter
error_rate_total{{service="orchestrator",error_type="timeout"}} {errors}

# HELP posts_published_total Total posts published
# TYPE posts_published_total counter
posts_published_total{{persona_id="techie"}} {posts_techie}
posts_published_total{{persona_id="entrepreneur"}} {posts_entrepreneur}

# HELP service_uptime_seconds Service uptime in seconds
# TYPE service_uptime_seconds gauge
service_uptime_seconds{{service="orchestrator"}} {uptime_orchestrator}
service_uptime_seconds{{service="celery_worker"}} {uptime_celery}

# HELP viral_posts_total Posts with >10% engagement
# TYPE viral_posts_total counter
viral_posts_total {viral_count}

# HELP follower_growth_rate Follower growth rate per hour
# TYPE follower_growth_rate gauge
follower_growth_rate {growth_rate}
"""


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            # Generate realistic metrics
            metrics = METRICS_TEMPLATE.format(
                engagement_rate=round(random.uniform(5.8, 6.5), 2),
                engagement_rate2=round(random.uniform(5.5, 6.3), 2),
                cost_per_follow=round(random.uniform(0.008, 0.011), 3),
                cost_per_follow2=round(random.uniform(0.009, 0.012), 3),
                revenue=round(random.uniform(20000, 25000), 2),
                bucket_50ms=random.randint(180, 220),
                bucket_100ms=random.randint(250, 280),
                bucket_500ms=random.randint(290, 310),
                bucket_inf=random.randint(290, 310),
                latency_sum=round(random.uniform(30, 40), 2),
                latency_count=random.randint(290, 310),
                tokens_4o=random.randint(45000, 55000),
                tokens_35=random.randint(30000, 40000),
                active_convos=random.randint(40, 60),
                cache_rate=round(random.uniform(85, 92), 1),
                errors=random.randint(0, 5),
                posts_techie=random.randint(1200, 1500),
                posts_entrepreneur=random.randint(1100, 1400),
                uptime_orchestrator=random.randint(86400, 172800),
                uptime_celery=random.randint(86400, 172800),
                viral_count=random.randint(45, 65),
                growth_rate=round(random.uniform(120, 180), 1),
            )

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(metrics.encode())
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress logs for cleaner output
        pass


if __name__ == "__main__":
    print("🚀 Starting mock metrics server on :8080")
    print("📊 Metrics available at http://localhost:8080/metrics")
    server = HTTPServer(("0.0.0.0", 8080), MetricsHandler)
    server.serve_forever()
