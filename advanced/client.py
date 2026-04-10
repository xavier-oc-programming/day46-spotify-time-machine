import os
import re
import time
from typing import List, Optional, Tuple

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from rapidfuzz import fuzz

from config import (
    SPOTIFY_SCOPE,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_CACHE_PATH,
    FUZZY_THRESHOLD,
    MULTI_ARTIST_THRESHOLD,
    TITLE_WEIGHT,
    ARTIST_WEIGHT,
    TITLE_WEIGHT_BROAD,
    YEAR_WEIGHT_BROAD,
    YEAR_BONUS_HIT,
    YEAR_BONUS_MISS,
    SEARCH_LIMIT,
    SEARCH_DELAY,
    PLAYLIST_NAME,
    PLAYLIST_DESCRIPTION,
    PLAYLIST_BATCH_SIZE,
    normalize_text,
    clean_artist_field,
)


class SpotifyClient:
    """Handles Spotify authentication, fuzzy track search, and playlist creation."""

    def __init__(self) -> None:
        self._sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=SPOTIFY_SCOPE,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                client_id=os.environ["SPOTIFY_CLIENT_ID"],
                client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
                show_dialog=True,
                cache_path=SPOTIFY_CACHE_PATH,
            )
        )
        self._user_id: str = self._sp.current_user()["id"]

    @property
    def user_id(self) -> str:
        return self._user_id

    def find_track(
        self,
        song_name: str,
        artist_name: str,
        year: str,
        threshold: int = FUZZY_THRESHOLD,
    ) -> Optional[str]:
        """
        Multi-stage fuzzy search for a Billboard song on Spotify.

        Strategy (from main2.py enhanced version):
        - Handles dual-title songs (e.g., "A/B") by trying each part.
        - Dynamic threshold: relaxed to MULTI_ARTIST_THRESHOLD for 3+ artist tracks.
        - Fallback query blends title score (70%) with year-match bonus (30%).
        - Returns the best Spotify track URI, or None if below threshold.
        """
        artist_name = re.sub(r"\(.*?\)", "", artist_name)
        artist_name = clean_artist_field(artist_name)

        billboard_artists = (
            [normalize_text(a) for a in re.split(r",\s*", artist_name)]
            if artist_name
            else []
        )

        # Dual-title handling: "Song A/Song B" → try each part separately
        title_variants = [song_name]
        if "/" in song_name:
            parts = [p.strip() for p in song_name.split("/") if len(p.strip()) > 3]
            title_variants.extend(parts)

        # Relax threshold for tracks crediting many artists
        dynamic_threshold = (
            MULTI_ARTIST_THRESHOLD if len(billboard_artists) > 2 else threshold
        )

        best_match = None
        highest_score = 0.0

        for title_variant in title_variants:
            clean_variant = normalize_text(title_variant)
            queries = self._build_queries(title_variant, artist_name, year)

            for query in queries:
                result = self._sp.search(q=query, type="track", limit=SEARCH_LIMIT)
                tracks = result.get("tracks", {}).get("items", [])

                for track in tracks:
                    score = self._score_track(
                        track, clean_variant, billboard_artists, year,
                        is_broad=(query == song_name),
                    )
                    if score > highest_score:
                        highest_score = score
                        best_match = track

                if best_match and highest_score >= dynamic_threshold:
                    break

            if best_match and highest_score >= dynamic_threshold:
                break

        if best_match and highest_score >= dynamic_threshold:
            matched_artists = [a["name"] for a in best_match["artists"]]
            print(
                f"[OK] {song_name} — {artist_name} "
                f"-> {best_match['name']} by {matched_artists} ({int(highest_score)}%)"
            )
            return best_match["uri"]

        print(f"[--] Skipped: {song_name} — {artist_name} ({int(highest_score)}%)")
        return None

    def collect_uris(
        self,
        billboard_rows: List[Tuple[str, str]],
        year: str,
        threshold: int = FUZZY_THRESHOLD,
    ) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Batch-search every (title, artist) row from Billboard.
        Returns (matched_uris, unmatched_rows).
        """
        uris: List[str] = []
        not_found: List[Tuple[str, str]] = []

        print(f"\nSearching Spotify for {len(billboard_rows)} songs...")

        for title, artist in billboard_rows:
            uri = self.find_track(title, artist, year, threshold)
            if uri:
                uris.append(uri)
            else:
                not_found.append((title, artist))
            time.sleep(SEARCH_DELAY)

        return uris, not_found

    def create_playlist(self, date_str: str, uris: List[str]) -> dict:
        """
        Create a private playlist named after date_str and add all URIs.
        Returns the full playlist object from the Spotify API.
        """
        playlist = self._sp.user_playlist_create(
            user=self._user_id,
            name=PLAYLIST_NAME.format(date=date_str),
            public=False,
            description=PLAYLIST_DESCRIPTION.format(date=date_str),
        )
        playlist_id = playlist["id"]

        for i in range(0, len(uris), PLAYLIST_BATCH_SIZE):
            self._sp.playlist_add_items(
                playlist_id=playlist_id, items=uris[i : i + PLAYLIST_BATCH_SIZE]
            )

        return playlist

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_queries(song_name: str, artist_name: str, year: str) -> List[str]:
        queries = []
        if artist_name:
            queries.append(f"track:{song_name} artist:{artist_name} year:{year}")
            queries.append(f"track:{song_name} artist:{artist_name}")
        queries.append(f"track:{song_name}")
        queries.append(song_name)  # ultra-broad fallback
        return queries

    @staticmethod
    def _score_track(
        track: dict,
        clean_variant: str,
        billboard_artists: List[str],
        year: str,
        is_broad: bool,
    ) -> float:
        spotify_title = normalize_text(track["name"])
        spotify_artists = [normalize_text(a["name"]) for a in track["artists"]]

        title_score = fuzz.partial_ratio(clean_variant, spotify_title)

        if billboard_artists and spotify_artists:
            lead_score = fuzz.partial_ratio(billboard_artists[0], spotify_artists[0])
            all_scores = [
                fuzz.partial_ratio(b, s)
                for b in billboard_artists
                for s in spotify_artists
            ]
            artist_score = max(all_scores + [lead_score])
        else:
            artist_score = title_score

        if is_broad:
            year_bonus = (
                YEAR_BONUS_HIT if year in track["album"]["release_date"] else YEAR_BONUS_MISS
            )
            return (title_score * TITLE_WEIGHT_BROAD) + (year_bonus * YEAR_WEIGHT_BROAD)

        return (title_score * TITLE_WEIGHT) + (artist_score * ARTIST_WEIGHT)
