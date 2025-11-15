# Testing Guide

## Overview

This project uses **pytest** for backend testing with coverage tracking. Tests are organized into unit tests (isolated functions) and integration tests (API endpoints, database operations).

## Running Tests

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run with coverage report
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### Run specific test categories
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Tests by marker
python -m pytest -m unit
python -m pytest -m integration
python -m pytest -m auth
```

### Run specific test file
```bash
python -m pytest tests/integration/test_health.py -v
```

### Run single test
```bash
python -m pytest tests/unit/test_security.py::test_password_hashing -v
```

## Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (isolated, no external dependencies)
│   ├── __init__.py
│   └── test_security.py    # Password hashing, JWT tokens
└── integration/             # Integration tests (API, database)
    ├── __init__.py
    ├── test_health.py      # Health check and root endpoints
    ├── test_auth.py        # Authentication endpoints
    └── test_database.py    # Database CRUD operations
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (isolated functions)
- `@pytest.mark.integration` - Integration tests (database, API)
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.auth` - Authentication/authorization tests
- `@pytest.mark.slow` - Slow-running tests

## Fixtures

Common fixtures available in all tests (defined in `conftest.py`):

### Database Fixtures
- `db_engine` - Test database engine (SQLite in-memory)
- `db_session` - Database session for tests

### Client Fixtures
- `client` - FastAPI test client
- `authenticated_client` - Test client with valid JWT token

### User Fixtures
- `test_user` - Test user in database (username: "testuser")
- `second_test_user` - Second test user (username: "alice")
- `test_user_token` - Valid JWT token for test_user

## Coverage Goals

Target coverage levels (aspirational for MVP):
- **Overall**: 80%+
- **Business logic**: 90%+
- **API endpoints**: 80%+
- **UI components** (frontend): 60%+

## Writing Tests

### Unit Test Example
```python
import pytest

@pytest.mark.unit
def test_password_hashing():
    """Test password hashing creates different hashes."""
    from app.core.security import get_password_hash, verify_password

    password = "testpassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2  # Different due to salt
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)
```

### Integration Test Example
```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
@pytest.mark.api
def test_health_check(client: TestClient):
    """Test the /health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

### Testing Authenticated Endpoints
```python
@pytest.mark.integration
@pytest.mark.auth
def test_protected_endpoint(authenticated_client: TestClient, test_user):
    """Test protected endpoint with authentication."""
    response = authenticated_client.get("/me")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
```

## Database Testing

Tests use an in-memory SQLite database that's created fresh for each test. PostgreSQL UUID columns are automatically converted to work with SQLite.

### Creating Test Data
```python
from app.models.user import User
from app.core.security import get_password_hash

def test_create_user(db_session):
    user = User(
        username="testuser",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
```

## Continuous Integration (Future)

Future CI setup will:
- Run tests on every PR
- Generate coverage reports
- Block merge if coverage drops below threshold
- Run linting (black, flake8, mypy)

## Troubleshooting

### Tests fail with "no module named pytest"
```bash
pip install -r requirements.txt
```

### Database errors about UUID types
The conftest.py monkey-patches PostgreSQL UUID to work with SQLite. If you see UUID errors, ensure you're importing models AFTER the conftest.py is loaded.

### Coverage reports not generated
Make sure pytest-cov is installed:
```bash
pip install pytest-cov
```

---

# Frontend Testing (React + Vitest)

## Overview

The frontend uses **Vitest** (Vite's native test runner) with **React Testing Library** for component testing. Vitest provides a Jest-compatible API but is optimized for Vite projects.

## Running Frontend Tests

Navigate to the `frontend/` directory first:

```bash
cd frontend
```

### Run all tests
```bash
npm test
```

### Run tests in watch mode
```bash
npm test
```

### Run tests once (CI mode)
```bash
npm test -- --run
```

### Run with coverage
```bash
npm run test:coverage
```

### Run with UI
```bash
npm run test:ui
```

## Frontend Test Structure

```
frontend/src/test/
├── setup.js                    # Global test setup and mocks
├── utils/
│   └── test-utils.jsx         # Custom render functions and helpers
├── unit/                       # Unit tests for components, hooks, context
│   ├── components/
│   │   └── Layout.test.jsx
│   ├── context/
│   │   ├── AuthContext.test.jsx
│   │   └── ThemeContext.test.jsx
│   └── pages/
│       └── Home.test.jsx
└── integration/                # Integration tests (user flows)
    └── (future tests)
```

## Test Utilities

### Custom Render Functions

Located in `src/test/utils/test-utils.jsx`:

```javascript
import { renderWithProviders, mockUser } from '../../utils/test-utils';

// Renders component with all providers (Router, Auth, Theme)
renderWithProviders(<MyComponent />);

// Renders component with only Router
renderWithRouter(<MyComponent />);
```

### Mock Helpers

```javascript
import { mockUser, mockApiResponse, mockApiError } from '../../utils/test-utils';

// Mock user object
const user = mockUser;

// Mock API success
const response = mockApiResponse({ id: '123', name: 'Test' });

// Mock API error
const error = mockApiError('Not found', 404);
```

## Writing Frontend Tests

### Component Test Example

```javascript
import { describe, it, expect, vi } from 'vitest';
import { screen, render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MyComponent from '../../../components/MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(
      <BrowserRouter>
        <MyComponent />
      </BrowserRouter>
    );

    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });
});
```

### Context/Hook Test Example

```javascript
import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../../../context/ThemeContext';

describe('ThemeContext', () => {
  it('toggles theme', () => {
    const { result } = renderHook(() => useTheme(), {
      wrapper: ThemeProvider,
    });

    expect(result.current.isDark).toBe(true);

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.isDark).toBe(false);
  });
});
```

### Testing with Mocked API

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import * as api from '../../../services/api';

// Mock the API module
vi.mock('../../../services/api', () => ({
  authAPI: {
    login: vi.fn(),
  },
}));

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles successful login', async () => {
    api.authAPI.login.mockResolvedValue({
      data: { access_token: 'token123' },
    });

    // ... test implementation
  });
});
```

## Coverage Configuration

Coverage is configured in `vite.config.js`:

- **Thresholds**: 60% for statements, functions, branches, and lines
- **Exclusions**: Test files, config files, API client (tested via integration)
- **Reporters**: Text (terminal), HTML, JSON

Current frontend coverage: **91.54%** ✓

## Resources

- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library queries](https://testing-library.com/docs/queries/about)
- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
