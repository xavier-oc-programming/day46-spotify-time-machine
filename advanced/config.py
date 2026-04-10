import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# URLs
BILLBOARD_BASE_URL = "https://www.billboard.com/charts/hot-100/{date}"

# Scraping
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30

# Spotify API
SPOTIFY_SCOPE = "playlist-modify-private"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
SPOTIFY_CACHE_PATH = str(DATA_DIR / "token.txt")

# Fuzzy matching / thresholds
FUZZY_THRESHOLD = 80
MULTI_ARTIST_THRESHOLD = 75  # relaxed threshold for tracks with 3+ artists
TITLE_WEIGHT = 0.8
ARTIST_WEIGHT = 0.2
TITLE_WEIGHT_BROAD = 0.7   # used in ultra-broad fallback query
YEAR_WEIGHT_BROAD = 0.3    # blended with title in ultra-broad fallback
YEAR_BONUS_HIT = 100       # score bonus when release year matches
YEAR_BONUS_MISS = 70       # score when release year does not match
SEARCH_LIMIT = 10

# Timing / rate limits
SEARCH_DELAY = 0.05  # seconds between Spotify API search calls

# Output / formatting
OUTPUT_FILENAME = "unmatched_songs_{year}.txt"
PLAYLIST_NAME = "{date} Billboard Hot 100"
PLAYLIST_DESCRIPTION = "Top 100 songs from Billboard Hot 100 on {date}"
PLAYLIST_BATCH_SIZE = 100  # Spotify add-items API limit


# ============================================================
# Pure text helpers — used by both scraper and client
# ============================================================

def normalize_text(text: str) -> str:
    """Lowercase, strip noise words and punctuation for fuzzy comparison."""
    t = text.lower()
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[-–—]", " ", t)
    t = re.sub(r"\b(feat\.|featuring|ft\.|remaster(ed)?|version|mix|edit)\b", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def clean_artist_field(artist: str) -> str:
    """Normalise Billboard artist strings: convert separators to commas."""
    if not artist:
        return ""
    artist = re.sub(r"(?i)featuring", ",", artist)
    artist = re.sub(r"(?i)\bfeat\.\b", ",", artist)
    artist = re.sub(r"(?i)\band\b", ",", artist)
    artist = artist.replace("&", ",")
    artist = re.sub(r"\s*,\s*", ", ", artist)
    artist = re.sub(r"\s{2,}", " ", artist)
    return artist.strip()
