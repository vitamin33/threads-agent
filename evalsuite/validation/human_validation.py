#!/usr/bin/env python3
"""
Human Validation System - Manual Spot Checks and Agreement Analysis

Implements human validation framework:
1. Random sampling of judgments for human review
2. Judge vs human agreement calculation
3. Rubric tightening recommendations based on agreement rates
"""

import csv
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class HumanJudgment:
    """Human judgment for comparison pair."""
    comparison_id: str
    prompt: str
    output_a: str
    output_b: str
    model_a: str
    model_b: str
    human_winner: str  # 'A', 'B', 'tie'
    human_reasons: str
    human_criteria_scores: Dict[str, int]  # 1-5 scale
    confidence_level: str  # 'high', 'medium', 'low'
    time_spent_seconds: Optional[int] = None
    annotator_id: Optional[str] = None


@dataclass
class AgreementAnalysis:
    """Analysis of judge vs human agreement."""
    total_comparisons: int
    exact_agreement: int
    agreement_rate: float
    criteria_agreement: Dict[str, float]
    disagreement_patterns: List[str]
    rubric_recommendations: List[str]
    judge_reliability_assessment: str


class HumanValidationSystem:
    """
    System for human validation and judge agreement analysis.
    
    Creates CSV files for human annotation and analyzes agreement
    between automated judge and human evaluations.
    """
    
    def __init__(self, output_dir: str = "validation"):
        """Initialize human validation system."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_human_annotation_csv(
        self,
        judgments: List[Dict[str, Any]],
        n_samples: int = 10,
        seed: int = 42
    ) -> str:
        """
        Create CSV file for human annotation of random judgment pairs.
        
        Args:
            judgments: List of automated judgments to sample from
            n_samples: Number of random pairs to sample
            seed: Random seed for reproducible sampling
            
        Returns:
            Path to created CSV file
        """
        
        random.seed(seed)
        
        # Sample random judgments
        if len(judgments) < n_samples:
            n_samples = len(judgments)
            
        sampled_judgments = random.sample(judgments, n_samples)
        
        # Create annotation CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.output_dir / f"human_annotation_{timestamp}.csv"
        
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = [
                'comparison_id', 'prompt', 'output_a', 'output_b',
                'model_a', 'model_b', 'llm_judge_winner', 'llm_judge_reasons',
                'human_winner', 'human_reasons', 'clarity_score', 
                'relevance_score', 'tone_score', 'factuality_score',
                'confidence_level', 'time_spent_seconds', 'annotator_id'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, judgment in enumerate(sampled_judgments):
                row = {
                    'comparison_id': f"human_val_{i+1:02d}",
                    'prompt': judgment.get('prompt', ''),
                    'output_a': judgment.get('output_a', ''),
                    'output_b': judgment.get('output_b', ''),
                    'model_a': judgment.get('model_a', ''),
                    'model_b': judgment.get('model_b', ''),
                    'llm_judge_winner': judgment.get('judgment', {}).get('winner', ''),
                    'llm_judge_reasons': judgment.get('judgment', {}).get('reasons', ''),
                    # Human fields to be filled
                    'human_winner': '',
                    'human_reasons': '',
                    'clarity_score': '',
                    'relevance_score': '',
                    'tone_score': '',
                    'factuality_score': '',
                    'confidence_level': '',
                    'time_spent_seconds': '',
                    'annotator_id': ''
                }
                
                writer.writerow(row)
        
        # Create instruction file
        self._create_annotation_instructions(csv_path.parent)
        
        print(f"📝 Human annotation CSV created: {csv_path}")
        print(f"📋 Instructions created: {csv_path.parent}/annotation_instructions.md")
        print(f"🎯 Please annotate {n_samples} pairs and return CSV for analysis")
        
        return str(csv_path)
    
    def _create_annotation_instructions(self, output_dir: Path):
        """Create detailed instructions for human annotators."""
        
        instructions_path = output_dir / "annotation_instructions.md"
        
        instructions = """# Human Validation Instructions

## Overview
You are validating automated LLM judgments by providing human evaluation of content pairs.

## Task
For each comparison pair, determine which output (A or B) is better for LinkedIn business content, or if they are tied.

## Evaluation Criteria
Rate each criterion on a scale of 1-5:

### 1. Clarity (1-5)
- 5: Crystal clear, easy to understand
- 4: Clear with minor ambiguity
- 3: Generally clear
- 2: Somewhat confusing
- 1: Unclear or confusing

### 2. Relevance (1-5)
- 5: Perfectly addresses the prompt
- 4: Good relevance with minor gaps
- 3: Generally relevant
- 2: Somewhat relevant
- 1: Irrelevant or off-topic

### 3. Tone (1-5)
- 5: Perfect professional LinkedIn tone
- 4: Good professional tone
- 3: Acceptable business tone
- 2: Slightly inappropriate tone
- 1: Inappropriate or unprofessional

### 4. Factuality (1-5)
- 5: All claims appear accurate/plausible
- 4: Mostly accurate with minor concerns
- 3: Generally plausible
- 2: Some questionable claims
- 1: Implausible or clearly false claims

## Instructions
1. Read both outputs carefully
2. Score each criterion 1-5 for both outputs
3. Choose winner: 'A', 'B', or 'tie'
4. Provide brief reasons for your decision
5. Rate your confidence: 'high', 'medium', 'low'
6. Record time spent (optional)

## Agreement Target
We aim for >70% agreement between human and LLM judge. If agreement is lower, we'll tighten the evaluation rubric.

