#!/usr/bin/env python3
"""
Pairwise Judge - LLM-as-Judge with Deterministic Formatting

Implements pairwise comparison using OpenAI or Claude
with deterministic JSON formatting and comprehensive retry logic.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class JudgmentResult:
    """Structured judgment result."""
    winner: str  # "A", "B", or "tie"
    reasons: str
    criteria_scores: Dict[str, float]
    prompt: str
    output_a: str
    output_b: str
    judge_model: str


class PairwiseJudge:
    """LLM-as-judge for pairwise model comparison."""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini"):
        """Initialize pairwise judge."""
        self.provider = provider.lower()
        self.model = model
        self.max_retries = 3
        self.timeout_seconds = 30
        
        # Load judge prompt
        self.judge_prompt = self._load_judge_prompt()
        
        # Initialize client
        self.client = self._init_client()
    
    def _load_judge_prompt(self) -> str:
        """Load judge prompt from config."""
        prompt_path = "evalsuite/configs/judge_prompt.txt"
        try:
            with open(prompt_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Judge prompt not found: {prompt_path}")
    
    def _init_client(self):
        """Initialize API client based on provider."""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable required")
            
            try:
                import openai
                return openai.OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("OpenAI library required: pip install openai")
                
        elif self.provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable required")
            
            try:
                import anthropic
                return anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("Anthropic library required: pip install anthropic")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def judge_pair(
        self, 
        prompt: str, 
        output_a: str, 
        output_b: str, 
        task: str
    ) -> JudgmentResult:
        """Judge a pair of outputs with retry logic."""
        
        judgment_prompt = self._format_judgment_prompt(prompt, output_a, output_b, task)
        
        for attempt in range(self.max_retries):
            try:
                # Make API call based on provider
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self.judge_prompt},
                            {"role": "user", "content": judgment_prompt}
                        ],
                        temperature=0.0,  # Deterministic judging
                        timeout=self.timeout_seconds
                    )
                    
                    judgment_text = response.choices[0].message.content
                    
                elif self.provider == "claude":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=1000,
                        messages=[
                            {"role": "user", "content": f"{self.judge_prompt}\\n\\n{judgment_prompt}"}
                        ],
                        temperature=0.0
                    )
                    
                    judgment_text = response.content[0].text
                
                # Parse judgment
                judgment = self._parse_judgment(judgment_text)
                
                return JudgmentResult(
                    winner=judgment["winner"],
                    reasons=judgment["reasons"],
                    criteria_scores=judgment["criteria_scores"],
                    prompt=prompt,
                    output_a=output_a,
                    output_b=output_b,
                    judge_model=f"{self.provider}:{self.model}"
                )
                
            except Exception as e:
                print(f"   ⚠️  Judge attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    # Final attempt failed - return tie with error
                    return JudgmentResult(
                        winner="tie",
                        reasons=f"Judge failed after {self.max_retries} attempts: {e}",
                        criteria_scores={"clarity": 3, "relevance": 3, "tone": 3, "factuality": 3},
                        prompt=prompt,
                        output_a=output_a,
                        output_b=output_b,
                        judge_model=f"{self.provider}:{self.model}"
                    )
                
                time.sleep(1)  # Brief delay before retry
        
    def _format_judgment_prompt(self, prompt: str, output_a: str, output_b: str, task: str) -> str:
        """Format the judgment prompt."""
        return f"""Task: {task}

Prompt: {prompt}

Output A: {output_a}

Output B: {output_b}

Please judge which output is better according to the criteria."""
    
    def _parse_judgment(self, judgment_text: str) -> Dict[str, Any]:
        """Parse judgment with robust error handling."""
        try:
            # Try to extract JSON from response
            start_idx = judgment_text.find('{')
            end_idx = judgment_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = judgment_text[start_idx:end_idx]
                judgment = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["winner", "reasons", "criteria_scores"]
                if all(field in judgment for field in required_fields):
                    # Validate winner value
                    if judgment["winner"] in ["A", "B", "tie"]:
                        return judgment
            
            # If parsing fails, return default tie
            raise ValueError("Invalid judgment format")
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fail closed with tie
            return {
                "winner": "tie",
                "reasons": f"Parse error: {e}",
                "criteria_scores": {
                    "clarity": 3,
                    "relevance": 3, 
                    "tone": 3,
                    "factuality": 3
                }
            }


def judge_outputs_pairwise(
    outputs: List[Dict[str, Any]], 
    task: str,
    judge_config: Dict[str, Any]
) -> List[JudgmentResult]:
    """Judge all pairwise combinations of outputs."""
    
    judge = PairwiseJudge(
        provider=judge_config.get("provider", "openai"),
        model=judge_config.get("model", "gpt-4o-mini")
    )
    
    judgments = []
    
    # Generate all pairwise combinations
    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            output_a = outputs[i]
            output_b = outputs[j]
            
            print(f"   🔍 Judging: {output_a['model_id']} vs {output_b['model_id']}")
            
            judgment = judge.judge_pair(
                prompt=output_a["prompt"],
                output_a=output_a["content"],
                output_b=output_b["content"],
                task=task
            )
            
            # Add model information
            judgment.model_a = output_a["model_id"]
            judgment.model_b = output_b["model_id"]
            
            judgments.append(judgment)
    
    return judgments