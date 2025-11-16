# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Docker-based deployment with multi-stage builds
- GitHub Actions CI/CD pipeline for automated Docker publishing
- Health checks for all services (postgres, backend, frontend)
- Database backup and restore API endpoints
- User authentication and authorization
- Recipe management (CRUD operations)
- Sequence management for weekly meal planning
- Meal schedule management
- Discord notifications support

### Changed
- Optimized Docker images with multi-stage builds (38% size reduction)
- Removed Docker socket dependency for improved security
- Running containers as non-root users

### Security
- Refactored backup/restore to use direct PostgreSQL connections instead of Docker socket
- Added Trivy security scanning in CI/CD pipeline
- Implemented non-root user (UID 1000) in Docker containers
- Added health check endpoints for service monitoring

## [1.0.0] - TBD

Initial production release - see Unreleased section for features.
