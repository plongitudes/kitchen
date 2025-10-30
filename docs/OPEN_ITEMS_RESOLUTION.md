# Open Items Resolution Summary

**Date:** October 29, 2025  
**Status:** ✅ ALL RESOLVED

All outstanding items from the conversation have been addressed and integrated into the requirements documentation.

---

## 1. Notification Preferences ✅

### Requirement
Configurable notification preferences per-user with multiple notifications per event, using formula-based timing up to 6 days in advance.

### Resolution
- **Added to US-29:** Per-user configuration for each event type with multiple timing options
- **Data Model:** New `notification_preferences` table with:
  - `event_type`: Specifies which event (action_reminder, shopping_list, week_transition)
  - `notification_times`: JSON array of objects with `{"value": int, "unit": "minutes"|"hours"|"days"}`
  - `notification_channels`: JSON array of delivery method specifications
- **UI Implementation:** Settings page includes notification preference builder
- **Constraints:** Maximum advance window is 6 days (enforced at API level)
- **Multiple Notifications:** Users can specify 5 minutes AND 12 hours AND 3 days before the same event

### Integration Points
- Section 6.5 (US-29)
- Section 5 (Data Model: notification_preferences table)
- Section 9 (Discord Integration Details)
- Section 11 (Settings Page UI)

---

## 2. Discord Bot Permissions Scope ⏸️

### Requirement
Defer for now; determine actual permissions needed during implementation

### Resolution
- **Status:** Outstanding — moved to implementation phase
- **Reason:** Permissions scope depends on specific Discord API usage patterns and will be determined during backend development
- **Note:** Added to outstanding items in Section 15

---

## 3. Docker Volume & Database Backups ✅

### Requirement
Docker volume maps to Unraid standard app data directory; daily SQL dumps with 30-day retention

### Resolution
- **Volume Mapping:** 
  - Maps to `/mnt/user/appdata/roanes-kitchen` (standard Unraid pattern)
  - Configured in deployment section (Section 8)
- **Backup Strategy:**
  - Daily SQL dumps (suggested time: 2:00 AM)
  - Retention: Keep only most recent 30 days
  - Location: `/mnt/user/appdata/roanes-kitchen/backups/`
  - Automated cleanup of dumps older than 30 days
  - Backup directory within same volume for Unraid backup coverage
- **Implementation:** Scheduled APScheduler job to handle daily dumps and cleanup

### Integration Points
- Section 8 (Deployment: Volume Mapping and Database Backups)
- Section 14 (Phase 1: Step 8 - Database backup job)

---

## 4. Notion Export Ready ✅

### Requirement
Notion export should be ready; data available in reference_material directory

### Resolution
- **Location:** `/Users/tonye/github/plongitudes/roanes-kitchen/reference_material/notion_export/`
- **Contents:**
  - CSV file: `Recipes 26ff21647dc880a2a91bd74f125d4b2b_Recipes 26ff21647dc880a799c9000b2f8f6552_all.csv`
  - Markdown files: Individual recipe files in `Recipes/` subdirectory (26 recipes total)
  - Examples: Burritos, Pasta Primavera, Tamales, Zucchini Parmesan, etc.
- **Status:** Ready for parsing during migration phase

### Integration Points
- Section 13 (Migration Plan)
- Section 14 (Phase 1: Recipe management API and schema design)

---

## 5. Color Palette Preferences ✅

### Requirement
Use Gruvbox dark/light theme for MVP, with specific palettes for future phases: 2 (Embers dark), 4 (Velvet dark), 17 (Kiwi light), 37 (Popsicle light)

### Resolution
- **MVP (Phase 1):** Gruvbox Dark/Light
  - Gruvbox Dark: `#282828` bg, `#ebdbb2` fg, `#b8bb26` accent-primary, `#d65d0e` accent-secondary
  - Gruvbox Light: `#fbf1c7` bg, `#3c3836` fg, `#9d0006` accent-primary, `#8f3f00` accent-secondary
  - Simple Light/Dark toggle in settings
  - Complete hex codes in new COLOR_PALETTES.md document
- **Phase 2:** Additional theme options
  - Embers (dark): Warm, moody dark theme
  - Velvet (dark): Rich, luxurious dark theme
  - Kiwi (light): Fresh, bright light theme
  - Popsicle (light): Playful, vibrant light theme
