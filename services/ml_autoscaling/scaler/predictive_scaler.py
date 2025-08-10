"""
Predictive Scaler for ML Workloads

Implements time-series forecasting and pattern recognition for proactive scaling
of ML infrastructure based on historical patterns and upcoming workload predictions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import deque
import math


class SeasonalityType(Enum):
    """Types of seasonality patterns in workload"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NONE = "none"


class TrendType(Enum):
    """Types of trend patterns in workload"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class HistoricalPattern:
    """Historical pattern detected in workload"""
    pattern_type: str
    confidence: float
    periodicity: Optional[int] = None
    amplitude: Optional[float] = None
    trend: Optional[TrendType] = None
    seasonality: Optional[SeasonalityType] = None


@dataclass
class WorkloadForecast:
    """Forecasted workload for future time periods"""
    timestamp: datetime
    predicted_load: float
    confidence_interval: Tuple[float, float]
    recommended_replicas: int
    pattern_based: bool = False


@dataclass
class PredictionResult:
    """Result of predictive scaling analysis"""
    current_replicas: int
    predicted_replicas: int
    confidence: float
    forecast_horizon_minutes: int
    forecasts: List[WorkloadForecast] = field(default_factory=list)
    detected_patterns: List[HistoricalPattern] = field(default_factory=list)
    scale_up_at: Optional[datetime] = None
    scale_down_at: Optional[datetime] = None
    reasoning: str = ""


@dataclass
class ScalingPolicy:
    """Policy for scaling decisions"""
    min_replicas: int = 1
    max_replicas: int = 10
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    prediction_confidence_threshold: float = 0.7
    look_ahead_minutes: int = 15
    look_back_hours: int = 24
    enable_proactive_scaling: bool = True


@dataclass
class MetricDataPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PredictiveScaler:
    """
    Implements predictive scaling for ML workloads using time-series analysis.
    
    Features:
    - Pattern detection (daily, weekly cycles)
    - Trend analysis
    - Anomaly detection
    - Proactive scaling based on forecasts
    - Business hours awareness
    - Cost optimization through predictive scale-down
    """
    
    def __init__(self, policy: Optional[ScalingPolicy] = None):
        """Initialize predictive scaler with policy"""
        self.policy = policy or ScalingPolicy()
        self.historical_data: deque = deque(maxlen=10000)
        self.patterns_cache: Dict[str, HistoricalPattern] = {}
        self.forecast_cache: List[WorkloadForecast] = []
        self.last_prediction_time: Optional[datetime] = None
        
    async def predict_scaling_needs(
        self,
        historical_metrics: List[MetricDataPoint],
        current_replicas: int,
        forecast_horizon_minutes: int = 30,
    ) -> PredictionResult:
        """
        Predict future scaling needs based on historical patterns.
        
        Args:
            historical_metrics: Historical metric data points
            current_replicas: Current number of replicas
            forecast_horizon_minutes: How far ahead to forecast
            
        Returns:
            PredictionResult with scaling recommendations
        """
        # Store historical data
        self.historical_data.extend(historical_metrics)
        
        # Detect patterns in historical data
        patterns = await self._detect_patterns(historical_metrics)
        
        # Generate forecast
        forecasts = await self._generate_forecast(
            historical_metrics,
            patterns,
            forecast_horizon_minutes
        )
        
        # Calculate recommended replicas
        predicted_replicas = self._calculate_predicted_replicas(
            forecasts,
            current_replicas
        )
        
        # Determine confidence
        confidence = self._calculate_confidence(patterns, forecasts)
        
        # Find optimal scaling times
        scale_up_at, scale_down_at = self._find_optimal_scaling_times(forecasts)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            patterns,
            forecasts,
            current_replicas,
            predicted_replicas
        )
        
        result = PredictionResult(
            current_replicas=current_replicas,
            predicted_replicas=predicted_replicas,
            confidence=confidence,
            forecast_horizon_minutes=forecast_horizon_minutes,
            forecasts=forecasts,
            detected_patterns=patterns,
            scale_up_at=scale_up_at,
            scale_down_at=scale_down_at,
            reasoning=reasoning
        )
        
        self.last_prediction_time = datetime.now()
        return result
    
    async def _detect_patterns(
        self,
        metrics: List[MetricDataPoint]
    ) -> List[HistoricalPattern]:
        """Detect patterns in historical metrics"""
        patterns = []
        
        if len(metrics) < 24:  # Need at least 24 hours of data
            return patterns
        
        # Convert to numpy array for analysis
        values = np.array([m.value for m in metrics])
        timestamps = [m.timestamp for m in metrics]
        
        # Detect daily pattern
        daily_pattern = self._detect_daily_pattern(values, timestamps)
        if daily_pattern:
            patterns.append(daily_pattern)
        
        # Detect weekly pattern
        if len(metrics) >= 168:  # At least a week of hourly data
            weekly_pattern = self._detect_weekly_pattern(values, timestamps)
            if weekly_pattern:
                patterns.append(weekly_pattern)
        
        # Detect trend
        trend_pattern = self._detect_trend(values)
        if trend_pattern:
            patterns.append(trend_pattern)
        
        # Detect anomalies
        anomaly_pattern = self._detect_anomalies(values)
        if anomaly_pattern:
            patterns.append(anomaly_pattern)
        
        # Cache patterns
        for pattern in patterns:
            self.patterns_cache[pattern.pattern_type] = pattern
        
        return patterns
    
    def _detect_daily_pattern(
        self,
        values: np.ndarray,
        timestamps: List[datetime]
    ) -> Optional[HistoricalPattern]:
        """Detect daily cyclical patterns"""
        # Group by hour of day
        hourly_groups = {}
        for i, ts in enumerate(timestamps):
            hour = ts.hour
            if hour not in hourly_groups:
                hourly_groups[hour] = []
            hourly_groups[hour].append(values[i])
        
        # Calculate variance by hour
        hourly_means = {h: np.mean(vals) for h, vals in hourly_groups.items()}
        
        if not hourly_means:
            return None
        
        # Check for significant variation
        mean_variation = np.std(list(hourly_means.values()))
        overall_mean = np.mean(values)
        
        if mean_variation > overall_mean * 0.1:  # 10% variation threshold
            # Calculate confidence based on variation ratio
            confidence_score = min(0.9, (mean_variation / overall_mean) * 2)
            return HistoricalPattern(
                pattern_type="daily_cycle",
                confidence=confidence_score,
                periodicity=24,
                amplitude=mean_variation,
                seasonality=SeasonalityType.DAILY
            )
        
        return None
    
    def _detect_weekly_pattern(
        self,
        values: np.ndarray,
        timestamps: List[datetime]
    ) -> Optional[HistoricalPattern]:
        """Detect weekly cyclical patterns"""
        # Group by day of week
        daily_groups = {}
        for i, ts in enumerate(timestamps):
            dow = ts.weekday()
            if dow not in daily_groups:
                daily_groups[dow] = []
            daily_groups[dow].append(values[i])
        
        # Calculate variance by day
        daily_means = {d: np.mean(vals) for d, vals in daily_groups.items()}
        
        if not daily_means:
            return None
        
        # Check for weekend pattern
        if len(daily_means) >= 7:
            weekday_mean = np.mean([daily_means.get(i, 0) for i in range(5)])
            weekend_mean = np.mean([daily_means.get(i, 0) for i in [5, 6]])
            
            if abs(weekday_mean - weekend_mean) > weekday_mean * 0.3:
                return HistoricalPattern(
                    pattern_type="weekly_cycle",
                    confidence=0.8,
                    periodicity=168,  # hours in a week
                    amplitude=abs(weekday_mean - weekend_mean),
                    seasonality=SeasonalityType.WEEKLY
                )
        
        return None
    
    def _detect_trend(self, values: np.ndarray) -> Optional[HistoricalPattern]:
        """Detect trend in values"""
        if len(values) < 10:
            return None
        
        # Simple linear regression for trend
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        mean_value = np.mean(values)
        if mean_value == 0:
            return None
        
        trend_strength = abs(slope) / mean_value
        
        if trend_strength > 0.01:  # 1% change threshold
            trend_type = TrendType.INCREASING if slope > 0 else TrendType.DECREASING
            return HistoricalPattern(
                pattern_type="trend",
                confidence=min(0.9, trend_strength * 10),
                trend=trend_type
            )
        
        # Check for volatility
        std_dev = np.std(values)
        if std_dev > mean_value * 0.5:
            return HistoricalPattern(
                pattern_type="volatile",
                confidence=0.7,
                trend=TrendType.VOLATILE
            )
        
        return HistoricalPattern(
            pattern_type="stable",
            confidence=0.9,
            trend=TrendType.STABLE
        )
    
    def _detect_anomalies(self, values: np.ndarray) -> Optional[HistoricalPattern]:
        """Detect anomalies in values"""
        if len(values) < 10:
            return None
        
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return None
        
        # Count outliers (> 2 std deviations for more sensitivity)
        outliers = np.sum(np.abs(values - mean) > 2 * std)
        outlier_ratio = outliers / len(values)
        
        # Also check for extreme outliers (> 5 std deviations)
        extreme_outliers = np.sum(np.abs(values - mean) > 5 * std)
        
        if outlier_ratio > 0.05 or extreme_outliers > 0:  # More than 5% outliers or any extreme outlier
            confidence = min(0.9, max(outlier_ratio * 5, extreme_outliers * 0.5))
            return HistoricalPattern(
                pattern_type="anomaly_detected",
                confidence=confidence
            )
        
        return None
    
    async def _generate_forecast(
        self,
        historical_metrics: List[MetricDataPoint],
        patterns: List[HistoricalPattern],
        forecast_horizon_minutes: int
    ) -> List[WorkloadForecast]:
        """Generate workload forecast based on patterns"""
        forecasts = []
        
        if not historical_metrics:
            return forecasts
        
        # Get baseline from recent metrics
        recent_values = [m.value for m in historical_metrics[-24:]]  # Last 24 hours
        baseline = np.mean(recent_values) if recent_values else 0
        
        # Generate forecasts for each time period
        current_time = datetime.now()
        for minutes_ahead in range(0, forecast_horizon_minutes, 5):
            forecast_time = current_time + timedelta(minutes=minutes_ahead)
            
            # Apply patterns to baseline
            predicted_load = baseline
            pattern_confidence = 0.5
            
            # Apply daily pattern
            daily_pattern = next((p for p in patterns if p.pattern_type == "daily_cycle"), None)
            if daily_pattern:
                hour_factor = self._get_hour_factor(forecast_time.hour)
                predicted_load *= hour_factor
                pattern_confidence = max(pattern_confidence, daily_pattern.confidence)
            
            # Apply weekly pattern
            weekly_pattern = next((p for p in patterns if p.pattern_type == "weekly_cycle"), None)
            if weekly_pattern:
                dow_factor = self._get_dow_factor(forecast_time.weekday())
                predicted_load *= dow_factor
                pattern_confidence = max(pattern_confidence, weekly_pattern.confidence)
            
            # Apply trend
            trend_pattern = next((p for p in patterns if p.pattern_type == "trend"), None)
            if trend_pattern and trend_pattern.trend == TrendType.INCREASING:
                # 5% increase per hour for increasing trend
                hours_ahead = minutes_ahead / 60
                predicted_load *= (1 + 0.05 * hours_ahead)
            elif trend_pattern and trend_pattern.trend == TrendType.DECREASING:
                # 5% decrease per hour for decreasing trend
                hours_ahead = minutes_ahead / 60
                predicted_load *= max(0.1, 1 - 0.05 * hours_ahead)
            
            # Calculate confidence interval
            std_dev = np.std(recent_values) if recent_values else predicted_load * 0.2
            confidence_interval = (
                max(0, predicted_load - 2 * std_dev),
                predicted_load + 2 * std_dev
            )
            
            # Calculate recommended replicas
            recommended_replicas = self._load_to_replicas(predicted_load)
            
            forecasts.append(WorkloadForecast(
                timestamp=forecast_time,
                predicted_load=predicted_load,
                confidence_interval=confidence_interval,
                recommended_replicas=recommended_replicas,
                pattern_based=bool(patterns)
            ))
        
        # Cache forecasts
        self.forecast_cache = forecasts
        
        return forecasts
    
    def _get_hour_factor(self, hour: int) -> float:
        """Get scaling factor for hour of day"""
        # Business hours (9-17) have higher load
        if 9 <= hour <= 17:
            return 1.5
        # Night hours have lower load
        elif 0 <= hour <= 6:
            return 0.3
        # Morning/evening transitions
        else:
            return 1.0
    
    def _get_dow_factor(self, dow: int) -> float:
        """Get scaling factor for day of week"""
        # Weekdays have higher load
        if dow < 5:  # Monday-Friday
            return 1.2
        # Weekends have lower load
        else:
            return 0.6
    
    def _load_to_replicas(self, load: float) -> int:
        """Convert predicted load to replica count"""
        # Simple linear scaling with thresholds
        if load < 10:
            return self.policy.min_replicas
        elif load < 50:
            return 2
        elif load < 100:
            return 3
        elif load < 200:
            return 5
        elif load < 500:
            return 8
        else:
            return min(self.policy.max_replicas, int(load / 50))
    
    def _calculate_predicted_replicas(
        self,
        forecasts: List[WorkloadForecast],
        current_replicas: int
    ) -> int:
        """Calculate predicted replica count from forecasts"""
        if not forecasts:
            return current_replicas
        
        # Get maximum predicted replicas in forecast window
        max_replicas = max(f.recommended_replicas for f in forecasts)
        
        # Apply policy constraints
        return max(
            self.policy.min_replicas,
            min(self.policy.max_replicas, max_replicas)
        )
    
    def _calculate_confidence(
        self,
        patterns: List[HistoricalPattern],
        forecasts: List[WorkloadForecast]
    ) -> float:
        """Calculate overall prediction confidence"""
        if not patterns and not forecasts:
            return 0.0
        
        # Average pattern confidence
        pattern_confidence = np.mean([p.confidence for p in patterns]) if patterns else 0.5
        
        # Check forecast consistency
        if forecasts:
            loads = [f.predicted_load for f in forecasts]
            cv = np.std(loads) / np.mean(loads) if np.mean(loads) > 0 else 1.0
            forecast_confidence = max(0, 1 - cv)  # Lower CV = higher confidence
        else:
            forecast_confidence = 0.5
        
        # Combined confidence
        return (pattern_confidence + forecast_confidence) / 2
    
    def _find_optimal_scaling_times(
        self,
        forecasts: List[WorkloadForecast]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Find optimal times to scale up or down"""
        if not forecasts:
            return None, None
        
        scale_up_at = None
        scale_down_at = None
        
        current_replicas = forecasts[0].recommended_replicas if forecasts else 1
        
        for forecast in forecasts:
            # Find first time we need to scale up
            if not scale_up_at and forecast.recommended_replicas > current_replicas:
                # Scale up a bit early to be ready
                scale_up_at = forecast.timestamp - timedelta(minutes=2)
            
            # Find first time we can scale down
            if not scale_down_at and forecast.recommended_replicas < current_replicas:
                # Scale down after load has decreased
                scale_down_at = forecast.timestamp + timedelta(minutes=5)
        
        return scale_up_at, scale_down_at
    
    def _generate_reasoning(
        self,
        patterns: List[HistoricalPattern],
        forecasts: List[WorkloadForecast],
        current_replicas: int,
        predicted_replicas: int
    ) -> str:
        """Generate human-readable reasoning for prediction"""
        reasons = []
        
        # Pattern-based reasoning
        for pattern in patterns:
            if pattern.pattern_type == "daily_cycle":
                reasons.append(f"Daily cycle detected with {pattern.confidence:.0%} confidence")
            elif pattern.pattern_type == "weekly_cycle":
                reasons.append(f"Weekly pattern detected (weekday/weekend difference)")
            elif pattern.pattern_type == "trend" and pattern.trend:
                reasons.append(f"{pattern.trend.value.capitalize()} trend detected")
            elif pattern.pattern_type == "anomaly_detected":
                reasons.append("Recent anomalies detected in workload")
        
        # Forecast-based reasoning
        if forecasts:
            max_load = max(f.predicted_load for f in forecasts)
            min_load = min(f.predicted_load for f in forecasts)
            if max_load > min_load * 2:
                reasons.append(f"Significant load variation expected ({min_load:.0f}-{max_load:.0f})")
        
        # Scaling decision
        if predicted_replicas > current_replicas:
            reasons.append(f"Scale up recommended: {current_replicas} → {predicted_replicas} replicas")
        elif predicted_replicas < current_replicas:
            reasons.append(f"Scale down possible: {current_replicas} → {predicted_replicas} replicas")
        else:
            reasons.append(f"Maintain current {current_replicas} replicas")
        
        return ". ".join(reasons) if reasons else "No significant patterns detected"
    
    async def should_scale_proactively(
        self,
        prediction: PredictionResult
    ) -> bool:
        """Determine if proactive scaling should be triggered"""
        if not self.policy.enable_proactive_scaling:
            return False
        
        # Check confidence threshold
        if prediction.confidence < self.policy.prediction_confidence_threshold:
            return False
        
        # Check if scaling is needed
        if prediction.predicted_replicas == prediction.current_replicas:
            return False
        
        # Check if we have a scale-up time coming soon
        if prediction.scale_up_at:
            minutes_until_scale = (prediction.scale_up_at - datetime.now()).total_seconds() / 60
            if 0 < minutes_until_scale < self.policy.look_ahead_minutes:
                return True
        
        return False
    
    def get_cached_forecast(self) -> List[WorkloadForecast]:
        """Get cached forecast if available"""
        return self.forecast_cache
    
    def clear_cache(self):
        """Clear all cached data"""
        self.patterns_cache.clear()
        self.forecast_cache.clear()
        self.historical_data.clear()
        self.last_prediction_time = None