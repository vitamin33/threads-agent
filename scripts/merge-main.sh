#!/bin/bash
# Claude Code Command: Merge latest main into current PR branch
# Usage: ./scripts/merge-main.sh [--auto-resolve-conflicts]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AUTO_RESOLVE=${1:-""}
MAIN_BRANCH="main"
CURRENT_BRANCH=$(git branch --show-current)

echo -e "${BLUE}🔄 Claude Code: Merge Main Workflow${NC}"
echo -e "${BLUE}======================================${NC}"

# Validate we're not on main branch
if [[ "$CURRENT_BRANCH" == "$MAIN_BRANCH" ]]; then
    echo -e "${RED}❌ Error: Cannot run merge workflow on main branch${NC}"
    echo -e "${YELLOW}💡 Switch to a feature branch first${NC}"
    exit 1
fi

echo -e "${GREEN}📍 Current branch: $CURRENT_BRANCH${NC}"

# Step 1: Fetch latest main
echo -e "\n${BLUE}📥 Step 1: Fetching latest main branch...${NC}"
git fetch origin $MAIN_BRANCH
echo -e "${GREEN}✅ Fetched origin/$MAIN_BRANCH${NC}"

# Check if there are new commits
COMMITS_BEHIND=$(git rev-list --count HEAD..origin/$MAIN_BRANCH)
if [[ "$COMMITS_BEHIND" == "0" ]]; then
    echo -e "${GREEN}✅ Branch is up to date with main. No merge needed.${NC}"
    exit 0
fi

echo -e "${YELLOW}📊 Branch is $COMMITS_BEHIND commit(s) behind main${NC}"

# Step 2: Stash changes if any
echo -e "\n${BLUE}💾 Step 2: Checking for uncommitted changes...${NC}"
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Uncommitted changes detected. Stashing...${NC}"
    STASH_MESSAGE="Claude Code auto-stash before merge $(date +%Y%m%d_%H%M%S)"
    git stash push -m "$STASH_MESSAGE"
    STASHED=true
    echo -e "${GREEN}✅ Changes stashed as: $STASH_MESSAGE${NC}"
else
    STASHED=false
    echo -e "${GREEN}✅ Working directory clean${NC}"
fi

# Step 3: Merge main
echo -e "\n${BLUE}🔀 Step 3: Merging origin/$MAIN_BRANCH...${NC}"
if git merge origin/$MAIN_BRANCH --no-edit; then
    echo -e "${GREEN}✅ Merge completed successfully${NC}"
    CONFLICTS=false
else
    echo -e "${YELLOW}⚠️  Merge conflicts detected${NC}"
    CONFLICTS=true
fi

# Step 4: Handle conflicts
if [[ "$CONFLICTS" == "true" ]]; then
    echo -e "\n${BLUE}🛠️  Step 4: Handling merge conflicts...${NC}"
    
    # Show conflicted files
    CONFLICT_FILES=$(git diff --name-only --diff-filter=U)
    echo -e "${YELLOW}📋 Conflicted files:${NC}"
    echo "$CONFLICT_FILES" | sed 's/^/  - /'
    
    if [[ "$AUTO_RESOLVE" == "--auto-resolve-conflicts" ]]; then
        echo -e "\n${YELLOW}🤖 Auto-resolving conflicts (prioritizing main branch)...${NC}"
        
        # Auto-resolve by taking main branch version for most files
        for file in $CONFLICT_FILES; do
            if [[ "$file" == *".md" ]] || [[ "$file" == *"README"* ]] || [[ "$file" == *"CHANGELOG"* ]]; then
                # For documentation, try to keep both versions
                echo -e "${BLUE}📝 Manual resolution needed for documentation: $file${NC}"
            else
                # For code files, prefer main branch
                echo -e "${YELLOW}🔧 Auto-resolving $file (using main branch version)${NC}"
                git checkout --theirs "$file"
                git add "$file"
            fi
        done
        
        # Check if all conflicts resolved
        if git diff --name-only --diff-filter=U | grep -q .; then
            echo -e "${YELLOW}⚠️  Some files still need manual resolution${NC}"
            echo -e "${BLUE}💡 Run: git status to see remaining conflicts${NC}"
            echo -e "${BLUE}💡 After resolving, run: git commit${NC}"
        else
            # Complete the merge
            git commit --no-edit
            echo -e "${GREEN}✅ All conflicts auto-resolved and committed${NC}"
        fi
    else
        echo -e "\n${YELLOW}💡 Resolve conflicts manually, then run:${NC}"
        echo -e "${BLUE}   git add <resolved-files>${NC}"
        echo -e "${BLUE}   git commit${NC}"
        echo -e "\n${BLUE}💡 Or rerun with --auto-resolve-conflicts flag${NC}"
    fi
fi

# Step 5: Restore stashed changes
if [[ "$STASHED" == "true" ]] && [[ "$CONFLICTS" == "false" || "$AUTO_RESOLVE" == "--auto-resolve-conflicts" ]]; then
    echo -e "\n${BLUE}📦 Step 5: Restoring stashed changes...${NC}"
    if git stash pop; then
        echo -e "${GREEN}✅ Stashed changes restored${NC}"
    else
        echo -e "${YELLOW}⚠️  Stash pop had conflicts. Check git status.${NC}"
    fi
fi

# Step 6: Push updates
if [[ "$CONFLICTS" == "false" || "$AUTO_RESOLVE" == "--auto-resolve-conflicts" ]]; then
    echo -e "\n${BLUE}🚀 Step 6: Pushing updated branch...${NC}"
    if git push origin "$CURRENT_BRANCH"; then
        echo -e "${GREEN}✅ Branch pushed successfully${NC}"
        echo -e "${GREEN}✅ PR will be automatically updated${NC}"
    else
        echo -e "${YELLOW}⚠️  Push failed. Check for issues.${NC}"
    fi
fi

# Summary
echo -e "\n${BLUE}📊 Merge Summary${NC}"
echo -e "${BLUE}===============${NC}"
echo -e "${GREEN}✅ Fetched latest main branch${NC}"
if [[ "$CONFLICTS" == "true" ]]; then
    if [[ "$AUTO_RESOLVE" == "--auto-resolve-conflicts" ]]; then
        echo -e "${GREEN}✅ Merge conflicts auto-resolved${NC}"
    else
        echo -e "${YELLOW}⚠️  Manual conflict resolution required${NC}"
    fi
else
    echo -e "${GREEN}✅ Clean merge completed${NC}"
fi
if [[ "$STASHED" == "true" ]]; then
    echo -e "${GREEN}✅ Stashed changes restored${NC}"
fi

echo -e "\n${GREEN}🎉 Merge workflow completed!${NC}"