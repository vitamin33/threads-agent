"""
Kubernetes Service Monitor
Real-time monitoring of service health in the cluster
"""

import subprocess
import json
from typing import Dict, List, Any
from datetime import datetime
import streamlit as st

class K8sServiceMonitor:
    """Monitor Kubernetes services health"""
    
    def __init__(self):
        self.namespace = "default"
        self.key_services = [
            "achievement-collector",
            "orchestrator", 
            "celery-worker",
            "persona-runtime",
            "fake-threads",
            "viral-engine",
            "tech-doc-generator"
        ]
    
    @st.cache_data(ttl=30)  # Cache for 30 seconds
    def get_service_status(_self) -> List[Dict[str, Any]]:
        """Get real-time status of all services from Kubernetes"""
        try:
            # Get pod status
            cmd = f"kubectl get pods -n {_self.namespace} -o json"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return _self._get_fallback_status()
            
            pods_data = json.loads(result.stdout)
            service_status = {}
            
            # Process each pod
            for pod in pods_data.get('items', []):
                pod_name = pod['metadata']['name']
                
                # Find which service this pod belongs to
                service_name = None
                for service in _self.key_services:
                    if pod_name.startswith(service):
                        service_name = service
                        break
                
                if not service_name:
                    continue
                
                # Get pod status
                phase = pod['status'].get('phase', 'Unknown')
                ready = all(c['ready'] for c in pod['status'].get('containerStatuses', []))
                
                # Calculate uptime
                start_time = pod['status'].get('startTime')
                if start_time:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    uptime_hours = (datetime.now(start_dt.tzinfo) - start_dt).total_seconds() / 3600
                else:
                    uptime_hours = 0
                
                # Get resource usage (if available)
                containers = pod['status'].get('containerStatuses', [])
                restarts = sum(c.get('restartCount', 0) for c in containers)
                
                # Store best status for each service (in case of multiple pods)
                if service_name not in service_status or ready:
                    service_status[service_name] = {
                        'name': _self._format_service_name(service_name),
                        'status': '🟢 Healthy' if ready and phase == 'Running' else '🟡 Degraded' if phase == 'Running' else '🔴 Down',
                        'phase': phase,
                        'ready': ready,
                        'uptime_hours': uptime_hours,
                        'restarts': restarts,
                        'pod_name': pod_name
                    }
            
            # Convert to list and add missing services
            result = []
            for service in _self.key_services:
                if service in service_status:
                    result.append(service_status[service])
                else:
                    result.append({
                        'name': _self._format_service_name(service),
                        'status': '🔴 Not Found',
                        'phase': 'Missing',
                        'ready': False,
                        'uptime_hours': 0,
                        'restarts': 0,
                        'pod_name': 'N/A'
                    })
            
            return result
            
        except Exception as e:
            print(f"K8s monitoring error: {e}")
            return _self._get_fallback_status()
    
    def _format_service_name(self, service: str) -> str:
        """Format service name for display"""
        return service.replace('-', ' ').title()
    
    def _get_fallback_status(self) -> List[Dict[str, Any]]:
        """Return fallback status when K8s is not accessible"""
        return [
            {
                'name': self._format_service_name(service),
                'status': '⚠️ Unknown',
                'phase': 'Unknown',
                'ready': False,
                'uptime_hours': 0,
                'restarts': 0,
                'pod_name': 'N/A'
            }
            for service in self.key_services
        ]
    
    @st.cache_data(ttl=60)
    def get_cluster_metrics(_self) -> Dict[str, Any]:
        """Get cluster-wide metrics"""
        try:
            # Get node metrics
            cmd = "kubectl top nodes --no-headers"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    # Parse metrics from all nodes
                    total_cpu_millicores = 0
                    total_memory_mb = 0
                    memory_percent_sum = 0
                    
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 5:
                            # Parse CPU millicores (e.g., "87m" -> 87)
                            cpu_str = parts[1]
                            if cpu_str.endswith('m'):
                                cpu_millicores = int(cpu_str[:-1])
                                total_cpu_millicores += cpu_millicores
                            
                            # Parse memory percentage
                            mem_percent_str = parts[4].rstrip('%')
                            if mem_percent_str.isdigit():
                                memory_percent_sum += int(mem_percent_str)
                    
                    # Calculate CPU usage percentage
                    # Assume 2000m (2 cores) total for k3d cluster
                    cpu_percent = min(int((total_cpu_millicores / 2000) * 100), 100)
                    
                    # Average memory percentage
                    avg_memory_percent = memory_percent_sum // len(lines) if lines else 50
                    
                    return {
                        'cpu_usage': cpu_percent if cpu_percent > 0 else 10,  # Minimum 10% for display
                        'memory_usage': avg_memory_percent,
                        'node_count': len(lines),
                        'status': 'healthy'
                    }
            
            # Fallback to estimates based on pod count
            cmd = "kubectl get pods -n default --no-headers | wc -l"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            pod_count = int(result.stdout.strip()) if result.returncode == 0 else 10
            
            # Estimate resource usage based on pod count
            cpu_estimate = min(15 + pod_count * 3, 80)
            memory_estimate = min(30 + pod_count * 4, 85)
            
            return {
                'cpu_usage': cpu_estimate,
                'memory_usage': memory_estimate,
                'node_count': 1,
                'status': 'estimated'
            }
            
        except Exception as e:
            print(f"Cluster metrics error: {e}")
            return {
                'cpu_usage': 45,
                'memory_usage': 62,
                'node_count': 1,
                'status': 'error'
            }
    
    @st.cache_data(ttl=300)
    def get_recent_events(_self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent Kubernetes events"""
        try:
            cmd = f"kubectl get events -n {_self.namespace} --sort-by='.lastTimestamp' -o json"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return []
            
            events_data = json.loads(result.stdout)
            events = []
            
            for event in events_data.get('items', [])[-limit:]:
                # Parse event timestamp
                timestamp = event.get('lastTimestamp', event.get('firstTimestamp'))
                if timestamp:
                    event_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_ago = _self._format_time_ago(event_time)
                else:
                    time_ago = "Unknown"
                
                events.append({
                    'time': time_ago,
                    'type': event.get('type', 'Normal'),
                    'reason': event.get('reason', 'Unknown'),
                    'message': event.get('message', 'No message'),
                    'object': event.get('involvedObject', {}).get('name', 'Unknown')
                })
            
            return events[::-1]  # Reverse to show newest first
            
        except Exception as e:
            print(f"Events error: {e}")
            return []
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as relative time"""
        now = datetime.now(timestamp.tzinfo)
        delta = now - timestamp
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "Just now"

# Singleton instance
@st.cache_resource
def get_k8s_monitor() -> K8sServiceMonitor:
    """Get or create K8s monitor instance"""
    return K8sServiceMonitor()