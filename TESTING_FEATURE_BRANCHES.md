# Testing Feature Branch Docker Images

## Overview

This guide explains how to test feature branch Docker images in Portainer before merging to main.

---

## Quick Start

### 1. In Portainer, edit your Stack's `.env` file:

```bash
# Change these two lines:
BACKEND_IMAGE_TAG=feature-system7-ui
FRONTEND_IMAGE_TAG=feature-system7-ui

# Keep everything else the same
POSTGRES_PASSWORD=your_password
JWT_SECRET_KEY=your_secret
# ... etc
```

### 2. Update the stack:

In Portainer:
1. Click **"Update the stack"**
2. ✅ **Pull and redeploy** (checked)
3. Click **"Update"**

Portainer will:
- Pull `plongitudex/kitchen-backend:feature-system7-ui`
- Pull `plongitudex/kitchen-frontend:feature-system7-ui`
- Restart with new images

### 3. Test the feature

Visit your site and test the new features!

### 4. Roll back if needed:

```bash
# Restore in .env:
BACKEND_IMAGE_TAG=latest
FRONTEND_IMAGE_TAG=latest
```

Then **Update the stack** again.

---

## Running Both Production and Feature Side-by-Side

If you want to test without disrupting production:

### Option 1: Different Ports

Create a second stack in Portainer called `kitchen-feature`:

```bash
# .env for feature stack
BACKEND_PORT=8001    # Different from production's 8000
FRONTEND_PORT=8676   # Different from production's 8675
BACKEND_IMAGE_TAG=feature-system7-ui
FRONTEND_IMAGE_TAG=feature-system7-ui

# Use same database or separate one
POSTGRES_PASSWORD=same_as_prod  # or different
```

Now you have:
- **Production:** `http://inverness.valley:8675` (latest images)
- **Feature Test:** `http://inverness.valley:8676` (feature images)

### Option 2: Different Stack Name

Duplicate the stack in Portainer:
1. **kitchen** (production, port 8675, `latest` tag)
2. **kitchen-feature** (testing, port 8676, `feature-system7-ui` tag)

---

## Available Image Tags

After pushing your feature branch, GitHub Actions builds:

| Branch | Backend Tag | Frontend Tag |
|--------|-------------|--------------|
| `main` | `latest`, `main` | `latest`, `main` |
| `feature/system7-ui` | `feature-system7-ui` | `feature-system7-ui` |
| Any feature branch | `feature-<branch-name>` | `feature-<branch-name>` |

Check Docker Hub to see available tags:
- https://hub.docker.com/r/plongitudex/kitchen-backend/tags
- https://hub.docker.com/r/plongitudex/kitchen-frontend/tags

---

## Troubleshooting

### Image not found?

Check GitHub Actions to ensure the build completed:
- https://github.com/plongitudes/kitchen/actions

### Want to force a fresh pull?

In Portainer:
1. Go to **Images**
2. Remove old `plongitudex/kitchen-*` images
3. Update stack (will pull fresh)

### Testing with different databases?

Feature stack can use a separate database:

```bash
# In feature stack .env
POSTGRES_PASSWORD=different_password
APPDATA_PATH=/mnt/user/appdata/kitchen-feature  # Different data directory
```

This gives you a clean database for testing migrations, etc.

---

## Best Practices

✅ **Test in isolation** - Use a separate stack for feature testing
✅ **Monitor logs** - Check Portainer logs during feature testing
✅ **Backup first** - Take a database backup before testing with production data
✅ **Document changes** - Note what you're testing in the stack description
✅ **Clean up** - Remove feature stacks after merging to main

---

## Example Workflow

```bash
# 1. Push feature branch
git push origin feature/system7-ui

# 2. Wait for GitHub Actions to build (~5-10 min)

# 3. In Portainer, update .env:
BACKEND_IMAGE_TAG=feature-system7-ui
FRONTEND_IMAGE_TAG=feature-system7-ui

# 4. Pull and redeploy

# 5. Test the features

# 6. If good, merge PR on GitHub

# 7. After merge, update .env back to:
BACKEND_IMAGE_TAG=latest
FRONTEND_IMAGE_TAG=latest

# 8. Pull and redeploy (now using merged main branch)
```

Done! 🎉
