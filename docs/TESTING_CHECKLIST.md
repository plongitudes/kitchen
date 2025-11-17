# Unraid End-to-End Testing Checklist

This checklist validates Roane's Kitchen on Unraid before v1.0.0 release.

## Prerequisites

- [ ] Unraid 6.10 or later
- [ ] Compose Manager plugin installed
- [ ] 2GB RAM available
- [ ] 5GB disk space available
- [ ] Network access for pulling Docker images

## Test 1: Fresh Installation

### Setup

- [ ] Create stack directory: `/mnt/user/appdata/roanes-kitchen`
- [ ] Copy `docker-compose.prod.yml` to stack directory
- [ ] Create `.env` file with secure credentials:
  ```bash
  POSTGRES_PASSWORD=$(openssl rand -base64 32)
  SECRET_KEY=$(openssl rand -base64 64)
  ENVIRONMENT=production
  APPDATA_PATH=/mnt/user/appdata/roanes-kitchen
  ```
- [ ] Set file permissions: `chmod 600 .env`

### Deployment

- [ ] Open Compose Manager in Unraid
- [ ] Add new stack named `roanes-kitchen`
- [ ] Point to docker-compose.prod.yml
- [ ] Click "Compose Up"
- [ ] Wait for all containers to start

### Verification

- [ ] All 3 containers running: `docker ps | grep roanes-kitchen`
- [ ] All containers show `(healthy)` status
- [ ] Backend logs show: "Starting application..."
- [ ] Frontend accessible at `http://[UNRAID-IP]:80`
- [ ] Backend API docs at `http://[UNRAID-IP]:8000/docs`
- [ ] No errors in logs: `docker-compose logs`

**Expected**: Fresh install completes in < 5 minutes, all services healthy.

## Test 2: User Management

### Create First User

- [ ] Navigate to frontend UI
- [ ] Register new user: `admin` / `secure-password-123`
- [ ] Login successful
- [ ] Dashboard loads without errors

### Multi-User Testing

- [ ] Create second user: `user2` / `password-456`
- [ ] Login as user2 in different browser/incognito
- [ ] Verify users see only their own data
- [ ] Logout and login as admin
- [ ] Admin can access all features

**Expected**: User registration and authentication work correctly.

## Test 3: Recipe Management

### Create Recipe

- [ ] Click "Add Recipe"
- [ ] Enter recipe details:
  - Title: "Test Recipe"
  - Ingredients: "2 eggs, 1 cup flour"
  - Instructions: "Mix and bake"
- [ ] Save recipe
- [ ] Recipe appears in list

### Edit Recipe

- [ ] Click recipe to view
- [ ] Edit title to "Updated Recipe"
- [ ] Save changes
- [ ] Changes persist after refresh

### Delete Recipe

- [ ] Delete test recipe
- [ ] Confirm deletion
- [ ] Recipe removed from list

**Expected**: Full CRUD operations work for recipes.

## Test 4: Meal Planning

### Create Schedule

- [ ] Navigate to Schedules
- [ ] Create new schedule for current week
- [ ] Assign recipes to meals (breakfast, lunch, dinner)
- [ ] Save schedule

### View Schedule

- [ ] View schedule calendar
- [ ] Verify assigned recipes display correctly
- [ ] Check grocery list generates from schedule

**Expected**: Scheduling and grocery list generation work.

## Test 5: Backup and Restore

### Create Backup

- [ ] Login and get auth token:
  ```bash
  TOKEN=$(curl -X POST http://[UNRAID-IP]:8000/auth/token \
    -d "username=admin&password=secure-password-123" \
    | jq -r .access_token)
  ```
- [ ] Create backup:
  ```bash
  curl -X POST http://[UNRAID-IP]:8000/backup/create \
    -H "Authorization: Bearer $TOKEN"
  ```
- [ ] Verify backup created in `/mnt/user/appdata/roanes-kitchen/backups/`
- [ ] Check file size > 0 bytes

### Test Restore

- [ ] Note current recipe count
- [ ] Create new test recipe
- [ ] Restore from backup:
  ```bash
  curl -X POST http://[UNRAID-IP]:8000/backup/restore/FILENAME \
    -H "Authorization: Bearer $TOKEN"
  ```
- [ ] Refresh frontend (database connection reset)
- [ ] Login again
- [ ] Verify new recipe gone (rolled back)
- [ ] Original data intact

### Verify No Docker Socket

- [ ] Check backend container:
  ```bash
  docker inspect roanes-kitchen-backend | grep -i "/var/run/docker.sock"
  ```
- [ ] Should return empty (no Docker socket mount)

**Expected**: Backup/restore works without Docker socket access.

## Test 6: Persistence

### Stop and Restart

- [ ] Note current data (recipes, users, schedules)
- [ ] Stop all containers:
  ```bash
  cd /mnt/user/appdata/roanes-kitchen
  docker-compose -f docker-compose.prod.yml down
  ```
