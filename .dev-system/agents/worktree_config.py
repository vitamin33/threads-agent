"""
Enhanced Worktree Configuration for 4-Agent Development
Agent-specific settings and coordination
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

class WorktreeConfig:
    """Configuration manager for individual worktree agents"""
    
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or os.getenv('AGENT_ID', 'main-dev')
        self.config_file = Path.cwd() / '.agent-config.json'
        
    def get_agent_services(self) -> Dict[str, list]:
        """Get services owned by each agent"""
        return {
            'a1': ['orchestrator', 'celery_worker', 'performance_monitor', 'mlflow_service'],
            'a2': ['persona_runtime', 'viral_engine', 'rag_pipeline', 'vllm_service'],
            'a3': ['achievement_collector', 'dashboard_api', 'tech_doc_generator'],
            'a4': ['revenue', 'finops_engine', 'threads_adaptor', 'fake_threads']
        }
    
    def get_my_services(self) -> list:
        """Get services for current agent"""
        agent_services = self.get_agent_services()
        return agent_services.get(self.agent_id, [])
    
    def get_agent_focus(self) -> Dict[str, str]:
        """Get focus area for each agent"""
        return {
            'a1': 'Infrastructure & Platform Engineering',
            'a2': 'AI/ML & Content Generation',
            'a3': 'Data & Analytics', 
            'a4': 'Revenue & Business Logic'
        }
    
    def get_deployment_order(self) -> list:
        """Get optimal deployment sequence"""
        return [
            {'agent': 'a1', 'reason': 'Infrastructure foundation - others depend on this'},
            {'agent': 'a2', 'reason': 'AI/ML services - core functionality'}, 
            {'agent': 'a3', 'reason': 'Analytics - depends on data from A1+A2'},
            {'agent': 'a4', 'reason': 'Business logic - depends on all others'}
        ]
    
    def get_cross_dependencies(self) -> Dict[str, list]:
        """Get cross-agent dependencies"""
        return {
            'a1': [],  # No dependencies
            'a2': ['a1'],  # AI depends on orchestrator  
            'a3': ['a1', 'a2'],  # Analytics depends on infra + AI
            'a4': ['a1', 'a2', 'a3']  # Business depends on everything
        }
    
    def generate_agent_brief(self) -> str:
        """Generate agent-specific morning brief"""
        my_services = self.get_my_services()
        focus = self.get_agent_focus().get(self.agent_id, 'General Development')
        
        brief = f"""
🤖 Agent {self.agent_id.upper()} Daily Brief
Focus: {focus}
Services: {', '.join(my_services)}

🎯 Today's Agent-Specific Priorities:
  1. Run: just eval-agents "{' '.join(my_services[:3])}"
  2. Check: Agent-specific quality trends
  3. Focus: {focus} improvements

⚡ Quick Commands:
  • just eval-agents "{' '.join(my_services[:2])}"  # Test your services
  • just prompt-list-agent {my_services[0] if my_services else 'core'}  # Your prompts
  • just knowledge-search "{focus.split()[0].lower()}"  # Relevant knowledge
"""
        return brief

def main():
    """CLI for worktree configuration"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-brief", action="store_true", help="Show agent-specific brief")
    parser.add_argument("--my-services", action="store_true", help="Show my services")
    parser.add_argument("--agent-id", help="Override agent ID")
    
    args = parser.parse_args()
    
    config = WorktreeConfig(args.agent_id)
    
    if args.agent_brief:
        print(config.generate_agent_brief())
    elif args.my_services:
        services = config.get_my_services()
        print(f"🤖 Agent {config.agent_id} Services:")
        for service in services:
            print(f"  • {service}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()