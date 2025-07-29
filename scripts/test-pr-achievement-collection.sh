#!/bin/bash
# Test PR Achievement Collection

echo "🧪 Testing PR Achievement Collection..."

# 1. Check database connection
echo "1️⃣ Testing database connection..."
python scripts/test-achievement-db-connection.py
if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please set DATABASE_URL"
    exit 1
fi

# 2. Create a test branch and make changes
echo -e "\n2️⃣ Creating test branch..."
git checkout -b test/achievement-collection-$(date +%s)

# 3. Make a small change
echo -e "\n3️⃣ Making test changes..."
cat >> services/achievement_collector/README.md << EOF

## Test Change for Achievement Collection
- Testing CI/CD achievement tracking
- Timestamp: $(date)
EOF

# 4. Commit and push
echo -e "\n4️⃣ Committing changes..."
git add services/achievement_collector/README.md
git commit -m "test: verify achievement collection in CI

This PR tests the achievement collection system:
- Database connectivity to PostgreSQL
- PR metrics extraction
- Achievement storage in persistent DB

Metrics:
- Performance improvement: 15% faster queries
- User impact: Better portfolio tracking
- Cost reduction: Optimized database queries"

# 5. Push branch
echo -e "\n5️⃣ Pushing branch..."
git push origin HEAD

# 6. Create PR using GitHub CLI
echo -e "\n6️⃣ Creating Pull Request..."
PR_URL=$(gh pr create \
    --title "Test Achievement Collection System" \
    --body "## Overview
This PR tests our achievement collection system in CI/CD.

### Changes
- Added test content to README
- Verifying PostgreSQL storage
- Testing metrics extraction

### Business Impact
- **Performance**: 15% faster achievement queries
- **User Experience**: Real-time achievement tracking
- **Revenue Impact**: Better portfolio = more opportunities

Epic: E4 - Advanced Testing
Sprint: 32
Linear: CRA-TEST-001" \
    --base main \
    --label "test,achievement-system" \
    2>&1 | tail -1)

echo -e "\n✅ Pull Request created: $PR_URL"
echo -e "\n📋 Next steps:"
echo "   1. Wait for CI workflow to run"
echo "   2. Check GitHub Actions for achievement tracking"
echo "   3. Verify achievement in database"
echo "   4. Merge PR to trigger achievement storage"