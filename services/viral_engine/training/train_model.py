# services/viral_engine/training/train_model.py
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier  # type: ignore[import-not-found,import-untyped]
    from sklearn.feature_extraction.text import (
        TfidfVectorizer,  # type: ignore[import-not-found,import-untyped]
    )
    from sklearn.metrics import (  # type: ignore[import-not-found,import-untyped]
        accuracy_score,
        classification_report,
        confusion_matrix,
    )
    from sklearn.model_selection import (  # type: ignore[import-not-found,import-untyped]
        cross_val_score,
        train_test_split,
    )
except ImportError:
    # These imports might fail in mypy but will work at runtime
    pass

from services.viral_engine.feature_extractor import AdvancedFeatureExtractor


class EngagementModelTrainer:
    """
    Train engagement prediction model with >80% accuracy target.
    Uses ensemble of TF-IDF features and handcrafted features.
    """

    def __init__(self, data_path: Optional[str] = None) -> None:
        self.data_path = (
            data_path
            or Path(__file__).parent.parent
            / "data"
            / "training"
            / "threads_dataset.json"
        )
        self.model_path = Path(__file__).parent.parent / "models"
        self.model_path.mkdir(exist_ok=True)

        self.feature_extractor = AdvancedFeatureExtractor()
        self.vectorizer = TfidfVectorizer(
            max_features=500, ngram_range=(1, 2), min_df=2, stop_words="english"
        )

        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

    def load_training_data(self) -> Tuple[List[str], List[int]]:
        """Load training data from JSON file"""
        try:
            with open(self.data_path, "r") as f:
                data = json.load(f)

            texts = []
            labels = []

            for item in data:
                texts.append(item["text"])
                # Binary classification: viral (1) if ER >= 6%, non-viral (0) otherwise
                labels.append(1 if item["engagement_rate"] >= 0.06 else 0)

            print(f"Loaded {len(texts)} samples")
            print(f"Viral posts: {sum(labels)}, Non-viral: {len(labels) - sum(labels)}")

            return texts, labels

        except FileNotFoundError:
            print(f"Training data not found at {self.data_path}")
            print("Generating synthetic training data for demo...")
            return self._generate_synthetic_data()

    def _generate_synthetic_data(self) -> Tuple[List[str], List[int]]:
        """Generate synthetic training data for demo purposes"""
        viral_templates = [
            "Unpopular opinion: {} This changed everything for me.",
            "I tried {} for 30 days. Here's what happened:",
            "Stop doing {}. Do this instead: {}",
            "Everyone thinks {}. Here's why they're wrong:",
            "{} is killing your productivity. Here's the fix:",
            "The #1 mistake people make with {}: {}",
            "Why successful people {} (and you should too)",
            "I analyzed 100 {}. Here's what I found:",
            "The truth about {} nobody talks about",
            "This {} hack increased my results by 300%",
        ]

        non_viral_templates = [
            "Today I went to {} and it was okay.",
            "Just thinking about {} right now.",
            "Anyone else like {}?",
            "Had {} for lunch.",
            "Working on {} today.",
            "{} is nice I guess.",
            "Saw {} earlier.",
            "Time for some {}.",
            "Another day, another {}.",
            "Just finished {}.",
        ]

        topics = [
            "productivity",
            "AI tools",
            "morning routines",
            "content creation",
            "social media",
            "entrepreneurship",
            "mindset",
            "habits",
            "technology",
            "marketing",
            "writing",
            "learning",
        ]

        texts = []
        labels = []

        # Generate viral posts
        for _ in range(500):
            template = np.random.choice(viral_templates)
            topic = np.random.choice(topics)

            if "{}" in template:
                post = template.format(topic)
                if template.count("{}") == 2:
                    post = template.format(topic, np.random.choice(topics))
            else:
                post = template

            texts.append(post)
            labels.append(1)

        # Generate non-viral posts
        for _ in range(500):
            template = np.random.choice(non_viral_templates)
            topic = np.random.choice(topics)
            post = template.format(topic)
            texts.append(post)
            labels.append(0)

        return texts, labels

    def prepare_features(self, texts: List[str]) -> np.ndarray:
        """Prepare combined feature matrix"""
        # TF-IDF features
        tfidf_features = self.vectorizer.fit_transform(texts).toarray()

        # Handcrafted features
        handcrafted_features_list: List[List[float]] = []
        for text in texts:
            features = self.feature_extractor.extract_all_features(text)
            feature_vector = [features[k] for k in sorted(features.keys())]
            handcrafted_features_list.append(feature_vector)

        handcrafted_features = np.array(handcrafted_features_list)

        # Combine features
        combined_features = np.hstack([tfidf_features, handcrafted_features])

        print(
            f"Feature dimensions: TF-IDF={tfidf_features.shape[1]}, Handcrafted={handcrafted_features.shape[1]}"
        )
        print(f"Combined features shape: {combined_features.shape}")

        return combined_features

    def train_model(self) -> None:
        """Train the engagement prediction model"""
        print("Loading training data...")
        texts, labels = self.load_training_data()

        print("Preparing features...")
        X = self.prepare_features(texts)
        y = np.array(labels)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

        # Cross-validation
        print("\nPerforming cross-validation...")
        cv_scores = cross_val_score(
            self.model, X_train, y_train, cv=5, scoring="accuracy"
        )
        print(f"Cross-validation scores: {cv_scores}")
        print(
            f"Mean CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})"
        )

        # Train final model
        print("\nTraining final model...")
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"\nTest set accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(
            classification_report(y_test, y_pred, target_names=["Non-viral", "Viral"])
        )

        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))

        # Feature importance
        if hasattr(self.model, "feature_importances_"):
            feature_names = [
                f"tfidf_{i}"
                for i in range(
                    X.shape[1] - len(self.feature_extractor.get_feature_names())
                )
            ]
            feature_names.extend(self.feature_extractor.get_feature_names())

            importances = self.model.feature_importances_
            indices = np.argsort(importances)[::-1][:20]

            print("\nTop 20 most important features:")
            for i, idx in enumerate(indices):
                print(f"{i + 1}. {feature_names[idx]}: {importances[idx]:.4f}")

        # Save model
        self.save_model()

        if accuracy >= 0.80:
            print(f"\n✅ Model achieved target accuracy: {accuracy:.1%}")
        else:
            print(f"\n⚠️  Model accuracy {accuracy:.1%} below target 80%")

    def save_model(self) -> None:
        """Save trained model and vectorizer"""
        model_file = self.model_path / "engagement_model.pkl"
        vectorizer_file = self.model_path / "tfidf_vectorizer.pkl"

        with open(model_file, "wb") as f:
            pickle.dump(self.model, f)

        with open(vectorizer_file, "wb") as f:
            pickle.dump(self.vectorizer, f)

        print(f"\nModel saved to {model_file}")
        print(f"Vectorizer saved to {vectorizer_file}")


if __name__ == "__main__":
    trainer = EngagementModelTrainer()
    trainer.train_model()
