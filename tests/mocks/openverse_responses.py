"""Mock Openverse API responses for tests."""

OPENVERSE_RESULTS_CC_BY_SA = {
    "count": 2,
    "results": [
        {
            "id": "abc123",
            "url": "https://openverse.example.com/food1.jpg",
            "foreign_landing_url": "https://openverse.example.com/food1",
            "license": "by-sa",
            "license_version": "4.0",
            "creator": "Chef Photo",
        },
        {
            "id": "def456",
            "url": "https://openverse.example.com/food2.jpg",
            "foreign_landing_url": "https://openverse.example.com/food2",
            "license": "cc0",
            "license_version": "1.0",
            "creator": "Public Domain Cook",
        },
    ],
}

OPENVERSE_RESULTS_UNLICENSED = {
    "count": 1,
    "results": [
        {
            "id": "xyz789",
            "url": "https://openverse.example.com/food3.jpg",
            "foreign_landing_url": "https://openverse.example.com/food3",
            "license": "all-rights-reserved",
            "license_version": "",
            "creator": "Restricted Author",
        },
    ],
}

OPENVERSE_RESULTS_EMPTY = {"count": 0, "results": []}

OPENVERSE_RESULTS_PDM = {
    "count": 1,
    "results": [
        {
            "id": "pdm001",
            "url": "https://openverse.example.com/pd_food.jpg",
            "foreign_landing_url": "https://openverse.example.com/pd_food",
            "license": "pdm",
            "license_version": "1.0",
            "creator": "",
        },
    ],
}
