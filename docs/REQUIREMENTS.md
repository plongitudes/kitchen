# Roanes Kitchen - Requirements & Design Document

## 1. Problem Statement

Two people sharing meal prep responsibilities need a self-hosted way to manage a growing library of recipes, assign them on a rotating schedule, and generate weekly grocery lists. Currently handled via Notion, which is too limited for this use case.

## 2. Users & Context

- **Primary Users:** Two people living together (one very technical, one semi-technical)
- **Usage Frequency:** Daily
- **Key Constraint:** UX friction is problematic for adoption; both users have ADHD, so clear reminders and low-friction workflows are critical
- **Hosting:** Self-hosted on Unraid server via Docker containers; access via Tailscale (internal network only, no credential security concerns)
- **Communication Hub:** Established Discord server for announcements and reminders

## 3. Success Criteria (MVP)

- [x] Migrate data away from Notion
- [x] Web UI allows users to:
  - Manage recipes (CRUD operations)
  - Create and maintain a repeating weekly meal schedule
  - Assign meals to dates and dates to people
  - View upcoming meals and assignments
  - Generate grocery lists based on shopping day and upcoming meals
- [x] Scheduled events trigger Discord notifications:
  - Upcoming meal event (e.g., "Bob is cooking Pasta Carbonara on Monday")
  - Grocery shopping event (e.g., "Here's Tuesday's grocery list")
  - Recipe additions/retirements (optional, nice-to-have)
- [x] Schedule repeats automatically after the final week

## 4. Core Concepts

### 4.1 Recipes
Recipes are owned by a person (tied to their cooking skill/preferences). Each recipe has:
- Name
- Ingredients (list of: ingredient name, quantity, unit)
- Instructions (ordered steps)
- Metadata (prep time, cook time, recipe type/category)
- Notes (prep notes, postmortem/cooking notes)
- Duration & dependency tracking (for future Gantt chart feature—see Phase 2)

### 4.2 Weekly Schedule
A repeating pattern of meal assignments. Example:
- Monday: Bob cooks
- Tuesday: Takeout (no prep)
- Wednesday: Bob cooks
- Thursday: Alice cooks
- Friday: Alice cooks
- Saturday: Grocery shopping day
- Sunday: Flexible/rest

This pattern repeats indefinitely. Changes to the schedule (e.g., person swaps a day off-line, or a permanent role change) require manual adjustment in the app, effective either that week or the next.

### 4.3 Meal Plan
The specific assignment of recipes to dates in a given week. Example:
- Monday (Bob): Pasta Carbonara
- Wednesday (Bob): Chicken Stir-Fry
- Thursday (Alice): Salmon with Roasted Vegetables
- Friday (Alice): Tacos

When a new week starts, the schedule repeats (same person cooks same day), but recipes can be rotated/reassigned.

### 4.4 Grocery List
Auto-generated based on a grocery shopping day. Pulls all recipes scheduled between the day after shopping and the day before the next shopping event, aggregates ingredients, and sums quantities.

### 4.5 Users & Accounts
Two user accounts in the system (one per person). No complex permissions needed; both can edit everything. Authentication is lightweight (username/password, bcrypt hashed). Accounts are used to:
- Associate people with recipe ownership
- Assign people to meal schedule dates
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

#### `schedules`
```
id: UUID (primary key)
name: string (e.g., "Default Weekly Schedule")
created_at: timestamp
updated_at: timestamp
```

#### `schedule_assignments`
```
id: UUID (primary key)
schedule_id: UUID (foreign key → schedules.id)
day_of_week: int (0=Sunday, 6=Saturday)
assigned_user_id: UUID (foreign key → users.id)
event_type: string (e.g., "cook", "takeout", "shopping", "rest")
order: int (for multiple events on same day, if needed)
created_at: timestamp
```

#### `meal_plans`
```
id: UUID (primary key)
week_start_date: date (Monday of the week)
created_at: timestamp
updated_at: timestamp
```

#### `meal_plan_entries`
```
id: UUID (primary key)
meal_plan_id: UUID (foreign key → meal_plans.id)
date: date
assigned_user_id: UUID (foreign key → users.id)
recipe_id: UUID (foreign key → recipes.id, nullable for takeout/rest days)
created_at: timestamp
updated_at: timestamp
```

