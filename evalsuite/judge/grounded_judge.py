#!/usr/bin/env python3
"""
Grounded Judge - Fact-Checking and Grounding Penalty System

Implements fact-grounding evaluation that:
1. Penalizes made-up statistics unless provided in context
2. Maintains separate "grounded mode" leaderboard
3. Provides fact shelf for controlled evaluation
"""

import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from .pairwise_judge import PairwiseJudge, JudgmentResult


@dataclass
class GroundingAnalysis:
    """Analysis of content grounding and factuality."""
    ungrounded_stats: List[str]
    grounded_stats: List[str]
    grounding_score: float  # 0-1, higher is better
    penalty_applied: float
    grounded_content: str  # Content with ungrounded stats flagged


@dataclass
class GroundedJudgmentResult:
    """Result from grounded evaluation."""
    normal_judgment: JudgmentResult
    grounded_judgment: JudgmentResult
    grounding_analysis_a: GroundingAnalysis
    grounding_analysis_b: GroundingAnalysis


class FactGroundingAnalyzer:
    """Analyzes content for factual grounding and unsubstantiated claims."""
    
    def __init__(self, fact_shelf: Optional[Dict[str, Any]] = None):
        """
        Initialize grounding analyzer.
        
        Args:
            fact_shelf: Dict of allowed facts and statistics
        """
        self.fact_shelf = fact_shelf or {}
        
        # Common ungrounded statistic patterns
        self.stat_patterns = [
            r'\b\d{1,2}%\b',  # Percentages like 80%, 1%
            r'\b\d+\s*billion\b',  # Billions
            r'\b\d+\s*million\b',  # Millions  
            r'\b\d+\s*thousand\b',  # Thousands
            r'\b\d+x\s+(?:increase|improvement|growth)\b',  # Multipliers
            r'\$\d+[kmb]?\b',  # Dollar amounts
        ]
    
    def analyze_grounding(self, content: str, allowed_facts: Optional[Set[str]] = None) -> GroundingAnalysis:
        """
        Analyze content for factual grounding.
        
        Args:
            content: Text content to analyze
            allowed_facts: Set of allowed factual claims
            
        Returns:
            GroundingAnalysis with grounding assessment
        """
        allowed_facts = allowed_facts or set()
        ungrounded_stats = []
        grounded_stats = []
        
        # Find all statistical claims
        all_stats = []
        for pattern in self.stat_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            all_stats.extend(matches)
        
        # Check each statistic against fact shelf and allowed facts
        for stat in all_stats:
            stat_context = self._get_stat_context(content, stat)
            
            if self._is_grounded_stat(stat, stat_context, allowed_facts):
                grounded_stats.append(stat)
            else:
                ungrounded_stats.append(stat)
        
        # Calculate grounding score
        total_stats = len(all_stats)
        if total_stats == 0:
            grounding_score = 1.0  # No stats = no penalty
        else:
            grounding_score = len(grounded_stats) / total_stats
        
        # Apply penalty for ungrounded stats
        penalty = len(ungrounded_stats) * 0.1  # 10% penalty per ungrounded stat
        
        # Create grounded version of content
        grounded_content = self._create_grounded_content(content, ungrounded_stats)
        
        return GroundingAnalysis(
            ungrounded_stats=ungrounded_stats,
            grounded_stats=grounded_stats,
            grounding_score=grounding_score,
            penalty_applied=penalty,
            grounded_content=grounded_content
        )
    
    def _get_stat_context(self, content: str, stat: str) -> str:
        """Get surrounding context for a statistic."""
        # Find the sentence containing the statistic
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            if stat in sentence:
                return sentence.strip()
        return ""
    
    def _is_grounded_stat(self, stat: str, context: str, allowed_facts: Set[str]) -> bool:
        """Check if a statistic is grounded in allowed facts."""
        
        # Check against fact shelf
        if self.fact_shelf:
            for fact_key, fact_data in self.fact_shelf.items():
                if isinstance(fact_data, dict):
                    if stat in str(fact_data.get('value', '')):
                        return True
                elif stat in str(fact_data):
                    return True
        
        # Check against allowed facts
        if allowed_facts:
            return any(stat in fact for fact in allowed_facts)
        
        # Check for attribution indicators (not foolproof but helpful)
        attribution_indicators = [
            'according to', 'study by', 'research shows', 'survey found',
            'data from', 'report by', 'analysis by', 'statistics from'
        ]
        
        context_lower = context.lower()
        return any(indicator in context_lower for indicator in attribution_indicators)
    
    def _create_grounded_content(self, content: str, ungrounded_stats: List[str]) -> str:
        """Create version of content with ungrounded stats flagged."""
        grounded_content = content
        
        for stat in ungrounded_stats:
            # Flag ungrounded statistics
            grounded_content = grounded_content.replace(
                stat, f"[UNGROUNDED: {stat}]"
            )
        
        return grounded_content


