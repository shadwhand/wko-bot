#!/usr/bin/env python3
"""Fetch Empirical Cycling community notes from lucasvance.github.io.

Downloads structured episode summaries as HTML, converts to plain text.
These complement the Whisper transcripts with curated key takeaways.

Usage:
    python fetch_ec_notes.py              # Fetch all notes
    python fetch_ec_notes.py --limit 40   # Fetch most recent 40
    python fetch_ec_notes.py --status     # Show what's been fetched
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
NOTES_DIR = PROJECT_ROOT / "docs" / "research" / "raw" / "empirical-cycling-notes"
BASE_URL = "https://lucasvance.github.io/empirical-cycling-community-notes"


def get_episode_index():
    """Fetch the main index page and extract all episode URLs + titles.

    Returns list of dicts sorted by date (newest first):
        [{url, title, series, episode_num, date_str, slug}, ...]
    """
    resp = requests.get(BASE_URL + "/", timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    episodes = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Match episode URLs like /empirical-cycling-community-notes/watts-doc/2025/07/24/wd-55.html
        m = re.search(
            r'/empirical-cycling-community-notes/([\w-]+)/(\d{4})/(\d{2})/(\d{2})/([\w-]+)\.html',
            href,
        )
        if not m:
            continue

        series = m.group(1)
        year, month, day = m.group(2), m.group(3), m.group(4)
        filename = m.group(5)
        title = a.get_text(strip=True)

        # Extract episode number
        ep_num = re.search(r'\d+', filename)
        ep_num = int(ep_num.group()) if ep_num else 0

        episodes.append({
            "url": f"{BASE_URL}/{series}/{year}/{month}/{day}/{filename}.html",
            "title": title,
            "series": series,
            "episode_num": ep_num,
            "date_str": f"{year}-{month}-{day}",
            "slug": f"{series}-{filename}",
        })

    # Deduplicate by URL
    seen = set()
    unique = []
    for ep in episodes:
        if ep["url"] not in seen:
            seen.add(ep["url"])
            unique.append(ep)

    # Sort by date descending
    unique.sort(key=lambda x: x["date_str"], reverse=True)
    logger.info(f"Found {len(unique)} episodes in index")
    return unique


def fetch_episode_notes(ep):
    """Fetch and extract the text content of a single episode's community notes.

    Returns the notes as plain text with the title prepended, or None on failure.
    """
    try:
        resp = requests.get(ep["url"], timeout=30)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav, header, footer
        for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        # Try to find main content
        content_div = soup.find("main") or soup.find("article") or soup.find("body")
        if not content_div:
            return None

        text = content_div.get_text(separator="\n", strip=True)

        # Prepend metadata
        header = f"# {ep['title']}\n"
        header += f"Series: {ep['series']} | Date: {ep['date_str']}\n"
        header += f"Source: {ep['url']}\n\n"

        return header + text

    except Exception as e:
        logger.warning(f"Failed to fetch {ep['url']}: {e}")
        return None


def fetch_all_notes(limit=None):
    """Fetch community notes for all (or limited) episodes."""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    state_file = NOTES_DIR / "_state.json"

    state = {}
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)

    episodes = get_episode_index()
    if limit:
        episodes = episodes[:limit]

    unprocessed = [ep for ep in episodes if ep["url"] not in state]
    logger.info(f"{len(unprocessed)} new episodes to fetch")

    fetched = 0
    for i, ep in enumerate(unprocessed):
        logger.info(f"[{i+1}/{len(unprocessed)}] {ep['title']}")

        notes = fetch_episode_notes(ep)
        if not notes or len(notes) < 200:
            state[ep["url"]] = {"status": "empty", "slug": ep["slug"], "title": ep["title"]}
            continue

        out_path = NOTES_DIR / f"{ep['slug']}.txt"
        with open(out_path, "w") as f:
            f.write(notes)

        state[ep["url"]] = {
            "status": "fetched",
            "slug": ep["slug"],
            "title": ep["title"],
            "series": ep["series"],
            "date": ep["date_str"],
            "length": len(notes),
            "file": out_path.name,
        }
        fetched += 1

        time.sleep(0.3)  # be polite

        if (i + 1) % 20 == 0:
            _save_state(state_file, state)

    _save_state(state_file, state)
    total = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "fetched")
    logger.info(f"Done: {fetched} new notes fetched ({total} total)")


def show_status():
    """Show what's been fetched."""
    state_file = NOTES_DIR / "_state.json"
    if not state_file.exists():
        print("No notes fetched yet.")
        return

    with open(state_file) as f:
        state = json.load(f)

    fetched = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "fetched")
    empty = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "empty")

    print(f"Community Notes Status:")
    print(f"  Fetched: {fetched}")
    print(f"  Empty/failed: {empty}")

    # Break down by series
    by_series = {}
    for v in state.values():
        if isinstance(v, dict) and v.get("status") == "fetched":
            s = v.get("series", "unknown")
            by_series[s] = by_series.get(s, 0) + 1

    for series, count in sorted(by_series.items()):
        print(f"    {series}: {count}")


def _save_state(state_file, state):
    tmp = state_file.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.rename(state_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Empirical Cycling community notes")
    parser.add_argument("--limit", type=int, help="Limit to N most recent episodes")
    parser.add_argument("--status", action="store_true", help="Show fetch status")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        fetch_all_notes(limit=args.limit)
