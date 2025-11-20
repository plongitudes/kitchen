from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class IngredientAliasBase(BaseModel):
    """Base schema for ingredient alias."""

    alias: str


class IngredientAliasResponse(IngredientAliasBase):
    """Response schema for ingredient alias."""

    id: UUID
    common_ingredient_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommonIngredientBase(BaseModel):
    """Base schema for common ingredient."""

    name: str
    category: Optional[str] = None


class CommonIngredientCreate(CommonIngredientBase):
    """Schema for creating a common ingredient."""

    pass


class CommonIngredientUpdate(BaseModel):
    """Schema for updating a common ingredient."""

    name: Optional[str] = None
    category: Optional[str] = None


class RecipeReference(BaseModel):
    """Minimal recipe info for ingredient lists."""

    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class CommonIngredientResponse(CommonIngredientBase):
    """Response schema for common ingredient."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    recipe_count: Optional[int] = 0  # Number of recipes using this ingredient
    recipes: Optional[List[RecipeReference]] = []  # List of recipes using this ingredient

    model_config = ConfigDict(from_attributes=True)


class CommonIngredientDetailResponse(CommonIngredientResponse):
    """Detailed response schema for common ingredient with aliases."""

    aliases: List[IngredientAliasResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UnmappedIngredient(BaseModel):
    """Schema for unmapped recipe ingredient."""

    ingredient_name: str
    recipe_count: int
    recipes: Optional[List[RecipeReference]] = []


class MapIngredientRequest(BaseModel):
    """Schema for mapping an ingredient name to a common ingredient."""

    ingredient_name: str
    common_ingredient_id: UUID


class MergeIngredientsRequest(BaseModel):
    """Schema for merging multiple common ingredients into one."""

    source_ingredient_ids: List[UUID]  # Ingredients to merge from
    target_ingredient_id: UUID  # Ingredient to merge into


class CreateMappingRequest(BaseModel):
    """Schema for creating a new common ingredient with initial alias."""

    name: str
    category: Optional[str] = None
    initial_alias: str  # The unmapped ingredient name to map
