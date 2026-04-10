# Spotify Musical Time Machine

Scrapes Billboard Hot 100 for any date in history and creates a matching private Spotify playlist.

Enter a date in `YYYY-MM-DD` format — say `1998-03-01` — and the script scrapes that week's Billboard Hot 100, finds each of the 100 songs on Spotify using fuzzy title/artist matching (title weighted 80%, artist 20%), and creates a private playlist on your Spotify account named `"1998-03-01 Billboard Hot 100"`. Songs that can't be matched are printed to the terminal and saved to `advanced/output/unmatched_songs_{year}.txt`.

`original/` preserves the Day 46 course code verbatim — a single-file procedural script with all logic inline and credentials redacted. `advanced/` refactors the same logic into two focused classes (`BillboardScraper`, `SpotifyClient`) backed by a central `config.py`, adds the enhanced matching from the second course iteration (dual-title handling, year-bonus scoring, adaptive thresholds), and reads credentials from `.env` instead of hardcoded strings.

Uses the **Spotify Web API** via the [spotipy](https://spotipy.readthedocs.io/) library for OAuth 2.0 authentication, track search, and playlist management. Billboard Hot 100 is scraped directly from billboard.com using `requests` + `BeautifulSoup` — no Billboard API key is needed.

---

## Table of Contents

0. [Prerequisites](#0-prerequisites)
1. [Quick Start](#1-quick-start)
2. [Builds Comparison](#2-builds-comparison)
3. [Usage](#3-usage)
4. [Data Flow](#4-data-flow)
5. [Features](#5-features)
6. [Navigation Flow](#6-navigation-flow)
7. [Architecture](#7-architecture)
8. [Module Reference](#8-module-reference)
9. [Configuration Reference](#9-configuration-reference)
10. [Data Schema](#10-data-schema)
11. [Environment Variables](#11-environment-variables)
12. [Design Decisions](#12-design-decisions)
13. [Course Context](#13-course-context)
14. [Dependencies](#14-dependencies)

---

## 0. Prerequisites

You need a free Spotify Developer account to get API credentials.

1. Go to [developer.spotify.com](https://developer.spotify.com) and log in with your Spotify account.
2. Create an app: **Dashboard → Create App**.
   - App name: anything (e.g. `Musical Time Machine`)
   - Redirect URI: `http://127.0.0.1:8888/callback` ← must match exactly
3. Copy **Client ID** and **Client Secret** from the app settings page.
4. Add them to your `.env` file (see [Environment Variables](#11-environment-variables)).

On first run, a browser window will open asking you to authorise the app. After you approve, Spotipy saves a token cache to `advanced/data/token.txt` so subsequent runs skip the browser step.

---

## 1. Quick Start

```bash
# Clone and install dependencies
git clone https://github.com/xavier-oc-programming/day46-spotify-time-machine.git
cd day46-spotify-time-machine
pip install -r requirements.txt

# Add Spotify credentials
cp .env.example .env
# Edit .env and fill in SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET

# Launch the menu
python menu.py

# Or run the advanced build directly
python advanced/main.py
```

---

## 2. Builds Comparison

| Feature | `original/` | `advanced/` |
|---|---|---|
| Structure | Single file, procedural | Three modules + config |
| Credentials | Hardcoded (redacted `*****`) | Read from `.env` |
| Dual-title handling | No | Yes (`"A/B"` → tries each part) |
| Adaptive threshold | Fixed 75 | Relaxed to 75 for 3+ artists |
| Year-bonus scoring | No | Yes (broad fallback query) |
| Output path | Relative to CWD | `advanced/output/` |
| Token cache | `original/token.txt` | `advanced/data/token.txt` |

---

## 3. Usage

```
$ python advanced/main.py

Which year do you want to travel to? Type the date in this format YYYY-MM-DD: 1998-03-01

Scraped 100 songs from Billboard Hot 100 (1998-03-01).
  - Too Close — Next
  - My Heart Will Go On (Love Theme From "Titanic") — Celine Dion
  - Together Again — Janet
  - Gettin' Jiggy Wit It — Will Smith
  - Nice & Slow — Usher

Logged in as Spotify user: yourspotifyusername

Searching Spotify for 100 songs...
[OK] Too Close — Next -> Too Close by ['Next'] (100%)
[OK] My Heart Will Go On — Celine Dion -> My Heart Will Go On by ['Celine Dion'] (95%)
...
[--] Skipped: Young, Sad And Blue — Lysette (62%)

Matched 97 tracks; unmatched: 3

3 songs were not found on Spotify:
  - Candle In The Wind 1997/Something About The Way You Look Tonight — Elton John
  - 4, 3, 2, 1 — LL Cool J, Method Man, Redman, DMX, Canibus And Master P
  - Young, Sad And Blue — Lysette

Saved unmatched songs to 'advanced/output/unmatched_songs_1998.txt'.

Playlist created: 1998-03-01 Billboard Hot 100
Open in Spotify: https://open.spotify.com/playlist/...
```

---

## 4. Data Flow

```
Input (date string)
    │
    ▼
BillboardScraper.scrape()
    │  requests.get(billboard.com/charts/hot-100/{date})
    │  BeautifulSoup CSS selectors → list of (title, artist)
    ▼
SpotifyClient.collect_uris()
    │  For each (title, artist):
    │    multi-stage Spotify search → fuzzy score → URI or None
    ▼
SpotifyClient.create_playlist()
    │  user_playlist_create() → playlist_id
    │  playlist_add_items() in batches of 100
    ▼
Output
    ├── Spotify private playlist (in your account)
    └── advanced/output/unmatched_songs_{year}.txt
```

---

## 5. Features

### Both builds
- Scrapes Billboard Hot 100 for any historical date
- Multi-stage Spotify search: `track+artist+year` → `track+artist` → `track` only
- Weighted fuzzy scoring: title 80%, artist 20%
- Deduplicates Billboard results before searching
- Saves unmatched songs to a text file
- Creates a private Spotify playlist with matched songs

### Advanced only
- Dual-title handling: `"Song A/Song B"` tries each part separately
- Adaptive threshold: relaxed to 75 for tracks with 3+ credited artists
- Year-bonus scoring in broad fallback: blends title match with release year
- OOP modules with clear separation of concerns
- Credentials via `.env` (not hardcoded)
- All constants in a single `config.py`

---

## 6. Navigation Flow

```
python menu.py
│
├── 1 → original/main.py
│       Input date → scrape → auth → search → create playlist
│
├── 2 → advanced/main.py
│       Input date → BillboardScraper → SpotifyClient → create playlist
│
└── q → exit
```

---

## 7. Architecture

```
day46-spotify-time-machine/
│
├── menu.py                     # Entry point: build selector
├── art.py                      # LOGO displayed by menu.py
├── requirements.txt
├── .env.example                # Credential template (committed)
├── .env                        # Real credentials (gitignored)
│
├── original/
│   └── main.py                 # Course code verbatim (credentials redacted)
│
├── advanced/
│   ├── config.py               # All constants + text helper functions
│   ├── scraper.py              # BillboardScraper — web scraping
│   ├── client.py               # SpotifyClient — auth, search, playlist
│   ├── main.py                 # Orchestrator
│   ├── data/
│   │   ├── .gitkeep
│   │   └── token.txt           # OAuth cache — gitignored, auto-generated
│   └── output/
│       └── unmatched_songs_1998.txt  # Example output (committed)
│
└── docs/
    └── COURSE_NOTES.md
```

---

## 8. Module Reference

### `advanced/scraper.py` — `BillboardScraper`

| Method | Returns | Description |
|---|---|---|
| `scrape(date_str)` | `List[Tuple[str, str]]` | Scrapes Hot 100 for date, returns `[(title, artist), ...]` |
| `_deduplicate(rows)` | `List[Tuple[str, str]]` | Removes duplicate `(title, artist)` pairs |

### `advanced/client.py` — `SpotifyClient`

| Method | Returns | Description |
|---|---|---|
| `__init__()` | — | Authenticates via OAuth; caches user ID |
| `user_id` | `str` | Property: Spotify user ID of authenticated user |
| `find_track(song, artist, year, threshold)` | `Optional[str]` | Fuzzy-searches Spotify; returns URI or `None` |
| `collect_uris(rows, year, threshold)` | `Tuple[List[str], List[Tuple]]` | Batch version of `find_track`; returns `(uris, not_found)` |
| `create_playlist(date_str, uris)` | `dict` | Creates private playlist, adds tracks, returns playlist object |
| `_build_queries(song, artist, year)` | `List[str]` | Builds ordered list of Spotify search queries |
| `_score_track(track, variant, artists, year, is_broad)` | `float` | Computes weighted fuzzy score for one Spotify track |

### `advanced/config.py`

| Item | Type | Description |
|---|---|---|
| `normalize_text(text)` | `str → str` | Lowercase + strip noise for fuzzy comparison |
| `clean_artist_field(artist)` | `str → str` | Normalise Billboard separators to commas |

---

## 9. Configuration Reference

| Constant | Default | Description |
|---|---|---|
| `BILLBOARD_BASE_URL` | `https://www.billboard.com/...` | URL template for Hot 100 chart |
| `USER_AGENT` | Chrome 140 string | HTTP User-Agent header for scraping |
| `REQUEST_TIMEOUT` | `30` | Seconds before Billboard request times out |
| `SPOTIFY_SCOPE` | `playlist-modify-private` | OAuth permission scope |
| `SPOTIFY_REDIRECT_URI` | `http://127.0.0.1:8888/callback` | OAuth redirect (must match Spotify app settings) |
| `FUZZY_THRESHOLD` | `80` | Minimum weighted score to accept a match |
| `MULTI_ARTIST_THRESHOLD` | `75` | Relaxed threshold for tracks with 3+ artists |
| `TITLE_WEIGHT` | `0.8` | Weight of title score in standard matching |
| `ARTIST_WEIGHT` | `0.2` | Weight of artist score in standard matching |
| `TITLE_WEIGHT_BROAD` | `0.7` | Title weight in ultra-broad fallback query |
| `YEAR_WEIGHT_BROAD` | `0.3` | Year-bonus weight in ultra-broad fallback |
| `YEAR_BONUS_HIT` | `100` | Bonus score when release year matches |
| `YEAR_BONUS_MISS` | `70` | Bonus score when release year does not match |
| `SEARCH_LIMIT` | `10` | Max Spotify tracks returned per search query |
| `SEARCH_DELAY` | `0.05` | Seconds between Spotify API calls |
| `PLAYLIST_BATCH_SIZE` | `100` | Tracks per `playlist_add_items` call (API limit) |

---

## 10. Data Schema

### Billboard scrape output
```
List[Tuple[str, str]]
  (song_title, artist_name)
  e.g. ("Too Close", "Next")
```

### `advanced/output/unmatched_songs_{year}.txt`
```
Unmatched songs from Billboard Hot 100 (YYYY-MM-DD)
============================================================

- Song Title — Artist Name
- Song Title — Artist Name
```

### `advanced/data/token.txt` (auto-generated, gitignored)
```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "playlist-modify-private",
  "expires_at": 1234567890,
  "refresh_token": "..."
}
```

---

## 11. Environment Variables

| Variable | Description | Where to find |
|---|---|---|
| `SPOTIFY_CLIENT_ID` | Your Spotify app's Client ID | Spotify Developer Dashboard → your app → Settings |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify app's Client Secret | Spotify Developer Dashboard → your app → Settings |

Copy `.env.example` to `.env` and fill in both values.

**Gotcha:** The redirect URI in your Spotify app settings must be exactly `http://127.0.0.1:8888/callback`.

**Gotcha:** On first run, a browser window opens for OAuth authorisation. Approve it and the token is cached in `advanced/data/token.txt` for subsequent runs.

---

## 12. Design Decisions

**Fuzzy matching over exact search** — Billboard and Spotify use different title/artist formats (e.g., `"feat."` vs `"Featuring"`, remaster suffixes, compilation editions). Exact string matching would miss a large fraction of valid songs. `rapidfuzz.partial_ratio` handles these discrepancies reliably.

**Title weighted higher than artist (80/20)** — The song title is more stable across catalogue versions than artist credits. A remix or compilation may list different featured artists on Spotify vs. Billboard, so artist score is secondary.

**Multi-stage search (specific → broad)** — Starting with `track+artist+year` gives the most accurate results; falling back to `track` only recovers songs where the artist string differs significantly. The ultra-broad `query=song_name` fallback uses year-bonus scoring to avoid false positives from unrelated songs with common titles.

**Dual-title handling (`"A/B"` split)** — Some Billboard entries combine two song titles with `/` (e.g., `"Candle In The Wind 1997/Something About The Way You Look Tonight"`). Splitting and trying each part separately recovers matches that the combined title misses entirely.

**Adaptive threshold for multi-artist tracks** — Tracks crediting 3+ artists (common in rap features) often have artist strings long enough to score poorly in fuzzy comparison. Relaxing the threshold from 80 to 75 for these entries reduces false rejections.

**Token cache in `advanced/data/`** — Storing the OAuth cache inside the project (gitignored) keeps it co-located with the code and avoids polluting the working directory. Spotipy refreshes the access token automatically using the cached refresh token.

**`sys.path.insert` in `advanced/main.py`** — The advanced modules use bare `from config import ...` style imports. Inserting the `advanced/` directory at position 0 ensures this works when `main.py` is called from any working directory (including from `menu.py` via `subprocess.run`).

---

## 13. Course Context

**Course:** 100 Days of Code: The Complete Python Pro Bootcamp  
**Day:** 46  
**Topic:** Spotify API + web scraping  

The original exercise introduces OAuth 2.0 authentication, the Spotify Web API, and web scraping in a single project. The advanced build adds OOP structure, environment-variable credentials, and the enhanced matching algorithm developed in the second course iteration.

---

## 14. Dependencies

| Module | Used in | Purpose |
|---|---|---|
| `requests` | `scraper.py` | HTTP GET for Billboard page |
| `beautifulsoup4` | `scraper.py` | Parse Billboard HTML, CSS selectors |
| `spotipy` | `client.py` | Spotify Web API client + OAuth 2.0 |
| `rapidfuzz` | `client.py` | Fast fuzzy string matching |
| `python-dotenv` | `advanced/main.py` | Load `.env` credentials |
| `re` | `config.py`, `client.py` | Regex-based text normalisation |
| `pathlib` | `config.py`, all | Cross-platform file paths |
