"""
M0: Rate Limiting System
Prevents API abuse and cost overruns in development
"""

import time
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import telemetry_decorator

@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    tokens_per_hour: int = 10000
    daily_cost_limit: float = 20.0
    concurrent_limit: int = 10

class RateLimitManager:
    """Manages rate limits and prevents API abuse"""
    
    def __init__(self):
        self.usage_file = DEV_SYSTEM_ROOT / "data" / "rate_usage.json"
        self.limits = self._load_limits()
        
    def _load_limits(self) -> RateLimit:
        """Load rate limits from config"""
        try:
            import yaml
            config_file = DEV_SYSTEM_ROOT / "config" / "dev-system.yaml"
            
            with open(config_file) as f:
                config = yaml.safe_load(f)
                
            rate_config = config.get('rate_limits', {})
            
            return RateLimit(
                requests_per_minute=rate_config.get('requests_per_minute', 60),
                tokens_per_hour=rate_config.get('tokens_per_hour', 10000),
                daily_cost_limit=rate_config.get('daily_cost_limit', 20.0),
                concurrent_limit=rate_config.get('concurrent_limit', 10)
            )
        except Exception:
            return RateLimit()  # Default limits
    
    def _get_usage_data(self) -> Dict[str, Any]:
        """Get current usage data"""
        if not self.usage_file.exists():
            return {
                'daily_requests': 0,
                'hourly_tokens': 0,
                'daily_cost': 0.0,
                'concurrent_requests': 0,
                'last_reset': time.time()
            }
        
        try:
            with open(self.usage_file) as f:
                data = json.load(f)
                
            # Reset daily counters if needed
            last_reset = data.get('last_reset', 0)
            if time.time() - last_reset > 86400:  # 24 hours
                data.update({
                    'daily_requests': 0,
                    'daily_cost': 0.0,
                    'last_reset': time.time()
                })
            
            # Reset hourly token counter
            if time.time() - data.get('hourly_reset', 0) > 3600:  # 1 hour
                data.update({
                    'hourly_tokens': 0,
                    'hourly_reset': time.time()
                })
            
            return data
            
        except Exception:
            return self._get_usage_data()  # Fallback to default
    
    def _save_usage_data(self, data: Dict[str, Any]):
        """Save usage data"""
        try:
            self.usage_file.parent.mkdir(exist_ok=True)
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save usage data: {e}")
    
    @telemetry_decorator(agent_name="rate_limiter", event_type="limit_check")
    def check_rate_limit(self, 
                        operation_type: str,
                        estimated_tokens: int = 0,
                        estimated_cost: float = 0.0) -> Dict[str, Any]:
        """
        Check if operation is within rate limits
        
        Args:
            operation_type: Type of operation (api_call, model_call, etc.)
            estimated_tokens: Expected token usage
            estimated_cost: Expected cost in USD
            
        Returns:
            Dict with allowed status and details
        """
        
        usage = self._get_usage_data()
        
        # Check daily request limit
        if usage['daily_requests'] >= self.limits.requests_per_minute * 24 * 60:
            return {
                'allowed': False,
                'reason': 'Daily request limit exceeded',
                'limit_type': 'daily_requests',
                'current': usage['daily_requests'],
                'limit': self.limits.requests_per_minute * 24 * 60,
                'reset_time': usage['last_reset'] + 86400
            }
        
        # Check hourly token limit
        if usage['hourly_tokens'] + estimated_tokens > self.limits.tokens_per_hour:
            return {
                'allowed': False,
                'reason': 'Hourly token limit would be exceeded',
                'limit_type': 'hourly_tokens',
                'current': usage['hourly_tokens'],
                'estimated': estimated_tokens,
                'limit': self.limits.tokens_per_hour,
                'reset_time': usage.get('hourly_reset', 0) + 3600
            }
        
        # Check daily cost limit
        if usage['daily_cost'] + estimated_cost > self.limits.daily_cost_limit:
            return {
                'allowed': False,
                'reason': 'Daily cost limit would be exceeded',
                'limit_type': 'daily_cost',
                'current': usage['daily_cost'],
                'estimated': estimated_cost,
                'limit': self.limits.daily_cost_limit,
                'reset_time': usage['last_reset'] + 86400
            }
        
        # Check concurrent requests
        if usage['concurrent_requests'] >= self.limits.concurrent_limit:
            return {
                'allowed': False,
                'reason': 'Concurrent request limit exceeded',
                'limit_type': 'concurrent_requests',
                'current': usage['concurrent_requests'],
                'limit': self.limits.concurrent_limit,
                'suggestion': 'Wait for current requests to complete'
            }
        
        return {
            'allowed': True,
            'usage': usage,
            'limits': asdict(self.limits),
            'remaining': {
                'daily_requests': (self.limits.requests_per_minute * 24 * 60) - usage['daily_requests'],
                'hourly_tokens': self.limits.tokens_per_hour - usage['hourly_tokens'],
                'daily_cost': self.limits.daily_cost_limit - usage['daily_cost']
            }
        }
    
    def record_usage(self, 
                    tokens_used: int = 0,
                    cost_incurred: float = 0.0,
                    concurrent_change: int = 0):
        """Record actual usage after operation"""
        usage = self._get_usage_data()
        
        usage['daily_requests'] += 1
        usage['hourly_tokens'] += tokens_used
        usage['daily_cost'] += cost_incurred
        usage['concurrent_requests'] = max(0, usage['concurrent_requests'] + concurrent_change)
        
        self._save_usage_data(usage)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        usage = self._get_usage_data()
        
        return {
            'daily_requests': usage['daily_requests'],
            'hourly_tokens': usage['hourly_tokens'],
            'daily_cost': usage['daily_cost'],
            'concurrent_requests': usage['concurrent_requests'],
            'limits': asdict(self.limits),
            'utilization': {
                'requests': usage['daily_requests'] / (self.limits.requests_per_minute * 24 * 60),
                'tokens': usage['hourly_tokens'] / self.limits.tokens_per_hour,
                'cost': usage['daily_cost'] / self.limits.daily_cost_limit
            }
        }

