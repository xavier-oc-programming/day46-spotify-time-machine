# Day 46 — Spotify Musical Time Machine

## Course Exercise

**100 Days of Code: The Complete Python Pro Bootcamp** — Day 46

### Task Description

Build a "Musical Time Machine" that:

1. Asks the user to enter any date in `YYYY-MM-DD` format.
2. Scrapes the **Billboard Hot 100** chart for that date using `requests` and `BeautifulSoup`.
3. Authenticates with the **Spotify Web API** using `spotipy` and OAuth 2.0.
4. Searches for each scraped song on Spotify.
5. Creates a **private playlist** on the user's Spotify account containing all matched songs.

### Core Concepts Practiced

- Web scraping with `requests` + `BeautifulSoup` (CSS selectors)
- OAuth 2.0 authentication flow with `spotipy`
- Spotify Web API: search, user playlists, add items
- String manipulation and data cleaning
- Error handling for unmatched songs

### Original Files

- `main.py` — Final optimized version (threshold 75, title/artist weighted scoring)
- `main2.py` — Enhanced iteration (threshold 80, dual-title handling, year-bonus scoring, adaptive thresholds for multi-artist tracks)
- `token.txt` — Spotify OAuth token cache (not committed — sensitive)
- `unmatched_songs_1998.txt` — Sample output from a 1998-03-01 run

### Notes

- `token.txt` is generated automatically by `spotipy` on first run (OAuth browser flow).
- Billboard Hot 100 is scraped directly — no API key needed.
- Credentials were hardcoded in original course files; redacted with `*****` in committed versions.
