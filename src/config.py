"""Configuration for VCT Calendar scraper."""

BASE_URL = "https://www.vlr.gg"

STAGES = {
    "kickoff": {"id": 45, "name": "Kickoff", "active": True},
    "masters": {"id": 46, "name": "Masters", "active": False},
    "stage1": {"id": 1, "name": "Stage 1", "active": False},
    "stage2": {"id": 16, "name": "Stage 2", "active": False},
    "champions": {"id": 47, "name": "Champions", "active": False},
}

EXCLUDED_REGIONS = []  # Include all regions (Americas, EMEA, Pacific, China)

REQUEST_DELAY = 1.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
