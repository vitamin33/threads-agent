# Viral Scraper Testing Guide

## Overview

This guide covers comprehensive testing strategies for the Viral Content Scraper Service, including unit tests, integration tests, performance tests, and end-to-end validation.

## Test Architecture

### Test Structure

```
tests/
├── __init__.py
├── test_health.py              # Health endpoint validation
├── test_models.py              # ViralPost data model tests
├── test_rate_limiting.py       # Rate limiter behavior tests
├── test_scraping_endpoints.py  # API endpoint functionality
└── test_viral_posts_endpoint.py # Content retrieval tests
```

### Test Categories

1. **Unit Tests**: Individual component validation (models, rate limiter)
2. **Integration Tests**: API endpoint behavior and interactions
3. **Performance Tests**: Load testing and scalability validation
4. **End-to-End Tests**: Complete workflow validation
5. **Contract Tests**: API contract compliance

## Test Coverage Status

### Current Results (17/19 tests passing)

```bash
pytest tests/ -v --tb=short

# Expected output:
tests/test_health.py::test_health_endpoint ✓
tests/test_models.py::test_viral_post_creation ✓
tests/test_models.py::test_viral_post_validation ✓
tests/test_models.py::test_top_1_percent_detection ✓
tests/test_rate_limiting.py::test_single_account_rate_limiting ✓
tests/test_rate_limiting.py::test_different_accounts_not_rate_limited ✓
tests/test_rate_limiting.py::test_rate_limit_reset ✓
tests/test_rate_limiting.py::test_rate_limit_status_endpoint ✓
tests/test_scraping_endpoints.py::test_scrape_account_success ✓
tests/test_scraping_endpoints.py::test_scrape_account_with_params ✓
tests/test_scraping_endpoints.py::test_scrape_account_rate_limited ✓
tests/test_scraping_endpoints.py::test_task_status_endpoint ✓
tests/test_viral_posts_endpoint.py::test_get_viral_posts_basic ✓
tests/test_viral_posts_endpoint.py::test_get_viral_posts_filtered ✓
tests/test_viral_posts_endpoint.py::test_get_viral_posts_top_1_percent ✓
tests/test_viral_posts_endpoint.py::test_get_viral_posts_by_account ✓
tests/test_viral_posts_endpoint.py::test_pagination_parameters ✓

# 2 failing tests (edge cases to be implemented)
```

## Running Tests

### Development Environment Setup

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Basic test run
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Specific test categories
python -m pytest tests/test_models.py -v
python -m pytest tests/test_rate_limiting.py -v
python -m pytest tests/ -k "rate_limit" -v

# Parallel test execution
pip install pytest-xdist
python -m pytest tests/ -n auto
```

### Docker Test Environment

```bash
# Build test image
docker build -t viral-scraper-test -f Dockerfile.test .

# Run tests in container
docker run --rm viral-scraper-test pytest tests/ -v

# Run with coverage
docker run --rm -v $(pwd):/app viral-scraper-test \
  pytest tests/ --cov=. --cov-report=html
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Test Viral Scraper

on:
  push:
    branches: [main, develop]
    paths: ['services/viral_scraper/**']
  pull_request:
    paths: ['services/viral_scraper/**']

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      working-directory: services/viral_scraper
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov httpx
    
    - name: Run tests
      working-directory: services/viral_scraper
      run: |
        pytest tests/ -v --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: services/viral_scraper/coverage.xml
        path_to_write_report: services/viral_scraper/
```

## Unit Tests

### Model Validation Tests

```python
# tests/test_models.py
import pytest
from datetime import datetime
from pydantic import ValidationError
from models import ViralPost

