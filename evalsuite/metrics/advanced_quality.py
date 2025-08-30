#!/usr/bin/env python3
"""
Advanced Quality Scoring - Granular Business Content Evaluation

Implements sophisticated quality metrics that distinguish between models
with fine-grained scoring across multiple dimensions.
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class QualityScore:
    """Detailed quality assessment results."""
    total_score: float
    max_score: float
    dimension_scores: Dict[str, float]
    detailed_feedback: List[str]
    
    @property
    def percentage(self) -> float:
        return (self.total_score / self.max_score) * 100 if self.max_score > 0 else 0


class AdvancedQualityScorer:
    """
    Professional content quality scorer with granular evaluation.
    
    Evaluates business content across 8 detailed dimensions:
    - Content Relevance (0-20 points)
    - Professional Tone (0-15 points)  
    - Structure & Format (0-15 points)
    - Clarity & Coherence (0-15 points)
    - Specificity & Value (0-15 points)
    - LinkedIn Appropriateness (0-10 points)
    - Grammar & Style (0-5 points)
    - Engagement Potential (0-5 points)
    
    Total: 100 points maximum
    """
    
    def __init__(self):
        self.business_keywords = {
            'strong': ['innovation', 'strategy', 'growth', 'efficiency', 'transformation', 
                      'optimization', 'competitive', 'scalability', 'ROI', 'productivity'],
            'medium': ['business', 'technology', 'future', 'improve', 'success', 
                      'solution', 'development', 'management', 'opportunity', 'industry'],
            'weak': ['work', 'company', 'team', 'help', 'good', 'new', 'better', 'use']
        }
        
        self.professional_indicators = [
            'professionals', 'colleagues', 'industry', 'market', 'enterprise',
            'organizations', 'leadership', 'stakeholders', 'clients', 'customers'
        ]
        
        self.engagement_signals = [
            '?', '!', 'share your', 'what do you think', 'thoughts?', 'agree?',
            'experience', 'comment', 'insights', 'perspective'
        ]

    def evaluate_content_relevance(self, text: str, prompt: str) -> Tuple[float, List[str]]:
        """
        Score content relevance to the prompt (0-20 points).
        Analyzes how well content addresses the specific request.
        """
        score = 0.0
        feedback = []
        
        text_lower = text.lower()
        prompt_lower = prompt.lower()
        
        # Extract key topics from prompt
        if 'ai' in prompt_lower and 'business' in prompt_lower:
            if 'ai' in text_lower and 'business' in text_lower:
                score += 8
                feedback.append("✓ Addresses AI in business context")
            elif 'ai' in text_lower or 'business' in text_lower:
                score += 4
                feedback.append("⚠ Partially addresses topic")
            else:
                feedback.append("✗ Missing key topic focus")
        
        # LinkedIn post format recognition
        if 'linkedin post' in prompt_lower:
            if len(text.split()) > 10 and ('.' in text or '!' in text):
                score += 6
                feedback.append("✓ Appropriate post length and format")
            else:
                score += 2
                feedback.append("⚠ Basic post format")
        
        # Content depth
        if len(text.split()) >= 30:
            score += 4
            feedback.append("✓ Sufficient content depth")
        elif len(text.split()) >= 15:
            score += 2
            feedback.append("⚠ Minimal content depth")
        else:
            feedback.append("✗ Insufficient content depth")
        
        # Future-focused analysis (if prompt mentions "future")
        if 'future' in prompt_lower:
            future_indicators = ['will', 'future', 'next', 'coming', 'ahead', 'tomorrow', 'evolving']
            if any(word in text_lower for word in future_indicators):
                score += 2
                feedback.append("✓ Addresses future perspective")
        
        return min(score, 20), feedback

    def evaluate_professional_tone(self, text: str) -> Tuple[float, List[str]]:
        """Score professional tone and language (0-15 points)."""
        score = 0.0
        feedback = []
        
        text_lower = text.lower()
        
        # Professional vocabulary
        strong_count = sum(1 for word in self.business_keywords['strong'] if word in text_lower)
        medium_count = sum(1 for word in self.business_keywords['medium'] if word in text_lower)
        
        if strong_count >= 2:
            score += 6
            feedback.append(f"✓ Strong business vocabulary ({strong_count} terms)")
        elif strong_count >= 1 or medium_count >= 3:
            score += 4
            feedback.append("✓ Good business vocabulary")
        elif medium_count >= 1:
            score += 2
            feedback.append("⚠ Basic business vocabulary")
        else:
            feedback.append("✗ Lacks professional vocabulary")
        
        # Professional audience indicators
        prof_count = sum(1 for word in self.professional_indicators if word in text_lower)
        if prof_count >= 1:
            score += 3
            feedback.append("✓ Professional audience awareness")
        
        # Avoid overly casual language
        casual_words = ['awesome', 'cool', 'amazing', 'super', 'totally', 'really really']
        casual_count = sum(1 for word in casual_words if word in text_lower)
        if casual_count == 0:
            score += 3
            feedback.append("✓ Appropriate formality level")
        else:
            score += 1
            feedback.append("⚠ Some casual language detected")
        
        # Professional confidence (avoid hedging)
        hedge_words = ['maybe', 'perhaps', 'probably', 'might be', 'could be']
        hedge_count = sum(1 for word in hedge_words if word in text_lower)
        if hedge_count == 0:
            score += 3
            feedback.append("✓ Confident professional tone")
        elif hedge_count <= 1:
            score += 2
            feedback.append("⚠ Minor hedging detected")
        else:
            feedback.append("✗ Excessive hedging undermines authority")
        
        return min(score, 15), feedback

    def evaluate_structure_format(self, text: str) -> Tuple[float, List[str]]:
        """Score content structure and formatting (0-15 points)."""
        score = 0.0
        feedback = []
        
        # Sentence structure
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) >= 3:
            score += 4
            feedback.append("✓ Good sentence structure")
        elif len(sentences) >= 2:
            score += 2
            feedback.append("⚠ Basic sentence structure")
        else:
            feedback.append("✗ Poor sentence structure")
        
        # Opening strength
        if sentences:
            first_sentence = sentences[0].lower()
            if any(word in first_sentence for word in ['future', 'ai', 'business', 'innovation']):
                score += 3
                feedback.append("✓ Strong topic-focused opening")
            elif len(first_sentence.split()) >= 5:
                score += 2
                feedback.append("⚠ Adequate opening")
            else:
                feedback.append("✗ Weak opening")
        
        # Paragraph structure (for longer content)
        if len(text.split()) > 50:
            if '\n' in text or text.count('.') >= 3:
                score += 3
                feedback.append("✓ Good paragraph structure")
            else:
                score += 1
                feedback.append("⚠ Wall of text - needs structure")
        
        # LinkedIn-specific format recognition
        if text.startswith('Title:') or ':' in text[:20]:
            score += 2
            feedback.append("✓ Professional title format")
        
        # Proper punctuation
        if text.endswith(('.', '!', '?')):
            score += 2
            feedback.append("✓ Proper ending punctuation")
        
        # Capitalization
        if text[0].isupper() if text else False:
            score += 1
            feedback.append("✓ Proper capitalization")
        
        return min(score, 15), feedback

    def evaluate_clarity_coherence(self, text: str) -> Tuple[float, List[str]]:
        """Score clarity and logical flow (0-15 points)."""
        score = 0.0
        feedback = []
        
        # Repetition analysis
        words = text.lower().split()
        if len(words) > 5:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Check for excessive repetition
            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq <= len(words) * 0.2:  # No word appears more than 20% of the time
                score += 5
                feedback.append("✓ No excessive repetition")
            else:
                score += 2
                feedback.append("⚠ Some repetitive language")
        
        # Coherence indicators
        transition_words = ['however', 'therefore', 'furthermore', 'additionally', 'meanwhile', 
                           'consequently', 'moreover', 'also', 'for example', 'in fact']
        if any(word in text.lower() for word in transition_words):
            score += 3
            feedback.append("✓ Good use of transitions")
        
        # Clear statements vs questions
        question_count = text.count('?')
        statement_count = text.count('.') + text.count('!')
        
        if statement_count >= question_count * 2:
            score += 4
            feedback.append("✓ Clear declarative content")
        elif statement_count >= question_count:
            score += 2
            feedback.append("⚠ Balanced statements and questions")
        else:
            feedback.append("✗ Too many questions, lacks clear statements")
        
        # Length appropriateness
        word_count = len(words)
        if 30 <= word_count <= 100:
            score += 3
            feedback.append("✓ Optimal length for LinkedIn")
        elif 20 <= word_count <= 150:
            score += 2
            feedback.append("⚠ Acceptable length")
        else:
            feedback.append("✗ Inappropriate length")
        
        return min(score, 15), feedback

    def evaluate_specificity_value(self, text: str) -> Tuple[float, List[str]]:
        """Score specific insights and practical value (0-15 points)."""
        score = 0.0
        feedback = []
        
        # Specific examples or concrete details
        concrete_indicators = ['example', 'instance', 'case', 'such as', 'including', 'like']
        if any(word in text.lower() for word in concrete_indicators):
            score += 4
            feedback.append("✓ Provides concrete examples")
        
        # Numbers and statistics
        if re.search(r'\d+%|\d+\s*(billion|million|thousand)', text):
            score += 3
            feedback.append("✓ Includes quantitative data")
        elif re.search(r'\d+', text):
            score += 2
            feedback.append("⚠ Some numerical content")
        
        # Actionable insights
        action_words = ['should', 'must', 'need to', 'recommend', 'suggest', 'implement', 'adopt']
        if any(word in text.lower() for word in action_words):
            score += 4
            feedback.append("✓ Provides actionable insights")
        
        # Value propositions
        value_words = ['benefit', 'advantage', 'improvement', 'solution', 'opportunity', 'potential']
        if any(word in text.lower() for word in value_words):
            score += 2
            feedback.append("✓ Mentions value/benefits")
        
        # Avoid generic statements
        generic_phrases = ['is important', 'very good', 'really helpful', 'makes sense']
        generic_count = sum(1 for phrase in generic_phrases if phrase in text.lower())
        if generic_count == 0:
            score += 2
            feedback.append("✓ Avoids generic statements")
        else:
            feedback.append("⚠ Contains some generic language")
        
        return min(score, 15), feedback

    def evaluate_linkedin_appropriateness(self, text: str) -> Tuple[float, List[str]]:
        """Score appropriateness for LinkedIn platform (0-10 points)."""
        score = 0.0
        feedback = []
        
        # Professional networking context
        network_words = ['network', 'connect', 'professional', 'colleague', 'industry', 'career']
        if any(word in text.lower() for word in network_words):
            score += 3
            feedback.append("✓ LinkedIn networking context")
        
        # Business focus
        if any(word in text.lower() for word in ['business', 'industry', 'market', 'corporate']):
            score += 2
            feedback.append("✓ Business-focused content")
        
        # Thought leadership tone
        thought_leadership = ['insight', 'perspective', 'experience', 'believe', 'opinion', 'view']
        if any(word in text.lower() for word in thought_leadership):
            score += 2
            feedback.append("✓ Thought leadership tone")
        
        # Appropriate length for LinkedIn
        word_count = len(text.split())
        if 25 <= word_count <= 80:
            score += 3
            feedback.append("✓ Ideal LinkedIn post length")
        elif 15 <= word_count <= 120:
            score += 2
            feedback.append("⚠ Acceptable LinkedIn length")
        else:
            score += 1
            feedback.append("⚠ Non-optimal length for LinkedIn")
        
        return min(score, 10), feedback

    def evaluate_grammar_style(self, text: str) -> Tuple[float, List[str]]:
        """Score grammar and writing style (0-5 points)."""
        score = 5.0  # Start with perfect score, deduct for issues
        feedback = []
        
        # Basic grammar checks
        if not text[0].isupper() if text else True:
            score -= 1
            feedback.append("✗ Capitalization error")
        
        if not text.endswith(('.', '!', '?')) if text else True:
            score -= 1
            feedback.append("✗ Missing ending punctuation")
        
        # Check for obvious errors (simplified)
        if ' i ' in text or text.startswith('i '):
            score -= 0.5
            feedback.append("⚠ Capitalization of 'I'")
        
        # Double spaces or formatting issues
        if '  ' in text:
            score -= 0.5
            feedback.append("⚠ Spacing issues")
        
        if score == 5.0:
            feedback.append("✓ Good grammar and style")
        
        return max(score, 0), feedback

    def evaluate_engagement_potential(self, text: str) -> Tuple[float, List[str]]:
        """Score potential for audience engagement (0-5 points)."""
        score = 0.0
        feedback = []
        
        # Engagement signals
        engagement_count = sum(1 for signal in self.engagement_signals 
                             if signal.lower() in text.lower())
        
        if engagement_count >= 2:
            score += 3
            feedback.append("✓ Strong engagement signals")
        elif engagement_count >= 1:
            score += 2
            feedback.append("⚠ Some engagement elements")
        else:
            feedback.append("✗ Lacks engagement elements")
        
        # Call to action or discussion prompt
        cta_words = ['share', 'comment', 'thoughts', 'experience', 'agree', 'disagree']
        if any(word in text.lower() for word in cta_words):
            score += 2
            feedback.append("✓ Includes call to action")
        
        return min(score, 5), feedback

    def evaluate_content(self, text: str, prompt: str = "") -> QualityScore:
        """
        Comprehensive content evaluation across all dimensions.
        
        Args:
            text: Generated content to evaluate
            prompt: Original prompt for context
            
        Returns:
            QualityScore with detailed breakdown
        """
        if not text or not text.strip():
            return QualityScore(0, 100, {}, ["✗ Empty content"])
        
        dimension_scores = {}
        all_feedback = []
        
        # Evaluate each dimension
        dimensions = [
            ("Content Relevance", 20, self.evaluate_content_relevance, [text, prompt]),
            ("Professional Tone", 15, self.evaluate_professional_tone, [text]),
            ("Structure & Format", 15, self.evaluate_structure_format, [text]),
            ("Clarity & Coherence", 15, self.evaluate_clarity_coherence, [text]),
            ("Specificity & Value", 15, self.evaluate_specificity_value, [text]),
            ("LinkedIn Appropriateness", 10, self.evaluate_linkedin_appropriateness, [text]),
            ("Grammar & Style", 5, self.evaluate_grammar_style, [text]),
            ("Engagement Potential", 5, self.evaluate_engagement_potential, [text])
        ]
        
        total_score = 0
        max_total = 0
        
        for dim_name, max_score, eval_func, args in dimensions:
            try:
                score, feedback = eval_func(*args)
                dimension_scores[dim_name] = score
                total_score += score
                max_total += max_score
                
                # Add dimension header to feedback
                all_feedback.append(f"\n{dim_name} ({score:.1f}/{max_score}):")
                all_feedback.extend([f"  {fb}" for fb in feedback])
                
            except Exception as e:
                dimension_scores[dim_name] = 0
                max_total += max_score
                all_feedback.append(f"\n{dim_name} (ERROR): {str(e)}")
        
        return QualityScore(
            total_score=total_score,
            max_score=max_total,
            dimension_scores=dimension_scores,
            detailed_feedback=all_feedback
        )


def quick_quality_test():
    """Quick test of the advanced quality scorer."""
    scorer = AdvancedQualityScorer()
    
    # Test samples from our models
    samples = [
        ("TinyLlama", "Title: The Future of AI in Business: A Revolutionary Technology That Will Transform Your Industry"),
        ("BLOOM-3B", "The future of AI in business is here. We're seeing it in the form of AI-powered chatbots"),
        ("BLOOM-560M", "In the future, AI will be the core of the human brain. It will be the core of the human brain.")
    ]
    
    prompt = "Write a LinkedIn post about the future of AI in business"
    
    print("🔬 ADVANCED QUALITY SCORING TEST")
    print("=" * 50)
    
    for model, text in samples:
        result = scorer.evaluate_content(text, prompt)
        print(f"\n{model}: {result.total_score:.1f}/100 ({result.percentage:.1f}%)")
        print(f"Top dimensions: {sorted(result.dimension_scores.items(), key=lambda x: x[1], reverse=True)[:3]}")


if __name__ == "__main__":
    quick_quality_test()