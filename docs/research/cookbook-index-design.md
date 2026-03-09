# Cookbook Index Design Research

## Source Material
Analysis of the index from *How to Cook Everything* (Mark Bittman, Revised Edition), pages 984-1070.

## Index Structure

### Three types of top-level entries
1. **Ingredients** — `Potato(es)`, `Chicken`, `Shrimp`, `Almond(s)`, `Chocolate`
2. **Dish types** — `Sandwich(es)`, `Soup`, `Cookies`, `Pie`, `Stew`
3. **Cooking methods** — `Broiled vegetables`, `Roasted vegetables`

### Entry hierarchy (up to 3 levels)
```
Potato(es)                          ← top-level ingredient heading
  baked, 336                        ← cooking method sub-entry
    bay-scented, 337                ← variation
    curried, 346
  braised
    cream-, 343
    curried in coconut milk, 344
  mashed, 339
```

## Inversion Rules

### Adjectives go last, after a comma
- "Classic Chocolate Chip Cookies" → `cookies, chocolate chip, classic`
- "Crisp Almond-Crusted Fish" → `fish, crisp, almond-crusted`
- "Quick Stuffed Tomatoes" → `tomatoes, quick stuffed`

### Entries under a heading don't repeat the heading word
Under `Potato(es)`:
- `baked, 336` — NOT `Potato, baked`
- `quesadillas, crispy` — NOT `Potato quesadillas, crispy`

### Cross-references for multi-ingredient recipes
"Artichokes with Potatoes, Garlic, Olives, and Shrimp" appears under:
- `Artichoke(s)` → `with potatoes, garlic, olives, and shrimp`
- `Potato(es)` → `artichokes with garlic, olives, shrimp, and`
- `Shrimp` → `artichokes with potatoes, garlic, olives, and`

The indexed ingredient's name is removed from the sub-entry text and replaced with trailing "and".

## Opaque/Foreign Dish Names

### Two tiers based on recognizability

**Tier 1 — Gets own top-level entry + cross-references:**
| Dish | Own entry | Also under |
|---|---|---|
| Guacamole | `G > Guacamole` | `Avocado(s) > guacamole. See Guacamole` |
| Baba ghanoush | `B > Baba ghanoush` | `Eggplant > baba ghanoush` |
| Puttanesca | `P > Puttanesca` | `Anchovy(ies) > puttanesca` |
| Risotto | `R > Risotto` (sub-entries) | `Rice` mentions risotto |
| Pesto | `P > Pesto` (sub-entries) | `Basil > pesto, traditional` |
| Osso buco | `O > Osso buco` | `Veal > shanks > osso buco` |

**Tier 2 — Only appears under its primary ingredient(s):**
| Dish | Only under |
|---|---|
| Saltimbocca | `Veal > saltimbocca` |
| Escabeche | `Chicken > escabeche` |
| Biryani | `Chicken > biryani` + `Rice > biryani` |
| Scampi | `Shrimp > scampi` |
| Cassoulet | `Stew > cassoulet` + `White beans > cassoulet` |

**The distinction:** Would a reader look this up by name? Guacamole yes, saltimbocca probably not.

## Design Decisions for Our System

### Existing schema fields we can leverage
- `recipe.name` — full recipe name
- `recipe.index_name` — inverted/alphabetized form for index entry (opt-in)
- `recipe.dish_type` — dish type category
- `ingredient.is_indexed` — star toggle, controls cross-references
- `ingredient.ingredient_name` — heading for cross-reference entries

### How index entries are generated

**Recipe's own entry (opt-in via `index_name`):**
- If `index_name` is set → recipe gets a top-level entry filed under that name
- If `index_name` is blank → recipe only appears under its starred ingredients
- Example: `index_name` = "Quesadillas, Crispy Potato" → filed under Q

**Ingredient cross-references (automatic via starred ingredients):**
- Each starred ingredient creates a heading
- The recipe appears as a sub-entry under that heading
- Cosmetic cleanup: if the ingredient name appears in the recipe name, strip it from the sub-entry text to avoid redundancy
- Example: "Crispy Potato Quesadillas" under `Potato(es)` → `quesadillas, crispy`
- When ingredient name is NOT in recipe name: use recipe name as-is
- Example: "Guacamole" under `Avocado(es)` → `guacamole`

### Word matching for cosmetic cleanup
- Match `dish_type` as a phrase first (handles multi-word types like "pot pie")
- Fuzzy-match starred `ingredient_name` against recipe name tokens (handle stemming: potatoes→potato)
- Everything unmatched = modifiers/adjectives → moved to end after comma
- Falls down on: adjectival forms (lemony≠lemons), ingredient not in name (guacamole), multi-word ingredients
- Fallback: `index_name` override handles all edge cases manually

### Default behavior
- `index_name`: blank by default (opt-in). Forces editorial thought about the inverted form.
- `is_indexed` star: per-ingredient toggle in the slide-out drawer.
