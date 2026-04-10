import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from config import OUTPUT_DIR, OUTPUT_FILENAME
from scraper import BillboardScraper
from client import SpotifyClient


def main() -> None:
    date = input(
        "Which year do you want to travel to? "
        "Type the date in this format YYYY-MM-DD: "
    ).strip()
    year = date.split("-")[0]

    # Step 1: Scrape Billboard Hot 100
    scraper = BillboardScraper()
    billboard_rows = scraper.scrape(date)
    print(f"\nScraped {len(billboard_rows)} songs from Billboard Hot 100 ({date}).")
    for title, artist in billboard_rows[:5]:
        print(f"  - {title} — {artist or '(artist unknown)'}")

    # Step 2: Authenticate with Spotify
    client = SpotifyClient()
    print(f"\nLogged in as Spotify user: {client.user_id}")

    # Step 3: Fuzzy-match songs on Spotify
    uris, not_found = client.collect_uris(billboard_rows, year)
    print(f"\nMatched {len(uris)} tracks; unmatched: {len(not_found)}")

    # Save unmatched songs to output/
    if not_found:
        print(f"\n{len(not_found)} songs were not found on Spotify:")
        for title, artist in not_found:
            print(f"  - {title} — {artist or '(artist unknown)'}")

        OUTPUT_DIR.mkdir(exist_ok=True)
        output_path = OUTPUT_DIR / OUTPUT_FILENAME.format(year=year)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Unmatched songs from Billboard Hot 100 ({date})\n")
            f.write("=" * 60 + "\n\n")
            for title, artist in not_found:
                f.write(f"- {title} — {artist or '(artist unknown)'}\n")
        print(f"\nSaved unmatched songs to '{output_path}'.")
    else:
        print("\nAll Billboard songs were successfully matched on Spotify!")

    # Step 4: Create Spotify playlist
    if uris:
        playlist = client.create_playlist(date, uris)
        print(f"\nPlaylist created: {playlist['name']}")
        print(f"Open in Spotify: {playlist['external_urls']['spotify']}")
    else:
        print("\nNo songs matched — playlist not created.")


if __name__ == "__main__":
    main()
