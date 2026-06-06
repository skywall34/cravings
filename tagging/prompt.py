"""Few-shot prompt template for food attribute tagging via Ollama/gemma4:e2b."""

SYSTEM_PROMPT = """You are a food attribute tagger. Given a food item name and optional description, output a JSON object with these exact fields and value ranges:

CONTINUOUS (0.0 to 1.0):
- spice_level: heat intensity (0=none, 1=extremely spicy)
- sweetness: sweet taste (0=none, 1=very sweet)
- sourness: sour/acidic taste (0=none, 1=very sour)
- savory_umami: savory depth (0=light, 1=deeply savory)
- saltiness: salt intensity (0=none, 1=very salty)
- bitterness: bitter taste (0=none, 1=very bitter)
- temperature: serving temp (0=cold/frozen, 0.5=room temp, 1=very hot)
- texture_softness: texture (0=crunchy/crispy, 1=soft/creamy)
- sauce_heaviness: how saucy (0=dry, 1=heavily sauced)
- richness: caloric density/fat (0=light, 1=heavy/indulgent)
- veggie_density: how vegetable-forward (0=none, 1=primarily vegetables)
- dairy_content: cheese/cream/milk presence (0=none, 1=dairy-heavy)
- smell_intensity: how aromatic/pungent (0=mild, 1=very pungent)
- nausea_trigger: likelihood of triggering nausea (0=safe, 1=high risk)

CATEGORICAL (use exact values):
- protein_type: chicken|beef|pork|fish|shellfish|egg|tofu_plant|legume|none
- cuisine_type: american|mexican|italian|chinese|japanese|thai|indian|korean|mediterranean|middle_eastern|french|spanish|german|eastern_european|vietnamese|filipino|indonesian|brazilian|caribbean|ethiopian|other
- carb_base: rice|noodles_pasta|bread|potato|tortilla|none

SAFETY FLAGS (list of strings, empty if none apply):
- safety_flags: any of [raw_fish, raw_egg, raw_meat, unpasteurized_dairy, high_mercury_fish]

DIETARY FLAGS (list of strings, empty if none apply):
- dietary_flags: any of [vegetarian, vegan, gluten_free, dairy_free, halal, kosher, contains_nuts, contains_shellfish, contains_soy, contains_eggs]

Output ONLY valid JSON. No explanation."""

FEW_SHOT_EXAMPLES = [
    {
        "input": "Chicken Tikka Masala - Tender chicken pieces in a creamy tomato-based curry sauce, served with basmati rice",
        "output": {
            "spice_level": 0.5,
            "sweetness": 0.2,
            "sourness": 0.2,
            "savory_umami": 0.7,
            "saltiness": 0.5,
            "bitterness": 0.0,
            "temperature": 0.9,
            "texture_softness": 0.7,
            "sauce_heaviness": 0.8,
            "richness": 0.7,
            "veggie_density": 0.1,
            "dairy_content": 0.5,
            "smell_intensity": 0.6,
            "nausea_trigger": 0.2,
            "protein_type": "chicken",
            "cuisine_type": "indian",
            "carb_base": "rice",
            "safety_flags": [],
            "dietary_flags": ["contains_eggs"],
        },
    },
    {
        "input": "Caesar Salad - Romaine lettuce, parmesan, croutons, caesar dressing",
        "output": {
            "spice_level": 0.0,
            "sweetness": 0.1,
            "sourness": 0.3,
            "savory_umami": 0.4,
            "saltiness": 0.5,
            "bitterness": 0.1,
            "temperature": 0.2,
            "texture_softness": 0.3,
            "sauce_heaviness": 0.3,
            "richness": 0.4,
            "veggie_density": 0.7,
            "dairy_content": 0.4,
            "smell_intensity": 0.3,
            "nausea_trigger": 0.1,
            "protein_type": "none",
            "cuisine_type": "american",
            "carb_base": "bread",
            "safety_flags": ["raw_egg"],
            "dietary_flags": ["contains_eggs"],
        },
    },
    {
        "input": "Spicy Tuna Roll - Raw tuna with spicy mayo, cucumber, and rice wrapped in nori",
        "output": {
            "spice_level": 0.4,
            "sweetness": 0.1,
            "sourness": 0.2,
            "savory_umami": 0.6,
            "saltiness": 0.4,
            "bitterness": 0.0,
            "temperature": 0.2,
            "texture_softness": 0.5,
            "sauce_heaviness": 0.3,
            "richness": 0.4,
            "veggie_density": 0.2,
            "dairy_content": 0.0,
            "smell_intensity": 0.4,
            "nausea_trigger": 0.3,
            "protein_type": "fish",
            "cuisine_type": "japanese",
            "carb_base": "rice",
            "safety_flags": ["raw_fish"],
            "dietary_flags": ["dairy_free"],
        },
    },
    {
        "input": "Croissant - Buttery, flaky laminated pastry baked golden, served warm",
        "output": {
            "spice_level": 0.0,
            "sweetness": 0.3,
            "sourness": 0.1,
            "savory_umami": 0.2,
            "saltiness": 0.3,
            "bitterness": 0.0,
            "temperature": 0.7,
            "texture_softness": 0.5,
            "sauce_heaviness": 0.0,
            "richness": 0.7,
            "veggie_density": 0.0,
            "dairy_content": 0.8,
            "smell_intensity": 0.5,
            "nausea_trigger": 0.0,
            "protein_type": "none",
            "cuisine_type": "french",
            "carb_base": "bread",
            "safety_flags": [],
            "dietary_flags": ["vegetarian", "contains_eggs"],
        },
    },
    {
        "input": "Pho Bo - Vietnamese beef noodle soup with rice noodles, herbs, bean sprouts, and lime",
        "output": {
            "spice_level": 0.2,
            "sweetness": 0.1,
            "sourness": 0.3,
            "savory_umami": 0.8,
            "saltiness": 0.5,
            "bitterness": 0.1,
            "temperature": 1.0,
            "texture_softness": 0.6,
            "sauce_heaviness": 0.7,
            "richness": 0.4,
            "veggie_density": 0.3,
            "dairy_content": 0.0,
            "smell_intensity": 0.6,
            "nausea_trigger": 0.1,
            "protein_type": "beef",
            "cuisine_type": "vietnamese",
            "carb_base": "noodles_pasta",
            "safety_flags": [],
            "dietary_flags": ["dairy_free", "gluten_free"],
        },
    },
    {
        "input": "Margherita Pizza - Wood-fired with fresh mozzarella, basil, and San Marzano tomatoes",
        "output": {
            "spice_level": 0.0,
            "sweetness": 0.2,
            "sourness": 0.3,
            "savory_umami": 0.6,
            "saltiness": 0.4,
            "bitterness": 0.0,
            "temperature": 0.9,
            "texture_softness": 0.4,
            "sauce_heaviness": 0.4,
            "richness": 0.6,
            "veggie_density": 0.3,
            "dairy_content": 0.7,
            "smell_intensity": 0.5,
            "nausea_trigger": 0.1,
            "protein_type": "none",
            "cuisine_type": "italian",
            "carb_base": "bread",
            "safety_flags": [],
            "dietary_flags": ["vegetarian", "contains_eggs"],
        },
    },
]


def build_tagging_prompt(food_name: str, description: str | None = None) -> list[dict]:
    import json

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for ex in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": ex["input"]})
        messages.append({"role": "assistant", "content": json.dumps(ex["output"])})

    user_input = food_name
    if description:
        user_input = f"{food_name} - {description}"
    messages.append({"role": "user", "content": user_input})

    return messages
