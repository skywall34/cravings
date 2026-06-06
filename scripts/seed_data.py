"""Seed food items for tagging pipeline validation."""

SEED_RESTAURANTS = [
    # --- existing (indices 0–9) ---
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

    # --- new (indices 10–32) ---
    {"name": "Bangkok Street", "cuisine_type": "thai", "source_type": "manual"},          # 10
    {"name": "Thai Corner", "cuisine_type": "thai", "source_type": "manual"},             # 11
    {"name": "Trattoria Roma", "cuisine_type": "italian", "source_type": "manual"},       # 12
    {"name": "Pizza Napoli", "cuisine_type": "italian", "source_type": "manual"},         # 13
    {"name": "K-BBQ House", "cuisine_type": "korean", "source_type": "manual"},           # 14
    {"name": "Bunsik Corner", "cuisine_type": "korean", "source_type": "manual"},         # 15
    {"name": "Casa Oaxaca", "cuisine_type": "mexican", "source_type": "manual"},          # 16
    {"name": "Taco Loco", "cuisine_type": "mexican", "source_type": "manual"},            # 17
    {"name": "Dim Sum Palace", "cuisine_type": "chinese", "source_type": "manual"},       # 18
    {"name": "Sichuan House", "cuisine_type": "chinese", "source_type": "manual"},        # 19
    {"name": "Ramen House", "cuisine_type": "japanese", "source_type": "manual"},         # 20
    {"name": "Izakaya Yoshi", "cuisine_type": "japanese", "source_type": "manual"},       # 21
    {"name": "Curry Club", "cuisine_type": "indian", "source_type": "manual"},            # 22
    {"name": "Tandoor Palace", "cuisine_type": "indian", "source_type": "manual"},        # 23
    {"name": "Smokehouse BBQ", "cuisine_type": "american", "source_type": "manual"},      # 24
    {"name": "Diner Classic", "cuisine_type": "american", "source_type": "manual"},       # 25
    {"name": "The Burger Lab", "cuisine_type": "american", "source_type": "manual"},      # 26
    {"name": "Mezze Bar", "cuisine_type": "mediterranean", "source_type": "manual"},      # 27
    {"name": "Aegean Kitchen", "cuisine_type": "mediterranean", "source_type": "manual"}, # 28
    {"name": "Shawarma Republic", "cuisine_type": "middle_eastern", "source_type": "manual"}, # 29
    {"name": "Levant Table", "cuisine_type": "middle_eastern", "source_type": "manual"},  # 30
    {"name": "Fusion Kitchen", "cuisine_type": "other", "source_type": "manual"},         # 31
    {"name": "Street Bites", "cuisine_type": "other", "source_type": "manual"},           # 32

    # --- world expansion (indices 33–62) ---
    {"name": "Café de Paris", "cuisine_type": "french", "source_type": "manual"},         # 33
    {"name": "Brasserie Lyon", "cuisine_type": "french", "source_type": "manual"},        # 34
    {"name": "Le Bistrot", "cuisine_type": "french", "source_type": "manual"},            # 35
    {"name": "Tapas Bar Madrid", "cuisine_type": "spanish", "source_type": "manual"},     # 36
    {"name": "La Paella", "cuisine_type": "spanish", "source_type": "manual"},            # 37
    {"name": "El Pimiento", "cuisine_type": "spanish", "source_type": "manual"},          # 38
    {"name": "Zum Goldenen Hahn", "cuisine_type": "german", "source_type": "manual"},     # 39
    {"name": "Biergarten Haus", "cuisine_type": "german", "source_type": "manual"},       # 40
    {"name": "Wurst & Brot", "cuisine_type": "german", "source_type": "manual"},          # 41
    {"name": "Babička Kitchen", "cuisine_type": "eastern_european", "source_type": "manual"}, # 42
    {"name": "Pierogi House", "cuisine_type": "eastern_european", "source_type": "manual"},   # 43
    {"name": "Budapest Table", "cuisine_type": "eastern_european", "source_type": "manual"},  # 44
    {"name": "Pho Saigon", "cuisine_type": "vietnamese", "source_type": "manual"},        # 45
    {"name": "Bún Bò Huế House", "cuisine_type": "vietnamese", "source_type": "manual"},  # 46
    {"name": "Bánh Mì & More", "cuisine_type": "vietnamese", "source_type": "manual"},    # 47
    {"name": "Lutong Pinoy", "cuisine_type": "filipino", "source_type": "manual"},        # 48
    {"name": "Kain Tayo", "cuisine_type": "filipino", "source_type": "manual"},           # 49
    {"name": "Adobo House", "cuisine_type": "filipino", "source_type": "manual"},         # 50
    {"name": "Warung Bali", "cuisine_type": "indonesian", "source_type": "manual"},       # 51
    {"name": "Nasi Goreng Kitchen", "cuisine_type": "indonesian", "source_type": "manual"}, # 52
    {"name": "Sate Haus", "cuisine_type": "indonesian", "source_type": "manual"},         # 53
    {"name": "Churrascaria Rio", "cuisine_type": "brazilian", "source_type": "manual"},   # 54
    {"name": "Feira da Carne", "cuisine_type": "brazilian", "source_type": "manual"},     # 55
    {"name": "Boteco Verde", "cuisine_type": "brazilian", "source_type": "manual"},       # 56
    {"name": "Rum Shack", "cuisine_type": "caribbean", "source_type": "manual"},          # 57
    {"name": "Island Flavors", "cuisine_type": "caribbean", "source_type": "manual"},     # 58
    {"name": "Jerk Palace", "cuisine_type": "caribbean", "source_type": "manual"},        # 59
    {"name": "Habesha Kitchen", "cuisine_type": "ethiopian", "source_type": "manual"},    # 60
    {"name": "Injera House", "cuisine_type": "ethiopian", "source_type": "manual"},       # 61
    {"name": "Addis Table", "cuisine_type": "ethiopian", "source_type": "manual"},        # 62

    # --- supplemental restaurants (indices 63–72) ---
    {"name": "Alsace Table", "cuisine_type": "french", "source_type": "manual"},          # 63
    {"name": "Bodega Sevilla", "cuisine_type": "spanish", "source_type": "manual"},       # 64
    {"name": "Rheinland Stub'n", "cuisine_type": "german", "source_type": "manual"},      # 65
    {"name": "Kraków Corner", "cuisine_type": "eastern_european", "source_type": "manual"}, # 66
    {"name": "Hội An Garden", "cuisine_type": "vietnamese", "source_type": "manual"},     # 67
    {"name": "Kamayan Table", "cuisine_type": "filipino", "source_type": "manual"},       # 68
    {"name": "Javanese Kitchen", "cuisine_type": "indonesian", "source_type": "manual"},  # 69
    {"name": "Bahia Nordeste", "cuisine_type": "brazilian", "source_type": "manual"},     # 70
    {"name": "Kingston Yard", "cuisine_type": "caribbean", "source_type": "manual"},      # 71
    {"name": "Blue Nile Café", "cuisine_type": "ethiopian", "source_type": "manual"},     # 72
]

