#!/bin/bash

echo "🔄 Website Updates Merge Workflow"
echo "================================="
echo ""

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "website-updates" ]; then
    echo "❌ You must be on the 'website-updates' branch to merge to main"
    echo "   Run: git checkout website-updates"
    exit 1
fi

echo ""
echo "📋 Pre-merge Checklist:"
echo "1. ✅ All changes are committed"
echo "2. ✅ Website is working correctly"
echo "3. ✅ All tests pass (if any)"
echo "4. ✅ Ready to merge to main"
echo ""

read -p "🤔 Are you ready to merge to main? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Merge cancelled"
    exit 1
fi

echo "🔄 Starting merge process..."

# Switch to main branch
echo "📥 Switching to main branch..."
git checkout main

# Pull latest changes from main
echo "📥 Pulling latest changes from main..."
git pull origin main

# Merge website-updates branch
echo "🔀 Merging website-updates into main..."
git merge website-updates

if [ $? -eq 0 ]; then
    echo "✅ Merge successful!"
    
    # Push to main
    echo "📤 Pushing changes to main..."
    git push origin main
    
    echo ""
    echo "🎉 Success! Your website updates are now live on main!"
    echo ""
    echo "📝 Next steps:"
    echo "   - Your website will be updated automatically (GitHub Pages)"
    echo "   - You can delete the website-updates branch if no longer needed"
    echo "   - Create a new branch for future updates"
    echo ""
    echo "🗑️  To delete the website-updates branch:"
    echo "   git branch -d website-updates"
    echo "   git push origin --delete website-updates"
    
else
    echo "❌ Merge failed! There are conflicts to resolve."
    echo ""
    echo "🔧 To resolve conflicts:"
    echo "   1. Fix the conflicts in the files"
    echo "   2. git add <fixed-files>"
    echo "   3. git commit"
    echo "   4. git push origin main"
    echo ""
    echo "🔄 To abort the merge:"
    echo "   git merge --abort"
    exit 1
fi 