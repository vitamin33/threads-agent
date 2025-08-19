"""
M7: Multi-Agent Evaluation Runner
Runs quality gates across all agents and generates comprehensive reports
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from evals.run import EvaluationRunner, SuiteResult
from ops.telemetry import telemetry_decorator

@dataclass
class MultiAgentResult:
    """Results from running multiple agent evaluations"""
    timestamp: str
    total_agents: int
    passed_agents: int
    failed_agents: int
    overall_score: float
    agent_results: Dict[str, SuiteResult]
    summary: Dict[str, Any]

class MultiAgentEvaluationRunner:
    """Runs evaluations across multiple agents"""
    
    def __init__(self):
        self.suites_dir = DEV_SYSTEM_ROOT / "evals" / "suites"
        self.reports_dir = DEV_SYSTEM_ROOT / "evals" / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def discover_agent_suites(self) -> List[str]:
        """Discover all available agent evaluation suites"""
        suites = []
        
        for suite_file in self.suites_dir.glob("*.yaml"):
            suite_name = suite_file.stem
            suites.append(suite_name)
        
        return sorted(suites)
    
    @telemetry_decorator(agent_name="multi_agent_runner", event_type="multi_eval")
    def run_all_agents(self, agents: List[str] = None) -> MultiAgentResult:
        """Run evaluations for all specified agents"""
        
        if agents is None:
            agents = self.discover_agent_suites()
        
        print(f"🧪 Running Multi-Agent Quality Evaluation")
        print(f"📋 Agents: {', '.join(agents)}")
        print(f"🎯 Total Suites: {len(agents)}")
        print("=" * 60)
        
        agent_results = {}
        start_time = datetime.now()
        
        for agent in agents:
            print(f"\n🔄 Evaluating {agent}...")
            
            try:
                suite_path = self.suites_dir / f"{agent}.yaml"
                
                if not suite_path.exists():
                    print(f"⚠️  Suite not found: {agent}")
                    continue
                
                runner = EvaluationRunner(suite_path)
                result = runner.run_suite()
                agent_results[agent] = result
                
                # Print agent summary
                status_emoji = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️"}[result.gate_status]
                print(f"  {status_emoji} {agent}: {result.weighted_score:.2f} ({result.passed_tests}/{result.total_tests} tests)")
                
            except Exception as e:
                print(f"  ❌ {agent}: Evaluation failed - {e}")
                # Create failed result for tracking
                agent_results[agent] = self._create_failed_result(agent, str(e))
        
        # Calculate overall metrics
        total_time = (datetime.now() - start_time).total_seconds()
        multi_result = self._calculate_multi_agent_metrics(agent_results, total_time)
        
        # Print summary
        self._print_multi_agent_summary(multi_result)
        
        # Save results
        self._save_multi_agent_results(multi_result)
        
        return multi_result
    
    def _calculate_multi_agent_metrics(self, agent_results: Dict[str, SuiteResult], total_time: float) -> MultiAgentResult:
        """Calculate metrics across all agent results"""
        
        if not agent_results:
            return MultiAgentResult(
                timestamp=datetime.now().isoformat(),
                total_agents=0,
                passed_agents=0,
                failed_agents=0,
                overall_score=0.0,
                agent_results={},
                summary={}
            )
        
        # Count pass/fail
        passed_agents = sum(1 for r in agent_results.values() if r.gate_status == "PASS")
        failed_agents = len(agent_results) - passed_agents
        
        # Calculate weighted overall score
        total_weight = 0
        weighted_sum = 0
        
        for agent, result in agent_results.items():
            # Weight by number of tests (more comprehensive suites get higher weight)
            weight = result.total_tests
            weighted_sum += result.weighted_score * weight
            total_weight += weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Generate summary statistics
        summary = {
            'execution_time_seconds': total_time,
            'best_agent': max(agent_results.items(), key=lambda x: x[1].weighted_score)[0] if agent_results else None,
            'worst_agent': min(agent_results.items(), key=lambda x: x[1].weighted_score)[0] if agent_results else None,
            'avg_score': sum(r.weighted_score for r in agent_results.values()) / len(agent_results),
            'total_tests': sum(r.total_tests for r in agent_results.values()),
            'total_passed_tests': sum(r.passed_tests for r in agent_results.values()),
            'total_cost': sum(r.total_cost_usd for r in agent_results.values()),
            'agents_needing_attention': [
                agent for agent, result in agent_results.items() 
                if result.weighted_score < 0.75
            ]
        }
        
        return MultiAgentResult(
            timestamp=datetime.now().isoformat(),
            total_agents=len(agent_results),
            passed_agents=passed_agents,
            failed_agents=failed_agents,
            overall_score=overall_score,
            agent_results=agent_results,
            summary=summary
        )
    
    def _create_failed_result(self, agent: str, error: str) -> SuiteResult:
        """Create a failed result for agents that couldn't be evaluated"""
        from evals.run import SuiteResult
        
        return SuiteResult(
            suite_name=agent,
            timestamp=datetime.now().isoformat(),
            total_tests=0,
            passed_tests=0,
            failed_tests=1,
            success_rate=0.0,
            avg_latency_ms=0.0,
            total_cost_usd=0.0,
            weighted_score=0.0,
            gate_status="FAIL",
            test_results=[]
        )
    
    def _print_multi_agent_summary(self, result: MultiAgentResult):
        """Print comprehensive multi-agent summary"""
        print(f"\n{'='*70}")
        print(f"📊 Multi-Agent Quality Summary")
        print(f"{'='*70}")
        print(f"Agents Evaluated:    {result.total_agents}")
        print(f"Passed:             {result.passed_agents} ({result.passed_agents/result.total_agents:.1%})")
        print(f"Failed:             {result.failed_agents} ({result.failed_agents/result.total_agents:.1%})")
        print(f"Overall Score:      {result.overall_score:.2f}")
        print(f"Execution Time:     {result.summary['execution_time_seconds']:.1f}s")
        print(f"Total Tests:        {result.summary['total_passed_tests']}/{result.summary['total_tests']}")
        print(f"Total Cost:         ${result.summary['total_cost']:.3f}")
        
        if result.summary['best_agent']:
            best_score = result.agent_results[result.summary['best_agent']].weighted_score
            print(f"Best Agent:         {result.summary['best_agent']} ({best_score:.2f})")
        
        if result.summary['worst_agent']:
            worst_score = result.agent_results[result.summary['worst_agent']].weighted_score
            print(f"Needs Attention:    {result.summary['worst_agent']} ({worst_score:.2f})")
        
        # Agents needing attention
        if result.summary['agents_needing_attention']:
            print(f"\n🚨 Agents Below 0.75 Quality Threshold:")
            for agent in result.summary['agents_needing_attention']:
                score = result.agent_results[agent].weighted_score
                print(f"  • {agent}: {score:.2f}")
        
        # Overall assessment
        if result.overall_score >= 0.85:
            print(f"\n✅ EXCELLENT: Multi-agent system quality is high")
        elif result.overall_score >= 0.75:
            print(f"\n✅ GOOD: Multi-agent system quality is acceptable")
        elif result.overall_score >= 0.65:
            print(f"\n⚠️  FAIR: Some agents need improvement")
        else:
            print(f"\n❌ POOR: Multi-agent system needs significant work")
    
    def _save_multi_agent_results(self, result: MultiAgentResult):
        """Save multi-agent results for historical tracking"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"multi_agent_{timestamp}.json"
        
        # Convert to dict for JSON serialization
        result_dict = asdict(result)
        
        with open(report_file, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        print(f"💾 Multi-agent results saved: {report_file}")

def run_all_agents(agents: List[str] = None) -> MultiAgentResult:
    """Main entry point for multi-agent evaluation"""
    runner = MultiAgentEvaluationRunner()
    return runner.run_all_agents(agents)

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-agent quality evaluation")
    parser.add_argument("--agents", nargs="+", help="Specific agents to evaluate")
    parser.add_argument("--list", action="store_true", help="List available agent suites")
    
    args = parser.parse_args()
    
    runner = MultiAgentEvaluationRunner()
    
    if args.list:
        agents = runner.discover_agent_suites()
        print("📋 Available Agent Suites:")
        for agent in agents:
            suite_path = runner.suites_dir / f"{agent}.yaml"
            print(f"  • {agent} ({suite_path})")
        return
    
    try:
        result = run_all_agents(args.agents)
        
        # Exit with appropriate code for CI
        if result.failed_agents > result.total_agents * 0.3:  # More than 30% failed
            print("\n❌ Too many agent failures for production deployment")
            sys.exit(1)
        elif result.overall_score < 0.70:
            print("\n❌ Overall quality too low for production deployment")
            sys.exit(1)
        else:
            print("\n✅ Multi-agent quality acceptable for deployment")
            
    except Exception as e:
        print(f"❌ Multi-agent evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()