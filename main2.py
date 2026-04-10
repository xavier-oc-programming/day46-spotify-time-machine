# Day 46 – Spotify Musical Time Machine (Final Enhanced Version)
# ------------------------------------------------------------
# Scrapes Billboard Hot 100 for a given date, cleans artist data,
# matches each song to Spotify using fuzzy logic (prioritizing title accuracy),
# and creates a private playlist on the user's Spotify account.
# ------------------------------------------------------------

import os
import re
import sys
import time
import warnings
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from rapidfuzz import fuzz

# Silence non-critical warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# ============================================================
# TEXT CLEANUP HELPERS
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize song/artist strings for fuzzy comparison:
    - Lowercase
    - Remove parentheses (e.g., Remastered 2011)
    - Unify punctuation and spaces
    - Remove common noise words (feat., version, edit)
    """
    t = text.lower()
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[-–—]", " ", t)
    t = re.sub(r"\b(feat\.|featuring|ft\.|remaster(ed)?|version|mix|edit)\b", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def clean_artist_field(artist: str) -> str:
    """
    Standardize Billboard artist strings before matching:
    - Convert 'Featuring', 'feat.', '&', 'and' → commas
    - Ensure proper spacing between names
    """
    if not artist:
        return ""
    artist = re.sub(r"(?i)featuring", ",", artist)
    artist = re.sub(r"(?i)\bfeat\.\b", ",", artist)
    artist = artist.replace("&", ",")
    artist = re.sub(r"(?i)\band\b", ",", artist)
    artist = re.sub(r"\s*,\s*", ", ", artist)
    artist = re.sub(r"\s{2,}", " ", artist)
    return artist.strip()


# ============================================================
# STEP 1 — SCRAPE BILLBOARD HOT 100
# ============================================================

def scrape_billboard(date_str: str) -> List[Tuple[str, str]]:
    """
    Scrape Billboard Hot 100 for a specific date.
    Returns a list of (song_title, artist_name) tuples.
    """
    url = f"https://www.billboard.com/charts/hot-100/{date_str}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title_tags = soup.select("li ul li h3")
    data = []

    for h3 in title_tags:
        title = h3.get_text(strip=True)
        if not title:
            continue

        artist = ""
        li = h3.find_parent("li")
        if li:
            artist_span = li.select_one("span.c-label.a-no-trucate")
            if artist_span:
                artist = clean_artist_field(artist_span.get_text(strip=True))

        data.append((title, artist))

    # Deduplicate
    seen = set()
    unique = []
    for t, a in data:
        key = (t, a)
        if key not in seen:
            seen.add(key)
            unique.append((t, a))
    return unique


# ============================================================
# STEP 2 — AUTHENTICATE WITH SPOTIFY
# ============================================================

def spotify_client() -> spotipy.Spotify:
    """
    Authenticate and return a Spotify client instance.
    """
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-private",
            redirect_uri="http://127.0.0.1:8888/callback",
            client_id="*****",  # e.g. "a1b2c3d4e5f6abc1234567890abcdef1"
            client_secret="*****",  # e.g. "a1b2c3d4e5f6abc1234567890abcdef1"
            show_dialog=True,
            cache_path="token.txt",
        )
    )


# ============================================================
# STEP 3 — FUZZY MATCHING WITH SMART FALLBACK
# ============================================================

def find_best_match(
    sp: spotipy.Spotify,
    song_name: str,
    artist_name: str,
    year: str,
    threshold: int = 80
) -> Optional[str]:
    """
    Enhanced multi-stage Spotify matching for Billboard songs.

    Improvements:
    1. Handles dual-title songs (e.g., "A/B") by trying each part separately.
    2. Cleans artist lists ('and', 'feat.', '&') for accurate matching.
    3. Adds fallback that weights song title (70%) and year (30%).
    """

    # --- Clean inputs ---
    artist_name = re.sub(r"\(.*?\)", "", artist_name)
    artist_name = clean_artist_field(artist_name)
    artist_name = re.sub(r"(?i)\band\b", ",", artist_name)

    clean_song = normalize_text(song_name)
    billboard_artists = (
        [normalize_text(a) for a in re.split(r",\s*", artist_name)] if artist_name else []
    )

    # --- Handle dual-title entries ---
    title_variants = [song_name]
    if "/" in song_name:
        parts = [p.strip() for p in song_name.split("/") if len(p.strip()) > 3]
        title_variants.extend(parts)

    # Adaptive threshold for multi-artist songs
    dynamic_threshold = threshold
    if len(billboard_artists) > 2:
        dynamic_threshold = 75

    best_match = None
    highest_score = 0

    # --- Search query variations ---
    search_queries = []
    if artist_name:
        search_queries.append(f"track:{song_name} artist:{artist_name} year:{year}")
        search_queries.append(f"track:{song_name} artist:{artist_name}")
    search_queries.append(f"track:{song_name}")  # base fallback
    search_queries.append(song_name)  # ultra-broad fallback

    # --- Search process ---
    for title_variant in title_variants:
        clean_variant = normalize_text(title_variant)

        for query in search_queries:
            result = sp.search(q=query, type="track", limit=10)
            tracks = result.get("tracks", {}).get("items", [])
            if not tracks:
                continue

            for track in tracks:
                spotify_title = track["name"]
                spotify_artists = [a["name"] for a in track["artists"]]

                clean_spotify_title = normalize_text(spotify_title)
                clean_spotify_artists = [normalize_text(a) for a in spotify_artists]

                # Compare song titles
                title_score = fuzz.partial_ratio(clean_variant, clean_spotify_title)

                # Compare artists
                if billboard_artists and clean_spotify_artists:
                    lead_artist_score = fuzz.partial_ratio(
                        billboard_artists[0], clean_spotify_artists[0]
                    )
                    all_artist_scores = [
                        fuzz.partial_ratio(b_artist, s_artist)
                        for b_artist in billboard_artists
                        for s_artist in clean_spotify_artists
                    ]
                    artist_score = max(all_artist_scores + [lead_artist_score])
                else:
                    artist_score = title_score

                # Weighted scoring
                total_score = (title_score * 0.8) + (artist_score * 0.2)

                # If this is the broad fallback, blend year relevance
                if query == song_name:
                    year_bonus = 100 if year in track["album"]["release_date"] else 70
                    total_score = (title_score * 0.7) + (year_bonus * 0.3)

                if total_score > highest_score:
                    highest_score = total_score
                    best_match = track

            if best_match and highest_score >= dynamic_threshold:
                break
        if best_match and highest_score >= dynamic_threshold:
            break

    # --- Final result ---
    if best_match and highest_score >= dynamic_threshold:
        print(
            f"✅ {song_name} — {artist_name} → {best_match['name']} "
            f"by {[a['name'] for a in best_match['artists']]} ({int(highest_score)}%)"
        )
        return best_match["uri"]

    print(f"⚠️  Skipped: {song_name} — {artist_name} ({int(highest_score)}%)")
    return None


def collect_track_uris(sp: spotipy.Spotify,
                       billboard_rows: List[Tuple[str, str]],
                       year: str,
                       threshold: int = 80) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    For each Billboard (title, artist) row, find a Spotify URI via fuzzy match.
    """
    uris = []
    not_found = []

    print(f"\n🔎 Searching Spotify for {len(billboard_rows)} songs...")

    for i, (title, artist) in enumerate(billboard_rows, start=1):
        uri = find_best_match(sp, title, artist, year, threshold)
        if uri:
            uris.append(uri)
        else:
            not_found.append((title, artist))
        time.sleep(0.05)

    return uris, not_found


