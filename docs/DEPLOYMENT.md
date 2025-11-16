# Unraid Deployment Guide

This guide walks through deploying Roane's Kitchen on Unraid.

## Prerequisites

- Unraid 6.10 or later
- Compose Manager plugin (recommended) or Docker Compose installed
- 2GB RAM minimum
- 5GB disk space

## Deployment Method

Roane's Kitchen is a multi-container application (frontend, backend, database). There are two recommended approaches for Unraid:

### Method 1: Docker Compose (Recommended)

This is the easiest and most maintainable approach.

#### Step 1: Install Compose Manager

1. Go to **Apps** tab in Unraid
2. Search for "Compose Manager"
3. Click Install and follow prompts

#### Step 2: Create Compose Stack

1. Navigate to **Docker** tab → **Compose Manager**
2. Click **Add New Stack**
3. Stack Name: `roanes-kitchen`
4. Copy the production docker-compose.yml from the repository
5. Customize environment variables (see Configuration below)

#### Step 3: Configure Environment

Create a `.env` file in your stack directory:

```env
# Database
POSTGRES_PASSWORD=your-secure-password-here

# Backend
SECRET_KEY=your-secret-key-change-this
ENVIRONMENT=production

# Discord Notifications (Optional)
DISCORD_BOT_TOKEN=
DISCORD_CHANNEL_ID=

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=8080

# Unraid Paths
APPDATA_PATH=/mnt/user/appdata/roanes-kitchen
```

#### Step 4: Configure Volume Paths

In docker-compose.prod.yml, ensure volumes map to Unraid paths:

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/user/appdata/roanes-kitchen/postgres

  backups:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/user/backups/roanes-kitchen
```

#### Step 5: Start the Stack

1. Click **Compose Up**
2. Wait for all containers to start
3. Verify all services are healthy: `docker ps`

#### Step 6: Access Application

Navigate to: `http://[UNRAID-IP]:8080`

Default login: `demo` / `demo123` (change immediately)

### Method 2: Individual Docker Containers

While possible, this method requires manually creating 3+ containers and managing networking between them. **Not recommended** - use Compose Manager instead.

## Configuration

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Database password | `admin` (change!) |
| `SECRET_KEY` | Backend JWT secret | Required |
| `ENVIRONMENT` | Environment mode | `production` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token | (none) |
| `DISCORD_CHANNEL_ID` | Discord channel ID | (none) |
| `BACKEND_PORT` | Backend API port | `8000` |
| `FRONTEND_PORT` | Frontend web port | `80` |
| `BACKUP_RETENTION_DAYS` | Backup retention | `30` |

### Volume Mappings

| Container Path | Unraid Path | Description |
|----------------|-------------|-------------|
| `/var/lib/postgresql/data` | `/mnt/user/appdata/roanes-kitchen/postgres` | Database storage |
| `/backups` | `/mnt/user/backups/roanes-kitchen` | Database backups |
| `/app/logs` | `/mnt/user/appdata/roanes-kitchen/logs` | Application logs |

### Port Mappings

| Container Port | Host Port | Description |
|----------------|-----------|-------------|
| `80` | `8080` | Frontend web UI |
| `8000` | `8000` | Backend API |
| `5432` | (internal) | PostgreSQL (no external access) |

## Security Best Practices

### 1. Change Default Credentials

After first login:
1. Go to Settings → Users
2. Delete or disable `demo` user
3. Create your own admin user

### 2. Secure Environment Variables

```bash
# Generate secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
```

### 3. Restrict Network Access

In Compose Manager, set network to `bridge` mode and use Nginx Proxy Manager or similar for HTTPS.

### 4. Enable Backups

The backup container runs daily backups by default. Verify:

```bash
docker exec roanes-kitchen-backup ls -lh /backups
```

## Maintenance

### Updating

