#!/bin/bash
# Prevent merges between Monolithic-Socrates and master/main branches
# This hook prevents accidental merges that would corrupt either version

MERGE_HEAD=$(git rev-parse -q --verify MERGE_HEAD)

if [ -z "$MERGE_HEAD" ]; then
    exit 0
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Get merge source (the branch being merged in)
MERGE_SOURCE=$(git rev-parse --abbrev-ref MERGE_HEAD)

# Extract branch names
CURRENT_CLEAN=$(echo "$CURRENT_BRANCH" | tr -d ' ')
MERGE_CLEAN=$(echo "$MERGE_SOURCE" | tr -d ' ')

# Check for dangerous merge combinations
if [[ "$CURRENT_CLEAN" == "Monolithic-Socrates" && ( "$MERGE_CLEAN" == "master" || "$MERGE_CLEAN" == "main" ) ]]; then
    echo "❌ MERGE BLOCKED: Cannot merge master/main into Monolithic-Socrates"
    echo "   The Monolithic-Socrates branch is a historical reference and must remain isolated."
    echo "   Any modularization changes must stay on master/main branch."
    exit 1
fi

if [[ ( "$CURRENT_CLEAN" == "master" || "$CURRENT_CLEAN" == "main" ) && "$MERGE_CLEAN" == "Monolithic-Socrates" ]]; then
    echo "❌ MERGE BLOCKED: Cannot merge Monolithic-Socrates into master/main"
    echo "   The Monolithic-Socrates branch is a historical reference archive."
    echo "   The current development continues on the master/main branch."
    echo ""
    echo "   If you need to cherry-pick specific commits from the monolithic version:"
    echo "   git cherry-pick <commit-hash>"
    exit 1
fi

exit 0
