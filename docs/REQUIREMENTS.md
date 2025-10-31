# Roanes Kitchen - Requirements & Design Document

## 1. Problem Statement

Two people sharing meal prep responsibilities need a self-hosted way to manage a growing library of recipes, organize them into themed weekly rotations, and generate grocery lists based on upcoming meals. Currently handled via Notion, which is too limited for this use case.

## 2. Users & Context

- **Primary Users:** Two people living together (one very technical, one semi-technical)
- **Usage Frequency:** Daily
- **Key Constraint:** UX friction is problematic for adoption; both users have ADHD, so clear reminders and low-friction workflows are critical
- **Hosting:** Self-hosted on Unraid server via Docker containers; access via Tailscale (internal network only, no credential security concerns)
- **Communication Hub:** Established Discord server for announcements and reminders
- **Ad-hoc Changes:** Discord is the primary communication channel for ad-hoc schedule changes; in Phase 2, the app will support per-instance modifications

## 3. Success Criteria (MVP)

- [x] Migrate data away from Notion
- [x] Web UI allows users to:
  - Manage recipes (CRUD operations, including ownership reassignment)
  - Create and manage a sequence of completely pre-packaged themed weeks (each week template includes day/person/action/recipe assignments)
  - View upcoming meals and assignments
  - Generate grocery lists based on shopping day and upcoming meals
- [x] Schedule automatically cycles through the sequence of weeks, then repeats
- [x] Scheduled events trigger Discord notifications:
  - Upcoming meal event (e.g., "Bob is cooking Pasta Carbonara on Monday")
  - Shopping event with grocery list (e.g., "Here's Tuesday's grocery list")
  - Recipe additions/retirements (optional, nice-to-have)

## 4. Core Concepts

### 4.1 Recipes
Recipes are owned by a person (tied to their cooking skill/preferences). Each recipe has:
- Name
- Ingredients (list of: ingredient name, quantity, unit)
- Instructions (ordered steps)
- Metadata (prep time, cook time, recipe type/category)
- Notes (prep notes, postmortem/cooking notes)
- Duration & dependency tracking (for future Gantt chart feature—see Phase 2)
- Retirement status (soft delete for accidental deletion recovery)

In MVP, recipes have a single owner. In Phase 2, recipes can be co-owned by multiple users.

### 4.2 Schedule Sequence
A rotating list of themed weeks. Example sequence:
1. "Indian Cuisine Week"
2. "Burger Week"
3. "Pasta Week"
4. "Asian Fusion Week"

After the final week, the sequence loops back to week 1. The system auto-advances through weeks on a regular cadence (e.g., weekly).

### 4.3 Week Template (Class)
A week template is a completely pre-packaged container that defines:
- Theme name (e.g., "Indian Cuisine Week")
- A mapping of days → (person, action, recipe) tuples

Example for "Indian Cuisine Week":
- Monday: Bob (cook, Tikka Masala)
- Tuesday: Alice (shop, null)
- Wednesday: Bob (cook, Butter Chicken)
- Thursday: Alice (cook, Saag Paneer)
- Friday: Alice (cook, Paneer Curry)
- Saturday: Bob (rest, null)
- Sunday: Bob (rest, null)

The template is immutable in MVP and defines exactly what will happen every time that week occurs.

### 4.4 Week Instance (Object)
When a new week begins, the system creates a week instance—a snapshot of the template tied to a specific calendar date. The instance inherits all day/person/action/recipe assignments from the template.

In MVP, instances are read-only copies of the template. In Phase 2, instances can be independently modified (e.g., "this week, swap Butter Chicken for a different recipe") without affecting the template or other instances.

### 4.5 Grocery List
Auto-generated based on a shopping action within a week instance. When a person is assigned to "shop" on a given day, a grocery list is generated covering all recipes scheduled from that day forward until (but not including) the next shopping day.

### 4.6 Users & Accounts
Two user accounts in the system (one per person). No complex permissions needed; both can edit everything. Authentication is lightweight (username/password, bcrypt hashed). Accounts are used to:
- Associate people with recipe ownership
- Assign people to day/action pairs within week templates (and their recipes)
- Send Discord notifications tagged to the person

## 5. Data Model

### Tables/Collections

#### `users`
```
id: UUID (primary key)
username: string (unique)
password_hash: string
created_at: timestamp
updated_at: timestamp
discord_user_id: string (optional, for notifications)
```

#### `settings`
```
id: UUID (primary key)
discord_bot_token: string (encrypted, for sending notifications)
notification_channel_id: string (Discord channel ID where all notifications post)
notification_time: string (HH:MM format, e.g., "07:00")
notification_timezone: string (e.g., "America/Los_Angeles", "UTC")
created_at: timestamp
updated_at: timestamp
```

**Note:** Single-row table for global application settings.

#### `recipes`
```
id: UUID (primary key)
owner_id: UUID (foreign key → users.id, ON DELETE RESTRICT)
name: string
recipe_type: string (e.g., "breakfast", "dinner", "dessert")
prep_time_minutes: int (optional)
cook_time_minutes: int (optional)
prep_notes: text (optional)
postmortem_notes: text (optional)
source_url: string (optional, for future recipe scraping)
retired_at: timestamp (optional, soft delete; null means active)
created_at: timestamp
updated_at: timestamp
```