def rate_limit_decorator(operation_type: str = "api_call"):
    """Decorator to enforce rate limits on functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = RateLimitManager()
            
            # Pre-flight check
            check_result = manager.check_rate_limit(operation_type)
            
            if not check_result['allowed']:
                raise Exception(f"Rate limit exceeded: {check_result['reason']}")
            
            # Execute function
            manager.record_usage(concurrent_change=1)
            
            try:
                result = func(*args, **kwargs)
                
                # Record actual usage if available
                if hasattr(result, 'usage'):
                    tokens = getattr(result.usage, 'total_tokens', 0)
                    manager.record_usage(tokens_used=tokens, concurrent_change=-1)
                else:
                    manager.record_usage(concurrent_change=-1)
                
                return result
                
            except Exception as e:
                manager.record_usage(concurrent_change=-1)
                raise
                
        return wrapper
    return decorator

def main():
    """CLI for rate limit management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rate limit management")
    parser.add_argument("--status", action="store_true", help="Show usage status")
    parser.add_argument("--reset", action="store_true", help="Reset usage counters")
    parser.add_argument("--test", action="store_true", help="Test rate limiting")
    
    args = parser.parse_args()
    
    manager = RateLimitManager()
    
    if args.status:
        summary = manager.get_usage_summary()
        
        print("📊 Rate Limit Status")
        print("=" * 40)
        print(f"Daily Requests: {summary['daily_requests']} ({summary['utilization']['requests']:.1%} of limit)")
        print(f"Hourly Tokens: {summary['hourly_tokens']} ({summary['utilization']['tokens']:.1%} of limit)")
        print(f"Daily Cost: ${summary['daily_cost']:.2f} ({summary['utilization']['cost']:.1%} of limit)")
        print(f"Concurrent: {summary['concurrent_requests']}/{summary['limits']['concurrent_limit']}")
        
    elif args.reset:
        # Reset usage counters
        usage_file = DEV_SYSTEM_ROOT / "data" / "rate_usage.json"
        if usage_file.exists():
            usage_file.unlink()
        print("✅ Usage counters reset")
        
    elif args.test:
        # Test rate limiting
        print("🧪 Testing rate limits...")
        
        for i in range(3):
            check = manager.check_rate_limit("test_operation", estimated_tokens=100, estimated_cost=0.01)
            
            if check['allowed']:
                print(f"✅ Test {i+1}: Allowed")
                manager.record_usage(tokens_used=100, cost_incurred=0.01)
            else:
                print(f"❌ Test {i+1}: {check['reason']}")
        
        print("📊 Final status:")
        status_result = manager.get_usage_summary()
        print(f"  Tokens: {status_result['hourly_tokens']}")
        print(f"  Cost: ${status_result['daily_cost']:.2f}")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()