class TestViralPostModel:
    """Test ViralPost data model validation and behavior"""
    
    def test_valid_viral_post_creation(self):
        """Test creating a valid ViralPost instance"""
        post_data = {
            "content": "This is a viral post about AI trends!",
            "account_id": "tech_influencer_123",
            "post_url": "https://threads.net/tech/post/123",
            "timestamp": datetime.now(),
            "likes": 1000,
            "comments": 50,
            "shares": 200,
            "engagement_rate": 0.15,
            "performance_percentile": 99.5
        }
        
        post = ViralPost(**post_data)
        
        assert post.content == "This is a viral post about AI trends!"
        assert post.account_id == "tech_influencer_123"
        assert post.likes == 1000
        assert post.performance_percentile == 99.5
        assert post.is_top_1_percent() is True
    
    def test_top_1_percent_detection(self):
        """Test top 1% performance tier detection"""
        # Top 1% post (>99th percentile)
        top_post = ViralPost(
            content="Viral content",
            account_id="test",
            post_url="https://test.com",
            timestamp=datetime.now(),
            likes=5000,
            comments=200,
            shares=1000,
            engagement_rate=0.25,
            performance_percentile=99.5
        )
        assert top_post.is_top_1_percent() is True
        
        # Regular post (not top 1%)
        regular_post = ViralPost(
            content="Regular content",
            account_id="test",
            post_url="https://test.com",
            timestamp=datetime.now(),
            likes=100,
            comments=5,
            shares=10,
            engagement_rate=0.05,
            performance_percentile=85.0
        )
        assert regular_post.is_top_1_percent() is False
    
    def test_validation_errors(self):
        """Test model validation for invalid data"""
        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            ViralPost()
        assert "field required" in str(exc_info.value)
        
        # Negative engagement metrics
        with pytest.raises(ValidationError) as exc_info:
            ViralPost(
                content="Test",
                account_id="test",
                post_url="https://test.com",
                timestamp=datetime.now(),
                likes=-100,  # Invalid negative value
                comments=5,
                shares=10,
                engagement_rate=0.05,
                performance_percentile=50.0
            )
        assert "ensure this value is greater than or equal to 0" in str(exc_info.value)
        
        # Invalid engagement rate (>1.0)
        with pytest.raises(ValidationError) as exc_info:
            ViralPost(
                content="Test",
                account_id="test",
                post_url="https://test.com",
                timestamp=datetime.now(),
                likes=100,
                comments=5,
                shares=10,
                engagement_rate=1.5,  # Invalid >1.0
                performance_percentile=50.0
            )
        assert "ensure this value is less than or equal to 1" in str(exc_info.value)
        
        # Invalid performance percentile (>100.0)
        with pytest.raises(ValidationError) as exc_info:
            ViralPost(
                content="Test",
                account_id="test",
                post_url="https://test.com",
                timestamp=datetime.now(),
                likes=100,
                comments=5,
                shares=10,
                engagement_rate=0.05,
                performance_percentile=150.0  # Invalid >100.0
            )
        assert "ensure this value is less than or equal to 100" in str(exc_info.value)
