"""Utility functions for generating Bittman-style index sub-entry text.

Given a recipe name and a heading name (ingredient or dish type), strips
the heading's tokens from the recipe name. The remainder becomes the
sub-entry text displayed under that heading in the recipe index.

Example: "Crispy Potato Quesadillas" under heading "Potato"
  → stripped: "crispy quesadillas"
  → with dish_type "quesadillas": "quesadillas, crispy"
"""

import re
from typing import List, Optional


def stem_food_word(word: str) -> str:
    """Strip common English food plurals to a base form.

    Only handles regular plural patterns relevant to food words.
    Not a full Porter stemmer — just enough for ingredient matching.
    """
    w = word.lower()
    if len(w) <= 2:
        return w

    # -oes → -o (potatoes → potato, tomatoes → tomato)
    if w.endswith("oes") and len(w) > 4:
        return w[:-2]

    # -ies → -y (cherries → cherry, berries → berry)
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"

    # -ves → -f (leaves → leaf, halves → half)
    if w.endswith("ves") and len(w) > 4:
        return w[:-3] + "f"

    # -ses → -se (cheeses → cheese, cases → case)
    if w.endswith("ses") and len(w) > 4:
        return w[:-1]

    # -ces → -ce (sauces → sauce)
    if w.endswith("ces") and len(w) > 4:
        return w[:-1]

    # -es after sibilants (dishes → dish, peaches → peach, boxes → box)
    if w.endswith("es") and len(w) > 3:
        base = w[:-2]
        if base.endswith(("sh", "ch", "x", "z")):
            return base

    # -s (beans → bean, carrots → carrot)
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]

    return w


def tokenize_name(text: str) -> List[str]:
    """Split text into lowercase word tokens, stripping punctuation."""
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def generate_sub_entry(
    recipe_name: str,
    heading_name: str,
    dish_type: Optional[str] = None,
) -> str:
    """Generate Bittman-style sub-entry text for a recipe under a heading.

    Strips heading tokens from the recipe name. If dish_type is provided
    and its tokens appear in the remaining text, inverts to put the dish
    type first with modifiers after a comma.

    Args:
        recipe_name: Full recipe name (e.g., "Crispy Potato Quesadillas")
        heading_name: Index heading (e.g., "Potato" or "Potatoes")
        dish_type: Optional dish type for inversion (e.g., "quesadillas")

    Returns:
        Sub-entry text (e.g., "quesadillas, crispy")
    """
    recipe_tokens = tokenize_name(recipe_name)
    heading_stems = {stem_food_word(t) for t in tokenize_name(heading_name)}

    # Remove tokens whose stem matches any heading stem
    remaining = [t for t in recipe_tokens if stem_food_word(t) not in heading_stems]

    if not remaining:
        return "about"

    # Dish type inversion: move dish type tokens to front
    if dish_type:
        dish_stems = {stem_food_word(t) for t in tokenize_name(dish_type)}
        dish_tokens = [t for t in remaining if stem_food_word(t) in dish_stems]
        modifier_tokens = [t for t in remaining if stem_food_word(t) not in dish_stems]

        if dish_tokens and modifier_tokens:
            return f"{' '.join(dish_tokens)}, {' '.join(modifier_tokens)}"

    return " ".join(remaining)
