# FinOps Executive Dashboards

Comprehensive Grafana dashboards for executive-level monitoring of the CRA-242 FinOps Executive Dashboard implementation. These dashboards provide real-time insights into business performance, cost optimization, and operational health.

## 📊 Dashboard Overview

### 1. Executive Summary Dashboard
**File:** `dashboards/executive-summary.json`
**Purpose:** High-level KPIs and business metrics for C-level executives

**Key Metrics:**
- ROI Percentage (Target: 300%+)
- Monthly Revenue Progress ($20k Target)
- Engagement Rate (Target: 6%+)
- Cost per Post Efficiency
- Revenue vs Cost Trends
- Growth Rate Indicators
- Monthly Target Achievement
- Efficiency Score Trends

**Refresh:** 5 minutes
**Best for:** Board meetings, executive reviews, strategic decisions

### 2. Revenue Attribution Dashboard
**File:** `dashboards/revenue-attribution.json`
**Purpose:** Detailed revenue analysis by content patterns, personas, and timing

**Key Features:**
- Revenue by Content Pattern (pie chart)
- Revenue by Persona (donut chart)
- Revenue by Posting Time (bar chart)
- Conversion Funnel Analysis
- Top Performing Content Analysis
- Revenue Trends by Pattern
- Attribution Accuracy Metrics

**Refresh:** 5 minutes
**Best for:** Marketing strategy, content optimization, attribution analysis

### 3. Cost Optimization Dashboard
**File:** `dashboards/cost-optimization.json`
**Purpose:** Cost breakdown, optimization recommendations, and efficiency tracking

**Key Features:**
- Cost Breakdown by Category (pie chart)
- Budget Utilization (gauge)
- Cost Trends Over Time
- Cost per Engagement Metrics
- Potential Savings Opportunities
- Optimization Recommendations (table)
- Model Usage Cost Analysis
- Efficiency Improvement Trends
- Infrastructure Cost Breakdown

**Refresh:** 5 minutes
**Best for:** CFO reviews, cost management, optimization planning

### 4. Real-time Operations Dashboard
**File:** `dashboards/realtime-operations.json`
**Purpose:** Live operational monitoring with 30-second refresh

**Key Features:**
- System Health Overview
- Live Content Generation Velocity
- Real-time Cost Tracking
- Service Performance Metrics
- Active Alerts and Notifications
- Current Engagement Metrics
- Resource Usage Monitoring
- API Response Times
- Error Rate Monitoring
- Queue Status

**Refresh:** 30 seconds
**Best for:** Operations teams, incident response, real-time monitoring

## 🔧 Configuration Files

### Data Sources
**File:** `datasources/finops-datasources.yml`

Configured data sources:
- **Prometheus:** Primary metrics storage
- **Loki:** Log aggregation and analysis
- **Jaeger:** Distributed tracing
- **FinOps API:** Custom JSON endpoints
- **PostgreSQL:** Raw data access
- **InfluxDB:** Time-series analytics (optional)
- **CloudWatch/Azure Monitor:** Cloud provider metrics (optional)

### Dashboard Provisioning
**File:** `provisioning/dashboards.yml`

Automatic dashboard deployment and updates:
- **Executive Dashboards:** 30-second update interval
- **Business KPIs:** 60-second update interval
- **Real-time Operations:** 10-second update interval
- **Folder Organization:** Structured by dashboard type
- **Permissions:** Role-based access control

### Alert Rules
**File:** `alerting/finops-alert-rules.yml`

Comprehensive alerting for:
- **Business Alerts:** ROI, revenue, growth targets
- **Cost Alerts:** Budget utilization, cost spikes
- **Performance Alerts:** Engagement rates, system health
- **Operational Alerts:** Service outages, error rates
- **Data Quality Alerts:** Attribution accuracy, data completeness

## 🚀 Quick Start

### 1. Deploy Dashboards
```bash
# Copy dashboards to Grafana provisioning directory
kubectl cp monitoring/grafana/dashboards/ grafana-pod:/etc/grafana/provisioning/dashboards/

# Or use Helm values (recommended)
helm upgrade threads-agent ./chart \
  --set grafana.dashboards.enabled=true \
  --set grafana.dashboards.path=/etc/grafana/provisioning/dashboards
```

### 2. Configure Data Sources
```bash
# Apply data source configuration
kubectl apply -f monitoring/grafana/datasources/finops-datasources.yml

# Verify data source connectivity
kubectl exec -it grafana-pod -- grafana-cli admin data-source list
```

### 3. Set Up Alerts
```bash
# Deploy alert rules
kubectl apply -f monitoring/grafana/alerting/finops-alert-rules.yml

# Configure notification channels
kubectl exec -it grafana-pod -- grafana-cli admin reset-admin-password newpassword
```

