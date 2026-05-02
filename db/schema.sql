-- Cravings Database Schema
-- SQL-standard for SQLite (local dev) → PostgreSQL (production) portability

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    api_token TEXT NOT NULL UNIQUE,

    -- dietary_flags_bitmask: same bit positions as food_items.dietary_flags_bitmask
    --   0=vegetarian, 1=vegan, 2=gluten_free, 3=dairy_free, 4=halal, 5=kosher,
    --   6=contains_nuts, 7=contains_shellfish, 8=contains_soy, 9=contains_eggs
    dietary_flags_bitmask INTEGER NOT NULL DEFAULT 0,
    -- safety_overrides_bitmask: bits set = user opts INTO that hard-safety risk
    --   bits match food_items.safety_risk_bitmask: 0=raw_fish, 1=raw_egg, 2=raw_meat,
    --   3=unpasteurized_dairy, 4=high_mercury_fish
    safety_overrides_bitmask INTEGER NOT NULL DEFAULT 0,

    -- Per-user Thompson Sampling model state
    mu_blob BLOB,                              -- numpy μ vector pickle
    b_blob BLOB,                               -- precision matrix B pickle
    total_swipes INTEGER NOT NULL DEFAULT 0,
    last_decay_ts REAL,                        -- unix timestamp of last decay
    drift_active INTEGER NOT NULL DEFAULT 0,   -- 0/1 boolean

    onboarding_complete INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_api_token ON users(api_token);

CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT,
    cuisine_type TEXT,
    source_type TEXT NOT NULL DEFAULT 'manual',  -- manual | api
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS food_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    restaurant_id INTEGER REFERENCES restaurants(id),

    -- Flavor Profile (6 continuous)
    spice_level REAL,
    sweetness REAL,
    sourness REAL,
    savory_umami REAL,
    saltiness REAL,
    bitterness REAL,

    -- Physical Properties (4 continuous)
    temperature REAL,
    texture_softness REAL,
    sauce_heaviness REAL,
    richness REAL,

    -- Composition (3 categorical + 2 continuous)
    protein_type TEXT,      -- chicken|beef|pork|fish|shellfish|egg|tofu_plant|legume|none
    cuisine_type TEXT,      -- american|mexican|italian|chinese|japanese|thai|indian|korean|mediterranean|middle_eastern|other
    carb_base TEXT,         -- rice|noodles_pasta|bread|potato|tortilla|none
    veggie_density REAL,
    dairy_content REAL,

    -- Sensory Signals
    smell_intensity REAL,
    nausea_trigger REAL,

    -- Safety & Dietary Bitmasks
    -- safety_risk_bitmask bits: 0=raw_fish, 1=raw_egg, 2=raw_meat, 3=unpasteurized_dairy, 4=high_mercury_fish
    safety_risk_bitmask INTEGER NOT NULL DEFAULT 0,
    -- dietary_flags_bitmask bits: 0=vegetarian, 1=vegan, 2=gluten_free, 3=dairy_free,
    --   4=halal, 5=kosher, 6=contains_nuts, 7=contains_shellfish, 8=contains_soy, 9=contains_eggs
    dietary_flags_bitmask INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    tagging_status TEXT NOT NULL DEFAULT 'pending',  -- pending | tagged | failed
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS swipe_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    food_item_id INTEGER NOT NULL REFERENCES food_items(id),
    direction TEXT NOT NULL,  -- right | left
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Context snapshot (denormalized — state at time of swipe)
    dietary_mode TEXT,       -- standard | vegetarian | vegan | restricted
    time_of_day REAL,        -- hour as decimal (0.0-23.99)
    mood TEXT,               -- comfort | adventurous | light_healthy | no_preference
    recent_rejection_rate REAL NOT NULL DEFAULT 0.0,
    days_since_last_session REAL NOT NULL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_food_items_restaurant ON food_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_food_items_tagging_status ON food_items(tagging_status);
CREATE INDEX IF NOT EXISTS idx_food_items_safety ON food_items(safety_risk_bitmask);
CREATE INDEX IF NOT EXISTS idx_swipe_events_food_item ON swipe_events(food_item_id);
CREATE INDEX IF NOT EXISTS idx_swipe_events_user ON swipe_events(user_id);
CREATE INDEX IF NOT EXISTS idx_swipe_events_timestamp ON swipe_events(timestamp);