#### `grocery_lists`
```
id: UUID (primary key)
meal_plan_id: UUID (foreign key → meal_plans.id)
shopping_date: date
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
- **US-2:** As a user, I can view all recipes I own.
- **US-3:** As a user, I can edit any field of my recipe (name, ingredients, instructions, metadata, notes).
- **US-4:** As a user, I can delete a recipe.
- **US-5:** As a user, I can see which person owns each recipe.

### 6.2 Weekly Schedule Management
- **US-6:** As a user, I can view the repeating weekly schedule (which person cooks which day).
- **US-7:** As an admin (probably the technical person), I can edit the weekly schedule (e.g., change who cooks on Monday, add a takeout day).
- **US-8:** When the schedule is updated, it takes effect either that week or the next (user can choose).

### 6.3 Meal Planning & Assignment
- **US-9:** As a user, I can view the current week's meal plan (which recipes are assigned to which dates/people).
- **US-10:** As a user, I can assign a recipe to a date/person in the current week's meal plan.
- **US-11:** As a user, I can unassign a recipe from a date (e.g., mark it as takeout or rest day).
- **US-12:** When a new week begins, the system auto-generates a new meal plan with the repeating schedule intact (people assigned to correct days, but recipes empty/awaiting assignment).

### 6.4 Grocery List Generation
- **US-13:** As a user, I can generate a grocery list for the upcoming week based on the shopping day (e.g., "generate groceries for Saturday's shopping trip, covering Mon-Fri meals").
- **US-14:** The grocery list aggregates ingredients from all assigned recipes, summing quantities where ingredients overlap.
- **US-15:** As a user, I can view past grocery lists (read-only).

### 6.5 Discord Integration
- **US-16:** When a meal is scheduled for a date, a Discord notification is sent to the assigned person (e.g., "Bob, you're cooking Pasta Carbonara on Monday at 6 PM").
- **US-17:** When a grocery shopping day arrives, a Discord notification is sent with the aggregated grocery list.
- **US-18:** Discord notifications are sent on a configurable schedule (e.g., 24 hours before the event, or on the morning of).

### 6.6 User Accounts & Authentication
- **US-19:** Users can create an account with username/password (stored securely with bcrypt).
- **US-20:** Users can log in and maintain a session.
- **US-21:** User accounts are tied to recipe ownership and meal schedule assignments.

## 7. API Endpoints (Rough)

### Authentication
- `POST /auth/register` — Create a new user account
- `POST /auth/login` — Authenticate and return session token
- `POST /auth/logout` — End session

### Recipes
- `GET /recipes` — List all recipes for authenticated user (filtered by owner)
- `POST /recipes` — Create a new recipe
- `GET /recipes/{id}` — Retrieve a specific recipe
- `PUT /recipes/{id}` — Update a recipe
- `DELETE /recipes/{id}` — Delete a recipe
- `GET /recipes/{id}/ingredients` — Get ingredients for a recipe
- `POST /recipes/{id}/ingredients` — Add an ingredient to a recipe
- `PUT /recipes/{id}/ingredients/{ingredient_id}` — Update an ingredient
- `DELETE /recipes/{id}/ingredients/{ingredient_id}` — Remove an ingredient

### Schedule
- `GET /schedules` — List all schedules (usually just one)
- `GET /schedules/{id}` — Get a specific schedule with assignments
- `PUT /schedules/{id}` — Update schedule (change who cooks which day)

### Meal Plans
- `GET /meal-plans` — List meal plans (current week, past weeks)
- `GET /meal-plans/current` — Get the current week's meal plan
- `POST /meal-plans/generate` — Auto-generate next week's meal plan
- `GET /meal-plans/{id}` — Get a specific meal plan
- `POST /meal-plans/{id}/entries` — Add a recipe assignment to a date
- `PUT /meal-plans/{id}/entries/{entry_id}` — Update a meal plan entry
- `DELETE /meal-plans/{id}/entries/{entry_id}` — Remove a meal plan entry

### Grocery Lists
- `GET /grocery-lists` — List all grocery lists
- `POST /grocery-lists/generate` — Generate a new grocery list for an upcoming shopping day
- `GET /grocery-lists/{id}` — Get a specific grocery list with items

### Discord Integration
- `POST /discord/sync-user` — Link a Discord user ID to an app user account (for notifications)
- `GET /discord/status` — Check Discord bot connection status

## 8. Architecture & Tech Stack

### Backend
- **Language/Framework:** Python + FastAPI (lightweight, fast, good for APIs)
- **Database:** PostgreSQL (self-hosted, ACID transactions, relational data structure)
- **Task Scheduling:** APScheduler or Celery (for Discord notifications on a schedule)
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

### LLM Integration (Future/Phase 2)
- **Beads:** Already integrated in project for potential future use
- **LangChain:** Deferred for now; may be useful for recipe scraping automation in Phase 2

## 9. Discord Integration Details

### Notification Types
1. **Meal Assignment Notification**
   - Trigger: A meal is assigned to a date (or week auto-generates)
   - Content: "Bob, you're cooking Pasta Carbonara on Monday"
   - Channel: DM or dedicated channel

2. **Grocery Shopping Notification**
   - Trigger: Grocery list is generated or shopping day arrives
   - Content: Formatted grocery list with ingredients and quantities
   - Channel: DM or dedicated channel

3. **Recipe Event Notification (Phase 2)**
   - Trigger: Recipe added/updated/deleted
   - Content: "New recipe added: Salmon with Roasted Vegetables (owned by Alice)"
   - Channel: Shared channel or DM

### Implementation
- Store Discord user IDs in the `users` table
- On MVP launch, users link their Discord accounts via a `/discord/sync-user` endpoint
- APScheduler or Celery jobs check for upcoming events and send notifications
- Discord bot posts to DMs or a configured channel

## 10. MVP Scope: What's In, What's Out

### IN (MVP)
- Recipe CRUD
- Weekly schedule definition
- Meal plan assignment
- Auto-generating meal plans for new weeks
- Grocery list generation with ingredient aggregation
- Basic authentication (username/password)
- Discord notifications (meal and grocery list)
- Self-hosted Docker setup

### OUT (Phase 2+)
- Recipe scraping from URLs
- Gantt chart visualization for meal prep timing
- Ingredient-level timing dependencies
- Cycle detection for dependencies
- Advanced permissions/roles
- Historical data archive UI
- Grocery list sorting by store aisle
- Bidirectional messaging with Discord (i.e., responding to notifications to mark tasks done)
- Mobile app
- Sync with calendar apps
- Dietary restrictions / nutritional analysis
- Meal rating/feedback system

## 11. Known Constraints & Decisions

### Recipes Tied to People
Recipes are owned by a single person, not shared globally. This reflects the current UX preference: Bob knows how to cook Pasta Carbonara; Alice doesn't. If Bob is assigned to a day, his recipes go with him. This keeps the logic simple in MVP but can be revisited in Phase 2 if shared recipe libraries are desired.

### No Quantity Aggregation Validation
Grocery lists show aggregated quantities, but the app doesn't validate whether users have enough food on hand. Users are expected to know their pantry state and adjust accordingly. This is a user responsibility, not an app responsibility.

### Bidirectional Dependencies (Phase 2 Note)
Recipe instruction steps can eventually have bidirectional dependencies. The data model supports this, but circular dependency validation is deferred to Phase 2 (when Gantt visualization is added). For MVP, users can enter dependency data, but it won't be validated or visualized.

### Static Recurring Schedule
The weekly schedule repeats identically each week. Ad-hoc swaps (e.g., "Bob and Alice trade Thursday and Monday this week only") are handled offline; permanent changes require an app adjustment. This keeps the logic simple in MVP.

### No Recipe Versioning
Recipes don't have version history. When a recipe is edited, the old version is lost. This is acceptable for MVP given the small team size and low volume. Versioning can be added in Phase 2 if needed.

## 12. Migration Plan (Notion → New App)

- Export recipe data from Notion
- Parse and map into app schema (recipes, ingredients, instructions)
- Manually define the weekly schedule in the app
- Import past meal plans (optional, deferred to Phase 2)
- Test end-to-end workflow before decommissioning Notion

## 13. Development Phases

### Phase 1 (MVP)
1. Backend setup (FastAPI, PostgreSQL, auth, DB schema)
2. Recipe management API
3. Schedule & meal plan API
4. Grocery list API
5. Frontend UI (React/Vite)
6. Discord bot integration
7. Deployment & testing

### Phase 2 (Post-MVP)
- Recipe scraping from URLs
- Gantt chart for meal prep timing
- Cycle detection for dependencies
- Grocery list aisle sorting
- Historical data UI
- Advanced features (dietary tracking, ratings, etc.)

---

## 14. Questions & Open Items

- [ ] Discord bot token & permissions set up
- [ ] PostgreSQL database admin access & backup strategy
- [ ] Exact notification timing preferences (e.g., when should meal reminders fire?)
- [ ] Notion export format—ready to parse?
- [ ] UI wireframes or layout preferences?
