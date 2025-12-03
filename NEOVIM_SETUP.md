# Neovim LSP Setup for Kitchen Project

## Overview
This project is now configured to work with your neovim setup using:
- **ruff** - Linting and formatting via LSP
- **basedpyright** - Type checking with lenient settings
- **conform.nvim** - Format on save (uses ruff LSP)

## Configuration Files Created

### Backend Python (`backend/`)
1. **`pyproject.toml`** - Ruff configuration
   - Line length: 100 (matches AGENTS.md)
   - Import sorting enabled (stdlib → third-party → local)
   - Sensible linting rules for FastAPI projects
   
2. **`pyrightconfig.json`** - Basedpyright configuration
   - Type checking: OFF (only autocompletion and imports)
   - Unused imports/variables: Not reported (ruff handles this)
   - Auto-import completions: Enabled
   - Organize imports: Disabled (ruff handles this)

3. **`.editorconfig`** - Editor consistency (root directory)
   - Python: 4 spaces, 100 char line length
   - JS/JSX: 2 spaces
   - Consistent line endings (LF)

## Virtual Environment Setup

The LSP servers need a Python virtual environment to resolve imports. The project has a `.venv` at the project root with Python 3.11.8 and all dependencies installed.

**To activate:**
```bash
# From project root
source .venv/bin/activate

# From backend directory
source ../.venv/bin/activate
```

**If you need to reinstall dependencies:**
```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

After setup, activate when needed:
```bash
# From project root
source .venv/bin/activate

# From backend directory
source ../.venv/bin/activate
```

## Neovim LSP Workflow

Your nvim config automatically:

1. **On Python file open:**
   - Enables `basedpyright` (autocomplete, go-to-definition, hover docs)
   - Enables `ruff` (linting, formatting, organize imports)

2. **On save (if `vim.g.format_on_save = true`):**
   - Formats code with ruff
   - Organizes imports

3. **Manual format (`<leader>F`):**
   - Organizes imports first
   - Then formats code

## Useful Commands

### In Neovim
```vim
" Enable format on save
:lua vim.g.format_on_save = true

" Disable format on save
:lua vim.g.format_on_save = false

" Manual format + organize imports
<leader>F

" Code actions (fix specific issues)
<leader>ca
```

### In Terminal
```bash
# Format all Python files
cd backend
ruff format .

# Check linting issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Run type checker
basedpyright app/
```

## How It Works

### Ruff LSP Server
- **Linting**: Shows warnings/errors inline
- **Formatting**: Via LSP (conform.nvim calls it)
- **Organize imports**: Available as code action
- **Config**: Reads from `pyproject.toml` [tool.ruff]

### Basedpyright LSP Server
- **Autocomplete**: Function signatures, variable types
- **Go-to-definition**: Jump to source (`gd`)
- **Hover docs**: Show docstrings (`K`)
- **Auto-imports**: Suggests imports for undefined names
- **Config**: Reads from `pyrightconfig.json`
- **Type checking**: Disabled (we only use it for IDE features)

### Separation of Concerns
- **Ruff**: Handles all linting, formatting, import sorting
- **Basedpyright**: Handles autocomplete, navigation, hover
- **No overlap**: Basedpyright's signature help is disabled to avoid duplicates

## Verifying Setup

1. Open a Python file in the backend: `nvim backend/app/main.py`
2. Check LSP clients are attached: `:LspInfo`
   - Should see: `basedpyright` and `ruff`
3. Hover over a function: `K` (should show docstring)
4. Go to definition: `gd` (should jump to source)
5. Format: `<leader>F` (should organize imports + format)

## Troubleshooting

### Imports show as errors in neovim
- Make sure virtual environment exists: `ls .venv/` (from project root)
- Restart LSP: `:LspRestart`
- Check Python path: `:lua print(vim.lsp.get_active_clients()[1].config.cmd[1])`

### Format not working
- Check format on save setting: `:lua print(vim.g.format_on_save)`
- Try manual format: `<leader>F`
- Check ruff LSP is running: `:LspInfo`

### basedpyright not finding modules
- Verify `pyrightconfig.json` exists in `backend/`
- Check venvPath: Should be ".." (parent dir) with venv name ".venv"
- Restart LSP: `:LspRestart`

## Mason Package Manager

Your nvim uses mason.nvim to install LSP servers. To ensure you have them:

```vim
:Mason
" Search for: basedpyright
" Search for: ruff
" Both should show as installed
```

If not installed:
```vim
:MasonInstall basedpyright ruff
```

## Project Structure

```
kitchen/                    # Project root
├── .venv/                  # Python virtual environment (shared)
├── backend/
│   ├── pyproject.toml      # Ruff configuration
│   ├── pyrightconfig.json  # Basedpyright configuration (venvPath points to ../.venv)
│   ├── app/                # Application code
│   └── tests/              # Test code
└── frontend/
```

## Next Steps

1. Activate virtual environment: `source .venv/bin/activate` (from project root)
2. Open neovim in backend directory: `cd backend && nvim .`
3. Verify LSP servers attach: `:LspInfo`
4. Try format on save by editing a file
5. Use `<leader>F` to organize imports + format

Enjoy your configured development environment!