### 4. Access Dashboards
```bash
# Port forward to Grafana
kubectl port-forward svc/grafana 3000:3000

# Open in browser
open http://localhost:3000

# Default credentials
# Username: admin
# Password: (check Helm values or reset)
```

## 📱 Mobile Responsiveness

All dashboards are optimized for mobile viewing:
- **Responsive breakpoints:** 768px (mobile), 1024px (tablet)
- **Compact layouts:** Single-column mobile view
- **Key metrics summary:** Simplified mobile dashboard
- **Touch-friendly:** Large touch targets and gestures

## 🔗 API Integration

### FinOps Engine Endpoints
The dashboards integrate with these API endpoints:

```bash
# Executive Summary
GET /dashboard/executive/summary

# Revenue Attribution
GET /revenue-attribution

# Cost Optimization
GET /cost-optimization

# Real-time WebSocket
WS /dashboard/realtime

# Mobile Dashboard
GET /dashboard/mobile
```

### Prometheus Metrics
Key metrics collected and displayed:

```promql
# ROI and Business Metrics
finops_roi_percentage
finops_total_revenue
finops_total_costs
finops_growth_rate
finops_efficiency_score

# Attribution Metrics
finops_revenue_by_persona
finops_revenue_by_pattern
finops_attribution_accuracy

# Cost Metrics
finops_cost_breakdown
finops_budget_utilization_percentage
finops_cost_per_engagement

# Operational Metrics
finops_system_health_score
finops_service_health
finops_api_request_duration_seconds
```

## 🚨 Alert Configuration

### Alert Levels
- **Critical:** Immediate attention required (PagerDuty, Slack)
- **Warning:** Action needed within business hours (Email, Slack)
- **Info:** Informational notifications (Email)

### Business Thresholds
- **ROI Target:** 300%+ (Warning: <300%, Critical: <200%)
- **Revenue Target:** $20k/month (Warning: <$16k)
- **Engagement Rate:** 6%+ (Warning: <4%, Critical: <2%)
- **Budget Utilization:** 100% (Warning: >90%, Critical: >100%)

### Notification Channels
Configure these in your environment:
```yaml
# Slack Webhook
SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# PagerDuty Service Key
PAGERDUTY_SERVICE_KEY: "YOUR_PAGERDUTY_SERVICE_KEY"

# Executive Email List
EXECUTIVE_EMAILS: "executives@threadsagent.com"
```

## 🛠 Customization

### Adding New Metrics
1. **Define Prometheus metric** in finops_engine service
2. **Update dashboard JSON** with new panel
3. **Add alert rule** if threshold monitoring needed
4. **Test visualization** with sample data

### Dashboard Modifications
1. **Edit JSON files** directly or use Grafana UI
2. **Export from UI** to update JSON files
3. **Validate JSON** before deployment
4. **Update provisioning** if folder structure changes

### Template Variables
Add dynamic filtering:
```json
{
  "name": "environment",
  "type": "custom",
  "options": [
    {"text": "Production", "value": "prod"},
    {"text": "Staging", "value": "staging"},
    {"text": "Development", "value": "dev"}
  ]
}
```

## 📈 Performance Optimization

### Dashboard Performance
- **Query optimization:** Use recording rules for complex queries
- **Cache settings:** Configure appropriate cache TTLs
- **Refresh intervals:** Balance freshness vs. load
- **Panel limits:** Limit data points for performance

### Data Source Optimization
- **Prometheus:** Use appropriate retention and scrape intervals
- **Query parallelization:** Enable concurrent queries
- **Index optimization:** Ensure proper metric labeling
- **Aggregation rules:** Pre-calculate common queries

## 🔍 Troubleshooting

### Common Issues

**Dashboard not loading:**
```bash
# Check Grafana logs
kubectl logs grafana-pod

# Verify data source connectivity
kubectl exec -it grafana-pod -- wget -O- http://prometheus:9090/api/v1/query?query=up
```

**Missing data:**
```bash
# Check FinOps engine metrics
curl http://finops-engine:8000/metrics

# Verify Prometheus targets
curl http://prometheus:9090/api/v1/targets
```

**Alerts not firing:**
```bash
# Check alert manager
kubectl logs alertmanager-pod

# Test notification channels
kubectl exec -it alertmanager-pod -- amtool config routes test
```

### Debug Mode
Enable debug logging:
```yaml
grafana:
  grafana.ini:
    log:
      level: debug
    metrics:
      enabled: true
```

## 📚 Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/)
- [FinOps Engine API Documentation](../services/finops_engine/README.md)
- [Alert Manager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)

## 🤝 Contributing

When adding new dashboards or metrics:
1. Follow existing naming conventions
2. Add appropriate documentation
3. Include alert rules for critical metrics
4. Test mobile responsiveness
5. Update this README

## 📄 License

This dashboard configuration is part of the threads-agent project and follows the same license terms.