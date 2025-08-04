import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
import structlog
import textstat
import re
import openai
from datetime import datetime

from ..models.article import InsightScore, ArticleContent, Platform, CodeAnalysis
from ..core.config import get_settings

logger = structlog.get_logger()


class InsightPredictor:
    """Predicts the quality and engagement potential of technical articles"""

    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)

        # Feature extractors
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000, stop_words="english", ngram_range=(1, 2)
        )

        # Models for different aspects
        self.technical_depth_model = None
        self.engagement_model = None
        self.uniqueness_model = None

        # Training data (would be loaded from database in production)
        self.historical_data = self._load_historical_data()

        # Trend keywords (updated regularly)
        self.trending_keywords = {
            "ai_ml": [
                "ai",
                "ml",
                "llm",
                "gpt",
                "machine learning",
                "artificial intelligence",
                "neural",
                "model",
            ],
            "cloud_native": [
                "kubernetes",
                "k8s",
                "docker",
                "microservices",
                "serverless",
                "cloud",
            ],
            "devops": [
                "devops",
                "ci/cd",
                "automation",
                "monitoring",
                "observability",
                "infrastructure",
            ],
            "performance": [
                "performance",
                "optimization",
                "scalability",
                "latency",
                "throughput",
            ],
            "security": [
                "security",
                "authentication",
                "authorization",
                "encryption",
                "vulnerability",
            ],
        }

    async def predict_insight_quality(
        self,
        content: ArticleContent,
        code_analysis: Optional[CodeAnalysis] = None,
        target_platform: Platform = Platform.DEVTO,
    ) -> InsightScore:
        """Predict comprehensive insight quality score"""

        logger.info(
            "Predicting insight quality", title=content.title, platform=target_platform
        )

        # Extract features
        features = await self._extract_features(content, code_analysis, target_platform)

        # Predict individual components
        technical_depth = await self._predict_technical_depth(features)
        uniqueness = await self._predict_uniqueness(features)
        readability = self._calculate_readability(content.content)
        engagement_potential = await self._predict_engagement(features, target_platform)
        trend_alignment = self._calculate_trend_alignment(content, target_platform)

        # Calculate overall score with weights
        weights = self._get_platform_weights(target_platform)
        overall_score = (
            technical_depth * weights["technical"]
            + uniqueness * weights["uniqueness"]
            + readability * weights["readability"]
            + engagement_potential * weights["engagement"]
            + trend_alignment * weights["trends"]
        )

        # Calculate confidence based on feature completeness
        confidence = self._calculate_confidence(features)

        return InsightScore(
            technical_depth=technical_depth,
            uniqueness=uniqueness,
            readability=readability,
            engagement_potential=engagement_potential,
            trend_alignment=trend_alignment,
            overall_score=overall_score,
            confidence=confidence,
        )

    async def _extract_features(
        self,
        content: ArticleContent,
        code_analysis: Optional[CodeAnalysis],
        platform: Platform,
    ) -> Dict[str, Any]:
        """Extract comprehensive features for prediction"""

        features = {}

        # Content features
        text = f"{content.title} {content.subtitle or ''} {content.content}"
        features.update(self._extract_text_features(text))

        # Structure features
        features.update(self._extract_structure_features(content))

        # Code features
        if code_analysis:
            features.update(self._extract_code_features(code_analysis))

        # Platform features
        features.update(self._extract_platform_features(content, platform))

        # Temporal features
        features.update(self._extract_temporal_features())

        return features

    def _extract_text_features(self, text: str) -> Dict[str, float]:
        """Extract text-based features"""
        features = {}

        # Basic text metrics
        words = text.split()
        features["word_count"] = len(words)
        features["char_count"] = len(text)
        features["sentence_count"] = len(re.split(r"[.!?]+", text))
        features["avg_word_length"] = (
            np.mean([len(word) for word in words]) if words else 0
        )

        # Readability metrics
        features["flesch_kincaid"] = textstat.flesch_kincaid_grade(text)
        features["flesch_reading_ease"] = textstat.flesch_reading_ease(text)
        features["smog_index"] = textstat.smog_index(text)
        features["automated_readability"] = textstat.automated_readability_index(text)

        # Technical complexity indicators
        features["code_blocks"] = text.count("```")
        features["code_references"] = len(re.findall(r"`[^`]+`", text))
        features["technical_terms"] = self._count_technical_terms(text)

        # Engagement indicators
        features["questions"] = text.count("?")
        features["exclamations"] = text.count("!")
        features["lists"] = text.count("\n- ") + text.count("\n* ")
        features["headers"] = text.count("\n#")

        # Emotional indicators
        features["first_person"] = text.lower().count(" i ") + text.lower().count("my ")
        features["second_person"] = text.lower().count("you ") + text.lower().count(
            "your "
        )

        return features

    def _extract_structure_features(self, content: ArticleContent) -> Dict[str, float]:
        """Extract structural features from content"""
        features = {}

        # Title features
        title_words = content.title.split()
        features["title_length"] = len(title_words)
        features["title_has_numbers"] = any(char.isdigit() for char in content.title)
        features["title_has_question"] = "?" in content.title
        features["title_has_how"] = content.title.lower().startswith("how")

        # Content structure
        features["has_subtitle"] = 1 if content.subtitle else 0
        features["code_examples_count"] = len(content.code_examples)
        features["insights_count"] = len(content.insights)
        features["tags_count"] = len(content.tags)
        features["estimated_read_time"] = content.estimated_read_time

        # Code example quality
        if content.code_examples:
            features["avg_code_length"] = np.mean(
                [len(ex["code"]) for ex in content.code_examples]
            )
            features["has_code_explanations"] = sum(
                1 for ex in content.code_examples if ex.get("explanation")
            ) / len(content.code_examples)
        else:
            features["avg_code_length"] = 0
            features["has_code_explanations"] = 0

        return features

    def _extract_code_features(self, analysis: CodeAnalysis) -> Dict[str, float]:
        """Extract features from code analysis"""
        features = {}

        # Complexity and quality
        features["code_complexity"] = analysis.complexity_score
        features["test_coverage"] = analysis.test_coverage
        features["patterns_count"] = len(analysis.patterns)
        features["dependencies_count"] = len(analysis.dependencies)

        # Architecture sophistication
        sophisticated_patterns = [
            "microservices",
            "kubernetes",
            "async_programming",
            "observability",
        ]
        features["sophisticated_patterns"] = sum(
            1 for p in analysis.patterns if p in sophisticated_patterns
        )

        # Modern tech stack
        modern_deps = ["fastapi", "kubernetes", "prometheus", "openai", "asyncio"]
        features["modern_dependencies"] = sum(
            1
            for dep in analysis.dependencies
            if any(modern in dep.lower() for modern in modern_deps)
        )

        # Function analysis
        if analysis.interesting_functions:
            features["avg_function_complexity"] = np.mean(
                [f.get("complexity", 1) for f in analysis.interesting_functions]
            )
            features["async_functions_ratio"] = sum(
                1 for f in analysis.interesting_functions if f.get("is_async", False)
            ) / len(analysis.interesting_functions)
        else:
            features["avg_function_complexity"] = 1
            features["async_functions_ratio"] = 0

        # Recent activity
        features["recent_changes_count"] = len(analysis.recent_changes)

        return features

    def _extract_platform_features(
        self, content: ArticleContent, platform: Platform
    ) -> Dict[str, float]:
        """Extract platform-specific features"""
        features = {}

        # Platform preferences
        platform_prefs = {
            Platform.DEVTO: {
                "prefers_tutorials": 1.2,
                "prefers_beginners": 1.1,
                "prefers_code_heavy": 1.3,
            },
            Platform.LINKEDIN: {
                "prefers_professional": 1.3,
                "prefers_leadership": 1.2,
                "prefers_business_value": 1.4,
            },
            Platform.TWITTER: {
                "prefers_concise": 1.5,
                "prefers_trendy": 1.3,
                "prefers_controversial": 1.1,
            },
        }

        prefs = platform_prefs.get(platform, {})
        for pref, weight in prefs.items():
            features[f"platform_{pref}"] = weight

        # Tag alignment with platform
        platform_tags = {
            Platform.DEVTO: ["tutorial", "beginners", "python", "javascript"],
            Platform.LINKEDIN: ["leadership", "engineering", "career", "management"],
            Platform.TWITTER: ["tips", "tech", "ai", "trending"],
        }

        relevant_tags = platform_tags.get(platform, [])
        features["tag_platform_alignment"] = sum(
            1 for tag in content.tags if tag in relevant_tags
        ) / max(len(content.tags), 1)

        return features

    def _extract_temporal_features(self) -> Dict[str, float]:
        """Extract time-based features"""
        now = datetime.utcnow()
        features = {}

        # Day of week (0 = Monday)
        features["day_of_week"] = now.weekday()
        features["is_weekday"] = 1 if now.weekday() < 5 else 0

        # Hour of day
        features["hour_of_day"] = now.hour
        features["is_peak_hours"] = 1 if 9 <= now.hour <= 17 else 0

        # Month and season
        features["month"] = now.month
        features["is_q4"] = 1 if now.month >= 10 else 0

        return features

    async def _predict_technical_depth(self, features: Dict[str, Any]) -> float:
        """Predict technical depth score using AI and heuristics"""

        # Heuristic scoring (would be replaced with trained model)
        score = 5.0  # Base score

        # Code complexity contribution
        score += min(features.get("code_complexity", 0) * 0.5, 2.0)

        # Technical terms and code blocks
        score += min(features.get("technical_terms", 0) * 0.1, 1.5)
        score += min(features.get("code_blocks", 0) * 0.3, 1.5)

        # Sophisticated patterns
        score += features.get("sophisticated_patterns", 0) * 0.5

        # Modern dependencies
        score += features.get("modern_dependencies", 0) * 0.3

        # Function complexity
        score += min(features.get("avg_function_complexity", 1) * 0.2, 1.0)

        return min(score, 10.0)

    async def _predict_uniqueness(self, features: Dict[str, Any]) -> float:
        """Predict uniqueness score"""

        # Use AI to assess uniqueness against common patterns
        uniqueness_prompt = f"""Rate the uniqueness of this technical content on a scale of 1-10.
        
        Features:
        - Code complexity: {features.get("code_complexity", "N/A")}
        - Patterns: {features.get("patterns_count", 0)}
        - Modern dependencies: {features.get("modern_dependencies", 0)}
        - Technical terms: {features.get("technical_terms", 0)}
        
        Consider:
        - How common are these technical approaches?
        - Does it show innovative problem-solving?
        - Are the patterns cutting-edge or standard?
        
        Respond with just a number from 1-10."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": uniqueness_prompt}],
                temperature=0.3,
                max_tokens=10,
            )

            score = float(response.choices[0].message.content.strip())
            return min(max(score, 1.0), 10.0)
        except Exception:
            # Fallback heuristic
            base_score = 5.0
            base_score += features.get("sophisticated_patterns", 0) * 0.8
            base_score += min(features.get("code_complexity", 0) * 0.3, 2.0)
            return min(base_score, 10.0)

    def _calculate_readability(self, content: str) -> float:
        """Calculate readability score"""

        # Multiple readability metrics
        flesch_ease = textstat.flesch_reading_ease(content)
        textstat.flesch_kincaid_grade(content)

        # Convert to 1-10 scale
        # Flesch Reading Ease: 0-100 (higher is better)
        readability_score = flesch_ease / 10

        # Adjust for technical content (technical content can be less readable but still valuable)
        technical_adjustment = min(content.count("```") * 0.5, 2.0)
        readability_score += technical_adjustment

        return min(max(readability_score, 1.0), 10.0)

    async def _predict_engagement(
        self, features: Dict[str, Any], platform: Platform
    ) -> float:
        """Predict engagement potential"""

        base_score = 5.0

        # Title engagement factors
        if features.get("title_has_numbers"):
            base_score += 0.8
        if features.get("title_has_question"):
            base_score += 0.6
        if features.get("title_has_how"):
            base_score += 0.7

        # Content engagement factors
        base_score += min(features.get("questions", 0) * 0.2, 1.0)
        base_score += min(features.get("lists", 0) * 0.1, 1.0)
        base_score += min(
            features.get("first_person", 0) * 0.1, 1.5
        )  # Personal stories

        # Code examples boost engagement
        base_score += min(features.get("code_examples_count", 0) * 0.4, 2.0)

        # Platform-specific adjustments
        if platform == Platform.LINKEDIN:
            base_score += features.get("platform_prefers_professional", 1.0) - 1.0
        elif platform == Platform.TWITTER:
            base_score += features.get("platform_prefers_trendy", 1.0) - 1.0

        # Read time sweet spot (7-12 minutes for technical content)
        read_time = features.get("estimated_read_time", 5)
        if 7 <= read_time <= 12:
            base_score += 1.0
        elif read_time > 15:
            base_score -= 0.5

        return min(base_score, 10.0)

    def _calculate_trend_alignment(
        self, content: ArticleContent, platform: Platform
    ) -> float:
        """Calculate alignment with current trends"""

        text = (
            f"{content.title} {content.subtitle or ''} {' '.join(content.tags)}".lower()
        )

        trend_score = 0.0
        total_weight = 0.0

        # Weight trends by current relevance
        trend_weights = {
            "ai_ml": 2.0,  # High weight for AI/ML content
            "cloud_native": 1.5,
            "devops": 1.3,
            "performance": 1.2,
            "security": 1.1,
        }

        for trend_category, keywords in self.trending_keywords.items():
            weight = trend_weights.get(trend_category, 1.0)
            matches = sum(1 for keyword in keywords if keyword in text)

            if matches > 0:
                trend_score += min(matches * weight * 2, 2.0)  # Cap per category

            total_weight += weight

        # Normalize to 1-10 scale
        if total_weight > 0:
            normalized_score = (trend_score / total_weight) * 10
        else:
            normalized_score = 5.0

        return min(max(normalized_score, 1.0), 10.0)

    def _get_platform_weights(self, platform: Platform) -> Dict[str, float]:
        """Get scoring weights for different platforms"""

        weights = {
            Platform.DEVTO: {
                "technical": 0.25,
                "uniqueness": 0.20,
                "readability": 0.25,
                "engagement": 0.20,
                "trends": 0.10,
            },
            Platform.LINKEDIN: {
                "technical": 0.20,
                "uniqueness": 0.15,
                "readability": 0.20,
                "engagement": 0.30,
                "trends": 0.15,
            },
            Platform.TWITTER: {
                "technical": 0.15,
                "uniqueness": 0.20,
                "readability": 0.15,
                "engagement": 0.35,
                "trends": 0.15,
            },
        }

        return weights.get(platform, weights[Platform.DEVTO])

    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate prediction confidence based on feature completeness"""

        essential_features = [
            "word_count",
            "technical_terms",
            "code_blocks",
            "title_length",
            "code_examples_count",
        ]

        available_features = sum(
            1 for feature in essential_features if feature in features
        )
        base_confidence = available_features / len(essential_features)

        # Boost confidence with more data
        if features.get("code_complexity", 0) > 0:
            base_confidence += 0.1
        if features.get("test_coverage", 0) > 0:
            base_confidence += 0.1
        if features.get("patterns_count", 0) > 0:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in text"""

        technical_terms = [
            "api",
            "kubernetes",
            "docker",
            "microservices",
            "async",
            "await",
            "database",
            "sql",
            "nosql",
            "redis",
            "postgresql",
            "mongodb",
            "fastapi",
            "django",
            "flask",
            "react",
            "vue",
            "angular",
            "git",
            "ci/cd",
            "devops",
            "monitoring",
            "logging",
            "metrics",
            "authentication",
            "authorization",
            "jwt",
            "oauth",
            "ssl",
            "tls",
            "algorithm",
            "complexity",
            "optimization",
            "performance",
            "scalability",
            "ai",
            "ml",
            "neural",
            "model",
            "training",
            "inference",
        ]

        text_lower = text.lower()
        return sum(1 for term in technical_terms if term in text_lower)

    def _load_historical_data(self) -> pd.DataFrame:
        """Load historical performance data (placeholder)"""

        # In production, this would load from database
        # For now, return empty DataFrame
        return pd.DataFrame()

    async def update_model_with_feedback(
        self,
        article_id: str,
        predicted_score: InsightScore,
        actual_metrics: Dict[str, float],
    ) -> None:
        """Update prediction models with actual performance feedback"""

        logger.info(
            "Updating model with feedback",
            article_id=article_id,
            predicted_overall=predicted_score.overall_score,
        )

        # In production, this would:
        # 1. Store the feedback in database
        # 2. Retrain models periodically
        # 3. Adjust prediction algorithms

        # For now, just log the feedback
        feedback = {
            "article_id": article_id,
            "predicted": predicted_score.overall_score,
            "actual_engagement": actual_metrics.get("engagement_rate", 0),
            "actual_views": actual_metrics.get("views", 0),
            "actual_shares": actual_metrics.get("shares", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info("Model feedback recorded", feedback=feedback)

    async def get_improvement_suggestions(
        self, content: ArticleContent, score: InsightScore
    ) -> List[str]:
        """Generate suggestions to improve article quality"""

        suggestions = []

        # Technical depth suggestions
        if score.technical_depth < 7:
            suggestions.append(
                "Add more technical details and code examples to increase depth"
            )
            suggestions.append(
                "Include architecture diagrams or system design explanations"
            )

        # Uniqueness suggestions
        if score.uniqueness < 6:
            suggestions.append(
                "Focus on unique aspects of your implementation or novel solutions"
            )
            suggestions.append(
                "Share personal insights and lessons learned that others might not know"
            )

        # Readability suggestions
        if score.readability < 6:
            suggestions.append("Break up long paragraphs and add more subheadings")
            suggestions.append(
                "Add code comments and explanations for complex examples"
            )

        # Engagement suggestions
        if score.engagement_potential < 7:
            suggestions.append("Start with a compelling hook or relatable problem")
            suggestions.append(
                "Add personal anecdotes and 'war stories' from your experience"
            )
            suggestions.append("Include questions to encourage reader interaction")

        # Trend alignment suggestions
        if score.trend_alignment < 6:
            suggestions.append(
                "Connect your solution to current trends like AI/ML or cloud-native technologies"
            )
            suggestions.append("Mention how your approach addresses modern challenges")

        return suggestions[:5]  # Limit to top 5 suggestions
