"""
Builds the 5 curated public demos (the "beta" surface linked from every
page's footer / demos.html) - replaces the old 11-demo lineup (a mix of
real and entirely fabricated playoff/cup/Play-In scenarios) with exactly 5,
all real data from the actual 2025-26 season, one per day-type, all with a
REAL Claude-written summary (not the comprehensive demo's filler text - by
request, since this surface is meant to look exactly like the real product
would, unlike the dev-only comprehensive demo which skips the summary call
on purpose across all 212 of its pages).

Picked with the user (2026-08-29), each for a specific reason - see that
conversation for the full reasoning:
- 2025-10-22: regular season (the season's 2nd game night, not the opener).
- 2025-11-28: NBA Cup group stage (11 games, near the end of group play so
  the group tables are close to settled).
- 2025-12-13: NBA Cup knockout - Conference Semifinals (bracket also shows
  both quarterfinals as history in the same page).
- 2026-05-17: Playoffs - Conf. Semifinals (Cleveland close out Detroit 4-3
  in a Game 7, on the heels of ALSO winning their Round 1 series in a Game
  7 - a real underdog story, both series visible as history).
- 2026-04-17: Play-In - the decider game (both earlier Play-In games for
  that conference show as history in the same page).

Only 5 slots for 6 conceptual day-types (CLAUDE.md's own category list adds
a distinct "גמר NBA" bucket) - deliberately no separate Finals pick: a late
Finals date would show the Finals AND both conference brackets as history
in one page, but the user asked for a Round 2 game there instead once this
was pointed out, so Finals coverage is dropped from this batch entirely
rather than picking a 6th date. The comprehensive demo (dev-only) already
covers every single game night for anyone who wants to see the Finals or
still-fabricated-style scenarios like Round 2/Conf Finals in more depth.

Each date's raw data is already sitting in _comprehensive_cache/{date}.json
from the comprehensive demo build - reused as-is here (no re-fetching), on
top of which this script adds the ONE real thing the comprehensive demo
deliberately skips: an actual storylines.find_storylines() +
summarize.summarize() call (real, billed Claude API request) per date.
Standings-as-of-date, demo_today (Israel-day-correct), and full-history
schedule enrichment reuse the exact same functions
_generate_comprehensive_demo.py already has for this - identical mechanism,
just wired to 5 dates with a real summary instead of 212 with a filler one.

Writes straight to output/{date}.html via render.save() - the same call the
old demo*.py scripts always used. Note this ALSO overwrites output/
index.html (save()'s own documented behavior, the real "latest brief"
pointer) - pre-existing, unchanged behavior of every demo script that came
before this one, not something new introduced here; harmless while
scheduler.py's real nightly runs stay disabled (see CLAUDE.md's backlog).
"""
import json
from pathlib import Path

from fetch import get_season_schedule, get_standings, compute_standings_as_of
from storylines import find_storylines
from summarize import summarize
from render import save
from _generate_comprehensive_demo import _il_today, enrich_full_history, load_highlight_cache

REPO_DIR = Path(__file__).parent
DATA_CACHE_DIR = REPO_DIR / "_comprehensive_cache"
SEASON = "2025-26"

CURATED_DATES = [
    "2025-10-22",
    "2025-11-28",
    "2025-12-13",
    "2026-04-17",
    "2026-05-17",
]


def build():
    print(f"Building {len(CURATED_DATES)} curated demos with real Claude summaries...")
    base_schedule = get_season_schedule(CURATED_DATES[-1])
    standings_meta = get_standings(SEASON)
    highlight_cache = load_highlight_cache()

    for i, date_str in enumerate(CURATED_DATES):
        cache_path = DATA_CACHE_DIR / f"{date_str}.json"
        if not cache_path.exists():
            print(f"  MISSING CACHE for {date_str} - run _generate_comprehensive_demo.py first. Skipping.")
            continue

        print(f"[{i + 1}/{len(CURATED_DATES)}] {date_str}: loading cached data...")
        data = json.loads(cache_path.read_text(encoding="utf-8"))

        data["demo_today"] = _il_today(data["season_schedule"], date_str)
        data["standings"] = compute_standings_as_of(date_str, base_schedule, standings_meta)
        enrich_full_history(data["season_schedule"], date_str, highlight_cache, data["standings"])

        print(f"  finding storylines...")
        detected_storylines = find_storylines(data)
        print(f"  calling Claude for a real summary...")
        summary = summarize(data, detected_storylines)

        output_path = save(data, summary)
        print(f"  saved: {output_path}")

    print("Done.")


if __name__ == "__main__":
    build()
