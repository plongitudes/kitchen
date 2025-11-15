from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.meal_plan_service import MealPlanService
from app.services.grocery_service import GroceryService
from app.services.discord_service import get_bot
from app.schemas.meal_plan import (
    MealPlanInstanceResponse,
    MealPlanInstanceDetailResponse,
    AdvanceWeekRequest,
    AdvanceWeekResponse,
    GroceryListResponse,
    GroceryListDetailResponse,
    GenerateGroceryListRequest,
    MealAssignmentCreate,
    MealAssignmentUpdate,
    MealAssignmentResponse,
)
from app.schemas.schedule import StartScheduleRequest

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


# ============================================================================
# Meal Plan Instance Endpoints
# ============================================================================


@router.get("", response_model=List[MealPlanInstanceResponse])
async def list_meal_plans(
    limit: Optional[int] = Query(50, description="Maximum number of instances to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of all meal plan instances."""
    instances = await MealPlanService.get_instances(db=db, limit=limit)
    return instances


@router.get("/current", response_model=MealPlanInstanceDetailResponse)
async def get_current_meal_plan(
    sequence_id: UUID = Query(..., description="Schedule sequence ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current active meal plan instance for a sequence."""
    instance = await MealPlanService.get_current_instance(
        db=db,
        sequence_id=sequence_id,
    )

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No meal plan instance found for this sequence",
        )

    # Build detailed response with dates
    instance_detail = await MealPlanService.build_instance_detail(
        instance=instance,
        db=db,
    )

    return instance_detail


@router.post("/advance-week", response_model=AdvanceWeekResponse)
async def advance_week(
    request_data: AdvanceWeekRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually advance to the next week in the sequence."""
    result = await MealPlanService.advance_week(
        db=db,
        sequence_id=request_data.sequence_id,
    )
    return result


@router.post("/start-on-week")
async def start_on_arbitrary_week(
    sequence_id: UUID = Query(..., description="Schedule sequence ID"),
    request_data: StartScheduleRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a schedule on an arbitrary week in the sequence.

    This allows users to:
    - Start a new schedule mid-week
    - Switch from one schedule to another
    - Preserve history from existing instances

    The system will:
    1. Calculate instance start date (most recent Sunday)
    2. Preserve meal assignments from past days if an instance exists
    3. Delete the old instance if it exists
    4. Create a new instance from the chosen template
    5. Copy preserved assignments to the new instance
    6. Update the sequence's current_week_index
    """
    result = await MealPlanService.start_on_arbitrary_week(
        db=db,
        sequence_id=sequence_id,
        week_template_id=request_data.week_template_id,
        position=request_data.position,
    )
    return result


@router.get("/{instance_id}", response_model=MealPlanInstanceDetailResponse)
async def get_meal_plan(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific meal plan instance with assignments and dates."""
    instance = await MealPlanService.get_instance_by_id(
        db=db,
        instance_id=instance_id,
    )

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan instance not found",
        )

    # Build detailed response with dates
    instance_detail = await MealPlanService.build_instance_detail(
        instance=instance,
        db=db,
    )

    return instance_detail


# ============================================================================
# Grocery List Endpoints
# ============================================================================


@router.post(
    "/{instance_id}/grocery-lists/generate",
    response_model=GroceryListDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_grocery_list(
    instance_id: UUID,
    request_data: GenerateGroceryListRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a grocery list for a specific shopping day."""
    grocery_list = await GroceryService.generate_grocery_list(
        db=db,
        instance_id=instance_id,
        shopping_date=request_data.shopping_date,
    )

    # Send Discord notification
    try:
        bot = get_bot()
        item_count = len(grocery_list.items)
        shopping_date = request_data.shopping_date.strftime("%A, %B %d")
        message = f"🛒 **Grocery List Generated**\n\n"
        message += f"Shopping Date: {shopping_date}\n"
        message += f"Items: {item_count}\n\n"

        # Add top items
        if item_count > 0:
            message += "**Items:**\n"
            for item in grocery_list.items[:10]:  # Show first 10
                message += f"- {item.quantity} {item.unit} {item.ingredient_name}\n"
            if item_count > 10:
                message += f"... and {item_count - 10} more items"

        await bot.send_message(message)
    except Exception as e:
        # Don't fail the request if Discord fails
        print(f"Failed to send Discord notification: {e}")

    return grocery_list


@router.get(
    "/{instance_id}/grocery-lists",
    response_model=List[GroceryListResponse],
)
async def list_instance_grocery_lists(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all grocery lists for a specific meal plan instance."""
    lists = await GroceryService.get_grocery_lists(
        db=db,
        instance_id=instance_id,
    )
    return lists


@router.get("/grocery-lists/all", response_model=List[GroceryListResponse])
async def list_grocery_lists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of all grocery lists."""
    lists = await GroceryService.get_grocery_lists(db=db)
    return lists


@router.get(
    "/grocery-lists/{grocery_list_id}",
    response_model=GroceryListDetailResponse,
)
async def get_grocery_list(
    grocery_list_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific grocery list with items."""
    grocery_list = await GroceryService.get_grocery_list_by_id(
        db=db,
        grocery_list_id=grocery_list_id,
    )

    if not grocery_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grocery list not found",
        )

    return grocery_list


# ============================================================================
# Meal Assignment Endpoints (Per-Instance Modifications)
# ============================================================================


@router.get(
    "/{instance_id}/assignments",
    response_model=List[MealAssignmentResponse],
)
async def list_meal_assignments(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all meal assignments for a specific meal plan instance."""
    assignments = await MealPlanService.get_meal_assignments(
        db=db,
        instance_id=instance_id,
    )
    return assignments


@router.post(
    "/{instance_id}/assignments",
    response_model=MealAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_meal_assignment(
    instance_id: UUID,
    assignment_data: MealAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new assignment to a meal plan instance."""
    assignment = await MealPlanService.create_meal_assignment(
        db=db,
        instance_id=instance_id,
        assignment_data=assignment_data,
    )
    return assignment


@router.put(
    "/{instance_id}/assignments/{assignment_id}",
    response_model=MealAssignmentResponse,
)
async def update_meal_assignment(
    instance_id: UUID,
    assignment_id: UUID,
    assignment_data: MealAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a meal assignment (person, action, or recipe)."""
    assignment = await MealPlanService.update_meal_assignment(
        db=db,
        instance_id=instance_id,
        assignment_id=assignment_id,
        assignment_data=assignment_data,
    )
    return assignment


@router.delete(
    "/{instance_id}/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_meal_assignment(
    instance_id: UUID,
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a meal assignment (revert to template or remove custom assignment)."""
    await MealPlanService.delete_meal_assignment(
        db=db,
        instance_id=instance_id,
        assignment_id=assignment_id,
    )
    return None
