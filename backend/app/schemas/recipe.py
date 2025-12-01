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
    prep_note: Optional[str] = None

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
    prep_note: Optional[str] = None

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
# Prep Step Schemas
# ============================================================================


class PrepStepIngredientBase(BaseModel):
    """Base schema for linking prep steps to ingredients."""

    recipe_ingredient_id: UUID


class PrepStepIngredientCreate(PrepStepIngredientBase):
    """Schema for creating a prep step ingredient link."""

    pass


class PrepStepIngredientResponse(PrepStepIngredientBase):
    """Schema for prep step ingredient link response."""

    id: UUID

    class Config:
        from_attributes = True


class RecipePrepStepBase(BaseModel):
    """Base schema for recipe prep steps."""

    description: str = Field(..., min_length=1)
    order: int = Field(..., ge=0)


class RecipePrepStepCreate(RecipePrepStepBase):
    """Schema for creating a recipe prep step.

    Use ingredient_ids when adding to an existing recipe (you know the UUIDs).
    Use ingredient_orders when creating with a new recipe (references by position).
    """

    ingredient_ids: List[UUID] = []  # For existing recipes - actual ingredient UUIDs
    ingredient_orders: List[int] = []  # For new recipes - ingredient positions (0-indexed)


class RecipePrepStepUpdate(BaseModel):
    """Schema for updating a recipe prep step."""

    description: Optional[str] = Field(None, min_length=1)
    order: Optional[int] = Field(None, ge=0)
    ingredient_ids: Optional[List[UUID]] = None  # Replace linked ingredients


class RecipePrepStepResponse(BaseModel):
    """Schema for recipe prep step response."""

    id: UUID
    recipe_id: UUID
    description: str
    order: int
    ingredient_ids: List[UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, prep_step) -> "RecipePrepStepResponse":
        """Convert from SQLAlchemy model to response schema."""
        return cls(
            id=prep_step.id,
            recipe_id=prep_step.recipe_id,
            description=prep_step.description,
            order=prep_step.order,
            ingredient_ids=[link.recipe_ingredient_id for link in prep_step.ingredient_links],
            created_at=prep_step.created_at,
        )


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
    """Schema for creating a recipe with ingredients, instructions, and prep steps."""

    ingredients: Optional[List[RecipeIngredientCreate]] = []
    instructions: Optional[List[RecipeInstructionCreate]] = []
    prep_steps: Optional[List[RecipePrepStepCreate]] = []


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
    prep_steps: Optional[List[RecipePrepStepCreate]] = None


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
    """Schema for detailed recipe response with ingredients, instructions, and prep steps."""

    ingredients: List[RecipeIngredientResponse] = []
    instructions: List[RecipeInstructionResponse] = []
    prep_steps: List[RecipePrepStepResponse] = []

    class Config:
        from_attributes = True

    @field_validator("prep_steps", mode="before")
    @classmethod
    def convert_prep_steps(cls, v):
        """Convert prep_steps from model format (with ingredient_links) to response format."""
        if not v:
            return []
        # If already RecipePrepStepResponse objects, return as-is
        if v and isinstance(v[0], RecipePrepStepResponse):
            return v
        # Convert from model objects
        result = []
        for ps in v:
            if hasattr(ps, "ingredient_links"):
                result.append(RecipePrepStepResponse(
                    id=ps.id,
                    recipe_id=ps.recipe_id,
                    description=ps.description,
                    order=ps.order,
                    ingredient_ids=[link.recipe_ingredient_id for link in ps.ingredient_links],
                    created_at=ps.created_at,
                ))
            else:
                result.append(ps)
        return result


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
