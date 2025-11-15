from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class CommonIngredient(Base):
    """Canonical ingredient names for normalization across recipes."""

    __tablename__ = "common_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    category = Column(String, nullable=True)  # dairy, produce, meat, pantry, spices, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    aliases = relationship(
        "IngredientAlias",
        back_populates="common_ingredient",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<CommonIngredient {self.name} ({self.category})>"


class IngredientAlias(Base):
    """Alternative names/spellings for common ingredients."""

    __tablename__ = "ingredient_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    common_ingredient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("common_ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alias = Column(String, nullable=False, unique=True)  # Case-insensitive lookup
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    common_ingredient = relationship("CommonIngredient", back_populates="aliases")

    # Case-insensitive unique index
    __table_args__ = (
        Index('idx_alias_lower', func.lower(alias), unique=True),
    )

    def __repr__(self):
        return f"<IngredientAlias {self.alias} -> {self.common_ingredient_id}>"
