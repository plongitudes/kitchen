from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
import json

from app.schemas.schedule import WeekDayAssignmentResponse, WeekTemplateResponse


# ============================================================================
# Meal Assignment Schemas
# ============================================================================


class MealAssignmentBase(BaseModel):
    """Base schema for meal assignments."""

    day_of_week: int = Field(..., ge=0, le=6)
    assigned_user_id: UUID
    action: str = Field(..., min_length=1)
    recipe_id: Optional[UUID] = None
    order: int = Field(default=0, ge=0)


class MealAssignmentCreate(MealAssignmentBase):
    """Schema for creating a meal assignment."""

    pass


class MealAssignmentUpdate(BaseModel):
    """Schema for updating a meal assignment."""

    assigned_user_id: Optional[UUID] = None
    action: Optional[str] = Field(None, min_length=1)
    recipe_id: Optional[UUID] = None
    order: Optional[int] = Field(None, ge=0)


class MealAssignmentResponse(MealAssignmentBase):
    """Schema for meal assignment response."""

    id: UUID
    meal_plan_instance_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Meal Plan Instance Schemas
# ============================================================================


class MealPlanInstanceBase(BaseModel):
    """Base schema for meal plan instances."""

    instance_start_date: date


class MealPlanInstanceResponse(MealPlanInstanceBase):
    """Schema for meal plan instance response."""

    id: UUID
    sequence_id: Optional[UUID] = None
    week_template_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DayAssignmentWithDate(BaseModel):
    """Assignment with calculated date for a specific day."""

    id: Optional[UUID] = None  # meal_assignment ID if this is a per-instance override
    date: date
    day_of_week: int
    assigned_user_id: UUID
    action: str
    recipe_id: Optional[UUID] = None
    recipe_name: Optional[str] = None
    order: int
    is_modified: bool = False  # True if this is a per-instance override


class MealPlanInstanceDetailResponse(MealPlanInstanceResponse):
    """Schema for detailed meal plan instance with assignments and dates."""

    theme_name: str
    week_number: int
    assignments: List[DayAssignmentWithDate] = []

    class Config:
        from_attributes = True


class AdvanceWeekRequest(BaseModel):
    """Schema for manually advancing to next week."""

    sequence_id: UUID


class AdvanceWeekResponse(BaseModel):
    """Schema for advance week response."""

    new_instance: MealPlanInstanceDetailResponse
    old_week_number: int
    new_week_number: int
    sequence_current_week_index: int


# ============================================================================
# Grocery List Schemas
# ============================================================================


class RecipeContribution(BaseModel):
    """Individual recipe's contribution to a grocery list item."""
    recipe_id: str
    recipe_name: Optional[str] = None
    quantity: float
    unit: str


class GroceryListItemResponse(BaseModel):
    """Schema for grocery list item response."""

    id: UUID
    ingredient_name: str
    total_quantity: float
    unit: str
    source_recipe_ids: List[str]  # JSON string from DB, parsed into list
    source_recipe_names: Optional[List[str]] = None  # Recipe names for display
    source_recipe_details: Optional[List[RecipeContribution]] = None  # Detailed contributions

    # Display-friendly quantities
    display_quantity: Optional[str] = None  # e.g., "1¼ cups"
    metric_equivalent: Optional[str] = None  # e.g., "300g"
    imperial_equivalent: Optional[str] = None  # e.g., "1¼ cups"

    @field_validator("source_recipe_ids", mode="before")
    @classmethod
    def parse_json_string(_cls, v):
        """Parse JSON string from database."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("source_recipe_details", mode="before")
    @classmethod
    def parse_recipe_details(_cls, v):
        """Parse JSON string from database."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class GroceryListBase(BaseModel):
    """Base schema for grocery lists."""

    shopping_date: date


class GroceryListResponse(GroceryListBase):
    """Schema for grocery list response."""

    id: UUID
    meal_plan_instance_id: UUID
    generated_at: datetime

    class Config:
        from_attributes = True


class GroceryListDetailResponse(GroceryListResponse):
    """Schema for detailed grocery list with items."""

    items: List[GroceryListItemResponse] = []

    class Config:
        from_attributes = True


class GenerateGroceryListRequest(BaseModel):
    """Schema for generating a grocery list."""

    shopping_date: date
