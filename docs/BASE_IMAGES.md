# Base Image Versions

This document explains the base image version choices for Roane's Kitchen and when to update them.

## Current Versions

| Component | Image | Version | Last Updated |
|-----------|-------|---------|--------------|
| Backend (build) | python | 3.11.10-slim | 2025-11-16 |
| Backend (runtime) | python | 3.11.10-slim | 2025-11-16 |
| Frontend (build) | node | 22.11.0-alpine | 2025-11-16 |
| Frontend (runtime) | nginx | 1.27.3-alpine | 2025-11-16 |
| Database | postgres | 15.10-alpine | 2025-11-16 |
| Backup container | postgres | 15.10-alpine | 2025-11-16 |

## Version Rationale

### Python 3.11.10-slim

**Why Python 3.11?**
- Stable, mature release with good performance
- FastAPI and async features work well
- Wide library support

**Why 3.11.10 specifically?**
- Latest patch release in the 3.11 series
- Includes security fixes and bug fixes
- No breaking changes from 3.11.9

**Why -slim variant?**
- Smaller image size (~150MB vs ~900MB for full)
- Contains everything we need for Python apps
- Missing dev tools (which we install separately in builder stage)

**When to update:**
- **Patch updates (3.11.x)**: Update quarterly or for security fixes
- **Minor updates (3.12, 3.13)**: Test thoroughly, may require code changes
- **Major updates (4.x)**: Rare, requires significant testing

### Node 22.11.0-alpine

**Why Node 22?**
- Current LTS (Long Term Support) release
- Will receive support until April 2027
- Vite and React work perfectly with it

**Why 22.11.0 specifically?**
- Latest stable in the 22.x LTS series
- Aligned with development environment (docker-compose.yml)
- Security and performance improvements

**Why alpine variant?**
- Smallest image size (~50MB vs ~350MB for regular)
- Sufficient for building frontend assets
- Standard choice for Node.js builds

**When to update:**
- **Patch updates (22.x.x)**: Update monthly or for security fixes
- **Minor updates (22.x)**: Update as released (safe within LTS)
- **Major updates (24.x)**: When new LTS is released (every 2 years)

### Nginx 1.27.3-alpine

**Why Nginx 1.27?**
- Stable mainline release
- Modern HTTP/2 support
- Well-tested for serving static files

**Why 1.27.3 specifically?**
- Latest stable in the 1.27 series
- Production-ready for static file serving
- Security patches included

**Why alpine variant?**
- Minimal size (~40MB vs ~150MB for regular)
- Perfect for static file serving
- Standard for production deployments

**When to update:**
- **Patch updates (1.27.x)**: Update quarterly or for security fixes
- **Minor updates (1.28, 1.29)**: Update yearly, test thoroughly
- **Major updates (2.x)**: When stable, requires testing

### PostgreSQL 15.10-alpine

**Why PostgreSQL 15?**
- Current stable series
- Excellent performance and features
- Wide tooling support

**Why 15.10 specifically?**
- Latest patch in the 15 series
- Bug fixes and security updates
- No breaking changes from 15.9

**Why alpine variant?**
- Smaller image size (~80MB vs ~150MB)
- Sufficient for our use case
- Matches other alpine images

**When to update:**
- **Patch updates (15.x)**: Update quarterly, test backups
- **Minor updates (16, 17)**: Requires database migration planning
- **Major updates**: Consult PostgreSQL upgrade documentation

## Update Schedule

### Regular Updates (Low Risk)

Update quarterly during maintenance windows:
- Python patch releases (3.11.x)
- Node patch releases (22.x.x)
- Nginx patch releases (1.27.x)
- PostgreSQL patch releases (15.x)

### Security Updates (Immediate)

Apply immediately when CVEs are announced:
- Check GitHub Security Advisories
- Monitor Docker Hub security scans
- Review Trivy scan results from CI/CD

### Major Updates (High Risk)

Plan carefully with testing:
- Create test environment
- Test all functionality
- Review migration guides
- Update documentation
- Plan rollback procedure

## How to Update Base Images

### 1. Check for New Versions

```bash
# Check Python versions
docker pull python:3.11-slim
docker images | grep python

# Check Node versions
docker pull node:22-alpine
docker images | grep node

# Check Nginx versions
docker pull nginx:alpine
docker images | grep nginx

# Check PostgreSQL versions
docker pull postgres:15-alpine
docker images | grep postgres
```

### 2. Update Dockerfiles

Edit these files:
- `backend/Dockerfile` - Update Python version (2 places)
- `frontend/Dockerfile` - Update Node and Nginx versions
- `docker-compose.yml` - Update PostgreSQL and Node versions
- `docker-compose.prod.yml` - Update PostgreSQL version (2 places)

### 3. Update This Document

Update the table at the top with:
- New version number
- Current date

### 4. Test Locally

```bash
# Rebuild images
docker-compose build --no-cache

# Start services
docker-compose up -d

# Run tests
docker-compose exec backend pytest

# Verify health
docker ps
curl http://localhost:8000/health
```

### 5. Commit and Create PR

```bash
git add backend/Dockerfile frontend/Dockerfile docker-compose*.yml docs/BASE_IMAGES.md
git commit -m "chore: update base images to latest patch versions

- Python: 3.11.9 → 3.11.10
- Node: 22.10.0 → 22.11.0
- Nginx: 1.27.2 → 1.27.3
- PostgreSQL: 15.9 → 15.10"
git push origin chore/update-base-images
```

### 6. Monitor After Deployment

Watch for issues:
- Check error logs
- Monitor performance
- Verify backups still work
- Test database migrations

## Security Scanning

Our CI/CD pipeline includes Trivy security scanning for all images.

**View scan results:**
- GitHub Actions → docker-publish workflow
- GitHub Security tab → Code scanning alerts

**When vulnerabilities are found:**
1. Assess severity (Critical > High > Medium > Low)
2. Check if fixed version available
3. Update base image version
4. Rebuild and redeploy
5. Verify vulnerability resolved

## Version Pinning Policy

**Why we pin versions:**
- **Reproducibility**: Same build today and tomorrow
- **Stability**: No surprise updates breaking things
- **Security**: Know exactly what we're running
- **Debugging**: Easier to identify issues

**What we DON'T do:**
- ❌ Use `latest` tag (too unpredictable)
- ❌ Use major-only tags (`python:3`) (too broad)
- ❌ Use minor-only tags (`python:3.11`) (auto-updates)

**What we DO:**
- ✅ Use full version tags (`python:3.11.10-slim`)
- ✅ Update deliberately and with testing
- ✅ Document version choices
- ✅ Track security advisories

## Alpine vs Debian Images

We use Alpine-based images where possible:

**Advantages:**
- Much smaller size (saves bandwidth and storage)
- Faster downloads and deployments
- Lower attack surface (fewer packages)

**Disadvantages:**
- Uses musl libc instead of glibc (rare compatibility issues)
- Smaller package ecosystem
- Different package manager (apk vs apt)

**When to use Debian instead:**
- Need specific glibc-dependent packages
- Debugging complex C extension issues
- Package not available in Alpine repos

## Questions?

**Q: Why not use `latest` tag?**
A: `latest` changes without notice. Today's `latest` might be broken tomorrow.

**Q: How often should we update?**
A: Quarterly for patches, immediately for security fixes, carefully for major versions.

**Q: What if a new version breaks something?**
A: Pin to previous working version, investigate, fix, then update.

**Q: Do I need to update all images at once?**
A: No, update independently. But test together before deploying.

---

**Last reviewed**: 2025-11-16
**Next review**: 2026-02-16 (quarterly)
