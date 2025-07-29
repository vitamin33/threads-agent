# 🏆 Achievement Collector Service

An intelligent PR-based achievement collection system that automatically transforms your GitHub Pull Requests into compelling professional achievements. The system extracts 50+ metrics, generates AI-powered stories for different audiences (HR, tech interviewers, CEOs), and prepares content for multiple platforms.

## 🚀 Key Features

- **Automatic PR Analysis**: Extracts 50+ metrics across code, performance, business, quality, and team dimensions
- **AI-Powered Business Value Extraction**: Quantifies impact in dollars, time saved, and performance gains
- **AI-Powered Story Generation**: Creates tailored narratives for technical, business, and leadership audiences
- **Multi-Platform Publishing**: Prepares content optimized for LinkedIn, Twitter, Dev.to, GitHub, and portfolio sites
- **Career Impact Tracking**: Measures and visualizes your professional growth with data-driven insights
- **GitHub Actions Integration**: Fully automated collection on every PR merge

## 📖 Documentation

### Getting Started
- [**PR Achievement System Overview**](./docs/PR_ACHIEVEMENT_SYSTEM.md) - Complete system architecture and workflow
- [**GitHub Actions Setup Guide**](./docs/GITHUB_ACTIONS_SETUP.md) - Step-by-step setup for automatic PR tracking
- [**Quick Start Guide**](./docs/PR_ACHIEVEMENT_SYSTEM.md#installation--setup) - Get up and running in 5 minutes

### For Developers
- [**API Reference**](./docs/API_REFERENCE.md) - Complete API documentation with examples
- [**Enhanced Business Value Calculation**](./docs/ENHANCED_BUSINESS_VALUE_CALCULATION.md) - Comprehensive business value system with agile KPIs
- [**AI Business Value Extraction**](./docs/AI_BUSINESS_VALUE_EXTRACTION.md) - Legacy documentation (see Enhanced version above)
- [**Deployment Guide**](./docs/DEPLOYMENT_GUIDE.md) - Docker, Kubernetes, and production deployment
- [**Best Practices**](./docs/BEST_PRACTICES.md) - Maximize your achievement impact

### Architecture Docs
- [Phase 1: Core System](./docs/PHASE_1_DOCUMENTATION.md) - Foundation and database design
- [Phase 2: Analytics](./docs/PHASE_2_DOCUMENTATION.md) - Analytics and insights
- [Phase 3: Export & Publishing](./docs/PHASE_3_ROADMAP.md) - Multi-platform publishing

## 🎯 Quick Example

```python
# Automatic PR achievement collection happens via GitHub Actions
# But you can also use the API directly:

from achievement_collector import AchievementClient

client = AchievementClient(api_key="your-key")

# Analyze a merged PR
achievement = await client.achievements.create_from_pr(
    pr_number=123,
    analyze=True,
    generate_stories=True
)

print(f"Impact Score: {achievement.impact_score}/100")
print(f"Skills Demonstrated: {achievement.skills_demonstrated}")
print(f"Business Value: {achievement.business_value}")
```

## 🏗️ Architecture Overview

```mermaid
graph TD
    A[GitHub PR Merged] --> B[GitHub Actions Workflow]
    B --> C[Comprehensive PR Analyzer]
    C --> D[50+ Metrics Extraction]
    D --> E[AI Story Generator]
    E --> F[Multi-Platform Publisher]
    F --> G[Achievement Database]
    G --> H[Portfolio/LinkedIn/Twitter]
```

## 📊 Metrics Collected

### Code Metrics
- Languages used and distribution
- Files changed, lines added/deleted
- Code complexity changes
- Refactoring patterns
- Change categories (feature, bugfix, etc.)

### Performance Metrics
- Latency improvements
- Throughput changes
- Resource utilization
- Database query optimization
- Caching effectiveness

### Business Metrics
- Financial impact (cost savings, revenue)
- User impact (affected users, satisfaction)
- Operational efficiency gains
- Time-to-market improvements

### Team Metrics
- Collaboration (reviewers, comments)
- Review time and iterations
- Cross-team participation
- Mentorship activities

## 🚀 Installation

### Quick Start (Local Development)

```bash
# Clone repository
git clone https://github.com/your-org/threads-agent
cd services/achievement_collector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
alembic upgrade head

# Run development server
uvicorn main:app --reload --port 8000
```

### GitHub Actions Setup

1. Add the workflow file to your repository:
```yaml
# .github/workflows/achievement-collector.yml
name: Collect PR Achievement
on:
  pull_request:
    types: [closed]

jobs:
  collect-achievement:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Collect Achievement
        uses: your-org/achievement-collector-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          database-url: ${{ secrets.DATABASE_URL }}
```

2. Add secrets to your repository settings

## 📈 Career Impact

The Achievement Collector helps you:

1. **Quantify Your Impact**: Turn vague accomplishments into measurable achievements
2. **Build Your Brand**: Generate professional content for multiple platforms
3. **Ace Interviews**: Have data-driven stories ready for any interview question
4. **Track Growth**: Visualize your skill development over time
5. **Stand Out**: Differentiate yourself with concrete, impressive metrics

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://user:pass@localhost/achievements

# Optional
GITHUB_TOKEN=ghp_your-token-here
REDIS_URL=redis://localhost:6379/0
MOCK_MODE=false  # Use true for testing without API calls
```

## 📦 API Endpoints

### Core Endpoints

- `POST /achievements` - Create new achievement
- `GET /achievements` - List achievements with filtering
- `GET /achievements/{id}` - Get specific achievement
- `PUT /achievements/{id}` - Update achievement
- `DELETE /achievements/{id}` - Delete achievement

### PR-Specific Endpoints

- `POST /achievements/pr/{pr_number}` - Create achievement from PR
- `GET /achievements/pr/{pr_number}` - Get PR achievement
- `GET /achievements/pr/{pr_number}/details` - Get detailed PR data

### Analytics Endpoints

- `GET /achievements/stats/summary` - Get achievement statistics
- `GET /analytics/performance` - Get performance metrics
- `GET /analytics/skills` - Analyze skill development
- `GET /analytics/career-progress` - Track career progression

See [API Reference](./API_REFERENCE.md) for complete documentation.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests
pytest -m e2e        # End-to-end tests

# Run with coverage
pytest --cov=services/achievement_collector
```

## 🚀 Deployment

### Docker

```bash
docker build -t achievement-collector .
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY achievement-collector
```

### Kubernetes

```bash
helm install achievement-collector ./helm -n achievements
```

See [Deployment Guide](./DEPLOYMENT_GUIDE.md) for production deployment.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is part of the Threads-Agent Stack. See LICENSE file for details.

## 🆘 Support

- **Documentation**: See `/docs` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@threads-agent.com

---

Built with ❤️ for developers who want to showcase their impact