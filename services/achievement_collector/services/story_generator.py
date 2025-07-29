"""AI-powered story generator for achievements."""

import os
from typing import Dict, List
import openai
import json

from ..core.logging import setup_logging

logger = setup_logging(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


class StoryGenerator:
    """Generate persona-based stories from achievement data."""

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key or self.api_key == "test":
            logger.warning("OpenAI API key not configured, using mock responses")
            self.mock_mode = True
        else:
            self.mock_mode = False
            openai.api_key = self.api_key

    async def generate_technical_story(self, analysis: Dict) -> Dict:
        """Generate technical story for developers and architects."""

        if self.mock_mode:
            return self._mock_technical_story(analysis)

        # Extract key technical points
        technical_highlights = self._extract_technical_highlights(analysis)

        prompt = f"""
        You are a senior software engineer writing about a technical achievement.
        
        Based on this PR analysis, create a compelling technical story:
        {json.dumps(technical_highlights, indent=2)}
        
        Format the response as JSON with:
        - summary: One-line technical summary (max 100 chars)
        - full_story: 2-3 paragraph technical deep dive
        - key_learnings: List of 3-5 technical insights
        - technical_impact: Brief statement of technical improvement
        """

        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating technical story: {e}")
            return self._mock_technical_story(analysis)

    async def generate_performance_story(
        self, pr_data: Dict, performance_metrics: Dict, code_metrics: Dict
    ) -> Dict:
        """Generate performance-focused story."""

        if self.mock_mode:
            return self._mock_performance_story(performance_metrics)

        prompt = f"""
        You are a performance engineer documenting an optimization success.
        
        PR Title: {pr_data.get("title", "Performance Optimization")}
        
        Performance Improvements:
        {json.dumps(performance_metrics, indent=2)}
        
        Code Changes:
        {
            json.dumps(
                {
                    "files_changed": code_metrics.get("files_changed", 0),
                    "languages": list(code_metrics.get("languages", {}).keys()),
                },
                indent=2,
            )
        }
        
        Create a performance story with:
        - summary: One-line performance win (max 100 chars)
        - full_story: Detailed explanation of optimization approach
        - metrics_highlight: Most impressive metric in human terms
        - scalability_impact: How this improves system scale
        """

        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating performance story: {e}")
            return self._mock_performance_story(performance_metrics)

    async def generate_business_story(
        self, pr_data: Dict, business_metrics: Dict
    ) -> Dict:
        """Generate business-focused story for stakeholders."""

        if self.mock_mode:
            return self._mock_business_story(business_metrics)

        prompt = f"""
        You are a product manager explaining technical work to business stakeholders.
        
        PR Title: {pr_data.get("title", "Technical Implementation")}
        
        Business Impact:
        {json.dumps(business_metrics, indent=2)}
        
        Create a business story with:
        - summary: Business value in one line (max 100 chars)
        - full_story: Non-technical explanation of business impact
        - roi_statement: Clear ROI or value proposition
        - strategic_alignment: How this supports business goals
        """

        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating business story: {e}")
            return self._mock_business_story(business_metrics)

    async def generate_leadership_story(self, pr_data: Dict, review_data: Dict) -> Dict:
        """Generate leadership and collaboration story."""

        if self.mock_mode:
            return self._mock_leadership_story(pr_data)

        prompt = f"""
        You are a tech lead highlighting team collaboration and leadership.
        
        PR: {pr_data.get("title", "Team Collaboration")}
        Team Size: {pr_data.get("requested_reviewers", [])}
        Review Comments: {review_data.get("total_comments", 0)}
        
        Create a leadership story with:
        - summary: Leadership/collaboration highlight (max 100 chars)
        - full_story: Story of team coordination and mentorship
        - team_impact: How this improved team capabilities
        - collaboration_score: Numeric score 0-100
        """

        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating leadership story: {e}")
            return self._mock_leadership_story(pr_data)

    async def generate_innovation_story(self, analysis: Dict) -> Dict:
        """Generate innovation and creativity story."""

        if self.mock_mode:
            return self._mock_innovation_story(analysis)

        innovation_metrics = analysis.get("innovation_metrics", {})

        prompt = f"""
        You are a principal engineer highlighting innovative solutions.
        
        Innovation Indicators:
        {json.dumps(innovation_metrics, indent=2)}
        
        Technical Implementation:
        {
            json.dumps(
                {
                    "languages": list(
                        analysis.get("code_metrics", {}).get("languages", {}).keys()
                    ),
                    "patterns": analysis.get("architectural_metrics", {}).get(
                        "patterns_implemented", {}
                    ),
                },
                indent=2,
            )
        }
        
        Create an innovation story with:
        - summary: Innovation in one line (max 100 chars)
        - full_story: Explanation of novel approach or solution
        - innovation_type: Category (technical/process/creative)
        - industry_impact: Potential broader impact
        """

        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating innovation story: {e}")
            return self._mock_innovation_story(analysis)

    async def generate_persona_stories(self, analysis: Dict) -> Dict:
        """Generate stories for all relevant personas."""

        stories = {}

        # Always generate technical story
        stories["technical"] = await self.generate_technical_story(analysis)

        # Conditionally generate other stories based on data
        if self._has_performance_data(analysis):
            stories["performance"] = await self.generate_performance_story(
                analysis.get("metadata", {}),
                analysis.get("performance_metrics", {}),
                analysis.get("code_metrics", {}),
            )

        if self._has_business_impact(analysis):
            stories["business"] = await self.generate_business_story(
                analysis.get("metadata", {}), analysis.get("business_metrics", {})
            )

        if self._has_team_collaboration(analysis):
            stories["leadership"] = await self.generate_leadership_story(
                analysis.get("metadata", {}), analysis.get("team_metrics", {})
            )

        if self._has_innovation(analysis):
            stories["innovation"] = await self.generate_innovation_story(analysis)

        # Generate persona-specific stories
        stories["personas"] = await self._generate_hiring_personas(analysis, stories)

        return stories

    async def _generate_hiring_personas(
        self, analysis: Dict, base_stories: Dict
    ) -> Dict:
        """Generate stories tailored for different hiring audiences."""

        personas = {}

        # HR Manager
        personas["hr_manager"] = {
            "focus": "soft skills and cultural fit",
            "highlights": self._extract_hr_highlights(analysis),
            "story": self._format_for_hr(base_stories),
        }

        # Tech Interviewer
        personas["tech_interviewer"] = {
            "focus": "technical depth and problem-solving",
            "highlights": self._extract_tech_interview_highlights(analysis),
            "story": self._format_for_tech_interview(base_stories),
        }

        # Startup CEO
        personas["startup_ceo"] = {
            "focus": "business impact and scrappiness",
            "highlights": self._extract_ceo_highlights(analysis),
            "story": self._format_for_ceo(base_stories),
        }

        # Investor
        personas["investor"] = {
            "focus": "scalability and market impact",
            "highlights": self._extract_investor_highlights(analysis),
            "story": self._format_for_investor(base_stories),
        }

        return personas

    # Helper methods

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with error handling."""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical storyteller who creates compelling narratives from software achievements.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def _extract_technical_highlights(self, analysis: Dict) -> Dict:
        """Extract key technical points for story generation."""

        return {
            "languages": list(
                analysis.get("code_metrics", {}).get("languages", {}).keys()
            ),
            "complexity_reduction": analysis.get("quality_metrics", {}).get(
                "complexity_change"
            ),
            "patterns_used": analysis.get("architectural_metrics", {}).get(
                "patterns_implemented"
            ),
            "performance_gains": analysis.get("performance_metrics", {}).get(
                "latency_changes"
            ),
            "test_coverage": analysis.get("quality_metrics", {}).get("test_coverage"),
            "refactoring": analysis.get("code_metrics", {}).get("refactoring_metrics"),
        }

    def _has_performance_data(self, analysis: Dict) -> bool:
        """Check if PR has performance improvements."""
        perf = analysis.get("performance_metrics", {})
        return bool(
            perf.get("latency_changes")
            or perf.get("throughput_changes")
            or perf.get("resource_usage")
        )

    def _has_business_impact(self, analysis: Dict) -> bool:
        """Check if PR has business impact."""
        biz = analysis.get("business_metrics", {})
        return bool(
            biz.get("financial_impact", {}).get("cost_savings")
            or biz.get("financial_impact", {}).get("revenue_impact")
            or biz.get("user_impact", {}).get("satisfaction_improvement")
        )

    def _has_team_collaboration(self, analysis: Dict) -> bool:
        """Check if PR shows team collaboration."""
        team = analysis.get("team_metrics", {})
        reviewers = team.get("collaboration", {}).get("reviewers_count", 0) or 0
        return reviewers > 2

    def _has_innovation(self, analysis: Dict) -> bool:
        """Check if PR contains innovation."""
        innovation = analysis.get("innovation_metrics", {})
        return bool(
            innovation.get("technical_innovation")
            or innovation.get("process_innovation")
        )

    # Persona-specific extraction methods

    def _extract_hr_highlights(self, analysis: Dict) -> List[str]:
        """Extract highlights for HR managers."""
        highlights = []

        # Collaboration
        reviewers_count = (
            analysis.get("team_metrics", {})
            .get("collaboration", {})
            .get("reviewers_count", 0)
            or 0
        )
        if reviewers_count > 0:
            highlights.append("Strong team collaboration")

        # Mentorship
        teaching_moments = (
            analysis.get("team_metrics", {})
            .get("mentorship", {})
            .get("teaching_moments", 0)
            or 0
        )
        if teaching_moments > 0:
            highlights.append("Mentored team members")

        # Problem solving
        overall_impact = (
            analysis.get("composite_scores", {}).get("overall_impact", 0) or 0
        )
        if overall_impact > 70:
            highlights.append("Exceptional problem-solving skills")

        # Communication (from PR description quality)
        if len(analysis.get("metadata", {}).get("description", "")) > 200:
            highlights.append("Clear technical communication")

        return highlights

    def _extract_tech_interview_highlights(self, analysis: Dict) -> List[str]:
        """Extract highlights for technical interviewers."""
        highlights = []

        # Algorithm optimization
        if analysis.get("performance_metrics", {}).get("latency_changes"):
            highlights.append("Algorithm optimization expertise")

        # System design
        if analysis.get("architectural_metrics", {}).get("patterns_implemented"):
            highlights.append("Strong system design skills")

        # Code quality
        test_coverage = (
            analysis.get("quality_metrics", {}).get("test_coverage", {}).get("after", 0)
            or 0
        )
        if test_coverage > 80:
            highlights.append("High code quality standards")

        # Technical depth
        languages = len(analysis.get("code_metrics", {}).get("languages", {}))
        if languages > 2:
            highlights.append(f"Polyglot programmer ({languages} languages)")

        return highlights

    def _extract_ceo_highlights(self, analysis: Dict) -> List[str]:
        """Extract highlights for startup CEOs."""
        highlights = []

        # Business impact
        financial = analysis.get("business_metrics", {}).get("financial_impact", {})
        cost_savings = financial.get("cost_savings", 0) if financial else 0
        if cost_savings and cost_savings > 0:
            highlights.append(f"Saved ${cost_savings:,.0f} annually")

        # Speed of delivery
        if analysis.get("metadata", {}).get("merge_time_hours", 0) < 48:
            highlights.append("Fast execution and delivery")

        # Customer focus
        users_affected = (
            analysis.get("business_metrics", {})
            .get("user_impact", {})
            .get("users_affected", 0)
            or 0
        )
        if users_affected > 0:
            highlights.append("Customer-focused development")

        # Resourcefulness
        lines_deleted = (
            analysis.get("code_metrics", {}).get("total_lines_deleted", 0) or 0
        )
        lines_added = analysis.get("code_metrics", {}).get("total_lines_added", 0) or 0
        if lines_deleted > lines_added:
            highlights.append("Efficient, lean solutions")

        return highlights

    def _extract_investor_highlights(self, analysis: Dict) -> List[str]:
        """Extract highlights for investors."""
        highlights = []

        # Scalability
        if analysis.get("performance_metrics", {}).get("scalability_improvement"):
            highlights.append("Built for scale")

        # Market impact
        if (
            analysis.get("business_metrics", {})
            .get("market_impact", {})
            .get("competitive_advantage")
        ):
            highlights.append("Competitive advantage creation")

        # Innovation
        if analysis.get("innovation_metrics", {}).get("patent_potential"):
            highlights.append("Innovative, patentable solutions")

        # Growth metrics
        if (
            analysis.get("impact_predictions", {})
            .get("business_growth", {})
            .get("revenue_potential")
        ):
            highlights.append("Revenue growth enabler")

        return highlights

    def _format_for_hr(self, stories: Dict) -> str:
        """Format stories for HR audience."""
        # Emphasize soft skills, teamwork, culture fit
        return stories.get("leadership", {}).get(
            "summary", stories.get("technical", {}).get("summary", "")
        )

    def _format_for_tech_interview(self, stories: Dict) -> str:
        """Format stories for technical interview."""
        # Emphasize technical depth, problem-solving
        return stories.get("technical", {}).get(
            "summary", stories.get("performance", {}).get("summary", "")
        )

    def _format_for_ceo(self, stories: Dict) -> str:
        """Format stories for CEO audience."""
        # Emphasize business impact, speed, resourcefulness
        return stories.get("business", {}).get(
            "summary", stories.get("performance", {}).get("summary", "")
        )

    def _format_for_investor(self, stories: Dict) -> str:
        """Format stories for investor audience."""
        # Emphasize scale, innovation, market impact
        return stories.get("innovation", {}).get(
            "summary", stories.get("business", {}).get("summary", "")
        )

    # Mock response methods for testing

    def _mock_technical_story(self, analysis: Dict) -> Dict:
        """Generate mock technical story."""
        languages = list(analysis.get("code_metrics", {}).get("languages", {}).keys())

        return {
            "type": "technical",
            "summary": f"Optimized {languages[0] if languages else 'system'} implementation for better performance",
            "full_story": f"""
            Implemented significant optimizations to the {languages[0] if languages else "core"} codebase,
            focusing on algorithm efficiency and code maintainability. The refactoring touched
            {analysis.get("code_metrics", {}).get("files_changed", 0)} files and improved overall
            system performance while maintaining backward compatibility.
            
            Key technical decisions included adopting more efficient data structures and
            eliminating redundant computations in critical paths.
            """.strip(),
            "key_learnings": [
                "Performance bottlenecks often hide in unexpected places",
                "Profiling before optimizing saves significant time",
                "Clean code and performance can coexist",
            ],
            "technical_impact": "Reduced computational complexity from O(n²) to O(n log n)",
        }

    def _mock_performance_story(self, performance_metrics: Dict) -> Dict:
        """Generate mock performance story."""
        latency = performance_metrics.get("latency_changes", {}).get("reported", {})
        improvement = latency.get("improvement_percentage", 50)

        return {
            "type": "performance",
            "summary": f"Achieved {improvement:.0f}% latency reduction through algorithmic optimization",
            "full_story": f"""
            Identified and resolved a critical performance bottleneck that was impacting user experience.
            Through careful profiling and analysis, discovered that the root cause was inefficient
            database queries in the hot path.
            
            By implementing query optimization and adding strategic caching, reduced average response
            time from {latency.get("before", 200)}ms to {latency.get("after", 100)}ms.
            """.strip(),
            "metrics_highlight": f"{improvement:.0f}% faster response times",
            "scalability_impact": "System can now handle 10x more concurrent users",
        }

    def _mock_business_story(self, business_metrics: Dict) -> Dict:
        """Generate mock business story."""
        financial = business_metrics.get("financial_impact", {})
        savings = financial.get("cost_savings", 15000)

        return {
            "type": "business",
            "summary": f"Delivered ${savings:,.0f} in annual cost savings through optimization",
            "full_story": """
            This technical improvement directly translates to significant business value.
            By optimizing resource utilization, we've reduced infrastructure costs while
            improving service quality.
            
            The changes enable us to serve more customers with the same infrastructure,
            improving both margins and customer satisfaction.
            """.strip(),
            "roi_statement": f"${savings:,.0f} annual savings with 2-month payback period",
            "strategic_alignment": "Supports Q4 objective of improving operational efficiency by 20%",
            "financial_impact": savings,
        }

    def _mock_leadership_story(self, pr_data: Dict) -> Dict:
        """Generate mock leadership story."""
        return {
            "type": "leadership",
            "summary": "Led cross-functional implementation with 4 team members",
            "full_story": """
            Successfully coordinated a complex technical implementation across multiple teams.
            Facilitated knowledge sharing sessions and ensured all team members understood
            the architectural decisions.
            
            Mentored junior developers through the code review process, helping them
            understand performance optimization techniques.
            """.strip(),
            "team_impact": "Upskilled 2 junior developers in performance optimization",
            "collaboration_score": 85,
        }

    def _mock_innovation_story(self, analysis: Dict) -> Dict:
        """Generate mock innovation story."""
        return {
            "type": "innovation",
            "summary": "Pioneered novel approach to real-time data processing",
            "full_story": """
            Developed an innovative solution that challenges conventional approaches to
            real-time data processing. By combining streaming architectures with
            intelligent caching, created a hybrid system that delivers both speed and accuracy.
            
            This approach has potential applications beyond our immediate use case and
            could influence how similar systems are designed.
            """.strip(),
            "innovation_type": "technical",
            "industry_impact": "Potential to influence real-time processing best practices",
        }
