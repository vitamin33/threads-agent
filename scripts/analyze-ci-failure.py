#!/usr/bin/env python3
"""
CI Failure Analysis Script
Analyzes GitHub Actions logs to understand fake-threads deployment issues
"""
import json
import re
import sys
from typing import Dict, List, Any
import argparse

def parse_github_logs(log_content: str) -> Dict[str, Any]:
    """Parse GitHub Actions log content and extract key information."""
    analysis = {
        'deployment_timeline': [],
        'fake_threads_events': [],
        'pod_states': [],
        'health_check_attempts': [],
        'resource_usage': {},
        'errors': [],
        'key_findings': []
    }
    
    lines = log_content.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Identify sections
        if 'FAKE-THREADS DEEP DIVE' in line:
            current_section = 'fake_threads'
        elif 'COMPREHENSIVE DEPLOYMENT ANALYSIS' in line:
            current_section = 'deployment'
        elif 'COMPREHENSIVE FAILURE ANALYSIS' in line:
            current_section = 'failure'
        
        # Parse deployment readiness issues
        if 'Deployment is not ready: default/fake-threads' in line:
            ready_match = re.search(r'(\d+) out of (\d+) expected pods are ready', line)
            if ready_match:
                analysis['deployment_timeline'].append({
                    'timestamp': extract_timestamp(line),
                    'ready_pods': int(ready_match.group(1)),
                    'expected_pods': int(ready_match.group(2)),
                    'line_number': i
                })
        
        # Parse pod events
        if current_section == 'fake_threads' and ('Warning' in line or 'Normal' in line):
            analysis['fake_threads_events'].append({
                'line': line,
                'line_number': i,
                'event_type': 'Warning' if 'Warning' in line else 'Normal'
            })
        
        # Parse health check failures
        if 'health check failed' in line.lower() or 'curl' in line and 'failed' in line:
            analysis['health_check_attempts'].append({
                'line': line,
                'line_number': i,
                'success': 'failed' not in line.lower()
            })
        
        # Parse resource constraints
        if 'CPU' in line and '%' in line:
            analysis['resource_usage']['cpu'] = line
        if 'Memory' in line and ('Mi' in line or 'Gi' in line):
            analysis['resource_usage']['memory'] = line
            
        # Collect errors
        if any(error_keyword in line.lower() for error_keyword in ['error:', 'failed:', 'timeout', 'cannot']):
            analysis['errors'].append({
                'line': line,
                'line_number': i,
                'section': current_section
            })
    
    # Generate key findings
    analysis['key_findings'] = generate_findings(analysis)
    
    return analysis

def extract_timestamp(line: str) -> str:
    """Extract timestamp from log line."""
    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
    return timestamp_match.group(0) if timestamp_match else 'unknown'

def generate_findings(analysis: Dict[str, Any]) -> List[str]:
    """Generate key findings from analysis."""
    findings = []
    
    # Timeline analysis
    if analysis['deployment_timeline']:
        timeline = analysis['deployment_timeline']
        if len(timeline) > 10:  # Stuck for a while
            findings.append(f"🕐 Deployment stuck for {len(timeline)} checks - readiness probe failing consistently")
        
        # Check if pods are consistently 0/1
        zero_ready_count = sum(1 for t in timeline if t['ready_pods'] == 0)
        if zero_ready_count == len(timeline):
            findings.append("❌ Pod never became ready - complete readiness failure")
    
    # Health check analysis
    failed_health_checks = [h for h in analysis['health_check_attempts'] if not h['success']]
    if failed_health_checks:
        findings.append(f"🏥 {len(failed_health_checks)} health check failures detected")
    
    # Error pattern analysis
    error_patterns = {}
    for error in analysis['errors']:
        error_type = classify_error(error['line'])
        error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
    
    for pattern, count in error_patterns.items():
        if count > 3:  # Recurring errors
            findings.append(f"🔄 Recurring {pattern} errors ({count} times)")
    
    # Resource analysis
    if analysis['resource_usage']:
        findings.append("📊 Resource usage data captured for analysis")
    
    return findings

