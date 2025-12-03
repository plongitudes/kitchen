from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.session import Base


class IngredientUnit(str, enum.Enum):
    """Valid units for recipe ingredients."""

    # Volume
    CUP = "cup"
    TABLESPOON = "tablespoon"
    TEASPOON = "teaspoon"
    FLUID_OUNCE = "fluid_ounce"
    PINT = "pint"
    QUART = "quart"
    GALLON = "gallon"
    ML = "ml"
    LITER = "liter"

    # Weight
    GRAM = "gram"
    KILOGRAM = "kilogram"
    OUNCE = "ounce"
    POUND = "pound"

    # Count
    COUNT = "count"
    WHOLE = "whole"
    ITEM = "item"

    # Special
    BUNCH = "bunch"
    CLOVE = "clove"
    CAN = "can"
    JAR = "jar"
    PACKAGE = "package"
    PINCH = "pinch"
    DASH = "dash"
    TO_TASTE = "to taste"


class Recipe(Base):
    """Recipe model with owner and soft delete support."""

    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    recipe_type = Column(String, nullable=True)  # e.g., breakfast, dinner, dessert
    description = Column(Text, nullable=True)  # Recipe description/summary
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    prep_notes = Column(Text, nullable=True)
    postmortem_notes = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)
    retired_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    ingredients = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
    instructions = relationship(
        "RecipeInstruction",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
    prep_steps = relationship(
        "RecipePrepStep",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Recipe {self.name}>"


class RecipeIngredient(Base):
    """Recipe ingredient with validated units."""

    __tablename__ = "recipe_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=True)
    unit: Column[IngredientUnit] = Column(
        SQLEnum(IngredientUnit, values_callable=lambda x: [e.value for e in x]), nullable=True
    )
    order = Column(Integer, nullable=False)
    common_ingredient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("common_ingredients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prep_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    common_ingredient = relationship("CommonIngredient")
    prep_step_links = relationship(
        "PrepStepIngredient",
        foreign_keys="[PrepStepIngredient.recipe_ingredient_id]",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<RecipeIngredient {self.quantity} {self.unit} {self.ingredient_name}>"


class RecipeInstruction(Base):
    """Recipe instruction step."""

    __tablename__ = "recipe_instructions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=True)  # For Gantt chart (Phase 2)
    depends_on_step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipe_instructions.id", ondelete="SET NULL"),
        nullable=True,
    )  # Phase 2 feature
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="instructions")

    def __repr__(self):
        return f"<RecipeInstruction {self.step_number}>"


class RecipePrepStep(Base):
    """Prep step that can be tied to one or more ingredients."""

    __tablename__ = "recipe_prep_steps"
    __table_args__ = (
        # Composite index for efficient prep step lookups by recipe and description
        Index("ix_recipe_prep_steps_recipe_id_description", "recipe_id", "description"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = Column(String, nullable=False)  # e.g., "Slice thinly" or "Dice into 1-inch cubes"
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="prep_steps")
    ingredient_links = relationship(
        "PrepStepIngredient",
        back_populates="prep_step",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<RecipePrepStep {self.order}: {self.description[:30]}>"


class PrepStepIngredient(Base):
    """Junction table linking prep steps to ingredients."""

    __tablename__ = "prep_step_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prep_step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipe_prep_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipe_ingredient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipe_ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prep_step = relationship("RecipePrepStep", back_populates="ingredient_links")
    ingredient = relationship("RecipeIngredient")

    def __repr__(self):
        return f"<PrepStepIngredient {self.prep_step_id} -> {self.recipe_ingredient_id}>"
