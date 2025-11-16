# Git Branching Setup Guide

This guide sets up the recommended branching strategy for production-ready deployment.

## Current State

- `main` branch exists but is outdated (initial commits only)
- `dev/phase-1` has all Phase 1 production-ready work
- Remote: https://github.com/plongitudes/roanes-kitchen

## Goal

- Update `main` to match `dev/phase-1` (all Phase 1 improvements)
- Set `main` as default branch on GitHub
- Configure branch protection rules
- Establish ongoing branching strategy

## Steps

### 1. Update Main Branch (Local)

```bash
# Make sure you're on dev/phase-1 with latest changes committed
git checkout dev/phase-1
git pull origin dev/phase-1

# Merge dev/phase-1 into main (fast-forward)
git checkout main
git merge dev/phase-1 --ff-only

# Push updated main to GitHub
git push origin main
```

### 2. Set Default Branch on GitHub

1. Go to: https://github.com/plongitudes/roanes-kitchen/settings/branches
2. Under "Default branch", click the switch icon
3. Select `main` from dropdown
4. Click "Update" and confirm

### 3. Configure Branch Protection Rules

On GitHub → Settings → Branches → "Add branch protection rule":

**Branch name pattern:** `main`

**Protect matching branches:**
- ✅ Require a pull request before merging
  - Required approvals: 1
  - ✅ Dismiss stale pull request approvals when new commits are pushed

- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - Status checks: Select "test" and "docker-publish" (after first workflow runs)

- ✅ Require conversation resolution before merging

- ✅ Do not allow bypassing the above settings
  - ⚠️ Optional: Include administrators (recommended for teams)

**Note:** For solo development, you may want to allow bypassing for yourself initially.

### 4. Optional: Clean Up Old Branches

After main is updated and default:

```bash
# List branches to identify old ones
git branch -a

# Delete old local branches (if no longer needed)
git branch -d vk/5838-you-are-the-clau
git branch -d vk/7144-you-are-the-clau
# etc...

# Delete remote branches
git push origin --delete branch-name
```

## Ongoing Branching Strategy

### Branch Types

- **`main`** - Production-ready code only
  - Protected with PR reviews required
  - Triggers Docker image publishing
  - Only merge from `dev` or hotfix branches

- **`dev`** - Integration branch
  - Merge feature branches here first
  - Test thoroughly before merging to main
  - Can be reset/rebased if needed

- **`feature/*`** - New features
  - Branch from: `dev`
  - Merge to: `dev` via PR
  - Naming: `feature/description` or `feature/issue-id`

- **`fix/*`** - Bug fixes
  - Branch from: `dev` (or `main` for hotfixes)
  - Merge to: `dev` via PR (or directly to `main` for hotfixes)
  - Naming: `fix/description` or `fix/issue-id`

### Workflow Example

```bash
# Create feature branch
git checkout dev
git pull origin dev
git checkout -b feature/meal-planning

# Work on feature, commit changes
git add .
git commit -m "Add meal planning feature"

# Push and create PR
git push -u origin feature/meal-planning
# Create PR on GitHub: feature/meal-planning → dev

# After PR approved and merged to dev, test in dev
# Then create PR: dev → main for production release
```

## Release Process

1. Merge `dev` → `main` via PR
2. Tag the release:
   ```bash
   git checkout main
   git pull origin main
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. GitHub Actions automatically builds and publishes Docker images
4. Deploy to production using tagged images

## Verification

After setup:
- Default branch is `main`: Check repo homepage
- Protection rules active: Try force-pushing to main (should fail)
- CI/CD working: Push to main triggers workflows
