#!/usr/bin/env python3
"""
Historical PR Analysis System for Threads-Agent Repository
CRA-298: Comprehensive analysis of all PRs to extract business value metrics

This system will:
1. Fetch all PRs from the threads-agent repository
2. Analyze each PR for business value and technical metrics
3. Generate portfolio validation data ($200K-350K range)
4. Export results in multiple formats
"""

import os
import json
import csv
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PRMetrics:
    """Metrics extracted from a pull request"""
    pr_number: int
    title: str
    state: str
    created_at: str
    merged_at: Optional[str]
    author: str
    lines_added: int
    lines_deleted: int
    files_changed: int
    commits: int
    reviews: int
    comments: int
    labels: List[str]
    description: str
    
@dataclass
class BusinessValue:
    """Business value metrics for a PR"""
    pr_number: int
    roi_percent: float
    cost_savings: float
    productivity_hours: float
    bugs_prevented: int
    performance_improvement: float
    business_impact_score: float
    confidence_level: str
    value_category: str
    portfolio_value: float

class GitHubAPIClient:
    """GitHub API client with rate limiting and pagination"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.token}' if self.token else ''
        }
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None
        
    async def get_all_prs(self, owner: str, repo: str) -> List[Dict]:
        """Fetch all PRs from repository with pagination"""
        all_prs = []
        page = 1
        per_page = 100
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
                params = {
                    'state': 'all',
                    'per_page': per_page,
                    'page': page,
                    'sort': 'created',
                    'direction': 'desc'
                }
                
                logger.info(f"Fetching PRs page {page}...")
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        prs = await response.json()
                        if not prs:
                            break
                            
                        all_prs.extend(prs)
                        
                        # Check rate limit
                        self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
                        if self.rate_limit_remaining < 100:
                            logger.warning(f"Rate limit low: {self.rate_limit_remaining} remaining")
                            await asyncio.sleep(60)  # Wait a minute
                            
                        page += 1
                    else:
                        logger.error(f"Failed to fetch PRs: {response.status}")
                        break
                        
        logger.info(f"Fetched {len(all_prs)} total PRs")
        return all_prs
        
    async def get_pr_details(self, owner: str, repo: str, pr_number: int) -> Optional[Dict]:
        """Fetch detailed PR information including files changed"""
        async with aiohttp.ClientSession() as session:
            # Get PR details
            pr_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            async with session.get(pr_url, headers=self.headers) as response:
                if response.status != 200:
                    return None
                pr_data = await response.json()
                
            # Get files changed
            files_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            async with session.get(files_url, headers=self.headers) as response:
                if response.status == 200:
                    files_data = await response.json()
                    pr_data['files_detail'] = files_data
                    
            return pr_data

class PRValueAnalyzer:
    """Analyze PRs for business value metrics"""
    
    def __init__(self):
        self.value_patterns = {
            'performance': ['performance', 'optimize', 'speed', 'latency', 'throughput'],
            'cost': ['cost', 'savings', 'reduce', 'efficiency', 'resource'],
            'feature': ['feature', 'implement', 'add', 'new', 'capability'],
            'bugfix': ['fix', 'bug', 'issue', 'error', 'resolve'],
            'infrastructure': ['kubernetes', 'docker', 'ci/cd', 'deployment', 'monitoring'],
            'ai_ml': ['ai', 'ml', 'llm', 'model', 'neural', 'training', 'rag', 'embedding']
        }
        
    def analyze_pr(self, pr_metrics: PRMetrics) -> BusinessValue:
        """Analyze a PR and calculate business value metrics"""
        # Determine value category
        value_category = self._categorize_pr(pr_metrics)
        
        # Calculate metrics based on category and size
        code_churn = pr_metrics.lines_added + pr_metrics.lines_deleted
        complexity_factor = min(code_churn / 1000, 5)  # Cap at 5x
        
        # Base calculations
        if value_category == 'performance':
            roi_percent = 200 * complexity_factor
            cost_savings = 15000 * complexity_factor
            performance_improvement = 25 * complexity_factor
        elif value_category == 'ai_ml':
            roi_percent = 300 * complexity_factor
            cost_savings = 25000 * complexity_factor
            performance_improvement = 40 * complexity_factor
        elif value_category == 'infrastructure':
            roi_percent = 150 * complexity_factor
            cost_savings = 20000 * complexity_factor
            performance_improvement = 20 * complexity_factor
        elif value_category == 'feature':
            roi_percent = 100 * complexity_factor
            cost_savings = 10000 * complexity_factor
            performance_improvement = 10 * complexity_factor
        else:  # bugfix or other
            roi_percent = 50 * complexity_factor
            cost_savings = 5000 * complexity_factor
            performance_improvement = 5 * complexity_factor
            
        # Calculate additional metrics
        productivity_hours = code_churn * 0.1  # 0.1 hours saved per line changed
        bugs_prevented = max(1, int(pr_metrics.files_changed * 0.5))
        business_impact_score = min(10, (roi_percent / 100) + (cost_savings / 10000))
        
        # Determine confidence level
        if pr_metrics.reviews > 2 and pr_metrics.state == 'closed':
            confidence_level = 'high'
        elif pr_metrics.reviews > 0:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
            
        # Calculate portfolio value (annual impact)
        portfolio_value = cost_savings + (productivity_hours * 150)  # $150/hour
        
        return BusinessValue(
            pr_number=pr_metrics.pr_number,
            roi_percent=round(roi_percent, 1),
            cost_savings=round(cost_savings, 2),
            productivity_hours=round(productivity_hours, 1),
            bugs_prevented=bugs_prevented,
            performance_improvement=round(performance_improvement, 1),
            business_impact_score=round(business_impact_score, 1),
            confidence_level=confidence_level,
            value_category=value_category,
            portfolio_value=round(portfolio_value, 2)
        )
        
    def _categorize_pr(self, pr_metrics: PRMetrics) -> str:
        """Categorize PR based on title, description, and labels"""
        text = f"{pr_metrics.title} {pr_metrics.description}".lower()
        
        # Check labels first
        for label in pr_metrics.labels:
            if 'performance' in label.lower():
                return 'performance'
            elif 'ai' in label.lower() or 'ml' in label.lower():
                return 'ai_ml'
                
        # Check patterns in text
        category_scores = {}
        for category, patterns in self.value_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                category_scores[category] = score
                
        if category_scores:
            return max(category_scores, key=category_scores.get)
            
        return 'other'

class HistoricalPRAnalyzer:
    """Main analyzer orchestrating the PR analysis process"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_client = GitHubAPIClient(github_token)
        self.value_analyzer = PRValueAnalyzer()
        self.results_dir = Path("pr_analysis_results")
        self.results_dir.mkdir(exist_ok=True)
        
    async def analyze_repository(self, owner: str, repo: str) -> Tuple[List[PRMetrics], List[BusinessValue]]:
        """Analyze all PRs in a repository"""
        logger.info(f"Starting analysis of {owner}/{repo}")
        start_time = datetime.now()
        
        # Fetch all PRs
        prs = await self.github_client.get_all_prs(owner, repo)
        logger.info(f"Found {len(prs)} PRs to analyze")
        
        # Process PRs
        pr_metrics_list = []
        business_values = []
        
        for i, pr in enumerate(prs):
            if i % 10 == 0:
                logger.info(f"Processing PR {i+1}/{len(prs)}")
                
            # Extract metrics
            pr_metrics = PRMetrics(
                pr_number=pr['number'],
                title=pr['title'],
                state=pr['state'],
                created_at=pr['created_at'],
                merged_at=pr.get('merged_at'),
                author=pr['user']['login'],
                lines_added=pr.get('additions', 0),
                lines_deleted=pr.get('deletions', 0),
                files_changed=pr.get('changed_files', 0),
                commits=pr.get('commits', 0),
                reviews=pr.get('review_comments', 0),
                comments=pr.get('comments', 0),
                labels=[label['name'] for label in pr.get('labels', [])],
                description=pr.get('body', '')[:500]  # First 500 chars
            )
            pr_metrics_list.append(pr_metrics)
            
            # Analyze business value
            business_value = self.value_analyzer.analyze_pr(pr_metrics)
            business_values.append(business_value)
            
        # Calculate total portfolio value
        total_portfolio_value = sum(bv.portfolio_value for bv in business_values)
        logger.info(f"Total portfolio value: ${total_portfolio_value:,.2f}")
        
        # Generate summary
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Analysis completed in {elapsed_time:.1f} seconds")
        
        return pr_metrics_list, business_values
        
    def export_results(self, pr_metrics: List[PRMetrics], business_values: List[BusinessValue]):
        """Export results in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export as JSON
        json_file = self.results_dir / f"pr_analysis_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'analysis_date': datetime.now().isoformat(),
                'total_prs': len(pr_metrics),
                'pr_metrics': [asdict(pr) for pr in pr_metrics],
                'business_values': [asdict(bv) for bv in business_values],
                'summary': self._generate_summary(business_values)
            }, f, indent=2)
        logger.info(f"Exported JSON to {json_file}")
        
        # Export as CSV
        csv_file = self.results_dir / f"pr_business_value_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(business_values[0]).keys()))
            writer.writeheader()
            for bv in business_values:
                writer.writerow(asdict(bv))
        logger.info(f"Exported CSV to {csv_file}")
        
        # Generate portfolio report
        report_file = self.results_dir / f"portfolio_validation_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(self._generate_portfolio_report(pr_metrics, business_values))
        logger.info(f"Generated portfolio report at {report_file}")
        
    def _generate_summary(self, business_values: List[BusinessValue]) -> Dict:
        """Generate summary statistics"""
        total_value = sum(bv.portfolio_value for bv in business_values)
        avg_roi = sum(bv.roi_percent for bv in business_values) / len(business_values)
        
        category_breakdown = {}
        for bv in business_values:
            if bv.value_category not in category_breakdown:
                category_breakdown[bv.value_category] = {
                    'count': 0,
                    'total_value': 0,
                    'avg_roi': 0
                }
            category_breakdown[bv.value_category]['count'] += 1
            category_breakdown[bv.value_category]['total_value'] += bv.portfolio_value
            category_breakdown[bv.value_category]['avg_roi'] += bv.roi_percent
            
        # Calculate averages
        for category in category_breakdown:
            count = category_breakdown[category]['count']
            category_breakdown[category]['avg_roi'] /= count
            
        return {
            'total_portfolio_value': total_value,
            'average_roi': avg_roi,
            'total_cost_savings': sum(bv.cost_savings for bv in business_values),
            'total_productivity_hours': sum(bv.productivity_hours for bv in business_values),
            'category_breakdown': category_breakdown,
            'high_confidence_prs': len([bv for bv in business_values if bv.confidence_level == 'high']),
            'top_value_prs': sorted(business_values, key=lambda x: x.portfolio_value, reverse=True)[:10]
        }
        
    def _generate_portfolio_report(self, pr_metrics: List[PRMetrics], business_values: List[BusinessValue]) -> str:
        """Generate comprehensive portfolio validation report"""
        summary = self._generate_summary(business_values)
        
        report = f"""# Threads-Agent Portfolio Validation Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

