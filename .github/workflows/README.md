# GitHub Actions Workflows

## Test Suite (`test.yml`)

**Full integration tests with PostgreSQL.** Runs on GitHub Actions.

### Jobs

1. **backend-tests**: Runs pytest with coverage
   - Sets up PostgreSQL service container
   - Runs all backend tests
   - Reports coverage
   - Uploads coverage to Codecov on main branch

2. **lint**: Runs code quality checks
   - flake8 for code style
   - mypy for type checking

⚠️ **Note**: This workflow uses PostgreSQL service containers on port 5433 (to avoid conflicts with your dev database on 5432).

## Quick Tests (`test-simple.yml`)

**Lightweight tests that work with act.** No database required.

### Jobs

1. **quick-lint**: Code quality checks (flake8, import validation)
2. **quick-unit-tests**: Unit tests and parser validation

This workflow is act-friendly and runs quickly for local development.

### Running Locally with Act

We use [act](https://github.com/nektos/act) to run GitHub Actions locally.

```bash
# List all workflows
act --list

# Run the quick tests (works with act)
act -W .github/workflows/test-simple.yml

# Run just the linter
act -W .github/workflows/test-simple.yml -j quick-lint

# Run just the unit tests
act -W .github/workflows/test-simple.yml -j quick-unit-tests

# Try running full test suite (may have service container issues with act)
act -W .github/workflows/test.yml -j backend-tests

# Run with verbose output
act -W .github/workflows/test-simple.yml -v
```

### Capturing Output

Act writes to stdout/stderr. Here are different ways to view output:

```bash
# Save output to file
act -W .github/workflows/test-simple.yml 2>&1 | tee act-output.log

# Run in verbose mode and save
act -W .github/workflows/test-simple.yml -v 2>&1 | tee act-verbose.log

# Just save to file without displaying
act -W .github/workflows/test-simple.yml > act-output.log 2>&1

# View live with colors preserved (requires unbuffer from expect package)
unbuffer act -W .github/workflows/test-simple.yml | tee act-output.log

# Follow along with less
act -W .github/workflows/test-simple.yml 2>&1 | less -R
```

### Debugging Failed Steps

If a step fails:

```bash
# Run with verbose to see more detail
act -W .github/workflows/test.yml -j backend-tests -v

# Check Docker logs for service containers
docker logs <container-id>

# See what containers act created
docker ps -a | grep act-

# Clean up act containers
docker ps -a | grep act- | awk '{print $1}' | xargs docker rm -f
```

### Configuration

The `.actrc` file in the root configures act with defaults:
- Uses linux/amd64 architecture (for M-series Macs)
- Uses catthehacker/ubuntu:act-latest image

### CI/CD Status

When these workflows run on GitHub:
- ✅ Tests must pass before merging PRs
- ⚠️  Currently tests are failing due to template refactor (see rk-33c, rk-6wi)
- 📊 Coverage reports uploaded to Codecov on main branch

### Local Development

For faster local testing without Docker:
```bash
cd backend
pytest
pytest --cov=app --cov-report=term
flake8 app
```