class GroundedJudge:
    """
    Judge that evaluates content with fact-grounding penalties.
    
    Maintains separate rankings for:
    - Normal mode (formatting + any claims allowed)
    - Grounded mode (penalties for unsubstantiated claims)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize grounded judge."""
        self.config = config
        self.judge = PairwiseJudge(config)
        self.analyzer = FactGroundingAnalyzer(config.get('fact_shelf'))
    
    def judge_pair_grounded(
        self,
        prompt: str,
        output_a: str,
        output_b: str,
        model_a: str = "Model A",
        model_b: str = "Model B",
        allowed_facts: Optional[Set[str]] = None
    ) -> GroundedJudgmentResult:
        """
        Judge pair with grounding analysis and penalties.
        
        Args:
            prompt: Original prompt
            output_a: Output from model A  
            output_b: Output from model B
            model_a: Name of model A
            model_b: Name of model B
            allowed_facts: Set of facts allowed for this prompt
            
        Returns:
            GroundedJudgmentResult with normal and grounded judgments
        """
        
        # 1. Normal judgment (no grounding penalties)
        normal_judgment, _ = self.judge.judge_pair(
            prompt=prompt,
            output_a=output_a,
            output_b=output_b,
            model_a=model_a,
            model_b=model_b,
            task_context="normal evaluation"
        )
        
        # 2. Analyze grounding for both outputs
        grounding_a = self.analyzer.analyze_grounding(output_a, allowed_facts)
        grounding_b = self.analyzer.analyze_grounding(output_b, allowed_facts)
        
        # 3. Create grounded versions (with penalties applied)
        grounded_content_a = grounding_a.grounded_content
        grounded_content_b = grounding_b.grounded_content
        
        # 4. Judge grounded versions
        grounded_judgment, _ = self.judge.judge_pair(
            prompt=f"{prompt}\n\nNote: [UNGROUNDED: X] indicates unsubstantiated claims that should be penalized.",
            output_a=grounded_content_a,
            output_b=grounded_content_b,
            model_a=model_a,
            model_b=model_b,
            task_context="grounded evaluation with fact-checking"
        )
        
        return GroundedJudgmentResult(
            normal_judgment=normal_judgment,
            grounded_judgment=grounded_judgment,
            grounding_analysis_a=grounding_a,
            grounding_analysis_b=grounding_b
        )


# Example fact shelf for business content
BUSINESS_FACT_SHELF = {
    "ai_adoption": {
        "value": "According to McKinsey, 70% of companies have adopted AI in at least one business function",
        "source": "McKinsey Global AI Survey 2023"
    },
    "remote_work": {
        "value": "FlexJobs survey shows 77% of workers want remote options",
        "source": "FlexJobs 2023 Career Pulse Survey"
    },
    "productivity": {
        "value": "MIT research indicates 14% productivity increase from AI tools",
        "source": "MIT Technology Review 2023"
    }
}


def test_grounding_analyzer():
    """Test the fact grounding analyzer."""
    analyzer = FactGroundingAnalyzer(BUSINESS_FACT_SHELF)
    
    # Test content with both grounded and ungrounded stats
    test_content = """
    AI is transforming business operations! According to McKinsey, 70% of companies 
    have adopted AI. However, chatbots handle 80% of customer queries (this seems 
    made up). Research shows 90% productivity gains are possible.
    """
    
    allowed_facts = {
        "According to McKinsey, 70% of companies have adopted AI"
    }
    
    result = analyzer.analyze_grounding(test_content, allowed_facts)
    
    print("🧪 Grounding Analysis Test:")
    print(f"Grounded stats: {result.grounded_stats}")
    print(f"Ungrounded stats: {result.ungrounded_stats}")
    print(f"Grounding score: {result.grounding_score:.2f}")
    print(f"Penalty: {result.penalty_applied:.1f}")


if __name__ == "__main__":
    test_grounding_analyzer()