# ============================================================
# STEP 4 — CREATE PLAYLIST & ADD SONGS
# ============================================================

def create_playlist_and_add(sp: spotipy.Spotify,
                            user_id: str,
                            date_str: str,
                            uris: List[str]) -> dict:
    """
    Create a private Spotify playlist and populate it with the given URIs.
    """
    playlist = sp.user_playlist_create(
        user=user_id,
        name=f"{date_str} Billboard Hot 100",
        public=False,
        description=f"Top 100 songs from Billboard Hot 100 on {date_str}",
    )
    playlist_id = playlist["id"]

    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id=playlist_id, items=uris[i:i + 100])

    return playlist


# ============================================================
# MAIN EXECUTION FLOW
# ============================================================

def main():
    # User input
    date = input("Which year do you want to travel to? Type the date in this format YYYY-MM-DD: ").strip()
    year = date.split("-")[0]

    # Step 1: Billboard scrape
    billboard_data = scrape_billboard(date)
    print(f"\n✅ Scraped {len(billboard_data)} songs from Billboard Hot 100 ({date}).")
    for t, a in billboard_data[:5]:
        print(f"   - {t} — {a if a else '(artist unknown)'}")

    # Step 2: Spotify auth
    sp = spotify_client()
    user_id = sp.current_user()["id"]
    print(f"\n🎧 Logged in as Spotify user: {user_id}")

    # Step 3: Fuzzy matching
    uris, not_found = collect_track_uris(sp, billboard_data, year, threshold=80)
    print(f"\n✅ Found {len(uris)} Spotify track URIs; not matched: {len(not_found)}")

    # Save unmatched
    if not_found:
        print(f"\n⚠️  {len(not_found)} songs were not found on Spotify:")
        for title, artist in not_found:
            print(f"   - {title} — {artist if artist else '(artist unknown)'}")

        output_file = f"unmatched_songs_{year}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Unmatched songs from Billboard Hot 100 ({date})\n")
            f.write("=" * 60 + "\n\n")
            for title, artist in not_found:
                f.write(f"- {title} — {artist if artist else '(artist unknown)'}\n")
        print(f"\n💾 Saved unmatched songs list to '{output_file}'.")
    else:
        print("\n🎉 All Billboard songs were successfully matched on Spotify!")

    # Step 4: Playlist creation
    if uris:
        playlist = create_playlist_and_add(sp, user_id, date, uris)
        print(f"\n🎶 Playlist created: {playlist['name']}")
        print(f"👉 Open in Spotify: {playlist['external_urls']['spotify']}")
    else:
        print("\nNo songs found — playlist not created.")

    sys.exit(0)


if __name__ == "__main__":
    main()
