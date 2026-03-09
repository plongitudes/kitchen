"""Unit tests for index_text module — Bittman-style sub-entry generation."""

import pytest
from app.utils.index_text import stem_food_word, tokenize_name, generate_sub_entry


class TestStemFoodWord:
    """Tests for the simple plural-stripping stemmer."""

    def test_oes_suffix(self):
        assert stem_food_word("potatoes") == "potato"
        assert stem_food_word("tomatoes") == "tomato"

    def test_ies_suffix(self):
        assert stem_food_word("cherries") == "cherry"
        assert stem_food_word("berries") == "berry"

    def test_sibilant_es_suffix(self):
        assert stem_food_word("dishes") == "dish"
        assert stem_food_word("peaches") == "peach"

    def test_ses_suffix(self):
        assert stem_food_word("cheeses") == "cheese"
        assert stem_food_word("sauces") == "sauce"

    def test_ves_suffix(self):
        assert stem_food_word("halves") == "half"
        assert stem_food_word("leaves") == "leaf"

    def test_regular_s_suffix(self):
        assert stem_food_word("beans") == "bean"
        assert stem_food_word("carrots") == "carrot"
        assert stem_food_word("onions") == "onion"

    def test_no_strip_short_words(self):
        assert stem_food_word("is") == "is"
        assert stem_food_word("as") == "as"

    def test_no_strip_double_s(self):
        assert stem_food_word("bass") == "bass"
        assert stem_food_word("grass") == "grass"

    def test_already_singular(self):
        assert stem_food_word("potato") == "potato"
        assert stem_food_word("chicken") == "chicken"
        assert stem_food_word("rice") == "rice"

    def test_case_insensitive(self):
        assert stem_food_word("Potatoes") == "potato"
        assert stem_food_word("BEANS") == "bean"


class TestTokenizeName:
    """Tests for the word tokenizer."""

    def test_basic_tokenization(self):
        assert tokenize_name("Crispy Potato Quesadillas") == ["crispy", "potato", "quesadillas"]

    def test_strips_punctuation(self):
        assert tokenize_name("Black-Bean Soup") == ["black", "bean", "soup"]

    def test_handles_apostrophes(self):
        assert tokenize_name("Shepherd's Pie") == ["shepherd's", "pie"]

    def test_lowercases(self):
        assert tokenize_name("CHICKEN TIKKA MASALA") == ["chicken", "tikka", "masala"]


class TestGenerateSubEntry:
    """Tests for the core sub-entry generation algorithm."""

    def test_strips_ingredient_from_name(self):
        """Basic case: ingredient word removed from recipe name."""
        result = generate_sub_entry("Crispy Potato Quesadillas", "Potato")
        assert result == "crispy quesadillas"

    def test_strips_plural_ingredient(self):
        """Plural form of ingredient is also stripped."""
        result = generate_sub_entry("Black Bean Soup", "Beans")
        assert result == "black soup"

    def test_multi_word_ingredient(self):
        """All tokens of a multi-word ingredient are stripped."""
        result = generate_sub_entry("Black Bean Soup", "Black Beans")
        assert result == "soup"

    def test_ingredient_not_in_name(self):
        """When ingredient doesn't appear in name, return full name lowercased."""
        result = generate_sub_entry("Guacamole", "Avocado")
        assert result == "guacamole"

    def test_name_equals_ingredient(self):
        """When recipe name is just the ingredient, return 'about'."""
        result = generate_sub_entry("Chicken", "Chicken")
        assert result == "about"

    def test_preserves_prepositions(self):
        """Trailing prepositions are kept (Bittman convention)."""
        result = generate_sub_entry("Braised with Potatoes", "Potato")
        assert result == "braised with"

    def test_preserves_leading_and(self):
        """Leading 'and' is preserved."""
        result = generate_sub_entry("Shrimp and Vegetable Stir-Fry", "Shrimp")
        assert result == "and vegetable stir fry"

    def test_cross_reference_strips_current_heading(self):
        """Multi-ingredient recipe only strips the current heading's ingredient."""
        result = generate_sub_entry(
            "Artichokes with Potatoes Garlic and Shrimp", "Potato"
        )
        assert "artichokes" in result
        assert "garlic" in result
        assert "shrimp" in result
        assert "potato" not in result

    def test_dish_type_inversion(self):
        """With dish_type, dish type moves to front with modifiers after comma."""
        result = generate_sub_entry(
            "Crispy Potato Quesadillas", "Potato", dish_type="quesadillas"
        )
        assert result == "quesadillas, crispy"

    def test_dish_type_no_modifiers(self):
        """When only dish type remains (no modifiers), no comma needed."""
        result = generate_sub_entry("Potato Soup", "Potato", dish_type="soup")
        assert result == "soup"

    def test_dish_type_not_in_remaining(self):
        """When dish_type tokens aren't in remaining text, no inversion."""
        result = generate_sub_entry(
            "Crispy Potato Bites", "Potato", dish_type="soup"
        )
        assert result == "crispy bites"

    def test_dish_type_multi_word(self):
        """Multi-word dish types are handled."""
        result = generate_sub_entry(
            "Chicken Pot Pie with Herbs", "Chicken", dish_type="pot pie"
        )
        assert result == "pot pie, with herbs"

    def test_dish_type_plural_match(self):
        """Dish type matches via stemming."""
        result = generate_sub_entry(
            "Crispy Chicken Tacos", "Chicken", dish_type="taco"
        )
        assert result == "tacos, crispy"

    def test_empty_recipe_name(self):
        """Edge case: empty recipe name."""
        result = generate_sub_entry("", "Potato")
        assert result == "about"
