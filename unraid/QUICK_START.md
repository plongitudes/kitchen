# Kitchen Unraid - Quick Start Checklist

## Before You Start

Generate these values and save them:

```bash
# PostgreSQL Password
openssl rand -base64 32

# JWT Secret Key
openssl rand -base64 64
```

## Installation Order

### ☐ Step 1: Create Network
```bash
docker network create kitchen-network
```

### ☐ Step 2: Install kitchen-postgres
- PostgreSQL Password: `[paste your generated password]`
- Database Data Path: `/mnt/user/appdata/kitchen/postgres`
- **Wait for healthy status** ✓

### ☐ Step 3: Install kitchen-backend
- Database URL:
  ```
  postgresql+asyncpg://admin:[POSTGRES_PASSWORD]@kitchen-postgres:5432/roanes_kitchen
  ```
- JWT Secret Key: `[paste your generated key]`
- Backend Port: `8000`
- Frontend URL: `http://[YOUR_IP]:8080` (e.g., `http://192.168.1.100:8080`)
- Environment: `production`
- Debug: `false`
- Logs Path: `/mnt/user/appdata/kitchen/logs`
- **Wait for healthy status** ✓
- **Check logs for successful migrations** ✓

### ☐ Step 4: Install kitchen-frontend
- Web UI Port: `8080`
- Backend API URL: `http://[YOUR_IP]:8000` (e.g., `http://192.168.1.100:8000`)

### ☐ Step 5: Test Access
- Open browser: `http://[YOUR_IP]:8080`
- Register new user
- Test basic functionality

## Quick Reference

| Container | Port | URL |
|-----------|------|-----|
| Frontend | 8080 | `http://[IP]:8080` |
| Backend | 8000 | `http://[IP]:8000/docs` |
| Postgres | 5432 | Internal only |

## Common Issues

**"relation 'users' does not exist"**
```bash
docker exec kitchen-postgres psql -U admin -d postgres -c "DROP DATABASE roanes_kitchen;"
docker exec kitchen-postgres psql -U admin -d postgres -c "CREATE DATABASE roanes_kitchen;"
# Then restart kitchen-backend
```

**Frontend can't connect to backend**
- Check Backend API URL uses actual IP (not localhost)
- Verify backend port matches
- Test: `http://[IP]:8000/health` should return `{"status":"healthy"}`

**Discord notifications not working**
- Verify bot token is correct
- Verify channel IDs are correct
- Check bot has permission to post
- Review backend logs for errors

## Data Locations

- Database: `/mnt/user/appdata/kitchen/postgres`
- Logs: `/mnt/user/appdata/kitchen/logs`

**Backup these directories regularly!**
