#!/usr/bin/env python3
"""
Robust Judge - Judge Consistency and Reliability Testing

Implements judge robustness checks:
1. Duplicate A/B pairs with shuffled order for consistency
2. Cross-judge validation with multiple judges
3. Judge agreement analysis and reliability metrics
"""

import random
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from .pairwise_judge import PairwiseJudge, JudgmentResult


@dataclass
class ConsistencyTest:
    """Result of judge consistency testing.""" 
    original_judgment: JudgmentResult
    duplicate_judgment: JudgmentResult
    consistent: bool
    agreement_score: float  # 0-1, higher is better


@dataclass
class RobustnessReport:
    """Comprehensive judge robustness analysis."""
    total_pairs: int
    duplicate_pairs: int
    consistency_rate: float
    agreement_scores: List[float]
    inconsistent_pairs: List[ConsistencyTest]
    judge_reliability: str  # 'high', 'medium', 'low'


class JudgeConsistencyTester:
    """Tests judge consistency with duplicate pairs."""
    
    def __init__(self, judge: PairwiseJudge, duplicate_rate: float = 0.15):
        """
        Initialize consistency tester.
        
        Args:
            judge: PairwiseJudge instance to test
            duplicate_rate: Fraction of pairs to duplicate for testing
        """
        self.judge = judge
        self.duplicate_rate = duplicate_rate
    
    def create_duplicate_pairs(
        self, 
        comparisons: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Create duplicate pairs for consistency testing.
        
        Args:
            comparisons: Original comparison pairs
            
        Returns:
            Tuple of (extended_comparisons, duplicate_indices)
        """
        n_duplicates = max(1, int(len(comparisons) * self.duplicate_rate))
        
        # Select random pairs to duplicate
        duplicate_indices = random.sample(range(len(comparisons)), n_duplicates)
        extended_comparisons = comparisons.copy()
        
        for idx in duplicate_indices:
            original = comparisons[idx]
            
            # Create duplicate with shuffled order if not already shuffled
            duplicate = {
                'prompt': original['prompt'],
                'output_a': original['output_b'],  # Swap A/B
                'output_b': original['output_a'],
                'model_a': original.get('model_b', 'Model B'),
                'model_b': original.get('model_a', 'Model A'),
                'task_context': original.get('task_context'),
                'is_duplicate': True,
                'original_index': idx,
                'duplicate_type': 'order_swap'
            }
            
            extended_comparisons.append(duplicate)
        
        return extended_comparisons, duplicate_indices
    
    def analyze_consistency(
        self,
        results: List[Dict[str, Any]],
        duplicate_indices: List[int]
    ) -> RobustnessReport:
        """
        Analyze judge consistency from results.
        
        Args:
            results: List of judgment results including duplicates
            duplicate_indices: Indices of original pairs that were duplicated
            
        Returns:
            RobustnessReport with consistency analysis
        """
        consistency_tests = []
        
        # Find duplicate pairs and analyze consistency
        duplicate_results = [r for r in results if r.get('is_duplicate', False)]
        
        for duplicate_result in duplicate_results:
            original_idx = duplicate_result['original_index']
            
            # Find original result
            original_result = None
            for result in results:
                if (not result.get('is_duplicate', False) and 
                    result.get('comparison_id') == original_idx):
                    original_result = result
                    break
            
            if original_result:
                consistency = self._check_pair_consistency(
                    original_result['judgment'],
                    duplicate_result['judgment']
                )
                consistency_tests.append(consistency)
        
        # Calculate overall metrics
        if consistency_tests:
            consistency_rate = sum(1 for test in consistency_tests if test.consistent) / len(consistency_tests)
            agreement_scores = [test.agreement_score for test in consistency_tests]
            avg_agreement = sum(agreement_scores) / len(agreement_scores)
            
            # Determine reliability level
            if consistency_rate >= 0.8 and avg_agreement >= 0.7:
                reliability = 'high'
            elif consistency_rate >= 0.6 and avg_agreement >= 0.5:
                reliability = 'medium'  
            else:
                reliability = 'low'
        else:
            consistency_rate = 0.0
            agreement_scores = []
            reliability = 'unknown'
        
        return RobustnessReport(
            total_pairs=len(results) - len(duplicate_results),
            duplicate_pairs=len(duplicate_results),
            consistency_rate=consistency_rate,
            agreement_scores=agreement_scores,
            inconsistent_pairs=[test for test in consistency_tests if not test.consistent],
            judge_reliability=reliability
        )
    
    def _check_pair_consistency(
        self,
        judgment1: Dict[str, Any],
        judgment2: Dict[str, Any]
    ) -> ConsistencyTest:
        """Check consistency between original and duplicate judgments."""
        
        # Compare winners (accounting for A/B swap)
        winner1 = judgment1.get('winner', 'tie')
        winner2 = judgment2.get('winner', 'tie')
        
        # For swapped pairs, flip the winner
        if winner2 == 'a':
            winner2_flipped = 'b'
        elif winner2 == 'b':
            winner2_flipped = 'a'
        else:
            winner2_flipped = 'tie'
        
        consistent = (winner1 == winner2_flipped)
        
        # Calculate agreement score based on criteria scores
        agreement_score = self._calculate_criteria_agreement(judgment1, judgment2)
        
        return ConsistencyTest(
            original_judgment=judgment1,
            duplicate_judgment=judgment2,
            consistent=consistent,
            agreement_score=agreement_score
        )
    
    def _calculate_criteria_agreement(
        self,
        judgment1: Dict[str, Any],
        judgment2: Dict[str, Any]
    ) -> float:
        """Calculate agreement score between criteria scores."""
        
        criteria1 = judgment1.get('criteria_scores', {})
        criteria2 = judgment2.get('criteria_scores', {})
        
        if not criteria1 or not criteria2:
            return 0.5  # Default if no criteria scores
        
        # Calculate average absolute difference
        common_criteria = set(criteria1.keys()) & set(criteria2.keys())
        
        if not common_criteria:
            return 0.5
        
        differences = []
        for criterion in common_criteria:
            diff = abs(criteria1[criterion] - criteria2[criterion])
            normalized_diff = diff / 4  # Max difference is 4 (5-1)
            agreement = 1 - normalized_diff
            differences.append(agreement)
        
        return sum(differences) / len(differences)


class CrossJudgeValidator:
    """Validates judgments across multiple judge models."""
    
    def __init__(self, judges: List[PairwiseJudge]):
        """Initialize with list of judge instances."""
        self.judges = judges
    
    def cross_validate_subset(
        self,
        comparisons: List[Dict[str, Any]],
        subset_size: int = 10
    ) -> Dict[str, Any]:
        """
        Cross-validate a subset of comparisons across multiple judges.
        
        Args:
            comparisons: List of comparison pairs
            subset_size: Number of pairs to cross-validate
            
        Returns:
            Cross-validation analysis results
        """
        
        # Select random subset
        subset_indices = random.sample(range(len(comparisons)), 
                                     min(subset_size, len(comparisons)))
        subset_comparisons = [comparisons[i] for i in subset_indices]
        
        # Get judgments from all judges
        all_judgments = {}
        
        for judge_idx, judge in enumerate(self.judges):
            judge_name = f"Judge_{judge_idx + 1}"
            all_judgments[judge_name] = []
            
            for comp in subset_comparisons:
                try:
                    judgment, _ = judge.judge_pair(
                        prompt=comp['prompt'],
                        output_a=comp['output_a'],
                        output_b=comp['output_b'],
                        model_a=comp.get('model_a', 'Model A'),
                        model_b=comp.get('model_b', 'Model B'),
                        task_context=comp.get('task_context')
                    )
                    all_judgments[judge_name].append(judgment)
                except Exception as e:
                    print(f"Cross-judge error for {judge_name}: {e}")
        
        # Analyze inter-judge agreement
        agreement_analysis = self._analyze_inter_judge_agreement(all_judgments)
        
        return {
            'subset_size': len(subset_comparisons),
            'judges_tested': len(self.judges),
            'judgments': all_judgments,
            'agreement_analysis': agreement_analysis
        }
    
    def _analyze_inter_judge_agreement(
        self,
        all_judgments: Dict[str, List[JudgmentResult]]
    ) -> Dict[str, float]:
        """Analyze agreement between different judges."""
        
        judge_names = list(all_judgments.keys())
        n_judges = len(judge_names)
        
        if n_judges < 2:
            return {'error': 'Need at least 2 judges for agreement analysis'}
        
        # Calculate pairwise agreement between judges
        agreements = {}
        
        for i in range(n_judges):
            for j in range(i + 1, n_judges):
                judge1 = judge_names[i]
                judge2 = judge_names[j]
                
                judgments1 = all_judgments[judge1]
                judgments2 = all_judgments[judge2]
                
                # Calculate agreement rate
                if len(judgments1) == len(judgments2):
                    agreements_count = sum(
                        1 for j1, j2 in zip(judgments1, judgments2)
                        if j1.winner == j2.winner
                    )
                    
                    agreement_rate = agreements_count / len(judgments1)
                    agreements[f"{judge1}_vs_{judge2}"] = agreement_rate
        
        # Calculate overall agreement
        if agreements:
            overall_agreement = sum(agreements.values()) / len(agreements)
            agreements['overall_inter_judge_agreement'] = overall_agreement
        
        return agreements


def test_judge_robustness():
    """Test judge robustness functionality."""
    
    # Mock judge for testing
    class MockJudge:
        def judge_pair(self, **kwargs):
            return JudgmentResult(
                winner=random.choice(['A', 'B', 'tie']),
                reasons="Mock judgment",
                criteria_scores={'clarity': 3, 'relevance': 4},
                confidence=0.7,
                judge_model="mock-judge"
            ), False
    
    mock_judge = MockJudge()
    tester = JudgeConsistencyTester(mock_judge)
    
    # Test with mock comparisons
    mock_comparisons = [
        {
            'prompt': 'Test prompt 1',
            'output_a': 'Output A1',
            'output_b': 'Output B1'
        },
        {
            'prompt': 'Test prompt 2', 
            'output_a': 'Output A2',
            'output_b': 'Output B2'
        }
    ]
    
    extended, duplicate_indices = tester.create_duplicate_pairs(mock_comparisons)
    
    print("🧪 Judge Robustness Test:")
    print(f"Original pairs: {len(mock_comparisons)}")
    print(f"With duplicates: {len(extended)}")
    print(f"Duplicate indices: {duplicate_indices}")


if __name__ == "__main__":
    test_judge_robustness()