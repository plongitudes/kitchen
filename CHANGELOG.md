# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-11-25

### Added
- Docker-based deployment with multi-stage builds
- Test channel configuration for Discord notifications in development/staging environments
- GitHub Actions CI/CD pipeline for automated Docker publishing
- Health checks for all services (postgres, backend, frontend)
- Database backup and restore API endpoints
- User authentication and authorization with JWT tokens
- Recipe management (CRUD operations) with ingredients and instructions
- Meal planning with weekly schedules and templates
- Grocery list generation from meal plans with unit conversions
- Discord notifications support for meal planning events
- Ingredient mapping system for grocery list consolidation
- Frontend with dark mode support and responsive design

### Changed
- Optimized Docker images with multi-stage builds (38% size reduction)
- Removed Docker socket dependency for improved security
- Running containers as non-root users
- Renamed SECRET_KEY to JWT_SECRET_KEY for clarity

### Fixed
- Discord notifications now display ingredient units correctly (e.g., "5 whole eggs" instead of "5 IngredientUnit.WHOLE eggs")
- Improved exception handling in grocery service (replaced bare except clause)
- Backup/restore operations now use database credentials from config instead of hardcoded values
- Restore process automatically runs migrations to update schema after restoring old backups

### Security
- Refactored backup/restore to use direct PostgreSQL connections instead of Docker socket
- Added Trivy security scanning in CI/CD pipeline
- Implemented non-root user (UID 1000) in Docker containers
- Added health check endpoints for service monitoring
- Environment variable validation with fail-fast in production
- Comprehensive security audit completed
