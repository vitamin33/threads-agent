#!/usr/bin/env python3
"""
Dual Judging System - Formatting-Blind Evaluation

Implements dual judging approach:
1. Normal text (with emojis, hashtags, markdown)  
2. Stripped text (content-only evaluation)

This separates presentation effects from substance quality.
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from .pairwise_judge import PairwiseJudge, JudgmentResult


@dataclass
class DualJudgmentResult:
    """Result from dual judging (formatted + stripped)."""
    formatted_judgment: JudgmentResult
    stripped_judgment: JudgmentResult
    presentation_advantage: str  # 'A', 'B', 'none'
    substance_winner: str  # 'A', 'B', 'tie'
    formatting_impact: float  # How much formatting changed the outcome


class FormattingStripper:
    """Removes formatting elements for content-only evaluation."""
    
    @staticmethod
    def strip_formatting(text: str) -> str:
        """Remove emojis, hashtags, markdown, and other formatting."""
        # Remove emojis (Unicode ranges for emojis)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        text = emoji_pattern.sub('', text)
        
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        
        # Remove bullet points and list formatting
        text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove excess whitespace
        text = ' '.join(text.split())
        
        return text.strip()


class DualJudge:
    """
    Dual judging system that evaluates both formatted and stripped content.
    
    Helps identify whether model advantages come from presentation
    or actual content substance.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize dual judge with configuration."""
        self.judge = PairwiseJudge(config)
        self.stripper = FormattingStripper()
    
    def judge_pair_dual(
        self,
        prompt: str,
        output_a: str,
        output_b: str,
        model_a: str = "Model A",
        model_b: str = "Model B",
        task_context: str = None
    ) -> DualJudgmentResult:
        """
        Judge pair with both formatted and stripped versions.
        
        Args:
            prompt: Original prompt
            output_a: Output from model A
            output_b: Output from model B
            model_a: Name of model A
            model_b: Name of model B
            task_context: Additional context
            
        Returns:
            DualJudgmentResult with both judgments and analysis
        """
        
        # 1. Judge formatted versions (normal)
        formatted_judgment, _ = self.judge.judge_pair(
            prompt=prompt,
            output_a=output_a,
            output_b=output_b,
            model_a=model_a,
            model_b=model_b,
            task_context=f"{task_context} (formatted)" if task_context else "formatted",
            randomize_order=True
        )
        
        # 2. Judge stripped versions (content-only)
        stripped_a = self.stripper.strip_formatting(output_a)
        stripped_b = self.stripper.strip_formatting(output_b)
        
        stripped_judgment, _ = self.judge.judge_pair(
            prompt=prompt,
            output_a=stripped_a,
            output_b=stripped_b,
            model_a=model_a,
            model_b=model_b,
            task_context=f"{task_context} (content-only)" if task_context else "content-only",
            randomize_order=True
        )
        
        # 3. Analyze formatting impact
        presentation_advantage = self._analyze_formatting_impact(
            formatted_judgment, stripped_judgment
        )
        
        # 4. Determine substance winner (stripped version)
        substance_winner = stripped_judgment.winner
        
        # 5. Calculate formatting impact score
        formatting_impact = self._calculate_formatting_impact(
            formatted_judgment, stripped_judgment
        )
        
        return DualJudgmentResult(
            formatted_judgment=formatted_judgment,
            stripped_judgment=stripped_judgment,
            presentation_advantage=presentation_advantage,
            substance_winner=substance_winner,
            formatting_impact=formatting_impact
        )
    
    def _analyze_formatting_impact(
        self, 
        formatted: JudgmentResult, 
        stripped: JudgmentResult
    ) -> str:
        """Analyze if formatting changed the judgment outcome."""
        
        if formatted.winner != stripped.winner:
            if formatted.winner == 'a' and stripped.winner != 'a':
                return 'A'  # Model A benefits from formatting
            elif formatted.winner == 'b' and stripped.winner != 'b':
                return 'B'  # Model B benefits from formatting
            else:
                return 'mixed'  # Complex formatting effect
        else:
            return 'none'  # Formatting didn't change outcome
    
    def _calculate_formatting_impact(
        self,
        formatted: JudgmentResult,
        stripped: JudgmentResult
    ) -> float:
        """Calculate numerical formatting impact score."""
        
        # Simple scoring based on winner changes
        if formatted.winner == stripped.winner:
            return 0.0  # No formatting impact
        elif formatted.winner == 'tie' or stripped.winner == 'tie':
            return 0.5  # Moderate impact (tie involvement)
        else:
            return 1.0  # Full impact (winner completely changed)


def run_dual_evaluation(
    outputs_a: List[Dict[str, Any]],
    outputs_b: List[Dict[str, Any]], 
    config: Dict[str, Any]
) -> List[DualJudgmentResult]:
    """
    Run dual evaluation on two sets of outputs.
    
    Returns comprehensive analysis including:
    - Formatted vs stripped judgments
    - Presentation advantage analysis
    - Substance quality assessment
    """
    
    dual_judge = DualJudge(config)
    results = []
    
    print("🔄 Running dual judgment evaluation...")
    print("   📝 Phase 1: Formatted content judging")
    print("   📝 Phase 2: Stripped content judging (content-only)")
    print("   📊 Phase 3: Formatting impact analysis")
    
    for i, (out_a, out_b) in enumerate(zip(outputs_a, outputs_b)):
        if out_a.get('prompt') != out_b.get('prompt'):
            continue  # Skip mismatched prompts
            
        print(f"   ⚖️  Judging pair {i+1}: {out_a.get('model_id')} vs {out_b.get('model_id')}")
        
        try:
            dual_result = dual_judge.judge_pair_dual(
                prompt=out_a['prompt'],
                output_a=out_a['content'],
                output_b=out_b['content'],
                model_a=out_a.get('model_id', 'Model A'),
                model_b=out_b.get('model_id', 'Model B'),
                task_context="LinkedIn business content"
            )
            
            results.append(dual_result)
            
        except Exception as e:
            print(f"   ❌ Error judging pair {i+1}: {e}")
    
    return results


if __name__ == "__main__":
    # Test the formatting stripper
    stripper = FormattingStripper()
    
    test_text = "🚀 **AI is revolutionizing** business operations! #Innovation #AI"
    stripped = stripper.strip_formatting(test_text)
    
    print("📝 Formatting Stripper Test:")
    print(f"Original: {test_text}")
    print(f"Stripped: {stripped}")