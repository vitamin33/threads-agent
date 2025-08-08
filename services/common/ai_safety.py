"""
AI safety and security monitoring for production systems.

Provides prompt injection detection, hallucination risk assessment,
and content safety checks for AI-generated outputs.
"""
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging
from services.common.ai_metrics import AI_PROMPT_INJECTIONS, AI_HALLUCINATION_FLAGS, AI_SECURITY_INCIDENTS

logger = logging.getLogger(__name__)


class AISecurityMonitor:
    """Monitor AI inputs and outputs for security and safety issues."""
    
    def __init__(self):
        """Initialize security monitor with detection patterns."""
        # Prompt injection patterns
        self.prompt_injection_patterns = [
            (r"ignore previous instructions", "override_attempt", "high"),
            (r"disregard all prior", "override_attempt", "high"),
            (r"system:\s*", "role_injection", "high"),
            (r"assistant:\s*", "role_injection", "high"),
            (r"forget everything above", "memory_manipulation", "high"),
            (r"new instructions:", "instruction_injection", "medium"),
            (r"act as if you", "behavior_manipulation", "medium"),
            (r"pretend to be", "identity_manipulation", "medium"),
            (r"you are now", "identity_manipulation", "medium"),
            (r"<\|.*?\|>", "special_tokens", "high"),
            (r"\[INST\].*?\[/INST\]", "special_tokens", "high"),
        ]
        
        # Hallucination risk indicators
        self.hallucination_keywords = {
            'financial': {
                'patterns': [r'\$[\d,]+(?:\.\d+)?(?:B|M|K)?', r'revenue', r'profit', r'earnings'],
                'risk_level': 'high'
            },
            'statistical': {
                'patterns': [r'\d+(?:\.\d+)?%', r'average of \d+', r'median', r'standard deviation'],
                'risk_level': 'medium'
            },
            'temporal': {
                'patterns': [r'20\d{2}', r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'],
                'risk_level': 'medium'
            },
            'medical': {
                'patterns': [r'diagnos', r'treatment', r'prescription', r'medical advice'],
                'risk_level': 'critical'
            },
            'legal': {
                'patterns': [r'legal advice', r'lawsuit', r'contract', r'liability'],
                'risk_level': 'critical'
            }
        }
        
        # Metrics tracking
        self.security_events = {
            'prompt_injections': 0,
            'hallucination_flags': 0,
            'content_violations': 0,
            'total_checks': 0
        }
        
    def check_prompt_injection(self, user_input: str, service: str = "unknown") -> Dict[str, Any]:
        """
        Detect potential prompt injection attempts.
        
        Args:
            user_input: The user's input to check
            service: Service name for metrics
            
        Returns:
            Dict with safety assessment and details
        """
        self.security_events['total_checks'] += 1
        lower_input = user_input.lower()
        detected_patterns = []
        
        for pattern, category, severity in self.prompt_injection_patterns:
            if re.search(pattern, lower_input, re.IGNORECASE):
                detected_patterns.append({
                    'pattern': pattern,
                    'category': category,
                    'severity': severity
                })
        
        if detected_patterns:
            self.security_events['prompt_injections'] += 1
            # Find highest severity
            max_severity = max(detected_patterns, key=lambda x: 
                              {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(x['severity'], 0))
            
            # Emit Prometheus metrics
            AI_PROMPT_INJECTIONS.labels(service=service, severity=max_severity['severity']).inc()
            AI_SECURITY_INCIDENTS.labels(service=service, incident_type="prompt_injection").inc()
            
            logger.warning(f"Prompt injection detected: {detected_patterns}")
            
            return {
                'safe': False,
                'risk_level': max_severity['severity'],
                'detected_patterns': detected_patterns,
                'recommendation': 'Block or sanitize input',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {
            'safe': True,
            'risk_level': 'none',
            'detected_patterns': [],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def flag_potential_hallucination(self, ai_output: str, model: str = "unknown", service: str = "unknown") -> Dict[str, Any]:
        """
        Flag outputs that might contain hallucinated facts.
        
        Args:
            ai_output: The AI-generated text to check
            model: Model name for metrics
            service: Service name for metrics
            
        Returns:
            Dict with hallucination risk assessment
        """
        flags = []
        max_risk_level = 'low'
        risk_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        
        for category, config in self.hallucination_keywords.items():
            category_matches = []
            
            for pattern in config['patterns']:
                matches = re.findall(pattern, ai_output, re.IGNORECASE)
                if matches:
                    category_matches.extend(matches)
            
            if category_matches:
                flags.append({
                    'category': category,
                    'matches': category_matches[:5],  # Limit to first 5 matches
                    'risk_level': config['risk_level']
                })
                
                # Update max risk level
                if risk_scores.get(config['risk_level'], 0) > risk_scores.get(max_risk_level, 0):
                    max_risk_level = config['risk_level']
        
        if flags:
            self.security_events['hallucination_flags'] += 1
            # Emit Prometheus metrics
            AI_HALLUCINATION_FLAGS.labels(model=model, service=service, risk_level=max_risk_level).inc()
        
        # Calculate confidence adjustment based on risk
        confidence_adjustments = {
            'low': 0.95,
            'medium': 0.85,
            'high': 0.7,
            'critical': 0.5
        }
        
        return {
            'potential_hallucination_risk': len(flags) > 0,
            'risk_level': max_risk_level if flags else 'none',
            'risk_factors': flags,
            'confidence_adjustment': confidence_adjustments.get(max_risk_level, 1.0),
            'recommendation': self._get_hallucination_recommendation(max_risk_level, flags),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_content_safety(self, content: str) -> Dict[str, Any]:
        """
        Check content for safety violations.
        
        Basic implementation - in production, would use more sophisticated
        content moderation APIs.
        """
        unsafe_patterns = [
            (r'harm\s+(yourself|others)', 'violence', 'critical'),
            (r'illegal\s+(?:activity|substance)', 'illegal_content', 'high'),
            (r'personal\s+(?:information|data|details)', 'privacy', 'medium'),
            (r'(?:credit\s+card|ssn|social\s+security)', 'pii', 'high'),
        ]
        
        violations = []
        
        for pattern, category, severity in unsafe_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append({
                    'category': category,
                    'severity': severity
                })
        
        if violations:
            self.security_events['content_violations'] += 1
            
        return {
            'safe': len(violations) == 0,
            'violations': violations,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get current security metrics."""
        total = max(1, self.security_events['total_checks'])
        
        return {
            'total_security_checks': total,
            'prompt_injection_rate': self.security_events['prompt_injections'] / total,
            'hallucination_flag_rate': self.security_events['hallucination_flags'] / total,
            'content_violation_rate': self.security_events['content_violations'] / total,
            'security_events': dict(self.security_events)
        }
    
    def _get_hallucination_recommendation(self, risk_level: str, flags: List[Dict]) -> str:
        """Generate recommendation based on hallucination risk."""
        if risk_level == 'critical':
            return "Add strong disclaimer or block response"
        elif risk_level == 'high':
            return "Add disclaimer about potential inaccuracies"
        elif risk_level == 'medium':
            return "Consider adding source citations"
        else:
            return "Monitor for user feedback"


# Global instance for easy access
ai_security = AISecurityMonitor()