def classify_error(error_line: str) -> str:
    """Classify error into categories."""
    error_line_lower = error_line.lower()
    
    if 'timeout' in error_line_lower:
        return 'timeout'
    elif 'connection' in error_line_lower and ('refused' in error_line_lower or 'failed' in error_line_lower):
        return 'connection'
    elif 'health' in error_line_lower:
        return 'health_check'
    elif 'resource' in error_line_lower or 'memory' in error_line_lower or 'cpu' in error_line_lower:
        return 'resource'
    elif 'port' in error_line_lower:
        return 'port'
    else:
        return 'general'

def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []
    
    # Based on findings
    findings = analysis['key_findings']
    
    if any('readiness probe failing' in f for f in findings):
        recommendations.extend([
            "🔧 Increase readiness probe initialDelaySeconds to 15s",
            "🔧 Increase readiness probe timeoutSeconds to 10s", 
            "🔧 Add startup probe with longer timeout (30s)"
        ])
    
    if any('health check failures' in f for f in findings):
        recommendations.extend([
            "🏥 Check if fake-threads service starts correctly in CI environment",
            "🏥 Add more detailed health endpoint logging",
            "🏥 Test health endpoint manually in CI pod"
        ])
    
    if any('connection' in error['line'].lower() for error in analysis['errors']):
        recommendations.extend([
            "🌐 Verify service port configuration (9009)",
            "🌐 Check if service binding is correct (0.0.0.0 vs localhost)"
        ])
    
    # Resource-based recommendations
    if analysis['resource_usage']:
        recommendations.append("📊 Review resource limits vs actual usage in CI")
    
    # Always recommend local testing
    recommendations.extend([
        "🧪 Run `just ci-test-local` to reproduce issue locally",
        "🔍 Compare local k3d cluster behavior vs CI cluster"
    ])
    
    return recommendations

def main():
    parser = argparse.ArgumentParser(description='Analyze CI failure logs')
    parser.add_argument('--log-file', '-f', help='Log file to analyze')
    parser.add_argument('--run-id', '-r', help='GitHub Actions run ID')
    parser.add_argument('--output', '-o', help='Output file for analysis results')
    
    args = parser.parse_args()
    
    if args.log_file:
        with open(args.log_file, 'r') as f:
            log_content = f.read()
    else:
        print("Reading from stdin...")
        log_content = sys.stdin.read()
    
    # Analyze logs
    analysis = parse_github_logs(log_content)
    
    # Generate recommendations
    recommendations = generate_recommendations(analysis)
    
    # Create full report
    report = {
        'analysis': analysis,
        'recommendations': recommendations,
        'summary': {
            'total_deployment_checks': len(analysis['deployment_timeline']),
            'total_errors': len(analysis['errors']),
            'health_check_failures': len([h for h in analysis['health_check_attempts'] if not h['success']]),
            'key_findings_count': len(analysis['key_findings'])
        }
    }
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Analysis saved to {args.output}")
    
    # Print summary to console
    print("🔍 CI FAILURE ANALYSIS SUMMARY")
    print("=" * 50)
    
    print(f"📊 Total deployment readiness checks: {report['summary']['total_deployment_checks']}")
    print(f"❌ Total errors detected: {report['summary']['total_errors']}")
    print(f"🏥 Health check failures: {report['summary']['health_check_failures']}")
    
    print("\n🎯 KEY FINDINGS:")
    for finding in analysis['key_findings']:
        print(f"  {finding}")
    
    print("\n💡 RECOMMENDATIONS:")
    for rec in recommendations:
        print(f"  {rec}")
    
    if not analysis['key_findings']:
        print("\n⚠️  No clear patterns detected. Manual log review needed.")

if __name__ == "__main__":
    main()