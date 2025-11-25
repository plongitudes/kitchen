# Kitchen - Unraid Installation Guide

This guide explains how to install Kitchen on Unraid using the Community Applications templates.

## Overview

Kitchen is a meal planning and recipe management application that consists of three Docker containers:
1. **kitchen-postgres** - PostgreSQL database
2. **kitchen-backend** - FastAPI backend API
3. **kitchen-frontend** - React web interface

## Prerequisites

- Unraid 7.1.4 or later
- Community Applications plugin installed

## Installation Steps

### Step 1: Create the Docker Network

Before installing any containers, create the shared network:

1. Open a terminal (Unraid console or SSH)
2. Run: `docker network create kitchen-network`

### Step 2: Install kitchen-postgres

1. Go to **Apps** tab in Unraid
2. Search for "kitchen-postgres" or add the template manually
3. Configure the following **REQUIRED** settings:
   - **PostgreSQL Password**: Generate a secure password (save this!)
     ```bash
     openssl rand -base64 32
     ```
   - **Database Data Path**: Default is `/mnt/user/appdata/kitchen/postgres` (recommended)
4. Leave other settings at defaults
5. Click **Apply** to start the container
6. **Wait for the container to be fully healthy** (check Docker tab - health status should show healthy)

### Step 3: Install kitchen-backend

1. Go to **Apps** tab
2. Search for "kitchen-backend" or add the template manually
3. Configure the following **REQUIRED** settings:

   **Database Configuration:**
   - **Database URL**:
     ```
     postgresql+asyncpg://admin:[YOUR_POSTGRES_PASSWORD]@kitchen-postgres:5432/roanes_kitchen
     ```
     Replace `[YOUR_POSTGRES_PASSWORD]` with the password from Step 2

   **Security Configuration:**
   - **JWT Secret Key**: Generate a secure key
     ```bash
     openssl rand -base64 64
     ```

   **Application Configuration:**
   - **Backend API Port**: Default `8000` (change if needed)
   - **Frontend URL**: Your Unraid server URL (e.g., `http://192.168.1.100:8080` or `http://tower.local:8080`)
   - **Environment**: `production`
   - **Debug Mode**: `false`

   **Optional Discord Configuration** (for meal plan notifications):
   - **Discord Bot Token**: Your Discord bot token (leave empty to disable)
   - **Discord Notification Channel ID**: Channel ID for meal plan notifications
   - **Discord Test Channel ID**: Channel ID for test messages

   **Storage:**
   - **Application Logs**: Default is `/mnt/user/appdata/kitchen/logs` (recommended)

4. Click **Apply** to start the container
5. **Wait for the container to be fully healthy** (this may take 30-60 seconds as migrations run)
6. Check logs to verify migrations completed successfully:
   ```
   Docker tab → kitchen-backend → Logs
   ```
   You should see: "Running database migrations..." followed by "Starting application..."

### Step 4: Install kitchen-frontend

1. Go to **Apps** tab
2. Search for "kitchen-frontend" or add the template manually
3. Configure the following **REQUIRED** settings:
   - **Web UI Port**: Default `8080` (change if port 8080 is already in use)
   - **Backend API URL**: Must match your backend configuration
     ```
     http://[YOUR_UNRAID_IP]:8000
     ```
     Examples:
     - `http://192.168.1.100:8000`
     - `http://tower.local:8000`

     **IMPORTANT**: Use your actual Unraid server IP or hostname, NOT `localhost`

4. Click **Apply** to start the container

### Step 5: Access Kitchen

1. Open your web browser
2. Navigate to: `http://[YOUR_UNRAID_IP]:[FRONTEND_PORT]`
   - Example: `http://192.168.1.100:8080`
3. Register a new user account or use the demo account (if backend is in development mode):
   - Username: `demo`
   - Password: `demo1234`

## Port Reference

| Container | Default Port | Purpose |
|-----------|-------------|---------|
| kitchen-postgres | 5432 (internal) | PostgreSQL database (not exposed to host) |
| kitchen-backend | 8000 | Backend API (access API docs at /docs) |
| kitchen-frontend | 8080 | Web interface |

## Data Persistence

All application data is stored in `/mnt/user/appdata/kitchen/`:
- `postgres/` - Database files
- `logs/` - Application logs

**IMPORTANT**: Do not delete these directories unless you want to completely reset the application!

## Troubleshooting

### Backend won't start / "relation 'users' does not exist" error

This means the database migrations didn't run properly. To fix:

1. Stop all Kitchen containers
2. Open terminal and run:
   ```bash
   docker exec -it kitchen-postgres psql -U admin -d roanes_kitchen -c "DROP DATABASE roanes_kitchen;"
   docker exec -it kitchen-postgres psql -U admin -d roanes_kitchen -c "CREATE DATABASE roanes_kitchen;"
   ```
3. Start kitchen-backend (migrations will run automatically)
4. Start kitchen-frontend

### Frontend shows "Network Error" or can't connect to backend

1. Verify kitchen-backend is running and healthy (Docker tab)
2. Check that the **Backend API URL** in kitchen-frontend matches your actual backend URL
   - Must use your Unraid server IP (not `localhost`)
   - Port must match backend configuration
3. Test backend API directly: `http://[YOUR_UNRAID_IP]:8000/health`
   - Should return: `{"status":"healthy"}`

### Can't access web interface

1. Verify kitchen-frontend is running (Docker tab)
2. Check for port conflicts - ensure no other container is using the same port
3. Try accessing from the Unraid WebUI link (Docker tab → kitchen-frontend → WebUI button)

### Discord notifications not working

1. Verify Discord bot token is correct
2. Verify channel IDs are correct (right-click channel in Discord → Copy Channel ID)
3. Ensure bot has permissions to post in the channels
4. Check backend logs for Discord-related errors:
   ```
   Docker tab → kitchen-backend → Logs
   ```

## Updating Kitchen

To update to the latest version:

1. Go to Docker tab
2. For each container (frontend, backend, postgres):
   - Click the container icon
   - Click "Force Update"
   - Click "Apply"
3. Restart containers in order:
   - kitchen-postgres (usually no changes needed)
   - kitchen-backend (migrations will run automatically if needed)
   - kitchen-frontend

**Note**: Always update backend before frontend to ensure API compatibility.

## Uninstalling Kitchen

To completely remove Kitchen:

1. Stop and remove all containers (Docker tab)
2. Remove the Docker network:
   ```bash
   docker network rm kitchen-network
   ```
3. (Optional) Delete application data:
   ```bash
   rm -rf /mnt/user/appdata/kitchen
   ```
   **WARNING**: This deletes all recipes, meal plans, and user data permanently!

## Security Best Practices

1. **Change default passwords**: Always use generated passwords for POSTGRES_PASSWORD and JWT_SECRET_KEY
2. **Use HTTPS**: Consider setting up a reverse proxy (like nginx or Swag) with SSL certificates
3. **Regular backups**: Back up `/mnt/user/appdata/kitchen/postgres` directory regularly
4. **Keep updated**: Update containers regularly to get security patches

## Support

- GitHub Issues: https://github.com/plongitudes/kitchen/issues
- Documentation: https://github.com/plongitudes/kitchen

## Advanced: Manual Template Installation

If the templates aren't available in Community Applications:

1. Download the XML files from:
   - https://raw.githubusercontent.com/plongitudes/kitchen/main/unraid/kitchen-postgres.xml
   - https://raw.githubusercontent.com/plongitudes/kitchen/main/unraid/kitchen-backend.xml
   - https://raw.githubusercontent.com/plongitudes/kitchen/main/unraid/kitchen-frontend.xml

2. Go to Docker tab → Add Container → Template repositories
3. Paste each template URL and apply

Or install via User Scripts:
```bash
# Create network
docker network create kitchen-network

# Start postgres
docker run -d \
  --name kitchen-postgres \
  --network kitchen-network \
  --restart unless-stopped \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=YOUR_PASSWORD_HERE \
  -e POSTGRES_DB=roanes_kitchen \
  -v /mnt/user/appdata/kitchen/postgres:/var/lib/postgresql/data \
  postgres:15.10-alpine

# Start backend (update environment variables!)
docker run -d \
  --name kitchen-backend \
  --network kitchen-network \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://admin:YOUR_PASSWORD_HERE@kitchen-postgres:5432/roanes_kitchen" \
  -e JWT_SECRET_KEY="YOUR_JWT_SECRET_HERE" \
  -e ENVIRONMENT=production \
  -e DEBUG=false \
  -v /mnt/user/appdata/kitchen/logs:/app/logs \
  plongitudex/kitchen-backend:latest

# Start frontend
docker run -d \
  --name kitchen-frontend \
  --network kitchen-network \
  --restart unless-stopped \
  -p 8080:80 \
  -e API_URL="http://YOUR_UNRAID_IP:8000" \
  plongitudex/kitchen-frontend:latest
```