```

### Rate Limiter Tests

```python
# tests/test_rate_limiting.py
import pytest
import time
from rate_limiter import RateLimiter

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_single_account_rate_limiting(self):
        """Test rate limiting for single account"""
        limiter = RateLimiter(requests_per_window=1, window_seconds=60)
        account_id = "test_account"
        
        # First request should be allowed
        assert limiter.check_rate_limit(account_id) is True
        
        # Second immediate request should be rate limited
        assert limiter.check_rate_limit(account_id) is False
        
        # Retry after should be positive
        retry_after = limiter.get_retry_after(account_id)
        assert retry_after > 0
        assert retry_after <= 60
    
    def test_different_accounts_independent(self):
        """Test that rate limiting is per-account"""
        limiter = RateLimiter(requests_per_window=1, window_seconds=60)
        
        # First account
        assert limiter.check_rate_limit("account_1") is True
        assert limiter.check_rate_limit("account_1") is False
        
        # Different account should not be rate limited
        assert limiter.check_rate_limit("account_2") is True
        assert limiter.check_rate_limit("account_2") is False
    
    def test_rate_limit_reset(self):
        """Test rate limit reset after time window"""
        limiter = RateLimiter(requests_per_window=1, window_seconds=0.1)  # 100ms window
        account_id = "test_account"
        
        # First request
        assert limiter.check_rate_limit(account_id) is True
        
        # Should be rate limited immediately
        assert limiter.check_rate_limit(account_id) is False
        
        # Wait for window to pass
        time.sleep(0.15)
        
        # Should be allowed again
        assert limiter.check_rate_limit(account_id) is True
    
    def test_rate_limit_status(self):
        """Test rate limit status reporting"""
        limiter = RateLimiter(requests_per_window=1, window_seconds=60)
        account_id = "test_account"
        
        # Before any requests
        status = limiter.get_status(account_id)
        assert status["account_id"] == account_id
        assert status["requests_remaining"] == 1
        assert "reset_time" in status
        
        # After first request
        limiter.check_rate_limit(account_id)
        status = limiter.get_status(account_id)
        assert status["requests_remaining"] == 0
    
    def test_multiple_windows(self):
        """Test behavior across multiple time windows"""
        limiter = RateLimiter(requests_per_window=2, window_seconds=0.1)
        account_id = "test_account"
        
        # Should allow multiple requests within window
        assert limiter.check_rate_limit(account_id) is True
        assert limiter.check_rate_limit(account_id) is True
        assert limiter.check_rate_limit(account_id) is False  # Exceeds limit
        
        # Wait for new window
        time.sleep(0.15)
        
        # Should reset
        assert limiter.check_rate_limit(account_id) is True
```

## Integration Tests

### API Endpoint Tests

```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from main import app

class TestAPIIntegration:
    """Test API endpoint integration and behavior"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "viral-scraper"
    
    def test_scrape_account_success(self, client):
        """Test successful account scraping request"""
        account_id = "test_account_success"
        response = client.post(f"/scrape/account/{account_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["account_id"] == account_id
        assert data["status"] == "queued"
    
    def test_scrape_account_with_parameters(self, client):
        """Test scraping request with custom parameters"""
        account_id = "test_account_params"
        payload = {
            "max_posts": 100,
            "days_back": 14,
            "min_performance_percentile": 95.0
        }
        
        response = client.post(f"/scrape/account/{account_id}", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["max_posts"] == 100
        assert data["days_back"] == 14
        assert data["min_performance_percentile"] == 95.0
    
    def test_rate_limiting_integration(self, client):
        """Test rate limiting across API calls"""
        account_id = "test_rate_limit_integration"
        
        # First request should succeed
        response1 = client.post(f"/scrape/account/{account_id}")
        assert response1.status_code == 200
        
        # Second request should be rate limited
        response2 = client.post(f"/scrape/account/{account_id}")
        assert response2.status_code == 429
        
        data = response2.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert "retry_after" in data["detail"]
    
    def test_viral_posts_endpoint(self, client):
        """Test viral posts retrieval"""
        response = client.get("/viral-posts")
        assert response.status_code == 200
        
        data = response.json()
        assert "posts" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_viral_posts_filtering(self, client):
        """Test viral posts with filters"""
        response = client.get("/viral-posts?top_1_percent_only=true&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        posts = data["posts"]
        
        # Verify filtering works (mock implementation returns data when top_1_percent_only=true)
        if posts:  # If mock data is returned
            for post in posts:
                assert post["performance_percentile"] > 99.0
    
    def test_rate_limit_status_endpoint(self, client):
        """Test rate limit status endpoint"""
        account_id = "test_rate_status"
        response = client.get(f"/rate-limit/status/{account_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == account_id
        assert "requests_remaining" in data
        assert "reset_time" in data
```

## Performance Tests

### Load Testing

```python
# tests/test_performance.py
import pytest
import asyncio
import httpx
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        base_url = "http://localhost:8080"
        
        async with httpx.AsyncClient() as client:
            # Create 10 concurrent health check requests
            tasks = []
            for i in range(10):
                task = client.get(f"{base_url}/health")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Should complete within reasonable time
            total_time = end_time - start_time
            assert total_time < 1.0  # Should complete within 1 second
    
    @pytest.mark.asyncio
    async def test_rate_limit_performance(self):
        """Test rate limiter performance under load"""
        base_url = "http://localhost:8080"
        
        async with httpx.AsyncClient() as client:
            # Test rate limiting with multiple accounts
            tasks = []
            for i in range(20):
                account_id = f"perf_test_account_{i}"
                task = client.post(f"{base_url}/scrape/account/{account_id}")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Count successful vs rate limited responses
            success_count = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
            rate_limited_count = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 429)
            
            assert success_count > 0  # Some should succeed (different accounts)
            assert success_count + rate_limited_count == 20  # All should respond
            
            # Should complete within reasonable time
            total_time = end_time - start_time
            assert total_time < 2.0  # Should complete within 2 seconds
    
    def test_memory_usage_stability(self):
        """Test memory usage remains stable over many requests"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests to rate limiter
        from rate_limiter import RateLimiter
        limiter = RateLimiter()
        
        for i in range(1000):
            account_id = f"memory_test_{i % 100}"  # Cycle through 100 accounts
            limiter.check_rate_limit(account_id)
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024
```

### Stress Testing with Locust

```python
# tests/test_stress.py
from locust import HttpUser, task, between

class ViralScraperUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize test user"""
        self.account_counter = 0
    
    @task(3)
    def health_check(self):
        """Test health endpoint (high frequency)"""
        self.client.get("/health")
    
    @task(2)
    def get_viral_posts(self):
        """Test viral posts endpoint"""
        self.client.get("/viral-posts?limit=10")
    
    @task(1)
    def scrape_account(self):
        """Test account scraping (rate limited)"""
        self.account_counter += 1
        account_id = f"stress_test_account_{self.account_counter}"
        
        response = self.client.post(f"/scrape/account/{account_id}")
        
        # Accept both success and rate limited responses
        if response.status_code not in [200, 429]:
            response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(1)
    def rate_limit_status(self):
        """Test rate limit status endpoint"""
        account_id = "stress_test_status_account"
        self.client.get(f"/rate-limit/status/{account_id}")

# Run stress test:
# locust -f tests/test_stress.py --host=http://localhost:8080
```

## End-to-End Tests

### Complete Workflow Tests

```python
# tests/test_e2e.py
import pytest
import asyncio
import httpx
import time

class TestEndToEnd:
    """End-to-end workflow tests"""
    
    @pytest.mark.asyncio
    async def test_complete_scraping_workflow(self):
        """Test complete content scraping workflow"""
        base_url = "http://localhost:8080"
        account_id = "e2e_test_account"
        
        async with httpx.AsyncClient() as client:
            # 1. Check service health
            health_response = await client.get(f"{base_url}/health")
            assert health_response.status_code == 200
            
            # 2. Check rate limit status
            rate_status_response = await client.get(f"{base_url}/rate-limit/status/{account_id}")
            assert rate_status_response.status_code == 200
            rate_status = rate_status_response.json()
            assert rate_status["requests_remaining"] > 0
            
            # 3. Trigger account scraping
            scrape_payload = {
                "max_posts": 50,
                "days_back": 7,
                "min_performance_percentile": 99.0
            }
            scrape_response = await client.post(
                f"{base_url}/scrape/account/{account_id}",
                json=scrape_payload
            )
            assert scrape_response.status_code == 200
            scrape_data = scrape_response.json()
            assert "task_id" in scrape_data
            task_id = scrape_data["task_id"]
            
            # 4. Check task status
            task_status_response = await client.get(f"{base_url}/scrape/tasks/{task_id}/status")
            assert task_status_response.status_code == 200
            task_data = task_status_response.json()
            assert task_data["task_id"] == task_id
            assert task_data["status"] in ["queued", "processing", "completed"]
            
            # 5. Verify rate limiting is now active
            second_scrape_response = await client.post(f"{base_url}/scrape/account/{account_id}")
            assert second_scrape_response.status_code == 429
            
            # 6. Get viral posts (should work regardless of scraping status)
            viral_posts_response = await client.get(f"{base_url}/viral-posts?account_id={account_id}")
            assert viral_posts_response.status_code == 200
            viral_data = viral_posts_response.json()
            assert "posts" in viral_data
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in complete workflow"""
        base_url = "http://localhost:8080"
        
        async with httpx.AsyncClient() as client:
            # Test invalid account ID (if validation exists)
            invalid_response = await client.post(f"{base_url}/scrape/account/")
            assert invalid_response.status_code == 422  # Validation error
            
            # Test invalid task ID
            invalid_task_response = await client.get(f"{base_url}/scrape/tasks/invalid-uuid/status")
            # Should return task not found or valid response with "not found" status
            assert invalid_task_response.status_code in [200, 404]
            
            # Test invalid parameters
            invalid_params = {
                "max_posts": -1,  # Invalid negative value
                "days_back": 0,   # Invalid zero value
                "min_performance_percentile": 150.0  # Invalid >100 value
            }
            invalid_param_response = await client.post(
                f"{base_url}/scrape/account/test_account",
                json=invalid_params
            )
            assert invalid_param_response.status_code == 422  # Validation error
