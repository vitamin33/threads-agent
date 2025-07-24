# Viral Content Retention Epic - Technical Plan

## Epic Overview
Build a viral content engine that increases user retention by implementing trending topic detection, personalized content recommendations, engagement tracking, and automated A/B testing.

**Target KPIs:**
- 6%+ engagement rate
- 80% user retention
- $0.01 cost per follow

## Current State Analysis

### ✅ What We Have
1. **Engagement Tracking**
   - ThreadsPost model with engagement metrics
   - Engagement rate calculation
   - Prometheus metrics for engagement_rate
   - Background task for metric updates

2. **Viral Content Detection**
   - ML-based engagement predictor
   - Quality scoring (0-1 scale)
   - Hook variant generation
   - Quality gate filtering

3. **Search Integration**
   - SearXNG for trend detection
   - Competitive analysis endpoints
   - Search-enhanced content generation

### ❌ What We Need
1. **User/Follower Tracking**
   - User model with retention data
   - Follower cohort tracking
   - User behavior patterns

2. **A/B Testing Infrastructure**
   - Experiment framework
   - Variant assignment
   - Statistical analysis
   - Winner selection

3. **Retention Analytics**
   - Cohort analysis
   - Churn prediction
   - Retention curves

## Technical Components

### 1. Database Schema Extensions

```sql
-- New tables needed
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    threads_id VARCHAR(255) UNIQUE,
    username VARCHAR(255),
    first_seen TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP,
    cohort_date DATE,
    is_follower BOOLEAN DEFAULT false,
    engagement_score FLOAT DEFAULT 0.0
);

CREATE TABLE user_interactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    post_id BIGINT REFERENCES threads_posts(id),
    interaction_type VARCHAR(50), -- 'like', 'comment', 'share', 'view'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE experiments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    status VARCHAR(50), -- 'active', 'completed', 'paused'
    variant_a_id VARCHAR(255),
    variant_b_id VARCHAR(255),
    winner_id VARCHAR(255),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    significance_level FLOAT
);

CREATE TABLE experiment_assignments (
    id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT REFERENCES experiments(id),
    user_id BIGINT REFERENCES users(id),
    variant VARCHAR(10), -- 'A' or 'B'
    assigned_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Service Modifications

#### A. Orchestrator Service
- **New Endpoints:**
  - `POST /experiments` - Create A/B test
  - `GET /experiments/{id}/results` - Get test results
  - `POST /users/track` - Track user behavior
  - `GET /analytics/retention` - Retention metrics

- **Files to Modify:**
  - `services/orchestrator/main.py` - Add new routes
  - `services/orchestrator/db/models.py` - Add user models
  - Create `services/orchestrator/experiments.py` - A/B testing logic
  - Create `services/orchestrator/analytics.py` - Retention analytics

#### B. Threads Adaptor Service
- **Enhancements:**
  - Parse user data from Threads responses
  - Track interaction sources
  - Update user last_active timestamps

- **Files to Modify:**
  - `services/threads_adaptor/main.py` - Parse user data
  - Add webhook for real-time engagement updates

#### C. Viral Engine Service
- **New Features:**
  - Content recommendation engine
  - Personalization based on user history
  - Time-of-day optimization

- **Files to Create:**
  - `services/viral_engine/recommender.py` - Recommendation logic
  - `services/viral_engine/personalization.py` - User personalization

### 3. Metrics & Monitoring

#### New Prometheus Metrics
```python
# services/common/metrics.py additions
user_retention_rate = Gauge(
    'user_retention_rate',
    'User retention rate by cohort',
    ['cohort_week', 'retention_week']
)

experiment_conversion_rate = Gauge(
    'experiment_conversion_rate',
    'A/B test conversion rates',
    ['experiment_name', 'variant']
)

user_lifetime_value = Histogram(
    'user_lifetime_value_dollars',
    'Estimated user lifetime value',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)
```

#### New Grafana Dashboard
- User retention curves
- A/B test performance
- Cohort analysis
- Engagement heatmaps

## Implementation Phases

### Phase 1: User Tracking Foundation (Week 1)
1. Create database migrations for user tables
2. Implement user tracking in threads_adaptor
3. Add user behavior endpoints to orchestrator
4. Basic retention metrics

### Phase 2: A/B Testing Framework (Week 2)
1. Create experiment management system
2. Implement variant assignment logic
3. Add statistical significance testing
4. Build experiment dashboard

### Phase 3: Recommendation Engine (Week 3)
1. Implement content recommendation algorithm
2. Add personalization features
3. Create feedback loop for improvements
4. Time-of-day optimization

### Phase 4: Integration & Optimization (Week 4)
1. Connect all components
2. Add comprehensive monitoring
3. Performance optimization
4. Documentation and testing

## Success Criteria
1. Track 100% of user interactions
2. Run 5+ A/B tests simultaneously
3. Achieve 6%+ engagement rate
4. Demonstrate 80% week-1 retention
5. Reduce cost per follow to $0.01

## Risk Mitigation
1. **Privacy**: Ensure user data handling complies with policies
2. **Scale**: Design for 10x current load
3. **Accuracy**: Validate engagement predictions
4. **Rollback**: Implement feature flags for safe deployment