- [ ] Wait 10 seconds
- [ ] Start containers:
  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```
- [ ] Wait for health checks to pass
- [ ] Login to frontend
- [ ] Verify all data intact

**Expected**: Data persists across container restarts.

## Test 7: Health Checks

### Monitor Health Status

- [ ] Check all services healthy:
  ```bash
  docker ps --format "table {{.Names}}\t{{.Status}}"
  ```
- [ ] All should show `(healthy)`
- [ ] Check health endpoints:
  ```bash
  curl http://[UNRAID-IP]:8000/health
  # Should return: {"status":"healthy",...}
  ```

### Simulate Failure

- [ ] Stop postgres manually:
  ```bash
  docker stop roanes-kitchen-postgres
  ```
- [ ] Wait 60 seconds
- [ ] Check backend status changes to `(unhealthy)`
- [ ] Start postgres:
  ```bash
  docker start roanes-kitchen-postgres
  ```
- [ ] Backend recovers to `(healthy)` within 60 seconds

**Expected**: Health checks detect failures and recovery.

## Test 8: Discord Notifications (Optional)

Only if you have a Discord bot configured:

### Setup

- [ ] Add to `.env`:
  ```env
  DISCORD_BOT_TOKEN=your-bot-token
  DISCORD_CHANNEL_ID=your-channel-id
  ```
- [ ] Restart backend:
  ```bash
  docker-compose -f docker-compose.prod.yml restart backend
  ```

### Test Notification

- [ ] Trigger notification via API or scheduled job
- [ ] Verify message appears in Discord channel
- [ ] Check backend logs for "Discord notification sent"

**Expected**: Discord integration works if configured.

## Test 9: Performance

### Response Time

- [ ] Measure API response time:
  ```bash
  time curl http://[UNRAID-IP]:8000/health
  ```
- [ ] Should be < 100ms
- [ ] Frontend page load < 2 seconds

### Resource Usage

- [ ] Check container stats:
  ```bash
  docker stats --no-stream
  ```
- [ ] Backend: < 200MB RAM
- [ ] Frontend: < 50MB RAM
- [ ] Postgres: < 100MB RAM (empty database)

### Load Test

- [ ] Create 10 recipes
- [ ] Create 5 schedules
- [ ] Check response times still acceptable
- [ ] No memory leaks over 1 hour

**Expected**: Acceptable performance on Unraid hardware.

## Test 10: Upgrade Path

### Simulate Upgrade

- [ ] Check current version:
  ```bash
  docker images | grep roanes-kitchen
  ```
- [ ] Create backup (see Test 5)
- [ ] Pull new version:
  ```bash
  docker-compose -f docker-compose.prod.yml pull
  ```
- [ ] Restart containers:
  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```
- [ ] Check logs for migration messages
- [ ] Verify data intact
- [ ] Test all functionality

**Expected**: Upgrade process smooth, data preserved.

## Test 11: Documentation Validation

### Follow README

- [ ] Open README.md
- [ ] Follow "Production Deployment" section exactly
- [ ] Note any confusing or missing steps
- [ ] Verify environment variables documented
- [ ] Check deployment guide matches actual process

### Follow Unraid Guide

- [ ] Open docs/DEPLOYMENT.md
- [ ] Follow Unraid deployment steps
- [ ] Verify all commands work
- [ ] Check troubleshooting section helpful

**Expected**: Documentation accurate and complete.

## Test 12: Security Validation

### Credential Security

- [ ] Verify no default passwords in production
- [ ] Check `.env` file permissions (600)
- [ ] Ensure `.env` not in git
- [ ] Verify strong password generation documented

### Container Security

- [ ] Verify backend runs as non-root:
  ```bash
  docker exec roanes-kitchen-backend whoami
  # Should return: appuser
  ```
- [ ] Check no Docker socket:
  ```bash
  docker inspect roanes-kitchen-backend | grep docker.sock
  # Should return nothing
  ```

### Network Security

- [ ] Verify postgres not externally accessible:
  ```bash
  netstat -tulpn | grep 5432
  # Should show only internal Docker network
  ```
- [ ] Check HTTPS documentation in SECURITY.md

**Expected**: All security best practices followed.

## Issues Found

Document any issues encountered:

| Test # | Issue | Severity | Workaround | Fixed? |
|--------|-------|----------|------------|--------|
|        |       |          |            |        |

## Sign-Off

- [ ] All critical tests passed
- [ ] All high-priority tests passed
- [ ] Documentation validated
- [ ] Security checks passed
- [ ] Performance acceptable
- [ ] Ready for v1.0.0 release

**Tester**: ___________________
**Date**: ___________________
**Unraid Version**: ___________________
**Hardware**: ___________________

---

## Notes

Add any additional observations or recommendations:
