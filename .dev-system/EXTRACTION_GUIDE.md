# Dev System Extraction Guide

This guide explains how to extract the `.dev-system/` folder to a standalone repository when ready.

## When to Extract

Extract when any of these conditions are met:
- ✅ All milestones M1-M9 are implemented
- ✅ 3+ external developers want to use the system
- ✅ You want to showcase it as a separate product
- ✅ The system API is stable (changes < weekly)

## Extraction Steps

### 1. Prepare for Extraction
```bash
# Ensure all paths are relative
cd .dev-system
find . -name "*.py" -exec grep -l "threads-agent" {} \;
find . -name "*.sh" -exec grep -l "threads-agent" {} \;

# Remove any hardcoded paths
# Update config to use environment variables
```

### 2. Create New Repository  
```bash
# Create new repo
gh repo create ai-agent-dev-system --public
git clone git@github.com:yourusername/ai-agent-dev-system.git

# Extract with history
cd threads-agent
git subtree push --prefix=.dev-system origin main
```

### 3. Standalone Setup
```bash
cd ai-agent-dev-system

# Create standalone setup
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="ai-agent-dev-system",
    version="1.0.0", 
    description="AI Agent Development System - Top 1% Developer Factory",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "click>=8.0",
        "rich>=13.0",
        "pandas>=1.5",
        "sqlalchemy>=1.4"
    ],
    entry_points={
        'console_scripts': [
            'ai-dev-system=cli.dev_system:main',
        ],
    },
)
EOF

# Create requirements.txt
pip freeze > requirements.txt

# Update README for standalone use
cp README.md README_STANDALONE.md
```

### 4. Update Integration Points

**In threads-agent repository:**
```bash
# Install as dependency
pip install -e ../ai-agent-dev-system

# Update justfile
dev-system command *args:
	@ai-dev-system {{command}} {{args}}

# Update path references
find . -name "*.py" -exec sed -i 's/.dev-system\//ai_dev_system\//g' {} \;
```

### 5. Documentation Updates

**New repository structure:**
```
ai-agent-dev-system/
├── README.md                 # Standalone documentation
├── setup.py                 # Python package setup
├── requirements.txt         # Dependencies  
├── ai_dev_system/          # Renamed from root folders
│   ├── __init__.py
│   ├── ops/
│   ├── evals/
│   ├── planner/
│   └── ...
├── examples/               # Usage examples
├── docs/                   # Full documentation
└── tests/                  # Test suite
```

## Integration Examples

### For New Projects
```bash
# Install the system
pip install ai-agent-dev-system

# Initialize in project
ai-dev-system init --all

# Add to project justfile
include ai-dev-system/justfile.include
```

### For Existing Projects  
```bash
# Gradual migration
ai-dev-system migrate --from legacy-scripts/

# Validate integration
ai-dev-system validate --project .
```

## Backward Compatibility

Maintain compatibility during transition:
1. Keep compatibility shims in threads-agent
2. Gradual deprecation warnings
3. Update documentation progressively  
4. Provide migration tools

## Success Metrics

Extraction is successful when:
- ✅ New project can use system in < 10 minutes
- ✅ All milestones work independently  
- ✅ Zero references to threads-agent specifics
- ✅ Full test coverage for standalone use
- ✅ Complete documentation and examples