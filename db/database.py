"""Re-export hub for backward compatibility. Import from sub-modules for new code:
  db.connection  — connection management, schema init
  db.users       — user CRUD, auth, password
  db.food        — food items, restaurants, embeddings, impressions
  db.swipe_events — swipe recording, stats, cuisine history
"""

from db.connection import (
    SCHEMA_PATH,
    DEFAULT_DB_PATH,
    get_connection,
    db_connection,
    init_db,
    _migrate,
)
from db.users import (
    generate_api_token,
    insert_user,
    get_user_by_token,
    get_user,
    update_user_model_state,
    update_user_dietary,
    update_user_onboarding,
    mark_onboarding_complete,
    get_user_by_email,
    attach_credentials,
    create_registered_user,
    rotate_api_token,
    update_password,
    hash_password,
    verify_password,
    get_recent_likes,
    push_recent_like,
    delete_user,
)
from db.food import (
    insert_food_item,
    insert_restaurant,
    get_restaurant_by_name,
    get_food_item_by_name,
    get_embeddings_for_items,
    get_untagged_items,
    get_eligible_food_items,
    get_popular_food_items,
    get_food_item,
    list_food_items,
    list_restaurants,
    record_impression,
    get_least_impressed,
    get_items_without_embedding,
    get_items_without_image,
    update_food_item_image,
    update_food_item_embedding,
    update_food_item_tags,
)
from db.swipe_events import (
    record_swipe,
    recent_rejection_rate,
    days_since_last_swipe,
    get_swiped_cuisines,
    get_swipe_stats,
    delete_swipes_for_user,
    delete_impressions_for_user,
    get_all_swipes_for_user,
)

__all__ = [
    # connection
    "SCHEMA_PATH", "DEFAULT_DB_PATH", "get_connection", "db_connection", "init_db", "_migrate",
    # users
    "generate_api_token", "insert_user", "get_user_by_token", "get_user",
    "update_user_model_state", "update_user_dietary", "update_user_onboarding",
    "mark_onboarding_complete", "get_user_by_email", "attach_credentials",
    "create_registered_user", "rotate_api_token", "update_password",
    "hash_password", "verify_password", "get_recent_likes", "push_recent_like",
    # food
    "insert_food_item", "insert_restaurant", "get_restaurant_by_name",
    "get_food_item_by_name", "get_embeddings_for_items", "get_untagged_items",
    "get_eligible_food_items", "get_popular_food_items", "get_food_item",
    "list_food_items", "list_restaurants",
    "record_impression", "get_least_impressed", "get_items_without_embedding",
    "get_items_without_image", "update_food_item_image", "update_food_item_embedding",
    "update_food_item_tags",
    # swipe_events
    "record_swipe", "recent_rejection_rate", "days_since_last_swipe",
    "get_swiped_cuisines", "get_swipe_stats",
    "delete_swipes_for_user", "delete_impressions_for_user", "get_all_swipes_for_user",
    # users (delete)
    "delete_user",
]