## Notes
- Take your time - quality over speed
- Trust your professional judgment
- When in doubt, explain your reasoning clearly
"""
        
        with open(instructions_path, 'w') as f:
            f.write(instructions)
    
    def analyze_agreement(self, completed_csv_path: str) -> AgreementAnalysis:
        """
        Analyze agreement between human annotations and LLM judge.
        
        Args:
            completed_csv_path: Path to completed human annotation CSV
            
        Returns:
            AgreementAnalysis with detailed agreement metrics
        """
        
        human_judgments = []
        
        # Load completed human annotations
        with open(completed_csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                if row['human_winner']:  # Skip incomplete annotations
                    human_judgments.append(row)
        
        if not human_judgments:
            raise ValueError("No completed human judgments found in CSV")
        
        # Calculate agreement metrics
        exact_agreements = 0
        criteria_scores = {'clarity': [], 'relevance': [], 'tone': [], 'factuality': []}
        disagreement_patterns = []
        
        for judgment in human_judgments:
            llm_winner = judgment['llm_judge_winner'].lower()
            human_winner = judgment['human_winner'].lower()
            
            # Exact agreement
            if llm_winner == human_winner:
                exact_agreements += 1
            else:
                # Record disagreement pattern
                pattern = f"{judgment['model_a']} vs {judgment['model_b']}: LLM={llm_winner}, Human={human_winner}"
                disagreement_patterns.append(pattern)
        
        agreement_rate = exact_agreements / len(human_judgments)
        
        # Analyze criteria agreement (if human provided scores)
        criteria_agreement = {}
        for criterion in criteria_scores.keys():
            human_scores = []
            llm_scores = []
            
            for judgment in human_judgments:
                human_score = judgment.get(f'{criterion}_score')
                if human_score and human_score.isdigit():
                    human_scores.append(int(human_score))
                    # Would need LLM criteria scores for comparison
            
            if human_scores:
                criteria_agreement[criterion] = sum(human_scores) / len(human_scores)
        
        # Generate rubric recommendations
        recommendations = self._generate_rubric_recommendations(
            agreement_rate, disagreement_patterns
        )
        
        # Assess judge reliability
        if agreement_rate >= 0.8:
            reliability = "high"
        elif agreement_rate >= 0.7:
            reliability = "acceptable" 
        elif agreement_rate >= 0.5:
            reliability = "concerning"
        else:
            reliability = "low"
        
        return AgreementAnalysis(
            total_comparisons=len(human_judgments),
            exact_agreement=exact_agreements,
            agreement_rate=agreement_rate,
            criteria_agreement=criteria_agreement,
            disagreement_patterns=disagreement_patterns[:10],  # Top 10
            rubric_recommendations=recommendations,
            judge_reliability_assessment=reliability
        )
    
    def _generate_rubric_recommendations(
        self,
        agreement_rate: float,
        disagreement_patterns: List[str]
    ) -> List[str]:
        """Generate recommendations for improving judge-human agreement."""
        
        recommendations = []
        
        if agreement_rate < 0.7:
            recommendations.append("Agreement below 70% threshold - tighten rubric")
            
        if agreement_rate < 0.6:
            recommendations.extend([
                "Add more specific evaluation criteria",
                "Provide more examples in judge prompt",
                "Consider domain-specific rubric adjustments"
            ])
        
        if agreement_rate < 0.5:
            recommendations.extend([
                "Fundamental rubric revision needed",
                "Consider different judge model",
                "Add human-in-the-loop validation"
            ])
        
        # Analyze disagreement patterns
        if len(disagreement_patterns) > 0:
            if any('tie' in pattern for pattern in disagreement_patterns):
                recommendations.append("Review tie handling - may be over/under-used")
            
            if len(set(disagreement_patterns)) < len(disagreement_patterns) / 2:
                recommendations.append("Systematic disagreement pattern detected")
        
        return recommendations

    def export_validation_report(
        self,
        agreement_analysis: AgreementAnalysis,
        output_path: Optional[str] = None
    ) -> str:
        """Export comprehensive validation report."""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"validation_report_{timestamp}.md"
        
        report = f"""# Human Validation Report

## Agreement Analysis
- **Total Comparisons**: {agreement_analysis.total_comparisons}
- **Exact Agreement**: {agreement_analysis.exact_agreement}/{agreement_analysis.total_comparisons}
- **Agreement Rate**: {agreement_analysis.agreement_rate:.1%}
- **Judge Reliability**: {agreement_analysis.judge_reliability_assessment}

## Criteria Agreement
{chr(10).join(f"- **{criterion.title()}**: {score:.2f}" for criterion, score in agreement_analysis.criteria_agreement.items())}

## Disagreement Patterns
{chr(10).join(f"- {pattern}" for pattern in agreement_analysis.disagreement_patterns[:5])}

## Recommendations
{chr(10).join(f"- {rec}" for rec in agreement_analysis.rubric_recommendations)}

## Conclusion
{"✅ Judge reliability is acceptable" if agreement_analysis.agreement_rate >= 0.7 else "⚠️ Judge reliability needs improvement"}

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        return str(output_path)


def create_demo_annotation_file():
    """Create a demo annotation file for testing."""
    validator = HumanValidationSystem()
    
    # Mock judgments for demo
    mock_judgments = [
        {
            'prompt': 'Write a LinkedIn post about AI in business',
            'output_a': 'AI is revolutionizing business operations with 80% efficiency gains!',
            'output_b': 'Artificial intelligence transforms how companies operate and compete.',
            'model_a': 'Qwen-2.5-7B',
            'model_b': 'Gemma-2-9B-IT',
            'judgment': {
                'winner': 'A',
                'reasons': 'More specific and engaging'
            }
        }
    ]
    
    csv_path = validator.create_human_annotation_csv(mock_judgments, n_samples=1)
    print(f"Demo annotation file created: {csv_path}")


if __name__ == "__main__":
    create_demo_annotation_file()