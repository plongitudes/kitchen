# Upgrade Guide

This guide explains how to safely upgrade Roane's Kitchen to newer versions.

## Table of Contents

- [Upgrade Overview](#upgrade-overview)
- [Before You Upgrade](#before-you-upgrade)
- [Upgrade Methods](#upgrade-methods)
- [Database Migrations](#database-migrations)
- [Breaking Changes](#breaking-changes)
- [Rollback Procedures](#rollback-procedures)
- [Version-Specific Upgrade Notes](#version-specific-upgrade-notes)

## Upgrade Overview

### How Upgrades Work

Roane's Kitchen uses **database migrations** to handle schema changes automatically. When you upgrade:

1. **Pull new Docker images** - Get the latest backend/frontend containers
2. **Backend starts** - Entrypoint script runs `alembic upgrade head` automatically
3. **Migrations apply** - Database schema updates to match new version
4. **Application starts** - New version runs with updated schema

### Upgrade Safety

- **Database migrations are automatic** - Applied on container start
- **Migrations are forward-only** - Each version builds on the previous
- **Always backup before upgrading** - See backup procedures below
- **Test upgrades** - Use staging environment when possible

## Before You Upgrade

### 1. Check Release Notes

**ALWAYS** read the release notes for breaking changes:
- Visit: https://github.com/plongitudes/roanes-kitchen/releases
- Check CHANGELOG.md for version-specific notes
- Look for "BREAKING CHANGE" or "Migration Required" labels

### 2. Backup Your Database

**Required before every upgrade:**

```bash
# Method 1: Using the backup API
curl -X POST http://localhost:8000/backup/create \
  -H "Authorization: Bearer YOUR_TOKEN"

# Download the backup
curl http://localhost:8000/backup/download/FILENAME \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o backup-pre-upgrade-$(date +%Y%m%d).sql

# Method 2: Direct PostgreSQL dump
docker exec roanes-kitchen-postgres pg_dump -U admin roanes_kitchen > \
  backup-pre-upgrade-$(date +%Y%m%d).sql
```

Store backups safely outside the container:
```bash
# Copy to safe location
cp backup-pre-upgrade-*.sql /mnt/backups/roanes-kitchen/manual/
```

### 3. Check Current Version

```bash
# Check running version
docker images | grep roanes-kitchen

# Check what version will be pulled
docker pull plongitudes/roanes-kitchen-backend:latest --dry-run
```

### 4. Review Migration Path

Check which migrations will run:

```bash
# Current database version
docker exec roanes-kitchen-backend alembic current

# Pending migrations
docker exec roanes-kitchen-backend alembic history
```

## Upgrade Methods

### Method 1: Tagged Version Upgrade (Recommended)

Use specific version tags for controlled upgrades:

```bash
# 1. Update docker-compose.prod.yml to specific version
# Change from:
#   image: plongitudes/roanes-kitchen-backend:latest
# To:
#   image: plongitudes/roanes-kitchen-backend:v1.2.0

# 2. Pull new images
docker-compose -f docker-compose.prod.yml pull

# 3. Stop services
docker-compose -f docker-compose.prod.yml down

# 4. Start with new version (migrations run automatically)
docker-compose -f docker-compose.prod.yml up -d

# 5. Watch logs for migration success
docker-compose -f docker-compose.prod.yml logs -f backend
```

Look for:
```
Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add_new_column
Starting application...
```

### Method 2: Latest Tag Upgrade (Risky)

If using `latest` tag (not recommended for production):

```bash
# 1. Pull latest images
docker-compose -f docker-compose.prod.yml pull

# 2. Recreate containers
docker-compose -f docker-compose.prod.yml up -d

# 3. Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Method 3: Unraid Compose Manager

For Unraid users:

1. Go to **Docker** → **Compose Manager**
2. Select **roanes-kitchen** stack
3. Click **Pull** to download new images
4. Click **Compose Down**
5. Click **Compose Up**
6. Monitor logs in Unraid UI

## Database Migrations

### How Migrations Work

Migrations are handled by Alembic and run automatically via `entrypoint.sh`:

```bash
# This happens automatically on container start:
alembic upgrade head
```

### Migration Safety

- **Additive migrations** (new columns, tables) are safe - no data loss
- **Destructive migrations** (dropping columns) require special handling
- **Data migrations** may take time on large databases

### Monitoring Migration Progress

```bash
# Watch migration logs in real-time
docker-compose logs -f backend | grep alembic

# Check migration status after upgrade
docker exec roanes-kitchen-backend alembic current

# View migration history
docker exec roanes-kitchen-backend alembic history
```

### Large Database Migrations

For databases > 1GB, some migrations may take several minutes:

```bash
# Before upgrading, check database size
docker exec roanes-kitchen-postgres psql -U admin -d roanes_kitchen -c \
  "SELECT pg_size_pretty(pg_database_size('roanes_kitchen'));"

# Estimate migration time (rough guide):
# < 100MB: < 1 minute
# 100MB - 1GB: 1-5 minutes
# 1GB - 10GB: 5-30 minutes
# > 10GB: 30+ minutes
```

## Breaking Changes

### What Are Breaking Changes?

Changes that require manual intervention:

1. **Configuration changes** - New required environment variables
2. **API changes** - Endpoints removed or modified
3. **Data format changes** - Incompatible with old clients
4. **Behavior changes** - Features work differently

### Breaking Change Process

When a release has breaking changes, the CHANGELOG will include:

```markdown
## [2.0.0] - 2025-12-01

### BREAKING CHANGES

- **Environment Variables**: New required variable `NOTIFICATION_SERVICE`
  - Action: Add `NOTIFICATION_SERVICE=discord` to your .env file
  - Migration: See docs/upgrade-2.0.md for details

- **API**: Removed deprecated `/api/v1/meals` endpoint
  - Action: Update clients to use `/api/v2/meals`
  - Migration: Old endpoint returns 410 Gone with migration guide

- **Database**: Recipe schema restructured
  - Action: Automatic migration, but backup required
  - Downgrade: Not supported - must restore from backup
```

### Handling Breaking Changes

1. **Read the upgrade notes** - Check `docs/upgrade-X.Y.md` if it exists
2. **Update configuration** - Add new environment variables
3. **Update clients** - If using the API directly
4. **Test in staging** - If possible
5. **Backup before upgrading** - Required for MAJOR version bumps

### Major Version Upgrades (X.0.0)

Major versions may not support downgrade:

```bash
# Upgrading from v1.x to v2.x

# 1. BACKUP FIRST (critical!)
docker exec roanes-kitchen-postgres pg_dump -U admin roanes_kitchen > \
  backup-v1-final.sql

# 2. Read upgrade guide
# Visit: https://github.com/plongitudes/roanes-kitchen/blob/main/docs/upgrade-2.0.md

# 3. Update environment variables (if required)
# Edit .env file with new required variables

# 4. Pull new version
docker-compose -f docker-compose.prod.yml pull

# 5. Upgrade (point of no return)
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify
curl http://localhost:8000/health
```

## Rollback Procedures

### Scenario 1: Migration Failed

If migration fails, container won't start:

```bash
# 1. Check error in logs
docker-compose logs backend

# 2. Rollback to previous version
# Edit docker-compose.prod.yml - change version tag back
image: plongitudes/roanes-kitchen-backend:v1.1.0  # previous version

# 3. Restart
docker-compose down
docker-compose up -d
```

### Scenario 2: Application Issues After Upgrade

If app runs but has issues:

```bash
# 1. Rollback to previous image version
docker-compose -f docker-compose.prod.yml down

# Edit docker-compose.prod.yml - revert to old version
# image: plongitudes/roanes-kitchen-backend:v1.1.0

docker-compose -f docker-compose.prod.yml up -d

# 2. Database is likely ahead of code now
# Check migration status
docker exec roanes-kitchen-backend alembic current

# 3. If database is incompatible, restore from backup
```

### Scenario 3: Database Restore Required

If you need to restore from backup:

```bash
# 1. Stop all services
docker-compose down

# 2. Start only postgres
docker-compose up -d postgres

# 3. Drop and recreate database
docker exec roanes-kitchen-postgres psql -U admin -d postgres -c \
  "DROP DATABASE roanes_kitchen;"
docker exec roanes-kitchen-postgres psql -U admin -d postgres -c \
  "CREATE DATABASE roanes_kitchen;"

# 4. Restore from backup
docker exec -i roanes-kitchen-postgres psql -U admin -d roanes_kitchen < \
  backup-pre-upgrade-20251116.sql

# 5. Start services with OLD version
# (Make sure docker-compose.prod.yml has old version tag)
docker-compose up -d
```

## Version-Specific Upgrade Notes

### Upgrading to v1.0.0

First production release - fresh install only.

### Future Versions

Check the `docs/` directory for version-specific guides:
- `docs/upgrade-1.1.md` - Upgrading to v1.1.x
- `docs/upgrade-2.0.md` - Upgrading to v2.0.x

## Best Practices

### 1. Pin Versions in Production

**DON'T** use `latest` tag:
```yaml
# Bad
image: plongitudes/roanes-kitchen-backend:latest
```

**DO** use specific versions:
```yaml
# Good
image: plongitudes/roanes-kitchen-backend:v1.2.0

# Or floating minor version (gets patches automatically)
image: plongitudes/roanes-kitchen-backend:1.2
```

### 2. Test Upgrades

If you have multiple environments:

```bash
# 1. Test in staging first
cd /staging/roanes-kitchen
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 2. Verify everything works
curl http://staging-host:8000/health

# 3. Then upgrade production
cd /production/roanes-kitchen
# ... same steps
```

### 3. Backup Schedule

- **Before every upgrade** - Manual backup
- **Daily automated** - Via backup container (already configured)
- **Before major versions** - Multiple backups, test restore

### 4. Upgrade Window

Plan upgrades during low-usage times:
- Small upgrades: ~5 minutes downtime
- Major upgrades: ~15-30 minutes downtime
- Consider maintenance mode page

### 5. Monitor After Upgrade

```bash
# Check health
curl http://localhost:8000/health

# Watch logs for errors
docker-compose logs -f backend | grep ERROR

# Verify database
docker exec roanes-kitchen-backend alembic current

# Check all services healthy
docker ps
```

## Troubleshooting

### Migration Won't Run

**Error**: "Target database is not up to date"

```bash
# Check current version
docker exec roanes-kitchen-backend alembic current

# Manually run upgrade
docker exec roanes-kitchen-backend alembic upgrade head
```

### Database Connection Errors After Upgrade

**Error**: "FATAL: database 'roanes_kitchen' does not exist"

```bash
# Database was dropped - restore from backup
# See "Scenario 3: Database Restore Required" above
```

### Frontend Shows Old Version

Browser cache issue:

```bash
# Clear browser cache or hard reload
# Chrome/Firefox: Ctrl+Shift+R or Cmd+Shift+R

# Force frontend rebuild
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Migration Stuck/Taking Too Long

```bash
# Check if migration is running
docker exec roanes-kitchen-postgres psql -U admin -d roanes_kitchen -c \
  "SELECT * FROM pg_stat_activity WHERE datname = 'roanes_kitchen';"

# If stuck, you may need to stop and restore from backup
```

## Emergency Contacts

If you encounter critical upgrade issues:
- **GitHub Issues**: https://github.com/plongitudes/roanes-kitchen/issues
- **Label**: "upgrade" and "help wanted"
- **Include**: Version numbers, error logs, migration status

## Additional Resources

- [CHANGELOG.md](../CHANGELOG.md) - All version changes
- [VERSIONING.md](../.github/VERSIONING.md) - Version numbering strategy
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guides
- [Releases](https://github.com/plongitudes/roanes-kitchen/releases) - Download specific versions

---

**Remember**: Always backup before upgrading!
