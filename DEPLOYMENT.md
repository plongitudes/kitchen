# Roanes Kitchen - Deployment Guide

This guide covers deploying Roanes Kitchen to an Unraid server using Docker Compose.

## Prerequisites

- Unraid server with Docker support
- Tailscale configured for remote access
- Git installed on Unraid (via Nerd Tools plugin)
- At least 2GB of available storage in appdata share

## Quick Start

### 1. Clone the Repository

SSH into your Unraid server and clone the repository:

```bash
cd /mnt/user/appdata
git clone <repository-url> kitchen
cd kitchen
```

### 2. Configure Environment

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` with your production values:

```bash
nano .env
```

**Important configurations to change:**

- `POSTGRES_PASSWORD`: Set a strong database password
- `JWT_SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `VITE_API_URL`: Set to your server's Tailscale address or local IP

### 3. Deploy

Start all services:

```bash
docker-compose -f docker-compose.prod.yml --env-file .env up -d
```

Check service status:

```bash
docker-compose -f docker-compose.prod.yml ps
```

View logs:

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Initialize Database

The database will be automatically initialized on first run via the backend's entrypoint script.

### 5. Access the Application

- **Frontend**: http://your-server-ip (port 80)
- **Backend API**: http://your-server-ip:8000
- **API Docs**: http://your-server-ip:8000/docs

## Architecture

### Services

1. **postgres**: PostgreSQL 15 database
   - Data stored in `/mnt/user/appdata/kitchen/postgres`
   - Healthchecks enabled
   - Persistent storage

2. **backend**: FastAPI application
   - Python 3.11
   - Async PostgreSQL connection
   - Auto-restarts on failure
   - Logs in `/mnt/user/appdata/kitchen/logs`

3. **frontend**: React + Vite application
   - Multi-stage build (Node.js build → Nginx serve)
   - Optimized static assets
   - SPA routing configured

4. **backup**: Automated PostgreSQL backups
   - Runs daily at 2:00 AM
   - Compressed SQL dumps
   - 30-day retention (configurable)
   - Backups in `/mnt/user/appdata/kitchen/backups`

### Volume Mappings

All data is stored in `/mnt/user/appdata/kitchen/`:

```
/mnt/user/appdata/kitchen/
├── postgres/          # Database files
├── backups/           # SQL dump backups
│   ├── roanes_kitchen_YYYYMMDD_HHMMSS.sql.gz
│   └── backup.log
└── logs/              # Application logs
```

## Backup & Restore

### Automated Backups

Backups run automatically daily at 2:00 AM. Configuration:

- **Schedule**: Daily at 2:00 AM (configured in `scripts/crontab`)
- **Location**: `/mnt/user/appdata/kitchen/backups`
- **Format**: Compressed SQL dumps (`roanes_kitchen_YYYYMMDD_HHMMSS.sql.gz`)
- **Retention**: 30 days (configurable via `BACKUP_RETENTION_DAYS`)
- **Logs**: `/mnt/user/appdata/kitchen/backups/backup.log`

### Manual Backup

To manually trigger a backup:

```bash
docker exec kitchen-backup /backup.sh
```

### Restore from Backup

1. Stop the backend service:
```bash
docker-compose -f docker-compose.prod.yml stop backend
```

2. Restore the database:
```bash
# Find the backup file you want to restore
ls -lh /mnt/user/appdata/kitchen/backups/

# Restore (replace YYYYMMDD_HHMMSS with your backup timestamp)
gunzip -c /mnt/user/appdata/kitchen/backups/roanes_kitchen_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i kitchen-postgres psql -U admin -d roanes_kitchen
```

3. Restart the backend:
```bash
docker-compose -f docker-compose.prod.yml start backend
```

## Maintenance

### Viewing Logs

All services:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

Specific service:
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

Application logs:
```bash
tail -f /mnt/user/appdata/kitchen/logs/*.log
```

Backup logs:
```bash
tail -f /mnt/user/appdata/kitchen/backups/backup.log
```

### Updating the Application

```bash
cd /mnt/user/appdata/kitchen
git pull
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml --env-file .env up -d
```

### Restarting Services

All services:
```bash
docker-compose -f docker-compose.prod.yml restart
```

Specific service:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Stopping Services

```bash
docker-compose -f docker-compose.prod.yml down
```

To also remove volumes (⚠️ **WARNING: This deletes all data!**):
```bash
docker-compose -f docker-compose.prod.yml down -v
```

## Troubleshooting

### Services Won't Start

Check service status and logs:
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

### Database Connection Issues

1. Verify postgres is healthy:
```bash
docker-compose -f docker-compose.prod.yml ps postgres
```

2. Check database connectivity:
```bash
docker exec kitchen-postgres pg_isready -U admin -d roanes_kitchen
```

### Frontend Can't Connect to Backend

1. Check `VITE_API_URL` in `.env`
2. Ensure backend is accessible on port 8000
3. Check browser console for CORS errors

### Backup Not Running

1. Check cron is running in backup container:
```bash
docker exec kitchen-backup ps aux | grep crond
```

2. View backup logs:
```bash
docker exec kitchen-backup cat /backups/backup.log
```

3. Manually test backup:
```bash
docker exec kitchen-backup /backup.sh
```

## Security Considerations

### For Production Deployment

1. **Change default passwords**:
   - Set strong `POSTGRES_PASSWORD`
   - Generate random `SECRET_KEY`

2. **Firewall configuration**:
   - Only expose necessary ports
   - Use Tailscale for remote access
   - Consider reverse proxy (e.g., Nginx Proxy Manager)

3. **Regular updates**:
   - Keep Docker images updated
   - Monitor security advisories
   - Regular `git pull` for application updates

4. **Backup verification**:
   - Periodically test backup restoration
   - Monitor backup log for failures
   - Ensure backups are being created

## Performance Tuning

### Backend Workers

By default, the backend runs with 2 workers. Adjust in `docker-compose.prod.yml`:

```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Recommended: 2-4 workers for typical usage.

### Database Configuration

For better performance with larger datasets, consider tuning PostgreSQL settings by creating a custom `postgresql.conf` and mounting it in the postgres service.

## Monitoring

### Health Checks

All services have health checks configured:

- **postgres**: `pg_isready` check every 30s
- **frontend**: Nginx `/health` endpoint

### Resource Usage

Monitor with `docker stats`:
```bash
docker stats kitchen-postgres kitchen-backend kitchen-frontend
```

## Unraid-Specific Tips

### Auto-start on Boot

To ensure services start automatically when Unraid boots:

1. The `restart: unless-stopped` policy handles this automatically
2. Verify in Unraid Docker UI that auto-start is enabled

### Updating via Unraid UI

While you can manage containers via the Unraid UI, it's recommended to use docker-compose for consistency with multi-container setups.

### Notifications

Configure Unraid notifications for:
- Docker container crashes
- Array/disk issues
- Backup verification (via User Scripts plugin)

## Support

For issues or questions:
1. Check logs first: `docker-compose -f docker-compose.prod.yml logs`
2. Verify all environment variables in `.env`
3. Consult the main README.md for application-specific details
