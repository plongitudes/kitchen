# Roane's Kitchen

> A meal planning and recipe management system designed to help you do better at adulting.

[![Docker Build](https://github.com/plongitudes/roanes-kitchen/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/plongitudes/roanes-kitchen/actions/workflows/docker-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Roane's Kitchen is a self-hosted meal planning and recipe management application that helps you organize weekly meal schedules, manage recipes, and receive Discord notifications for meal prep reminders.

## Features

- **Meal Planning** - Create and manage weekly meal schedules with breakfast, lunch, and dinner
- **Recipe Management** - Store and organize your favorite recipes with ingredients and instructions
- **Sequence Planning** - Build multi-week meal rotation sequences
- **Discord Notifications** - Automated reminders sent to your Discord channel
- **Backup & Restore** - Built-in database backup and restore functionality
- **Docker-Based** - Easy deployment with Docker Compose
- **Multi-Architecture** - Supports amd64 and arm64 platforms

## Quick Start

Get up and running in 5 minutes:

```bash
# Clone the repository
git clone https://github.com/plongitudes/roanes-kitchen.git
cd roanes-kitchen

# Start the services
docker-compose up -d

# Access the application
open http://localhost:5173
```

Default credentials: `demo` / `demo123`

## Architecture

Roane's Kitchen consists of three main services:

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Frontend  │────▶│   Backend   │────▶│  PostgreSQL  │
│  (React +   │     │  (FastAPI)  │     │  (Database)  │
│   Vite)     │     │             │     │              │
│  Port 5173  │     │  Port 8000  │     │  Port 5432   │
└─────────────┘     └─────────────┘     └──────────────┘
```

- **Frontend**: React + TypeScript + Tailwind CSS (Vite dev server)
- **Backend**: Python FastAPI with async SQLAlchemy
- **Database**: PostgreSQL 15 with automated migrations (Alembic)

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **System Requirements**:
  - 2GB RAM minimum
  - 1GB disk space for application + database
- **Optional**:
  - Discord Bot Token for notifications

## Development Setup

### 1. Clone and Configure

```bash
git clone https://github.com/plongitudes/roanes-kitchen.git
cd roanes-kitchen

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Start Services

```bash
# Start all services in development mode
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Development Workflow

```bash
# Restart backend after code changes
docker-compose restart backend

# Run backend tests
docker-compose exec backend pytest

# Frontend hot-reload is automatic (Vite)
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback last migration
docker-compose exec backend alembic downgrade -1
```

## Production Deployment

### Docker Compose (Recommended)

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Or pull pre-built images from Docker Hub
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_PASSWORD=your-secure-password

# Backend
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production

# Discord (Optional)
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=80

# Unraid (Optional)
APPDATA_PATH=/mnt/user/appdata/roanes-kitchen
```

### Unraid Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed Unraid setup instructions.

## Docker Images

Pre-built images are available on Docker Hub:

- `plongitudes/roanes-kitchen-backend:latest`
- `plongitudes/roanes-kitchen-frontend:latest`

Use version tags for production:
- `plongitudes/roanes-kitchen-backend:v1.0.0`
- `plongitudes/roanes-kitchen-backend:1.0`
- `plongitudes/roanes-kitchen-backend:1`

## Discord Notifications Setup

1. Create a Discord Bot:
   - Go to https://discord.com/developers/applications
   - Create a New Application
   - Go to "Bot" section and create a bot
   - Copy the Bot Token

2. Add Bot to Your Server:
   - Go to OAuth2 → URL Generator
   - Select scopes: `bot`
   - Select permissions: `Send Messages`, `Embed Links`
   - Use generated URL to add bot to server

3. Get Channel ID:
   - Enable Developer Mode in Discord (User Settings → Advanced)
   - Right-click your channel → Copy ID

4. Update Environment Variables:
   ```env
   DISCORD_BOT_TOKEN=your-bot-token-here
   DISCORD_CHANNEL_ID=your-channel-id-here
   ```

## Backup and Restore

### Create Backup

```bash
curl -X POST http://localhost:8000/backup/create \
  -H "Authorization: Bearer YOUR_TOKEN"

# Download backup
curl http://localhost:8000/backup/download/FILENAME \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o backup.sql
```

### Restore Backup

```bash
# Upload backup file
curl -X POST http://localhost:8000/backup/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@backup.sql"

# Restore from uploaded file
curl -X POST http://localhost:8000/backup/restore/backup.sql \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
roanes-kitchen/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration and dependencies
│   │   ├── models/      # SQLAlchemy models
│   │   └── main.py      # Application entry point
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   └── Dockerfile       # Multi-stage backend build
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── api/         # API client
│   │   └── types/       # TypeScript types
│   └── Dockerfile       # Multi-stage frontend build
├── .github/
│   └── workflows/       # CI/CD pipelines
├── docker-compose.yml       # Development setup
├── docker-compose.prod.yml  # Production setup
└── CHANGELOG.md            # Version history
```

## Health Checks

All services include health checks:

```bash
# Check service status
docker ps

# All services should show (healthy)
# Backend health endpoint
curl http://localhost:8000/health
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development workflow
- Pull request process
- Coding standards

## Versioning

This project follows [Semantic Versioning](https://semver.org/). See [VERSIONING.md](.github/VERSIONING.md) for our versioning strategy.

## Security

For security vulnerabilities, please see our [Security Policy](SECURITY.md) or contact the maintainers directly.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- UI components styled with [Tailwind CSS](https://tailwindcss.com/)

## Support

- **Issues**: [GitHub Issues](https://github.com/plongitudes/roanes-kitchen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/plongitudes/roanes-kitchen/discussions)

---

Made with ❤️ for better adulting
