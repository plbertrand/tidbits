#!/bin/bash

# Get the current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Checkout main and pull latest changes
echo "Checking out main branch..."
git checkout main
echo "Pulling latest changes from main..."
git pull --rebase

# Get a list of all local branches, excluding main
BRANCHES=$(git branch --format="%(refname:short)" | grep -v "^main$")

# Loop through each branch and rebase it onto main
for branch in $BRANCHES
do
  echo "Switching to branch: $branch"
  git checkout "$branch"
  echo "Rebasing $branch onto main..."
  git rebase main
  if [ $? -ne 0 ]; then
    echo "Rebase failed for $branch. Please resolve conflicts and run 'git rebase --continue' or 'git rebase --abort'."
    exit 1
  fi
done

# Switch back to the original branch
echo "Switching back to original branch: $CURRENT_BRANCH"
git checkout "$CURRENT_BRANCH"

echo "All branches rebased against main."
