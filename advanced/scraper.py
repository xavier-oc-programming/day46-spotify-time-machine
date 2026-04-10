from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

from config import BILLBOARD_BASE_URL, USER_AGENT, REQUEST_TIMEOUT, clean_artist_field


class BillboardScraper:
    """Scrapes the Billboard Hot 100 chart for a given date."""

    def scrape(self, date_str: str) -> List[Tuple[str, str]]:
        """
        Fetch and parse Billboard Hot 100 for date_str (YYYY-MM-DD).
        Returns a deduplicated list of (song_title, artist_name) tuples.
        Raises requests.HTTPError on non-2xx responses.
        """
        url = BILLBOARD_BASE_URL.format(date=date_str)
        headers = {"User-Agent": USER_AGENT}

        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        data = []
        for h3 in soup.select("li ul li h3"):
            title = h3.get_text(strip=True)
            if not title:
                continue

            artist = ""
            li = h3.find_parent("li")
            if li:
                span = li.select_one("span.c-label.a-no-trucate")
                if span:
                    artist = clean_artist_field(span.get_text(strip=True))

            data.append((title, artist))

        return self._deduplicate(data)

    @staticmethod
    def _deduplicate(rows: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        seen: set = set()
        unique = []
        for row in rows:
            if row not in seen:
                seen.add(row)
                unique.append(row)
        return unique