```

## Contract Tests

### API Contract Validation

```python
# tests/test_contracts.py
import pytest
from fastapi.testclient import TestClient
from main import app
import jsonschema

class TestAPIContracts:
    """Test API contract compliance"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_endpoint_contract(self, client):
        """Test health endpoint response contract"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        
        # Define expected schema
        expected_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                "service": {"type": "string", "const": "viral-scraper"}
            },
            "required": ["status", "service"],
            "additionalProperties": False
        }
        
        # Validate response against schema
        jsonschema.validate(data, expected_schema)
    
    def test_scrape_response_contract(self, client):
        """Test scrape endpoint response contract"""
        response = client.post("/scrape/account/test_account")
        assert response.status_code == 200
        
        data = response.json()
        
        # Define expected schema
        expected_schema = {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "format": "uuid"},
                "account_id": {"type": "string"},
                "status": {"type": "string", "enum": ["queued", "processing", "completed", "failed"]},
                "max_posts": {"type": "integer", "minimum": 1},
                "days_back": {"type": "integer", "minimum": 1},
                "min_performance_percentile": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["task_id", "account_id", "status"],
            "additionalProperties": False
        }
        
        # Validate response against schema
        jsonschema.validate(data, expected_schema)
    
    def test_rate_limit_response_contract(self, client):
        """Test rate limit response contract"""
        # Trigger rate limiting
        client.post("/scrape/account/contract_test_account")
        response = client.post("/scrape/account/contract_test_account")
        
        assert response.status_code == 429
        data = response.json()
        
        # Define expected schema for rate limit error
        expected_schema = {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "retry_after": {"type": "integer", "minimum": 0}
                    },
                    "required": ["error", "retry_after"]
                }
            },
            "required": ["detail"]
        }
        
        jsonschema.validate(data, expected_schema)
    
    def test_viral_posts_response_contract(self, client):
        """Test viral posts response contract"""
        response = client.get("/viral-posts")
        assert response.status_code == 200
        
        data = response.json()
        
        # Define expected schema
        viral_post_schema = {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "account_id": {"type": "string"},
                "post_url": {"type": "string", "format": "uri"},
                "timestamp": {"type": "string", "format": "date-time"},
                "likes": {"type": "integer", "minimum": 0},
                "comments": {"type": "integer", "minimum": 0},
                "shares": {"type": "integer", "minimum": 0},
                "engagement_rate": {"type": "number", "minimum": 0, "maximum": 1},
                "performance_percentile": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["content", "account_id", "post_url", "timestamp", "likes", "comments", "shares", "engagement_rate", "performance_percentile"]
        }
        
        expected_schema = {
            "type": "object",
            "properties": {
                "posts": {
                    "type": "array",
                    "items": viral_post_schema
                },
                "total_count": {"type": "integer", "minimum": 0},
                "page": {"type": "integer", "minimum": 1},
                "page_size": {"type": "integer", "minimum": 1}
            },
            "required": ["posts", "total_count", "page", "page_size"]
        }
        
        jsonschema.validate(data, expected_schema)
