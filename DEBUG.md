# VSCode Debugging Guide

## Backend (FastAPI) Debugging

### Option 1: Debug with Docker (Recommended)

1. **Enable debugpy in docker-compose:**
   ```bash
   # Set in .env file or export before running docker-compose
   export ENABLE_DEBUGPY=true
   ```

2. **Restart backend with debug command:**
   ```bash
   docker-compose stop backend
   docker-compose up backend  # Watch for "🐛 Debugpy listening on port 5678"
   ```

3. **Attach VSCode debugger:**
   - Set breakpoints in backend code
   - Press F5 or Run > Start Debugging
   - Select "Python: FastAPI Backend"
   - Debugger will attach to running container

### Option 2: Debug without Docker

1. **Install dependencies locally:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export DATABASE_URL=postgresql+asyncpg://admin:admin@localhost:5432/roanes_kitchen
   export SECRET_KEY=dev-secret-key
   export DEBUG=true
   ```

3. **Run with debugpy:**
   ```bash
   export ENABLE_DEBUGPY=true
   python debug_server.py
   ```

4. **Attach VSCode** (same as Option 1 step 3)

## Frontend (React) Debugging

### Chrome DevTools (Easiest)

1. Open http://localhost:3000
2. Press F12 for DevTools
3. Use Sources tab to set breakpoints
4. Console tab shows logs and errors

### VSCode Chrome Debugger

1. **Install extension:**
   - "Debugger for Chrome" (or use built-in JS debugger)

2. **Start debugging:**
   - Press F5
   - Select "Chrome: Frontend"
   - Chrome will open with debugger attached

3. **Set breakpoints:**
   - Open any .jsx file
   - Click left of line numbers to set breakpoints
   - Breakpoints will pause execution

## Common Debugging Tasks

### Backend API Request Issues

1. Set breakpoint in route handler (e.g., `backend/app/api/settings.py`)
2. Make request from frontend
3. Inspect variables, step through code

### Frontend State/Props Issues

1. Use React DevTools browser extension
2. Or set breakpoint in component render/useEffect
3. Inspect state and props in VSCode debugger

### Database Query Issues

1. Set breakpoint before SQLAlchemy query
2. Inspect query parameters
3. Check logs for actual SQL queries (SQLAlchemy logs them)

### Authentication/JWT Issues

1. Backend: Breakpoint in `app/core/deps.py:get_current_user`
2. Frontend: Check localStorage in browser DevTools
3. Verify token in Network tab of DevTools

## Tips

- **Hot reload works with debugging** - code changes reload automatically
- **Use `print()` and `console.log()`** for quick debugging
- **Check Docker logs:** `docker-compose logs -f backend`
- **Database access:** `docker-compose exec postgres psql -U admin -d roanes_kitchen`
- **Backend shell:** `docker-compose exec backend python`

## VSCode Extensions Recommended

- Python (Microsoft)
- Debugger for Chrome
- React Developer Tools (browser extension)
- SQLTools (for DB queries)
