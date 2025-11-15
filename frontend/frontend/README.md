# Roane's Kitchen - Frontend

React frontend for the Roane's Kitchen meal planning system.

## Tech Stack

- **React 18+** - UI library
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Axios** - HTTP client for API calls

## Theme

The app uses the Gruvbox color palette with dark and light modes:

- **Gruvbox Dark** (default): Warm, retro-inspired dark theme
  - Background: `#282828`
  - Foreground: `#ebdbb2`
- **Gruvbox Light**: Clean, warm light theme
  - Background: `#fbf1c7`
  - Foreground: `#3c3836`

Theme toggle available in the navigation sidebar.

## Development

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Route components
├── services/       # API client and services
├── context/        # React Context providers (Auth, Theme)
├── utils/          # Helper functions
└── App.jsx         # Main app component with routing
```

## Features

- JWT authentication with login/register
- Protected routes requiring authentication
- Dark/light theme toggle
- Responsive sidebar navigation
- API integration with backend

## Routes

- `/` - Home dashboard
- `/recipes` - Recipe management
- `/schedules` - Schedule management
- `/meal-plans` - Meal plan instances
- `/grocery-lists` - Grocery list generation
- `/login` - Authentication