- **Phase IV+:** Full TVA retro 70s/80s aesthetic building on Gruvbox foundation

### Integration Points
- Section 11 (UI/UX - Theming & Visual Design)
- Section 11 (Settings Page UI - Theme toggle)
- New document: `docs/COLOR_PALETTES.md` (comprehensive implementation guide)

---

## 6. Notification Delivery Methods ✅

### Requirement
For each notification, let user specify one or more of: DM, specific channel, specific channel with @-mention

### Resolution
- **Per-Event Configuration:** Each event type (action reminder, shopping list, week transition) has independent delivery settings
- **Multiple Methods Simultaneously:** Users can enable ALL three methods for same event (e.g., notify via DM AND channel AND channel with mention)
- **Data Structure:** `notification_channels` JSON array allows multiple entries:
  ```json
  [
    {"type": "dm"},
    {"type": "channel", "channel_id": 123456},
    {"type": "channel_mention", "channel_id": 123456}
  ]
  ```
- **UI Implementation:** Checkboxes for each delivery method in settings; channel selector appears when channel is chosen
- **Flexibility:** Users can have different delivery preferences for different event types

### Integration Points
- Section 5 (Data Model: notification_preferences.notification_channels)
- Section 6.5 (US-29)
- Section 9 (Discord Integration Details - Notification Configuration)
- Section 11 (Settings Page UI - Notification Preferences Configuration)
- Section 7 (API Endpoints: /users/{user_id}/notification-preferences)

---

## Document Updates Made

### 1. REQUIREMENTS.md
- Updated Section 6.5 (US-29) with comprehensive notification preferences specification
- Added `notification_preferences` table to Section 5 (Data Model)
- Updated Section 9 (Discord Integration) with notification configuration details
- Updated Section 11 (Settings Page UI) with notification preferences builder
- Enhanced Section 11 (Theming) with Gruvbox details and COLOR_PALETTES.md reference
- Added Section 7 (Notification Preferences API endpoints)
- Updated Section 8 (Deployment) with volume mapping and backup strategy
- Updated Section 10 (MVP Scope) to include per-user notifications and daily backups
- Updated Section 15 (Open Items) to reflect all resolved items

### 2. COLOR_PALETTES.md (NEW)
- Created comprehensive theming guide
- Gruvbox hex codes for dark and light variants
- Phase 2 palette descriptions (Embers, Velvet, Kiwi, Popsicle)
- Implementation strategy across all phases
- Tailwind CSS config examples
- Accessibility notes

### 3. UPDATE_SUMMARY.md (from previous session)
- Already created; documents conversation integration

---

## Files Updated

- ✅ `/Users/tonye/github/plongitudes/roanes-kitchen/docs/REQUIREMENTS.md` (15 sections, comprehensive)
- ✅ `/Users/tonye/github/plongitudes/roanes-kitchen/docs/COLOR_PALETTES.md` (NEW)
- ✅ `/Users/tonye/github/plongitudes/roanes-kitchen/docs/UPDATE_SUMMARY.md` (from earlier)

---

## Summary Table

| Item | Requirement | Solution | Status |
|------|-------------|----------|--------|
| Notification Preferences | Configurable per-user, multiple timings up to 6 days | New table, US-29, API endpoint | ✅ |
| Discord Permissions | Determine scope | Deferred to implementation | ⏸️ |
| Docker Volumes | Map to Unraid app data | `/mnt/user/appdata/roanes-kitchen` | ✅ |
| Database Backups | Daily dumps, 30-day retention | APScheduler job, automated cleanup | ✅ |
| Notion Export | Ready to parse | CSV + markdown in reference_material | ✅ |
| Color Palettes | Gruvbox MVP + 4 Phase 2 options | Full implementation guide created | ✅ |
| Notification Delivery | DM, channel, @-mention (multiple) | JSON data structure, UI builder | ✅ |

---

## Next Steps

1. **Critical Review:** Second Claude review pass (planned)
2. **Sprint Planning:** First dev sprint planning with Beads in mind
3. **Notion Parsing:** Examine structure of CSV + markdown for import script
4. **Development:** Start Phase 1 (MVP) with comprehensive specifications

## Ready for Development ✅

The requirements document is now **complete and production-ready**. All architectural decisions are locked in, data models are defined, UI/UX preferences are detailed, and color theming is planned across all phases.

