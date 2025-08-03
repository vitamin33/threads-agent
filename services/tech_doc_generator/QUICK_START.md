# Tech Doc Generator - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
cd services/tech_doc_generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get Your API Keys

#### Dev.to (Easiest - 2 min)
1. Go to https://dev.to/settings/extensions
2. Generate API key
3. Save it immediately

#### LinkedIn (Medium - 10 min)
1. Create app at https://www.linkedin.com/developers/
2. Request "Share on LinkedIn" product
3. Use OAuth flow to get access token

#### Twitter/X (Hardest - 1-2 days)
1. Apply at https://developer.twitter.com/
2. Wait for approval
3. Create app and generate tokens

### 3. Configure Environment
Create `.env` file:
```bash
# Minimum required for testing
DEVTO_API_KEY=your_key_here
OPENAI_API_KEY=your_openai_key  # For content generation

# Optional
LINKEDIN_ACCESS_TOKEN=your_token
TWITTER_BEARER_TOKEN=your_token
```

### 4. Test Your Setup
```bash
# Test code analysis (no API keys needed)
python test_integration.py

# Test with mock data (no API keys needed)
python test_simple.py

# Test real publishing (requires API keys)
python test_real_publishing.py
```

## 📝 First Article Generation

### Option 1: Command Line
```python
from app.services.code_analyzer import CodeAnalyzer
from app.services.content_generator import ContentGenerator
from app.models.article import ArticleType, Platform

# Analyze your code
analyzer = CodeAnalyzer("/path/to/your/project")
analysis = await analyzer.analyze_source(SourceType.REPOSITORY, ".")

# Generate article
generator = ContentGenerator()
article = await generator.generate_article(
    analysis=analysis,
    article_type=ArticleType.ARCHITECTURE,
    target_platform=Platform.DEVTO
)

print(f"Generated: {article.title}")
print(f"Preview: {article.content[:200]}...")
```

### Option 2: API Endpoint
```bash
# Start the service
uvicorn app.main:app --reload

# Generate article via API
curl -X POST http://localhost:8084/api/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "repository",
    "source_path": "/path/to/project",
    "article_type": "architecture",
    "target_platform": "devto"
  }'
```

## 🎯 Platform-Specific Tips

### Dev.to
- Articles are created as **drafts** by default
- Edit and review before publishing
- Best for technical deep-dives
- Supports full markdown with code blocks

### LinkedIn
- Keep it professional and concise
- Focus on business value and career insights
- Best for thought leadership
- 1300 character limit for posts

### Twitter/X
- Automatically creates threads
- Each tweet limited to 280 characters
- Best for quick insights and tips
- Use engaging hooks

## ⚡ Common Issues

### "No module named 'redis'"
```bash
pip install redis
```

### "API key not found"
- Check your `.env` file is in the correct directory
- Make sure to `source venv/bin/activate`
- Try `python -m dotenv` to verify

### "401 Unauthorized"
- Dev.to: Regenerate API key
- LinkedIn: Token expired (60 days), need OAuth refresh
- Twitter: Check all 4 tokens are set

## 🔥 Pro Tips

1. **Start Small**: Test with your README first
2. **Review Everything**: AI can hallucinate, always review
3. **Track Performance**: Monitor which content performs best
4. **Iterate**: Use engagement data to improve prompts
5. **Be Authentic**: Add your personal touch to AI content

## 📚 Full Documentation

- [Platform Setup Guide](./PLATFORM_SETUP_GUIDE.md) - Detailed setup instructions
- [API Documentation](./API_DOCS.md) - Endpoint reference
- [Architecture Overview](./TECHNICAL_DOCUMENTATION.md) - System design

## Need Help?

- Check test files for examples
- Review error logs for specific issues
- Open an issue on GitHub

---

**Ready to automate your technical content? Let's go! 🚀**