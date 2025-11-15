# API Migration Guide: Template Refactor

**Date:** November 7, 2025
**Impact:** Breaking changes to schedule/week endpoints

---

## Overview

The schedule weeks system was refactored to use reusable templates. All `/schedules/{id}/weeks/*` endpoints have been removed and replaced with `/templates/*` endpoints.

---

## Breaking Changes

### Removed Endpoints

The following endpoints **no longer exist**:

```
GET    /schedules/{sequence_id}/weeks
POST   /schedules/{sequence_id}/weeks
GET    /schedules/{sequence_id}/weeks/{week_id}
PUT    /schedules/{sequence_id}/weeks/{week_id}
DELETE /schedules/{sequence_id}/weeks/{week_id}
POST   /schedules/{sequence_id}/weeks/{week_id}/restore
POST   /schedules/{sequence_id}/weeks/reorder
GET    /schedules/{sequence_id}/current-week
GET    /schedules/{sequence_id}/weeks/{week_id}/assignments
POST   /schedules/{sequence_id}/weeks/{week_id}/assignments
PUT    /schedules/{sequence_id}/weeks/{week_id}/assignments/{day}
DELETE /schedules/{sequence_id}/weeks/{week_id}/assignments/{day}
```

---

## Migration Path

### 1. Template Management

**OLD:** Creating a week in a sequence
```http
POST /schedules/{sequence_id}/weeks
{
  "name": "Week 1",
  "order": 0
}
```

**NEW:** Create a template, then associate with sequence
```http
# Step 1: Create template
POST /templates
{
  "name": "Week 1"
}

# Step 2: Associate with sequence
POST /schedules/{sequence_id}/templates
{
  "template_id": "<uuid>",
  "order": 0
}
```

### 2. Template Retrieval

**OLD:** Get all weeks in a sequence
```http
GET /schedules/{sequence_id}/weeks
```

**NEW:** Get templates associated with a sequence
```http
GET /schedules/{sequence_id}/templates
```

### 3. Template Details

**OLD:** Get week details
```http
GET /schedules/{sequence_id}/weeks/{week_id}
```

**NEW:** Get template details directly
```http
GET /templates/{template_id}
```

### 4. Current Week/Template

**OLD:** Get current week
```http
GET /schedules/{sequence_id}/current-week
```

**NEW:** Get current template
```http
GET /schedules/{sequence_id}/current-template
```

**Response Schema Change:**
- OLD: Returns `ScheduleWeek` object
- NEW: Returns `WeekTemplate` object with same structure

### 5. Day Assignments

**OLD:** Manage assignments under week
```http
GET /schedules/{sequence_id}/weeks/{week_id}/assignments
PUT /schedules/{sequence_id}/weeks/{week_id}/assignments/{day}
```

**NEW:** Manage assignments directly on template
```http
GET /templates/{template_id}/assignments
PUT /templates/{template_id}/assignments/{day}
```

### 6. Template Updates

**OLD:** Update week
```http
PUT /schedules/{sequence_id}/weeks/{week_id}
{
  "name": "Updated Week 1"
}
```

**NEW:** Update template directly
```http
PUT /templates/{template_id}
{
  "name": "Updated Week 1"
}
```

### 7. Template Deletion (Retirement)

**OLD:** Retire/restore week
```http
DELETE /schedules/{sequence_id}/weeks/{week_id}
POST   /schedules/{sequence_id}/weeks/{week_id}/restore
```

**NEW:** Retire/restore template
```http
DELETE /templates/{template_id}
POST   /templates/{template_id}/restore
```

### 8. Reordering

**OLD:** Reorder weeks in sequence
```http
POST /schedules/{sequence_id}/weeks/reorder
{
  "week_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**NEW:** Reorder templates in sequence
```http
POST /schedules/{sequence_id}/templates/reorder
{
  "template_ids": ["uuid1", "uuid2", "uuid3"]
}
```

---

## Schema Changes

### Database Tables

**Renamed:**
- `schedule_weeks` → `week_templates`
- `week_day_assignments` → `template_day_assignments`

**New Junction Table:**
- `schedule_template_mappings` (links sequences to templates with order)

### Response Objects

**Renamed:**
- `ScheduleWeek` → `WeekTemplate`
- `ScheduleWeekCreate` → `WeekTemplateCreate`
- `ScheduleWeekUpdate` → `WeekTemplateUpdate`
- `ScheduleWeekResponse` → `WeekTemplateResponse`

**Field Changes:**
- `week_id` → `template_id` (in all contexts)
- `schedule_id` → removed from template responses (now in mapping)

---

## Frontend Migration Checklist

### Services Layer
- [ ] Update `scheduleService.js`:
  - Replace `getWeeks()` with `getTemplates()`
  - Replace `createWeek()` with `createTemplate()` + `associateTemplate()`
  - Replace `updateWeek()` with `updateTemplate()`
  - Replace `deleteWeek()` with `retireTemplate()`
  - Replace `getCurrentWeek()` with `getCurrentTemplate()`

### Components
- [ ] Update `ScheduleList.jsx`: Change week references to templates
- [ ] Update `ScheduleDetail.jsx`: Use new template endpoints
- [ ] Update `WeekAssignments.jsx`: Update assignment endpoints
- [ ] Update `MealPlanCurrent.jsx`: Use current-template endpoint

### State Management
- [ ] Update Redux/Context stores: Rename week → template in state
- [ ] Update action creators: Use new API endpoints
- [ ] Update reducers: Handle new response schemas

---

## Benefits of New System

1. **Template Reusability:** Templates can be shared across multiple sequences
2. **Cleaner Separation:** Templates are independent entities, not nested under sequences
3. **Flexible Ordering:** Same template can appear multiple times in different positions
4. **Easier Management:** Direct template CRUD without sequence context

---

## Questions?

For issues or questions about this migration:
1. Check existing frontend implementation in `/frontend/src/services/`
2. Review backend API code in `/backend/app/api/templates.py`
3. Open an issue with tag `migration-help`
