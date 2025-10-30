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

#### `notification_preferences`
```
id: UUID (primary key)
user_id: UUID (foreign key → users.id)
event_type: string (e.g., "action_reminder", "shopping_list", "week_transition")
notification_channels: JSON array (list of: {"type": "dm"|"channel"|"channel_mention", "channel_id": int (optional)})
notification_times: JSON array (list of: {"value": int, "unit": "minutes"|"hours"|"days"})
created_at: timestamp
updated_at: timestamp
```

#### `recipes`
```
id: UUID (primary key)
owner_id: UUID (foreign key → users.id)
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

#### `recipe_ingredients`
```
id: UUID (primary key)
recipe_id: UUID (foreign key → recipes.id)
ingredient_name: string
quantity: float
unit: string (e.g., "cups", "tsp", "lbs", "g")
order: int (for sorting)
created_at: timestamp
```

#### `recipe_instructions`
```
id: UUID (primary key)
recipe_id: UUID (foreign key → recipes.id)
step_number: int
description: string
duration_minutes: int (optional, null for MVP; used in Phase 2 for Gantt chart)
depends_on_step_id: UUID (optional, null for MVP; Phase 2 feature)
created_at: timestamp
```

#### `schedule_sequences`
```
id: UUID (primary key)
name: string (e.g., "Fall & Winter Rotation")
created_at: timestamp
updated_at: timestamp
current_week_index: int (tracks which week in the sequence is active; auto-increments)
advancement_day_of_week: int (0=Sunday, 6=Saturday; which day to advance to next week)
advancement_time: string (HH:MM format; what time on that day to advance)
discord_bot_token: string (optional, stored encrypted; used for notifications)
```

#### `schedule_weeks` (Week Template / "Class")
```
id: UUID (primary key)
sequence_id: UUID (foreign key → schedule_sequences.id)
week_number: int (position in sequence, 1-indexed)
theme_name: string (e.g., "Indian Cuisine Week")
created_at: timestamp
updated_at: timestamp
```

#### `week_day_assignments` (Template Assignments)
```
id: UUID (primary key)
week_id: UUID (foreign key → schedule_weeks.id)
day_of_week: int (0=Sunday, 6=Saturday)
assigned_user_id: UUID (foreign key → users.id)
action: string (e.g., "cook", "shop", "takeout", "rest")
recipe_id: UUID (foreign key → recipes.id, nullable for non-cook actions)
order: int (for multiple actions on same day, if needed)
created_at: timestamp
```

#### `meal_plan_instances` (Week Instance / "Object")
```
id: UUID (primary key)
schedule_week_id: UUID (foreign key → schedule_weeks.id)
instance_start_date: date (actual calendar date when this week instance begins)
created_at: timestamp
updated_at: timestamp
```

#### `meal_assignments` (Instance-Level Assignments)
```
id: UUID (primary key)
meal_plan_instance_id: UUID (foreign key → meal_plan_instances.id)
date: date (specific calendar date)
assigned_user_id: UUID (foreign key → users.id)
action: string (e.g., "cook", "shop", "takeout", "rest")
recipe_id: UUID (foreign key → recipes.id, nullable for non-cook actions)
created_at: timestamp
updated_at: timestamp
```

#### `grocery_lists`
```
id: UUID (primary key)
meal_plan_instance_id: UUID (foreign key → meal_plan_instances.id)
shopping_date: date (the date the shopping action occurs)
generated_at: timestamp
```

#### `grocery_list_items`
```
id: UUID (primary key)
grocery_list_id: UUID (foreign key → grocery_lists.id)
ingredient_name: string
total_quantity: float
unit: string
source_recipe_ids: string (JSON array of recipe IDs, for reference)
created_at: timestamp
```

## 6. Features & User Stories (MVP)

### 6.1 Recipe Management
- **US-1:** As a user, I can add a new recipe by providing name, ingredients (with quantities/units), instructions (as ordered steps), prep/cook times, and notes.
- **US-2:** As a user, I can view all recipes.
- **US-3:** As a user, I can edit any field of my recipe (name, ingredients, instructions, metadata, notes).
- **US-4:** As a user, I can retire a recipe (soft delete with a retirement date) to prevent accidental permanent deletion. Retired recipes are hidden from active use but remain in the system for historical reference.
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
- **US-14:** As a user, I can view the current week instance with all day/person/action/recipe assignments inherited from the template.
- **US-15:** As a user, I can view past week instances to see what was scheduled.
- **US-16:** When a new week instance begins, the system auto-creates the instance with all day/person/action/recipe assignments copied from the week template.

### 6.4 Grocery List Generation
- **US-17:** As a user, I can generate a grocery list for a given week instance, covering meals from the shopping day forward until (but not including) the next shopping day.
- **US-18:** The grocery list aggregates ingredients from all assigned recipes, summing quantities where ingredients overlap.
- **US-19:** As a user, I can view past grocery lists (read-only).

### 6.5 Settings & Configuration
- **US-26:** As a user, I can access a settings page to configure application preferences.
- **US-27:** As a user, I can store and update the Discord bot token via a settings UI.
- **US-28:** As a user, I can configure the weekly advancement schedule (day of week and time) via dropdown menus.
- **US-29:** As a user, I can configure per-user notification preferences. For each type of event (action reminder, shopping list, week transition), I can specify one or more notification delivery methods: DM, specific Discord channel, or specific Discord channel with @-mention. For timing, I can set multiple notifications in advance (e.g., "5 minutes before" AND "12 hours before" AND "3 days before"), with a maximum advance window of 6 days. Timing is specified using a formula: "N units" (minutes, hours, or days) in advance.

### 6.6 Discord Integration
- **US-20:** When a person is assigned to an action on a given date (from the week instance), a Discord notification is sent to them about the upcoming action (e.g., "Bob, you're cooking Tikka Masala on Monday").
- **US-21:** When a person is assigned to a "shop" action on a given date, a Discord notification is sent with the aggregated grocery list.
- **US-22:** Discord notifications are sent on a configurable schedule (per-user notification preferences; see US-29).

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
- `DELETE /recipes/{id}` — Soft-delete (retire) a recipe by setting retired_at
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
- `GET /meal-plans/current` — Get the current week instance with all assignments
- `POST /meal-plans/advance-week` — Manually advance to the next week template in the sequence
- `GET /meal-plans/{instance_id}` — Get a specific meal plan instance with all assignments

### Grocery Lists
- `GET /grocery-lists` — List all grocery lists
- `POST /grocery-lists/generate` — Generate a new grocery list for the current week instance
- `GET /grocery-lists/{id}` — Get a specific grocery list with items

### Notification Preferences
- `GET /users/{user_id}/notification-preferences` — Get user's notification preferences
- `PUT /users/{user_id}/notification-preferences` — Update notification preferences (channels and timing for each event type)

### Settings & Configuration
- `GET /settings` — Get current application settings (advancement schedule, notification preferences)
- `PUT /settings` — Update application settings (Discord bot token, advancement schedule, notification preferences)
- `POST /settings/validate-discord-token` — Validate Discord bot token before saving

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
   - Trigger: Per user-configured timing in advance of event (e.g., "5 minutes before", "3 hours before", "1 day before")
   - Content: "Bob, you're cooking Tikka Masala on Monday" or "Alice, you're shopping on Tuesday"
   - Delivery: Per-user preference (DM, channel, or channel with @-mention)

2. **Shopping Notification**
   - Trigger: Per user-configured timing in advance of shopping day
   - Content: Formatted grocery list with ingredients and quantities (covering Mon-Tue, for example)
   - Delivery: Per-user preference (DM, channel, or channel with @-mention)

3. **Week Transition Notification**
   - Trigger: When sequence advances to a new week template
   - Content: "New week: Burger Week. Bob cooks Monday & Wednesday, Alice cooks Thursday & Friday"
   - Delivery: Per-user preference (DM, channel, or channel with @-mention)

### Notification Configuration
- **User-Configurable Timing:** For each event type, users can set multiple notification times in advance (e.g., 5 minutes, 12 hours, 3 days before)
- **Time Formula:** N units in advance (where unit is minutes, hours, or days; maximum 6 days)
- **Delivery Methods (per event, per user):**
  - DM (direct message)
  - Specific channel (text in channel)
  - Specific channel with @-mention (tagged notification in channel)
- **Multiple Delivery Methods Allowed:** User can receive multiple notifications for the same event via different delivery methods

### Implementation
- Store Discord user IDs in the `users` table
- Store notification preferences in `notification_preferences` table (see Section 5)
- On MVP launch, users link their Discord accounts via a `/discord/sync-user` endpoint
- APScheduler jobs check for upcoming events using notification preferences and send notifications accordingly
- Discord bot posts to DMs or configured channels based on user preferences

## 10. MVP Scope: What's In, What's Out

### IN (MVP)
- Recipe CRUD (including ownership reassignment and soft delete)
- Schedule sequences with completely pre-packaged themed week templates
- Day/person/action/recipe assignments within week templates
- Meal plan instance generation (copying template assignments)
- Auto-advancing through the week template sequence
- Grocery list generation with ingredient aggregation
- Basic authentication (username/password)
- Per-user configurable Discord notifications (multiple timings per event, multiple delivery methods)
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
- Grocery list sorting by store aisle
- Bidirectional messaging with Discord (i.e., responding to notifications to mark tasks done)
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
- **Dedicated Settings UI:** Separate page for user preferences and global defaults:
  - Discord bot token input (with validation)
  - Week advancement schedule dropdowns (day of week, time)
  - Per-user notification preferences configuration:
    - Event type selector (action reminder, shopping list, week transition)
    - Notification timing configuration (multiple entries allowed, each with "N units in advance")
    - Delivery method checkboxes (DM, channel, channel with @-mention)
    - Channel selector when channel is chosen
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
- **Notification Preferences UI:** Intuitive builder for specifying multiple notification times and delivery methods per event

### Future Flexibility
- The single-page architecture and component-based design allow for easy UI updates without backend changes
- Phase 2 can introduce new sections (e.g., in-situ grocery list editing, recipe rating) without restructuring
- Phase IV+ theming can be applied globally across all components using a centralized theme system (CSS variables, Tailwind theme config, or similar)

## 12. Known Constraints & Decisions

### Week Templates are Immutable in MVP; Per-Instance Modifications in Phase 2
In MVP, week templates are completely pre-packaged and immutable. When a week instance is created, it inherits all assignments (day/person/action/recipe) from the template as a snapshot. In MVP, instances are read-only. In Phase 2, an "overrides" or modifications layer can be added to allow per-instance changes (e.g., swapping recipes for a specific week) without affecting the template or other instances. This class/object pattern allows templates to remain clean blueprints while instances can be flexible when needed.

### Recipes Tied to Single Owner (MVP), Shared Ownership (Phase 2)
In MVP, recipes are owned by a single person, reflecting the current UX preference: Bob knows how to cook Pasta Carbonara; Alice doesn't. Users can reassign ownership to another user if they learn the recipe. In Phase 2, the data model can be extended to allow multiple owners per recipe (via a join table), enabling collaborative recipe management.

### Soft Delete for Recipes (Retirement)
Recipes use soft delete with a `retired_at` timestamp. This allows accidental deletions to be easily recovered and provides historical record-keeping. Retired recipes are hidden from active recipe selection but remain queryable for reports and recovery.

### Multiple Actions Per Day Per Person
A person can have multiple actions on the same day (e.g., "shop" and "takeout"). The `order` field in `week_day_assignments` disambiguates if needed. No validation prevents multiple actions; the UI and business logic handle it appropriately.

### No Quantity Aggregation Validation
Grocery lists show aggregated quantities, but the app doesn't validate whether users have enough food on hand. Users are expected to know their pantry state and adjust accordingly. This is a user responsibility, not an app responsibility.

### Bidirectional Dependencies (Phase 2 Note)
Recipe instruction steps can eventually have bidirectional dependencies. The data model supports this, but circular dependency validation is deferred to Phase 2 (when Gantt visualization is added). For MVP, users can enter dependency data, but it won't be validated or visualized.

### No Recipe Versioning
Recipes don't have version history. When a recipe is edited, the old version is lost. This is acceptable for MVP given the small team size and low volume. Versioning can be added in Phase 2 if needed.

### Per-User Notification Preferences
Each user can configure notification preferences independently. For each event type (action reminder, shopping list, week transition), users can specify:
- Multiple notification times in advance (e.g., 5 minutes AND 12 hours AND 3 days before, max 6 days)
- Multiple delivery methods (DM, channel, channel with @-mention can all be active simultaneously)
- This allows maximum flexibility for adoption and usage patterns while maintaining simplicity

## 13. Migration Plan (Notion → New App)

- Notion export data available in `/Users/tonye/github/plongitudes/roanes-kitchen/reference_material/notion_export`
- Export contains CSV summary and individual recipe markdown files
- Parse and map into app schema (recipes, ingredients, instructions)
- Define the week template sequence and day/person/action/recipe assignments in the app
- Trigger creation of the first week instance
- Test end-to-end workflow before decommissioning Notion

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
- [x] **Notification timing preferences:** Configurable per-user; multiple timings per event (5 min to 6 days); formula-based "N units in advance"
- [x] **Database backup strategy:** Daily SQL dumps, 30-day retention, stored in app data volume
- [x] **Notion export format:** Ready to parse; CSV summary + markdown recipe files in `reference_material/notion_export`
- [x] **Color/styling preferences:** Gruvbox Dark/Light for MVP; Phase 2 adds Embers, Velvet, Kiwi, Popsicle palettes (see COLOR_PALETTES.md)
- [x] **Notification delivery method:** Per-event, per-user choice of DM, channel, or channel with @-mention (multiple allowed simultaneously)

### Outstanding
- [ ] Discord bot permissions scope (which permissions needed for DMs and channel posting) — **Defer to implementation phase**

