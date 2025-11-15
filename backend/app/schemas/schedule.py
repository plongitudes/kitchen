from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# Week Day Assignment Schemas
# ============================================================================


class WeekDayAssignmentBase(BaseModel):
    """Base schema for week day assignments."""

    day_of_week: int = Field(..., ge=0, le=6)  # 0=Sunday, 6=Saturday
    assigned_user_id: UUID
    action: str = Field(..., min_length=1)  # e.g., cook, shop, takeout, rest
    recipe_id: Optional[UUID] = None  # Null for non-cook actions
    order: int = Field(default=0, ge=0)  # For multiple actions per day


class WeekDayAssignmentCreate(WeekDayAssignmentBase):
    """Schema for creating a week day assignment."""

    pass


class WeekDayAssignmentUpdate(BaseModel):
    """Schema for updating a week day assignment."""

    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    assigned_user_id: Optional[UUID] = None
    action: Optional[str] = Field(None, min_length=1)
    recipe_id: Optional[UUID] = None
    order: Optional[int] = Field(None, ge=0)


class WeekDayAssignmentResponse(WeekDayAssignmentBase):
    """Schema for week day assignment response."""

    id: UUID
    week_template_id: UUID
    recipe_name: Optional[str] = None  # Populated from Recipe relationship
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Week Template Schemas (independent, reusable)
# ============================================================================


class WeekTemplateBase(BaseModel):
    """Base schema for week templates."""

    name: str = Field(..., min_length=1)


class WeekTemplateCreate(WeekTemplateBase):
    """Schema for creating a week template."""

    assignments: Optional[List[WeekDayAssignmentCreate]] = []


class WeekTemplateUpdate(BaseModel):
    """Schema for updating a week template."""

    name: Optional[str] = Field(None, min_length=1)
    assignments: Optional[List[WeekDayAssignmentCreate]] = None


class WeekTemplateResponse(WeekTemplateBase):
    """Schema for week template response."""

    id: UUID
    retired_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WeekTemplateDetailResponse(WeekTemplateResponse):
    """Schema for detailed week template response with assignments."""

    day_assignments: List[WeekDayAssignmentResponse] = []

    class Config:
        from_attributes = True


class WeekTemplateForkRequest(BaseModel):
    """Schema for forking a week template."""

    new_name: Optional[str] = None  # If not provided, will be "Fork of [original name]"


# ============================================================================
# Sequence Week Mapping Schemas (join table)
# ============================================================================


class SequenceWeekMappingBase(BaseModel):
    """Base schema for sequence-week mappings."""

    week_template_id: UUID
    position: Optional[int] = Field(
        None,
        ge=1,
        description="Position in sequence (1-indexed). If omitted, template is added to the end.",
    )


class SequenceWeekMappingCreate(SequenceWeekMappingBase):
    """Schema for adding a template to a sequence."""

    pass


class SequenceWeekMappingResponse(SequenceWeekMappingBase):
    """Schema for sequence-week mapping response."""

    id: UUID
    sequence_id: UUID
    removed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SequenceWeekMappingDetailResponse(SequenceWeekMappingResponse):
    """Schema for detailed mapping with template info."""

    week_template: WeekTemplateResponse

    class Config:
        from_attributes = True


# ============================================================================
# Schedule Sequence Schemas
# ============================================================================


class ScheduleSequenceBase(BaseModel):
    """Base schema for schedule sequences."""

    name: str = Field(..., min_length=1)
    advancement_day_of_week: int = Field(..., ge=0, le=6)  # 0=Sunday, 6=Saturday
    advancement_time: str = Field(
        ..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$"
    )  # HH:MM format

    @field_validator("advancement_time")
    @classmethod
    def validate_time_format(_cls, v: str) -> str:
        """Validate time is in HH:MM format."""
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Time must be in HH:MM format")
        hours, minutes = int(parts[0]), int(parts[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Invalid time value")
        return v


class ScheduleSequenceCreate(ScheduleSequenceBase):
    """Schema for creating a schedule sequence."""

    pass


class ScheduleSequenceUpdate(BaseModel):
    """Schema for updating a schedule sequence."""

    name: Optional[str] = Field(None, min_length=1)
    advancement_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    advancement_time: Optional[str] = Field(
        None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$"
    )

    @field_validator("advancement_time")
    @classmethod
    def validate_time_format(_cls, v: Optional[str]) -> Optional[str]:
        """Validate time is in HH:MM format."""
        if v is None:
            return v
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Time must be in HH:MM format")
        hours, minutes = int(parts[0]), int(parts[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Invalid time value")
        return v


class ScheduleSequenceResponse(ScheduleSequenceBase):
    """Schema for schedule sequence response."""

    id: UUID
    current_week_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleSequenceDetailResponse(ScheduleSequenceResponse):
    """Schema for detailed schedule sequence response with template mappings."""

    week_mappings: List[SequenceWeekMappingDetailResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# Utility Schemas
# ============================================================================


class TemplateReorderRequest(BaseModel):
    """Schema for reordering templates in a sequence."""

    template_ids: List[UUID] = Field(..., min_length=1)


class StartScheduleRequest(BaseModel):
    """Schema for starting a schedule on an arbitrary week."""

    week_template_id: UUID = Field(..., description="The template to start with")
    position: int = Field(
        ..., ge=1, description="Position of the template in the sequence (1-indexed)"
    )
