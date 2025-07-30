"""Enhanced AI analysis for achievements using GPT-4."""

import json
import os
from typing import Dict

import openai

from ..db.models import Achievement


class AIAnalyzer:
    """Enhanced AI analysis for achievements using GPT-4."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key and self.api_key != "test":
            openai.api_key = self.api_key
            self.client = openai.AsyncOpenAI()
        else:
            self.client = None

    async def analyze_achievement_impact(self, achievement: Achievement) -> Dict:
        """Perform deep analysis of achievement impact."""
        if not self.client:
            return self._mock_analysis(achievement)

        prompt = f"""
        Analyze this professional achievement and provide insights:
        
        Title: {achievement.title}
        Category: {achievement.category}
        Description: {achievement.description}
        Metrics: {achievement.metrics}
        Technologies: {", ".join(achievement.technologies or [])}
        Business Value: {achievement.business_value}
        
        Provide:
        1. Quantified impact score (0-100)
        2. Key strengths demonstrated
        3. Transferable skills highlighted
        4. Potential career advancement implications
        5. Suggested improvements or follow-up achievements
        6. Industry relevance and market value
        
        Format as JSON with these keys: impact_score, strengths, skills, career_implications, next_steps, market_value
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career coach and achievement analyst.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            return response.choices[0].message.content
        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._mock_analysis(achievement)

    async def generate_professional_summary(self, achievements: list) -> str:
        """Generate a professional summary based on achievements."""
        if not self.api_key or self.api_key == "test":
            return self._mock_professional_summary(achievements)

        try:
            # Prepare achievement data
            achievement_data = []
            for a in achievements[:10]:  # Limit to top 10
                achievement_data.append(
                    {
                        "title": a.title,
                        "impact": a.impact_score,
                        "skills": a.skills_demonstrated,
                        "category": a.category,
                    }
                )

            prompt = f"""Based on these achievements, generate a professional summary (3-4 sentences):
            {achievement_data}
            
            Focus on key skills, impact, and professional strengths."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI summary generation failed: {e}")
            return self._mock_professional_summary(achievements)

    def _mock_professional_summary(self, achievements: list) -> str:
        """Mock professional summary for offline mode."""
        if not achievements:
            return "Experienced professional with a track record of delivering impactful results."

        # Extract top skills
        skill_counts = {}
        for a in achievements:
            if a.skills_demonstrated:
                for skill in a.skills_demonstrated:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        skills_text = ", ".join([skill[0] for skill in top_skills])

        return f"Results-driven professional with expertise in {skills_text}. Proven track record of delivering {len(achievements)} significant achievements with measurable business impact. Strong focus on innovation, optimization, and continuous improvement."

    async def generate_linkedin_content(self, achievement) -> str:
        """Generate LinkedIn post content for an achievement."""
        if not self.api_key or self.api_key == "test":
            return self._mock_linkedin_content(achievement)

        try:
            prompt = f"""Create an engaging LinkedIn post about this achievement:
            Title: {achievement.title}
            Description: {achievement.description}
            Impact: {achievement.impact_score}
            Skills: {achievement.skills_demonstrated}
            
            Make it professional, engaging, and authentic. Include a call to action."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI LinkedIn content generation failed: {e}")
            return self._mock_linkedin_content(achievement)

    def _mock_linkedin_content(self, achievement) -> str:
        """Mock LinkedIn content for offline mode."""
        return f"🚀 Excited to share a recent achievement: {achievement.title}\n\n{achievement.description}\n\n💡 Key takeaway: Continuous improvement and innovation drive real business impact.\n\n#TechInnovation #ContinuousImprovement #ProfessionalGrowth"

    def _mock_analysis(self, achievement: Achievement) -> Dict:
        """Mock analysis for offline mode."""
        return {
            "impact_score": 85,
            "strengths": ["Technical excellence", "Business impact", "Innovation"],
            "skills": ["Python", "AI/ML", "System optimization", "Leadership"],
            "career_implications": "Strong candidate for senior engineering roles",
            "next_steps": [
                "Scale solution to larger datasets",
                "Present at conferences",
            ],
            "market_value": "High demand - $150k-$200k range",
        }

    async def extract_business_value(self, pr_description: str, pr_metrics: Dict = None) -> Dict:
        """Extract business value from PR description using enhanced calculator and AI."""
        pr_metrics = pr_metrics or {}
        
        # First try the enhanced calculator
        from .business_value_calculator import AgileBusinessValueCalculator
        calculator = AgileBusinessValueCalculator()
        
        enhanced_result = calculator.extract_business_value(pr_description, pr_metrics)
        if enhanced_result:
            return enhanced_result
        
        # Fallback to AI if available
        if not self.client:
            return self._extract_business_value_offline(pr_description)

        prompt = f"""
        Analyze this PR description and extract quantifiable business value using industry best practices:
        
        PR Description: {pr_description}
        PR Metrics: Files changed: {pr_metrics.get('changed_files', 'unknown')}, Lines: +{pr_metrics.get('additions', 0)}/-{pr_metrics.get('deletions', 0)}
        
        Calculate realistic business value based on:
        1. Time savings (use role-based rates: Junior $75/hr, Mid $100/hr, Senior $125/hr)
        2. Infrastructure cost reductions (typical server costs $500-2000/month)
        3. Quality improvements (defect fix cost ~$1200, incident costs $2500-25000)
        4. Risk mitigation (security/compliance value)
        5. Automation benefits (manual process elimination)
        6. Technical debt reduction (future maintenance savings)
        
        Be conservative with estimates and include confidence levels.
        Return JSON with: total_value, currency, period, type, confidence, breakdown, method, justification
        If no clear business value, return null.
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a business value analyst specializing in quantifying software engineering improvements using industry-standard metrics and conservative estimates.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # Lower temperature for more conservative estimates
            )

            # Handle both JSON object and regular text responses
            try:
                result = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # If not JSON, try to extract from text
                content = response.choices[0].message.content
                result = self._parse_ai_text_response(content)
            
            return result if result and result.get("total_value") else None

        except Exception as e:
            print(f"AI business value extraction error: {e}")
            return self._extract_business_value_offline(pr_description)

    def _extract_business_value_offline(self, pr_description: str) -> Dict:
        """Offline extraction for testing and fallback."""
        import re

        # Simple pattern matching for offline mode

        # Dollar amount patterns
        dollar_match = re.search(
            r"\$(\d{1,3}(?:,\d{3})*|\d+)(?:\s+(?:per\s+)?(?:year|annually))?",
            pr_description,
        )
        if dollar_match:
            # Remove commas and convert to int
            amount_str = dollar_match.group(1).replace(",", "")
            return {
                "total_value": int(amount_str),
                "currency": "USD",
                "period": "yearly",
                "type": "cost_savings",
            }

        # Time savings patterns
        time_match = re.search(
            r"sav(?:es?|ing)\s+(\d+)\s+(?:developer\s+)?hours?\s+(?:per\s+)?(week|month|year|annually)",
            pr_description,
            re.IGNORECASE,
        )
        if time_match:
            hours = int(time_match.group(1))
            period = time_match.group(2).lower()

            # Convert to annual hours
            if period == "week":
                annual_hours = hours * 52
            elif period == "month":
                annual_hours = hours * 12
            else:  # year or annually
                annual_hours = hours

            return {
                "total_value": annual_hours * 100,  # $100/hour
                "currency": "USD",
                "period": "yearly",
                "type": "time_savings",
                "breakdown": {"time_saved_hours": annual_hours, "hourly_rate": 100},
            }

        # Performance improvement pattern - also match "response time", "optimization", etc.
        perf_match = re.search(
            r"(?:performance|response time|optimization|optimized|reduced).*?(\d+)%|(\d+)%.*?(?:performance|response time|optimization)",
            pr_description,
            re.IGNORECASE,
        )
        if perf_match:
            percentage = int(perf_match.group(1) or perf_match.group(2))
            # Estimate value: assume $1000/month baseline infrastructure cost
            # Performance improvement saves percentage of that
            monthly_savings = 1000 * (percentage / 100)
            return {
                "total_value": int(monthly_savings * 12),  # Annual value
                "currency": "USD",
                "period": "yearly",
                "type": "performance_improvement",
                "confidence": 0.7,
                "breakdown": {
                    "performance_gain_pct": percentage,
                    "infrastructure_savings": int(monthly_savings * 12),
                },
                "extraction_method": "pattern_matching",
                "raw_text": f"{percentage}% performance improvement",
            }

        # Bug fix pattern - estimate prevented incident cost (exclude trivial fixes)
        if re.search(
            r"bug|issue|error|crash|critical|prevent", pr_description, re.IGNORECASE
        ) and not re.search(
            r"typo|spelling|documentation", pr_description, re.IGNORECASE
        ):
            # Estimate $5000 per prevented incident
            return {
                "total_value": 5000,
                "currency": "USD",
                "period": "one-time",
                "type": "bug_prevention",
                "confidence": 0.6,
                "extraction_method": "pattern_matching",
                "raw_text": "Bug fix - estimated incident prevention value",
            }

        return None
    
    def _parse_ai_text_response(self, content: str) -> Dict:
        """Parse AI text response when JSON parsing fails."""
        import re
        
        # Try to extract dollar amount
        dollar_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', content)
        if dollar_match:
            amount = int(dollar_match.group(1).replace(',', ''))
            
            # Determine type from content
            if 'time' in content.lower() or 'hour' in content.lower():
                value_type = 'time_savings'
            elif 'performance' in content.lower() or 'optimization' in content.lower():
                value_type = 'performance_improvement'
            else:
                value_type = 'cost_savings'
                
            return {
                "total_value": amount,
                "currency": "USD",
                "period": "yearly",
                "type": value_type,
                "confidence": 0.6,
                "method": "ai_text_parsing",
                "source": content[:200]
            }
        return None

    async def update_achievement_business_value(
        self, db, achievement: Achievement
    ) -> bool:
        """Update an achievement with extracted business value data."""
        try:
            # Extract business value from description with metrics context
            pr_metrics = achievement.metrics_after or {}
            business_data = await self.extract_business_value(achievement.description, pr_metrics)

            if not business_data:
                return False

            # Store the full JSON in business_value field
            business_value_json = json.dumps(business_data)
            
            # Check if the JSON is too long for VARCHAR(255)
            # If so, store a summary in business_value and full data in metadata
            if len(business_value_json) > 255:
                # Create a short summary for business_value field
                total_value = business_data.get('total_value', 0)
                currency = business_data.get('currency', 'USD')
                period = business_data.get('period', 'yearly')
                
                # Store summary in business_value
                achievement.business_value = f"${total_value:,} {currency}/{period}"
                
                # Store full JSON in metadata
                if not achievement.metadata_json:
                    achievement.metadata_json = {}
                achievement.metadata_json['business_value_full'] = business_data
                
                logger.info(f"Business value JSON too long ({len(business_value_json)} chars), "
                           f"stored summary: {achievement.business_value}")
            else:
                # JSON fits in VARCHAR(255), store directly
                achievement.business_value = business_value_json

            # Update specific metric fields based on the extracted data
            if business_data.get("type") == "time_savings":
                achievement.time_saved_hours = business_data.get("breakdown", {}).get(
                    "time_saved_hours", 0
                )

            # Extract performance percentage if mentioned
            import re

            perf_match = re.search(r"(\d+)%", achievement.description)
            if perf_match and business_data.get("type") in [
                "performance_improvement",
                "cost_savings",
            ]:
                achievement.performance_improvement_pct = float(perf_match.group(1))

            # Commit changes to database
            db.commit()
            return True

        except Exception as e:
            print(f"Error updating achievement business value: {e}")
            return False

    async def batch_update_business_values(
        self, db, achievements: list[Achievement]
    ) -> Dict:
        """Batch update multiple achievements with business values."""
        results = {"updated": 0, "failed": 0, "errors": []}

        for achievement in achievements:
            try:
                success = await self.update_achievement_business_value(db, achievement)
                if success:
                    results["updated"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"achievement_id": achievement.id, "error": str(e)}
                )

        return results