```bash
# Using Compose Manager
1. Go to Docker → Compose Manager
2. Select roanes-kitchen stack
3. Click "Pull" to get latest images
4. Click "Compose Down" then "Compose Up"

# Or manually
cd /path/to/roanes-kitchen
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs

# Specific service
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Follow logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Database Backup

Automatic backups run daily. To manually trigger:

```bash
docker exec roanes-kitchen-backup /backup.sh
```

Backups are stored in: `/mnt/user/backups/roanes-kitchen/`

### Restore from Backup

```bash
# Stop services
docker-compose -f docker-compose.prod.yml stop backend

# Use the restore API endpoint
curl -X POST http://localhost:8000/backup/restore/FILENAME \
  -H "Authorization: Bearer YOUR_TOKEN"

# Or manually restore
docker exec roanes-kitchen-postgres psql -U admin -d postgres -c "DROP DATABASE roanes_kitchen;"
docker exec roanes-kitchen-postgres psql -U admin -d postgres -c "CREATE DATABASE roanes_kitchen;"
docker exec -i roanes-kitchen-postgres psql -U admin -d roanes_kitchen < /path/to/backup.sql

# Restart services
docker-compose -f docker-compose.prod.yml start backend
```

## Troubleshooting

### Frontend shows "API Error"

**Cause:** Backend not accessible or environment variable misconfigured

**Solution:**
1. Check backend is running: `docker ps | grep backend`
2. Check backend logs: `docker-compose logs backend`
3. Verify `VITE_API_URL` points to correct backend URL

### Database connection errors

**Cause:** PostgreSQL not ready or wrong credentials

**Solution:**
1. Check postgres health: `docker ps | grep postgres`
2. Verify `DATABASE_URL` in backend environment
3. Check postgres logs: `docker-compose logs postgres`

### Permission denied errors

**Cause:** Volume permissions mismatch

**Solution:**
```bash
# Set correct ownership
chown -R 1000:1000 /mnt/user/appdata/roanes-kitchen
chown -R 1000:1000 /mnt/user/backups/roanes-kitchen
```

### Services won't start

**Cause:** Port conflicts or missing dependencies

**Solution:**
1. Check for port conflicts: `netstat -tulpn | grep 8080`
2. Verify all environment variables are set
3. Check docker-compose.prod.yml syntax

## Advanced Configuration

### Custom Backup Schedule

Edit the backup crontab:

```bash
# Edit crontab file
vi scripts/crontab

# Default: Daily at 2 AM
0 2 * * * /backup.sh

# Example: Every 6 hours
0 */6 * * * /backup.sh
```

### HTTPS with Nginx Proxy Manager

1. Install Nginx Proxy Manager from Community Applications
2. Add proxy host:
   - Domain: `meals.yourdomain.com`
   - Forward Hostname/IP: `roanes-kitchen-frontend`
   - Forward Port: `80`
   - Enable SSL with Let's Encrypt

### Discord Notifications

See main README for Discord bot setup instructions.

## Migration from Docker to Compose

If you previously installed individual containers:

1. **Backup your database**:
   ```bash
   docker exec roanes-kitchen-postgres pg_dump -U admin roanes_kitchen > backup.sql
   ```

2. **Stop old containers**:
   ```bash
   docker stop roanes-kitchen-backend roanes-kitchen-frontend roanes-kitchen-postgres
   ```

3. **Deploy with Compose Manager** (see Method 1 above)

4. **Restore backup** if needed

## Support

- **Issues**: https://github.com/plongitudes/roanes-kitchen/issues
- **Documentation**: https://github.com/plongitudes/roanes-kitchen
- **Unraid Forums**: Post in Docker Support section

## Version Information

Check running versions:

```bash
docker exec roanes-kitchen-backend python -c "from app import __version__; print(__version__)"
```

Or check Docker image tags:

```bash
docker images | grep roanes-kitchen
```

---

For the latest deployment instructions, visit the [GitHub repository](https://github.com/plongitudes/roanes-kitchen).