# (restaurant_index, name, description)
SEED_FOOD_ITEMS = [
    # ─── Thai Orchid (0) — existing 5 ───────────────────────────────────────
    (0, "Pad Thai", "Stir-fried rice noodles with shrimp, bean sprouts, peanuts, and tamarind sauce"),
    (0, "Green Curry", "Spicy green curry with chicken, Thai basil, bamboo shoots, and coconut milk"),
    (0, "Tom Yum Soup", "Hot and sour shrimp soup with lemongrass, galangal, and lime"),
    (0, "Mango Sticky Rice", "Sweet sticky rice with fresh mango and coconut cream"),
    (0, "Thai Iced Tea", "Strong brewed tea with sweetened condensed milk over ice"),

    # ─── Mama Lucia's (1) — existing 5 ─────────────────────────────────────
    (1, "Spaghetti Carbonara", "Pasta with pancetta, egg, pecorino romano, and black pepper"),
    (1, "Margherita Pizza", "Wood-fired with fresh mozzarella, basil, and San Marzano tomatoes"),
    (1, "Chicken Parmesan", "Breaded chicken cutlet with marinara and melted mozzarella, served with penne"),
    (1, "Tiramisu", "Espresso-soaked ladyfingers layered with mascarpone cream and cocoa"),
    (1, "Minestrone Soup", "Hearty vegetable soup with beans, pasta, and fresh herbs"),

    # ─── Seoul Kitchen (2) — existing 5 ─────────────────────────────────────
    (2, "Bulgogi", "Thinly sliced marinated beef grilled with onions and served with steamed rice"),
    (2, "Kimchi Jjigae", "Spicy fermented cabbage stew with pork belly and tofu"),
    (2, "Bibimbap", "Mixed rice bowl with vegetables, beef, gochujang, and a fried egg"),
    (2, "Korean Fried Chicken", "Double-fried chicken with sweet and spicy gochujang glaze"),
    (2, "Japchae", "Glass noodles stir-fried with vegetables, beef, and soy sesame sauce"),

    # ─── Taqueria El Sol (3) — existing 5 ───────────────────────────────────
    (3, "Carne Asada Burrito", "Grilled steak with rice, beans, cheese, guacamole in a flour tortilla"),
    (3, "Fish Tacos", "Battered fish with cabbage slaw, chipotle crema on corn tortillas"),
    (3, "Chicken Quesadilla", "Grilled flour tortilla stuffed with chicken, cheese, and peppers"),
    (3, "Churros", "Fried dough pastry coated in cinnamon sugar with chocolate dipping sauce"),
    (3, "Elote", "Grilled Mexican street corn with mayo, cotija cheese, chili powder, and lime"),

    # ─── Golden Dragon (4) — existing 5 ─────────────────────────────────────
    (4, "Kung Pao Chicken", "Stir-fried chicken with peanuts, chili peppers, and Sichuan peppercorns"),
    (4, "Mapo Tofu", "Soft tofu in spicy chili and fermented bean sauce with ground pork"),
    (4, "Fried Rice", "Wok-fried rice with egg, vegetables, and soy sauce"),
    (4, "Hot and Sour Soup", "Spicy and tangy soup with tofu, mushrooms, and egg ribbons"),
    (4, "Peking Duck", "Roasted duck with thin pancakes, hoisin sauce, scallions, and cucumber"),

    # ─── Sakura Sushi (5) — existing 5 ──────────────────────────────────────
    (5, "Spicy Tuna Roll", "Raw tuna with spicy mayo, cucumber, and rice wrapped in nori"),
    (5, "Chicken Teriyaki", "Grilled chicken glazed with sweet soy teriyaki sauce, served with rice"),
    (5, "Miso Soup", "Traditional soup with tofu, wakame seaweed, and green onions"),
    (5, "Salmon Sashimi", "Thinly sliced raw salmon served with wasabi and pickled ginger"),
    (5, "Tempura Udon", "Thick wheat noodles in hot dashi broth topped with shrimp tempura"),

    # ─── Bombay Spice (6) — existing 5 ──────────────────────────────────────
    (6, "Chicken Tikka Masala", "Tender chicken pieces in a creamy tomato-based curry sauce with basmati rice"),
    (6, "Palak Paneer", "Fresh spinach curry with cubes of Indian cottage cheese"),
    (6, "Lamb Biryani", "Fragrant basmati rice layered with spiced lamb, saffron, and fried onions"),
    (6, "Samosa", "Crispy pastry filled with spiced potatoes and peas, served with chutney"),
    (6, "Naan Bread", "Traditional tandoor-baked flatbread brushed with butter"),

    # ─── The Grill House (7) — existing 5 ───────────────────────────────────
    (7, "Classic Cheeseburger", "Angus beef patty with cheddar, lettuce, tomato, pickle on a brioche bun"),
    (7, "BBQ Ribs", "Slow-smoked pork ribs with house BBQ sauce, coleslaw, and cornbread"),
    (7, "Grilled Salmon", "Pan-seared Atlantic salmon with lemon butter sauce and roasted asparagus"),
    (7, "Mac and Cheese", "Creamy baked macaroni with three-cheese blend and breadcrumb topping"),
    (7, "Caesar Salad", "Romaine lettuce, parmesan, croutons, and house-made caesar dressing"),

    # ─── Olive & Vine (8) — existing 5 ──────────────────────────────────────
    (8, "Greek Salad", "Tomatoes, cucumber, red onion, olives, and feta cheese with olive oil"),
    (8, "Lamb Gyro", "Seasoned lamb in warm pita with tzatziki, tomatoes, and onions"),
    (8, "Hummus Plate", "Creamy chickpea hummus with olive oil, pita bread, and vegetable crudités"),
    (8, "Grilled Halloumi", "Pan-grilled halloumi cheese with roasted peppers and mint"),
    (8, "Baklava", "Layers of phyllo dough with chopped walnuts and honey syrup"),

    # ─── Falafel King (9) — existing 5 ──────────────────────────────────────
    (9, "Falafel Wrap", "Crispy chickpea fritters with tahini, pickled vegetables in pita"),
    (9, "Shawarma Plate", "Slow-roasted seasoned chicken with garlic sauce, rice, and salad"),
    (9, "Tabbouleh", "Fresh parsley salad with bulgur wheat, tomatoes, mint, and lemon"),
    (9, "Beef Kebab", "Grilled spiced ground beef skewers with onions and sumac"),
    (9, "Kunafa", "Shredded pastry with sweet cheese filling soaked in rose water syrup"),

    # ═══════════════════════════════════════════════════════════════════════════
    # NEW ITEMS BELOW
    # ═══════════════════════════════════════════════════════════════════════════

    # ─── Bangkok Street (10) — thai ──────────────────────────────────────────
    (10, "Pad See Ew", "Wide rice noodles stir-fried with Chinese broccoli, egg, and sweet soy sauce"),
    (10, "Massaman Curry", "Rich, mild curry with tender beef, potatoes, onions, peanuts, and coconut milk"),
    (10, "Thai Spring Rolls", "Crispy fried rolls stuffed with glass noodles, cabbage, carrot, and mushrooms"),
    (10, "Larb Gai", "Spicy minced chicken salad with lime juice, fish sauce, mint, and toasted rice powder"),
    (10, "Khao Man Gai", "Poached chicken over fragrant rice cooked in chicken broth, served with ginger dipping sauce"),
    (10, "Pad Krapow", "Spicy stir-fried minced pork with holy basil, chili, and garlic over rice with fried egg"),
    (10, "Thai Papaya Salad", "Shredded green papaya with tomatoes, green beans, peanuts, lime, and fish sauce"),
    (10, "Boat Noodles", "Rich dark pork broth noodle soup with crispy pork, blood cake, and herbs"),
    (10, "Pineapple Fried Rice", "Wok-fried jasmine rice with pineapple chunks, shrimp, cashews, and raisins"),
    (10, "Crying Tiger", "Grilled marinated beef with spicy Isaan dipping sauce and fresh herbs"),

    # ─── Thai Corner (11) — thai ─────────────────────────────────────────────
    (11, "Red Curry", "Spicy red curry paste with chicken, red bell peppers, and coconut milk"),
    (11, "Panang Curry", "Thick, rich curry with beef, kaffir lime leaves, and peanuts in coconut cream"),
    (11, "Tom Kha Gai", "Creamy coconut milk soup with chicken, galangal, lemongrass, and mushrooms"),
    (11, "Som Tum", "Classic green papaya salad with dried shrimp, peanuts, chili, and lime"),
    (11, "Pad Woon Sen", "Stir-fried glass noodles with egg, vegetables, oyster sauce, and pork"),
    (11, "Thai Basil Noodles", "Flat rice noodles with fresh Thai basil, holy basil, chili, and ground chicken"),
    (11, "Satay Skewers", "Grilled pork or chicken skewers marinated in turmeric and served with peanut sauce"),
    (11, "Pandan Coconut Cake", "Light steamed cake with pandan extract and fresh grated coconut"),
    (11, "Khao Niao Mamuang", "Glutinous rice topped with sliced mango and poured coconut cream sauce"),
    (11, "Thai Fish Cake", "Seasoned ground fish mixed with red curry paste, fried into patties with sweet chili sauce"),

    # ─── Trattoria Roma (12) — italian ───────────────────────────────────────
    (12, "Cacio e Pepe", "Spaghetti tossed with aged Pecorino Romano, Parmigiano Reggiano, and freshly cracked black pepper"),
    (12, "Osso Buco", "Braised veal shanks in white wine, vegetables, and gremolata, served over saffron risotto"),
    (12, "Ribollita", "Thick Tuscan bread soup with cannellini beans, kale, tomatoes, and stale bread"),
    (12, "Grilled Branzino", "Whole sea bass roasted with lemon, capers, olive oil, and fresh herbs"),
    (12, "Arancini", "Crispy fried risotto balls stuffed with mozzarella and ragù, served with marinara"),
    (12, "Penne Arrabbiata", "Penne pasta in fiery tomato sauce with garlic, red chili flakes, and fresh parsley"),
    (12, "Insalata Caprese", "Fresh mozzarella di bufala, heirloom tomatoes, fresh basil, and aged balsamic"),
    (12, "Saltimbocca", "Pan-seared veal cutlet with prosciutto and sage in a white wine butter sauce"),
    (12, "Panna Cotta", "Silky vanilla cream dessert with fresh berry coulis and mint"),
    (12, "Focaccia", "Oven-baked dimpled flatbread with olive oil, sea salt, rosemary, and cherry tomatoes"),

    # ─── Pizza Napoli (13) — italian ─────────────────────────────────────────
    (13, "Quattro Stagioni Pizza", "Pizza divided into four sections with artichokes, ham, mushrooms, and olives"),
    (13, "Diavola Pizza", "Spicy pizza with salami piccante, roasted red peppers, and chili oil"),
    (13, "Prosciutto e Rucola Pizza", "Thin-crust pizza topped with prosciutto di Parma, arugula, and shaved Parmigiano"),
    (13, "Spaghetti alle Vongole", "Spaghetti with fresh clams, white wine, garlic, parsley, and chili flakes"),
    (13, "Gnocchi al Pesto", "Soft potato dumplings tossed in fresh Genovese basil pesto with pine nuts"),
    (13, "Lasagna Bolognese", "Layers of egg pasta with slow-cooked beef ragù, béchamel, and Parmigiano Reggiano"),
    (13, "Bruschetta al Pomodoro", "Toasted ciabatta rubbed with garlic, topped with fresh tomatoes, basil, and olive oil"),
    (13, "Cannoli", "Crispy pastry tubes filled with sweetened ricotta and chocolate chips"),
    (13, "Risotto ai Funghi", "Creamy Arborio rice with mixed wild mushrooms, white wine, and Parmigiano"),
    (13, "Eggplant Parmigiana", "Layered fried eggplant with marinara, fresh mozzarella, and Parmigiano, baked golden"),

    # ─── K-BBQ House (14) — korean ───────────────────────────────────────────
    (14, "Samgyeopsal", "Thick-cut grilled pork belly eaten wrapped in lettuce with garlic, ssamjang, and kimchi"),
    (14, "LA Galbi", "Cross-cut beef short ribs marinated in soy, pear, garlic, and sesame, grilled over charcoal"),
    (14, "Dakgalbi", "Spicy stir-fried chicken with rice cakes, cabbage, and gochujang sauce"),
    (14, "Doenjang Jjigae", "Hearty fermented soybean paste stew with tofu, zucchini, and mushrooms"),
    (14, "Haemul Pajeon", "Crispy savory pancake loaded with squid, shrimp, and scallions"),
    (14, "Gamjatang", "Spicy pork neck bone soup with potatoes, perilla seeds, and green onions"),
    (14, "Budae Jjigae", "Army stew with spam, hot dogs, kimchi, ramen noodles, and baked beans in spicy broth"),
    (14, "Tteokbokki", "Chewy rice cakes in sweet and spicy gochujang sauce with fish cakes and scallions"),
    (14, "Sundubu Jjigae", "Spicy soft tofu stew with clams, pork, and a raw egg cracked in at the end"),
    (14, "Naengmyeon", "Cold buckwheat noodles in chilled beef broth with cucumber, pear, and hard-boiled egg"),

    # ─── Bunsik Corner (15) — korean ─────────────────────────────────────────
    (15, "Gimbap", "Seaweed-wrapped rice rolls filled with spinach, egg, pickled radish, and seasoned beef"),
    (15, "Ramyeon", "Instant-style spicy Korean ramen with a soft egg, green onions, and processed cheese"),
    (15, "Twigim", "Assorted Korean street food fritters including shrimp, vegetables, and sweet potato"),
    (15, "Hotteok", "Warm sweet fried dough pancake filled with brown sugar, cinnamon, and walnuts"),
    (15, "Eomuk Guk", "Clear fish cake broth soup served with skewered fish cakes"),
    (15, "Dakbokkeumtang", "Braised spicy chicken with potatoes, carrots, and green onions in gochujang broth"),
    (15, "Kimbap Variety", "Tuna, kimchi, or shrimp kimbap rolls with various fillings wrapped in seasoned rice"),
    (15, "Sogogi Guk", "Mild beef soup with radish, glass noodles, and green onions"),
    (15, "Jokbal", "Soy-braised pig's trotters sliced thin and eaten with shrimp paste and pickled vegetables"),
    (15, "Bingsu", "Shaved ice dessert topped with sweetened red beans, condensed milk, and mochi pieces"),

    # ─── Casa Oaxaca (16) — mexican ──────────────────────────────────────────
    (16, "Tlayuda", "Large crispy tortilla topped with black bean paste, Oaxacan cheese, tasajo, and avocado"),
    (16, "Mole Negro", "Rich, complex sauce of dried chilies, chocolate, and spices over turkey with rice"),
    (16, "Tamales Oaxaqueños", "Banana leaf-wrapped corn masa stuffed with chicken and mole, steamed tender"),
    (16, "Memelitas", "Thick oval corn tortillas topped with black beans, fresh cheese, and salsa"),
    (16, "Estofado", "Sweet and savory chicken stew with green olives, capers, and tomatoes in spiced broth"),
    (16, "Chapulines Tostadas", "Crunchy toasted grasshoppers with lime, chili, and salt over crispy tostadas with guacamole"),
    (16, "Enfrijoladas", "Corn tortillas dipped in pureed black bean sauce, filled with cheese and cream"),
    (16, "Memela de Chorizo", "Thick cornmeal cake with spicy chorizo, bean paste, and fresh epazote"),
    (16, "Agua de Jamaica", "Chilled hibiscus flower drink lightly sweetened with cane sugar"),
    (16, "Chocolate Oaxaqueño", "Thick traditional Oaxacan hot chocolate with cinnamon, made with stone-ground cacao"),

    # ─── Taco Loco (17) — mexican ────────────────────────────────────────────
    (17, "Al Pastor Tacos", "Marinated pork shaved from a vertical spit, served on corn tortillas with pineapple and cilantro"),
    (17, "Carnitas Tacos", "Slow-braised pork shoulder fried crispy, served with white onion and salsa verde"),
    (17, "Barbacoa Tacos", "Slow-cooked shredded beef cheek with consommé, onion, cilantro on corn tortillas"),
    (17, "Enfrijoladas", "Corn tortillas bathed in black bean sauce with shredded chicken and crema"),
    (17, "Huarache", "Oval fried masa base topped with beans, cactus, salsa, and crumbled queso"),
    (17, "Sopa de Lima", "Yucatecan sour soup with shredded chicken, lime juice, fried tortilla strips, and cilantro"),
    (17, "Esquites", "Warm cup of corn kernels with mayo, lime, chili powder, cotija, and epazote"),
    (17, "Aguas Frescas", "Fresh fruit water made with watermelon, cantaloupe, or tamarind"),
    (17, "Gorditas", "Thick stuffed corn masa pockets filled with chicharrón, beans, and salsa"),
    (17, "Flautas", "Crispy rolled tacos filled with shredded chicken, served with guacamole and sour cream"),

    # ─── Dim Sum Palace (18) — chinese ───────────────────────────────────────
    (18, "Har Gow", "Steamed shrimp dumplings in translucent rice flour skin, served with chili oil"),
    (18, "Siu Mai", "Open-topped pork and shrimp dumplings topped with a fish roe pearl"),
    (18, "Char Siu Bao", "Fluffy steamed buns filled with sweet BBQ pork, soft and pillowy inside"),
    (18, "Cheung Fun", "Silky steamed rice rolls filled with shrimp or beef, drizzled with sweet soy sauce"),
    (18, "Lo Mai Gai", "Glutinous rice stuffed with chicken, mushrooms, and Chinese sausage, wrapped in lotus leaf"),
    (18, "Turnip Cake", "Pan-fried savory radish cake with dried shrimp, Chinese sausage, and scallions"),
    (18, "Egg Tart", "Flaky pastry shell filled with smooth silky egg custard, lightly sweet"),
    (18, "Chicken Feet", "Braised then deep-fried chicken feet in black bean garlic sauce, steamed tender"),
    (18, "Dan Dan Mian", "Noodles in spicy sesame peanut sauce with minced pork and Sichuan chili oil"),
    (18, "Wonton Soup", "Delicate pork and shrimp wontons in clear chicken broth with bok choy"),

    # ─── Sichuan House (19) — chinese ────────────────────────────────────────
    (19, "Mala Hot Pot", "Sichuan numbing and spicy broth for cooking thinly sliced meats, tofu, and vegetables"),
    (19, "Twice Cooked Pork", "Boiled then wok-fried pork belly with leeks, garlic, and doubanjiang chili bean paste"),
    (19, "Sichuan Dan Dan Noodles", "Noodles topped with minced pork in fiery sesame sauce with Sichuan peppercorn oil"),
    (19, "Spicy Boiled Fish", "Thin-sliced fish fillet in bright red Sichuan chili broth with bean sprouts and peppercorns"),
    (19, "Husband and Wife Beef", "Cold sliced beef and tendon in spicy peanut and chili oil sauce with celery"),
    (19, "Yu Xiang Pork", "Stir-fried shredded pork in sweet and sour garlic sauce with wood ear mushrooms"),
    (19, "Dry Pot Cauliflower", "Stir-fried cauliflower with pork belly, dried chilies, and fermented black beans"),
    (19, "Steamed Egg with Salted Pork", "Silky steamed egg custard topped with minced salted pork and soy sauce"),
    (19, "Chongqing Chicken", "Crispy diced chicken buried under a mound of dried red chilies and Sichuan peppercorns"),
    (19, "Braised Pork Belly Dongpo", "Thick square of pork belly slow-braised in soy, rice wine, and sugar until meltingly tender"),

    # ─── Ramen House (20) — japanese ─────────────────────────────────────────
    (20, "Tonkotsu Ramen", "Rich creamy pork bone broth with chashu pork, soft egg, bamboo shoots, and nori"),
    (20, "Shoyu Ramen", "Clear soy-seasoned chicken broth with wavy noodles, chashu, and menma"),
    (20, "Miso Ramen", "Hearty Hokkaido-style miso broth with corn, butter, ground pork, and bean sprouts"),
    (20, "Spicy Tantanmen", "Japanese sesame peanut ramen with spicy ground pork and chili oil"),
    (20, "Tsukemen", "Thick noodles dipped into concentrated rich pork-dashi dipping broth"),
    (20, "Gyoza", "Pan-fried pork and cabbage dumplings, crispy-bottomed and juicy inside"),
    (20, "Karaage", "Japanese fried chicken marinated in soy and ginger, served with lemon and kewpie mayo"),
    (20, "Takoyaki", "Grilled octopus balls with tenkasu, bonito flakes, mayo, and Worcestershire sauce"),
    (20, "Chashu Don", "Slow-braised soy pork belly slices over steamed rice with pickled ginger"),
    (20, "Tamagoyaki", "Rolled Japanese omelette seasoned with dashi and mirin, slightly sweet"),

    # ─── Izakaya Yoshi (21) — japanese ───────────────────────────────────────
    (21, "Yakitori", "Skewered chicken thighs, skin, or hearts grilled over charcoal with tare sauce"),
    (21, "Edamame", "Steamed salted young soybeans in the pod"),
    (21, "Agedashi Tofu", "Lightly battered silken tofu in savory dashi broth with grated daikon and ginger"),
    (21, "Tonkatsu", "Crispy panko-breaded pork cutlet with tonkatsu sauce and finely shredded cabbage"),
    (21, "Okonomiyaki", "Savory Japanese pancake with cabbage, pork, and seafood topped with mayo and bonito"),
    (21, "Ebi Tempura", "Crispy light-battered prawns with tentsuyu dipping sauce and grated daikon"),
    (21, "Natto with Rice", "Fermented soybeans with pungent aroma served over sticky rice with mustard and soy"),
    (21, "Uni Gunkan", "Battleship sushi topped with fresh sea urchin roe and soy sauce"),
    (21, "Mochi Ice Cream", "Soft mochi rice cake wrapped around green tea, red bean, or sesame ice cream"),
    (21, "Ryu Ramen Noir", "Squid ink ramen broth with seafood, nori, and black garlic oil"),

    # ─── Curry Club (22) — indian ────────────────────────────────────────────
    (22, "Butter Chicken", "Tender tandoor-roasted chicken in mild, creamy tomato butter sauce with basmati rice"),
    (22, "Dal Makhani", "Black lentils slow-cooked overnight with butter, cream, and aromatic spices"),
    (22, "Aloo Gobi", "Dry spiced cauliflower and potato dish with turmeric, cumin, and fresh coriander"),
    (22, "Chana Masala", "Hearty chickpea curry in tangy spiced tomato gravy with cumin and amchur"),
    (22, "Malai Kofta", "Soft paneer and potato dumplings in rich cream and cashew sauce"),
    (22, "Rogan Josh", "Slow-braised Kashmiri lamb curry with whole spices, Kashmiri chili, and yogurt"),
    (22, "Mutter Paneer", "Peas and fresh cheese cubes in spiced tomato and onion curry sauce"),
    (22, "Lassi", "Yogurt-based drink served sweet with mango or salty with cumin and mint"),
    (22, "Gulab Jamun", "Soft milk solid dumplings soaked in rose water and saffron sugar syrup"),
    (22, "Raita", "Cool yogurt condiment with cucumber, cumin, and fresh cilantro"),

    # ─── Tandoor Palace (23) — indian ────────────────────────────────────────
    (23, "Tandoori Mixed Grill", "Assorted marinated meats including seekh kebab, boti kebab, and chicken tikka cooked in clay oven"),
    (23, "Chicken Tikka", "Boneless chicken marinated in yogurt and spices, grilled in tandoor until charred"),
    (23, "Seekh Kebab", "Minced spiced lamb shaped around skewers and grilled in tandoor, served with chutney"),
    (23, "Saag Chicken", "Shredded spiced chicken in pureed mustard greens and spinach with ginger"),
    (23, "Fish Amritsari", "Spicy fish fillets battered in chickpea flour with carom seeds, fried crispy"),
    (23, "Prawn Masala", "Jumbo prawns in tangy onion tomato masala with coastal spices and coconut"),
    (23, "Kulcha", "Leavened flatbread stuffed with spiced potato or paneer, baked in tandoor"),
    (23, "Phirni", "Chilled creamy ground rice pudding with saffron and cardamom, served in clay pots"),
    (23, "Kheer", "Slow-cooked rice pudding with whole milk, cardamom, saffron, and crushed pistachios"),
    (23, "Shahi Paneer", "Paneer in rich saffron cream and almond sauce with whole aromatic spices"),

    # ─── Smokehouse BBQ (24) — american ──────────────────────────────────────
    (24, "Smoked Brisket", "18-hour oak-smoked beef brisket with bark crust, served with pickles and white bread"),
    (24, "Pulled Pork Sandwich", "Slow-smoked pork shoulder on a brioche bun with vinegar slaw and house BBQ sauce"),
    (24, "Baby Back Ribs Rack", "Full rack of hickory-smoked pork ribs with dry rub and sweet molasses BBQ glaze"),
    (24, "Smoked Turkey Leg", "Giant carnival-style smoked turkey leg with honey glaze and charred edges"),
    (24, "Burnt Ends", "Caramelized fatty beef brisket point cubes sauced and re-smoked for tender bark"),
    (24, "Baked Beans", "Slow-cooked navy beans with smoked pork, molasses, brown sugar, and jalapeño"),
    (24, "Jalapeño Cheddar Sausage", "Handmade smoked sausage links with pickled jalapeño and sharp cheddar"),
    (24, "Smoked Wings", "Whole chicken wings smoked low and slow, finished on grill with buffalo or dry rub"),
    (24, "Pit Beans Combo", "Pulled pork, brisket, and burnt ends over white rice with Carolina vinegar sauce"),
    (24, "Peach Cobbler", "Warm cinnamon-spiced peach cobbler with buttery biscuit topping and vanilla ice cream"),

    # ─── Diner Classic (25) — american ───────────────────────────────────────
    (25, "Pancakes Stack", "Fluffy buttermilk pancakes served with maple syrup, butter, and fresh berries"),
    (25, "Eggs Benedict", "Poached eggs on Canadian bacon and toasted English muffin with hollandaise sauce"),
    (25, "Club Sandwich", "Triple-decker toasted white bread with turkey, bacon, lettuce, tomato, and mayo"),
    (25, "Patty Melt", "Smashed beef patty on rye bread with caramelized onions and Swiss cheese"),
    (25, "French Dip", "Thin-sliced roast beef on a hoagie roll served with rich beef au jus for dipping"),
    (25, "Meatloaf", "Classic ground beef and pork loaf with ketchup glaze, mashed potatoes, and green beans"),
    (25, "Chicken Fried Steak", "Breaded cube steak fried golden with cream gravy and mashed potatoes"),
    (25, "Milkshake", "Thick hand-spun shake in chocolate, vanilla, or strawberry with whipped cream"),
    (25, "Apple Pie", "Double-crust spiced apple pie served warm with a scoop of vanilla ice cream"),
    (25, "Reuben Sandwich", "Corned beef, Swiss, sauerkraut, and Thousand Island dressing on grilled rye"),

    # ─── The Burger Lab (26) — american ──────────────────────────────────────
    (26, "Smash Burger", "Thin smash-griddled patty with American cheese, raw onion, pickles, and special sauce"),
    (26, "Double Wagyu Burger", "Two Wagyu beef patties with aged cheddar, truffle aioli, and crispy shallots"),
    (26, "Mushroom Swiss Burger", "Beef patty with sautéed cremini mushrooms, Swiss cheese, and garlic herb mayo"),
    (26, "BBQ Bacon Burger", "Beef patty with thick-cut bacon, onion rings, BBQ sauce, and cheddar"),
    (26, "Veggie Beyond Burger", "Beyond Meat patty with avocado, arugula, sun-dried tomato mayo, and vegan cheese"),
    (26, "Truffle Fries", "Hand-cut fries tossed in truffle oil, Parmigiano, and fresh parsley"),
    (26, "Onion Rings", "Thick-cut beer-battered onion rings with buttermilk ranch dipping sauce"),
    (26, "Loaded Nachos", "Tortilla chips topped with beef chili, jalapeños, three-cheese sauce, and sour cream"),
    (26, "Chicken Sandwich", "Crispy fried chicken thigh with pickles, coleslaw, and honey hot sauce on a potato bun"),
    (26, "Lobster Roll", "Cold Maine lobster salad with light mayo and chives in a toasted split-top bun"),

    # ─── Mezze Bar (27) — mediterranean ──────────────────────────────────────
    (27, "Spanakopita", "Flaky phyllo pastry triangles filled with spinach, feta cheese, and fresh dill"),
    (27, "Grilled Octopus", "Charred whole octopus tentacle with lemon, capers, olive oil, and smoked paprika"),
    (27, "Moussaka", "Baked layered eggplant, spiced ground lamb, and béchamel with cinnamon and nutmeg"),
    (27, "Dolmades", "Grape leaves stuffed with lemony herbed rice and minced lamb, served with yogurt"),
    (27, "Tzatziki Dip", "Thick Greek yogurt with grated cucumber, garlic, dill, and lemon, served with pita"),
    (27, "Souvlaki Plate", "Pork or chicken skewers marinated in lemon and oregano, served with pita and salad"),
    (27, "Saganaki", "Pan-seared kefalograviera cheese flamed with ouzo, served sizzling with lemon"),
    (27, "Pastitsio", "Greek baked pasta with spiced meat sauce and thick béchamel, similar to lasagna"),
    (27, "Revithada", "Slow-baked chickpeas with rosemary, lemon zest, and olive oil on clay pot"),
    (27, "Galaktoboureko", "Custard-filled phyllo pastry soaked in citrus syrup and dusted with powdered sugar"),

    # ─── Aegean Kitchen (28) — mediterranean ──────────────────────────────────
    (28, "Horiatiki Salad", "Chunky village salad with ripe tomatoes, cucumber, pepper, onion, olives, and a slab of feta"),
    (28, "Grilled Swordfish", "Mediterranean swordfish steak with lemon herb caper sauce and grilled vegetables"),
    (28, "Pita with Skordalia", "Toasted pita bread served with garlicky potato and almond dip"),
    (28, "Lamb Kleftiko", "Slow-baked lamb with potatoes, garlic, herbs, wrapped and steamed in parchment"),
    (28, "Fasolada", "White bean soup with carrots, tomatoes, celery, and olive oil — Greek national dish"),
    (28, "Borek", "Thin crispy pastry rolls filled with feta and parsley or spiced ground beef"),
    (28, "Avgolemono Soup", "Silky egg-lemon chicken soup with orzo, creamy without cream"),
    (28, "Strapatsada", "Scrambled eggs with ripe tomatoes, feta crumbles, and fresh oregano"),
    (28, "Loukoumades", "Greek honey puffs drizzled with thyme honey, cinnamon, and crushed walnuts"),
    (28, "Taramasalata", "Blended fish roe dip with olive oil, lemon, and soaked bread, served with pita"),

    # ─── Shawarma Republic (29) — middle_eastern ─────────────────────────────
    (29, "Chicken Shawarma Wrap", "Spiced rotisserie chicken with garlic toum, pickled turnips, and parsley in flatbread"),
    (29, "Beef Shawarma Plate", "Slow-roasted spiced beef slices with tahini, tomatoes, onion, and fries"),
    (29, "Fattoush Salad", "Chopped lettuce, tomato, radish, and cucumber with toasted pita and sumac vinaigrette"),
    (29, "Manakeesh", "Flatbread topped with za'atar and olive oil, or seasoned ground beef with tomato"),
    (29, "Kibbeh", "Fried bulgur shells stuffed with spiced ground lamb, onion, and pine nuts"),
    (29, "Lentil Soup", "Thick pureed red lentil soup with cumin, lemon, and fried onions garnish"),
    (29, "Baba Ganoush", "Smoky roasted eggplant dip blended with tahini, garlic, and lemon juice"),
    (29, "Muhammara", "Roasted red pepper and walnut dip spiced with Aleppo pepper and pomegranate molasses"),
    (29, "Knafeh", "Cheese-filled shredded phyllo soaked in sweet orange blossom syrup with crushed pistachios"),
    (29, "Jallab", "Chilled rose water drink with grape juice, tamarind, and pine nuts"),

    # ─── Levant Table (30) — middle_eastern ──────────────────────────────────
    (30, "Mezze Platter", "Assorted spreads with hummus, baba ganoush, labneh, stuffed grape leaves, and pita"),
    (30, "Lamb Ouzi", "Whole slow-roasted lamb shoulder over vermicelli rice with nuts and spices"),
    (30, "Mujadara", "Caramelized onion lentil rice pilaf topped with crispy fried shallots and yogurt"),
    (30, "Freekeh Soup", "Green wheat grain soup with shredded chicken, cinnamon, and fried pine nuts"),
    (30, "Kafta Bil Saniyeh", "Baked ground beef patties with sliced tomatoes, onion, and tahini in a tray"),
    (30, "Shish Taouk", "Marinated chicken cubes grilled on skewers with garlic sauce and pickles"),
    (30, "Fatayer", "Baked triangular pastries stuffed with spiced lamb, spinach, or cheese"),
    (30, "Labneh Plate", "Strained yogurt cheese balls rolled in za'atar and olive oil with olives and tomatoes"),
    (30, "Mamoul", "Semolina shortbread cookies stuffed with date paste, walnuts, or pistachios"),
    (30, "Ayran", "Chilled savory yogurt drink whipped with water and a pinch of salt"),

    # ─── Fusion Kitchen (31) — other ─────────────────────────────────────────
    (31, "Korean BBQ Tacos", "Bulgogi beef in corn tortillas with kimchi slaw, gochujang aioli, and sesame seeds"),
    (31, "Miso Ramen Burger", "Beef patty served in a ramen noodle bun with miso glaze and pickled daikon"),
    (31, "Thai Curry Pizza", "Thin-crust pizza with green curry sauce, chicken, Thai basil, and coconut cream drizzle"),
    (31, "Kimchi Grilled Cheese", "Sourdough with aged cheddar, kimchi, and gochujang butter, griddled crispy"),
    (31, "Banh Mi Cheesesteak", "Vietnamese-style hoagie with Philly cheesesteak filling, pickled daikon, and jalapeños"),
    (31, "Matcha Tiramisu", "Italian tiramisu with matcha powder instead of espresso, mascarpone and green tea"),
    (31, "Masala Fish and Chips", "Beer-battered fish with curry spice blend, served with turmeric fries and mango chutney"),
    (31, "Sushi Burrito", "Giant hand roll-style burrito with spicy tuna, avocado, cucumber, and sesame"),
    (31, "Pho French Onion Soup", "Deep beefy pho broth base topped with caramelized onions and a broiled gruyere crouton"),
    (31, "Black Sesame Cheesecake", "New York-style cheesecake with black sesame paste swirled into creamy filling"),

    # ─── Street Bites (32) — other ────────────────────────────────────────────
    (32, "Loaded Fries", "Crispy fries piled with cheddar cheese sauce, sour cream, bacon bits, and jalapeños"),
    (32, "Acai Bowl", "Frozen acai smoothie base topped with granola, banana, blueberries, and honey"),
    (32, "Avocado Toast", "Sourdough with smashed avocado, everything bagel seasoning, lemon zest, and poached egg"),
    (32, "Chicken Caesar Wrap", "Grilled chicken, romaine, Parmigiano, and caesar dressing in a flour tortilla"),
    (32, "Quinoa Power Bowl", "Roasted vegetables, quinoa, chickpeas, and tahini dressing with pumpkin seeds"),
    (32, "Buffalo Cauliflower", "Crispy roasted cauliflower florets tossed in buffalo sauce with blue cheese dip"),
    (32, "Poke Bowl", "Hawaiian tuna poke over sushi rice with avocado, edamame, cucumber, and ponzu"),
    (32, "Shakshuka", "Eggs poached in spiced tomato and red pepper sauce with feta and crusty bread"),
    (32, "Smoked Salmon Bagel", "Toasted everything bagel with cream cheese, smoked salmon, capers, and red onion"),
    (32, "Croissant Sandwich", "Buttery croissant with ham, Swiss cheese, Dijon mustard, and cornichons"),

    # ─── Bangkok Street (10) — thai, extra ───────────────────────────────────
    (10, "Nam Tok", "Grilled beef salad with toasted rice powder, lime, fish sauce, shallots, and mint"),
    (10, "Khao Soi", "Northern Thai coconut curry noodle soup with braised chicken and crispy noodles on top"),
    (10, "Yam Woon Sen", "Glass noodle salad with minced pork, shrimp, lime dressing, and chili"),
    (10, "Pad Prik King", "Dry stir-fry of green beans and pork with red curry paste and kaffir lime leaves"),
    (10, "Gai Tod", "Crispy deep-fried whole chicken marinated in lemongrass and fish sauce"),
    (10, "Tom Kloang Pla", "Smoky dried fish soup with tamarind broth and fresh dill"),
    (10, "Khao Tom", "Thai rice porridge with minced pork, ginger, and century egg"),
    (10, "Sai Oua", "Northern Thai grilled pork sausage with lemongrass, galangal, and kaffir lime"),
    (10, "Pad Phed Moo Pa", "Jungle curry stir-fry with wild boar, krachai fingerroot, green peppercorns"),
    (10, "Kanom Krok", "Crispy-edged coconut rice pancakes with sweet or savory fillings, hot from cast iron"),

    # ─── Thai Corner (11) — thai, extra ──────────────────────────────────────
    (11, "Laab Moo", "Spicy minced pork salad with toasted rice powder, fish sauce, lime, and fresh herbs"),
    (11, "Khao Na Ped", "Rice topped with roasted duck and red gravy, pickled mustard greens on the side"),
    (11, "Tom Saap", "Spicy lemongrass pork rib soup with galangal, lime, and fresh chili"),
    (11, "Pad Kra Pao Moo Krob", "Crispy pork belly stir-fried with holy basil, oyster sauce, and bird chilies"),
    (11, "Geng Keow Wan Gai", "Authentic green chicken curry with round Thai eggplants and sweet basil"),
    (11, "Yam Pla Duk Fu", "Crispy catfish floss salad with green mango, lime dressing, and shallots"),
    (11, "Khao Pad Sapparot", "Pineapple fried rice with cashews, raisins, turmeric, and dried shrimp"),
    (11, "Gaeng Massaman Gai", "Mild Muslim-style chicken curry with cinnamon, cardamom, potatoes, and peanuts"),
    (11, "Wun Sen Pad", "Cellophane noodle stir-fry with egg, tomato, onion, and oyster sauce"),
    (11, "Bua Loy", "Glutinous rice flour balls in warm pandan coconut milk dessert soup"),

    # ─── Trattoria Roma (12) — italian, extra ─────────────────────────────────
    (12, "Vitello Tonnato", "Cold thinly sliced veal covered in creamy tuna and caper sauce"),
    (12, "Tagliatelle al Ragù", "Egg pasta ribbons in slow-cooked Bolognese meat sauce with Parmigiano"),
    (12, "Polenta e Funghi", "Creamy soft polenta topped with wild mushroom ragù and Gorgonzola"),
    (12, "Acquacotta", "Tuscan peasant soup of stale bread, eggs, kale, and tomato with Pecorino"),
    (12, "Abbacchio alla Romana", "Slow-braised milk-fed lamb with garlic, anchovy, rosemary, and white wine"),
    (12, "Stracciatella", "Roman egg-drop soup with clear chicken broth, Parmigiano, and nutmeg"),
    (12, "Coda alla Vaccinara", "Roman oxtail stew with celery, tomato, pine nuts, raisins, and bitter cocoa"),
    (12, "Supplì al Telefono", "Fried risotto balls with a stretchy mozzarella center, Rome street food classic"),
    (12, "Torta della Nonna", "Shortcrust pastry tart filled with lemon custard and topped with pine nuts and powdered sugar"),
    (12, "Salmoriglio Branzino", "Grilled sea bass fillets with Sicilian salmoriglio sauce of lemon, olive oil, oregano"),

    # ─── Pizza Napoli (13) — italian, extra ──────────────────────────────────
    (13, "Puttanesca Spaghetti", "Spaghetti with tomatoes, olives, capers, anchovies, garlic, and chili flakes"),
    (13, "Calzone Napoletano", "Folded pizza dough stuffed with ricotta, salami, and mozzarella, baked in wood oven"),
    (13, "Ravioli al Burro e Salvia", "Ricotta-stuffed pasta in brown butter and fresh sage with Parmigiano"),
    (13, "Pasta e Fagioli", "Thick Neapolitan pasta and cannellini bean soup with rosemary and guanciale"),
    (13, "Linguine alle Vongole", "Linguine with Manila clams, white wine, garlic, parsley, and chili"),
    (13, "Pollo alla Cacciatora", "Hunter-style braised chicken with tomatoes, olives, capers, rosemary, and white wine"),
    (13, "Melanzane alla Parmigiana", "Classic baked eggplant with tomato, basil, and oozy mozzarella — Neapolitan style"),
    (13, "Sfogliatella", "Shell-shaped flaky pastry filled with citrus-scented ricotta and candied orange peel"),
    (13, "Rigatoni all'Amatriciana", "Rigatoni in guanciale and pecorino tomato sauce with chili flakes — Roman classic"),
    (13, "Zabaglione", "Warm whipped egg yolk custard with Marsala wine, served with savoiardi biscuits"),

    # ─── K-BBQ House (14) — korean, extra ────────────────────────────────────
    (14, "Chadolbaegi", "Paper-thin sliced beef brisket grilled at the table, dipped in sesame oil and salt"),
    (14, "Dwaeji Galbi", "Grilled pork spare ribs marinated in sweet soy and garlic over charcoal"),
    (14, "Sogogi Muchim", "Spicy cold beef salad with cucumber, gochugaru, and sesame oil"),
    (14, "Suyuk", "Boiled pork belly slices served with fermented shrimp paste and garlic in lettuce"),
    (14, "Yukgaejang", "Fiery shredded beef and scallion soup with gochugaru, fernbrake, and glass noodles"),
    (14, "Galbitang", "Clear beef short rib soup with daikon and glass noodles, gently simmered for hours"),
    (14, "Hobakjuk", "Smooth pumpkin porridge lightly sweetened with rice balls and pine nut garnish"),
    (14, "Sigeumchi Namul", "Blanched spinach seasoned with sesame oil, garlic, and soy as a banchan side"),
    (14, "Pajeon", "Thin crispy scallion pancakes served with soy dipping sauce and sesame seeds"),
    (14, "Baechu Kimchi", "Freshly made whole leaf napa cabbage kimchi with gochugaru, fish sauce, and ginger"),

    # ─── Bunsik Corner (15) — korean, extra ──────────────────────────────────
    (15, "Soondae", "Korean blood sausage stuffed with glass noodles and pork, served with liver and salt"),
    (15, "Gunmandu", "Pan-fried pork and tofu dumplings, crispy on one side, served with soy vinegar dip"),
    (15, "Odeng Bokkeum", "Stir-fried fish cake strips with green onions, sesame, and gochugaru"),
    (15, "Rabokki", "Ramen noodles added to tteokbokki sauce with fish cakes and a soft egg"),
    (15, "Yubuchobap", "Seasoned rice stuffed inside sweet inari tofu pockets"),
    (15, "Dak Gangjeong", "Sweet and crispy Korean fried chicken bites in soy garlic or honey butter glaze"),
    (15, "Kimchi Bokkeum Bap", "Fried rice made with aged kimchi, spam, egg, and sesame oil"),
    (15, "Kongguksu", "Chilled noodles in cold blended soybean broth, served in summer"),
    (15, "Jeon Variety", "Assorted Korean pancakes including kimchi, seafood, and zucchini with dipping sauce"),
    (15, "Sikhye", "Sweet cold rice punch dessert drink with malt barley, garnished with pine nuts"),

    # ─── Casa Oaxaca (16) — mexican, extra ───────────────────────────────────
    (16, "Tetela", "Triangular masa pocket filled with black bean paste and Oaxacan cheese, griddle-cooked"),
    (16, "Tasajo", "Dry-cured thinly sliced beef from Oaxaca, grilled over charcoal"),
    (16, "Coloradito Mole", "Earthy red mole with dried mulato and ancho chilies over grilled pork ribs"),
    (16, "Quesillo Quesadilla", "Hand-pressed masa quesadilla with stretchy Oaxacan string cheese and epazote"),
    (16, "Empanadas de Amarillo", "Folded masa pockets filled with chicken in yellow mole, cooked on a comal"),
    (16, "Caldo de Guías", "Summer squash and corn tendril broth soup with black bean dumplings"),
    (16, "Tostadas de Chapulines", "Fried tostadas with refried beans, grasshoppers, avocado, and salsa roja"),
    (16, "Tejate", "Ancient Oaxacan drink made from cacao, corn, and mamey seed, served cold"),
    (16, "Pan de Yema", "Traditional Oaxacan egg-yolk bread slightly sweet, eaten with hot chocolate"),
    (16, "Garnachas", "Small oval masa cakes topped with black bean paste, shredded beef, and salsa"),

    # ─── Taco Loco (17) — mexican, extra ─────────────────────────────────────
    (17, "Birria Tacos", "Braised chili-spiced beef tacos dipped in consommé and griddle-fried until crispy"),
    (17, "Nopales con Huevo", "Scrambled eggs with diced cactus paddles, tomato, jalapeño, and epazote"),
    (17, "Tamales Rojos", "Corn masa stuffed with pork in red guajillo chili sauce, steamed in corn husks"),
    (17, "Pozole Rojo", "Hearty hominy stew with pork, dried chilies, and garnished with cabbage, radish, and lime"),
    (17, "Enchiladas Verdes", "Corn tortillas filled with chicken, smothered in tomatillo salsa verde and cream"),
    (17, "Taquitos Dorados", "Rolled and deep-fried tortillas filled with seasoned mashed potato or chicken"),
    (17, "Agua de Tamarindo", "Tart tamarind fruit water sweetened with piloncillo sugar"),
    (17, "Molcajete de Carne", "Stone mortar dish of sizzling grilled meats, cactus, cheese, and salsa"),
    (17, "Sopa de Fideo", "Short vermicelli noodles toasted then simmered in tomato broth with epazote"),
    (17, "Chiles Rellenos", "Poblano peppers stuffed with cheese or picadillo, battered in egg and fried"),

    # ─── Dim Sum Palace (18) — chinese, extra ────────────────────────────────
    (18, "Xiao Long Bao", "Delicate soup dumplings filled with pork and gelatinized broth, steamed in bamboo"),
    (18, "Char Siu So", "Flaky puff pastry buns filled with sweet honey BBQ pork, baked golden"),
    (18, "Taro Dumpling", "Crispy net-patterned wu gok dumpling with taro shell and minced pork filling"),
    (18, "Steamed Pork Ribs", "Black bean garlic steamed pork spare rib segments, tender and savory"),
    (18, "Scallop Dumpling", "Translucent shrimp and scallop dumpling topped with flying fish roe"),
    (18, "Chive Dumpling", "Steamed green dumpling with Chinese chives, shrimp, and pork — vibrant and fresh"),
    (18, "Pan-Fried Turnip Cake", "Crispy golden slabs of radish cake with XO sauce and dried shrimp"),
    (18, "Sesame Ball", "Deep-fried glutinous rice ball coated in sesame seeds with lotus paste inside"),
    (18, "Mango Pudding", "Silky Hong Kong-style mango pudding with evaporated milk and fresh mango cubes"),
    (18, "Congee with Century Egg", "Silky rice porridge with preserved egg and shredded salted pork"),

    # ─── Sichuan House (19) — chinese, extra ─────────────────────────────────
    (19, "Sichuan Cold Noodles", "Room-temperature wheat noodles in numbing sesame peanut sauce with cucumber"),
    (19, "Tea-Smoked Duck", "Sichuan-style duck smoked over tea leaves and camphor, crispy skin and tender meat"),
    (19, "Steamed Fish with Doubanjiang", "Whole steamed fish covered in spicy fermented chili bean paste and ginger"),
    (19, "Suan Cai Yu", "Poached fish fillets in sour pickled mustard green broth with chili oil"),
    (19, "Fuqi Feipian", "Thinly sliced beef shank and tripe in aromatic spicy sauce with celery"),
    (19, "Mao Xue Wang", "Spicy hot pot of duck blood, tripe, and spam in red chili broth"),
    (19, "Kung Pao Tofu", "Crispy tofu cubes with peanuts, dried chili, and Sichuan peppercorn stir-fry"),
    (19, "Sichuan Braised Beef Noodles", "Slow-braised beef in spicy bean paste broth over thick wheat noodles"),
    (19, "La Zi Ji", "Chongqing whole chicken pieces fried with vast quantities of dried red chilies"),
    (19, "Huang Men Ji", "Braised whole chicken with potatoes, flat noodles, and spicy black bean sauce"),

    # ─── Ramen House (20) — japanese, extra ──────────────────────────────────
    (20, "Abura Soba", "Soupless ramen with concentrated tare, lard, and toppings tossed at the table"),
    (20, "Mazemen", "Brothless ramen mixed with rich sesame paste, chili oil, and pork minced"),
    (20, "Kare Ramen", "Japanese curry ramen broth with chashu, corn, and a pat of butter"),
    (20, "Shio Ramen", "Clear and delicate salt-seasoned broth with chicken, seabream, and fine noodles"),
    (20, "Vegetable Tsukemen", "Thick noodles dipped in rich vegetable dashi broth with mushrooms and kombu"),
    (20, "Yakibuta Don", "Wok-charred chashu pork slices over steamed rice with scallions and tare"),
    (20, "Edamame Gyoza", "Pan-fried dumplings filled with edamame, tofu, and shiso — vegetarian"),
    (20, "Negi Shio Ramen", "Shio broth ramen topped with mounds of salted chopped scallions and yuzu"),
    (20, "Mentaiko Onigiri", "Rice ball filled with spicy marinated pollock roe wrapped in toasted nori"),
    (20, "Karaage Don", "Japanese fried chicken thighs over rice with egg scramble and tare"),

    # ─── Izakaya Yoshi (21) — japanese, extra ────────────────────────────────
    (21, "Hamachi Kama", "Yellowtail collar grilled with salt and lemon — fatty, smoky, and delicate"),
    (21, "Yaki Onigiri", "Grilled rice balls brushed with soy sauce and mirin until caramelized"),
    (21, "Mentaiko Pasta", "Spaghetti tossed in spicy pollock roe butter with nori and shiso"),
    (21, "Tofu Dengaku", "Firm tofu skewered and coated in sweet miso, grilled until caramelized"),
    (21, "Sashimi Moriawase", "Chef's selection of five seasonal fish sliced thin with wasabi and pickled ginger"),
    (21, "Chawanmushi", "Silky savory egg custard steamed with shrimp, ginkgo, and mitsuba"),
    (21, "Daikon Salad", "Thin daikon shreds with sesame dressing, bonito flakes, and soy sauce"),
    (21, "Buta Kakuni", "Slow-braised Okinawan pork belly in soy, mirin, and sake — melting tender"),
    (21, "Yakitori Negima", "Chicken thigh and scallion skewers grilled over binchōtan charcoal"),
    (21, "Hojicha Panna Cotta", "Creamy roasted green tea panna cotta with caramel and toasted sesame"),

    # ─── Curry Club (22) — indian, extra ─────────────────────────────────────
    (22, "Kadai Paneer", "Paneer cooked with bell peppers in aromatic kadai spice blend and tomato"),
    (22, "Baingan Bharta", "Flame-roasted eggplant mash with onions, tomatoes, ginger, and fresh coriander"),
    (22, "Pav Bhaji", "Spiced mixed vegetable mash served with buttered dinner rolls and chopped onion"),
    (22, "Chole Bhature", "Spicy chickpea curry with giant deep-fried puffy bread, pickled onion, and mango pickle"),
    (22, "Keema Matar", "Spiced minced lamb with green peas in tomato-onion gravy, eaten with paratha"),
    (22, "Dahi Vada", "Lentil dumplings soaked in cool yogurt with tamarind chutney and cumin"),
    (22, "Halwa", "Slow-cooked semolina dessert with ghee, cardamom, cashews, and raisins"),
    (22, "Aloo Paratha", "Whole-wheat flatbread stuffed with spiced mashed potato, served with curd and butter"),
    (22, "Methi Chicken", "Tender chicken curry with fresh fenugreek leaves and cream — mildly bitter and aromatic"),
    (22, "Ras Malai", "Soft paneer discs poached in milk, served in chilled cardamom rose water cream"),

    # ─── Tandoor Palace (23) — indian, extra ─────────────────────────────────
    (23, "Murgh Malai Tikka", "Cashew and cream-marinated chicken tikka with mild spices, cooked in tandoor"),
    (23, "Lamb Chops Masala", "Marinated lamb chops in spicy yogurt, grilled in tandoor and finished with chaat masala"),
    (23, "Achari Paneer Tikka", "Paneer marinated in pickling spices and mustard, charred in clay oven"),
    (23, "Daal Baati Churma", "Rajasthani baked wheat balls with five-lentil daal and sweet churma crumble"),
    (23, "Sarson ka Saag", "Slow-cooked mustard greens with butter, served with makki roti corn flatbread"),
    (23, "Nalli Gosht", "Slow-braised lamb shanks in whole spice gravy, meat falling off the bone"),
    (23, "Paratha Basket", "Assorted stuffed breads: aloo, gobi, mooli with fresh-churned butter"),
    (23, "Kulfi", "Dense Indian ice cream with cardamom, pistachios, and saffron on a stick"),
    (23, "Rasmalai Cheesecake", "Fusion dessert with rasmalai cream cheese filling and cardamom crust"),
    (23, "Masala Chai", "Spiced black tea brewed with ginger, cardamom, cinnamon, and steamed milk"),

    # ─── Smokehouse BBQ (24) — american, extra ───────────────────────────────
    (24, "Smoked Mac and Cheese", "Three-cheese mac with smoked Gouda, cheddar, gruyere, and burnt brisket pieces"),
    (24, "Collard Greens", "Slow-braised collard greens with smoked ham hock, apple cider vinegar, and sugar"),
    (24, "Smoked Sausage Po Boy", "Louisiana-style smoked andouille on hoagie with remoulade, pickles, and jalapeños"),
    (24, "Texas Chili", "No-bean beef chili with dried ancho and guajillo chilies, slow-cooked and thick"),
    (24, "Pit Chicken Quarters", "Whole leg quarters smoked low and slow with vinegar-based Alabama white sauce"),
    (24, "Smoked Corn on the Cob", "Hickory-smoked corn with garlic butter, cotija, and ancho chili powder"),
    (24, "Pork Belly Burnt Ends", "Cubed pork belly smoked and then caramelized in Kansas City glaze"),
    (24, "Loaded Baked Potato", "Twice-baked potato with pulled pork, cheddar, sour cream, and bacon bits"),
    (24, "Banana Pudding", "Layered vanilla wafer, banana, and whipped cream pudding cups"),
    (24, "Sweet Tea", "Southern-style heavily sweetened black iced tea with lemon wedge"),

    # ─── Diner Classic (25) — american, extra ────────────────────────────────
    (25, "Breakfast Burrito", "Scrambled eggs, sausage, hash brown, cheese, and salsa in a flour tortilla"),
    (25, "BLT Sandwich", "Thick-cut applewood bacon, iceberg lettuce, heirloom tomato, and mayo on sourdough"),
    (25, "Tuna Melt", "Tuna salad with cheddar on grilled rye bread, served with pickle and chips"),
    (25, "Pot Roast", "Slow-braised chuck roast with carrots, potatoes, and onion gravy"),
    (25, "Biscuits and Gravy", "Fluffy buttermilk biscuits smothered in peppered pork sausage gravy"),
    (25, "Banana Cream Pie", "Custard and fresh banana pie in graham cracker crust with whipped cream"),
    (25, "Denver Omelette", "Three-egg omelette with diced ham, green pepper, onion, and Swiss cheese"),
    (25, "Chili Dog", "All-beef hot dog topped with Texas chili, cheddar, and pickled jalapeños"),
    (25, "Hash Brown Skillet", "Crispy potato hash with peppers, onion, and eggs cooked to order"),
    (25, "Cherry Pie", "Double-crust lattice cherry pie with tart Montmorency cherries and vanilla ice cream"),

    # ─── The Burger Lab (26) — american, extra ───────────────────────────────
    (26, "Black Bean Burger", "House-made black bean and oat patty with chipotle mayo, avocado, and pickled onions"),
    (26, "Breakfast Burger", "Beef patty with fried egg, bacon, American cheese, and sriracha aioli"),
    (26, "Korean Burger", "Beef patty with kimchi, gochujang glaze, pickled daikon, and sesame brioche"),
    (26, "Pimento Cheese Burger", "Smash patty topped with housemade pimento cheese spread and pickled green tomato"),
    (26, "Animal Style Fries", "Fries with cheese sauce, griddled onions, and thousand island dressing"),
    (26, "Fried Chicken Sandwich Deluxe", "Buttermilk fried thigh with comeback sauce, bread and butter pickles, on a toasted bun"),
    (26, "Jalapeño Popper Burger", "Beef patty stuffed with cream cheese and jalapeño, wrapped in bacon"),
    (26, "Garlic Parmesan Wings", "Crispy baked wings tossed in garlic butter and Parmigiano with parsley"),
    (26, "Soft Serve Sundae", "Vanilla soft-serve with hot fudge, peanut butter, crushed pretzels, and caramel"),
    (26, "Craft Root Beer Float", "House-made root beer poured over two scoops of vanilla ice cream"),

    # ─── Mezze Bar (27) — mediterranean, extra ───────────────────────────────
    (27, "Fava Bean Dip", "Greek fava spread with caramelized onions, capers, and lemon on pita"),
    (27, "Grilled Lamb Chops", "Marinated lamb chops with oregano and lemon, served over orzo pilaf"),
    (27, "Tiropita", "Baked phyllo pie with layers of feta and ricotta cheese filling"),
    (27, "Psarosoupa", "Greek fisherman's soup with seasonal fish, potato, olive oil, and lemon"),
    (27, "Gemista", "Baked stuffed tomatoes and peppers with herbed rice, pine nuts, and olive oil"),
    (27, "Kritharoto", "Orzo pasta risotto-style with shrimp, lemon zest, and feta crumbles"),
    (27, "Skordalia with Beet", "Garlic almond dip alongside roasted beet slices and walnuts"),
    (27, "Gigantes Plaki", "Giant baked butter beans in tomato, olive oil, parsley, and dill sauce"),
    (27, "Rizogalo", "Creamy Greek rice pudding with cinnamon, orange zest, and warm milk"),
    (27, "Ouzo Sorbet", "Anise-scented sorbet with ouzo infused into the syrup base"),

    # ─── Aegean Kitchen (28) — mediterranean, extra ──────────────────────────
    (28, "Garides Saganaki", "Shrimp baked in spicy tomato sauce with feta cheese and Ouzo, bubbling hot"),
    (28, "Imam Bayildi", "Turkish-style baked whole eggplant stuffed with onion, tomato, and garlic in olive oil"),
    (28, "Lamb Stifado", "Braised lamb in sweet red wine and whole pearl onions with cloves and cinnamon"),
    (28, "Kakavia Fish Stew", "Greek fisherman's bouillabaisse with rockfish, tomatoes, capers, and wine"),
    (28, "Tiganites", "Traditional Greek fried dough pancakes drizzled with honey and sesame"),
    (28, "Htapodi Ksidato", "Marinated octopus salad with red wine vinegar, onion, and fresh herbs"),
    (28, "Kolokythokeftedes", "Crispy fried zucchini and feta fritters served with tzatziki"),
    (28, "Soutzoukakia", "Baked cumin-spiced meatballs in rich tomato wine sauce from Smyrna"),
    (28, "Portokalopita", "Syrup-soaked phyllo and orange cake with vanilla cream and cinnamon"),
    (28, "Mastiha Ice Cream", "Greek mastic-flavored ice cream with chewy mastic resin and rose water"),

    # ─── Shawarma Republic (29) — middle_eastern, extra ──────────────────────
    (29, "Lamb Shawarma Wrap", "Slow-roasted spiced lamb with tahini, pickled turnip, and parsley in flatbread"),
    (29, "Msakhan", "Palestinian roasted chicken over taboon bread with caramelized onions and sumac"),
    (29, "Fatteh", "Toasted pita pieces layered with chickpeas, yogurt, tahini, and toasted pine nuts"),
    (29, "Warak Dawali", "Grape leaves stuffed with spiced lamb and rice, slow-simmered with lemon"),
    (29, "Maqluba", "Upside-down rice, eggplant, and chicken pilaf with crispy fried shallots"),
    (29, "Hummus Beiruti", "Extra smooth hummus topped with warm chickpeas, lemon, and olive oil"),
    (29, "Saj Bread", "Thin crispy flatbread baked on convex iron plate with zaatar or halloumi"),
    (29, "Atayef", "Stuffed pancakes filled with cream or walnut, folded and fried, drenched in sugar syrup"),
    (29, "Tamar Hindi", "Cold sweet-sour tamarind juice with rose water and a pinch of salt"),
    (29, "Malfouf", "Lebanese stuffed cabbage rolls with spiced rice and lamb in lemony tomato broth"),

    # ─── Levant Table (30) — middle_eastern, extra ───────────────────────────
    (30, "Kibbeh Nayyeh", "Raw minced lamb mixed with bulgur, onion, and cumin — Lebanese steak tartare"),
    (30, "Shakriyeh", "Lamb knuckle in yogurt sauce served over rice — a Levantine classic"),
    (30, "Arayes", "Toasted flatbread stuffed with spiced minced lamb and grilled until crispy"),
    (30, "Fteer Meshaltet", "Flaky layered Egyptian pastry eaten with honey or white cheese"),
    (30, "Mansaf", "Jordanian festive lamb in fermented dried yogurt sauce over rice with almonds"),
    (30, "Qatayef Asafiri", "Small semolina pancakes filled with clotted cream and drenched in sugar syrup"),
    (30, "Muhallabia", "Silky Lebanese milk pudding with orange blossom water and crushed pistachios"),
    (30, "Laban Ummo", "Lamb pieces simmered in yogurt sauce with turmeric and garlic over rice"),
    (30, "Khobz Arabi", "Freshly baked Arabic bread puffed from a wood oven with sesame and nigella seeds"),
    (30, "Jallab Mocktail", "Non-alcoholic grape and rose water drink with raisins and pine nuts over ice"),

    # ─── Fusion Kitchen (31) — other, extra ──────────────────────────────────
    (31, "Ramen Carbonara", "Instant-style ramen with pancetta, egg yolk, Pecorino, and black pepper"),
    (31, "Teriyaki Flatbread", "Thin flatbread with chicken teriyaki, mozzarella, pineapple, and pickled ginger"),
    (31, "Indian Spiced Burger", "Lamb patty with tikka masala aioli, mango chutney, raita, and fried onion"),
    (31, "Miso Butterscotch Pudding", "Creamy pudding with white miso and butterscotch layered with sea salt"),
    (31, "Yakitori Caesar Salad", "Romaine topped with grilled yakitori chicken, yuzu dressing, and nori croutons"),
    (31, "Chinese BBQ Pork Pizza", "Char siu pork, hoisin sauce, scallion, and mozzarella on thin crust"),
    (31, "Rendang Pulled Beef Tacos", "Indonesian-spiced slow-cooked beef in corn tortillas with cucumber slaw"),
    (31, "Wasabi Guacamole", "Avocado mash with fresh wasabi, lime, sesame, and black tobiko roe"),
    (31, "Gochujang Honey Ribs", "St. Louis ribs glazed with honey-gochujang sauce and sesame seeds"),
    (31, "Matcha Horchata", "Almond milk horchata with matcha powder, cinnamon, and condensed milk"),

    # ─── Street Bites (32) — other, extra ────────────────────────────────────
    (32, "Grain Bowl", "Farro, roasted beets, goat cheese, candied walnuts, and lemon tahini dressing"),
    (32, "Breakfast Tacos", "Scrambled eggs, black beans, salsa verde, and cotija on corn tortillas"),
    (32, "Turkey Club Wrap", "Turkey, avocado, bacon, lettuce, tomato, and ranch in a spinach tortilla"),
    (32, "Veggie Burger", "Beet and chickpea patty with sprouts, avocado, and sriracha on a wheat bun"),
    (32, "Overnight Oats", "Cold-soaked oats with chia seeds, almond milk, berries, and maple syrup"),
    (32, "Cheese Quesadilla", "Flour tortilla with three-cheese blend, griddled crispy with sour cream"),
    (32, "Caprese Panini", "Pressed ciabatta with fresh mozzarella, tomato, pesto, and balsamic glaze"),
    (32, "Fruit Smoothie", "Blended frozen mango, banana, and pineapple with coconut water and lime"),
    (32, "Loaded Sweet Potato", "Baked sweet potato with black beans, corn salsa, Greek yogurt, and cilantro"),
    (32, "Waffle with Fried Chicken", "Crispy fried chicken thigh on a Belgian waffle with maple syrup and hot sauce"),

    # ─── Café de Paris (33) — french ────────────────────────────────────────────
    (33, "Croissant", "Buttery, flaky laminated pastry baked golden and served warm"),
    (33, "Pain au Chocolat", "Laminated pastry folded around two dark chocolate batons, flaky and rich"),
    (33, "Croque Monsieur", "Ham and Gruyère béchamel sandwich grilled until bubbling and golden"),
    (33, "Quiche Lorraine", "Shortcrust tart filled with smoked bacon, Gruyère, and silky egg custard"),
    (33, "Soupe à l'Oignon", "Slow-caramelized onion broth topped with a crouton and melted Comté cheese"),
    (33, "Tartare de Boeuf", "Finely chopped raw beef with capers, cornichons, Dijon, and a raw egg yolk"),
    (33, "Salade Niçoise", "Tuna, hard-boiled egg, green beans, olives, and anchovies on dressed greens"),
    (33, "Crêpes Suzette", "Thin crêpes flambéed in orange butter and Grand Marnier sauce"),
    (33, "Tarte Tatin", "Upside-down caramelized apple tart baked in a cast-iron skillet"),
    (33, "Macarons", "Delicate almond meringue shells sandwiched with flavored ganache or buttercream"),
    (33, "Profiteroles", "Choux pastry puffs filled with vanilla ice cream and topped with warm chocolate sauce"),
    (33, "Mousse au Chocolat", "Airy dark chocolate mousse folded with egg whites and served chilled"),
    (33, "Mille-Feuille", "Three layers of puff pastry filled with pastry cream and glazed with fondant"),
    (33, "French Onion Soup", "Deep brown onion broth, toasted baguette, and molten Gruyère crust"),
    (33, "Omelette aux Fines Herbes", "Softly folded egg omelette with chervil, tarragon, and chives"),
    (33, "Gougères", "Warm Gruyère-scented choux puffs served as an aperitif nibble"),
    (33, "Crème Brûlée", "Silky vanilla custard beneath a crackly caramelized sugar shell"),
    (33, "Baguette with Pâté", "Sliced crusty baguette with country-style pork pâté and cornichons"),

    # ─── Brasserie Lyon (34) — french ──────────────────────────────────────────
    (34, "Coq au Vin", "Chicken braised slowly in red wine with pearl onions, lardons, and mushrooms"),
    (34, "Bouillabaisse", "Marseille fisherman's stew with saffron broth, rouille, and crusty croutons"),
    (34, "Steak Frites", "Bistro-cut pan-fried steak with golden hand-cut fries and béarnaise sauce"),
    (34, "Escargots de Bourgogne", "Snails baked in garlic-herb butter in individual shells"),
    (34, "Moules Marinières", "Steamed mussels in white wine, shallot, parsley, and butter broth"),
    (34, "Gratin Dauphinois", "Thinly sliced potato layered with cream and Gruyère, baked golden"),
    (34, "Vichyssoise", "Chilled leek and potato cream soup finished with crème fraîche and chives"),
    (34, "Pot-au-Feu", "Boiled beef and winter vegetables in a clear herbed broth with bone marrow toast"),
    (34, "Blanquette de Veau", "Veal pieces in a velvety white wine and cream sauce with mushrooms"),
    (34, "Duck Confit", "Slow-cooked duck leg in its own fat, crisped in the pan, with lentils"),
    (34, "Tarte Flambée", "Alsatian thin-crust tart with crème fraîche, onion, and smoked lardons"),
    (34, "Clafoutis", "Baked custard with fresh cherries set in a lightly sweetened batter"),
    (34, "Crème Caramel", "Inverted caramel flan with amber sauce flowing over soft custard"),
    (34, "Île Flottante", "Poached meringue islands floating on crème anglaise with caramel threads"),
    (34, "Pain Perdu", "Thick brioche soaked in vanilla custard and pan-fried golden — French toast"),
    (34, "Salade Lyonnaise", "Frisée lettuce, lardons, croutons, and a poached egg with Dijon vinaigrette"),

    # ─── Le Bistrot (35) — french ──────────────────────────────────────────────
    (35, "Pissaladière", "Provençal flatbread topped with caramelized onions, anchovies, and niçoise olives"),
    (35, "Soufflé au Fromage", "Baked Gruyère soufflé that rises dramatically above its ramekin"),
    (35, "Magret de Canard", "Pan-seared duck breast with cherry jus and dauphinoise potato"),
    (35, "Cassoulet", "White bean stew with confit duck, Toulouse sausage, and pork rind, baked with a crust"),
    (35, "Sole Meunière", "Dover sole dusted in flour and pan-fried in browned butter with capers and lemon"),
    (35, "Croissant aux Amandes", "Twice-baked croissant filled with almond frangipane and toasted flaked almonds"),
    (35, "Fromage Blanc", "Fresh white cheese served with honey and seasonal fruit compote"),
    (35, "Pâté de Campagne", "Rustic country-style pork terrine with green peppercorns and gherkins"),
    (35, "Ratatouille", "Slow-roasted Provençal vegetable stew of tomato, eggplant, zucchini, and peppers"),
    (35, "Tarte aux Fruits", "Shortcrust tart filled with pastry cream and topped with glazed seasonal fruit"),
    (35, "Champignons à la Crème", "Wild mushrooms sautéed in butter and finished with crème fraîche and thyme"),
    (35, "Flamiche", "Flaky pastry tart filled with leeks and Maroilles cheese from northern France"),
    (35, "Navarin d'Agneau", "Spring lamb stew with turnips, peas, and new potatoes in a herbed sauce"),
    (35, "Financiers", "Small almond-brown butter cakes with crispy edges and moist centers"),
    (35, "Paris-Brest", "Ring of choux pastry filled with praline mousseline cream and caramelized hazelnuts"),

    # ─── Tapas Bar Madrid (36) — spanish ────────────────────────────────────────
    (36, "Patatas Bravas", "Crispy fried potato cubes with smoky tomato sauce and garlic aioli"),
    (36, "Tortilla Española", "Thick Spanish omelette of egg and slowly cooked potato, served in wedges"),
    (36, "Gambas al Ajillo", "Sizzling shrimp in olive oil with garlic, chili, and sherry"),
    (36, "Croquetas de Jamón", "Creamy béchamel and Ibérico ham croquettes fried crispy golden"),
    (36, "Pan con Tomate", "Toasted bread rubbed with ripe tomato, olive oil, and salt"),
    (36, "Pimientos de Padrón", "Blistered green peppers from Galicia, scattered with flaky sea salt"),
    (36, "Boquerones en Vinagre", "White anchovies marinated in vinegar with olive oil and parsley"),
    (36, "Chorizo al Vino", "Spanish chorizo sliced and simmered in red wine until tender"),
    (36, "Albóndigas en Salsa", "Pork meatballs braised in a rich tomato sauce with saffron"),
    (36, "Pulpo a la Gallega", "Boiled Galician octopus with paprika, olive oil, and coarse salt on wood"),
    (36, "Mejillones en Escabeche", "Steamed mussels preserved in a spiced vinegar and olive oil marinade"),
    (36, "Jamón Ibérico", "Hand-sliced air-cured acorn-fed Ibérico ham on toasted bread"),
    (36, "Queso Manchego con Membrillo", "Aged Manchego cheese with sweet quince paste and walnuts"),
    (36, "Tortilla de Patatas con Cebolla", "Spanish omelette with onion, softer and more custardy than the classic"),
    (36, "Calamares a la Romana", "Deep-fried squid rings in light batter with aioli and lemon"),

    # ─── La Paella (37) — spanish ──────────────────────────────────────────────
    (37, "Paella Valenciana", "Traditional saffron rice with chicken, rabbit, green beans, and garrofó beans"),
    (37, "Paella de Mariscos", "Saffron rice packed with shrimp, mussels, clams, and squid"),
    (37, "Fideuà", "Thin noodles cooked like paella with seafood in a rich fish stock with aioli"),
    (37, "Gazpacho", "Chilled blended soup of ripe tomatoes, cucumber, pepper, olive oil, and sherry vinegar"),
    (37, "Salmorejo", "Thick cold tomato cream from Córdoba topped with jamón and hard-boiled egg"),
    (37, "Cocido Madrileño", "Madrid's chickpea, vegetable, and meat stew served in three courses"),
    (37, "Fabada Asturiana", "White bean stew with morcilla, chorizo, and cured pork from Asturias"),
    (37, "Arroz con Leche", "Creamy Spanish rice pudding with cinnamon and lemon zest"),
    (37, "Churros con Chocolate", "Fried dough sticks dipped in thick hot dark chocolate"),
    (37, "Crema Catalana", "Catalan custard with a caramelized sugar crust, flavored with lemon and cinnamon"),
    (37, "Empanada Gallega", "Galician double-crust pie stuffed with tuna, peppers, and onions"),
    (37, "Pisto Manchego", "La Mancha's version of ratatouille with zucchini, tomato, and pepper topped with egg"),
    (37, "Migas", "Fried breadcrumbs from Extremadura with chorizo, peppers, and grapes"),
    (37, "Tarta de Santiago", "Almond cake from Santiago de Compostela dusted with the Cross of St. James"),

    # ─── El Pimiento (38) — spanish ────────────────────────────────────────────
    (38, "Bravas con Allioli", "Double-fried potatoes with smoky bravas sauce and Catalan garlic emulsion"),
    (38, "Calamar en su Tinta", "Squid braised in its own ink with garlic and white wine over black rice"),
    (38, "Angulas al Ajillo", "Tiny baby eels sautéed in olive oil with garlic and guindilla chili"),
    (38, "Cochinillo Asado", "Castilian suckling pig roasted until the skin shatters and the meat melts"),
    (38, "Callos a la Madrileña", "Madrid-style tripe stew with chorizo, morcilla, and smoked paprika"),
    (38, "Leche Frita", "Fried milk custard squares — thick béchamel set, breaded, and golden-fried"),
    (38, "Buñuelos de Bacalao", "Salt cod fritters in light airy batter with parsley and lemon aioli"),
    (38, "Morcilla de Burgos", "Blood sausage from Burgos with rice, onion, and pimentón, sliced and grilled"),
    (38, "Rabo de Toro", "Slow-braised oxtail in red wine with carrots and pearl onions"),
    (38, "Ensaladilla Rusa", "Spanish potato salad with peas, carrots, tuna, and homemade mayonnaise"),
    (38, "Torta de Aceite", "Crispy anise and sesame olive-oil biscuit from Seville"),

    # ─── Zum Goldenen Hahn (39) — german ────────────────────────────────────────
    (39, "Bratwurst", "Coarsely ground pork sausage grilled over charcoal with mustard and a roll"),
    (39, "Wiener Schnitzel", "Thinly pounded veal breaded and pan-fried golden, with lemon and lingonberry"),
    (39, "Sauerbraten", "Rhineland pot roast marinated in vinegar and spices for days, with potato dumplings"),
    (39, "Sauerkraut", "Slow-fermented shredded cabbage with juniper berries and caraway seeds"),
    (39, "Brezel", "Lye-dipped twisted pretzel with coarse salt, chewy inside and dark brown outside"),
    (39, "Kartoffelsuppe", "Thick potato soup with smoked bacon, leek, and marjoram"),
    (39, "Rouladen", "Thin beef rolled with mustard, onion, bacon, and pickle, braised in dark sauce"),
    (39, "Kassler", "Smoked and cured pork chop served with sauerkraut and potato purée"),
    (39, "Currywurst", "Sliced pork sausage under a tangy curry-ketchup sauce with fried potatoes"),
    (39, "Weißwurst", "White veal sausage boiled and peeled, eaten with sweet mustard and a pretzel"),
    (39, "Schweinebraten", "Bavarian roast pork with crispy rind, dark gravy, and bread dumplings"),
    (39, "Rindergulasch", "Slow-cooked beef goulash with onions, paprika, and caraway over egg noodles"),
    (39, "Apfelstrudel", "Thin pastry rolled around spiced apple filling with raisins and pine nuts"),
    (39, "Black Forest Cake", "Layers of chocolate sponge, whipped cream, and Morello cherries"),
    (39, "Semmelknödel", "Bavarian bread dumplings made from day-old rolls, served with roast and gravy"),

    # ─── Biergarten Haus (40) — german ─────────────────────────────────────────
    (40, "Leberkäse", "Bavarian meatloaf made of finely ground corned beef and pork, pan-fried"),
    (40, "Obatzda", "Camembert and cream cheese spread with paprika, butter, and caraway seeds"),
    (40, "Käsespätzle", "Swabian egg noodle bake with melted Emmentaler and crispy fried onions"),
    (40, "Maultaschen", "Swabian pasta pockets stuffed with meat and spinach in herb broth"),
    (40, "Zwiebelrostbraten", "Bavarian pan-fried beef steak topped with crispy onion rings and gravy"),
    (40, "Griebenschmalz", "Rendered lard with cracklings spread on dark rye bread with radish"),
    (40, "Dampfnudeln", "Steamed sweet yeast dumplings with vanilla custard or plum compote"),
    (40, "Bavarian Cream", "Gelatin-set cream enriched with egg yolk custard and whipped cream"),
    (40, "Bienenstich", "Honey-almond topped yeast cake filled with vanilla pastry cream"),
    (40, "Streuselkuchen", "Yeast cake topped with a thick butter and flour crumble — Silesian classic"),
    (40, "Zwiebelkuchen", "Savory onion tart with lardons, caraway, and sour cream in shortcrust pastry"),
    (40, "Flammkuchen Elsässer", "Alsatian thin-crust tart with crème fraîche, onion, and bacon"),
    (40, "Lebkuchen", "Spiced honey gingerbread with anise, cloves, and candied orange peel"),

    # ─── Wurst & Brot (41) — german ────────────────────────────────────────────
    (41, "Frankfurter", "Classic pork-veal sausage boiled and served in a bun with mustard"),
    (41, "Blutwurst", "Blood sausage sliced cold with dark rye bread, mustard, and raw onion"),
    (41, "Landjäger", "Hard dried beef-pork sausage pressed into a rectangular shape, chewy and smoky"),
    (41, "Linseneintopf", "Hearty lentil stew with smoked sausage, celery, carrot, and marjoram"),
    (41, "Erbsensuppe", "Split pea soup with smoked pork knuckle and marjoram — thick and warming"),
    (41, "Handkäse mit Musik", "Hessian sour milk cheese marinated in onion and caraway vinegar dressing"),
    (41, "Rehgulasch", "Venison goulash with juniper, red wine, and mushrooms over spätzle"),
    (41, "Baumkuchen", "Multi-layered spit cake with dozens of thin rings, coated in dark chocolate"),
    (41, "Pflaumenkuchen", "Open yeast tart covered in rows of halved fresh plums with cinnamon sugar"),
    (41, "Kartoffelpuffer", "Grated potato pancakes pan-fried crispy, served with sour cream or apple sauce"),
    (41, "Rote Grütze", "Nordic-German red berry pudding of strawberry, raspberry, and currant with cream"),

    # ─── Babička Kitchen (42) — eastern_european ────────────────────────────────
    (42, "Pierogi", "Boiled dumplings stuffed with potato and cheese, served with sour cream and bacon"),
    (42, "Borscht", "Deep magenta beet soup with sour cream, served with rye bread"),
    (42, "Stuffed Cabbage Rolls", "Cabbage leaves filled with minced pork and rice, braised in tomato sauce"),
    (42, "Kielbasa", "Smoked pork sausage grilled and served with mustard, sauerkraut, and rye bread"),
    (42, "Żurek", "Sour rye soup with hard-boiled egg and white sausage in a bread bowl"),
    (42, "Bigos", "Polish hunter's stew of sauerkraut, fresh cabbage, pork, kielbasa, and mushrooms"),
    (42, "Kotlet Schabowy", "Breaded and fried pork cutlet served with mashed potato and stewed red cabbage"),
    (42, "Placki Ziemniaczane", "Polish potato pancakes with sour cream and smoked salmon or bacon"),
    (42, "Kapusniak", "Tangy sauerkraut soup with pork ribs, carrot, and barley"),
    (42, "Kopytka", "Polish potato gnocchi with butter and breadcrumbs or mushroom sauce"),
    (42, "Sernik", "Polish cheesecake made with twaróg fresh cheese, vanilla, and raisins"),
    (42, "Makowiec", "Polish poppy seed roll with honey, raisins, and orange peel inside yeast dough"),
    (42, "Szarlotka", "Polish apple cake with cinnamon and a crumbly streusel top"),

    # ─── Pierogi House (43) — eastern_european ─────────────────────────────────
    (43, "Pierogi Ruskie", "Potato and farmer's cheese dumplings with caramelized onion and sour cream"),
    (43, "Pierogi z Mięsem", "Meat-filled dumplings with pork and beef, pan-fried until crispy"),
    (43, "Beet Salad", "Roasted beet and goat cheese salad with walnuts, dill, and lemon dressing"),
    (43, "Chicken Kyiv", "Butter-stuffed breaded chicken breast fried golden with garlic parsley butter"),
    (43, "Pampushky", "Ukrainian soft garlic rolls brushed with sunflower oil and dill"),
    (43, "Halushky", "Ukrainian dumplings with cottage cheese, butter, and sour cream"),
    (43, "Pelmeni", "Russian minced meat dumplings boiled and served with butter and sour cream"),
    (43, "Syrniki", "Cottage cheese pancakes fried golden, served with sour cream and jam"),
    (43, "Medovik", "Russian honey layer cake with thin sponge layers and sour cream frosting"),
    (43, "Sharlotka", "Simple Russian apple cake — a light sponge with cinnamon-scented apples"),
    (43, "Okroshka", "Cold kvass-based summer soup with cucumber, radish, egg, and sausage"),
    (43, "Borscht Ukrainsky", "Ukrainian borscht with pork rib, potato, beans, and fresh dill"),

    # ─── Budapest Table (44) — eastern_european ────────────────────────────────
    (44, "Goulash", "Hungarian beef stew with paprika, caraway, onion, and egg noodle dumplings"),
    (44, "Lángos", "Deep-fried flatbread topped with sour cream and grated cheese — Hungarian street food"),
    (44, "Stuffed Peppers", "Green peppers filled with ground pork and rice, simmered in tomato sauce"),
    (44, "Dobos Torte", "Seven-layer sponge cake with chocolate buttercream and a caramel-sharded top"),
    (44, "Kürtőskalács", "Spit-roasted chimney cake wound in yeast dough with caramelized sugar crust"),
    (44, "Halászlé", "Hungarian fisherman's hot paprika soup from the Danube with whole carp"),
    (44, "Töltött Káposzta", "Hungarian stuffed cabbage with ground pork and rice in paprika-tomato sauce"),
    (44, "Rétes", "Stretched strudel pastry with apple, cherry, or cabbage filling"),
    (44, "Pörkölt", "Rich pork or veal stew with onions and sweet paprika over egg noodles"),
    (44, "Túrós Tészta", "Egg noodles tossed with cottage cheese, sour cream, and smoky lardons"),
    (44, "Lecho", "Hungarian pepper and tomato stew with smoked sausage, paprika, and eggs"),
    (44, "Somlói Galuska", "Trifle of three sponge cakes, rum raisins, walnut, and chocolate cream"),

    # ─── Pho Saigon (45) — vietnamese ───────────────────────────────────────────
    (45, "Pho Bo", "Beef noodle soup with slow-simmered bone broth, rice noodles, herbs, bean sprouts, lime"),
    (45, "Pho Ga", "Chicken pho with crystal-clear aromatic broth, rice noodles, and fresh herbs"),
    (45, "Bun Bo Hue", "Spicy Central Vietnamese beef and pork noodle soup with lemongrass broth"),
    (45, "Banh Mi Thit", "Toasted baguette with pork, pâté, pickled daikon, jalapeño, and cilantro"),
    (45, "Com Tam", "Broken jasmine rice with grilled pork chop, egg, pickles, and nuoc cham"),
    (45, "Banh Xeo", "Crispy yellow rice flour crêpe filled with shrimp, pork, and bean sprouts"),
    (45, "Goi Cuon", "Fresh rice paper rolls with shrimp, pork, vermicelli, herbs, and peanut sauce"),
    (45, "Bun Cha", "Hanoi grilled pork patties with vermicelli noodles in sweet-sour dipping broth"),
    (45, "Bo Luc Lac", "Shaking wok-tossed beef cubes with garlic butter, pepper, and a lime salt dip"),
    (45, "Hu Tieu", "Clear or dry pork and seafood noodle soup with crispy shallots and fresh herbs"),
    (45, "Canh Chua", "Southern sour soup with tamarind, tomato, pineapple, and fish or shrimp"),
    (45, "Ca Phe Sua Da", "Strong Vietnamese drip coffee with sweetened condensed milk over crushed ice"),
    (45, "Che Ba Mau", "Three-colour dessert with red bean, mung bean jelly, and pandan coconut milk"),
    (45, "Banh Cuon", "Steamed rice rolls filled with seasoned ground pork and wood ear mushrooms"),
    (45, "Mi Quang", "Turmeric noodle dish from Da Nang with shrimp, pork, peanuts, and crispy rice crackers"),

    # ─── Bún Bò Huế House (46) — vietnamese ────────────────────────────────────
    (46, "Bun Rieu", "Crab and tomato vermicelli soup with tofu, shrimp paste, and fresh herbs"),
    (46, "Banh Beo", "Steamed rice water fern cakes topped with dried shrimp and scallion oil"),
    (46, "Banh Nam", "Flat steamed rice cake with shrimp and pork in a delicate banana leaf wrapper"),
    (46, "Bun Mam", "Southern Vietnamese fermented fish noodle soup with eggplant and pork"),
    (46, "Goi Ngo Sen", "Lotus root salad with shrimp, pork, peanuts, and rau ram herb"),
    (46, "Bap Chuoi Tron", "Banana flower salad with shredded chicken, peanuts, and nuoc cham dressing"),
    (46, "Nem Nuong", "Grilled pork meatballs on skewers dipped in sweet spicy sauce"),
    (46, "Ca Ri Ga", "Southern Vietnamese yellow chicken curry with coconut milk and potatoes"),
    (46, "Sinh To Bo", "Creamy blended avocado smoothie with condensed milk and crushed ice"),
    (46, "Banh Cam", "Deep-fried sesame rice balls with sweet mung bean paste filling"),
    (46, "Banh It Tran", "Sticky rice balls with minced shrimp and pork, rolled in sesame seeds"),
    (46, "Ca Kho To", "Caramelized braised fish in clay pot with coconut water, ginger, and chili"),
    (46, "Nuoc Cham", "Classic Vietnamese dipping sauce of fish sauce, lime, sugar, garlic, and chili"),
    (46, "Xoi Ga", "Sticky rice topped with shredded poached chicken, fried shallots, and ginger"),

    # ─── Bánh Mì & More (47) — vietnamese ──────────────────────────────────────
    (47, "Banh Mi Cha Lua", "Vietnamese baguette with steamed pork roll, mayo, pickled veg, and chili"),
    (47, "Goi Ga Bap Cai", "Shredded cabbage and poached chicken salad with nuoc cham and peanuts"),
    (47, "Com Chien", "Wok-fried jasmine rice with egg, scallion, and choice of pork or shrimp"),
    (47, "Pho Cuon", "Fresh unfried pho roll with beef, bean sprouts, and herbs dipped in sauce"),
    (47, "Banh Uot", "Silky wide steamed rice sheets with pork and wood ear mushroom filling"),
    (47, "Bun Thit Nuong", "Cold vermicelli with chargrilled pork, herbs, pickled veg, and peanut sauce"),
    (47, "Com Hen", "Tiny basket clams over broken rice with lemongrass, peanuts, and sesame crackers"),
    (47, "Bun Dau Mam Tom", "Fried tofu and pork with vermicelli and pungent fermented shrimp paste"),
    (47, "Xoi Xeo", "Yellow sticky rice with mung bean, fried shallots, and scallion oil"),
    (47, "Mut Dua", "Crystallized coconut strips — sweet Tet holiday candy"),
    (47, "Banh Khuc", "Steamed sticky rice cake with wormwood leaves, mung bean, and sticky pork"),
    (47, "Nuoc Dua Tuoi", "Fresh young coconut water served chilled from the coconut"),
    (47, "Banh Trang Nuong", "Grilled rice paper topped with quail egg, scallion oil, and dried shrimp"),

    # ─── Lutong Pinoy (48) — filipino ───────────────────────────────────────────
    (48, "Adobo", "Braised chicken or pork in vinegar, soy sauce, garlic, bay leaves, and peppercorns"),
    (48, "Sinigang na Baboy", "Sour tamarind soup with pork ribs, eggplant, radish, and water spinach"),
    (48, "Kare-Kare", "Oxtail and tripe in peanut-annatto stew, served with bagoong shrimp paste"),
    (48, "Lechon", "Spit-roasted whole pork with crispy skin, served with liver sauce and vinegar"),
    (48, "Crispy Pata", "Deep-fried pork knuckle until the skin is shatteringly crisp"),
    (48, "Dinuguan", "Pork offal simmered in dark pig's blood sauce with vinegar and green chili"),
    (48, "Pinakbet", "Vegetable medley of bitter melon, eggplant, and okra stewed with bagoong"),
    (48, "Pancit Canton", "Stir-fried wheat noodles with pork, shrimp, cabbage, and soy-calamansi sauce"),
    (48, "Lumpia Shanghai", "Deep-fried pork and vegetable spring rolls with sweet chili dipping sauce"),
    (48, "Arroz Caldo", "Ginger chicken congee topped with fried garlic, scallion, and calamansi"),
    (48, "Leche Flan", "Dense caramel egg custard steamed in llanera molds with amber sugar sauce"),
    (48, "Halo-Halo", "Crushed ice dessert with red beans, jackfruit, coconut, ube, and leche flan"),
    (48, "Champorado", "Sticky sweet chocolate rice porridge topped with dried fish and condensed milk"),

    # ─── Kain Tayo (49) — filipino ─────────────────────────────────────────────
    (49, "Tapsilog", "Cured beef tapa with garlic fried rice and fried egg — Filipino breakfast trio"),
    (49, "Longsilog", "Sweet pork sausage with garlic fried rice and fried egg"),
    (49, "Tocilog", "Cured sweet red pork with garlic fried rice and fried egg"),
    (49, "Palabok", "Rice noodles smothered in orange shrimp sauce with chicharon and hard-boiled egg"),
    (49, "Nilaga", "Boiled beef or pork with potato, bok choy, and corn in clear broth"),
    (49, "Tinola", "Chicken and green papaya soup with moringa leaves and ginger broth"),
    (49, "Bulalo", "Slow-boiled beef shank and marrow soup with cabbage and corn"),
    (49, "Mechado", "Beef larded and stewed in tomato sauce with potato, carrot, and bay leaf"),
    (49, "Caldereta", "Goat or beef stew in tomato and liver paste sauce with potato and olives"),
    (49, "Sisig", "Sizzling plate of chopped pork cheek and ears with onion, egg, and calamansi"),
    (49, "Chicken Inasal", "Annatto-marinated grilled chicken from Bacolod with garlic rice and vinegar"),
    (49, "Batchoy", "Pork noodle soup from Iloilo with liver, cracklings, and garlic over miki noodles"),

    # ─── Adobo House (50) — filipino ───────────────────────────────────────────
    (50, "Kinilaw na Tuna", "Raw tuna cured in cane vinegar with ginger, onion, chili, and coconut cream"),
    (50, "Laing", "Dried taro leaves simmered in thick coconut milk with chili and shrimp paste"),
    (50, "Binagoongan", "Pork belly braised with fermented shrimp paste and tomato"),
    (50, "Okoy", "Crispy shrimp and sweet potato fritters with spiced vinegar dip"),
    (50, "Turon", "Deep-fried banana and jackfruit spring roll coated in caramelized sugar"),
    (50, "Bibingka", "Rice cake baked in banana leaf with salted egg, coconut, and kesong puti"),
    (50, "Puto Bumbong", "Steamed purple rice in bamboo tubes topped with butter, coconut, and sugar"),
    (50, "Polvoron", "Crumbly toasted flour and powdered milk candy wrapped in cellophane"),
    (50, "Ube Halaya", "Sweet purple yam jam cooked thick with condensed milk and butter"),
    (50, "Palitaw", "Flat sticky rice cakes coated in coconut, sesame seeds, and sugar"),
    (50, "Espasol", "Toasted rice tube candy rolled in rice flour with coconut milk filling"),

    # ─── Warung Bali (51) — indonesian ─────────────────────────────────────────
    (51, "Nasi Goreng", "Indonesian wok-fried rice with kecap manis, shallots, and a fried egg on top"),
    (51, "Mie Goreng", "Stir-fried egg noodles with shrimp, chicken, cabbage, and sweet soy sauce"),
    (51, "Sate Ayam", "Grilled chicken skewers marinated in turmeric and served with peanut sauce"),
    (51, "Rendang", "Slow-cooked dry beef curry in coconut milk with lemongrass, galangal, and chilies"),
    (51, "Gado Gado", "Indonesian salad of blanched vegetables, tofu, and egg with peanut sauce"),
    (51, "Soto Ayam", "Yellow chicken turmeric soup with glass noodles, boiled egg, and fried shallots"),
    (51, "Rawon", "Dark black beef soup from East Java with kluwek nuts, lemongrass, and herbs"),
    (51, "Opor Ayam", "Chicken braised in coconut milk with galangal, lemongrass, and candlenut"),
    (51, "Semur Daging", "Beef braised in sweet soy sauce with nutmeg, cloves, and white pepper"),
    (51, "Pepes Ikan", "Spiced fish wrapped in banana leaf and steamed or grilled"),
    (51, "Sambal Udang", "Shrimp cooked in spicy ground chili sambal with tomato and shallots"),
    (51, "Sayur Asem", "Tamarind vegetable soup with peanuts, corn, long beans, and melinjo leaves"),
    (51, "Klepon", "Green pandan rice balls filled with palm sugar and rolled in grated coconut"),
    (51, "Dadar Gulung", "Green pandan crêpe rolled around a sweetened coconut filling"),

    # ─── Nasi Goreng Kitchen (52) — indonesian ─────────────────────────────────
    (52, "Nasi Uduk", "Coconut rice cooked in pandan and lemongrass, served with fried chicken and tempeh"),
    (52, "Lontong Sayur", "Rice cakes in coconut vegetable curry with hard-boiled egg and kerupuk"),
    (52, "Ketoprak", "Rice noodles and tofu with peanut sauce, soy sauce, and lime"),
    (52, "Bubur Ayam", "Indonesian chicken rice porridge with ginger, crispy shallots, and soy sauce"),
    (52, "Sate Padang", "Minced offal skewers from Padang in a thick yellow spiced sauce"),
    (52, "Gudeg", "Slow-cooked young jackfruit stew from Yogyakarta in coconut milk and palm sugar"),
    (52, "Cap Cay", "Chinese-Indonesian stir-fried mixed vegetable dish with oyster sauce"),
    (52, "Tahu Goreng", "Deep-fried tofu with sweet soy sauce, peanuts, cucumber, and sprouts"),
    (52, "Tempe Goreng", "Fermented soybean cake fried crispy, served with sambal and rice"),
    (52, "Bakso", "Indonesian meatball soup with clear broth, noodles, and fried shallots"),
    (52, "Es Teler", "Chilled coconut, avocado, and jackfruit in coconut milk and condensed milk"),

    # ─── Sate Haus (53) — indonesian ───────────────────────────────────────────
    (53, "Sate Lilit", "Balinese minced fish and coconut satay pressed on lemongrass skewers"),
    (53, "Babi Guling", "Balinese whole roasted suckling pig stuffed with turmeric and spiced coconut"),
    (53, "Lawar Bali", "Balinese minced meat and coconut salad with spiced palm sugar dressing"),
    (53, "Nasi Campur Bali", "Balinese mixed rice plate with sate, lawar, spiced pork, and sambal"),
    (53, "Ayam Betutu", "Slow-roasted chicken marinated in Balinese spice paste wrapped in banana leaf"),
    (53, "Martabak Manis", "Thick sweet pancake folded over chocolate, cheese, and peanuts"),
    (53, "Es Dawet", "Chilled pandan jelly drink in coconut milk and palm sugar syrup"),
    (53, "Pukis", "Boat-shaped coconut milk and pandan batter cakes cooked in special iron molds"),
    (53, "Kelepon", "Javanese green rice balls filled with melted palm sugar and dusted in coconut"),
    (53, "Jajan Pasar", "Market sweets platter of multicolored rice cakes, coconut balls, and kueh"),

    # ─── Churrascaria Rio (54) — brazilian ─────────────────────────────────────
    (54, "Picanha", "Prime beef sirloin cap grilled over charcoal and sliced tableside at the skewer"),
    (54, "Fraldinha", "Flank steak seasoned with coarse salt and grilled over hot coals"),
    (54, "Costela de Boi", "Slow-smoked beef short ribs in a churrascaria dry rub — fork-tender"),
    (54, "Linguiça Toscana", "Seasoned pork sausage with garlic and fennel, grilled over charcoal"),
    (54, "Coração de Frango", "Grilled chicken hearts on skewers seasoned with garlic and lime"),
    (54, "Pão de Queijo", "Chewy Minas Gerais tapioca cheese bread puffs baked fresh"),
    (54, "Farofa", "Toasted cassava flour sautéed with butter, bacon, egg, and scallion"),
    (54, "Feijoada", "Brazil's national dish — black bean and pork stew with smoked meat and rice"),
    (54, "Coxinha", "Teardrop-shaped pulled chicken and cream cheese croquette in crispy dough"),
    (54, "Bolinho de Bacalhau", "Salt cod and potato fritter with parsley and egg yolk, fried golden"),
    (54, "Brigadeiro", "Condensed milk and cocoa truffle rolled in chocolate sprinkles — beloved candy"),
    (54, "Quindim", "Baked coconut and egg yolk custard cup from Bahia, jewel-bright yellow"),
    (54, "Pudim de Leite", "Brazilian caramel flan with an extra smooth and rich consistency"),
    (54, "Caipirinha Mocktail", "Crushed lime with cane sugar and sparkling water in a caipirinha style"),

    # ─── Feira da Carne (55) — brazilian ───────────────────────────────────────
    (55, "Churrasco Misto", "Mixed grill platter of picanha, fraldinha, and sausage with chimichurri"),
    (55, "Kafta Brasileira", "Ground beef skewers seasoned with cumin, onion, and parsley"),
    (55, "Frango na Brasa", "Whole chicken halved and grilled slowly over charcoal until charred"),
    (55, "Espeto de Carne Seca", "Salted dried beef on skewers caramelized and served with cassava"),
    (55, "Mandioca Frita", "Deep-fried cassava sticks — creamy inside and golden crispy outside"),
    (55, "Caldinho de Feijão", "Shot glass of warm pureed black bean broth with garlic and sausage"),
    (55, "Pastel de Queijo", "Deep-fried thin pastry pocket filled with melted mozzarella cheese"),
    (55, "Empadinha", "Small Brazilian shortcrust pie filled with chicken and heart of palm"),
    (55, "Goiabada com Queijo", "Guava paste paired with salty white Minas cheese — Romeo and Juliet"),
    (55, "Caldo de Cana", "Fresh pressed sugarcane juice served over ice with lime"),
    (55, "Beijinho", "Coconut condensed milk truffle with a clove on top — sister to the brigadeiro"),
    (55, "Bolo de Fubá", "Yellow cornmeal cake with anise from Minas Gerais"),

    # ─── Boteco Verde (56) — brazilian ─────────────────────────────────────────
    (56, "Moqueca de Camarão", "Bahian shrimp stew in coconut milk with palm oil, tomato, and peppers"),
    (56, "Bobó de Camarão", "Cassava cream and shrimp stew with palm oil from Bahia"),
    (56, "Vatapá", "Bread, shrimp, coconut milk, and peanut paste dish from Salvador"),
    (56, "Acarajé", "Deep-fried black-eyed pea fritter filled with vatapá and caruru from street stalls"),
    (56, "Mungunzá", "Sweet hominy corn cooked in coconut milk with cinnamon and cloves"),
    (56, "Canjica", "Creamy sweet corn porridge with condensed milk and peanuts from São Paulo"),
    (56, "Pamonha", "Sweet or savory corn tamale in corn husks boiled slowly"),
    (56, "Bolo de Rolo", "Thin jelly-roll cake with guava paste filling — Pernambuco speciality"),
    (56, "Cocada", "Coconut candy slow-cooked with sugar until golden and chewy"),
    (56, "Tapioca Crêpe", "Crispy tapioca flour crêpe filled with coconut, banana, or cream cheese"),
    (56, "Romeu e Julieta", "Vanilla cream cheese with guava paste dessert combination"),
    (56, "Açaí Bowl", "Frozen Amazonian açaí berry blended thick with granola and fresh banana"),

    # ─── Rum Shack (57) — caribbean ─────────────────────────────────────────────
    (57, "Jerk Chicken", "Scotch bonnet and allspice marinated chicken grilled over pimento wood"),
    (57, "Jerk Pork", "Spiced slow-cooked pork shoulder with jerk seasoning and charred edges"),
    (57, "Rice and Peas", "Jamaican kidney beans cooked in coconut milk with thyme and garlic rice"),
    (57, "Plantain Tostones", "Twice-fried green plantain discs, crispy outside and soft inside"),
    (57, "Ackee and Saltfish", "Jamaica's national dish — ackee fruit with salt cod, onion, and pepper"),
    (57, "Callaloo Soup", "Caribbean greens braised with crab, coconut milk, and okra"),
    (57, "Fish Escovitch", "Fried whole fish marinated in spicy vinegar with peppers and onions"),
    (57, "Festival Dumplings", "Sweet fried cornmeal dumplings, golden and slightly chewy"),
    (57, "Curry Goat", "Slow-braised goat in Caribbean curry with potato and scotch bonnet"),
    (57, "Oxtail Stew", "Slow-cooked oxtail in dark brown stew gravy with butter beans and thyme"),
    (57, "Sorrel Drink", "Chilled hibiscus flower infusion with ginger and cloves"),
    (57, "Bammy", "Flatbread made from bitter cassava — soaked and fried, served with fish"),
    (57, "Pepper Pot", "Guyanese national dish of cassareep-based meat and vegetables stew"),

    # ─── Island Flavors (58) — caribbean ────────────────────────────────────────
    (58, "Roti with Curry", "Trinidadian dhalpuri roti wrapped around curried chicken or channa"),
    (58, "Doubles", "Trinidadian street food — two fried bara filled with channa and tamarind chutney"),
    (58, "Pelau", "One-pot chicken, rice, and pigeon peas caramelized in brown sugar"),
    (58, "Saltfish Fritters", "Salt cod and pepper fritters fried golden — Barbadian breakfast staple"),
    (58, "Macaroni Pie", "Baked Caribbean macaroni and cheese with a firm, sliceable texture"),
    (58, "Soursop Punch", "Blended soursop with evaporated milk, vanilla, and nutmeg over ice"),
    (58, "Pholourie", "Split pea fritter balls with mango and tamarind chutney from Trinidad"),
    (58, "Black Cake", "Dense rum-soaked fruit cake with burnt sugar — West Indian Christmas classic"),
    (58, "Cou Cou and Flying Fish", "Barbadian cornmeal and okra cake with steamed flying fish in sauce"),
    (58, "Bake and Shark", "Deep-fried shark in fried dough bake with all the toppings — T&T street food"),
    (58, "Johnny Cakes", "Pan-fried or baked cornmeal bread rolls from across the Caribbean"),

    # ─── Jerk Palace (59) — caribbean ───────────────────────────────────────────
    (59, "Jerk Shrimp", "Large shrimp grilled in scotch bonnet jerk marinade with lime butter"),
    (59, "Brown Stew Chicken", "Jamaican braised chicken in a dark sweet-savory brown stew sauce"),
    (59, "Steam Fish", "Whole fish steamed over vegetables with scotch bonnet, okra, and thyme"),
    (59, "Rundown", "Mackerel or saltfish simmered in coconut cream with onion and tomato"),
    (59, "Roasted Breadfruit", "Whole breadfruit roasted over open flame until charred and fluffy inside"),
    (59, "Ducana with Saltfish", "Sweet potato and coconut dumplings with sautéed salted cod"),
    (59, "Guava Duff", "Bahamian dessert of guava rolled in dough and steamed with butter rum sauce"),
    (59, "Coconut Drops", "Jamaican hard coconut candy cooked with ginger and molded into chunks"),
    (59, "Tamarind Balls", "Tangy-sweet candies made of tamarind pulp, sugar, and pepper"),
    (59, "Mannish Water", "Jamaican goat head soup with green bananas, yam, and scotch bonnet"),

    # ─── Habesha Kitchen (60) — ethiopian ───────────────────────────────────────
    (60, "Doro Wat", "Ethiopian spiced chicken stew with hard-boiled egg in berbere butter sauce"),
    (60, "Injera", "Large spongy fermented teff flatbread used as both plate and utensil"),
    (60, "Tibs", "Sautéed cubed lamb or beef with rosemary, onion, and Ethiopian spices"),
    (60, "Kitfo", "Ethiopian lean beef tartare seasoned with mitmita spice and niter kibbeh butter"),
    (60, "Shiro Wat", "Roasted chickpea and fava powder stew with onion and berbere"),
    (60, "Misir Wat", "Red lentil stew slowly cooked with berbere, onion, and niter kibbeh"),
    (60, "Ayib", "Fresh Ethiopian cottage cheese served alongside spicy stews to temper heat"),
    (60, "Gomen", "Collard greens sautéed with onion, garlic, and niter kibbeh spiced butter"),
    (60, "Kategna", "Injera toasted with berbere and spiced butter — a crispy snack"),
    (60, "Buna", "Ethiopian coffee ceremony — heavily roasted dark brew in small cups with incense"),

    # ─── Injera House (61) — ethiopian ─────────────────────────────────────────
    (61, "Beyaynetu", "Fasting plate of vegan stews — misir, gomen, timatim, and yataklete kilkil"),
    (61, "Yataklete Kilkil", "Ethiopian mixed vegetable stew with potato, carrot, and ginger"),
    (61, "Timatim Fitfit", "Tomato, green pepper, and onion salad tossed with torn injera"),
    (61, "Ful Medames", "Ethiopian spiced fava bean stew with olive oil, lemon, and cumin"),
    (61, "Dulet", "Minced tripe, liver, and lean beef seasoned with mitmita and niter kibbeh"),
    (61, "Chechebsa", "Torn flatbread tossed in spiced butter and served with honey or yogurt"),
    (61, "Enkulal Firfir", "Scrambled eggs torn with injera in spiced niter kibbeh butter"),
    (61, "Teff Porridge", "Whole grain teff cooked into a warm nutty porridge with honey and milk"),
    (61, "Sambusa", "Ethiopian fried pastry pocket filled with spiced lentils or meat"),
    (61, "Tej", "Traditional Ethiopian honey wine mead with gesho buckthorn bitterness"),

    # ─── Addis Table (62) — ethiopian ──────────────────────────────────────────
    (62, "Zilzil Tibs", "Strips of beef sautéed with rosemary and jalapeño in a hot clay pot"),
    (62, "Beef Tibs with Berbere", "Cubed beef stir-fried with onion, tomato, and berbere spice paste"),
    (62, "Doro Tibs", "Chicken pieces sautéed in spiced butter with onions and green peppers"),
    (62, "Lamb Tibs", "Tender lamb cubes pan-fried with fresh rosemary, onion, and awaze chili sauce"),
    (62, "Kolo", "Roasted barley, sunflower seeds, and peanuts — Ethiopian trail mix snack"),
    (62, "Beso", "Roasted barley flour mixed with spices into a dry snack eaten on the road"),
    (62, "Shiro Fit Fit", "Torn injera pieces folded into thick shiro stew with spiced butter"),
    (62, "Firfir", "Torn injera simmered in berbere-spiced stew — a common breakfast"),
    (62, "Awaze", "Fiery Ethiopian chili paste made with berbere, mead, and mustard"),
    (62, "Habesha Beer", "Mildly fermented barley home brew called tella — earthy and slightly sour"),

    # ─── Alsace Table (63) — french, supplemental ───────────────────────────────
    (63, "Baeckeoffe", "Alsatian casserole of marinated pork, lamb, and potato slow-baked in a sealed pot"),
    (63, "Choucroute Garnie", "Alsatian sauerkraut braised in Riesling with sausages, pork belly, and potatoes"),
    (63, "Kugelhopf", "Brioche-like ring cake studded with raisins and almonds, dusted with powdered sugar"),
    (63, "Munster Cheese Plate", "Pungent washed-rind Munster cheese with caraway seeds and rye bread"),
    (63, "Beurre Blanc", "Classic Loire butter sauce emulsified with white wine and shallot reduction"),
    (63, "Terrine de Foie Gras", "Silky duck liver terrine with sweet brioche and Sauternes jelly"),
    (63, "Brandade de Morue", "Creamy salt cod purée with olive oil, garlic, and potato from Nîmes"),
    (63, "Tarte au Citron", "Sharp lemon curd tart in a crisp pastry shell topped with meringue peaks"),
    (63, "Canelé Bordelais", "Small fluted Bordeaux cake with dark caramelized crust and custardy inside"),
    (63, "Galette des Rois", "Puff pastry cake filled with almond frangipane — served during Epiphany"),
    (63, "Poule au Pot", "Whole chicken stuffed with herb bread and vegetables, simmered in broth"),
    (63, "Andouillette", "French tripe sausage grilled and served with mustard cream sauce"),

    # ─── Bodega Sevilla (64) — spanish, supplemental ────────────────────────────
    (64, "Flamenquín", "Andalusian pork and jamón loin roulade breaded and deep-fried"),
    (64, "Torrijas", "Spanish Easter French toast soaked in milk, honey, and cinnamon"),
    (64, "Caldo Gallego", "Galician white bean and turnip top soup with chorizo and salted pork"),
    (64, "Purrusalda", "Basque leek and salt cod stew with potato and olive oil"),
    (64, "Espárragos con Mahonesa", "White asparagus from Navarra with homemade mayonnaise"),
    (64, "Oreja a la Plancha", "Grilled pork ear thinly sliced with paprika and garlic — Galician classic"),
    (64, "Arroz Negro", "Valencian black rice with squid ink, squid, and alioli"),
    (64, "Piperade", "Basque slow-cooked pepper, tomato, and onion sauce with egg or jamón"),
    (64, "Pestiños", "Deep-fried anise and sesame honey fritters from Andalucia"),
    (64, "Tocino de Cielo", "Intensely sweet egg yolk custard from Jerez — heavier than crème caramel"),
    (64, "Chistorra", "Thin fast-cured Basque pork sausage fried quickly in olive oil"),
    (64, "Ensalada de Bacalao", "Salt cod salad with orange, olive, onion, and capers"),

    # ─── Rheinland Stub'n (65) — german, supplemental ───────────────────────────
    (65, "Himmel und Erde", "Mashed potato with applesauce, fried black pudding, and caramelized onions"),
    (65, "Halve Hahn", "Cologne rye roll with Dutch cheese, mustard, and onion — a pub classic"),
    (65, "Reibekuchen", "Cologne potato fritters served with apple sauce at Christmas markets"),
    (65, "Zwetschgendatschi", "Bavarian sheet cake covered in fresh plums and streusel crumble"),
    (65, "Scholle mit Speck", "Pan-fried North Sea plaice with crispy bacon and mustard sauce"),
    (65, "Pichelsteiner Eintopf", "Bavarian mixed meat and vegetable stew — each family has their own version"),
    (65, "Grüne Soße", "Frankfurt's cold green sauce of seven herbs with hard-boiled egg and potato"),
    (65, "Christstollen", "Dresden Christmas bread with marzipan, dried fruit, and candied peel"),
    (65, "Nürnberger Rostbratwurst", "Tiny Nuremberg sausages grilled over charcoal in a bun with mustard"),
    (65, "Milchreis", "German rice pudding cooked in milk with cinnamon-sugar and topped with cherries"),
    (65, "Kaiserschmarrn", "Austrian-German torn pancake with rum raisins and powdered sugar"),

    # ─── Kraków Corner (66) — eastern_european, supplemental ────────────────────
    (66, "Barszcz Czerwony", "Clear beet consommé with ear-shaped mushroom dumplings — Christmas tradition"),
    (66, "Flaki", "Polish tripe soup with marjoram, ginger, and allspice in a clear broth"),
    (66, "Czernina", "Polish duck blood soup with dried prunes and homemade noodles — unique and ancient"),
    (66, "Rosół", "Polish golden chicken broth with fine noodles and parsley — Sunday comfort"),
    (66, "Beet Kvass", "Fermented beet drink — earthy, slightly sour, and deeply colored"),
    (66, "Holubtsi", "Ukrainian cabbage rolls stuffed with beef and rice in tomato cream sauce"),
    (66, "Varenyky z Vyshniamy", "Ukrainian sweet cherry dumplings with sour cream and sugar"),
    (66, "Kluski Śląskie", "Silesian potato dumplings with a dimple in the center, served with roast pork"),
    (66, "Gulasz Wieprzowy", "Polish pork goulash with sauerkraut, mushrooms, and tomato over noodles"),
    (66, "Faworki", "Polish angel wings — deep-fried pastry ribbons dusted with powdered sugar"),
    (66, "Makowniki", "Rolled poppy seed cake with candied orange peel and honey"),

    # ─── Hội An Garden (67) — vietnamese, supplemental ─────────────────────────
    (67, "Cao Lầu", "Hội An signature chewy noodle dish with pork, bean sprouts, and crispy croutons"),
    (67, "White Rose Dumplings", "Delicate Hội An steamed shrimp dumplings shaped like white roses"),
    (67, "Cơm Gà Hội An", "Hội An yellow turmeric chicken rice — chicken thigh over fragrant garlic rice"),
    (67, "Bánh Đập", "Grilled sticky rice cake with fresh rice paper and sweet scallion oil"),
    (67, "Bún Đậu Mắm Tôm", "Northern fried tofu and pork with vermicelli and fermented shrimp paste"),
    (67, "Bánh Mì Chả Cá", "Vietnamese baguette with fish cake, chili, pickled daikon, and mayo"),
    (67, "Chả Giò", "Crispy deep-fried pork and glass noodle spring rolls with nuoc cham"),
    (67, "Súp Cua", "Vietnamese crab egg drop soup with glass noodles and shallot oil"),
    (67, "Bánh Ít Lá Gai", "Dark sticky rice cake wrapped in ramie leaf with mung bean and coconut"),
    (67, "Sinh Tố Dừa", "Fresh coconut water blended with coconut meat, condensed milk, and ice"),
    (67, "Nước Mía", "Fresh-pressed sugarcane juice with kumquat — common street drink"),
    (67, "Chè Đậu Xanh", "Sweet warm mung bean dessert soup with coconut milk and pandan leaf"),

    # ─── Kamayan Table (68) — filipino, supplemental ────────────────────────────
    (68, "Kamayan Feast", "Traditional Filipino feast eaten by hand on banana leaves with lechon and sides"),
    (68, "Bulalo de Batangas", "Batangas-style beef shank soup with marrow, corn, and winter vegetables"),
    (68, "Pinapaitan", "Bitter Ilocano soup of goat offal with bile, ginger, and chili"),
    (68, "Sinigang sa Miso", "Pork or fish tamarind soup enriched with miso paste and mustard greens"),
    (68, "Kare-Kare Extras", "Bagoong seafood paste and extra oxtail sides for the peanut stew"),
    (68, "Dinakdakan", "Ilocano grilled pork face salad with calamansi, onion, and mayonnaise"),
    (68, "Ginataan", "Sweet coconut milk dessert stew with saba banana, jackfruit, and sticky rice balls"),
    (68, "Mango Float", "No-bake mango cream dessert with layers of graham crackers and sweetened cream"),
    (68, "Inihaw na Bangus", "Grilled milkfish stuffed with tomato, onion, and ginger with soy-vinegar dip"),
    (68, "Pork Barbecue Skewer", "Filipino pineapple-marinated pork skewers grilled over charcoal"),
    (68, "Pancit Malabon", "Thick rice noodles with shrimp, squid, oyster, and smoked fish sauce"),

    # ─── Javanese Kitchen (69) — indonesian, supplemental ───────────────────────
    (69, "Nasi Pecel", "Javanese rice with peanut-lime sauce over blanched vegetables"),
    (69, "Pecel Lele", "Javanese fried catfish with green sambal and steamed rice"),
    (69, "Rujak Cingur", "East Javanese salad with ox snout, tropical fruit, and black shrimp paste"),
    (69, "Soto Mie Bogor", "Bogor-style noodle soup with beef, risoles, and a tangy fermented sour note"),
    (69, "Asinan Betawi", "Jakarta pickled vegetable and fruit salad in vinegar peanut broth"),
    (69, "Kue Cucur", "Pan-fried palm sugar and rice flour soft-chewy cake — street snack"),
    (69, "Wedang Jahe", "Hot ginger and palm sugar drink infused with cloves and lemongrass"),
    (69, "Tahu Tek", "Surabaya-style tofu, potato, and bean sprout dish with peanut and shrimp paste"),
    (69, "Nasi Liwet Solo", "Coconut rice from Solo cooked in chicken broth with banana blossom and egg"),
    (69, "Serabi Notosuman", "Solo steamed rice flour pancake with coconut milk filling"),
    (69, "Jamu Kunyit Asam", "Traditional Javanese turmeric and tamarind herbal tonic drink"),

    # ─── Bahia Nordeste (70) — brazilian, supplemental ──────────────────────────
    (70, "Xinxim de Galinha", "Afro-Brazilian chicken stew with dried shrimp, peanut, and palm oil"),
    (70, "Caruru", "Stewed okra with dried shrimp, palm oil, and toasted peanut — Bahian classic"),
    (70, "Efó", "Leafy Bahian stew of spinach with dried shrimp, palm oil, and onion"),
    (70, "Angú", "Cornmeal porridge from Minas Gerais cooked thick with broth and drizzled in butter"),
    (70, "Frango com Quiabo", "Chicken with okra in a rich onion and garlic sauce from Minas Gerais"),
    (70, "Rapadura", "Solid unrefined cane sugar block eaten as candy or dissolved in drinks"),
    (70, "Beiju de Tapioca", "Dry tapioca crêpe filled with coconut or sweet guava paste"),
    (70, "Pé de Moleque", "Peanut brittle from the Northeast sold at street fairs"),
    (70, "Doce de Leite", "Brazilian milk caramel slow-cooked until thick and spreadable"),
    (70, "Suco de Açaí", "Cold açaí berry blend served thin as a juice with guaraná syrup"),
    (70, "Sopa Seca", "Dry noodle soup from Pará — pasta baked until crusted in tomato and chicken fat"),

    # ─── Kingston Yard (71) — caribbean, supplemental ───────────────────────────
    (71, "Mannish Water Stew", "Jamaican goat head broth with green banana, dumpling, and scotch bonnet"),
    (71, "Stew Peas", "Kidney bean and salted pigtail stew in rich coconut milk — Jamaican staple"),
    (71, "Mackerel Rundown", "Mackerel simmered in coconut milk with onion, scotch bonnet, and thyme"),
    (71, "Peanut Punch", "Blended peanut, condensed milk, vanilla, and nutmeg energy drink"),
    (71, "Crab and Callaloo", "Whole crab stewed with callaloo greens, coconut milk, and Scotch bonnet"),
    (71, "Conch Fritters", "Bahamian minced conch battered and deep-fried with hot sauce"),
    (71, "Piña Colada Mocktail", "Blended pineapple, coconut cream, and ice — tropical refresher"),
    (71, "Haitian Griot", "Marinated fried pork shoulder crisp outside with pikliz pickled slaw"),
    (71, "Accra", "Trinidadian salt fish fritters spiced with chili and herbs"),
    (71, "Jerk Mac and Cheese", "Creamy mac and cheese finished with jerk sauce and green onion"),
    (71, "Sweet Potato Pudding", "Jamaican baked sweet potato and coconut pudding with allspice"),

    # ─── Blue Nile Café (72) — ethiopian, supplemental ─────────────────────────
    (72, "Ye'difin Misir", "Whole lentil stew with onion, tomato, and niter kibbeh butter"),
    (72, "Asa Tibs", "Fish stir-fried with onion, rosemary, and jalapeño in spiced butter"),
    (72, "Gored Gored", "Cubed raw beef seasoned with mitmita and niter kibbeh — raw beef delicacy"),
    (72, "Ye'abesha Gomen", "Ethiopian mustard greens braised with onion, garlic, and ginger"),
    (72, "Kinche", "Cracked wheat porridge cooked with niter kibbeh and spices for breakfast"),
    (72, "Tikil Gomen", "Mild cabbage, potato, and carrot stew spiced with turmeric and cumin"),
    (72, "Alecha", "Mild lamb or chicken stew without berbere — turmeric and ginger forward"),
    (72, "Ye'beg Tibs", "Sautéed lamb cubes with onion and jalapeño in a hot clay pot"),
    (72, "Himbasha", "Slightly sweet Ethiopian celebration bread flavored with cardamom and black seed"),
    (72, "Ater Kik Alicha", "Split pea stew with onion, turmeric, and green chili — vegan fasting dish"),
    (72, "Shiro Tibs", "Chickpea powder stew mixed into sautéed lamb for a thick, spiced combination"),
]
