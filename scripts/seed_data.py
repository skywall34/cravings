"""Seed food items for tagging pipeline validation."""

SEED_RESTAURANTS = [
    {"name": "Thai Orchid", "cuisine_type": "thai", "source_type": "manual"},
    {"name": "Mama Lucia's", "cuisine_type": "italian", "source_type": "manual"},
    {"name": "Seoul Kitchen", "cuisine_type": "korean", "source_type": "manual"},
    {"name": "Taqueria El Sol", "cuisine_type": "mexican", "source_type": "manual"},
    {"name": "Golden Dragon", "cuisine_type": "chinese", "source_type": "manual"},
    {"name": "Sakura Sushi", "cuisine_type": "japanese", "source_type": "manual"},
    {"name": "Bombay Spice", "cuisine_type": "indian", "source_type": "manual"},
    {"name": "The Grill House", "cuisine_type": "american", "source_type": "manual"},
    {"name": "Olive & Vine", "cuisine_type": "mediterranean", "source_type": "manual"},
    {"name": "Falafel King", "cuisine_type": "middle_eastern", "source_type": "manual"},
]

# (restaurant_index, name, description)
SEED_FOOD_ITEMS = [
    # Thai Orchid (0)
    (0, "Pad Thai", "Stir-fried rice noodles with shrimp, bean sprouts, peanuts, and tamarind sauce"),
    (0, "Green Curry", "Spicy green curry with chicken, Thai basil, bamboo shoots, and coconut milk"),
    (0, "Tom Yum Soup", "Hot and sour shrimp soup with lemongrass, galangal, and lime"),
    (0, "Mango Sticky Rice", "Sweet sticky rice with fresh mango and coconut cream"),
    (0, "Thai Iced Tea", "Strong brewed tea with sweetened condensed milk over ice"),

    # Mama Lucia's (1)
    (1, "Spaghetti Carbonara", "Pasta with pancetta, egg, pecorino romano, and black pepper"),
    (1, "Margherita Pizza", "Wood-fired with fresh mozzarella, basil, and San Marzano tomatoes"),
    (1, "Chicken Parmesan", "Breaded chicken cutlet with marinara and melted mozzarella, served with penne"),
    (1, "Tiramisu", "Espresso-soaked ladyfingers layered with mascarpone cream and cocoa"),
    (1, "Minestrone Soup", "Hearty vegetable soup with beans, pasta, and fresh herbs"),

    # Seoul Kitchen (2)
    (2, "Bulgogi", "Thinly sliced marinated beef grilled with onions and served with steamed rice"),
    (2, "Kimchi Jjigae", "Spicy fermented cabbage stew with pork belly and tofu"),
    (2, "Bibimbap", "Mixed rice bowl with vegetables, beef, gochujang, and a fried egg"),
    (2, "Korean Fried Chicken", "Double-fried chicken with sweet and spicy gochujang glaze"),
    (2, "Japchae", "Glass noodles stir-fried with vegetables, beef, and soy sesame sauce"),

    # Taqueria El Sol (3)
    (3, "Carne Asada Burrito", "Grilled steak with rice, beans, cheese, guacamole in a flour tortilla"),
    (3, "Fish Tacos", "Battered fish with cabbage slaw, chipotle crema on corn tortillas"),
    (3, "Chicken Quesadilla", "Grilled flour tortilla stuffed with chicken, cheese, and peppers"),
    (3, "Churros", "Fried dough pastry coated in cinnamon sugar with chocolate dipping sauce"),
    (3, "Elote", "Grilled Mexican street corn with mayo, cotija cheese, chili powder, and lime"),

    # Golden Dragon (4)
    (4, "Kung Pao Chicken", "Stir-fried chicken with peanuts, chili peppers, and Sichuan peppercorns"),
    (4, "Mapo Tofu", "Soft tofu in spicy chili and fermented bean sauce with ground pork"),
    (4, "Fried Rice", "Wok-fried rice with egg, vegetables, and soy sauce"),
    (4, "Hot and Sour Soup", "Spicy and tangy soup with tofu, mushrooms, and egg ribbons"),
    (4, "Peking Duck", "Roasted duck with thin pancakes, hoisin sauce, scallions, and cucumber"),

    # Sakura Sushi (5)
    (5, "Spicy Tuna Roll", "Raw tuna with spicy mayo, cucumber, and rice wrapped in nori"),
    (5, "Chicken Teriyaki", "Grilled chicken glazed with sweet soy teriyaki sauce, served with rice"),
    (5, "Miso Soup", "Traditional soup with tofu, wakame seaweed, and green onions"),
    (5, "Salmon Sashimi", "Thinly sliced raw salmon served with wasabi and pickled ginger"),
    (5, "Tempura Udon", "Thick wheat noodles in hot dashi broth topped with shrimp tempura"),

    # Bombay Spice (6)
    (6, "Chicken Tikka Masala", "Tender chicken pieces in a creamy tomato-based curry sauce with basmati rice"),
    (6, "Palak Paneer", "Fresh spinach curry with cubes of Indian cottage cheese"),
    (6, "Lamb Biryani", "Fragrant basmati rice layered with spiced lamb, saffron, and fried onions"),
    (6, "Samosa", "Crispy pastry filled with spiced potatoes and peas, served with chutney"),
    (6, "Naan Bread", "Traditional tandoor-baked flatbread brushed with butter"),

    # The Grill House (7)
    (7, "Classic Cheeseburger", "Angus beef patty with cheddar, lettuce, tomato, pickle on a brioche bun"),
    (7, "BBQ Ribs", "Slow-smoked pork ribs with house BBQ sauce, coleslaw, and cornbread"),
    (7, "Grilled Salmon", "Pan-seared Atlantic salmon with lemon butter sauce and roasted asparagus"),
    (7, "Mac and Cheese", "Creamy baked macaroni with three-cheese blend and breadcrumb topping"),
    (7, "Caesar Salad", "Romaine lettuce, parmesan, croutons, and house-made caesar dressing"),

    # Olive & Vine (8)
    (8, "Greek Salad", "Tomatoes, cucumber, red onion, olives, and feta cheese with olive oil"),
    (8, "Lamb Gyro", "Seasoned lamb in warm pita with tzatziki, tomatoes, and onions"),
    (8, "Hummus Plate", "Creamy chickpea hummus with olive oil, pita bread, and vegetable crudités"),
    (8, "Grilled Halloumi", "Pan-grilled halloumi cheese with roasted peppers and mint"),
    (8, "Baklava", "Layers of phyllo dough with chopped walnuts and honey syrup"),

    # Falafel King (9)
    (9, "Falafel Wrap", "Crispy chickpea fritters with tahini, pickled vegetables in pita"),
    (9, "Shawarma Plate", "Slow-roasted seasoned chicken with garlic sauce, rice, and salad"),
    (9, "Tabbouleh", "Fresh parsley salad with bulgur wheat, tomatoes, mint, and lemon"),
    (9, "Beef Kebab", "Grilled spiced ground beef skewers with onions and sumac"),
    (9, "Kunafa", "Shredded pastry with sweet cheese filling soaked in rose water syrup"),
]
