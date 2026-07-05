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
    set_premium,
    create_billing_session,
    get_billing_session,
    complete_billing_session,
    generate_verification_code,
    set_email_verified,
    upsert_verification,
    get_verification,
    bump_verification_attempts,
    delete_verification,
    verification_is_expired,
    verification_resend_too_soon,
    verification_code_matches,
    VERIFICATION_MAX_ATTEMPTS,
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
    get_items_for_judging,
    get_rejected_items,
    update_food_item_image,
    update_food_item_judgement,
    update_food_item_embedding,
    update_food_item_tags,
    mark_food_item_tagging_failed,
    clear_eligible_cache,
)
from db.swipe_events import (
    record_swipe,
    recent_rejection_rate,
    days_since_last_swipe,
    get_swiped_cuisines,
    get_swipe_stats,
    get_insights,
    delete_swipes_for_user,
    delete_impressions_for_user,
    get_all_swipes_for_user,
    consume_snapshot_item,
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
    "generate_verification_code", "set_email_verified", "upsert_verification",
    "get_verification", "bump_verification_attempts", "delete_verification",
    "verification_is_expired", "verification_resend_too_soon",
    "verification_code_matches", "VERIFICATION_MAX_ATTEMPTS",
    # food
    "insert_food_item", "insert_restaurant", "get_restaurant_by_name",
    "get_food_item_by_name", "get_embeddings_for_items", "get_untagged_items",
    "get_eligible_food_items", "get_popular_food_items", "get_food_item",
    "list_food_items", "list_restaurants",
    "record_impression", "get_least_impressed", "get_items_without_embedding",
    "get_items_without_image", "get_items_for_judging", "get_rejected_items",
    "update_food_item_image", "update_food_item_judgement",
    "update_food_item_embedding", "update_food_item_tags",
    "mark_food_item_tagging_failed", "clear_eligible_cache",
    # swipe_events
    "record_swipe", "recent_rejection_rate", "days_since_last_swipe",
    "get_swiped_cuisines", "get_swipe_stats", "get_insights",
    "delete_swipes_for_user", "delete_impressions_for_user", "get_all_swipes_for_user",
    "consume_snapshot_item",
    # users (delete)
    "delete_user",
]
