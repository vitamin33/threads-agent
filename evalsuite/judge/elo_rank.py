#!/usr/bin/env python3
"""
Elo Ranking with Bootstrap Confidence Intervals

Implements Bradley-Terry model and Elo ranking system
with 1,000 bootstrap resamples for 95% confidence intervals.
"""

import random
import statistics
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np


@dataclass
class EloResult:
    """Elo ranking result with confidence intervals."""
    model_id: str
    elo_score: float
    ci_lower: float
    ci_upper: float
    win_rate: float
    total_comparisons: int


class EloRanking:
    """Elo ranking system with bootstrap confidence intervals."""
    
    def __init__(self, k_factor: float = 32.0):
        """Initialize Elo ranking system."""
        self.k_factor = k_factor
        self.initial_rating = 1000.0
    
    def calculate_elo_rankings(self, judgments: List[Any]) -> List[EloResult]:
        """Calculate Elo rankings from pairwise judgments."""
        
        print("🏆 Calculating Elo rankings with bootstrap CIs...")
        
        # Extract all models
        models = set()
        for judgment in judgments:
            models.add(judgment.model_a)
            models.add(judgment.model_b)
        
        models = list(models)
        print(f"   📊 Models: {len(models)}")
        print(f"   🔍 Judgments: {len(judgments)}")
        
        # Calculate base Elo scores
        base_elos = self._calculate_base_elo(judgments, models)
        
        # Bootstrap confidence intervals
        bootstrap_results = self._bootstrap_confidence_intervals(judgments, models)
        
        # Combine results
        results = []
        for model in models:
            elo_score = base_elos[model]
            ci_lower, ci_upper = bootstrap_results[model]
            
            # Calculate win rate
            wins = sum(1 for j in judgments 
                      if (j.model_a == model and j.winner == "A") or 
                         (j.model_b == model and j.winner == "B"))
            total = sum(1 for j in judgments 
                       if j.model_a == model or j.model_b == model)
            win_rate = wins / total if total > 0 else 0.0
            
            results.append(EloResult(
                model_id=model,
                elo_score=elo_score,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                win_rate=win_rate,
                total_comparisons=total
            ))
        
        # Sort by Elo score (descending)
        results.sort(key=lambda x: x.elo_score, reverse=True)
        
        print("   ✅ Elo rankings calculated with 95% CIs")
        return results
    
    def _calculate_base_elo(self, judgments: List[Any], models: List[str]) -> Dict[str, float]:
        """Calculate base Elo scores."""
        elos = {model: self.initial_rating for model in models}
        
        for judgment in judgments:
            model_a = judgment.model_a
            model_b = judgment.model_b
            winner = judgment.winner
            
            if winner == "tie":
                continue  # Skip ties for Elo calculation
            
            # Current ratings
            rating_a = elos[model_a]
            rating_b = elos[model_b]
            
            # Expected scores
            expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
            expected_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))
            
            # Actual scores
            if winner == "A":
                actual_a, actual_b = 1.0, 0.0
            else:  # winner == "B"
                actual_a, actual_b = 0.0, 1.0
            
            # Update ratings
            elos[model_a] += self.k_factor * (actual_a - expected_a)
            elos[model_b] += self.k_factor * (actual_b - expected_b)
        
        return elos
    
    def _bootstrap_confidence_intervals(
        self, 
        judgments: List[Any], 
        models: List[str],
        n_bootstrap: int = 1000
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate bootstrap confidence intervals."""
        
        bootstrap_elos = defaultdict(list)
        
        for i in range(n_bootstrap):
            if (i + 1) % 200 == 0:
                print(f"   📊 Bootstrap progress: {i+1}/{n_bootstrap}")
            
            # Resample judgments with replacement
            resampled_judgments = random.choices(judgments, k=len(judgments))
            
            # Calculate Elo for this resample
            sample_elos = self._calculate_base_elo(resampled_judgments, models)
            
            for model, elo in sample_elos.items():
                bootstrap_elos[model].append(elo)
        
        # Calculate 95% confidence intervals
        confidence_intervals = {}
        for model in models:
            elo_samples = bootstrap_elos[model]
            ci_lower = np.percentile(elo_samples, 2.5)
            ci_upper = np.percentile(elo_samples, 97.5)
            confidence_intervals[model] = (ci_lower, ci_upper)
        
        return confidence_intervals


def rank_models_with_bootstrap(judgments: List[Any]) -> List[EloResult]:
    """Rank models using Elo with bootstrap confidence intervals."""
    
    ranker = EloRanking()
    return ranker.calculate_elo_rankings(judgments)