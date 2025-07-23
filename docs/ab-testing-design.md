# A/B Testing Infrastructure Design

## Overview
Build a sophisticated A/B testing system for the Threads Laboratory that can:
- Run multiple concurrent experiments
- Calculate statistical significance
- Automatically stop poor performers
- Schedule posts intelligently
- Select winners based on data

## Architecture

### 1. Experiment Management

#### Database Schema
```sql
-- Experiments table
CREATE TABLE experiments (
    id BIGSERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    description TEXT,
    persona_id VARCHAR(50),
    status VARCHAR(50), -- 'draft', 'active', 'paused', 'completed'
    type VARCHAR(50), -- 'ab_test', 'multi_variant', 'bandit'
    
    -- Configuration
    min_sample_size INT DEFAULT 100,
    max_duration_hours INT DEFAULT 72,
    confidence_level FLOAT DEFAULT 0.95,
    power FLOAT DEFAULT 0.8,
    
    -- Scheduling
    posts_per_hour INT DEFAULT 2,
    posting_hours JSONB, -- {"start": 9, "end": 21}
    
    -- Results
    winner_variant_id VARCHAR(50),
    significance_achieved BOOLEAN DEFAULT FALSE,
    p_value FLOAT,
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Experiment variants (extends hook_variants)
CREATE TABLE experiment_variants (
    id BIGSERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) REFERENCES experiments(experiment_id),
    variant_id VARCHAR(50) REFERENCES hook_variants(variant_id),
    
    -- Assignment
    traffic_allocation FLOAT DEFAULT 0.5, -- For uneven splits
    is_control BOOLEAN DEFAULT FALSE,
    
    -- Performance
    posts_count INT DEFAULT 0,
    impressions_total INT DEFAULT 0,
    engagements_total INT DEFAULT 0,
    engagement_rate FLOAT,
    
    -- Statistical data
    conversion_count INT DEFAULT 0,
    mean_engagement FLOAT,
    variance FLOAT,
    standard_error FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Statistical Analysis Engine

#### Core Statistical Functions
```python
class StatisticalAnalyzer:
    """Handles all statistical calculations for experiments"""
    
    def calculate_sample_size(self, baseline_rate, minimum_effect, power=0.8, alpha=0.05):
        """Calculate required sample size for desired power"""
        
    def test_significance(self, control_data, variant_data, test_type='two_tailed'):
        """Perform statistical significance test"""
        # Returns: p_value, confidence_interval, effect_size
        
    def calculate_bayesian_probability(self, control_metrics, variant_metrics):
        """Bayesian approach for early stopping"""
        
    def sequential_testing(self, data_stream):
        """Sequential probability ratio test for continuous monitoring"""
```

### 3. Multi-Armed Bandit Implementation

#### Thompson Sampling Algorithm
```python
class ThompsonSampling:
    """Adaptive traffic allocation based on performance"""
    
    def __init__(self, n_variants):
        self.successes = np.ones(n_variants)  # Beta dist alpha
        self.failures = np.ones(n_variants)   # Beta dist beta
    
    def select_variant(self):
        """Sample from posterior and select best"""
        samples = [
            np.random.beta(self.successes[i], self.failures[i])
            for i in range(len(self.successes))
        ]
        return np.argmax(samples)
    
    def update(self, variant_idx, success):
        """Update posterior with new observation"""
        if success:
            self.successes[variant_idx] += 1
        else:
            self.failures[variant_idx] += 1
```

### 4. Intelligent Posting Scheduler

#### Features
- Time-of-day optimization
- Avoid flooding (space posts)
- Respect rate limits
- Prioritize experiments nearing significance
- Balance variant exposure

#### Implementation
```python
class ExperimentScheduler:
    """Manages posting schedule for all active experiments"""
    
    def __init__(self):
        self.active_experiments = []
        self.posting_queue = PriorityQueue()
        
    def schedule_next_posts(self, time_window_hours=1):
        """Determine what to post in next time window"""
        
        for experiment in self.active_experiments:
            # Check if experiment needs more data
            if experiment.needs_more_samples():
                # Select variant based on strategy
                variant = experiment.select_next_variant()
                
                # Calculate optimal posting time
                post_time = self.calculate_optimal_time(
                    experiment.persona_id,
                    experiment.posting_hours
                )
                
                # Add to queue with priority
                priority = self.calculate_priority(experiment)
                self.posting_queue.put((priority, post_time, variant))
    
    def calculate_priority(self, experiment):
        """Higher priority for experiments close to significance"""
        # Consider: time running, samples collected, p-value trajectory
```

### 5. Auto-Stop Mechanisms

#### Stopping Rules
1. **Statistical Significance**: Stop when p < 0.05
2. **Futility Stopping**: Stop if unlikely to find effect
3. **Poor Performance**: Stop variants with engagement < 2%
4. **Maximum Duration**: Stop after max_duration_hours
5. **Bayesian Stopping**: Stop when P(variant > control) > 0.95

```python
class ExperimentMonitor:
    """Monitors experiments and applies stopping rules"""
    
    def check_stopping_conditions(self, experiment):
        """Check all stopping conditions"""
        
        # 1. Statistical significance
        if experiment.p_value < experiment.confidence_level:
            return "significance_reached"
            
        # 2. Futility check
        if self.is_futile(experiment):
            return "futility"
            
        # 3. Poor performance
        for variant in experiment.variants:
            if variant.engagement_rate < 0.02 and variant.posts_count > 20:
                variant.disable()
                
        # 4. Time limit
        if experiment.duration_hours > experiment.max_duration_hours:
            return "max_duration"
            
        # 5. Bayesian stopping
        prob = self.calculate_win_probability(experiment)
        if prob > 0.95 or prob < 0.05:
            return "bayesian_threshold"
```

## API Endpoints

### Experiment Management
```
POST   /experiments/create
GET    /experiments/{id}
PUT    /experiments/{id}/pause
PUT    /experiments/{id}/resume
DELETE /experiments/{id}
GET    /experiments/active
```

### Statistical Analysis
```
GET    /experiments/{id}/significance
GET    /experiments/{id}/power-analysis
POST   /experiments/{id}/calculate-sample-size
GET    /experiments/{id}/confidence-intervals
```

### Scheduling
```
GET    /scheduler/next-posts
POST   /scheduler/override
GET    /scheduler/calendar
```

### Monitoring
```
GET    /experiments/{id}/dashboard
GET    /experiments/{id}/real-time-stats
WS     /experiments/{id}/stream  # WebSocket for real-time updates
```

## Implementation Plan

### Phase 1: Core Statistical Engine (Week 1)
1. Implement statistical functions
2. Create experiment models
3. Build significance testing
4. Add Bayesian analysis

### Phase 2: Scheduling System (Week 1-2)
1. Create Celery Beat tasks
2. Build posting queue
3. Implement rate limiting
4. Add time optimization

### Phase 3: Monitoring & Automation (Week 2)
1. Auto-stop mechanisms
2. Real-time monitoring
3. Winner selection
4. Reporting system

### Phase 4: Advanced Features (Week 2+)
1. Multi-armed bandits
2. Segmentation
3. Interaction effects
4. Meta-analysis

## Success Metrics
- Run 20+ experiments concurrently
- Achieve significance in <48 hours
- Reduce poor content by 90%
- Increase avg engagement to 8%+
- Save 80% of manual testing time