```

## Test Data Management

### Fixtures and Mock Data

```python
# tests/conftest.py
import pytest
from datetime import datetime, timedelta
from typing import List
from models import ViralPost

@pytest.fixture
def sample_viral_post() -> ViralPost:
    """Create a sample viral post for testing"""
    return ViralPost(
        content="This is a test viral post about AI advancements!",
        account_id="test_account_123",
        post_url="https://threads.net/test/post/123",
        timestamp=datetime.now(),
        likes=1000,
        comments=50,
        shares=200,
        engagement_rate=0.15,
        performance_percentile=99.5
    )

@pytest.fixture
def sample_viral_posts() -> List[ViralPost]:
    """Create multiple sample viral posts"""
    posts = []
    for i in range(10):
        post = ViralPost(
            content=f"Test viral post #{i}",
            account_id=f"test_account_{i}",
            post_url=f"https://threads.net/test/post/{i}",
            timestamp=datetime.now() - timedelta(days=i),
            likes=1000 + i * 100,
            comments=50 + i * 5,
            shares=200 + i * 20,
            engagement_rate=0.10 + i * 0.01,
            performance_percentile=90.0 + i
        )
        posts.append(post)
    return posts

@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter for testing"""
    from unittest.mock import Mock
    limiter = Mock()
    limiter.check_rate_limit.return_value = True
    limiter.get_retry_after.return_value = 0
    limiter.get_status.return_value = {
        "account_id": "test",
        "requests_remaining": 1,
        "reset_time": datetime.now().isoformat()
    }
    return limiter
```

## Continuous Testing

### Test Automation

```bash
#!/bin/bash
# scripts/run-tests.sh

set -e

echo "🧪 Running Viral Scraper Test Suite"

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install -q pytest pytest-asyncio pytest-cov httpx jsonschema

# Run tests with different configurations
echo "📋 Running unit tests..."
pytest tests/test_models.py tests/test_rate_limiting.py -v

echo "🔗 Running integration tests..."
pytest tests/test_api_integration.py -v

echo "⚡ Running performance tests..."
pytest tests/test_performance.py -v -s

echo "🎯 Running end-to-end tests..."
pytest tests/test_e2e.py -v

echo "📝 Running contract tests..."
pytest tests/test_contracts.py -v

# Generate coverage report
echo "📊 Generating coverage report..."
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

echo "✅ All tests completed!"
echo "📈 Coverage report available at htmlcov/index.html"
```

### Quality Gates

```yaml
# quality-gates.yml
test_requirements:
  unit_tests:
    coverage_threshold: 90%
    pass_rate: 100%
  
  integration_tests:
    coverage_threshold: 80%
    pass_rate: 95%
  
  performance_tests:
    max_response_time: 100ms
    concurrent_users: 100
    error_rate: <1%
  
  contract_tests:
    schema_compliance: 100%
    api_compatibility: 100%

deployment_gates:
  - all_tests_pass: true
  - coverage_threshold: 85%
  - security_scan_pass: true
  - performance_baseline: maintained
```

## Troubleshooting Tests

### Common Test Issues

#### Tests Fail Due to Rate Limiting

```python
# Use unique account IDs per test
import uuid

def test_with_unique_account():
    account_id = f"test_account_{uuid.uuid4()}"
    # Test logic here
```

#### Async Test Issues

```python
# Ensure proper async test setup
import pytest

@pytest.mark.asyncio
async def test_async_function():
    # Async test logic
    pass

# Configure pytest for async
# pytest.ini
[tool:pytest]
asyncio_mode = auto
```

#### Memory Leaks in Tests

```python
# Proper cleanup in tests
import gc

def test_with_cleanup():
    # Test logic
    pass
    
    # Force garbage collection
    gc.collect()
```

---

**Last Updated**: 2025-08-03
**Test Suite Version**: v1.0.0
**Coverage Target**: 90%+
**Current Status**: 17/19 tests passing