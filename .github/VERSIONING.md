# Semantic Versioning Strategy

Roanes Kitchen follows [Semantic Versioning 2.0.0](https://semver.org/) (semver).

## Version Format

```
v{MAJOR}.{MINOR}.{PATCH}

Examples:
- v1.0.0 - First production release
- v1.1.0 - Added meal planning feature
- v1.1.1 - Fixed authentication bug
- v2.0.0 - New API with breaking changes
```

## Version Number Guidelines

### MAJOR version (X.0.0)
Increment when making **incompatible API changes** or **major breaking changes**:
- Database schema changes requiring migration
- API endpoint removals or signature changes
- Configuration file format changes
- Major UI/UX overhauls

**Examples:**
- Changing authentication method (OAuth to JWT)
- Removing deprecated endpoints
- Major database restructuring

### MINOR version (1.X.0)
Increment when adding **new features** in a **backward-compatible** manner:
- New API endpoints
- New UI features
- New configuration options (with defaults)
- Performance improvements

**Examples:**
- Adding meal planning calendar view
- New Discord notification features
- Recipe import functionality

### PATCH version (1.1.X)
Increment when making **backward-compatible bug fixes**:
- Bug fixes
- Security patches
- Documentation updates
- Dependency updates (security/bugfix only)

**Examples:**
- Fixing login error
- Correcting timezone calculation
- Patching security vulnerability

## Pre-release Versions

For development and testing:

```
v1.2.0-alpha.1    - Early development
v1.2.0-beta.1     - Feature complete, testing
v1.2.0-rc.1       - Release candidate
```

**Naming:**
- `alpha` - Early development, unstable
- `beta` - Feature complete, may have bugs
- `rc` - Release candidate, final testing

## Release Process

### 1. Decide Version Number

Review changes since last release:
```bash
git log v1.0.0..HEAD --oneline
```

Determine version bump:
- Breaking changes? → MAJOR
- New features? → MINOR
- Bug fixes only? → PATCH

### 2. Update Version References

Update version in these files (if applicable):
- `backend/app/__init__.py` - Add `__version__ = "1.1.0"`
- `frontend/package.json` - Update `version` field
- `CHANGELOG.md` - Document changes (see below)

### 3. Create Git Tag

```bash
# Make sure you're on main branch
git checkout main
git pull origin main

# Create annotated tag
git tag -a v1.1.0 -m "Release v1.1.0: Meal planning feature"

# Push tag to trigger Docker publishing
git push origin v1.1.0
```

### 4. Verify Docker Images

Check GitHub Actions completes successfully:
- https://github.com/plongitudes/roanes-kitchen/actions

Verify images published to Docker Hub:
- `plongitudes/roanes-kitchen-backend:v1.1.0`
- `plongitudes/roanes-kitchen-frontend:v1.1.0`
- `plongitudes/roanes-kitchen-backend:1.1` (minor version tag)
- `plongitudes/roanes-kitchen-backend:1` (major version tag)

### 5. Create GitHub Release

1. Go to: https://github.com/plongitudes/roanes-kitchen/releases/new
2. Select tag: `v1.1.0`
3. Title: `v1.1.0 - Meal Planning`
4. Description: Copy from CHANGELOG.md
5. Check "Set as the latest release"
6. Publish release

## Changelog Format

Maintain `CHANGELOG.md` in the root directory:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Discord notification scheduling

### Changed
- Improved error messages for failed backups

### Fixed
- Timezone handling in meal scheduler

## [1.1.0] - 2025-12-01
### Added
- Meal planning calendar view
- Weekly meal schedule export
- Recipe tags and filtering

### Changed
- Updated UI with new color scheme
- Improved mobile responsiveness

### Fixed
- Login redirect issue
- Recipe image upload error

## [1.0.0] - 2025-11-16
### Added
- User authentication and authorization
- Recipe management (CRUD operations)
- Database backup and restore
- Discord notifications
- Health check endpoints
- Multi-stage Docker builds

### Security
- Removed Docker socket dependency
- Added non-root user in containers
- Trivy security scanning in CI/CD
```

## Deployment Tags

For production deployment, reference specific versions:

```yaml
# docker-compose.prod.yml
backend:
  image: plongitudes/roanes-kitchen-backend:v1.1.0  # Specific version

# Or use floating tags (auto-updates):
backend:
  image: plongitudes/roanes-kitchen-backend:1.1  # Updates to 1.1.X
  # OR
  image: plongitudes/roanes-kitchen-backend:1    # Updates to 1.X.X
  # OR
  image: plongitudes/roanes-kitchen-backend:latest  # Latest release (risky)
```

**Recommendation:** Use specific version tags (`v1.1.0`) in production for stability.

## Version Compatibility Matrix

| Backend | Frontend | Min DB Version | Notes |
|---------|----------|----------------|-------|
| v1.1.x  | v1.1.x   | v1.0           | Meal planning feature |
| v1.0.x  | v1.0.x   | v1.0           | Initial release |

## FAQ

**Q: When should I increment MAJOR version?**
A: Only for breaking changes that require user action (migration, config changes, etc.)

**Q: Can I skip version numbers?**
A: Yes, but avoid it. Use pre-release versions for testing instead.

**Q: How do I fix a bug in an old version?**
A: Create a branch from the old tag, fix, and release a PATCH version:
```bash
git checkout v1.0.0 -b fix/v1.0.1
# Make fixes
git tag v1.0.1
git push origin v1.0.1
```

**Q: What about database migrations?**
A: Include migration scripts in releases. Document in CHANGELOG under "Migration" section.