**ON DELETE behavior:** Cannot delete a user who owns recipes (RESTRICT). Recipes must be reassigned to another user or retired before user deletion. User deletion is deferred to Phase 2.

#### `recipe_ingredients`
```
id: UUID (primary key)
recipe_id: UUID (foreign key → recipes.id, ON DELETE CASCADE)
ingredient_name: string
quantity: float
unit: string (constrained to valid units; see below)
order: int (for sorting)
created_at: timestamp
```

**Valid Units:**
- Volume: `cup`, `tablespoon`, `teaspoon`, `fluid_ounce`, `pint`, `quart`, `gallon`, `ml`, `liter`
- Weight: `gram`, `kilogram`, `ounce`, `pound`
- Count: `count`, `whole`, `item`
- Special: `bunch`, `clove`, `can`, `pinch`, `dash`, `to_taste`

**Note:** Units are validated against this list to ensure consistency. The Pint library (see Section 8) handles conversions between compatible units (e.g., cups ↔ tablespoons, grams ↔ kilograms) during grocery list aggregation.

**ON DELETE behavior:** Ingredients are deleted when their recipe is deleted (CASCADE). In Phase 2+, ingredients may become independent entities with brand preferences and sourcing information.

#### `recipe_instructions`
```
id: UUID (primary key)
recipe_id: UUID (foreign key → recipes.id, ON DELETE CASCADE)
step_number: int
description: string
duration_minutes: int (optional, null for MVP; used in Phase 2 for Gantt chart)
depends_on_step_id: UUID (optional, null for MVP; Phase 2 feature)
created_at: timestamp
```

**ON DELETE behavior:** Instructions are deleted when their recipe is deleted (CASCADE).

#### `schedule_sequences`
```
id: UUID (primary key)
name: string (e.g., "Fall & Winter Rotation")
created_at: timestamp
updated_at: timestamp
current_week_index: int (tracks which week in the sequence is active; auto-increments)
advancement_day_of_week: int (0=Sunday, 6=Saturday; which day to advance to next week)
advancement_time: string (HH:MM format; what time on that day to advance)
```

#### `schedule_weeks` (Week Template / "Class")
```
id: UUID (primary key)
sequence_id: UUID (foreign key → schedule_sequences.id, ON DELETE RESTRICT)
week_number: int (position in sequence, 1-indexed)
theme_name: string (e.g., "Indian Cuisine Week")
retired_at: timestamp (optional, soft delete; null means active)
created_at: timestamp
updated_at: timestamp
```

**ON DELETE behavior:** Cannot delete a sequence that has week templates (RESTRICT). Week templates use soft delete with `retired_at` timestamp to preserve historical data for instances that reference them.

#### `week_day_assignments` (Template Assignments)
```
id: UUID (primary key)
week_id: UUID (foreign key → schedule_weeks.id, ON DELETE CASCADE)
day_of_week: int (0=Sunday, 6=Saturday)
assigned_user_id: UUID (foreign key → users.id, ON DELETE RESTRICT)
action: string (e.g., "cook", "shop", "takeout", "rest")
recipe_id: UUID (foreign key → recipes.id, nullable for non-cook actions, ON DELETE RESTRICT)
order: int (for multiple actions on same day, if needed)
created_at: timestamp
```

**ON DELETE behavior:**
- Assignments are deleted when their week template is retired/deleted (CASCADE)
- Cannot delete a user who is assigned in week templates (RESTRICT)
- Cannot delete a recipe that is assigned in week templates (RESTRICT) - must remove from template or retire the recipe first

#### `meal_plan_instances` (Week Instance / "Object")
```
id: UUID (primary key)
schedule_week_id: UUID (foreign key → schedule_weeks.id, ON DELETE RESTRICT)
instance_start_date: date (actual calendar date when this week instance begins)
created_at: timestamp
updated_at: timestamp
```

**Note:** In MVP, instances are read-only references to their template. To view an instance's assignments, query `week_day_assignments` from the linked `schedule_week_id` and calculate actual dates using `instance_start_date`. The `meal_assignments` table is deferred to Phase 2 when per-instance modifications are needed.

**ON DELETE behavior:** Cannot delete a week template that has instances referencing it (RESTRICT). Use retirement (`retired_at`) instead to preserve historical data.

#### `grocery_lists`
```
id: UUID (primary key)
meal_plan_instance_id: UUID (foreign key → meal_plan_instances.id, ON DELETE CASCADE)
shopping_date: date (the date the shopping action occurs)
generated_at: timestamp
```

**Note:** Multiple grocery lists per week instance are supported (one per shopping day). In typical usage, each week has one shopping day, but the data model supports multiple if needed. Each list covers meals from the day after its shopping_date through the next shopping_date (inclusive), which may span multiple week instances.

**ON DELETE behavior:** Grocery lists are deleted when their meal plan instance is deleted (CASCADE).

#### `grocery_list_items`
```
id: UUID (primary key)
grocery_list_id: UUID (foreign key → grocery_lists.id, ON DELETE CASCADE)
ingredient_name: string
total_quantity: float
unit: string
source_recipe_ids: string (JSON array of recipe IDs, for reference)
created_at: timestamp
```

**ON DELETE behavior:** Items are deleted when their grocery list is deleted (CASCADE).

## 6. Features & User Stories (MVP)

