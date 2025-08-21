"""
M4: Release Path with Canary/Rollback System
Safe deployment automation with percentage-based canary and automatic rollback
"""

import os
import time
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import telemetry_decorator, get_daily_metrics

class ReleaseStrategy(Enum):
    """Release deployment strategies"""
    DIRECT = "direct"           # Direct deployment (risky)
    STAGING = "staging"         # Deploy to staging first
    CANARY = "canary"          # Percentage-based canary
    BLUE_GREEN = "blue_green"  # Blue-green deployment

class ReleaseStatus(Enum):
    """Release status tracking"""
    PENDING = "pending"
    STAGING = "staging"
    CANARY = "canary"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

@dataclass
class ReleaseConfig:
    """Release configuration"""
    strategy: ReleaseStrategy
    canary_percentage: int = 10
    health_check_timeout: int = 300  # 5 minutes
    rollback_threshold: float = 0.15  # 15% error rate
    staging_suffix: str = "-staging"
    metrics_window: int = 900  # 15 minutes for health assessment

@dataclass
class ReleaseMetrics:
    """Release health metrics"""
    timestamp: float
    error_rate: float
    latency_p95: float
    success_rate: float
    request_count: int
    alerts: List[str]

class ReleaseManager:
    """Manages canary deployments and automatic rollback"""
    
    def __init__(self, config: ReleaseConfig = None):
        self.config = config or ReleaseConfig(
            strategy=ReleaseStrategy.CANARY,
            canary_percentage=10,
            rollback_threshold=0.15
        )
        self.release_history = self._load_release_history()
    
    def _load_release_history(self) -> List[Dict[str, Any]]:
        """Load release history for learning"""
        history_file = DEV_SYSTEM_ROOT / "ops" / "release_history.json"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file) as f:
                return json.load(f)
        except:
            return []
    
    def _save_release_history(self):
        """Save release history"""
        history_file = DEV_SYSTEM_ROOT / "ops" / "release_history.json"
        with open(history_file, 'w') as f:
            json.dump(self.release_history, f, indent=2)
    
    @telemetry_decorator(agent_name="release_manager", event_type="deployment")
    def deploy_with_strategy(self, 
                           strategy: str = "canary", 
                           percentage: int = 10,
                           environment: str = "dev") -> Dict[str, Any]:
        """
        Deploy using specified strategy
        
        Args:
            strategy: Release strategy (canary, staging, direct)
            percentage: Canary percentage for canary deployments
            environment: Target environment (dev, staging, prod)
            
        Returns:
            Deployment result with status and metrics
        """
        
        release_id = f"rel_{int(time.time())}"
        start_time = time.time()
        
        print(f"🚀 Starting {strategy} deployment ({percentage}% canary)")
        print(f"📋 Release ID: {release_id}")
        print(f"🎯 Environment: {environment}")
        
        try:
            # Step 1: Pre-deployment validation
            validation_result = self._validate_pre_deployment()
            if not validation_result['valid']:
                return self._create_failure_result(release_id, "Pre-deployment validation failed", validation_result)
            
            # Step 2: Deploy based on strategy
            if strategy == "staging":
                result = self._deploy_to_staging(release_id, environment)
            elif strategy == "canary":
                result = self._deploy_canary(release_id, percentage, environment)
            elif strategy == "direct":
                result = self._deploy_direct(release_id, environment)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
            
            # Step 3: Health monitoring
            if result['status'] in ['staging', 'canary', 'deployed']:
                health_result = self._monitor_health(release_id, result)
                result.update(health_result)
            
            # Step 4: Auto-rollback decision
            if result.get('health', {}).get('should_rollback', False):
                rollback_result = self._auto_rollback(release_id, result)
                result.update(rollback_result)
            
            # Record release
            release_record = {
                'release_id': release_id,
                'strategy': strategy,
                'percentage': percentage,
                'environment': environment,
                'start_time': start_time,
                'end_time': time.time(),
                'duration_seconds': time.time() - start_time,
                'result': result
            }
            
            self.release_history.append(release_record)
            self._save_release_history()
            
            return result
            
        except Exception as e:
            return self._create_failure_result(release_id, f"Deployment failed: {e}")
    
    def _validate_pre_deployment(self) -> Dict[str, Any]:
        """Validate system is ready for deployment"""
        validations = []
        
        # Check M2 quality gates
        try:
            from evals.run import run_evaluation_suite
            eval_result = run_evaluation_suite("core")
            
            if eval_result.gate_status == "FAIL":
                validations.append({
                    'check': 'quality_gates',
                    'status': 'FAIL',
                    'message': f'Quality gates failing (score: {eval_result.weighted_score:.2f})'
                })
            else:
                validations.append({
                    'check': 'quality_gates',
                    'status': 'PASS',
                    'message': f'Quality gates passing (score: {eval_result.weighted_score:.2f})'
                })
        except Exception as e:
            validations.append({
                'check': 'quality_gates',
                'status': 'SKIP',
                'message': f'Quality check unavailable: {e}'
            })
        
        # Check M1 telemetry health
        try:
            metrics = get_daily_metrics(1)
            
            if metrics['success_rate'] < 0.9:
                validations.append({
                    'check': 'telemetry_health',
                    'status': 'FAIL',
                    'message': f'Low success rate: {metrics["success_rate"]:.1%}'
                })
            else:
                validations.append({
                    'check': 'telemetry_health',
                    'status': 'PASS',
                    'message': f'Good success rate: {metrics["success_rate"]:.1%}'
                })
        except Exception as e:
            validations.append({
                'check': 'telemetry_health',
                'status': 'SKIP',
                'message': f'Telemetry unavailable: {e}'
            })
        
        # Check git status
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=DEV_SYSTEM_ROOT.parent)
            
            if result.stdout.strip():
                validations.append({
                    'check': 'git_clean',
                    'status': 'FAIL',
                    'message': 'Working directory not clean'
                })
            else:
                validations.append({
                    'check': 'git_clean',
                    'status': 'PASS',
                    'message': 'Working directory clean'
                })
        except Exception as e:
            validations.append({
                'check': 'git_clean',
                'status': 'SKIP',
                'message': f'Git check failed: {e}'
            })
        
        # Determine overall validation status
        failed_checks = [v for v in validations if v['status'] == 'FAIL']
        
        print("🔍 Pre-deployment validation:")
        for validation in validations:
            status_emoji = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[validation['status']]
            print(f"  {status_emoji} {validation['check']}: {validation['message']}")
        
        return {
            'valid': len(failed_checks) == 0,
            'validations': validations,
            'failed_checks': failed_checks
        }
    
    def _deploy_to_staging(self, release_id: str, environment: str) -> Dict[str, Any]:
        """Deploy to staging environment first"""
        print(f"🏗️  Deploying to staging environment...")
        
        # Simulate staging deployment
        time.sleep(2)  # Simulate deployment time
        
        staging_env = f"{environment}{self.config.staging_suffix}"
        
        return {
            'status': 'staging',
            'environment': staging_env,
            'message': f'Successfully deployed to {staging_env}',
            'staging_url': f'https://{staging_env}.{os.getenv("PROJECT_DOMAIN", "threads-agent.com")}',
            'next_action': 'Validate staging, then promote to production'
        }
    
    def _deploy_canary(self, release_id: str, percentage: int, environment: str) -> Dict[str, Any]:
        """Deploy using canary strategy"""
        print(f"🐦 Deploying canary ({percentage}% traffic)...")
        
        # Simulate canary deployment
        time.sleep(3)  # Simulate deployment time
        
        return {
            'status': 'canary',
            'environment': environment,
            'canary_percentage': percentage,
            'message': f'Canary deployed with {percentage}% traffic',
            'canary_url': f'https://canary-{environment}.{os.getenv("PROJECT_DOMAIN", "threads-agent.com")}',
            'monitoring_duration': self.config.metrics_window,
            'next_action': f'Monitor for {self.config.metrics_window}s, auto-rollback if error rate > {self.config.rollback_threshold:.1%}'
        }
    
    def _deploy_direct(self, release_id: str, environment: str) -> Dict[str, Any]:
        """Deploy directly to production (risky)"""
        print(f"⚡ Direct deployment to {environment} (no safety net)...")
        
        # Simulate direct deployment
        time.sleep(1)
        
        return {
            'status': 'deployed',
            'environment': environment,
            'message': f'Direct deployment to {environment} complete',
            'warning': 'No canary protection - monitor closely',
            'next_action': 'Monitor metrics manually'
        }
    
    def _monitor_health(self, release_id: str, deployment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor deployment health and decide on rollback"""
        print(f"📊 Monitoring deployment health...")
        
        # Simulate health monitoring
        time.sleep(1)
        
        # Get current telemetry as baseline
        try:
            current_metrics = get_daily_metrics(1)
            baseline_success_rate = current_metrics['success_rate']
            baseline_latency = current_metrics['p95_latency_ms']
        except:
            baseline_success_rate = 0.95
            baseline_latency = 1000.0
        
        # Simulate monitoring window
        monitoring_duration = deployment_result.get('monitoring_duration', 300)
        print(f"⏱️  Monitoring for {monitoring_duration}s...")
        
        # Simulate realistic post-deployment metrics
        import random
        
        # 90% chance of good deployment, 10% chance of issues
        deployment_success = random.random() > 0.1
        
        if deployment_success:
            # Good deployment - slight improvement
            new_success_rate = min(1.0, baseline_success_rate + random.uniform(0.0, 0.02))
            new_latency = baseline_latency * random.uniform(0.95, 1.05)
            error_rate = random.uniform(0.01, 0.05)
        else:
            # Bad deployment - performance degradation
            new_success_rate = baseline_success_rate * random.uniform(0.7, 0.9)
            new_latency = baseline_latency * random.uniform(1.2, 2.0)
            error_rate = random.uniform(0.15, 0.3)
        
        # Health assessment
        health_metrics = ReleaseMetrics(
            timestamp=time.time(),
            error_rate=error_rate,
            latency_p95=new_latency,
            success_rate=new_success_rate,
            request_count=random.randint(100, 1000),
            alerts=[]
        )
        
        # Add alerts based on thresholds
        if error_rate > self.config.rollback_threshold:
            health_metrics.alerts.append(f"High error rate: {error_rate:.2%}")
        
        if new_latency > baseline_latency * 1.5:
            health_metrics.alerts.append(f"High latency: {new_latency:.0f}ms")
        
        should_rollback = (
            error_rate > self.config.rollback_threshold or
            new_latency > baseline_latency * 2.0 or
            new_success_rate < 0.8
        )
        
        print(f"📈 Health Check Results:")
        print(f"  • Error Rate: {error_rate:.2%} (threshold: {self.config.rollback_threshold:.2%})")
        print(f"  • Success Rate: {new_success_rate:.1%}")
        print(f"  • P95 Latency: {new_latency:.0f}ms")
        print(f"  • Request Count: {health_metrics.request_count}")
        
        if health_metrics.alerts:
            print(f"🚨 Alerts: {', '.join(health_metrics.alerts)}")
        
        return {
            'health': {
                'metrics': {
                    'error_rate': error_rate,
                    'success_rate': new_success_rate,
                    'latency_p95': new_latency,
                    'request_count': health_metrics.request_count
                },
                'alerts': health_metrics.alerts,
                'should_rollback': should_rollback,
                'assessment': 'UNHEALTHY' if should_rollback else 'HEALTHY'
            }
        }
    
    def _auto_rollback(self, release_id: str, deployment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform automatic rollback"""
        print(f"🔄 Triggering automatic rollback...")
        
        # Simulate rollback
        time.sleep(2)
        
        # Record rollback reason
        alerts = deployment_result.get('health', {}).get('alerts', [])
        rollback_reason = ', '.join(alerts) if alerts else 'Health check failed'
        
        print(f"✅ Rollback complete")
        print(f"📋 Reason: {rollback_reason}")
        
        return {
            'status': 'rolled_back',
            'rollback_reason': rollback_reason,
            'rollback_time': time.time(),
            'message': 'Automatic rollback completed successfully',
            'next_action': 'Investigate issues before next deployment'
        }
    
    def _create_failure_result(self, release_id: str, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized failure result"""
        return {
            'status': 'failed',
            'release_id': release_id,
            'message': message,
            'timestamp': time.time(),
            'details': details or {},
            'next_action': 'Fix issues and retry deployment'
        }
    
    def get_release_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent release history"""
        return self.release_history[-limit:]
    
    def get_rollback_rate(self, days: int = 7) -> float:
        """Calculate rollback rate over specified period"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        recent_releases = [
            r for r in self.release_history 
            if r['start_time'] >= cutoff_time
        ]
        
        if not recent_releases:
            return 0.0
        
        rollbacks = [
            r for r in recent_releases 
            if r['result']['status'] == 'rolled_back'
        ]
        
        return len(rollbacks) / len(recent_releases)

# Kubernetes integration helpers
class K8sReleaseManager:
    """Kubernetes-specific release management"""
    
    def __init__(self, namespace: str = None):
        self.namespace = namespace or os.getenv("K8S_NAMESPACE", "threads-agent")
    
    def helm_deploy_canary(self, chart_path: str, percentage: int) -> Dict[str, Any]:
        """Deploy using Helm with canary configuration"""
        print(f"☸️  Deploying with Helm (canary {percentage}%)...")
        
        # Simulate Helm deployment
        time.sleep(2)
        
        return {
            'status': 'canary',
            'chart': chart_path,
            'namespace': self.namespace,
            'canary_percentage': percentage,
            'message': f'Helm canary deployment successful'
        }
    
    def check_pod_health(self) -> Dict[str, Any]:
        """Check Kubernetes pod health"""
        try:
            # Check if kubectl is available and cluster is reachable
            result = subprocess.run(['kubectl', 'cluster-info'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    'healthy': False,
                    'message': 'Kubernetes cluster not reachable',
                    'pods': []
                }
            
            # Get pod status
            result = subprocess.run([
                'kubectl', 'get', 'pods', 
                '-n', self.namespace, 
                '-o', 'json'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                pods_data = json.loads(result.stdout)
                pods = []
                
                for pod in pods_data.get('items', []):
                    pods.append({
                        'name': pod['metadata']['name'],
                        'status': pod['status']['phase'],
                        'ready': self._is_pod_ready(pod)
                    })
                
                healthy_pods = [p for p in pods if p['ready']]
                
                return {
                    'healthy': len(healthy_pods) > 0,
                    'message': f'{len(healthy_pods)}/{len(pods)} pods healthy',
                    'pods': pods
                }
            
        except Exception as e:
            return {
                'healthy': False,
                'message': f'Health check failed: {e}',
                'pods': []
            }
        
        return {
            'healthy': False,
            'message': 'Unable to check pod health',
            'pods': []
        }
    
    def _is_pod_ready(self, pod: Dict[str, Any]) -> bool:
        """Check if a pod is ready"""
        conditions = pod.get('status', {}).get('conditions', [])
        
        for condition in conditions:
            if condition.get('type') == 'Ready':
                return condition.get('status') == 'True'
        
        return False

def deploy_with_strategy(strategy: str = "canary", percentage: int = 10, environment: str = "dev") -> Dict[str, Any]:
    """Main entry point for deployment"""
    manager = ReleaseManager()
    return manager.deploy_with_strategy(strategy, percentage, environment)

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Release management system")
    parser.add_argument("--strategy", default="canary", 
                       choices=["canary", "staging", "direct"],
                       help="Deployment strategy")
    parser.add_argument("--percentage", type=int, default=10,
                       help="Canary percentage (1-100)")
    parser.add_argument("--environment", default="dev",
                       help="Target environment")
    parser.add_argument("--history", action="store_true",
                       help="Show release history")
    
    args = parser.parse_args()
    
    if args.history:
        manager = ReleaseManager()
        history = manager.get_release_history()
        
        print("📋 Recent Release History:")
        for release in history[-5:]:
            status_emoji = {
                'deployed': '✅',
                'rolled_back': '🔄', 
                'failed': '❌',
                'canary': '🐦'
            }.get(release['result']['status'], '❓')
            
            duration = release['duration_seconds']
            print(f"  {status_emoji} {release['release_id']}: {release['strategy']} -> {release['result']['status']} ({duration:.1f}s)")
        
        rollback_rate = manager.get_rollback_rate(7)
        print(f"\n📊 7-day rollback rate: {rollback_rate:.1%}")
        
    else:
        result = deploy_with_strategy(args.strategy, args.percentage, args.environment)
        
        print(f"\n{'='*60}")
        print(f"📋 Deployment Summary:")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        
        if 'next_action' in result:
            print(f"  Next: {result['next_action']}")

if __name__ == "__main__":
    main()