"""RAG Quality Evaluation and Monitoring System."""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics

import numpy as np
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer

from services.rag_pipeline.core.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for RAG evaluation metrics."""

    # Retrieval metrics
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mrr: Optional[float] = None  # Mean Reciprocal Rank
    ndcg: Optional[float] = None  # Normalized Discounted Cumulative Gain

    # Answer quality metrics
    relevance_score: Optional[float] = None
    faithfulness_score: Optional[float] = None
    answer_relevance: Optional[float] = None
    context_recall: Optional[float] = None

    # Text similarity metrics
    bleu_score: Optional[float] = None
    rouge_score: Optional[float] = None

    # Metadata
    evaluation_time: datetime = None
    query_id: Optional[str] = None

    def __post_init__(self):
        if self.evaluation_time is None:
            self.evaluation_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "mrr": self.mrr,
            "ndcg": self.ndcg,
            "relevance_score": self.relevance_score,
            "faithfulness_score": self.faithfulness_score,
            "answer_relevance": self.answer_relevance,
            "context_recall": self.context_recall,
            "bleu_score": self.bleu_score,
            "rouge_score": self.rouge_score,
            "evaluation_time": self.evaluation_time.isoformat(),
            "query_id": self.query_id,
        }


class RelevanceScorer:
    """Evaluates relevance of retrieved contexts to query."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """Initialize relevance scorer."""
        self.embedding_service = embedding_service

    async def score_contexts(self, query: str, contexts: List[str]) -> List[float]:
        """Score relevance of contexts to query using semantic similarity."""
        if not self.embedding_service:
            # Fallback to lexical similarity
            return [self._lexical_similarity(query, context) for context in contexts]

        try:
            # Get embeddings for query and contexts
            query_embedding = await self.embedding_service.embed_text(query)
            context_embeddings = await self.embedding_service.embed_batch(contexts)

            # Calculate cosine similarities
            similarities = []
            for context_emb in context_embeddings:
                similarity = self._cosine_similarity(query_embedding, context_emb)
                similarities.append(max(0.0, similarity))  # Ensure non-negative

            return similarities

        except Exception as e:
            logger.warning(f"Error calculating semantic similarity: {e}")
            # Fallback to lexical similarity
            return [self._lexical_similarity(query, context) for context in contexts]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

        if norm_product == 0:
            return 0.0

        return dot_product / norm_product

    def _lexical_similarity(self, query: str, context: str) -> float:
        """Calculate lexical similarity using word overlap."""
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())

        if not query_words or not context_words:
            return 0.0

        intersection = query_words.intersection(context_words)
        union = query_words.union(context_words)

        return len(intersection) / len(union) if union else 0.0


class FaithfulnessScorer:
    """Evaluates faithfulness of generated answers to source context."""

    def __init__(self, llm_client: Optional[Any] = None):
        """Initialize faithfulness scorer."""
        self.llm_client = llm_client

    async def score_faithfulness(self, context: str, answer: str) -> float:
        """Score faithfulness of answer to context."""
        if self.llm_client:
            return await self._llm_based_faithfulness(context, answer)
        else:
            return self._heuristic_faithfulness(context, answer)

    async def _llm_based_faithfulness(self, context: str, answer: str) -> float:
        """Use LLM to evaluate faithfulness."""
        prompt = f"""
        Evaluate if the answer is faithful to the given context. 
        Return a score from 0.0 to 1.0 where:
        - 1.0 = Answer is completely faithful to context
        - 0.5 = Answer is partially faithful 
        - 0.0 = Answer contradicts or ignores context
        
        Context: {context}
        Answer: {answer}
        
        Score (0.0-1.0):
        """

        try:
            response = self.llm_client.chat(prompt)
            # Extract numeric score from response
            score_match = re.search(r"(\d+\.?\d*)", response)
            if score_match:
                score = float(score_match.group(1))
                return min(1.0, max(0.0, score))
            return 0.5  # Default if parsing fails
        except Exception as e:
            logger.warning(f"LLM faithfulness evaluation failed: {e}")
            return self._heuristic_faithfulness(context, answer)

    def _heuristic_faithfulness(self, context: str, answer: str) -> float:
        """Heuristic faithfulness evaluation based on fact overlap."""
        # Extract key facts/entities from context and answer
        context_facts = self._extract_facts(context)
        answer_facts = self._extract_facts(answer)

        if not answer_facts:
            return 0.5  # Neutral if no facts in answer

        # Check how many answer facts are supported by context
        supported_facts = 0
        for answer_fact in answer_facts:
            if any(
                self._fact_similarity(answer_fact, context_fact) > 0.7
                for context_fact in context_facts
            ):
                supported_facts += 1

        return supported_facts / len(answer_facts) if answer_facts else 0.5

    def _extract_facts(self, text: str) -> List[str]:
        """Extract key facts/statements from text."""
        # Simple fact extraction based on sentences
        sentences = re.split(r"[.!?]+", text)
        facts = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filter out very short sentences
                facts.append(sentence)

        return facts

    def _fact_similarity(self, fact1: str, fact2: str) -> float:
        """Calculate similarity between two facts."""
        # Simple word overlap similarity
        words1 = set(fact1.lower().split())
        words2 = set(fact2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


class AnswerRelevanceScorer:
    """Evaluates relevance of generated answer to original query."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """Initialize answer relevance scorer."""
        self.embedding_service = embedding_service

    async def score_answer_relevance(self, query: str, answer: str) -> float:
        """Score how well the answer addresses the query."""
        if self.embedding_service:
            try:
                query_emb = await self.embedding_service.embed_text(query)
                answer_emb = await self.embedding_service.embed_text(answer)

                similarity = self._cosine_similarity(query_emb, answer_emb)
                return max(0.0, similarity)
            except Exception as e:
                logger.warning(f"Error calculating answer relevance: {e}")

        # Fallback to lexical similarity
        return self._lexical_relevance(query, answer)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

        if norm_product == 0:
            return 0.0

        return dot_product / norm_product

    def _lexical_relevance(self, query: str, answer: str) -> float:
        """Calculate lexical relevance using word overlap."""
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        if not query_words or not answer_words:
            return 0.0

        intersection = query_words.intersection(answer_words)
        return len(intersection) / len(query_words) if query_words else 0.0


class ContextRecallScorer:
    """Evaluates how well the answer captures information from relevant context."""

    async def score_context_recall(self, context: List[str], answer: str) -> float:
        """Score how much relevant context information is captured in answer."""
        if not context:
            return 0.0

        # Combine all context
        combined_context = " ".join(context)

        # Extract key information from context
        context_info = self._extract_key_information(combined_context)
        answer_info = self._extract_key_information(answer)

        if not context_info:
            return 0.5  # Neutral if no extractable info

        # Calculate recall: how much context info is in answer
        recalled_info = 0
        for ctx_info in context_info:
            if any(
                self._info_similarity(ctx_info, ans_info) > 0.6
                for ans_info in answer_info
            ):
                recalled_info += 1

        return recalled_info / len(context_info) if context_info else 0.0

    def _extract_key_information(self, text: str) -> List[str]:
        """Extract key information points from text."""
        # Simple extraction of sentences with key indicators
        sentences = re.split(r"[.!?]+", text)
        key_info = []

        # Look for sentences with numbers, names, or key concepts
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and (
                re.search(r"\d+", sentence)  # Contains numbers
                or re.search(r"[A-Z][a-z]+ [A-Z][a-z]+", sentence)  # Contains names
                or any(
                    keyword in sentence.lower()
                    for keyword in [
                        "is",
                        "are",
                        "was",
                        "were",
                        "defined",
                        "means",
                        "called",
                    ]
                )
            ):
                key_info.append(sentence)

        return key_info

    def _info_similarity(self, info1: str, info2: str) -> float:
        """Calculate similarity between information points."""
        words1 = set(info1.lower().split())
        words2 = set(info2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


class RAGEvaluator:
    """Main RAG evaluation system."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        llm_client: Optional[Any] = None,
    ):
        """Initialize RAG evaluator."""
        self.embedding_service = embedding_service
        self.llm_client = llm_client

        # Initialize scorers
        self.relevance_scorer = RelevanceScorer(embedding_service)
        self.faithfulness_scorer = FaithfulnessScorer(llm_client)
        self.answer_relevance_scorer = AnswerRelevanceScorer(embedding_service)
        self.context_recall_scorer = ContextRecallScorer()

    async def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        ground_truth_docs: Optional[List[Dict[str, Any]]] = None,
    ) -> EvaluationMetrics:
        """Evaluate retrieval quality."""
        metrics = EvaluationMetrics()

        if not retrieved_docs:
            return metrics

        # Extract content from documents
        retrieved_contents = [doc.get("content", "") for doc in retrieved_docs]

        # Calculate relevance scores
        relevance_scores = await self.relevance_scorer.score_contexts(
            query, retrieved_contents
        )

        # Calculate ranking metrics
        metrics.mrr = self._calculate_mrr(relevance_scores, threshold=0.5)
        metrics.ndcg = self._calculate_ndcg(relevance_scores, k=len(relevance_scores))

        # Calculate precision/recall if ground truth is available
        if ground_truth_docs:
            gt_contents = [doc.get("content", "") for doc in ground_truth_docs]
            precision, recall, f1 = await self._calculate_precision_recall(
                retrieved_contents, gt_contents
            )
            metrics.precision = precision
            metrics.recall = recall
            metrics.f1_score = f1

        return metrics

    async def evaluate_answer_quality(
        self,
        query: str,
        context: List[str],
        generated_answer: str,
        reference_answer: Optional[str] = None,
    ) -> EvaluationMetrics:
        """Evaluate generated answer quality."""
        metrics = EvaluationMetrics()

        # Evaluate answer relevance to query
        metrics.answer_relevance = (
            await self.answer_relevance_scorer.score_answer_relevance(
                query, generated_answer
            )
        )

        # Evaluate faithfulness to context
        if context:
            combined_context = " ".join(context)
            metrics.faithfulness_score = (
                await self.faithfulness_scorer.score_faithfulness(
                    combined_context, generated_answer
                )
            )

            # Evaluate context recall
            metrics.context_recall = (
                await self.context_recall_scorer.score_context_recall(
                    context, generated_answer
                )
            )

        # Calculate relevance score (average of answer relevance and faithfulness)
        if (
            metrics.answer_relevance is not None
            and metrics.faithfulness_score is not None
        ):
            metrics.relevance_score = (
                metrics.answer_relevance + metrics.faithfulness_score
            ) / 2

        # Calculate text similarity metrics if reference is available
        if reference_answer:
            metrics.bleu_score = self._calculate_bleu_score(
                generated_answer, reference_answer
            )
            metrics.rouge_score = self._calculate_rouge_score(
                generated_answer, reference_answer
            )

        return metrics

    async def evaluate_end_to_end(
        self, test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate complete RAG pipeline end-to-end."""
        results = []

        for case in test_cases:
            query = case["query"]
            context = case.get("context", [])
            generated_answer = case.get("generated_answer", "")
            reference_answer = case.get("reference_answer")
            retrieved_docs = case.get("retrieved_docs", [])

            # Evaluate retrieval if documents provided
            retrieval_metrics = None
            if retrieved_docs:
                retrieval_metrics = await self.evaluate_retrieval(query, retrieved_docs)

            # Evaluate answer quality
            answer_metrics = await self.evaluate_answer_quality(
                query, context, generated_answer, reference_answer
            )

            # Calculate overall score
            overall_score = self._calculate_overall_score(
                retrieval_metrics, answer_metrics
            )

            results.append(
                {
                    "query": query,
                    "retrieval_metrics": retrieval_metrics.to_dict()
                    if retrieval_metrics
                    else None,
                    "answer_metrics": answer_metrics.to_dict(),
                    "overall_score": overall_score,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return results

    async def batch_evaluate(
        self, test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple test cases in batch."""
        # Use asyncio to evaluate cases concurrently
        tasks = []
        batch_size = 5  # Limit concurrent evaluations

        for i in range(0, len(test_cases), batch_size):
            batch = test_cases[i : i + batch_size]
            tasks.append(self.evaluate_end_to_end(batch))

        batch_results = await asyncio.gather(*tasks)

        # Flatten results
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)

        return results

    def get_aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregate metrics from multiple evaluation results."""
        if not results:
            return {}

        # Extract all metric values
        overall_scores = [
            r["overall_score"] for r in results if r["overall_score"] is not None
        ]
        relevance_scores = []
        faithfulness_scores = []
        answer_relevance_scores = []

        for result in results:
            answer_metrics = result.get("answer_metrics", {})
            if answer_metrics.get("relevance_score") is not None:
                relevance_scores.append(answer_metrics["relevance_score"])
            if answer_metrics.get("faithfulness_score") is not None:
                faithfulness_scores.append(answer_metrics["faithfulness_score"])
            if answer_metrics.get("answer_relevance") is not None:
                answer_relevance_scores.append(answer_metrics["answer_relevance"])

        # Calculate averages
        aggregates = {
            "total_evaluations": len(results),
            "avg_overall_score": statistics.mean(overall_scores)
            if overall_scores
            else 0,
            "std_overall_score": statistics.stdev(overall_scores)
            if len(overall_scores) > 1
            else 0,
            "avg_relevance": statistics.mean(relevance_scores)
            if relevance_scores
            else 0,
            "avg_faithfulness": statistics.mean(faithfulness_scores)
            if faithfulness_scores
            else 0,
            "avg_answer_relevance": statistics.mean(answer_relevance_scores)
            if answer_relevance_scores
            else 0,
        }

        return aggregates

    async def evaluate_context_relevance(
        self, query: str, contexts: List[str]
    ) -> List[float]:
        """Evaluate relevance of each context to the query."""
        return await self.relevance_scorer.score_contexts(query, contexts)

    async def detect_hallucination(self, context: List[str], answer: str) -> float:
        """Detect hallucination in generated answer."""
        combined_context = " ".join(context) if isinstance(context, list) else context
        return await self.faithfulness_scorer.score_faithfulness(
            combined_context, answer
        )

    def _calculate_bleu_score(self, candidate: str, reference: str) -> float:
        """Calculate BLEU score between candidate and reference."""
        try:
            candidate_tokens = candidate.lower().split()
            reference_tokens = [
                reference.lower().split()
            ]  # BLEU expects list of references

            if not candidate_tokens or not reference_tokens[0]:
                return 0.0

            score = sentence_bleu(reference_tokens, candidate_tokens)
            return score
        except Exception as e:
            logger.warning(f"Error calculating BLEU score: {e}")
            return 0.0

    def _calculate_rouge_score(self, candidate: str, reference: str) -> float:
        """Calculate ROUGE score between candidate and reference."""
        try:
            scorer = rouge_scorer.RougeScorer(["rouge1"], use_stemmer=True)
            scores = scorer.score(reference, candidate)
            return scores["rouge1"].fmeasure
        except Exception as e:
            logger.warning(f"Error calculating ROUGE score: {e}")
            return 0.0

    def _calculate_mrr(
        self, relevance_scores: List[float], threshold: float = 0.5
    ) -> float:
        """Calculate Mean Reciprocal Rank."""
        for i, score in enumerate(relevance_scores):
            if score >= threshold:
                return 1.0 / (i + 1)
        return 0.0

    def _calculate_ndcg(self, relevance_scores: List[float], k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain."""
        if not relevance_scores:
            return 0.0

        # Calculate DCG
        dcg = 0.0
        for i, score in enumerate(relevance_scores[:k]):
            if i == 0:
                dcg += score
            else:
                dcg += score / np.log2(i + 1)

        # Calculate IDCG (ideal DCG)
        ideal_scores = sorted(relevance_scores[:k], reverse=True)
        idcg = 0.0
        for i, score in enumerate(ideal_scores):
            if i == 0:
                idcg += score
            else:
                idcg += score / np.log2(i + 1)

        return dcg / idcg if idcg > 0 else 0.0

    async def _calculate_precision_recall(
        self, retrieved: List[str], ground_truth: List[str]
    ) -> Tuple[float, float, float]:
        """Calculate precision, recall, and F1 score."""
        if not retrieved or not ground_truth:
            return 0.0, 0.0, 0.0

        # Use semantic similarity to match retrieved with ground truth
        relevant_retrieved = 0

        for ret_doc in retrieved:
            # Check if this retrieved doc matches any ground truth doc
            ret_embedding = (
                await self.embedding_service.embed_text(ret_doc)
                if self.embedding_service
                else None
            )

            for gt_doc in ground_truth:
                if ret_embedding and self.embedding_service:
                    gt_embedding = await self.embedding_service.embed_text(gt_doc)
                    similarity = self._cosine_similarity(ret_embedding, gt_embedding)
                    if similarity > 0.7:  # Threshold for relevance
                        relevant_retrieved += 1
                        break
                else:
                    # Fallback to lexical similarity
                    if self._lexical_similarity(ret_doc, gt_doc) > 0.5:
                        relevant_retrieved += 1
                        break

        precision = relevant_retrieved / len(retrieved) if retrieved else 0.0
        recall = relevant_retrieved / len(ground_truth) if ground_truth else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return precision, recall, f1

    def _lexical_similarity(self, text1: str, text2: str) -> float:
        """Calculate lexical similarity using word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

        if norm_product == 0:
            return 0.0

        return dot_product / norm_product

    def _calculate_overall_score(
        self,
        retrieval_metrics: Optional[EvaluationMetrics],
        answer_metrics: EvaluationMetrics,
    ) -> float:
        """Calculate overall RAG pipeline score."""
        scores = []

        # Weight retrieval metrics (30%)
        if retrieval_metrics:
            retrieval_score = 0.0
            count = 0

            if retrieval_metrics.mrr is not None:
                retrieval_score += retrieval_metrics.mrr
                count += 1
            if retrieval_metrics.ndcg is not None:
                retrieval_score += retrieval_metrics.ndcg
                count += 1

            if count > 0:
                scores.append(("retrieval", retrieval_score / count, 0.3))

        # Weight answer metrics (70%)
        answer_score = 0.0
        count = 0

        if answer_metrics.relevance_score is not None:
            answer_score += answer_metrics.relevance_score
            count += 1
        if answer_metrics.faithfulness_score is not None:
            answer_score += answer_metrics.faithfulness_score
            count += 1
        if answer_metrics.answer_relevance is not None:
            answer_score += answer_metrics.answer_relevance
            count += 1

        if count > 0:
            scores.append(("answer", answer_score / count, 0.7))

        # Calculate weighted average
        if not scores:
            return 0.0

        weighted_sum = sum(score * weight for _, score, weight in scores)
        total_weight = sum(weight for _, _, weight in scores)

        return weighted_sum / total_weight if total_weight > 0 else 0.0
