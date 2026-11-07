"""Food tags. Pure: no database.

Tags describe what was eaten, never whether it was "good". There are no calories,
portions or scores anywhere in Thyma, by design: this audience has a higher risk
around restrictive eating, so food logging stays descriptive.
"""

import re
from collections.abc import Iterable, Mapping
from datetime import time

# The built-in catalog, in display order. Seeded into food_tags by migration 0005.
CATALOG: dict[str, str] = {
    "dairy": "Dairy",
    "gluten": "Gluten",
    "added_sugar": "Added sugar",
    "refined_carbs": "Refined carbs",
    "caffeine": "Caffeine",
    "alcohol": "Alcohol",
    "fried": "Fried",
    "high_protein": "High protein",
    "high_fiber": "High fiber",
    "soy": "Soy",
    "spicy": "Spicy",
    "processed": "Processed",
    "late_night": "Late night",
}

# Set by code from the meal time, never chosen by hand.
LATE_NIGHT = "late_night"

# Words that suggest a tag. Suggestions only: the user confirms every one.
KEYWORDS: dict[str, list[str]] = {
    "dairy": [
        "milk", "paneer", "cheese", "curd", "yogurt", "yoghurt", "dahi", "ghee", "butter",
        "cream", "chai", "latte", "cappuccino", "lassi", "ice cream", "kheer", "raita", "whey",
    ],
    "gluten": [
        "bread", "roti", "chapati", "naan", "paratha", "pasta", "wheat", "sandwich", "wrap",
        "pizza", "cake", "cookie", "biscuit", "noodle", "bagel", "croissant", "beer", "couscous",
        "barley", "seitan", "toast",
    ],
    "added_sugar": [
        "sugar", "dessert", "cake", "cookie", "chocolate", "candy", "sweets", "mithai",
        "ice cream", "soda", "cola", "jalebi", "gulab jamun", "donut", "doughnut", "brownie",
        "syrup", "honey", "jam", "kheer", "halwa",
    ],
    "refined_carbs": [
        "white rice", "rice", "bread", "naan", "pasta", "noodle", "maida", "pizza", "cracker",
        "chips", "fries", "bagel", "croissant", "pastry",
    ],
    "caffeine": [
        "coffee", "chai", "tea", "espresso", "latte", "cappuccino", "cola", "matcha",
        "energy drink",
    ],
    "alcohol": [
        "wine", "beer", "vodka", "whisky", "whiskey", "gin", "rum", "cocktail", "tequila",
        "champagne", "cider",
    ],
    "fried": [
        "fried", "fries", "pakora", "samosa", "bhaji", "tempura", "chips", "crisps", "nugget",
        "vada", "puri", "bhatura", "fritter",
    ],
    "high_protein": [
        "chicken", "egg", "fish", "tofu", "paneer", "lentil", "dal", "daal", "chickpea", "chana",
        "rajma", "beans", "tempeh", "turkey", "beef", "prawn", "shrimp", "salmon", "tuna",
        "protein", "edamame", "whey",
    ],
    "high_fiber": [
        "lentil", "dal", "daal", "beans", "chickpea", "oats", "salad", "broccoli", "vegetable",
        "veggies", "sabzi", "quinoa", "brown rice", "apple", "pear", "berries", "chia", "flax",
        "whole wheat", "millet", "bajra", "jowar", "ragi",
    ],
    "soy": ["tofu", "soy", "soya", "edamame", "tempeh", "miso"],
    "spicy": [
        "spicy", "chilli", "chili", "hot sauce", "curry", "sriracha", "jalapeno", "vindaloo",
        "schezwan",
    ],
    "processed": [
        "chips", "crisps", "sausage", "bacon", "ham", "salami", "instant noodle", "maggi",
        "nugget", "frozen", "packaged", "hot dog", "soda", "cola",
    ],
}  # fmt: skip


def _matches(word: str, text: str) -> bool:
    """Whole-word match, allowing a plural ("egg" matches "eggs", not "eggplant")."""
    return re.search(rf"\b{re.escape(word)}(?:s|es)?\b", text) is not None


def suggest_tags(description: str, custom: Mapping[str, str] | None = None) -> list[str]:
    """Tags whose keywords appear in the description, plus custom tags named in it.

    Built-in tags come first in catalog order, then custom tags by key.
    """
    text = description.lower()
    found = [tag for tag, words in KEYWORDS.items() if any(_matches(w, text) for w in words)]
    for key, display_name in sorted((custom or {}).items()):
        if _matches(display_name.lower(), text) or _matches(key.replace("_", " "), text):
            found.append(key)
    return found


def is_late_night(meal_time: time | None) -> bool:
    """Eaten at 9pm or later, or in the small hours (before 4am). No time, no tag."""
    if meal_time is None:
        return False
    return meal_time >= time(21, 0) or meal_time < time(4, 0)


def tidy_tags(tags: Iterable[str], meal_time: time | None) -> list[str]:
    """Lowercase, de-duplicate, and set late_night from the time (it can't be picked by hand)."""
    tidy: list[str] = []
    for tag in tags:
        key = tag.strip().lower()
        if key and key != LATE_NIGHT and key not in tidy:
            tidy.append(key)
    if is_late_night(meal_time):
        tidy.append(LATE_NIGHT)
    return tidy


def tag_key(display_name: str) -> str:
    """The key for a custom tag: "Green Tea!" -> "green_tea"."""
    return "_".join(re.findall(r"[a-z0-9]+", display_name.lower()))
