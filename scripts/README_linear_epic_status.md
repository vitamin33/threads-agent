# Linear Epic Status Checker

## Overview

The `linear_epic_status.py` script fetches information about epics E5 through E12 from the Linear API and provides intelligent recommendations for parallel work.

## Features

- 📋 Fetches epic status, progress, and team assignments
- 🎯 Recommends optimal epic for parallel work (considering E6 is in progress)
- 📊 Shows completion metrics and team overlap analysis
- 🔍 Smart scoring system for work prioritization

## Usage

### Prerequisites

1. **Linear API Key**: Get your API key from Linear settings
2. **Virtual Environment**: Activate the project's virtual environment
3. **Dependencies**: Ensure `requests` is installed (included in requirements.txt)

### Running the Script

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Set your Linear API key
export LINEAR_API_KEY=your_linear_api_key_here

# 3. Run the script
python scripts/linear_epic_status.py
```

### Alternative Usage

```bash
# One-liner execution
source venv/bin/activate && LINEAR_API_KEY=your_key python scripts/linear_epic_status.py
```

## Sample Output

```
🔍 Fetching epic information from Linear...

================================================================================
📋 LINEAR EPIC STATUS REPORT (E5-E12)
================================================================================

✅ E5: Performance Optimization
   Status: Completed
   Progress: 100.0% (8/8 tasks)
   Team: Alice, Bob (Lead)
   Description: Optimize API response times and database queries...
   URL: https://linear.app/threads-agent/project/e5-performance

🔄 E6: Advanced Multi-Variant Testing  
   Status: In Progress
   Progress: 60.0% (6/10 tasks)
   Team: Charlie, David (Lead)
   Description: Implement Thompson sampling for A/B testing...
   URL: https://linear.app/threads-agent/project/e6-testing

⭕ E7: Real-time Analytics Dashboard
   Status: Not Started
   Progress: 0.0% (0/5 tasks)
   Team: Unassigned
   Description: Build real-time metrics dashboard...
   URL: https://linear.app/threads-agent/project/e7-analytics

================================================================================
🤖 PARALLEL WORK RECOMMENDATION
================================================================================
Current: E6 (In Progress)
🎯 Recommended: E7
   Reasons: clean start, no conflicts, small scope, earlier in sequence
   Score: 75/70

💡 Tip: Choose epics with minimal team overlap and clear scope
================================================================================
```

## Recommendation Algorithm

The script uses a smart scoring system to recommend the best epic for parallel work:

### Scoring Criteria

1. **Clean Start** (+30 points): Not Started epics are preferred
2. **Team Conflicts** (+20/+10/-10 points): Fewer assignees = less conflict
3. **Scope Size** (+15/+5 points): Smaller epics complete faster
4. **Sequential Order** (+10 points): Earlier epics may have dependencies

### Parallel Work Considerations

- Avoids epics with many team members (reduces conflicts)
- Prioritizes unassigned or minimally assigned epics
- Considers epic size for faster completion
- Accounts for potential dependencies in epic sequencing

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Activate virtual environment first
2. **API Key Error**: Check LINEAR_API_KEY environment variable
3. **No Epics Found**: Verify epic naming convention (E5, E6, etc.)
4. **Permission Denied**: Ensure API key has project read permissions

### Debug Mode

For additional debugging, you can modify the script to add verbose logging:

```python
# Add at the top of main()
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration

This script can be integrated into your workflow automation:

```bash
# Add to workflow-automation.sh
./scripts/linear_epic_status.py | grep "Recommended:" | head -1
```

## API Rate Limits

The script respects Linear's API rate limits by:
- Using efficient GraphQL queries
- Minimal API calls per epic
- Built-in timeout handling (30 seconds)

## Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Consider using Linear's team-scoped API keys for production