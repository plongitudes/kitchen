"""API endpoints for week templates."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.template_service import TemplateService
from app.services.discord_service import get_bot, NotificationFormatter
from app.schemas.schedule import (
    WeekTemplateResponse,
    WeekTemplateDetailResponse,
    WeekTemplateCreate,
    WeekTemplateUpdate,
    WeekTemplateForkRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=List[WeekTemplateResponse])
async def list_templates(
    include_retired: bool = Query(False, description="Include retired templates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all week templates."""
    templates = await TemplateService.list_templates(db, include_retired=include_retired)
    return templates


@router.get("/{template_id}", response_model=WeekTemplateDetailResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific week template with assignments."""
    template = await TemplateService.get_template_by_id(
        db, template_id, include_assignments=True
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return template


@router.post("", response_model=WeekTemplateDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: WeekTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new week template with assignments."""
    template = await TemplateService.create_template(db, template_data)
    return template


@router.put("/{template_id}", response_model=WeekTemplateResponse)
async def update_template(
    template_id: UUID,
    template_data: WeekTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a week template."""
    template = await TemplateService.update_template(db, template_id, template_data)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return template


@router.post("/{template_id}/fork", response_model=WeekTemplateDetailResponse)
async def fork_template(
    template_id: UUID,
    fork_request: WeekTemplateForkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fork (deep copy) a week template with all its assignments."""
    template = await TemplateService.fork_template(
        db, template_id, new_name=fork_request.new_name
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return template


@router.delete("/{template_id}")
async def retire_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retire a week template (soft delete).

    This removes the template from all sequences and auto-advances
    sequences that are currently using this template.
    """
    result = await TemplateService.retire_template(db, template_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Send Discord notification for template retirement
    bot = get_bot()
    if bot.is_connected():
        try:
            message = NotificationFormatter.format_template_retirement(
                template_name=result['template'].name,
                affected_sequences=result['affected_sequences']
            )
            await bot.send_message(message)
        except Exception as e:
            # Log error but don't fail the retirement operation
            logger.error(f"Failed to send Discord notification for template retirement: {e}")

    return {
        "message": "Template retired successfully",
        "template_id": str(result['template'].id),
        "affected_sequences": [
            {
                "sequence_id": str(seq['sequence_id']),
                "sequence_name": seq['sequence_name'],
                "old_position": seq['old_position'],
                "new_position": seq['new_position'],
            }
            for seq in result['affected_sequences']
        ],
        "can_hard_delete": result['can_hard_delete'],
    }


@router.delete("/{template_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hard delete a template (only if not referenced by any instances).

    This permanently removes the template from the database.
    Returns 400 if the template has existing meal plan instances.
    """
    success = await TemplateService.delete_template(db, template_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete template: it has existing meal plan instances or was not found",
        )
