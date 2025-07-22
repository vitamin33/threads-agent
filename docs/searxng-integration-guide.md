# SearXNG Integration Guide for Threads-Agent

## Overview
This guide explains how SearXNG search capabilities are integrated into the threads-agent development and planning system to enhance content generation, trend detection, and competitive analysis.

## Architecture Integration

### 1. Search Wrapper Service (`services/common/searxng_wrapper.py`)
- **Purpose**: Centralized search API wrapper with caching
- **Features**:
  - Sync/async search methods
  - Result caching (1-hour TTL)
  - Trend detection
  - Viral pattern analysis
  - Competitive intelligence

### 2. Enhanced Persona Runtime (`services/persona_runtime/search_enhanced_runtime.py`)
- **Purpose**: Search-aware content generation
- **New Workflow Nodes**:
  - `trend_research`: Discovers trending topics before hook generation
  - `competitive_analysis`: Analyzes viral patterns for style guidance
- **Benefits**:
  - Context-aware hooks
  - Trend-aligned content
  - Viral pattern incorporation

### 3. Orchestrator Search Endpoints (`services/orchestrator/search_endpoints.py`)
- **New API Endpoints**:
  - `POST /search/trends` - Find trending topics
  - `POST /search/competitive` - Analyze viral content
  - `POST /search/quick` - General search
  - `POST /search/enhanced-task` - Search-powered content generation

### 4. Monitoring & Metrics
- **New Prometheus Metrics**:
  - `search_requests_total` - Search usage tracking
  - `search_latency_seconds` - Performance monitoring
  - `trends_discovered_total` - Trend detection success
  - `viral_patterns_analyzed_total` - Competitive analysis tracking
  - `search_enhanced_posts_total` - Enhanced content tracking

### 5. Automated Workflows (`scripts/trend-detection-workflow.sh`)
- **Features**:
  - Hourly trend detection
  - Automatic content generation triggers
  - Multi-persona support
  - Dashboard view

## Quick Start

### 1. Start SearXNG
```bash
just searxng-start
```

### 2. Test Search
```bash
just searxng-test "AI mental health trends"
```

### 3. Check Trends
```bash
just trend-check "AI and productivity"
```

### 4. Generate Trending Content
```bash
just trend-generate ai-jesus "AI spirituality"
```

### 5. Start Automated Workflow
```bash
just trend-start  # Runs continuously, checking trends hourly
```

## Development Workflow Integration

### For Content Generation
1. **Manual Search-Enhanced Post**:
   ```bash
   just search-enhanced-post ai-elon "Mars colonization"
   ```

2. **Competitive Analysis First**:
   ```bash
   just competitive-analysis "AI productivity tips"
   # Review viral patterns
   just trend-generate ai-jesus "AI productivity tips"
   ```

### For Planning & Strategy
1. **Trend Dashboard**:
   ```bash
   just trend-dashboard
   ```
   Shows:
   - Current trending topics
   - Recent enhanced tasks
   - Service status

2. **Market Research**:
   ```bash
   # Find what's trending
   just trend-check "mental health AI"
   
   # Analyze competition
   just competitive-analysis "AI therapy" threads
   ```

### For Monitoring
- **Grafana Dashboards**: Search metrics integrated into business KPIs
- **Prometheus Metrics**: Track search usage, cache hits, trend relevance
- **Alerts**: Notify when trending topics match target keywords

## Use Cases

### 1. Trend-Driven Content Strategy
- Hourly trend detection finds emerging topics
- Automatically generates content for hot trends
- Measures engagement vs trend relevance

### 2. Competitive Intelligence
- Analyze what's going viral in your niche
- Extract successful content patterns
- Learn from high-engagement posts

### 3. Persona Optimization
- Test which personas perform best on trending topics
- Adapt content style based on viral patterns
- A/B test search-enhanced vs standard content

### 4. Real-Time Relevance
- Posts include current trends and news
- Higher engagement from timely content
- Reduced chance of outdated references

## Configuration

### Environment Variables
```bash
# In your .env or k8s secrets
SEARXNG_URL=http://localhost:8888
SEARCH_ENABLED=true
SEARCH_TIMEOUT=10
TREND_CHECK_INTERVAL=3600  # 1 hour
```

### Helm Values
```yaml
# chart/values-dev.yaml
orchestrator:
  env:
    SEARXNG_URL: "http://searxng:8888"
    SEARCH_ENABLED: "true"

persona_runtime:
  env:
    SEARCH_ENABLED: "true"
```

## Best Practices

### 1. Cache Management
- Search results cached for 1 hour
- Monitor cache hit rates via metrics
- Clear cache if switching search engines

### 2. Rate Limiting
- SearXNG self-hosted = no rate limits
- Still space out requests (2s between)
- Use async methods for parallel searches

### 3. Content Quality
- Review search context before generation
- Don't over-optimize for trends
- Maintain persona voice consistency

### 4. Monitoring
- Track search-enhanced post performance
- Compare engagement: enhanced vs standard
- Adjust trend timeframes based on results

## Troubleshooting

### SearXNG Not Starting
```bash
# Check Docker
docker ps | grep searxng

# View logs
just searxng-logs

# Restart
just searxng-stop
just searxng-start
```

### No Search Results
```bash
# Test SearXNG directly
curl "http://localhost:8888/search?q=test&format=json"

# Check orchestrator logs
kubectl logs deploy/orchestrator | grep search
```

### Trends Not Updating
```bash
# Check workflow status
ps aux | grep trend-detection

# Manual trend check
just trend-check "your topic"

# Clear cache and retry
rm -rf ./data/trending_topics.json*
```

## Future Enhancements

### Phase 1 (Current)
- ✅ Basic search integration
- ✅ Trend detection
- ✅ Competitive analysis
- ✅ Search metrics

### Phase 2 (Planned)
- [ ] ML-based trend prediction
- [ ] Sentiment analysis on viral content
- [ ] Auto-persona selection based on trends
- [ ] Search result quality scoring

### Phase 3 (Future)
- [ ] Multi-language trend detection
- [ ] Platform-specific optimization
- [ ] Predictive content calendar
- [ ] ROI tracking per trend

## Conclusion

The SearXNG integration transforms threads-agent from a static content generator to a dynamic, trend-aware system that:
- Discovers what's hot in real-time
- Learns from successful content
- Automatically adapts to market changes
- Provides data-driven content strategy

This positions your threads-agent system to achieve the 6%+ engagement target by surfing trends and creating timely, relevant content.