### 6.1 Recipe Management
- **US-1:** As a user, I can add a new recipe by providing name, ingredients (with quantities/units), instructions (as ordered steps), prep/cook times, and notes.
- **US-2:** As a user, I can view all recipes.
- **US-3:** As a user, I can edit any field of my recipe (name, ingredients, instructions, metadata, notes).
- **US-4:** As a user, I can retire a recipe (soft delete with a retirement date) to prevent accidental permanent deletion. Retired recipes are hidden from active use but remain in the system for historical reference. The system validates that the recipe is not actively used in any week templates before allowing retirement. If the recipe is in use, the system shows which templates use it and requires the user to either remove it from those templates or retire the templates first.
- **US-5:** As a user, I can see which person owns each recipe.
- **US-6:** As a user, I can reassign ownership of a recipe to another user (e.g., if Alice learns to cook Bob's signature dish, she can take ownership).

### 6.2 Schedule Sequence & Week Template Management
- **US-7:** As a user, I can view the sequence of themed week templates in the rotation.
- **US-8:** As a user, I can create a new themed week template, defining which person performs which action with which recipe on each day of the week (completely pre-packaged).
- **US-9:** As a user, I can edit a week template's theme name or day/person/action/recipe assignments.
- **US-10:** As a user, I can delete a week template from the sequence.
- **US-11:** As a user, I can reorder week templates within the sequence.
- **US-12:** The system automatically advances to the next week template in the sequence. Users can configure the advancement schedule via a simple dropdown UI (e.g., "Every Monday at 9:00 AM", "Every Tuesday at 6:00 PM"). Natural language scheduling is deferred to Phase 2.
- **US-13:** After the final week template, the sequence loops back to the first week template.

### 6.3 Meal Planning & Assignment (Instance-Level)
- **US-14:** As a user, I can view the current week instance with all day/person/action/recipe assignments. Assignments are derived from the week template (`week_day_assignments`) with dates calculated from the instance's start date.
- **US-15:** As a user, I can view past week instances to see what was scheduled.
- **US-16:** When a new week instance begins, the system auto-creates the instance as a reference to the week template. In MVP, instances are read-only; all assignments are queried from the template on-demand.

### 6.4 Grocery List Generation
- **US-17:** As a user, I can generate a grocery list for a specific shopping day, covering meals from the day after shopping through the next shopping day (inclusive). The list may span multiple week instances if the shopping cycle crosses week boundaries. The shopping day itself is excluded from the list.
- **US-18:** The grocery list aggregates ingredients from all assigned recipes, summing quantities where ingredients overlap. Aggregation uses the Pint library to convert compatible units to a canonical form (e.g., "1 cup + 8 fluid_ounce + 2 tablespoon" → "2.125 cups"). Volume units aggregate with other volume units, weight units with weight units. Incompatible units (e.g., "1 cup butter" + "8 oz butter") appear as separate line items.
- **US-19:** As a user, I can view past grocery lists (read-only).

### 6.5 Settings & Configuration
- **US-26:** As a user, I can access a settings page to configure application preferences.
- **US-27:** As a user, I can store and update the Discord bot token via a settings UI (with validation).
- **US-28:** As a user, I can configure the weekly advancement schedule (day of week and time) via dropdown menus.
- **US-29:** As a user, I can configure global notification settings via the settings page:
  - Discord notification channel ID (the channel where all notifications will be posted)
  - Notification time (HH:MM format, default "07:00")
  - Notification timezone (e.g., "America/Los_Angeles", "UTC")

### 6.6 Discord Integration
- **US-20:** When a person is assigned to an action on a given date (from the week instance), a Discord notification is posted to the configured channel at the configured notification time on the day of the event (e.g., "Today: Bob is cooking Tikka Masala").
- **US-21:** When a person is assigned to a "shop" action on a given date, a Discord notification is posted to the configured channel with the aggregated grocery list at the configured notification time on the day of the shopping action.
- **US-22:** Discord notifications are sent at the configured notification time (default 7am) on the day of the event to the configured Discord channel. All times respect the configured timezone.

### 6.7 User Accounts & Authentication
- **US-30:** Users can create an account with username/password (stored securely with bcrypt).
- **US-31:** Users can log in and maintain a session.
- **US-32:** User accounts are tied to recipe ownership and week template/instance assignments.

## 7. API Endpoints (Rough)

### Authentication
- `POST /auth/register` — Create a new user account
- `POST /auth/login` — Authenticate and return session token
- `POST /auth/logout` — End session

### Recipes
- `GET /recipes` — List all recipes (optionally filtered by owner)
- `POST /recipes` — Create a new recipe
- `GET /recipes/{id}` — Retrieve a specific recipe with ingredients and instructions
- `PUT /recipes/{id}` — Update a recipe (including reassigning owner_id)
- `DELETE /recipes/{id}` — Soft-delete (retire) a recipe by setting retired_at. Validates that recipe is not in active week templates; returns 400 with list of templates using the recipe if validation fails.
- `GET /recipes/{id}/usage` — Check which week templates currently use this recipe
- `POST /recipes/{id}/restore` — Restore a retired recipe (clear retired_at)
- `GET /recipes/{id}/ingredients` — Get ingredients for a recipe
- `POST /recipes/{id}/ingredients` — Add an ingredient to a recipe
- `PUT /recipes/{id}/ingredients/{ingredient_id}` — Update an ingredient
- `DELETE /recipes/{id}/ingredients/{ingredient_id}` — Remove an ingredient

### Schedule Sequences & Week Templates
- `GET /schedules` — List all schedule sequences
- `POST /schedules` — Create a new schedule sequence
- `GET /schedules/{sequence_id}` — Get a schedule sequence with all its week templates
- `GET /schedules/{sequence_id}/weeks` — List all week templates in a sequence
- `POST /schedules/{sequence_id}/weeks` — Create a new week template in a sequence
- `GET /schedules/{sequence_id}/weeks/{week_id}` — Get a specific week template with day/person/action/recipe assignments
- `PUT /schedules/{sequence_id}/weeks/{week_id}` — Update a week template (theme, day/person/action/recipe assignments)
- `DELETE /schedules/{sequence_id}/weeks/{week_id}` — Delete a week template from a sequence
- `POST /schedules/{sequence_id}/weeks/reorder` — Reorder week templates within a sequence
- `GET /schedules/{sequence_id}/current-week` — Get the currently active week template

### Meal Plan Instances
- `GET /meal-plans` — List all meal plan instances
- `GET /meal-plans/current` — Get the current week instance with all assignments (derived from template)
- `POST /meal-plans/advance-week` — Manually advance to the next week template in the sequence
- `GET /meal-plans/{instance_id}` — Get a specific meal plan instance with all assignments (derived from template)

### Grocery Lists
- `GET /grocery-lists` — List all grocery lists
- `GET /meal-plans/{instance_id}/grocery-lists` — Get all grocery lists for a specific week instance
- `POST /meal-plans/{instance_id}/grocery-lists/generate?shopping_date=YYYY-MM-DD` — Generate a grocery list for a specific shopping day within the given week instance (covers meals from day after shopping through next shopping day, may span multiple instances)
- `GET /grocery-lists/{id}` — Get a specific grocery list with items

### Settings & Configuration
- `GET /settings` — Get current global application settings (Discord bot token, notification channel, notification time, timezone, etc.)
- `PUT /settings` — Update global application settings (Discord bot token, notification channel ID, notification time, timezone)
- `POST /settings/validate-discord-token` — Validate Discord bot token and channel ID before saving

### Discord Integration
- `POST /discord/sync-user` — Link a Discord user ID to an app user account (for notifications)
- `GET /discord/status` — Check Discord bot connection status

## 8. Architecture & Tech Stack

### Backend
- **Language/Framework:** Python + FastAPI (lightweight, fast, good for APIs)
- **Database:** PostgreSQL (self-hosted, ACID transactions, relational data structure)
- **Task Scheduling:** APScheduler (for weekly week advancement and Discord notifications)
- **ORM:** SQLAlchemy (for database queries and migrations)
- **Authentication:** JWT tokens (simple, stateless)
- **Discord Bot:** discord.py (lightweight bot for sending notifications)
- **Unit Conversion:** Pint (for ingredient unit conversions and grocery list aggregation)

### Frontend
- **Framework:** React (or similar SPA framework)
- **Styling:** TailwindCSS (for fast, consistent UI)
- **State Management:** Simple context API or similar (scope is small enough to avoid Redux complexity)
- **Build Tool:** Vite (fast, modern)

### Deployment
- **Containerization:** Docker + Docker Compose
- **Hosting:** Self-hosted Unraid server
- **Networking:** Tailscale (already set up)
- **Database:** PostgreSQL in a Docker container
- **Volume Mapping:** Docker volumes should map to Unraid's standard app data directory (e.g., `/mnt/user/appdata/roanes-kitchen` or equivalent)
- **Database Backups:** 
  - SQL dumps created daily via a scheduled job (e.g., 2:00 AM)
  - Retention: Keep only the most recent 30 days of backups (automated cleanup of dumps older than 30 days)
  - Backup location: Within the same volume (e.g., `/mnt/user/appdata/roanes-kitchen/backups/`) for easy access and backup

### LLM Integration (Future/Phase 2)
- **Beads:** Already integrated in project for potential future use
- **LangChain:** Deferred for now; may be useful for recipe scraping automation in Phase 2

## 9. Discord Integration Details

### Notification Types
1. **Action Notification**
   - Trigger: At the configured notification time (default 7am) on the day of the event
   - Content: "Today: Bob is cooking Tikka Masala" or "Today: Alice is shopping"
   - Delivery: Posted to the configured Discord channel

2. **Shopping Notification**
   - Trigger: At the configured notification time (default 7am) on the day of the shopping action
   - Content: Formatted grocery list with ingredients and quantities
   - Delivery: Posted to the configured Discord channel

3. **Week Transition Notification**
   - Trigger: At the configured notification time (default 7am) on the day the new week starts
   - Content: "New week starting: Burger Week. Bob cooks Monday & Wednesday, Alice cooks Thursday & Friday"
   - Delivery: Posted to the configured Discord channel

### Notification Configuration
- **Global Settings (not per-user):**
  - Discord bot token (encrypted, stored in `settings` table)
  - Notification channel ID (single channel for all notifications)
  - Notification time (HH:MM format, default "07:00")
  - Notification timezone (e.g., "America/Los_Angeles", "UTC")
- **Server Timezone:** Server runs in UTC but converts notification time to configured timezone

### Implementation
- Store Discord user IDs in the `users` table (for potential future use or @mentions)
- Store global notification settings in `settings` table (see Section 5)
- APScheduler jobs:
  1. **Daily notification check:** Runs frequently (every minute or 5 minutes), checks if current time matches configured notification time in configured timezone, then posts all events happening today
  2. **Week advancement:** Creates new meal plan instance and posts week transition notification at configured notification time on the day the week starts
- Discord bot posts to the configured channel only (no DMs, no per-user preferences in MVP)

## 10. MVP Scope: What's In, What's Out

### IN (MVP)
- Recipe CRUD (including ownership reassignment and soft delete)
- Schedule sequences with completely pre-packaged themed week templates
- Day/person/action/recipe assignments within week templates
- Meal plan instance generation (copying template assignments)
- Auto-advancing through the week template sequence
- Grocery list generation with ingredient aggregation
- Basic authentication (username/password)
- Global Discord notifications (single channel, configurable time/timezone, sent on day of event)
- Self-hosted Docker setup with daily backups (30-day retention)

### OUT (Phase 2+)
- Per-instance modifications (e.g., "this week, swap the Butter Chicken recipe for something else")
- Instance-level overrides (e.g., "this week, Bob cooks Thursday instead of Monday")
- Historical instance tracking & modification logging
- Schedule pause/resume (pause the sequence advancement temporarily)
- Recipe scraping from URLs
- Gantt chart visualization for meal prep timing
- Ingredient-level timing dependencies
- Cycle detection for dependencies
- Advanced permissions/roles
- Shared recipe ownership (multiple users per recipe)
- Centralized ingredient management with brand preferences and sourcing information
- Grocery list sorting by store aisle
- Per-user notification preferences (multiple timings, DMs, @-mentions)
- Advance notifications (e.g., "3 days before", "12 hours before")
- Bidirectional messaging with Discord (i.e., responding to notifications to mark tasks done)
- User deactivation/deletion functionality
- Mobile app
- Sync with calendar apps
- Dietary restrictions / nutritional analysis
- Meal rating/feedback system
- Multiple color theme options (Phase 2+)

## 11. UI/UX Design & Layout Preferences

### Design Philosophy
The app prioritizes low-friction workflows and clear information architecture, recognizing that both users have ADHD and need intuitive navigation and reminders.

### Architecture & Navigation
- **Single-Page App (SPA):** Client-side routing using React Router (or similar). This allows for flexible layout changes and modular feature additions in later phases without restructuring the core navigation.
- **Layout Pattern:** Primary navigation sidebar or top nav with main content area. Reserved space for persistent sections like "Upcoming Week's Grocery Trip".

### Core UI Components

#### Recipe Management
- **Recipe List:** Card-based layout showing recipe name, owner, category, and quick actions (edit, retire, view details).
- **Recipe Detail Panel:** Vertical card format with editable fields:
  - Name, category, prep/cook times
  - Ingredients (add/remove/edit inline)
  - Instructions (numbered, add/remove/reorder)
  - Prep notes, postmortem notes
  - Owner reassignment dropdown
  - Retire button with validation (shows warning modal if recipe is in active templates)
- **Recipe Retirement UI:**
  - When retiring a recipe in use, show modal: "This recipe is used in 3 week templates: [list]. Remove it from these templates or retire them before retiring this recipe."
  - Option to view each template directly from the warning modal
- **Barebones but Adoptable:** Minimal design that doesn't overwhelm users but provides enough functionality for daily use.

#### Schedule & Meal Planning
- **Week Templates View:** List or card layout showing all themed weeks in the sequence with quick actions (edit, delete, reorder).
- **Week Template Editor:** Display day-by-day assignments (day, assigned user, action, recipe). Allow inline editing of assignments.
- **Current Week Instance:** Prominent display of the active week theme and full day-by-day schedule with assigned people and recipes.
- **Past Instances:** Collapsible history or separate view showing previous weeks (read-only).

#### Grocery Management
- **Upcoming Week's Grocery Trip Section:** Reserved UI area showing the next shopping day and a preview of the grocery list. In Phase 2, this will support in-situ editing and checkboxes before the list goes "live".
- **Grocery List View:** Aggregated ingredients with quantities and units. Reference which recipes contributed each ingredient. Option to view past lists.

#### Settings Page
- **Dedicated Settings UI:** Separate page for global application settings:
  - Discord bot token input (encrypted, with validation)
  - Discord notification channel ID input
  - Notification time picker (HH:MM format, default "07:00")
  - Notification timezone selector (dropdown or autocomplete)
  - Week advancement schedule dropdowns (day of week, time)
  - Theme toggle (Gruvbox Dark / Gruvbox Light)

### Theming & Visual Design

#### MVP (Phase 1)
- **Primary Theme:** Gruvbox (retro-inspired color scheme with warm earth tones)
  - Gruvbox Dark: For dark mode (default background `#282828`, foreground `#ebdbb2`)
  - Gruvbox Light: For light mode (default background `#fbf1c7`, foreground `#3c3836`)
- **Theme Toggle:** Simple Light/Dark switch in settings respecting user preference
- **Color Palette Details:** See `/docs/COLOR_PALETTES.md` for complete hex codes and implementation details
- **Typography:** Clear hierarchy with standard web fonts
- **Responsive Design:** Works on desktop and tablet (mobile deferred to Phase 2+)

#### Phase 2 (Color Theming)
- **Phased Color System:** Expand with supplementary palettes:
  - Embers (dark): Warm, moody dark theme
  - Velvet (dark): Rich, luxurious dark theme
  - Kiwi (light): Fresh, bright light theme
  - Popsicle (light): Playful, vibrant light theme
- **Theme Selection Dropdown:** Allow users to choose from multiple themed options
- **Foundation for Retro Aesthetic:** All chosen palettes support transition to TVA-inspired design

#### Phase IV+ (Retro 70s/Early 80s TVA Aesthetic)
- **Design Inspiration:** Time Variance Authority building from Marvel's "Loki" TV series
- **Color Integration:** Build on Gruvbox foundation with warm oranges, burnt siennas, teals, mustard yellows, and rich earth tones
- **Production Design Elements:** Geometric patterns, angular layouts, retro typography, subtle parallax effects
- **Tone:** Nostalgic, slightly futuristic, playful—reflecting the TVA's blend of bureaucratic organization and cosmic scope
- **This is a visual refinement phase; functional architecture remains stable.**

### Interaction Patterns
- **Low-Friction Editing:** Cards or inline editing for quick updates without modal dialogs where possible
- **Confirmation for Destructive Actions:** Soft deletes (retirement) prompt for confirmation; restores are always available
- **Responsive Feedback:** Clear success/error messages for user actions
- **Discord Integration Feedback:** Visual indicator when Discord bot is connected/disconnected

### UX Patterns for MVP

#### Loading States
- **API Calls:** Show spinner or skeleton UI during data fetches (critical for ADHD-friendly UX)
- **Form Submissions:** Disable submit button and show loading indicator while processing
- **Long Operations:** Grocery list generation shows progress ("Aggregating ingredients...")
- **Navigation:** Show loading state when transitioning between routes

#### Error Handling
- **Validation Errors:** Inline field-level errors (red border + message below field)
- **API Errors:** Toast notifications at top of screen with error message
- **Network Errors:** "Connection lost" banner with retry button
- **Permission Errors:** Clear message explaining why action failed (e.g., "Cannot retire recipe - in use by 3 templates")
- **Retry Logic:** Failed API calls show "Retry" button

#### Empty States
- **No Recipes:** "No recipes yet. Create your first recipe to get started" with prominent CTA button
- **No Week Templates:** "Create your first themed week to start planning meals"
- **No Instances:** "No meal plans yet. Advance to start your first week"
- **No Grocery Lists:** "Generate a grocery list for your next shopping day"

#### Authentication Flows
- **Login:** Username/password form, session stored in localStorage/cookie
- **Session Expiry:** JWT expires after 7 days; redirect to login with "Session expired" message
- **No Password Reset in MVP:** Users with forgotten passwords contact admin (2-person system)
- **Registration:** Simple username/password form (no email verification needed)

#### Discord Setup Flow
- **First-Time Setup:**
  1. Create Discord bot in Discord Developer Portal (user does this manually)
  2. Add bot to Discord server (user does this manually)
  3. In app settings, paste bot token
  4. Click "Validate Token" button → app checks bot connection
  5. Enter channel ID where notifications should post
  6. Save settings
- **Connection Status:** Settings page shows "Connected" or "Disconnected" with last check time
- **No OAuth Flow in MVP:** Manual token entry is sufficient for 2-person system

### Future Flexibility
- The single-page architecture and component-based design allow for easy UI updates without backend changes
- Phase 2 can introduce new sections (e.g., in-situ grocery list editing, recipe rating) without restructuring
- Phase IV+ theming can be applied globally across all components using a centralized theme system (CSS variables, Tailwind theme config, or similar)

## 12. Known Constraints & Decisions

### Week Templates are Immutable in MVP; Per-Instance Modifications in Phase 2
In MVP, week templates are completely pre-packaged and immutable. When a week instance is created, it acts as a read-only reference to the template. Instances do not store their own assignments; instead, assignments are queried from the template's `week_day_assignments` on-demand, with dates calculated from the instance's `instance_start_date`.

In Phase 2, a `meal_assignments` table will be added to store instance-specific assignments. This allows per-instance modifications (e.g., swapping recipes for a specific week) without affecting the template or other instances. The Phase 2 migration will involve:
1. Adding the `meal_assignments` table
2. Optionally backfilling historical instances with copies of their template assignments (for historical accuracy)
3. Enabling instance-level editing in the UI

This class/object pattern allows templates to remain clean blueprints while instances can be flexible when needed.

### Recipes Tied to Single Owner (MVP), Shared Ownership (Phase 2)
In MVP, recipes are owned by a single person, reflecting the current UX preference: Bob knows how to cook Pasta Carbonara; Alice doesn't. Users can reassign ownership to another user if they learn the recipe. In Phase 2, the data model can be extended to allow multiple owners per recipe (via a join table), enabling collaborative recipe management.

### Soft Delete for Recipes and Week Templates (Retirement)
Recipes and week templates use soft delete with a `retired_at` timestamp. This allows accidental deletions to be easily recovered and provides historical record-keeping. Retired items are hidden from active selection but remain queryable for reports, recovery, and historical data integrity.

**Retirement validation:**
- Recipes in active week templates cannot be retired (must remove from templates first, or retire the templates)
- Week templates with future instances cannot be retired without confirmation
- Retired week templates remain accessible to past instances that reference them

### Multiple Actions Per Day Per Person
A person can have multiple actions on the same day (e.g., "shop" and "takeout"). The `order` field in `week_day_assignments` disambiguates if needed. No validation prevents multiple actions; the UI and business logic handle it appropriately.

### No Quantity Aggregation Validation
Grocery lists show aggregated quantities, but the app doesn't validate whether users have enough food on hand. Users are expected to know their pantry state and adjust accordingly. This is a user responsibility, not an app responsibility.

### Schedule Advancement Edge Cases
**Initial Setup:**
- When a schedule sequence is first created, `current_week_index` starts at 0 (pointing to the first week template)
- The first meal plan instance is created immediately with `instance_start_date` = current date (or next occurrence of `advancement_day_of_week`)
- Users manually trigger the first instance creation via UI or it happens automatically on first system startup

**Manual Advancement:**
- `POST /meal-plans/advance-week` increments `current_week_index` and creates a new instance
- Manual advancement does not affect the automatic advancement schedule
- Next auto-advancement occurs at the next scheduled time (e.g., next Monday at 9am)
- This can result in two advancements close together if manual happens right before auto

**System Downtime Recovery:**
- On startup, check if advancement was missed during downtime
- If current date/time is past the last scheduled advancement, catch up by advancing once (not multiple times)
- Example: System down for 3 weeks → on restart, advance once to current week, not 3 times
- This prevents creating multiple historical instances

**Timezone Handling:**
- Server runs in UTC but `advancement_time` is interpreted in `notification_timezone` (from settings)
- APScheduler converts timezone on schedule creation
- If timezone setting changes, existing schedules must be recreated
- Example: `advancement_time = "09:00"`, `timezone = "America/Los_Angeles"` → advance at 17:00 UTC

**Sequence Loop Behavior:**
- When `current_week_index` reaches the end of the sequence, reset to 0
- Example: 4 week templates (indices 0-3) → after week 3, next advancement goes to week 0

### Bidirectional Dependencies (Phase 2 Note)
Recipe instruction steps can eventually have bidirectional dependencies. The data model supports this, but circular dependency validation is deferred to Phase 2 (when Gantt visualization is added). For MVP, users can enter dependency data, but it won't be validated or visualized.

### Foreign Key Deletion Constraints
All foreign key relationships have explicit ON DELETE behavior to prevent data integrity issues:

**CASCADE (child data deleted with parent):**
- recipe_ingredients → recipes
- recipe_instructions → recipes
- week_day_assignments → schedule_weeks
- grocery_lists → meal_plan_instances
- grocery_list_items → grocery_lists

**RESTRICT (prevent deletion if references exist):**
- recipes.owner_id → users (can't delete user who owns recipes)
- week_day_assignments.assigned_user_id → users (can't delete user assigned in templates)
- week_day_assignments.recipe_id → recipes (can't delete recipe used in templates)
- schedule_weeks → schedule_sequences (can't delete sequence with templates)
- meal_plan_instances → schedule_weeks (can't delete template with instances)

**Deletion edge cases:**
- **User deletion:** Deferred to Phase 2. In MVP, users cannot be deleted (2-person system doesn't need this).
- **Recipe deletion:** Use retirement (`retired_at`) instead of hard delete. Validation prevents retiring recipes in active templates.
- **Week template deletion:** Use retirement (`retired_at`) to preserve historical data for instances.
- **Sequence deletion:** Must delete or retire all week templates first (RESTRICT enforces this).

### No Recipe Versioning
Recipes don't have version history. When a recipe is edited, the old version is lost. This is acceptable for MVP given the small team size and low volume. Versioning can be added in Phase 2 if needed.

### Global Notification Settings (Simplified for MVP)
To reduce complexity in MVP, notification settings are global (not per-user):
- Single Discord channel for all notifications (no DMs, no per-user preferences)
- Configurable notification time (default 7am) sent on the day of the event
- Configurable timezone to ensure notifications arrive at the correct local time
- Server runs in UTC but converts notification time to configured timezone
- Per-user preferences, advance notifications (e.g., "3 days before"), and multiple delivery methods are deferred to Phase 2

### Grocery List Generation Across Week Boundaries
Week instances represent calendar weeks (typically Sun-Sat), but shopping cycles may not align with these boundaries. To handle this:
- Each grocery list is generated for a specific shopping day
- The list covers meals from the day **after** the shopping day through the **next** shopping day (inclusive)
- The shopping day itself is excluded from the list
- Lists may span multiple week instances when the shopping cycle crosses week boundaries

**Example:** If shopping is on Monday, the list covers Tuesday through the following Monday (inclusive), which spans two week instances if weeks run Sun-Sat.

**Implementation:** The grocery list generation algorithm:
1. Validate that the specified `shopping_date` has a "shop" action in the given `meal_plan_instance`
2. Find the next "shop" action by searching:
   - First, remaining days in the current instance
   - Then, subsequent week instances in chronological order
3. Query all `meal_assignments` with recipes from `shopping_date + 1 day` through `next_shopping_date` (inclusive)
4. Aggregate ingredients across all recipes in that date range using unit-aware aggregation (see below)

### Unit-Aware Ingredient Aggregation
Grocery list aggregation uses the **Pint** library for Python to handle unit conversions and intelligent summing:

**Aggregation Logic:**
1. Group ingredients by `ingredient_name` (case-insensitive)
2. For each ingredient group, use Pint to determine unit dimensionality:
   - Volume units (cup, tablespoon, teaspoon, fluid_ounce, ml, liter, etc.) → convert to canonical volume unit (e.g., cups)
   - Weight units (gram, kilogram, ounce, pound) → convert to canonical weight unit (e.g., grams)
   - Count/special units (bunch, clove, can, to_taste) → no conversion, sum as-is
3. Sum quantities within each dimension
4. If an ingredient has multiple dimensions (e.g., "1 cup butter" + "8 oz butter"), display as separate line items

**Example:**
```
Input:
- Recipe A: 1 cup milk
- Recipe B: 8 fluid_ounce milk
- Recipe C: 2 tablespoon milk

Output:
- milk: 2.125 cups (Pint converts all to cups: 1 + 1 + 0.125)
```

**Limitation (acceptable for MVP):** Volume-to-weight conversions require ingredient density (e.g., "1 cup flour" cannot convert to grams without knowing flour's density). These appear as separate items. Phase 2 can add an ingredient density table if needed.

**Library:** Pint (https://pint.readthedocs.io/) - industry-standard Python library for physical quantities and unit conversions, includes built-in support for cooking measurements.

## 13. Migration Plan (Notion → New App)

**Notion export location:** `/Users/tonye/github/plongitudes/roanes-kitchen/reference_material/notion_export`

**Export contents:**
- CSV summary file with recipe metadata
- 26 individual recipe markdown files with ingredients and instructions

**Migration Steps:**

### Automated: Recipe Import (Script)
1. **Parse Notion export data:**
   - Read CSV for recipe metadata (name, owner, type, times)
   - Parse markdown files for ingredients and instructions
   - Map ingredient strings to app's unit constraints (normalize "Cup" → "cup", etc.)

2. **Import into database:**
   - Create user accounts (if not already exist)
   - Insert recipes with metadata
   - Insert recipe_ingredients (validate units against allowed list)
   - Insert recipe_instructions (preserve step order)

3. **Validation:**
   - Verify all 26 recipes imported successfully
   - Check for unit validation errors (flag for manual cleanup)
   - Confirm ownership assignments

**Estimated effort:** 1-2 hours to write script + run import

### Manual: Schedule Setup
1. **Create schedule sequence:**
   - Define sequence name (e.g., "Fall & Winter Rotation")
   - Set advancement schedule (day of week + time)

2. **Create week templates:**
   - Define themed weeks (e.g., "Indian Cuisine Week", "Burger Week", "Pasta Week")
   - For each week, assign:
     - Person to each day
     - Action (cook, shop, rest, takeout)
     - Recipe (if action = cook)
   - Set week order in sequence

3. **Create first meal plan instance:**
   - Trigger initial instance creation for current week
   - Verify assignments display correctly

**Estimated effort:** 2-4 hours (depending on number of themed weeks)

### Testing & Cutover
1. Test recipe viewing and editing
2. Test grocery list generation for current week
3. Verify Discord notifications (if configured)
4. Run through complete week advancement cycle
5. Decommission Notion after successful validation

**Total migration effort:** 4-6 hours (automated import + manual schedule setup + testing)

## 14. Development Phases

### Phase 1 (MVP)
1. Backend setup (FastAPI, PostgreSQL, auth, DB schema)
2. Recipe management API
3. Schedule sequence & week template API
4. Meal plan instance generation & retrieval API
5. Grocery list API
6. Frontend UI (React/Vite) with Gruvbox theming
7. APScheduler for week advancement and per-user configurable Discord notifications
8. Database backup job (daily, 30-day retention)
9. Deployment & testing

### Phase 2 (Post-MVP)
- Per-instance modifications (recipe swaps, action reassignments)
- Historical instance tracking & audit log
- Schedule pause/resume functionality
- Shared recipe ownership
- Recipe scraping from URLs
- Gantt chart for meal prep timing
- Cycle detection for dependencies
- Grocery list aisle sorting
- Additional color theme options (Embers, Velvet, Kiwi, Popsicle)
- Advanced features (dietary tracking, ratings, etc.)

---

## 15. Questions & Open Items

### Answered ✅
- [x] **Discord bot token storage:** Webapp stores bot token in settings UI (encrypted)
- [x] **PostgreSQL credentials:** Default admin:admin for MVP
- [x] **Natural language scheduling:** Deferred to Phase 2; MVP uses dropdown UI (e.g., "Every Monday at 9:00 AM")
- [x] **Notion export location:** Available at `/Users/tonye/github/plongitudes/roanes-kitchen/reference_material/notion_export`
- [x] **Week advancement cadence:** Always weekly
- [x] **UI wireframes & layout preferences:** Comprehensive UI/UX section added (Section 11)
- [x] **Notification timing preferences:** Simplified to global settings; single notification at configurable time (default 7am) on day of event; per-user preferences deferred to Phase 2
- [x] **Database backup strategy:** Daily SQL dumps, 30-day retention, stored in app data volume
- [x] **Notion export format:** Ready to parse; CSV summary + markdown recipe files in `reference_material/notion_export`
- [x] **Color/styling preferences:** Gruvbox Dark/Light for MVP; Phase 2 adds Embers, Velvet, Kiwi, Popsicle palettes (see COLOR_PALETTES.md)
- [x] **Notification delivery method:** Global single Discord channel; DMs and per-user preferences deferred to Phase 2

### Outstanding
- [ ] Discord bot permissions scope (which permissions needed for channel posting) — **Defer to implementation phase**

