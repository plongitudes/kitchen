# Docker Hub Setup Guide

This guide walks through setting up Docker Hub publishing for the Kitchen project.

## Prerequisites

1. A Docker Hub account (https://hub.docker.com)
2. Admin access to this GitHub repository

## Step 1: Create Docker Hub Repositories

Create two public repositories on Docker Hub:
- `plongitudes/kitchen-backend`
- `plongitudes/kitchen-frontend`

## Step 2: Create Docker Hub Access Token

1. Go to Docker Hub → Account Settings → Security
2. Click "New Access Token"
3. Name: `github-actions-kitchen`
4. Access permissions: Read, Write, Delete
5. Generate and **copy the token** (you won't see it again)

## Step 3: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Value |
|-------------|-------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | The access token from Step 2 |

## Step 4: Update Image Prefix (Optional)

If you want to use a different Docker Hub organization/username, update the `IMAGE_PREFIX` in `.github/workflows/docker-publish.yml`:

```yaml
env:
  REGISTRY: docker.io
  IMAGE_PREFIX: your-username/kitchen  # Change this
```

## How It Works

The workflow automatically:
- Builds Docker images on push to `main` branch
- Publishes to Docker Hub with multiple tags:
  - `latest` (from main branch)
  - `v1.2.3` (from git tags like `v1.2.3`)
  - `main-abc1234` (branch-sha for traceability)
- Supports multi-architecture: `amd64` and `arm64`
- Runs Trivy security scans and uploads results to GitHub Security tab

## Testing the Workflow

1. Push to main branch or create a tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. Check the Actions tab to see the workflow run

3. Verify images on Docker Hub:
   - https://hub.docker.com/r/plongitudes/kitchen-backend
   - https://hub.docker.com/r/plongitudes/kitchen-frontend

## Using the Published Images

Update `docker-compose.prod.yml` to use published images instead of building locally:

```yaml
backend:
  image: plongitudes/kitchen-backend:latest
  # Remove build section

frontend:
  image: plongitudes/kitchen-frontend:latest
  # Remove build section
```
