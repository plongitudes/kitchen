from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.recipe import IngredientUnit


# ============================================================================
# Ingredient Schemas
# ============================================================================


class RecipeIngredientBase(BaseModel):
    """Base schema for recipe ingredients."""

    ingredient_name: str = Field(..., min_length=1)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[IngredientUnit] = None
    order: int = Field(..., ge=0)

    @field_validator("unit", mode="before")
    @classmethod
    def validate_unit(_cls, v):
        """Convert string to IngredientUnit enum by value, not name."""
        if v is None or v == "":
            return None
        if isinstance(v, IngredientUnit):
            return v
        # Try to match by value (lowercase)
        for unit in IngredientUnit:
            if unit.value == v:
                return unit
        # If no match, let Pydantic handle the error
        return v


class RecipeIngredientCreate(RecipeIngredientBase):
    """Schema for creating a recipe ingredient."""

    pass


class RecipeIngredientUpdate(BaseModel):
    """Schema for updating a recipe ingredient."""

    ingredient_name: Optional[str] = Field(None, min_length=1)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[IngredientUnit] = None
    order: Optional[int] = Field(None, ge=0)

    @field_validator("unit", mode="before")
    @classmethod
    def validate_unit(_cls, v):
        """Convert string to IngredientUnit enum by value, not name."""
        if v is None or v == "":
            return None
        if isinstance(v, IngredientUnit):
            return v
        # Try to match by value (lowercase)
        for unit in IngredientUnit:
            if unit.value == v:
                return unit
        # If no match, let Pydantic handle the error
        return v


class RecipeIngredientResponse(RecipeIngredientBase):
    """Schema for recipe ingredient response."""

    id: UUID
    recipe_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Instruction Schemas
# ============================================================================


class RecipeInstructionBase(BaseModel):
    """Base schema for recipe instructions."""

    step_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    duration_minutes: Optional[int] = Field(None, ge=0)


class RecipeInstructionCreate(RecipeInstructionBase):
    """Schema for creating a recipe instruction."""

    pass


class RecipeInstructionUpdate(BaseModel):
    """Schema for updating a recipe instruction."""

    step_number: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, min_length=1)
    duration_minutes: Optional[int] = Field(None, ge=0)


class RecipeInstructionResponse(RecipeInstructionBase):
    """Schema for recipe instruction response."""

    id: UUID
    recipe_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Recipe Schemas
# ============================================================================


class RecipeBase(BaseModel):
    """Base schema for recipes."""

    name: str = Field(..., min_length=1)
    recipe_type: Optional[str] = None
    description: Optional[str] = None
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    prep_notes: Optional[str] = None
    postmortem_notes: Optional[str] = None
    source_url: Optional[str] = None


class RecipeCreate(RecipeBase):
    """Schema for creating a recipe with ingredients and instructions."""

    ingredients: Optional[List[RecipeIngredientCreate]] = []
    instructions: Optional[List[RecipeInstructionCreate]] = []


class RecipeUpdate(BaseModel):
    """Schema for updating a recipe."""

    name: Optional[str] = Field(None, min_length=1)
    recipe_type: Optional[str] = None
    description: Optional[str] = None
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    prep_notes: Optional[str] = None
    postmortem_notes: Optional[str] = None
    source_url: Optional[str] = None
    owner_id: Optional[UUID] = None  # For owner reassignment
    ingredients: Optional[List[RecipeIngredientCreate]] = None
    instructions: Optional[List[RecipeInstructionCreate]] = None


class RecipeResponse(RecipeBase):
    """Schema for recipe response."""

    id: UUID
    owner_id: UUID
    retired_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipeDetailResponse(RecipeResponse):
    """Schema for detailed recipe response with ingredients and instructions."""

    ingredients: List[RecipeIngredientResponse] = []
    instructions: List[RecipeInstructionResponse] = []

    class Config:
        from_attributes = True


class RecipeUsageResponse(BaseModel):
    """Schema for recipe usage in week templates."""

    is_used: bool
    templates: List[dict]  # List of {week_id, theme_name, day_of_week}


class RecipeListFilters(BaseModel):
    """Query parameters for filtering recipe list."""

    owner_id: Optional[UUID] = None
    include_retired: bool = False
    recipe_type: Optional[str] = None


# ============================================================================
# Recipe Import Schemas
# ============================================================================


class RecipeImportRequest(BaseModel):
    """Schema for importing a recipe from a URL."""

    url: HttpUrl


class RecipeImportPreviewIngredient(BaseModel):
    """Parsed ingredient for import preview."""

    ingredient_name: str
    quantity: float
    unit: Optional[IngredientUnit] = None


class RecipeImportPreviewInstruction(BaseModel):
    """Parsed instruction for import preview."""

    step_number: int
    description: str


class RecipeImportPreviewResponse(BaseModel):
    """Preview of scraped recipe data before saving."""

    name: str
    recipe_type: str = "dinner"  # Default
    description: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    source_url: str
    ingredients: List[RecipeImportPreviewIngredient]
    instructions: List[RecipeImportPreviewInstruction]
