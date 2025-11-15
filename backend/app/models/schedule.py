from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class ScheduleSequence(Base):
    """Schedule sequence (rotating list of themed weeks)."""

    __tablename__ = "schedule_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    current_week_index = Column(Integer, default=0, nullable=False)
    advancement_day_of_week = Column(Integer, nullable=False)  # 0=Sunday, 6=Saturday
    advancement_time = Column(String, nullable=False)  # HH:MM format
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    week_mappings = relationship(
        "SequenceWeekMapping",
        back_populates="sequence",
        order_by="SequenceWeekMapping.position",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ScheduleSequence {self.name}>"


class WeekTemplate(Base):
    """Week template (independent, reusable meal plan blueprint)."""

    __tablename__ = "week_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # "Italian Week", "Fork of Italian Week"
    retired_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    day_assignments = relationship(
        "WeekDayAssignment",
        back_populates="week_template",
        cascade="all, delete-orphan",
        order_by="WeekDayAssignment.day_of_week, WeekDayAssignment.order",
    )
    sequence_mappings = relationship(
        "SequenceWeekMapping",
        back_populates="week_template",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<WeekTemplate {self.name}>"


class SequenceWeekMapping(Base):
    """Many-to-many mapping between sequences and week templates."""

    __tablename__ = "sequence_week_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schedule_sequences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    week_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("week_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position = Column(Integer, nullable=False)  # 1-indexed position in sequence
    removed_at = Column(DateTime(timezone=True), nullable=True)  # Removed from this sequence
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    sequence = relationship("ScheduleSequence", back_populates="week_mappings")
    week_template = relationship("WeekTemplate", back_populates="sequence_mappings")

    def __repr__(self):
        return f"<SequenceWeekMapping seq={self.sequence_id} pos={self.position}>"


class WeekDayAssignment(Base):
    """Day assignment within a week template (person/action/recipe mapping)."""

    __tablename__ = "week_day_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("week_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week = Column(Integer, nullable=False)  # 0=Sunday, 6=Saturday
    assigned_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    action = Column(String, nullable=False)  # e.g., cook, shop, takeout, rest
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=True,  # Null for non-cook actions
        index=True,
    )
    order = Column(Integer, default=0, nullable=False)  # For multiple actions per day
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    week_template = relationship("WeekTemplate", back_populates="day_assignments")
    recipe = relationship("Recipe")  # For accessing recipe.name

    @property
    def recipe_name(self):
        """Get the recipe name from the relationship."""
        return self.recipe.name if self.recipe else None

    def __repr__(self):
        return f"<WeekDayAssignment day={self.day_of_week} action={self.action}>"
