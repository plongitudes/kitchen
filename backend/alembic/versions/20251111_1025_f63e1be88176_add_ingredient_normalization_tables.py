"""add ingredient normalization tables

Revision ID: f63e1be88176
Revises: a7102d195b91
Create Date: 2025-11-11 10:25:17.685786

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'f63e1be88176'
down_revision: Union[str, None] = 'a7102d195b91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Seed data: common ingredients with their aliases
COMMON_INGREDIENTS = [
    # Dairy
    {"name": "milk", "category": "dairy", "aliases": ["whole milk", "2% milk", "skim milk"]},
    {"name": "butter", "category": "dairy", "aliases": ["unsalted butter", "salted butter"]},
    {"name": "eggs", "category": "dairy", "aliases": ["egg", "large eggs", "chicken eggs"]},
    {"name": "cheese", "category": "dairy", "aliases": ["cheddar cheese", "shredded cheese"]},
    {"name": "cream", "category": "dairy", "aliases": ["heavy cream", "whipping cream", "heavy whipping cream"]},
    {"name": "yogurt", "category": "dairy", "aliases": ["greek yogurt", "plain yogurt"]},
    {"name": "sour cream", "category": "dairy", "aliases": []},
    {"name": "parmesan cheese", "category": "dairy", "aliases": ["parmesan", "parmigiano-reggiano", "grated parmesan"]},

    # Produce
    {"name": "onion", "category": "produce", "aliases": ["yellow onion", "white onion", "onions"]},
    {"name": "garlic", "category": "produce", "aliases": ["garlic cloves", "fresh garlic"]},
    {"name": "tomato", "category": "produce", "aliases": ["tomatoes", "roma tomatoes", "fresh tomatoes"]},
    {"name": "potato", "category": "produce", "aliases": ["potatoes", "russet potatoes", "yukon gold potatoes"]},
    {"name": "carrot", "category": "produce", "aliases": ["carrots", "baby carrots"]},
    {"name": "celery", "category": "produce", "aliases": ["celery stalk", "celery stalks"]},
    {"name": "bell pepper", "category": "produce", "aliases": ["sweet pepper", "capsicum", "red bell pepper", "green bell pepper"]},
    {"name": "lemon", "category": "produce", "aliases": ["lemons", "fresh lemon"]},
    {"name": "scallion", "category": "produce", "aliases": ["green onion", "spring onion", "scallions", "green onions"]},
    {"name": "cilantro", "category": "produce", "aliases": ["coriander", "fresh cilantro", "coriander leaves"]},
    {"name": "parsley", "category": "produce", "aliases": ["fresh parsley", "italian parsley", "flat-leaf parsley"]},
    {"name": "ginger", "category": "produce", "aliases": ["fresh ginger", "ginger root"]},
    {"name": "spinach", "category": "produce", "aliases": ["fresh spinach", "baby spinach"]},
    {"name": "lettuce", "category": "produce", "aliases": ["romaine lettuce", "iceberg lettuce"]},

    # Meat & Protein
    {"name": "chicken breast", "category": "meat", "aliases": ["chicken breasts", "boneless chicken breast", "skinless chicken breast"]},
    {"name": "ground beef", "category": "meat", "aliases": ["ground chuck", "lean ground beef"]},
    {"name": "bacon", "category": "meat", "aliases": ["bacon strips", "thick cut bacon"]},
    {"name": "pork chop", "category": "meat", "aliases": ["pork chops", "bone-in pork chops"]},
    {"name": "salmon", "category": "meat", "aliases": ["salmon fillet", "salmon fillets", "fresh salmon"]},
    {"name": "shrimp", "category": "meat", "aliases": ["prawns", "jumbo shrimp", "raw shrimp"]},

    # Pantry Staples
    {"name": "all-purpose flour", "category": "pantry", "aliases": ["AP flour", "white flour", "plain flour", "flour"]},
    {"name": "sugar", "category": "pantry", "aliases": ["granulated sugar", "white sugar"]},
    {"name": "brown sugar", "category": "pantry", "aliases": ["light brown sugar", "dark brown sugar", "packed brown sugar"]},
    {"name": "salt", "category": "pantry", "aliases": ["table salt", "kosher salt", "sea salt"]},
    {"name": "black pepper", "category": "pantry", "aliases": ["pepper", "ground black pepper", "freshly ground black pepper"]},
    {"name": "olive oil", "category": "pantry", "aliases": ["EVOO", "extra virgin olive oil", "extra-virgin olive oil"]},
    {"name": "vegetable oil", "category": "pantry", "aliases": ["canola oil", "cooking oil"]},
    {"name": "rice", "category": "pantry", "aliases": ["white rice", "long grain rice", "jasmine rice"]},
    {"name": "pasta", "category": "pantry", "aliases": ["spaghetti", "penne", "dried pasta"]},
    {"name": "bread", "category": "pantry", "aliases": ["white bread", "sandwich bread", "sliced bread"]},
    {"name": "soy sauce", "category": "pantry", "aliases": ["shoyu", "low sodium soy sauce"]},
    {"name": "chicken broth", "category": "pantry", "aliases": ["chicken stock", "low sodium chicken broth"]},
    {"name": "beef broth", "category": "pantry", "aliases": ["beef stock"]},
    {"name": "tomato paste", "category": "pantry", "aliases": ["concentrated tomato paste"]},
    {"name": "canned tomatoes", "category": "pantry", "aliases": ["diced tomatoes", "crushed tomatoes", "whole peeled tomatoes"]},
    {"name": "baking powder", "category": "pantry", "aliases": []},
    {"name": "baking soda", "category": "pantry", "aliases": ["sodium bicarbonate"]},
    {"name": "vanilla extract", "category": "pantry", "aliases": ["pure vanilla extract", "vanilla"]},

    # Spices & Herbs
    {"name": "cumin", "category": "spices", "aliases": ["ground cumin", "cumin powder"]},
    {"name": "paprika", "category": "spices", "aliases": ["sweet paprika", "smoked paprika"]},
    {"name": "oregano", "category": "spices", "aliases": ["dried oregano", "oregano leaves"]},
    {"name": "basil", "category": "spices", "aliases": ["dried basil", "basil leaves"]},
    {"name": "thyme", "category": "spices", "aliases": ["dried thyme", "thyme leaves"]},
    {"name": "cinnamon", "category": "spices", "aliases": ["ground cinnamon", "cinnamon powder"]},
    {"name": "garlic powder", "category": "spices", "aliases": []},
    {"name": "onion powder", "category": "spices", "aliases": []},
    {"name": "chili powder", "category": "spices", "aliases": ["chile powder"]},
    {"name": "cayenne pepper", "category": "spices", "aliases": ["ground cayenne", "cayenne"]},
    {"name": "red pepper flakes", "category": "spices", "aliases": ["crushed red pepper", "red chili flakes"]},
    {"name": "italian seasoning", "category": "spices", "aliases": ["italian herbs"]},
]


def upgrade() -> None:
    # Create common_ingredients table
    op.create_table(
        'common_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_common_ingredients_name'), 'common_ingredients', ['name'], unique=True)

    # Create ingredient_aliases table
    op.create_table(
        'ingredient_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('common_ingredient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alias', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['common_ingredient_id'], ['common_ingredients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alias')
    )
    op.create_index(op.f('ix_ingredient_aliases_common_ingredient_id'), 'ingredient_aliases', ['common_ingredient_id'], unique=False)
    # Case-insensitive unique index on alias
    op.execute('CREATE UNIQUE INDEX idx_alias_lower ON ingredient_aliases (LOWER(alias))')

    # Add common_ingredient_id to recipe_ingredients
    op.add_column('recipe_ingredients',
        sa.Column('common_ingredient_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_recipe_ingredients_common_ingredient_id',
        'recipe_ingredients', 'common_ingredients',
        ['common_ingredient_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(
        op.f('ix_recipe_ingredients_common_ingredient_id'),
        'recipe_ingredients',
        ['common_ingredient_id'],
        unique=False
    )

    # Seed common ingredients
    common_ingredients_table = sa.table(
        'common_ingredients',
        sa.column('id', postgresql.UUID),
        sa.column('name', sa.String),
        sa.column('category', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    ingredient_aliases_table = sa.table(
        'ingredient_aliases',
        sa.column('id', postgresql.UUID),
        sa.column('common_ingredient_id', postgresql.UUID),
        sa.column('alias', sa.String),
        sa.column('created_at', sa.DateTime),
    )

    now = datetime.utcnow()

    for ingredient_data in COMMON_INGREDIENTS:
        ingredient_id = uuid.uuid4()

        # Insert common ingredient
        op.execute(
            common_ingredients_table.insert().values(
                id=ingredient_id,
                name=ingredient_data["name"],
                category=ingredient_data["category"],
                created_at=now,
                updated_at=now,
            )
        )

        # Insert aliases
        for alias in ingredient_data["aliases"]:
            op.execute(
                ingredient_aliases_table.insert().values(
                    id=uuid.uuid4(),
                    common_ingredient_id=ingredient_id,
                    alias=alias,
                    created_at=now,
                )
            )


def downgrade() -> None:
    # Drop indexes and foreign key
    op.drop_index(op.f('ix_recipe_ingredients_common_ingredient_id'), table_name='recipe_ingredients')
    op.drop_constraint('fk_recipe_ingredients_common_ingredient_id', 'recipe_ingredients', type_='foreignkey')
    op.drop_column('recipe_ingredients', 'common_ingredient_id')

    # Drop alias index
    op.execute('DROP INDEX IF EXISTS idx_alias_lower')
    op.drop_index(op.f('ix_ingredient_aliases_common_ingredient_id'), table_name='ingredient_aliases')
    op.drop_table('ingredient_aliases')

    # Drop common ingredients
    op.drop_index(op.f('ix_common_ingredients_name'), table_name='common_ingredients')
    op.drop_table('common_ingredients')
