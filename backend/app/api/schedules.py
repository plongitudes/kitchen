from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.schedule_service import ScheduleService
from app.schemas.schedule import (
    ScheduleSequenceResponse,
    ScheduleSequenceDetailResponse,
    ScheduleSequenceCreate,
    ScheduleSequenceUpdate,
    WeekTemplateResponse,
    WeekTemplateDetailResponse,
    WeekDayAssignmentResponse,
    WeekDayAssignmentCreate,
    WeekDayAssignmentUpdate,
    TemplateReorderRequest,
    SequenceWeekMappingCreate,
    SequenceWeekMappingResponse,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


# ============================================================================
# Schedule Sequence Endpoints
# ============================================================================


@router.get("", response_model=List[ScheduleSequenceResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of all schedule sequences."""
    sequences = await ScheduleService.get_sequences(db=db)
    return sequences


@router.post("", response_model=ScheduleSequenceResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    sequence_data: ScheduleSequenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new schedule sequence."""
    sequence = await ScheduleService.create_sequence(db=db, sequence_data=sequence_data)
    return sequence


@router.get("/{sequence_id}", response_model=ScheduleSequenceDetailResponse)
async def get_schedule(
    sequence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a schedule sequence with all template mappings."""
    sequence = await ScheduleService.get_sequence_by_id(
        db=db,
        sequence_id=sequence_id,
        include_mappings=True,
    )

    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule sequence not found",
        )

    return sequence


@router.put("/{sequence_id}", response_model=ScheduleSequenceResponse)
async def update_schedule(
    sequence_id: UUID,
    sequence_data: ScheduleSequenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a schedule sequence."""
    sequence = await ScheduleService.update_sequence(
        db=db,
        sequence_id=sequence_id,
        sequence_data=sequence_data,
    )
    return sequence


@router.delete("/{sequence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    sequence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a schedule sequence."""
    await ScheduleService.delete_sequence(db=db, sequence_id=sequence_id)


# ============================================================================
# Template Mapping Endpoints (Sequence-Template Many-to-Many)
# ============================================================================


@router.post("/{sequence_id}/templates", response_model=SequenceWeekMappingResponse, status_code=status.HTTP_201_CREATED)
async def add_template_to_sequence(
    sequence_id: UUID,
    mapping_data: SequenceWeekMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a template to a sequence at a specific position."""
    mapping = await ScheduleService.add_template_to_sequence(
        db=db,
        sequence_id=sequence_id,
        template_id=mapping_data.week_template_id,
        position=mapping_data.position,
    )
    return mapping


@router.delete("/{sequence_id}/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_template_from_sequence(
    sequence_id: UUID,
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a template from a sequence (soft delete the mapping)."""
    await ScheduleService.remove_template_from_sequence(
        db=db,
        sequence_id=sequence_id,
        template_id=template_id,
    )


@router.put("/{sequence_id}/templates/reorder")
async def reorder_templates(
    sequence_id: UUID,
    reorder_data: TemplateReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reorder templates in a sequence."""
    await ScheduleService.reorder_sequence_templates(
        db=db,
        sequence_id=sequence_id,
        template_ids=reorder_data.template_ids,
    )
    return {"message": "Templates reordered successfully"}


@router.get("/{sequence_id}/current-template", response_model=WeekTemplateDetailResponse)
async def get_current_template(
    sequence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the currently active week template in a sequence."""
    template = await ScheduleService.get_current_template(
        db=db,
        sequence_id=sequence_id,
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active template found",
        )

    return template


