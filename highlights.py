"""
Looks up a single game's highlight video on GAMETIME HIGHLIGHTS
(@TheGametimeHighlights) - an unofficial, third-party YouTube channel, NOT
run by the NBA. Chosen (over the NBA's own official channel) specifically
because it posts one video per individual game - the official channel only
ever posts a single combined "Nightly Recap" per night, with no per-game
video and no game_id to link against (see CLAUDE.md for the full
comparison). There's no API tying an NBA game_id to a YouTube video id
either way, official or not, so every lookup here is a fresh search of the
channel's own videos, matched by both teams' full names and the exact date
appearing together in a video's title.

No API key or registration (same spirit as nba_api/ESPN elsewhere in this
project) - just a plain HTTP GET of the channel's search page, parsing the
same `ytInitialData` JSON blob YouTube itself renders server-side into the
page (the same data a real browser's JS would read to draw the results
list - no headless browser needed to get it).

Confirmed empirically (see CLAUDE.md) that this channel tends to post
noticeably before the NBA's own official recap, but it's still HTML
scraping of an undocumented, unofficial page, not a stable API - it WILL
break if YouTube changes this page's structure, and it may simply not have
a given game's video up yet (or ever, if the channel skipped it). Both
cases return None rather than raising, matching every other unofficial
source in this project (get_injuries, get_player_power_ratings in
fetch.py) - a missing highlight link degrades the brief, it doesn't break
it. See scheduler.py's two-pass design for how a same-night miss here gets
one retry a couple hours later.
"""
import json
import re

import requests

_CHANNEL_HANDLE = "TheGametimeHighlights"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_REQUEST_TIMEOUT_SECONDS = 15
_INITIAL_DATA_RE = re.compile(r"var ytInitialData\s*=\s*(\{.*?\});</script>", re.S)

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _title_date(date_str: str) -> str:
    """"YYYY-MM-DD" -> "Month D, YYYY" - matches this channel's own title convention."""
    year, month, day = (int(part) for part in date_str.split("-"))
    return f"{_MONTHS[month - 1]} {day}, {year}"


def _video_renderers(node) -> list[dict]:
    """Walks YouTube's ytInitialData tree collecting every videoRenderer node."""
    found: list[dict] = []
    if isinstance(node, dict):
        if "videoRenderer" in node:
            found.append(node["videoRenderer"])
        for value in node.values():
            found.extend(_video_renderers(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_video_renderers(value))
    return found


def find_highlight_url(home_team: str, away_team: str, date_str: str) -> str | None:
    """
    home_team/away_team must be full "City Name" team names (e.g. "Los
    Angeles Clippers", matching data['games'][i]['line_score'][j]'s
    teamCity + teamName) - this channel's titles use full names, not
    tricodes, and the search itself is more precise with them. Returns
    None on any failure (network error, unparseable page, no matching
    video yet) - never raises, so a scraping break degrades to "no link"
    for the caller instead of failing the whole fetch.
    """
    query = f"{home_team} vs {away_team} {_title_date(date_str)}"
    try:
        response = requests.get(
            f"https://www.youtube.com/@{_CHANNEL_HANDLE}/search",
            params={"query": query},
            headers=_HEADERS,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        match = _INITIAL_DATA_RE.search(response.text)
        if not match:
            return None
        data = json.loads(match.group(1))
    except (requests.RequestException, ValueError):
        return None

    target_date = _title_date(date_str)
    for renderer in _video_renderers(data):
        title_runs = renderer.get("title", {}).get("runs", [])
        title = "".join(run.get("text", "") for run in title_runs)
        if target_date not in title:
            continue
        if home_team not in title or away_team not in title:
            continue
        video_id = renderer.get("videoId")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    return None
