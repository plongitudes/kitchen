# Requirements Update Summary

## Status: ✅ COMPLETE

All items from the conversation in `update.md` have been successfully integrated into `REQUIREMENTS.md`.

## Changes Made

### 1. Data Model Updates
- **schedule_sequences table** now includes:
  - `advancement_day_of_week: int` (0=Sunday, 6=Saturday)
  - `advancement_time: string` (HH:MM format)
  - `discord_bot_token: string` (encrypted storage)

### 2. User Stories Additions
- **Section 6.5 - Settings & Configuration** (NEW)
  - US-26: Access settings page
  - US-27: Store/update Discord bot token
  - US-28: Configure advancement schedule via dropdowns
  - US-29: Configure notification preferences
  
- **Section 6.7 - User Accounts & Authentication** (RENUMBERED)
  - US-30: Create account
  - US-31: Login/session management
  - US-32: Account associations

### 3. Feature Updates
- **US-12** revised to specify dropdown scheduling (no natural language parsing in MVP)
- Natural language scheduling deferred to Phase 2

### 4. API Endpoints (NEW)
- **Settings & Configuration endpoints:**
  - `GET /settings`
  - `PUT /settings`
  - `POST /settings/validate-discord-token`

### 5. New Section: UI/UX Design & Layout Preferences (Section 11)
Comprehensive coverage of:
- Design philosophy & architecture
- Core UI components (recipes, schedule, grocery, settings)
- Theming approach:
  - MVP (Phase 1): Light/Dark toggle
  - Phase 2: Color theming system
  - Phase IV+: Retro 70s/80s TVA aesthetic inspiration
- Interaction patterns
- Future flexibility

### 6. Configuration Decisions
- ✅ **Discord bot token:** Stored in webapp settings UI (encrypted)
- ✅ **PostgreSQL credentials:** admin:admin for MVP
- ✅ **Scheduling approach:** Dropdown UI (not natural language)
- ✅ **Notion export location:** `/Users/tonye/github/plongitudes/roanes-kitchen/reference_material`
- ✅ **Week advancement:** Always weekly
- ✅ **UI design:** Single-page app with detailed preferences documented

### 7. Section Numbering Updates
- Section 11: UI/UX Design (NEW)
- Section 12: Known Constraints & Decisions (was 11)
- Section 13: Migration Plan (was 12)
- Section 14: Development Phases (was 13)
- Section 15: Questions & Open Items (was 14)

### 8. Updated Open Items
**Answered Questions:**
- [x] Discord bot token storage
- [x] PostgreSQL setup
- [x] Natural language parsing approach
- [x] Notion export location
- [x] Week advancement cadence
- [x] UI wireframes & layout

**Outstanding Questions:**
- [ ] Exact notification timing preferences
- [ ] Discord bot permissions scope
- [ ] PostgreSQL backup strategy
- [ ] Notion export format/mapping details
- [ ] MVP color/styling preferences
- [ ] Notification delivery method preference

## File Locations
- **Updated Requirements:** `/Users/tonye/github/plongitudes/roanes-kitchen/docs/REQUIREMENTS.md`
- **Original Conversation:** `/Users/tonye/github/plongitudes/roanes-kitchen/update.md`
- **Notion Export Reference:** `/Users/tonye/github/plongitudes/roanes-kitchen/reference_material`

## Next Steps
1. ✅ Critical review pass (by another Claude)
2. First dev sprint planning (with Beads in mind)
3. Examine Notion export structure
4. Begin development!
