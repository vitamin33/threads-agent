"""
Web portfolio generator - Creates interactive portfolio websites.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from ..base import BaseExporter


class WebPortfolioGenerator(BaseExporter):
    """Generate interactive web portfolio sites."""
    
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir:
            self.template_dir = template_dir
        else:
            # Use default templates
            self.template_dir = os.path.join(
                os.path.dirname(__file__), 
                'templates'
            )
            
    async def export(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        user_info: Optional[Dict[str, str]] = None,
        output_dir: Optional[str] = None,
        theme: str = "modern"
    ) -> str:
        """
        Generate a complete portfolio website.
        
        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters
            user_info: User information
            output_dir: Output directory for website files
            theme: Portfolio theme
            
        Returns:
            Path to generated website directory
        """
        achievements = self.get_achievements(db, user_id, filters)
        
        if not output_dir:
            output_dir = f"portfolio_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare data
        portfolio_data = self._prepare_portfolio_data(achievements, user_info)
        
        # Generate HTML files
        self._generate_html_files(portfolio_data, output_dir, theme)
        
        # Generate CSS and JS files
        self._generate_static_files(output_dir, theme)
        
        # Generate data files
        self._generate_data_files(portfolio_data, output_dir)
        
        return output_dir
    
    def _prepare_portfolio_data(
        self, 
        achievements: List,
        user_info: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Prepare data for portfolio generation."""
        # Basic user info
        if not user_info:
            user_info = {
                'name': 'Portfolio',
                'title': 'Software Developer',
                'bio': 'Passionate developer with a track record of impactful solutions.'
            }
            
        # Calculate statistics
        stats = {
            'total_achievements': len(achievements),
            'total_impact': sum(a.impact_score or 0 for a in achievements),
            'total_hours': sum(a.duration_hours or 0 for a in achievements),
            'categories': len(set(a.category for a in achievements)),
            'skills': len(set(
                skill for a in achievements 
                if a.skills_demonstrated 
                for skill in a.skills_demonstrated
            ))
        }
        
        # Group achievements
        achievements_by_category = {}
        for achievement in achievements:
            if achievement.category not in achievements_by_category:
                achievements_by_category[achievement.category] = []
            achievements_by_category[achievement.category].append(achievement)
            
        # Timeline data
        timeline_data = self._generate_timeline_data(achievements)
        
        # Skills data
        skills_data = self._generate_skills_data(achievements)
        
        # Impact chart data
        impact_data = self._generate_impact_data(achievements)
        
        return {
            'user': user_info,
            'stats': stats,
            'achievements': achievements,
            'achievements_by_category': achievements_by_category,
            'timeline': timeline_data,
            'skills': skills_data,
            'impact_chart': impact_data,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_timeline_data(self, achievements: List) -> List[Dict]:
        """Generate timeline visualization data."""
        timeline = []
        
        for achievement in sorted(achievements, key=lambda a: a.completed_at or datetime.min):
            if achievement.completed_at:
                timeline.append({
                    'date': achievement.completed_at.isoformat(),
                    'title': achievement.title,
                    'category': achievement.category,
                    'impact': achievement.impact_score or 0,
                    'skills': achievement.skills_demonstrated or []
                })
                
        return timeline
    
    def _generate_skills_data(self, achievements: List) -> Dict[str, Any]:
        """Generate skills visualization data."""
        skill_counts = {}
        skill_timeline = {}
        
        for achievement in achievements:
            if achievement.skills_demonstrated:
                for skill in achievement.skills_demonstrated:
                    # Count occurrences
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
                    
                    # Track timeline
                    if skill not in skill_timeline:
                        skill_timeline[skill] = []
                    if achievement.completed_at:
                        skill_timeline[skill].append(achievement.completed_at.isoformat())
                        
        # Create radar chart data
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:12]
        
        radar_data = {
            'labels': [s[0] for s in top_skills],
            'values': [s[1] for s in top_skills],
            'max_value': max(s[1] for s in top_skills) if top_skills else 10
        }
        
        return {
            'counts': skill_counts,
            'timeline': skill_timeline,
            'radar': radar_data,
            'total': len(skill_counts)
        }
    
    def _generate_impact_data(self, achievements: List) -> Dict[str, Any]:
        """Generate impact visualization data."""
        # Monthly impact scores
        monthly_impact = {}
        category_impact = {}
        
        for achievement in achievements:
            if achievement.completed_at and achievement.impact_score:
                month_key = achievement.completed_at.strftime('%Y-%m')
                monthly_impact[month_key] = monthly_impact.get(month_key, 0) + achievement.impact_score
                
                category_impact[achievement.category] = category_impact.get(
                    achievement.category, 0
                ) + achievement.impact_score
                
        # Sort monthly data
        sorted_months = sorted(monthly_impact.items())
        
        return {
            'monthly': {
                'labels': [m[0] for m in sorted_months],
                'values': [m[1] for m in sorted_months]
            },
            'by_category': category_impact,
            'distribution': self._calculate_impact_distribution(achievements)
        }
    
    def _calculate_impact_distribution(self, achievements: List) -> Dict[str, int]:
        """Calculate impact score distribution."""
        distribution = {
            'low': 0,      # 0-33
            'medium': 0,   # 34-66
            'high': 0      # 67-100
        }
        
        for achievement in achievements:
            if achievement.impact_score:
                if achievement.impact_score <= 33:
                    distribution['low'] += 1
                elif achievement.impact_score <= 66:
                    distribution['medium'] += 1
                else:
                    distribution['high'] += 1
                    
        return distribution
    
    def _generate_html_files(
        self, 
        data: Dict[str, Any],
        output_dir: str,
        theme: str
    ):
        """Generate HTML files for the portfolio."""
        # Create basic HTML structure
        self._create_index_html(data, output_dir, theme)
        self._create_achievements_html(data, output_dir, theme)
        self._create_skills_html(data, output_dir, theme)
        self._create_timeline_html(data, output_dir, theme)
        
    def _create_index_html(self, data: Dict, output_dir: str, theme: str):
        """Create main index.html file."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['user'].get('name', 'Portfolio')} - Professional Portfolio</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/theme-{theme}.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <h1 class="logo">{data['user'].get('name', 'Portfolio')}</h1>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                <li><a href="#achievements">Achievements</a></li>
                <li><a href="#skills">Skills</a></li>
                <li><a href="#timeline">Timeline</a></li>
            </ul>
        </div>
    </nav>
    
    <section id="home" class="hero">
        <div class="container">
            <h1>{data['user'].get('name', 'Professional')}</h1>
            <h2>{data['user'].get('title', 'Software Developer')}</h2>
            <p>{data['user'].get('bio', '')}</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>{data['stats']['total_achievements']}</h3>
                    <p>Achievements</p>
                </div>
                <div class="stat-card">
                    <h3>{data['stats']['total_impact']}</h3>
                    <p>Total Impact</p>
                </div>
                <div class="stat-card">
                    <h3>{data['stats']['skills']}</h3>
                    <p>Skills</p>
                </div>
                <div class="stat-card">
                    <h3>{data['stats']['total_hours']:,}</h3>
                    <p>Project Hours</p>
                </div>
            </div>
        </div>
    </section>
    
    <section id="impact-overview" class="section">
        <div class="container">
            <h2>Impact Overview</h2>
            <div class="chart-container">
                <canvas id="impactChart"></canvas>
            </div>
        </div>
    </section>
    
    <section id="recent-achievements" class="section">
        <div class="container">
            <h2>Recent Achievements</h2>
            <div class="achievement-grid" id="recentAchievements">
                <!-- Dynamically loaded -->
            </div>
        </div>
    </section>
    
    <script src="js/portfolio.js"></script>
    <script>
        // Initialize portfolio with data
        window.portfolioData = {json.dumps(data, default=str)};
        initializePortfolio();
    </script>
</body>
</html>
"""
        
        with open(os.path.join(output_dir, 'index.html'), 'w') as f:
            f.write(html_content)
            
    def _create_achievements_html(self, data: Dict, output_dir: str, theme: str):
        """Create achievements page."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Achievements - {data['user'].get('name', 'Portfolio')}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/theme-{theme}.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <h1 class="logo">{data['user'].get('name', 'Portfolio')}</h1>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="achievements.html" class="active">Achievements</a></li>
                <li><a href="skills.html">Skills</a></li>
                <li><a href="timeline.html">Timeline</a></li>
            </ul>
        </div>
    </nav>
    
    <section class="section">
        <div class="container">
            <h1>All Achievements</h1>
            
            <div class="filters">
                <select id="categoryFilter" onchange="filterAchievements()">
                    <option value="">All Categories</option>
                    {' '.join(f'<option value="{cat}">{cat.title()}</option>' for cat in data['achievements_by_category'].keys())}
                </select>
                
                <select id="sortBy" onchange="sortAchievements()">
                    <option value="date">Sort by Date</option>
                    <option value="impact">Sort by Impact</option>
                    <option value="complexity">Sort by Complexity</option>
                </select>
            </div>
            
            <div id="achievementsList" class="achievements-list">
                <!-- Dynamically populated -->
            </div>
        </div>
    </section>
    
    <script src="js/portfolio.js"></script>
    <script>
        window.portfolioData = {json.dumps(data, default=str)};
        loadAchievementsPage();
    </script>
</body>
</html>
"""
        
        with open(os.path.join(output_dir, 'achievements.html'), 'w') as f:
            f.write(html_content)
            
    def _create_skills_html(self, data: Dict, output_dir: str, theme: str):
        """Create skills visualization page."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skills - {data['user'].get('name', 'Portfolio')}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/theme-{theme}.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <h1 class="logo">{data['user'].get('name', 'Portfolio')}</h1>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="achievements.html">Achievements</a></li>
                <li><a href="skills.html" class="active">Skills</a></li>
                <li><a href="timeline.html">Timeline</a></li>
            </ul>
        </div>
    </nav>
    
    <section class="section">
        <div class="container">
            <h1>Technical Skills</h1>
            
            <div class="skills-overview">
                <div class="stat-card">
                    <h3>{data['skills']['total']}</h3>
                    <p>Total Skills</p>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-container">
                    <h3>Skill Proficiency</h3>
                    <canvas id="skillRadar"></canvas>
                </div>
                
                <div class="chart-container">
                    <h3>Skill Distribution</h3>
                    <canvas id="skillBar"></canvas>
                </div>
            </div>
            
            <div class="skills-list" id="skillsList">
                <!-- Dynamically populated -->
            </div>
        </div>
    </section>
    
    <script src="js/portfolio.js"></script>
    <script>
        window.portfolioData = {json.dumps(data, default=str)};
        loadSkillsPage();
    </script>
</body>
</html>
"""
        
        with open(os.path.join(output_dir, 'skills.html'), 'w') as f:
            f.write(html_content)
            
    def _create_timeline_html(self, data: Dict, output_dir: str, theme: str):
        """Create timeline visualization page."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timeline - {data['user'].get('name', 'Portfolio')}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/theme-{theme}.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <h1 class="logo">{data['user'].get('name', 'Portfolio')}</h1>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="achievements.html">Achievements</a></li>
                <li><a href="skills.html">Skills</a></li>
                <li><a href="timeline.html" class="active">Timeline</a></li>
            </ul>
        </div>
    </nav>
    
    <section class="section">
        <div class="container">
            <h1>Career Timeline</h1>
            
            <div class="timeline" id="timeline">
                <!-- Dynamically populated -->
            </div>
        </div>
    </section>
    
    <script src="js/portfolio.js"></script>
    <script>
        window.portfolioData = {json.dumps(data, default=str)};
        loadTimelinePage();
    </script>
</body>
</html>
"""
        
        with open(os.path.join(output_dir, 'timeline.html'), 'w') as f:
            f.write(html_content)
            
    def _generate_static_files(self, output_dir: str, theme: str):
        """Generate CSS and JavaScript files."""
        # Create directories
        css_dir = os.path.join(output_dir, 'css')
        js_dir = os.path.join(output_dir, 'js')
        os.makedirs(css_dir, exist_ok=True)
        os.makedirs(js_dir, exist_ok=True)
        
        # Generate main CSS
        self._create_main_css(css_dir)
        
        # Generate theme CSS
        self._create_theme_css(css_dir, theme)
        
        # Generate JavaScript
        self._create_portfolio_js(js_dir)
        
    def _create_main_css(self, css_dir: str):
        """Create main stylesheet."""
        css_content = """
/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Navigation */
.navbar {
    background: #fff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 20px;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
}

.nav-links {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-links a {
    text-decoration: none;
    color: #666;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #0066cc;
}

/* Hero Section */
.hero {
    padding: 4rem 0;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 0.5rem;
}

.hero h2 {
    font-size: 1.5rem;
    font-weight: 300;
    margin-bottom: 1rem;
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    margin-top: 3rem;
}

.stat-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 10px;
    transition: transform 0.3s;
}

.stat-card:hover {
    transform: translateY(-5px);
}

.stat-card h3 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

/* Sections */
.section {
    padding: 4rem 0;
}

.section h2 {
    font-size: 2rem;
    margin-bottom: 2rem;
    text-align: center;
}

/* Chart Containers */
.chart-container {
    background: #fff;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
}

/* Achievement Grid */
.achievement-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.achievement-card {
    background: #fff;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.3s, box-shadow 0.3s;
}

.achievement-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.achievement-card h3 {
    margin-bottom: 0.5rem;
    color: #333;
}

.achievement-card .category {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background: #e3f2fd;
    color: #1976d2;
    border-radius: 20px;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
}

.achievement-card .impact {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #666;
    font-size: 0.875rem;
}

/* Filters */
.filters {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}

.filters select {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    background: #fff;
}

/* Timeline */
.timeline {
    position: relative;
    padding: 2rem 0;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    height: 100%;
    background: #ddd;
}

.timeline-item {
    position: relative;
    padding: 2rem;
    width: 45%;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.timeline-item:nth-child(odd) {
    margin-left: auto;
}

.timeline-item::before {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    background: #0066cc;
    border-radius: 50%;
    top: 2rem;
}

.timeline-item:nth-child(odd)::before {
    left: -10px;
}

.timeline-item:nth-child(even)::before {
    right: -10px;
}

/* Skills List */
.skills-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1rem;
    margin-top: 2rem;
}

.skill-tag {
    padding: 0.5rem 1rem;
    background: #f0f0f0;
    border-radius: 20px;
    text-align: center;
    font-size: 0.875rem;
    transition: background 0.3s;
}

.skill-tag:hover {
    background: #e0e0e0;
}

/* Responsive */
@media (max-width: 768px) {
    .nav-links {
        display: none;
    }
    
    .hero h1 {
        font-size: 2rem;
    }
    
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .timeline-item {
        width: 100%;
        margin-left: 0 !important;
    }
    
    .timeline::before {
        left: 20px;
    }
    
    .timeline-item::before {
        left: 10px !important;
        right: auto !important;
    }
}
"""
        
        with open(os.path.join(css_dir, 'style.css'), 'w') as f:
            f.write(css_content)
            
    def _create_theme_css(self, css_dir: str, theme: str):
        """Create theme-specific CSS."""
        if theme == "modern":
            theme_css = """
/* Modern Theme */
:root {
    --primary-color: #0066cc;
    --secondary-color: #764ba2;
    --accent-color: #667eea;
    --text-color: #333;
    --bg-color: #f8f9fa;
}

body {
    background: var(--bg-color);
}

.hero {
    background: linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%);
}

.achievement-card .category {
    background: #e3f2fd;
    color: #1976d2;
}

.achievement-card.high-impact {
    border-left: 4px solid #4caf50;
}

.skill-tag.expert {
    background: #c8e6c9;
    color: #2e7d32;
}

.skill-tag.proficient {
    background: #bbdefb;
    color: #1565c0;
}
"""
        elif theme == "dark":
            theme_css = """
/* Dark Theme */
:root {
    --primary-color: #61dafb;
    --secondary-color: #bb86fc;
    --accent-color: #03dac6;
    --text-color: #e0e0e0;
    --bg-color: #121212;
}

body {
    background: var(--bg-color);
    color: var(--text-color);
}

.navbar {
    background: #1e1e1e;
}

.hero {
    background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
}

.stat-card,
.achievement-card,
.chart-container {
    background: #1e1e1e;
    color: var(--text-color);
}

.achievement-card .category {
    background: rgba(97, 218, 251, 0.1);
    color: var(--primary-color);
}
"""
        else:
            theme_css = """
/* Default Theme */
"""
        
        with open(os.path.join(css_dir, f'theme-{theme}.css'), 'w') as f:
            f.write(theme_css)
            
    def _create_portfolio_js(self, js_dir: str):
        """Create portfolio JavaScript file."""
        js_content = """
// Portfolio JavaScript

let currentFilter = '';
let currentSort = 'date';

function initializePortfolio() {
    // Load recent achievements
    loadRecentAchievements();
    
    // Initialize impact chart
    initializeImpactChart();
}

function loadRecentAchievements() {
    const container = document.getElementById('recentAchievements');
    if (!container) return;
    
    const recent = window.portfolioData.achievements
        .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))
        .slice(0, 6);
        
    container.innerHTML = recent.map(achievement => `
        <div class="achievement-card ${achievement.impact_score >= 80 ? 'high-impact' : ''}">
            <span class="category">${achievement.category}</span>
            <h3>${achievement.title}</h3>
            <p>${achievement.description || ''}</p>
            <div class="impact">
                <span>Impact: ${achievement.impact_score || 0}</span>
                ${achievement.skills_demonstrated ? 
                    `<span>• ${achievement.skills_demonstrated.slice(0, 3).join(', ')}</span>` : ''}
            </div>
        </div>
    `).join('');
}

function initializeImpactChart() {
    const ctx = document.getElementById('impactChart');
    if (!ctx) return;
    
    const monthlyData = window.portfolioData.impact_chart.monthly;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.labels,
            datasets: [{
                label: 'Monthly Impact Score',
                data: monthlyData.values,
                borderColor: '#0066cc',
                backgroundColor: 'rgba(0, 102, 204, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function loadAchievementsPage() {
    displayAchievements();
}

function displayAchievements() {
    const container = document.getElementById('achievementsList');
    if (!container) return;
    
    let achievements = [...window.portfolioData.achievements];
    
    // Apply filter
    if (currentFilter) {
        achievements = achievements.filter(a => a.category === currentFilter);
    }
    
    // Apply sort
    achievements.sort((a, b) => {
        switch(currentSort) {
            case 'impact':
                return (b.impact_score || 0) - (a.impact_score || 0);
            case 'complexity':
                return (b.complexity_score || 0) - (a.complexity_score || 0);
            default:
                return new Date(b.completed_at) - new Date(a.completed_at);
        }
    });
    
    container.innerHTML = achievements.map(achievement => `
        <div class="achievement-card">
            <span class="category">${achievement.category}</span>
            <h3>${achievement.title}</h3>
            <p>${achievement.description || ''}</p>
            <div class="details">
                <p><strong>Impact:</strong> ${achievement.impact_score || 0}/100</p>
                <p><strong>Complexity:</strong> ${achievement.complexity_score || 0}/100</p>
                ${achievement.business_value ? 
                    `<p><strong>Business Impact:</strong> ${achievement.business_value}</p>` : ''}
                ${achievement.skills_demonstrated ? 
                    `<p><strong>Skills:</strong> ${achievement.skills_demonstrated.join(', ')}</p>` : ''}
                ${achievement.duration_hours ? 
                    `<p><strong>Duration:</strong> ${achievement.duration_hours} hours</p>` : ''}
            </div>
        </div>
    `).join('');
}

function filterAchievements() {
    currentFilter = document.getElementById('categoryFilter').value;
    displayAchievements();
}

function sortAchievements() {
    currentSort = document.getElementById('sortBy').value;
    displayAchievements();
}

function loadSkillsPage() {
    // Initialize skill radar chart
    const radarCtx = document.getElementById('skillRadar');
    if (radarCtx) {
        const radarData = window.portfolioData.skills.radar;
        
        new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: radarData.labels,
                datasets: [{
                    label: 'Skill Level',
                    data: radarData.values,
                    borderColor: '#0066cc',
                    backgroundColor: 'rgba(0, 102, 204, 0.2)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: radarData.max_value
                    }
                }
            }
        });
    }
    
    // Initialize skill bar chart
    const barCtx = document.getElementById('skillBar');
    if (barCtx) {
        const topSkills = Object.entries(window.portfolioData.skills.counts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
            
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: topSkills.map(s => s[0]),
                datasets: [{
                    label: 'Projects',
                    data: topSkills.map(s => s[1]),
                    backgroundColor: '#0066cc'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Display skills list
    displaySkillsList();
}

function displaySkillsList() {
    const container = document.getElementById('skillsList');
    if (!container) return;
    
    const skills = Object.entries(window.portfolioData.skills.counts)
        .sort((a, b) => b[1] - a[1]);
        
    container.innerHTML = skills.map(([skill, count]) => {
        const level = count >= 5 ? 'expert' : count >= 2 ? 'proficient' : 'familiar';
        return `<div class="skill-tag ${level}">${skill} (${count})</div>`;
    }).join('');
}

function loadTimelinePage() {
    const container = document.getElementById('timeline');
    if (!container) return;
    
    const timeline = window.portfolioData.timeline
        .sort((a, b) => new Date(b.date) - new Date(a.date));
        
    container.innerHTML = timeline.map((item, index) => `
        <div class="timeline-item">
            <div class="timeline-date">${new Date(item.date).toLocaleDateString()}</div>
            <h3>${item.title}</h3>
            <span class="category">${item.category}</span>
            ${item.impact ? `<p>Impact: ${item.impact}</p>` : ''}
            ${item.skills.length ? `<p>Skills: ${item.skills.join(', ')}</p>` : ''}
        </div>
    `).join('');
}
"""
        
        with open(os.path.join(js_dir, 'portfolio.js'), 'w') as f:
            f.write(js_content)
            
    def _generate_data_files(self, data: Dict, output_dir: str):
        """Generate data files for the portfolio."""
        # Save full data as JSON
        data_dir = os.path.join(output_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        with open(os.path.join(data_dir, 'portfolio.json'), 'w') as f:
            json.dump(data, f, indent=2, default=str)