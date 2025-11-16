# Contributing to Roane's Kitchen

Thank you for your interest in contributing to Roane's Kitchen! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to:
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully
- Focus on what's best for the community

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report:
- Check the [existing issues](https://github.com/plongitudes/roanes-kitchen/issues) to avoid duplicates
- Try to reproduce the issue with the latest version

When creating a bug report, include:
- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Environment details**: OS, Docker version, browser
- **Logs** from `docker-compose logs backend frontend`
- **Screenshots** if applicable

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been suggested
- Explain the use case and why it would be valuable
- Be open to discussion and alternative approaches

### Pull Requests

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards (see below)

3. **Test your changes**:
   ```bash
   # Backend tests
   docker-compose exec backend pytest

   # Frontend linting
   cd frontend && npm run lint
   ```

4. **Commit your changes** with clear messages:
   ```bash
   git commit -m "Add meal planning calendar view"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** with:
   - Clear description of changes
   - Link to related issue (if applicable)
   - Screenshots for UI changes
   - Test results or coverage

## Development Workflow

### Setting Up Your Development Environment

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/roanes-kitchen.git
   cd roanes-kitchen
   ```

2. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/plongitudes/roanes-kitchen.git
   ```

3. Start development environment:
   ```bash
   docker-compose up -d
   ```

### Keeping Your Fork Updated

```bash
git fetch upstream
git checkout dev
git merge upstream/dev
git push origin dev
```

### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Adding tests

## Coding Standards

### Backend (Python)

We follow PEP 8 with some exceptions:
- Line length: 100 characters (not 79)
- Use type hints for function signatures
- Use async/await for database operations

**Code style:**
```python
# Good
async def get_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Recipe:
    """Fetch a recipe by ID."""
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id)
    )
    return result.scalar_one_or_none()

# Bad
def get_recipe(recipe_id, db):
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()
```

**Tools:**
- Linter: `ruff check`
- Formatter: `ruff format`
- Type checker: `basedpyright`

### Frontend (TypeScript + React)

- Use TypeScript for all new files
- Functional components with hooks (no class components)
- Use Tailwind CSS for styling (avoid inline styles)

**Code style:**
```tsx
// Good
interface RecipeCardProps {
  recipe: Recipe;
  onDelete: (id: string) => void;
}

export const RecipeCard: React.FC<RecipeCardProps> = ({ recipe, onDelete }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold">{recipe.title}</h3>
      <button onClick={() => onDelete(recipe.id)}>Delete</button>
    </div>
  );
};

// Bad
export function RecipeCard(props: any) {
  return <div style={{background: 'white'}}>{props.recipe.title}</div>;
}
```

**Tools:**
- Linter: `eslint`
- Formatter: `prettier`
- Type checker: Built into TypeScript

### Database Migrations

When changing models:

1. Create migration:
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "Add meal_plan_notes column"
   ```

2. Review the generated migration in `backend/alembic/versions/`

3. Test migration:
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend alembic downgrade -1
   docker-compose exec backend alembic upgrade head
   ```

4. Include migration file in your PR

### Testing

#### Backend Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec backend pytest tests/test_recipes.py

# Run specific test
docker-compose exec backend pytest tests/test_recipes.py::test_create_recipe
```

**Test structure:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_recipe(client: AsyncClient, auth_headers: dict):
    """Test recipe creation endpoint."""
    response = await client.post(
        "/recipes/",
        json={"title": "Test Recipe", "ingredients": "eggs"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Recipe"
```

#### Frontend Tests

```bash
# Run tests (when implemented)
cd frontend && npm test

# Run linting
cd frontend && npm run lint
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add meal planning calendar view
fix: correct timezone handling in scheduler
docs: update deployment guide for Unraid
refactor: simplify recipe API endpoint
test: add tests for backup functionality
```

**Format:**
```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance tasks

## Pull Request Process

1. **Ensure all tests pass**
2. **Update documentation** if needed
3. **Add entries to CHANGELOG.md** under "Unreleased"
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Squash commits** if requested

### PR Review Criteria

Reviewers will check:
- Code follows project standards
- Tests are included and passing
- Documentation is updated
- No breaking changes (or properly documented)
- Commit messages are clear

## Release Process

For maintainers only:

1. Update CHANGELOG.md with release version and date
2. Create and push version tag: `git tag v1.1.0 && git push origin v1.1.0`
3. GitHub Actions will build and publish Docker images
4. Create GitHub release with changelog

## Questions?

- **General questions**: [GitHub Discussions](https://github.com/plongitudes/roanes-kitchen/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/plongitudes/roanes-kitchen/issues)
- **Security issues**: See [SECURITY.md](SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Roane's Kitchen! 🎉
