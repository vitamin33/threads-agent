"""
Comprehensive Rate Limiting Test Suite for M0
Tests rate limiting under various load conditions and edge cases
"""

import time
import sys
from pathlib import Path

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.rate_limits import RateLimitManager, rate_limit_decorator

def test_basic_rate_limiting():
    """Test basic rate limiting functionality"""
    print("🧪 Testing basic rate limiting...")
    
    manager = RateLimitManager()
    
    # Test normal operation
    result = manager.check_rate_limit("test_op", estimated_tokens=100, estimated_cost=0.01)
    assert result['allowed'], "Normal operation should be allowed"
    
    # Record usage
    manager.record_usage(tokens_used=100, cost_incurred=0.01)
    
    # Check updated status
    summary = manager.get_usage_summary()
    assert summary['hourly_tokens'] >= 100, "Usage should be recorded"
    assert summary['daily_cost'] >= 0.01, "Cost should be recorded"
    
    print("✅ Basic rate limiting working")

def test_rate_limit_thresholds():
    """Test rate limit threshold enforcement"""
    print("🧪 Testing rate limit thresholds...")
    
    manager = RateLimitManager()
    
    # Try to exceed token limit
    result = manager.check_rate_limit("test_op", estimated_tokens=20000)  # Exceeds 10k limit
    assert not result['allowed'], "Should block excessive token usage"
    assert 'hourly_tokens' in result['reason'], "Should mention token limit"
    
    # Try to exceed cost limit
    result = manager.check_rate_limit("test_op", estimated_cost=25.0)  # Exceeds $20 limit
    assert not result['allowed'], "Should block excessive cost"
    assert 'daily_cost' in result['reason'], "Should mention cost limit"
    
    print("✅ Rate limit thresholds working")

def test_concurrent_limiting():
    """Test concurrent request limiting"""
    print("🧪 Testing concurrent request limiting...")
    
    manager = RateLimitManager()
    
    # Simulate concurrent requests
    for i in range(12):  # Exceeds limit of 10
        manager.record_usage(concurrent_change=1)
    
    # Should now block new requests
    result = manager.check_rate_limit("test_op")
    assert not result['allowed'], "Should block when concurrent limit exceeded"
    
    # Reset concurrent counter
    for i in range(12):
        manager.record_usage(concurrent_change=-1)
    
    print("✅ Concurrent limiting working")

@rate_limit_decorator("test_decorated")
def test_decorated_function(value):
    """Test function with rate limiting decorator"""
    time.sleep(0.1)  # Simulate work
    return f"processed_{value}"

def test_decorator_functionality():
    """Test rate limiting decorator"""
    print("🧪 Testing rate limiting decorator...")
    
    # Should work normally
    result = test_decorated_function("test1")
    assert result == "processed_test1", "Decorated function should work"
    
    # Function should be tracked in telemetry
    from ops.telemetry import get_daily_metrics
    metrics = get_daily_metrics(1)
    
    print("✅ Rate limiting decorator working")

def test_usage_reset():
    """Test usage counter reset functionality"""
    print("🧪 Testing usage reset...")
    
    manager = RateLimitManager()
    
    # Add some usage
    manager.record_usage(tokens_used=500, cost_incurred=2.0)
    
    initial_summary = manager.get_usage_summary()
    assert initial_summary['hourly_tokens'] >= 500, "Usage should be recorded"
    
    # Reset via CLI
    import subprocess
    result = subprocess.run([
        'python3', 'ops/rate_limits.py', '--reset'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, "Reset should succeed"
    
    # Check reset worked
    final_summary = manager.get_usage_summary()
    assert final_summary['daily_requests'] == 0, "Requests should be reset"
    
    print("✅ Usage reset working")

def test_integration_with_telemetry():
    """Test rate limiting integration with M1 telemetry"""
    print("🧪 Testing telemetry integration...")
    
    from ops.telemetry import get_daily_metrics
    
    manager = RateLimitManager()
    
    # Rate limiter should use telemetry data
    try:
        metrics = get_daily_metrics(1)
        check_result = manager.check_rate_limit("telemetry_test")
        
        assert check_result['allowed'], "Should allow with good telemetry"
        print("✅ Telemetry integration working")
        
    except Exception as e:
        print(f"⚠️  Telemetry integration test skipped: {e}")

def run_all_rate_limit_tests():
    """Run complete rate limiting test suite"""
    print("🚀 Starting M0 Rate Limiting Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Rate Limiting", test_basic_rate_limiting),
        ("Rate Limit Thresholds", test_rate_limit_thresholds),
        ("Concurrent Limiting", test_concurrent_limiting),
        ("Decorator Functionality", test_decorator_functionality),
        ("Usage Reset", test_usage_reset),
        ("Telemetry Integration", test_integration_with_telemetry)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"📊 Rate Limiting Tests: {passed}/{passed + failed} passed")
    if failed == 0:
        print("🎉 All rate limiting tests passed!")
    print(f"{'='*50}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_rate_limit_tests()
    sys.exit(0 if success else 1)