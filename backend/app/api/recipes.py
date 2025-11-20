"""
Recipe API endpoints.

Handles CRUD operations for recipes, ingredients, and instructions.
Includes recipe import/scraping functionality and usage tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import json
import io

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.recipe_service import RecipeService
from app.schemas.recipe import (
    RecipeResponse,
    RecipeDetailResponse,
    RecipeCreate,
    RecipeUpdate,
    RecipeUsageResponse,
    RecipeIngredientResponse,
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
    RecipeInstructionResponse,
    RecipeInstructionCreate,
    RecipeInstructionUpdate,
    RecipeImportRequest,
    RecipeImportPreviewResponse,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


# ============================================================================
# Recipe Endpoints
# ============================================================================


@router.get("", response_model=List[RecipeResponse])
async def list_recipes(
    owner_id: Optional[UUID] = Query(None, description="Filter by owner"),
    include_retired: bool = Query(False, description="Include retired recipes"),
    recipe_type: Optional[str] = Query(None, description="Filter by recipe type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of recipes with optional filtering.

    Args:
        owner_id: Optional UUID to filter recipes by owner
        include_retired: Include soft-deleted recipes in results
        recipe_type: Filter by recipe type (e.g., "dinner", "breakfast")
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        List of Recipe objects matching the filters
    """
    recipes = await RecipeService.get_recipes(
        db=db,
        owner_id=owner_id,
        include_retired=include_retired,
        recipe_type=recipe_type,
    )
    return recipes


@router.post("/import-preview", response_model=RecipeImportPreviewResponse)
async def import_recipe_preview(
    import_data: RecipeImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import and preview a recipe from a URL without saving to database.

    Scrapes recipe data from 550+ supported cooking websites using recipe-scrapers
    library. Returns parsed data for preview before committing to database.

    Args:
        import_data: Request containing recipe URL to scrape
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        RecipeImportPreviewResponse with scraped recipe data

    Raises:
        HTTPException: 400 if website not supported, 500 if scraping fails
    """
    preview = await RecipeService.import_recipe_preview(
        url=str(import_data.url),
    )
    return preview


@router.get("/export-all")
async def export_all_recipes_json(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all recipes as a single JSON file."""
    recipes = await RecipeService.get_recipes(
        db=db, owner_id=current_user.id, include_retired=False
    )

    # Build export data for all recipes
    export_data = {
        "recipes": [
            {
                "name": recipe.name,
                "recipe_type": recipe.recipe_type,
                "description": recipe.description,
                "prep_time_minutes": recipe.prep_time_minutes,
                "cook_time_minutes": recipe.cook_time_minutes,
                "prep_notes": recipe.prep_notes,
                "postmortem_notes": recipe.postmortem_notes,
                "source_url": recipe.source_url,
                "ingredients": [
                    {
                        "ingredient_name": ing.ingredient_name,
                        "quantity": ing.quantity,
                        "unit": ing.unit,
                        "order": ing.order,
                        "prep_note": ing.prep_note,
                    }
                    for ing in sorted(recipe.ingredients, key=lambda x: x.order)
                ],
                "instructions": [
                    {
                        "step_number": inst.step_number,
                        "description": inst.description,
                        "duration_minutes": inst.duration_minutes,
                    }
                    for inst in sorted(recipe.instructions, key=lambda x: x.step_number)
                ],
            }
            for recipe in recipes
        ]
    }

    # Create JSON file in memory
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="all_recipes.json"'}
    )


