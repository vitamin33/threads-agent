# Viral Metrics Testing Suite

This directory contains comprehensive integration and E2E tests for the viral metrics collection system.

## Test Structure

### Core Test Files

- **`conftest.py`** - Test fixtures and configuration
- **`test_integration_comprehensive.py`** - Integration tests for real-time collection
- **`test_batch_processing_performance.py`** - Batch processing and performance tests
- **`test_anomaly_detection_scenarios.py`** - Anomaly detection edge cases
- **`test_e2e_system_integration.py`** - End-to-end system integration tests
- **`test_metrics_collector.py`** - Unit tests for individual components

### Test Categories

#### Integration Tests (@pytest.mark.e2e)
Tests that require the full system stack:
- Real-time metrics collection with <60s SLA
- Redis caching layer with TTL verification  
- Database persistence for metrics history
- Prometheus metrics emission
- Fake-threads API integration

#### Performance Tests
- Batch processing throughput (50-100 posts/batch)
- Parallel execution with concurrency limits
- Memory usage under load
- Performance regression baselines

#### Anomaly Detection Tests
- Viral coefficient drop detection (30%+ threshold)
- Negative engagement trajectory (-50+ threshold)
- Pattern fatigue warnings (>0.8 score)
- Multiple simultaneous anomalies
- Edge cases and data validation

#### System Integration Tests
- Complete workflow from API to database
- Celery task integration
- High concurrency load handling
- System resilience under failures
- Multi-persona batch processing

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Ensure services are available (for integration tests)
just dev-start  # or manual k3d cluster setup
```

### Test Execution

```bash
# Run all viral metrics tests
pytest services/viral_metrics/tests/ -v

# Run only integration tests
pytest services/viral_metrics/tests/ -m e2e -v

# Run specific test file
pytest services/viral_metrics/tests/test_integration_comprehensive.py -v

# Run with performance benchmarking
pytest services/viral_metrics/tests/test_batch_processing_performance.py -v --durations=10

# Run with coverage
pytest services/viral_metrics/tests/ --cov=services.viral_metrics --cov-report=html
```

### Test Markers

- `@pytest.mark.e2e` - Integration tests requiring full system
- `@pytest.mark.asyncio` - Async tests (applied automatically)

## Test Scenarios Covered

### 1. Real-Time Metrics Collection (<60s SLA)
- ✅ Single post metrics collection
- ✅ Concurrent collection (20+ posts)
- ✅ Performance under varying load
- ✅ SLA compliance verification

### 2. Redis Caching Layer
- ✅ Cache hit/miss behavior
- ✅ TTL verification (5-minute default)
- ✅ Cache failure recovery
- ✅ Concurrent cache operations

### 3. Database Persistence  
- ✅ Metrics table inserts
- ✅ History table inserts (6 metrics per post)
- ✅ Database failure recovery
- ✅ Bulk insert optimization

### 4. Prometheus Metrics Emission
- ✅ Gauge metrics for all viral KPIs
- ✅ Histogram metrics for latency
- ✅ Proper label assignment
- ✅ Emission failure handling

### 5. Batch Processing Performance
- ✅ Throughput testing (10-100 posts)
- ✅ Parallel execution limits (5-20 concurrent)
- ✅ Memory usage monitoring
- ✅ Error recovery in batches

### 6. Anomaly Detection Scenarios
- ✅ Viral coefficient drops (30%, 50%, 60%)
- ✅ Negative trajectories (-50, -70, -85)
- ✅ Pattern fatigue (0.8, 0.9, 0.95)
- ✅ Multiple simultaneous anomalies
- ✅ Alert triggering for high severity

## Performance Benchmarks

| Metric | Target | Test Coverage |
|--------|--------|---------------|
| Single collection | < 5s | ✅ test_real_time_metrics_collection_sla |
| Batch processing | < 30s (50 posts) | ✅ test_batch_processing_throughput |
| Database write | < 1s | ✅ test_database_persistence_integration |
| Redis cache | < 0.1s | ✅ test_redis_caching_integration |
| Memory usage | < 100MB (200 posts) | ✅ test_memory_usage_regression |

## Mock Objects and Fixtures

### Key Fixtures
- `mock_redis` - Redis connection with realistic behavior
- `mock_database` - Database with storage simulation
- `mock_prometheus` - Prometheus client with call tracking
- `mock_fake_threads_api` - HTTP transport for API mocking
- `sample_engagement_data` - Realistic engagement data
- `performance_benchmarks` - Performance thresholds

### Custom Assertions
- `assert_valid_metrics_structure()` - Validates metric ranges
- `assert_sla_compliance()` - Verifies timing requirements
- `assert_database_persistence()` - Checks data storage
- `assert_prometheus_emission()` - Validates metrics emission

## Troubleshooting

### Common Issues

1. **Test timeouts**
   ```bash
   # Increase timeout for slow tests
   pytest --timeout=120 services/viral_metrics/tests/
   ```

2. **Mock failures**
   ```bash
   # Clear mock state between tests
   pytest --cache-clear services/viral_metrics/tests/
   ```

3. **Memory issues**
   ```bash
   # Run tests with memory profiling
   pytest --profile services/viral_metrics/tests/test_batch_processing_performance.py
   ```

### Performance Analysis

```bash
# Generate performance report
pytest services/viral_metrics/tests/ --benchmark-only --benchmark-sort=mean

# Memory profiling
pytest services/viral_metrics/tests/test_e2e_system_integration.py --profile-svg
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Viral Metrics Tests
  run: |
    pytest services/viral_metrics/tests/ -v \
      --cov=services.viral_metrics \
      --cov-report=xml \
      --junit-xml=test-results.xml
```

### Performance Gates
- Single collection: < 5s (fails CI if exceeded)
- Batch processing: < 30s for 50 posts
- Memory usage: < 100MB for 200 posts
- Test success rate: > 95%

## Test Data

### Engagement Data Scenarios
- **High Performance**: 50K views, 7.5K likes, viral coefficient ~20%
- **Medium Performance**: 2.5K views, 375 likes, viral coefficient ~13%  
- **Low Performance**: 500 views, 15 likes, viral coefficient ~4%

### Anomaly Scenarios
- **Viral Coefficient Drop**: 60% baseline to current comparison
- **Negative Trajectory**: -75 engagement acceleration
- **Pattern Fatigue**: 0.85+ fatigue score

## Contributing

### Adding New Tests

1. **Integration Tests** - Add to `test_integration_comprehensive.py`
2. **Performance Tests** - Add to `test_batch_processing_performance.py`
3. **Anomaly Tests** - Add to `test_anomaly_detection_scenarios.py`
4. **E2E Tests** - Add to `test_e2e_system_integration.py`

### Test Naming Convention
- `test_[component]_[scenario]_[expected_behavior]`
- Use descriptive names that explain the test purpose
- Include performance expectations in test names when relevant

### Required Test Elements
- Clear docstring explaining test purpose
- Proper fixture usage
- Performance assertions where applicable
- Error condition testing
- Mock verification

This comprehensive test suite ensures the viral metrics system meets all performance, reliability, and functionality requirements.