"""
Integration tests for ingredients API.

Tests cover:
- Common ingredient CRUD operations
- Unmapped ingredient listing
- Ingredient mapping and merging
- Auto-mapping functionality
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


class TestIngredientListAndGet:
    """Test ingredient listing and retrieval."""

    def test_list_ingredients_empty(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test listing ingredients when none exist."""
        response = async_authenticated_client.get("/ingredients")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_and_list_ingredient(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test creating and listing an ingredient."""
        # Create (aliases are created via mapping, not on create)
        create_response = async_authenticated_client.post(
            "/ingredients",
            json={
                "name": "Garlic",
                "category": "produce",
            },
        )
        assert create_response.status_code == 201
        ingredient = create_response.json()
        assert ingredient["name"] == "Garlic"
        assert ingredient["category"] == "produce"

        # List
        list_response = async_authenticated_client.get("/ingredients")
        assert list_response.status_code == 200
        ingredients = list_response.json()
        assert any(i["name"] == "Garlic" for i in ingredients)

    def test_get_ingredient_by_id(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test getting a specific ingredient by ID."""
        # Create
        create_response = async_authenticated_client.post(
            "/ingredients",
            json={"name": "Onion", "category": "produce"},
        )
        ingredient_id = create_response.json()["id"]

        # Get
        response = async_authenticated_client.get(f"/ingredients/{ingredient_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ingredient_id
        assert data["name"] == "Onion"

    def test_get_ingredient_not_found(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test getting non-existent ingredient."""
        fake_id = str(uuid4())
        response = async_authenticated_client.get(f"/ingredients/{fake_id}")

        assert response.status_code == 404

    def test_list_ingredients_with_search(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test filtering ingredients by search term."""
        # Create test ingredients
        async_authenticated_client.post(
            "/ingredients",
            json={"name": "Chicken Breast", "category": "protein"},
        )
        async_authenticated_client.post(
            "/ingredients",
            json={"name": "Chicken Thigh", "category": "protein"},
        )
        async_authenticated_client.post(
            "/ingredients",
            json={"name": "Beef Steak", "category": "protein"},
        )

        # Search
        response = async_authenticated_client.get("/ingredients?search=chicken")

        assert response.status_code == 200
        ingredients = response.json()
        assert all("chicken" in i["name"].lower() for i in ingredients)

    def test_list_ingredients_with_category_filter(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test filtering ingredients by category."""
        # Create test ingredients
        async_authenticated_client.post(
            "/ingredients",
            json={"name": "Milk", "category": "dairy"},
        )
        async_authenticated_client.post(
            "/ingredients",
            json={"name": "Carrot", "category": "produce"},
        )

        # Filter by category
        response = async_authenticated_client.get("/ingredients?category=dairy")

        assert response.status_code == 200
        ingredients = response.json()
        assert all(i["category"] == "dairy" for i in ingredients)


class TestIngredientUpdate:
    """Test ingredient update operations."""

    def test_update_ingredient(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test updating an ingredient."""
        # Create
        create_response = async_authenticated_client.post(
            "/ingredients",
            json={"name": "Tomato", "category": "produce"},
        )
        ingredient_id = create_response.json()["id"]

        # Update
        response = async_authenticated_client.put(
            f"/ingredients/{ingredient_id}",
            json={"name": "Roma Tomato", "category": "produce"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Roma Tomato"

    def test_update_ingredient_not_found(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test updating non-existent ingredient."""
        fake_id = str(uuid4())
        response = async_authenticated_client.put(
            f"/ingredients/{fake_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 404


class TestIngredientDelete:
    """Test ingredient deletion."""

    def test_delete_ingredient(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test deleting an unused ingredient."""
        # Create
        create_response = async_authenticated_client.post(
            "/ingredients",
            json={"name": "Celery", "category": "produce"},
        )
        ingredient_id = create_response.json()["id"]

        # Delete
        response = async_authenticated_client.delete(f"/ingredients/{ingredient_id}")

        assert response.status_code == 204

        # Verify deleted
        get_response = async_authenticated_client.get(f"/ingredients/{ingredient_id}")
        assert get_response.status_code == 404

    def test_delete_ingredient_not_found(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test deleting non-existent ingredient."""
        fake_id = str(uuid4())
        response = async_authenticated_client.delete(f"/ingredients/{fake_id}")

        assert response.status_code == 404


class TestIngredientAliases:
    """Test ingredient alias operations."""

    def test_create_ingredient_and_add_alias_via_mapping(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test creating ingredient and adding alias via create-with-mapping."""
        # First create a recipe with unmapped ingredient
        recipe_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Pepper Stir Fry",
                "recipe_type": "dinner",
                "cook_time_minutes": 15,
                "ingredients": [
                    {"ingredient_name": "bell peppers", "quantity": 2, "unit": "whole", "order": 1},
                ],
                "instructions": [],
            },
        )
        assert recipe_response.status_code == 201

        # Create with initial mapping
        response = async_authenticated_client.post(
            "/ingredients/create-with-mapping",
            json={
                "name": "Bell Pepper",
                "category": "produce",
                "initial_alias": "bell peppers",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Bell Pepper"
        # Should have at least the initial alias
        alias_names = [a["alias"] for a in data["aliases"]]
        assert "bell peppers" in alias_names


class TestUnmappedIngredients:
    """Test unmapped ingredient operations."""

    def test_list_unmapped_ingredients(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test listing unmapped ingredients."""
        # First create a recipe with ingredients
        recipe_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Soup",
                "recipe_type": "dinner",
                "cook_time_minutes": 30,
                "ingredients": [
                    {"ingredient_name": "mystery vegetable", "quantity": 1, "unit": "cup", "order": 1},
                ],
                "instructions": [],
            },
        )
        assert recipe_response.status_code == 201

        # List unmapped
        response = async_authenticated_client.get("/ingredients/unmapped")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestIngredientMapping:
    """Test ingredient mapping operations."""

    def test_map_ingredient(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test mapping an unmapped ingredient to a common ingredient."""
        # Create a recipe with unmapped ingredient
        recipe_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Garlic Bread",
                "recipe_type": "side",
                "cook_time_minutes": 10,
                "ingredients": [
                    {"ingredient_name": "garlic cloves", "quantity": 4, "unit": "whole", "order": 1},
                ],
                "instructions": [],
            },
        )
        assert recipe_response.status_code == 201

        # Create a common ingredient
        ingredient_response = async_authenticated_client.post(
            "/ingredients",
            json={"name": "Garlic", "category": "produce"},
        )
        common_id = ingredient_response.json()["id"]

        # Map the ingredient
        response = async_authenticated_client.post(
            "/ingredients/map",
            json={
                "ingredient_name": "garlic cloves",
                "common_ingredient_id": common_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "recipes_updated" in data

    def test_create_with_mapping(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test creating a new ingredient with initial mapping."""
        # Create a recipe with unmapped ingredient
        recipe_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Basil Pesto",
                "recipe_type": "sauce",
                "cook_time_minutes": 5,
                "ingredients": [
                    {"ingredient_name": "fresh basil leaves", "quantity": 2, "unit": "cup", "order": 1},
                ],
                "instructions": [],
            },
        )
        assert recipe_response.status_code == 201

        # Create with mapping
        response = async_authenticated_client.post(
            "/ingredients/create-with-mapping",
            json={
                "name": "Basil",
                "category": "herbs",
                "initial_alias": "fresh basil leaves",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Basil"
        alias_names = [a["alias"] for a in data["aliases"]]
        assert "fresh basil leaves" in alias_names


class TestIngredientMerge:
    """Test ingredient merging."""

    def test_merge_ingredients(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test merging multiple ingredients into one."""
        # Create source ingredients
        source1 = async_authenticated_client.post(
            "/ingredients",
            json={"name": "Green Onion", "category": "produce"},
        ).json()
        source2 = async_authenticated_client.post(
            "/ingredients",
            json={"name": "Scallion", "category": "produce"},
        ).json()

        # Create target ingredient
        target = async_authenticated_client.post(
            "/ingredients",
            json={"name": "Spring Onion", "category": "produce"},
        ).json()

        # Merge
        response = async_authenticated_client.post(
            "/ingredients/merge",
            json={
                "source_ingredient_ids": [source1["id"], source2["id"]],
                "target_ingredient_id": target["id"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "recipes_updated" in data


class TestAutoMap:
    """Test auto-mapping functionality."""

    def test_auto_map_ingredients(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test auto-mapping unmapped ingredients."""
        # Create multiple recipes with same unmapped ingredient
        for i in range(3):
            async_authenticated_client.post(
                "/recipes",
                json={
                    "name": f"Test Recipe {i}",
                    "recipe_type": "dinner",
                    "cook_time_minutes": 20,
                    "ingredients": [
                        {"ingredient_name": "common test ingredient", "quantity": 1, "unit": "cup", "order": 1},
                    ],
                    "instructions": [],
                },
            )

        # Auto-map with min_recipe_count=2
        response = async_authenticated_client.post(
            "/ingredients/auto-map?min_recipe_count=2"
        )

        assert response.status_code == 200
        data = response.json()
        assert "ingredients_created" in data
        assert "recipe_ingredients_updated" in data


class TestAuthRequired:
    """Test that authentication is required."""

    def test_list_requires_auth(
        self,
        async_client: TestClient,
    ):
        """Test that listing ingredients requires authentication."""
        response = async_client.get("/ingredients")
        assert response.status_code == 401

    def test_create_requires_auth(
        self,
        async_client: TestClient,
    ):
        """Test that creating ingredients requires authentication."""
        response = async_client.post(
            "/ingredients",
            json={"name": "Test", "category": "test"},
        )
        assert response.status_code == 401
