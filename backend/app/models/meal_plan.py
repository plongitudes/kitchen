from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class MealPlanInstance(Base):
    """Week instance (object/snapshot) referencing a week template."""

    __tablename__ = "meal_plan_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schedule_sequences.id", ondelete="SET NULL"),
        nullable=True,  # Nullable for backward compatibility and manual instances
        index=True,
    )
    week_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("week_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    instance_start_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    sequence = relationship("ScheduleSequence")
    week_template = relationship("WeekTemplate")
    grocery_lists = relationship(
        "GroceryList",
        back_populates="meal_plan_instance",
        cascade="all, delete-orphan",
    )
    meal_assignments = relationship(
        "MealAssignment",
        back_populates="meal_plan_instance",
        cascade="all, delete-orphan",
        order_by="MealAssignment.day_of_week, MealAssignment.order",
    )

    def __repr__(self):
        return f"<MealPlanInstance {self.instance_start_date}>"


class GroceryList(Base):
    """Grocery list for a specific shopping day."""

    __tablename__ = "grocery_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_plan_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_plan_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shopping_date = Column(Date, nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    meal_plan_instance = relationship("MealPlanInstance", back_populates="grocery_lists")
    items = relationship(
        "GroceryListItem",
        back_populates="grocery_list",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<GroceryList {self.shopping_date}>"


class GroceryListItem(Base):
    """Aggregated ingredient item in a grocery list."""

    __tablename__ = "grocery_list_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grocery_list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("grocery_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name = Column(String, nullable=False)
    total_quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    source_recipe_ids = Column(Text, nullable=False)  # JSON array of recipe IDs
    source_recipe_details = Column(Text, nullable=True)  # JSON array of recipe contributions
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    grocery_list = relationship("GroceryList", back_populates="items")

    def __repr__(self):
        return f"<GroceryListItem {self.total_quantity} {self.unit} {self.ingredient_name}>"


class MealAssignment(Base):
    """Instance-specific meal assignment (overrides template assignment)."""

    __tablename__ = "meal_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_plan_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_plan_instances.id", ondelete="CASCADE"),
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
    action = Column(String, nullable=False)  # e.g., cook, shop, takeout, rest, leftovers
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=True,  # Null for non-cook actions
        index=True,
    )
    order = Column(Integer, default=0, nullable=False)  # For multiple actions per day
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    meal_plan_instance = relationship("MealPlanInstance", back_populates="meal_assignments")

    def __repr__(self):
        return f"<MealAssignment day={self.day_of_week} action={self.action}>"