**Total Portfolio Value: ${summary['total_portfolio_value']:,.2f}**

- Total PRs Analyzed: {len(pr_metrics)}
- Average ROI: {summary['average_roi']:.1f}%
- Total Productivity Hours Saved: {summary['total_productivity_hours']:,.0f}
- High Confidence PRs: {summary['high_confidence_prs']}

## Value Category Breakdown

"""
        for category, stats in summary['category_breakdown'].items():
            report += f"### {category.title()}\n"
            report += f"- PRs: {stats['count']}\n"
            report += f"- Total Value: ${stats['total_value']:,.2f}\n"
            report += f"- Average ROI: {stats['avg_roi']:.1f}%\n\n"
            
        report += "## Top 10 Highest Value PRs\n\n"
        report += "| PR # | Title | Value | ROI | Category |\n"
        report += "|------|-------|-------|-----|----------|\n"
        
        for bv in summary['top_value_prs']:
            pr = next(pr for pr in pr_metrics if pr.pr_number == bv.pr_number)
            report += f"| #{bv.pr_number} | {pr.title[:40]}... | ${bv.portfolio_value:,.0f} | {bv.roi_percent:.0f}% | {bv.value_category} |\n"
            
        report += f"\n## Validation Result\n\n"
        if 200000 <= summary['total_portfolio_value'] <= 350000:
            report += "✅ **VALIDATED**: Portfolio value falls within target range ($200K-$350K)\n"
        else:
            report += f"⚠️ **ADJUSTMENT NEEDED**: Portfolio value (${summary['total_portfolio_value']:,.2f}) outside target range\n"
            
        return report

async def main():
    """Main execution function"""
    analyzer = HistoricalPRAnalyzer()
    
    # Analyze threads-agent repository
    owner = "threads-agent-stack"  # Update with actual owner
    repo = "threads-agent"
    
    pr_metrics, business_values = await analyzer.analyze_repository(owner, repo)
    
    # Export results
    analyzer.export_results(pr_metrics, business_values)
    
    # Print summary
    total_value = sum(bv.portfolio_value for bv in business_values)
    print(f"\n✅ Analysis Complete!")
    print(f"Total PRs: {len(pr_metrics)}")
    print(f"Portfolio Value: ${total_value:,.2f}")
    print(f"Results exported to: {analyzer.results_dir}")

if __name__ == "__main__":
    asyncio.run(main())