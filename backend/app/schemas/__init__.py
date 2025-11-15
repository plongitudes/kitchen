"""Pydantic schemas for API request/response validation."""

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
)
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeDetailResponse,
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
    RecipeIngredientResponse,
    RecipeInstructionCreate,
    RecipeInstructionUpdate,
    RecipeInstructionResponse,
    RecipeUsageResponse,
    RecipeListFilters,
)
from app.schemas.schedule import (
    ScheduleSequenceCreate,
    ScheduleSequenceUpdate,
    ScheduleSequenceResponse,
    ScheduleSequenceDetailResponse,
    WeekTemplateCreate,
    WeekTemplateUpdate,
    WeekTemplateResponse,
    WeekTemplateDetailResponse,
    WeekTemplateForkRequest,
    WeekDayAssignmentCreate,
    WeekDayAssignmentUpdate,
    WeekDayAssignmentResponse,
    TemplateReorderRequest,
    SequenceWeekMappingCreate,
    SequenceWeekMappingResponse,
)
from app.schemas.meal_plan import (
    MealPlanInstanceResponse,
    MealPlanInstanceDetailResponse,
    DayAssignmentWithDate,
    AdvanceWeekRequest,
    AdvanceWeekResponse,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "Token",
    # Recipe schemas
    "RecipeCreate",
    "RecipeUpdate",
    "RecipeResponse",
    "RecipeDetailResponse",
    "RecipeIngredientCreate",
    "RecipeIngredientUpdate",
    "RecipeIngredientResponse",
    "RecipeInstructionCreate",
    "RecipeInstructionUpdate",
    "RecipeInstructionResponse",
    "RecipeUsageResponse",
    "RecipeListFilters",
    # Schedule schemas
    "ScheduleSequenceCreate",
    "ScheduleSequenceUpdate",
    "ScheduleSequenceResponse",
    "ScheduleSequenceDetailResponse",
    "WeekTemplateCreate",
    "WeekTemplateUpdate",
    "WeekTemplateResponse",
    "WeekTemplateDetailResponse",
    "WeekTemplateForkRequest",
    "WeekDayAssignmentCreate",
    "WeekDayAssignmentUpdate",
    "WeekDayAssignmentResponse",
    "TemplateReorderRequest",
    "SequenceWeekMappingCreate",
    "SequenceWeekMappingResponse",
    # Meal plan schemas
    "MealPlanInstanceResponse",
    "MealPlanInstanceDetailResponse",
    "DayAssignmentWithDate",
    "AdvanceWeekRequest",
    "AdvanceWeekResponse",
]
