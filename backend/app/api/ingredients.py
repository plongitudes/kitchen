from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.ingredient_service import IngredientService
from app.schemas.ingredient import (
    CommonIngredientResponse,
    CommonIngredientDetailResponse,
    CommonIngredientCreate,
    CommonIngredientUpdate,
    UnmappedIngredient,
    MapIngredientRequest,
    MergeIngredientsRequest,
    CreateMappingRequest,
)

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=List[CommonIngredientResponse])
async def list_ingredients(
    search: Optional[str] = Query(None, description="Search by ingredient name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of all common ingredients with recipe counts."""
    ingredients = await IngredientService.get_all_ingredients(
        db=db,
        search=search,
        category=category,
    )

    # Enrich with recipe counts and recipe lists
    response = []
    for ingredient in ingredients:
        recipe_count = await IngredientService.get_recipe_count(db, ingredient.id)
        recipes = await IngredientService.get_recipes_for_ingredient(db, ingredient.id)
        ingredient_dict = {
            "id": ingredient.id,
            "name": ingredient.name,
            "category": ingredient.category,
            "created_at": ingredient.created_at,
            "updated_at": ingredient.updated_at,
            "recipe_count": recipe_count,
            "recipes": [{"id": r.id, "name": r.name} for r in recipes],
        }
        response.append(CommonIngredientResponse(**ingredient_dict))

    return response


@router.get("/unmapped", response_model=List[UnmappedIngredient])
async def list_unmapped_ingredients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of recipe ingredients with no common ingredient mapping."""
    unmapped = await IngredientService.get_unmapped_ingredients(db=db)
    return unmapped


@router.get("/unmapped/{ingredient_name}/recipes")
async def get_recipes_for_unmapped(
    ingredient_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recipes that use a specific unmapped ingredient."""
    recipes = await IngredientService.get_recipes_for_unmapped_ingredient(
        db=db,
        ingredient_name=ingredient_name,
    )
    return recipes


@router.get("/{ingredient_id}", response_model=CommonIngredientDetailResponse)
async def get_ingredient(
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a common ingredient with aliases and recipe count."""
    ingredient = await IngredientService.get_ingredient_by_id(db, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )

    # Add recipe count
    recipe_count = await IngredientService.get_recipe_count(db, ingredient.id)

    # Build response
    ingredient_dict = {
        "id": ingredient.id,
        "name": ingredient.name,
        "category": ingredient.category,
        "created_at": ingredient.created_at,
        "updated_at": ingredient.updated_at,
        "recipe_count": recipe_count,
        "aliases": ingredient.aliases,
    }

    return CommonIngredientDetailResponse(**ingredient_dict)


@router.post("", response_model=CommonIngredientDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    ingredient_data: CommonIngredientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new common ingredient."""
    ingredient = await IngredientService.create_ingredient(db, ingredient_data)

    # Reload with aliases
    ingredient = await IngredientService.get_ingredient_by_id(db, ingredient.id)
    recipe_count = await IngredientService.get_recipe_count(db, ingredient.id)

    ingredient_dict = {
        "id": ingredient.id,
        "name": ingredient.name,
        "category": ingredient.category,
        "created_at": ingredient.created_at,
        "updated_at": ingredient.updated_at,
        "recipe_count": recipe_count,
        "aliases": ingredient.aliases,
    }

    return CommonIngredientDetailResponse(**ingredient_dict)


@router.put("/{ingredient_id}", response_model=CommonIngredientDetailResponse)
async def update_ingredient(
    ingredient_id: UUID,
    ingredient_data: CommonIngredientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a common ingredient."""
    ingredient = await IngredientService.update_ingredient(db, ingredient_id, ingredient_data)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )

    # Reload with aliases
    ingredient = await IngredientService.get_ingredient_by_id(db, ingredient.id)
    recipe_count = await IngredientService.get_recipe_count(db, ingredient.id)

    ingredient_dict = {
        "id": ingredient.id,
        "name": ingredient.name,
        "category": ingredient.category,
        "created_at": ingredient.created_at,
        "updated_at": ingredient.updated_at,
        "recipe_count": recipe_count,
        "aliases": ingredient.aliases,
    }

    return CommonIngredientDetailResponse(**ingredient_dict)


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a common ingredient (only if not in use)."""
    success = await IngredientService.delete_ingredient(db, ingredient_id)
    if not success:
        # Check if it doesn't exist or is in use
        ingredient = await IngredientService.get_ingredient_by_id(db, ingredient_id)
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient not found",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete ingredient that is used in recipes",
            )

    return None


@router.delete("/{ingredient_id}/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alias(
    ingredient_id: UUID,
    alias_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an alias from a common ingredient."""
    success = await IngredientService.delete_alias(db, ingredient_id, alias_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alias not found",
        )
    return None


@router.post("/map", status_code=status.HTTP_200_OK)
async def map_ingredient(
    mapping_data: MapIngredientRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Map an ingredient name to a common ingredient."""
    try:
        count = await IngredientService.map_ingredient(
            db=db,
            ingredient_name=mapping_data.ingredient_name,
            common_ingredient_id=mapping_data.common_ingredient_id,
        )
        return {
            "message": f"Successfully mapped '{mapping_data.ingredient_name}' to common ingredient",
            "recipes_updated": count,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/create-with-mapping", response_model=CommonIngredientDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient_with_mapping(
    mapping_data: CreateMappingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new common ingredient and map an initial alias."""
    ingredient = await IngredientService.create_ingredient_with_mapping(db, mapping_data)

    # Reload with aliases
    ingredient = await IngredientService.get_ingredient_by_id(db, ingredient.id)
    recipe_count = await IngredientService.get_recipe_count(db, ingredient.id)

    ingredient_dict = {
        "id": ingredient.id,
        "name": ingredient.name,
        "category": ingredient.category,
        "created_at": ingredient.created_at,
        "updated_at": ingredient.updated_at,
        "recipe_count": recipe_count,
        "aliases": ingredient.aliases,
    }

    return CommonIngredientDetailResponse(**ingredient_dict)


@router.post("/merge", status_code=status.HTTP_200_OK)
async def merge_ingredients(
    merge_data: MergeIngredientsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Merge multiple common ingredients into one."""
    try:
        count = await IngredientService.merge_ingredients(
            db=db,
            source_ingredient_ids=merge_data.source_ingredient_ids,
            target_ingredient_id=merge_data.target_ingredient_id,
        )
        return {
            "message": "Successfully merged ingredients",
            "recipes_updated": count,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/auto-map", status_code=status.HTTP_200_OK)
async def auto_map_common_ingredients(
    min_recipe_count: int = Query(2, description="Minimum recipe count to auto-map"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Auto-create common ingredients for unmapped ingredients used in multiple recipes."""
    result = await IngredientService.auto_map_common_ingredients(
        db=db,
        min_recipe_count=min_recipe_count,
    )
    return {
        "message": f"Auto-mapped {result['ingredients_created']} ingredients",
        "ingredients_created": result["ingredients_created"],
        "recipe_ingredients_updated": result["recipe_ingredients_updated"],
    }
