"""Canned Wikimedia API responses for testing."""

SPARQL_TIER1_HIT = {
    "results": {
        "bindings": [
            {
                "image": {
                    "type": "uri",
                    "value": "http://commons.wikimedia.org/wiki/Special:FilePath/Spaghetti_carbonara.jpg"
                }
            }
        ]
    }
}

SPARQL_TIER1_MISS = {
    "results": {"bindings": []}
}

WIKIPEDIA_PAGEIMAGE_HIT = {
    "type": "standard",
    "title": "Carbonara",
    "originalimage": {
        "source": "https://upload.wikimedia.org/wikipedia/commons/1/1/Carbonara.jpg",
        "width": 2000,
        "height": 1500,
    },
    "thumbnail": {
        "source": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1/Carbonara.jpg/330px-Carbonara.jpg",
        "width": 330,
        "height": 248,
    }
}

WIKIPEDIA_PAGEIMAGE_MISS = None  # 404 response

# Simulates Wikipedia returning a thumbnail URL with URL-encoded filename (e.g. commas → %2C)
WIKIPEDIA_PAGEIMAGE_THUMBNAIL_ENCODED = {
    "type": "standard",
    "title": "Fried rice",
    "originalimage": {
        "source": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Koh_Mak%2C_Thailand%2C_Fried_rice.jpg/3840px-Koh_Mak%2C_Thailand%2C_Fried_rice.jpg",
        "width": 3840,
        "height": 2880,
    },
}

COMMONS_EXTMETA_CC_BY_SA = {
    "query": {
        "pages": {
            "99": {
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/1/1/Carbonara.jpg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Carbonara.jpg",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY-SA 4.0"},
                            "Artist": {"value": "Jane Photographer"},
                        }
                    }
                ]
            }
        }
    }
}

COMMONS_EXTMETA_REJECTED = {
    "query": {
        "pages": {
            "99": {
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/1/1/Foo.jpg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Foo.jpg",
                        "extmetadata": {
                            "LicenseShortName": {"value": "All rights reserved"},
                            "Artist": {"value": "Proprietary Corp"},
                        }
                    }
                ]
            }
        }
    }
}

COMMONS_IMAGE_URL = {
    "query": {
        "pages": {
            "99": {
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/1/1/Carbonara.jpg",
                    }
                ]
            }
        }
    }
}
