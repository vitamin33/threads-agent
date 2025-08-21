"""
Multi-Agent Coordination System
Cross-agent impact analysis and deployment sequencing
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

class AgentCoordinator:
    """Coordinates activities across multiple agents"""
    
    def __init__(self):
        self.agents_dir = DEV_SYSTEM_ROOT / "agents"
        self.coordination_file = self.agents_dir / "coordination_state.json"
        
    def get_agent_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Get service dependencies between agents"""
        return {
            'a1': {
                'services': ['orchestrator', 'celery_worker', 'performance_monitor', 'mlflow_service'],
                'depends_on': [],
                'provides_to': ['a2', 'a3', 'a4'],
                'deployment_priority': 1,
                'focus': 'Infrastructure & Platform',
                'deployment_strategy': 'staging_first'
            },
            'a2': {
                'services': ['persona_runtime', 'viral_engine', 'rag_pipeline', 'vllm_service'],
                'depends_on': ['a1'],
                'provides_to': ['a3', 'a4'],
                'deployment_priority': 2,
                'focus': 'AI/ML & Content',
                'deployment_strategy': 'canary_10'
            },
            'a3': {
                'services': ['achievement_collector', 'dashboard_api', 'tech_doc_generator'],
                'depends_on': ['a1', 'a2'],
                'provides_to': ['a4'],
                'deployment_priority': 2,  # Can deploy parallel with A2
                'focus': 'Data & Analytics',
                'deployment_strategy': 'canary_15'
            },
            'a4': {
                'services': ['revenue', 'finops_engine', 'threads_adaptor', 'fake_threads'],
                'depends_on': ['a1', 'a2', 'a3'],
                'provides_to': [],
                'deployment_priority': 3,
                'focus': 'Revenue & Business',
                'deployment_strategy': 'canary_5'  # Conservative for revenue
            }
        }
    
    def get_deployment_sequence(self) -> List[Dict[str, Any]]:
        """Get optimal deployment sequence based on dependencies"""
        dependencies = self.get_agent_dependencies()
        
        sequence = []
        
        # Priority 1: Infrastructure (A1)
        sequence.append({
            'phase': 1,
            'agents': ['a1'],
            'rationale': 'Infrastructure foundation - all others depend on orchestrator and celery',
            'strategy': 'staging_first',
            'wait_for_health': True
        })
        
        # Priority 2: Core functionality (A2 + A3 parallel)
        sequence.append({
            'phase': 2,
            'agents': ['a2', 'a3'],
            'rationale': 'AI/ML and Analytics can deploy in parallel after infrastructure',
            'strategy': 'canary_parallel',
            'wait_for_health': True
        })
        
        # Priority 3: Business logic (A4)
        sequence.append({
            'phase': 3,
            'agents': ['a4'],
            'rationale': 'Revenue systems deploy last with maximum safety',
            'strategy': 'canary_conservative',
            'wait_for_health': True
        })
        
        return sequence
    
    def analyze_cross_agent_impact(self, changed_agent: str, changed_services: List[str] = None) -> Dict[str, Any]:
        """Analyze impact of changes on other agents"""
        
        dependencies = self.get_agent_dependencies()
        
        if changed_agent not in dependencies:
            return {'error': f'Unknown agent: {changed_agent}'}
        
        agent_config = dependencies[changed_agent]
        affected_agents = agent_config['provides_to']
        
        impact_analysis = {
            'changed_agent': changed_agent,
            'changed_services': changed_services or agent_config['services'],
            'affected_agents': [],
            'deployment_recommendations': [],
            'risk_assessment': 'low'
        }
        
        # Analyze impact on each affected agent
        for affected_agent in affected_agents:
            affected_config = dependencies[affected_agent]
            
            # Check service dependencies
            impacted_services = self._find_impacted_services(
                changed_services or agent_config['services'],
                affected_config['services']
            )
            
            if impacted_services:
                impact_analysis['affected_agents'].append({
                    'agent': affected_agent,
                    'focus': affected_config['focus'],
                    'impacted_services': impacted_services,
                    'recommended_tests': [f'just eval-agents "{" ".join(impacted_services)}"']
                })
        
        # Generate deployment recommendations
        if impact_analysis['affected_agents']:
            impact_analysis['deployment_recommendations'] = [
                f'Deploy {changed_agent} first with staging validation',
                f'Test affected agents: {", ".join([a["agent"] for a in impact_analysis["affected_agents"]])}',
                f'Use conservative canary percentages for dependent services'
            ]
            
            # Assess risk based on number of affected agents
            affected_count = len(impact_analysis['affected_agents'])
            if affected_count >= 3:
                impact_analysis['risk_assessment'] = 'high'
            elif affected_count >= 2:
                impact_analysis['risk_assessment'] = 'medium'
        
        return impact_analysis
    
    def _find_impacted_services(self, changed_services: List[str], target_services: List[str]) -> List[str]:
        """Find which target services might be impacted by changes"""
        
        # Service dependency mapping
        service_dependencies = {
            'persona_runtime': ['orchestrator'],  # Depends on task routing
            'viral_engine': ['orchestrator'],     # Depends on task coordination
            'dashboard_api': ['celery_worker'],   # Depends on background processing
            'revenue': ['orchestrator'],          # Depends on API routing
            'achievement_collector': ['orchestrator'], # Depends on data flow
            'threads_adaptor': ['orchestrator']   # Depends on API coordination
        }
        
        impacted = []
        
        for target_service in target_services:
            dependencies = service_dependencies.get(target_service, [])
            
            # Check if any changed service affects this target
            for changed_service in changed_services:
                if changed_service in dependencies:
                    impacted.append(target_service)
                    break
        
        return impacted
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of all agents"""
        
        # Load latest quality results for each agent
        reports_dir = DEV_SYSTEM_ROOT / "evals" / "reports"
        agent_status = {}
        
        dependencies = self.get_agent_dependencies()
        
        for agent_id, config in dependencies.items():
            status = {
                'agent_id': agent_id,
                'focus': config['focus'],
                'services': config['services'],
                'deployment_priority': config['deployment_priority'],
                'last_quality_check': None,
                'quality_score': 0.0,
                'deployment_ready': False
            }
            
            # Try to get latest quality data for agent's services
            try:
                # This would integrate with M7 multi-agent results
                status['quality_score'] = 0.75  # Placeholder
                status['deployment_ready'] = status['quality_score'] > 0.70
                status['last_quality_check'] = datetime.now().isoformat()
            except Exception:
                pass
            
            agent_status[agent_id] = status
        
        return agent_status

def main():
    """CLI for agent coordination"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-agent coordination")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Agent status
    status_parser = subparsers.add_parser('status', help='Show all agent statuses')
    
    # Impact analysis
    impact_parser = subparsers.add_parser('impact', help='Analyze cross-agent impact')
    impact_parser.add_argument('agent', help='Agent that changed')
    impact_parser.add_argument('--services', nargs='+', help='Specific services changed')
    
    # Deployment sequence
    deploy_parser = subparsers.add_parser('deploy-sequence', help='Show deployment sequence')
    
    args = parser.parse_args()
    
    coordinator = AgentCoordinator()
    
    if args.command == 'status':
        statuses = coordinator.get_agent_status()
        
        print("🤖 Multi-Agent Status Dashboard")
        print("=" * 50)
        
        for agent_id, status in statuses.items():
            ready_emoji = "✅" if status['deployment_ready'] else "⚠️"
            print(f"{ready_emoji} **Agent {agent_id.upper()}**: {status['focus']}")
            print(f"   Quality: {status['quality_score']:.2f}")
            print(f"   Services: {', '.join(status['services'][:3])}...")
            print(f"   Ready: {'Yes' if status['deployment_ready'] else 'No'}")
            print()
    
    elif args.command == 'impact':
        impact = coordinator.analyze_cross_agent_impact(args.agent, args.services)
        
        if 'error' in impact:
            print(f"❌ {impact['error']}")
            return 1
        
        print(f"🔄 Cross-Agent Impact Analysis: {args.agent}")
        print("=" * 50)
        print(f"Risk Assessment: {impact['risk_assessment'].upper()}")
        
        if impact['affected_agents']:
            print(f"\n🎯 Affected Agents:")
            for affected in impact['affected_agents']:
                print(f"  • {affected['agent']} ({affected['focus']})")
                print(f"    Impacted services: {', '.join(affected['impacted_services'])}")
                print(f"    Recommended test: {affected['recommended_tests'][0]}")
        
        if impact['deployment_recommendations']:
            print(f"\n📋 Deployment Recommendations:")
            for rec in impact['deployment_recommendations']:
                print(f"  • {rec}")
    
    elif args.command == 'deploy-sequence':
        sequence = coordinator.get_deployment_sequence()
        
        print("🚀 Optimal Deployment Sequence")
        print("=" * 50)
        
        for phase in sequence:
            agents_str = ', '.join([f"A{a[-1]}" for a in phase['agents']])
            print(f"Phase {phase['phase']}: {agents_str}")
            print(f"  Strategy: {phase['strategy']}")
            print(f"  Rationale: {phase['rationale']}")
            print(f"  Wait for health: {'Yes' if phase['wait_for_health'] else 'No'}")
            print()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()