@router.post("/import-json")
async def import_recipe_json(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import a recipe from JSON file."""
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .json files are allowed"
        )

    try:
        # Read and parse JSON
        content = await file.read()
        recipe_data = json.loads(content.decode('utf-8'))

        # Validate required fields
        required_fields = ["name", "ingredients", "instructions"]
        for field in required_fields:
            if field not in recipe_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )

        # Create recipe
        create_data = RecipeCreate(
            name=recipe_data["name"],
            recipe_type=recipe_data.get("recipe_type"),
            description=recipe_data.get("description"),
            prep_time_minutes=recipe_data.get("prep_time_minutes"),
            cook_time_minutes=recipe_data.get("cook_time_minutes"),
            prep_notes=recipe_data.get("prep_notes"),
            postmortem_notes=recipe_data.get("postmortem_notes"),
            source_url=recipe_data.get("source_url"),
            ingredients=[
                RecipeIngredientCreate(**ing) for ing in recipe_data["ingredients"]
            ],
            instructions=[
                RecipeInstructionCreate(**inst) for inst in recipe_data["instructions"]
            ],
        )

        recipe = await RecipeService.create_recipe(
            db=db, recipe_data=create_data, owner_id=current_user.id
        )

        return {
            "message": f"Recipe '{recipe.name}' imported successfully",
            "recipe_id": str(recipe.id),
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/import-multiple-json")
async def import_multiple_recipes_json(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import multiple recipes from a JSON file."""
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .json files are allowed"
        )

    try:
        # Read and parse JSON
        content = await file.read()
        data = json.loads(content.decode('utf-8'))

        # Check if it's a bulk import (has "recipes" array)
        if "recipes" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format: expected 'recipes' array"
            )

        recipes_data = data["recipes"]
        imported_count = 0
        failed_count = 0
        errors = []

        for idx, recipe_data in enumerate(recipes_data):
            try:
                # Validate required fields
                required_fields = ["name", "ingredients", "instructions"]
                for field in required_fields:
                    if field not in recipe_data:
                        raise ValueError(f"Missing required field: {field}")

                # Create recipe
                create_data = RecipeCreate(
                    name=recipe_data["name"],
                    recipe_type=recipe_data.get("recipe_type"),
                    description=recipe_data.get("description"),
                    prep_time_minutes=recipe_data.get("prep_time_minutes"),
                    cook_time_minutes=recipe_data.get("cook_time_minutes"),
                    prep_notes=recipe_data.get("prep_notes"),
                    postmortem_notes=recipe_data.get("postmortem_notes"),
                    source_url=recipe_data.get("source_url"),
                    ingredients=[
                        RecipeIngredientCreate(**ing) for ing in recipe_data["ingredients"]
                    ],
                    instructions=[
                        RecipeInstructionCreate(**inst) for inst in recipe_data["instructions"]
                    ],
                )

                await RecipeService.create_recipe(
                    db=db, recipe_data=create_data, owner_id=current_user.id
                )
                imported_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(f"Recipe {idx + 1} ('{recipe_data.get('name', 'unknown')}'): {str(e)}")

        result_message = f"Imported {imported_count} recipe(s)"
        if failed_count > 0:
            result_message += f", {failed_count} failed"

        return {
            "message": result_message,
            "imported": imported_count,
            "failed": failed_count,
            "errors": errors if errors else None,
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/{recipe_id}/reimport", response_model=RecipeDetailResponse)
async def reimport_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-import recipe from its source URL, updating ingredients and instructions.

    Fetches fresh data from the recipe's source_url and updates the recipe.
    Preserves user edits to postmortem_notes and recipe_type, but replaces
    all ingredients and instructions with newly scraped data.

    Args:
        recipe_id: UUID of recipe to re-import
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        Updated Recipe object with fresh data

    Raises:
        HTTPException: 404 if recipe not found, 400 if no source_url exists
    """
    recipe = await RecipeService.reimport_recipe(
        db=db,
        recipe_id=recipe_id,
    )
    return recipe


@router.post("", response_model=RecipeDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new recipe with ingredients and instructions.

    Args:
        recipe_data: Recipe creation payload with name, ingredients, instructions
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        Created Recipe object with all relationships loaded
    """
    recipe = await RecipeService.create_recipe(
        db=db,
        recipe_data=recipe_data,
        owner_id=current_user.id,
    )
    return recipe


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a recipe by ID with ingredients and instructions."""
    recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    return recipe


@router.put("/{recipe_id}", response_model=RecipeDetailResponse)
async def update_recipe(
    recipe_id: UUID,
    recipe_data: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a recipe (including owner reassignment)."""
    recipe = await RecipeService.update_recipe(
        db=db,
        recipe_id=recipe_id,
        recipe_data=recipe_data,
    )
    return recipe


@router.delete("/{recipe_id}", response_model=RecipeResponse)
async def retire_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete (retire) a recipe with validation.

    Prevents deletion if recipe is used in active week templates.

    Args:
        recipe_id: UUID of recipe to retire
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        Retired Recipe object with retired_at timestamp

    Raises:
        HTTPException: 400 if recipe is used in active templates
    """
    recipe = await RecipeService.delete_recipe(db=db, recipe_id=recipe_id)
    return recipe


@router.post("/{recipe_id}/restore", response_model=RecipeResponse)
async def restore_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restore a retired recipe."""
    recipe = await RecipeService.restore_recipe(db=db, recipe_id=recipe_id)
    return recipe


@router.get("/{recipe_id}/usage", response_model=RecipeUsageResponse)
async def get_recipe_usage(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check which week templates use this recipe."""
    templates = await RecipeService.check_recipe_usage(db=db, recipe_id=recipe_id)
    return {
        "is_used": len(templates) > 0,
        "templates": templates,
    }


# ============================================================================
# Ingredient Endpoints
# ============================================================================


@router.get("/{recipe_id}/ingredients", response_model=List[RecipeIngredientResponse])
async def list_recipe_ingredients(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all ingredients for a recipe."""
    ingredients = await RecipeService.get_ingredients(db=db, recipe_id=recipe_id)
    return ingredients


@router.post(
    "/{recipe_id}/ingredients",
    response_model=RecipeIngredientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_ingredient(
    recipe_id: UUID,
    ingredient_data: RecipeIngredientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an ingredient to a recipe."""
    ingredient = await RecipeService.create_ingredient(
        db=db,
        recipe_id=recipe_id,
        ingredient_data=ingredient_data,
    )
    return ingredient


@router.put(
    "/{recipe_id}/ingredients/{ingredient_id}",
    response_model=RecipeIngredientResponse,
)
async def update_recipe_ingredient(
    recipe_id: UUID,
    ingredient_id: UUID,
    ingredient_data: RecipeIngredientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a recipe ingredient."""
    ingredient = await RecipeService.update_ingredient(
        db=db,
        ingredient_id=ingredient_id,
        ingredient_data=ingredient_data,
    )
    return ingredient


@router.delete(
    "/{recipe_id}/ingredients/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_recipe_ingredient(
    recipe_id: UUID,
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove an ingredient from a recipe."""
    await RecipeService.delete_ingredient(db=db, ingredient_id=ingredient_id)
    return None


# ============================================================================
# Instruction Endpoints
# ============================================================================


@router.get("/{recipe_id}/instructions", response_model=List[RecipeInstructionResponse])
async def list_recipe_instructions(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all instructions for a recipe."""
    instructions = await RecipeService.get_instructions(db=db, recipe_id=recipe_id)
    return instructions


@router.post(
    "/{recipe_id}/instructions",
    response_model=RecipeInstructionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_instruction(
    recipe_id: UUID,
    instruction_data: RecipeInstructionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an instruction to a recipe."""
    instruction = await RecipeService.create_instruction(
        db=db,
        recipe_id=recipe_id,
        instruction_data=instruction_data,
    )
    return instruction


@router.put(
    "/{recipe_id}/instructions/{instruction_id}",
    response_model=RecipeInstructionResponse,
)
async def update_recipe_instruction(
    recipe_id: UUID,
    instruction_id: UUID,
    instruction_data: RecipeInstructionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a recipe instruction."""
    instruction = await RecipeService.update_instruction(
        db=db,
        instruction_id=instruction_id,
        instruction_data=instruction_data,
    )
    return instruction


@router.delete(
    "/{recipe_id}/instructions/{instruction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_recipe_instruction(
    recipe_id: UUID,
    instruction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove an instruction from a recipe."""
    await RecipeService.delete_instruction(db=db, instruction_id=instruction_id)
    return None


# ============================================================================
# Recipe Export/Import (JSON)
# ============================================================================


@router.get("/{recipe_id}/export")
async def export_recipe_json(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export a recipe as JSON file."""
    recipe = await RecipeService.get_recipe(db=db, recipe_id=recipe_id)

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # Build export data structure
    export_data = {
        "name": recipe.name,
        "recipe_type": recipe.recipe_type,
        "description": recipe.description,
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "prep_notes": recipe.prep_notes,
        "postmortem_notes": recipe.postmortem_notes,
        "source_url": recipe.source_url,
        "ingredients": [
            {
                "ingredient_name": ing.ingredient_name,
                "quantity": ing.quantity,
                "unit": ing.unit,
                "order": ing.order,
                "prep_note": ing.prep_note,
            }
            for ing in sorted(recipe.ingredients, key=lambda x: x.order)
        ],
        "instructions": [
            {
                "step_number": inst.step_number,
                "description": inst.description,
                "duration_minutes": inst.duration_minutes,
            }
            for inst in sorted(recipe.instructions, key=lambda x: x.step_number)
        ],
    }

    # Create JSON file in memory
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')

    # Create filename from recipe name
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in recipe.name)
    filename = f"{safe_name}.json"

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
