"""
Builds the "comprehensive demo" (דמו כולל): real fetched data (standings,
brackets, results, real nba.com game-page AND YouTube highlight links) for
EVERY real game night of the 2025-26 season, so picking any date answers
"if I'd opened the app on this date last season, this is what it would have
looked like." No Claude summary call (the expensive/slow-and-irrelevant-here
part) - a fixed filler paragraph stands in for it instead. Highlights ARE
included (include_highlights defaults to True - not passed here at all),
by explicit request, even though that's the slowest/least reliable step
(a YouTube search per game, not nba_api) - expect this run to take a long
while for the full season.

Written to output/comprehensive/ (a dedicated subdirectory, NOT
output/{date}.html) specifically because some of these real dates collide
with existing demo fixtures' own dates (e.g. 2025-11-28 is also
demo_cup_groups_new's date) - writing there would silently overwrite them.

The season schedule (ScheduleLeagueV2) is fetched ONCE up front and passed
into every date's fetch_for_date() call instead of letting it redundantly
re-fetch the same full-season payload ~212 times.

Not part of the regular demo-regeneration pipeline (kept separate from
demo.py etc.) since it does real, slow, live nba_api/ESPN calls instead of
loading a frozen fixture - re-run manually only when needed. Safe to
interrupt and re-run: already-built dates are skipped.
"""
import sys
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
from nba_api.stats.endpoints import scheduleleaguev2

from fetch import fetch_for_date, get_season_schedule, _dataframe_for
from render import render, OUTPUT_DIR

COMPREHENSIVE_DIR = OUTPUT_DIR / "comprehensive"
SEASON = "2025-26"

FILLER_SUMMARY = (
    "כאן יופיע הסיכום שכתב Claude על לילה זה - כמה פסקאות בעברית על מה שקרה, "
    "כולל הרגעים הבולטים וההקשר הרחב יותר. הדף הזה מדגים את שאר הברייף (טבלה, "
    "בראקטים, תוצאות, קישורים - כולל תקצירי וידאו אמיתיים) עם נתונים אמיתיים "
    "מהעונה שעברה, בלי להריץ בפועל את הקריאה היקרה יותר ל-Claude לכל תאריך."
)


def real_game_dates() -> list[str]:
    """
    Every US Eastern date the 2025-26 season actually had a completed game
    on - regular season, Cup (any stage), Play-In, Playoffs (gameId prefixes
    002/004/005/006 - excludes preseason 001 and All-Star 003, same
    convention as fetch.get_season_schedule).
    """
    result = scheduleleaguev2.ScheduleLeagueV2(season=SEASON)
    df = _dataframe_for(result, "SeasonGames")
    df = df[df["gameId"].str.startswith(("002", "004", "005", "006"))]
    df = df[df["gameStatus"] == 3]
    df = df.copy()
    df["date_str"] = pd.to_datetime(df["gameDate"]).dt.strftime("%Y-%m-%d")
    return sorted(df["date_str"].unique())


def build():
    COMPREHENSIVE_DIR.mkdir(parents=True, exist_ok=True)
    dates = real_game_dates()
    print(f"{len(dates)} real game nights found for {SEASON}.")

    # Fetched once, reused for every date below (see module docstring).
    base_schedule = get_season_schedule(dates[-1])
    print(f"Base season schedule fetched once: {len(base_schedule)} games.")

    built = []
    for i, date_str in enumerate(dates):
        out_path = COMPREHENSIVE_DIR / f"{date_str}.html"
        if out_path.exists():
            built.append(date_str)
            continue
        print(f"[{i + 1}/{len(dates)}] Fetching real data for {date_str}...")
        try:
            data = fetch_for_date(date_str, season_schedule=base_schedule)  # include_highlights defaults True
            # See _fix_comprehensive_demo.py's fix_file() comment - the
            # "לוח התוצאות" tab needs to open on this page's own date, not
            # whatever the real viewer's live "today" happens to be.
            data["demo_today"] = date_str
        except Exception as e:
            print(f"  FAILED: {e} - skipping this date.")
            continue
        html = render(data, FILLER_SUMMARY)
        out_path.write_text(html, encoding="utf-8")
        built.append(date_str)
        time.sleep(0.5)

    return built


def build_index(built):
    """
    DEPRECATED - kept only so an old checkout can still call this without
    crashing. The comprehensive demo's home screen (output/comprehensive/
    index.html) is no longer a separate bespoke picker page: by request, it's
    now just a copy of the latest real date's own full page (see
    _fix_comprehensive_demo.py's main(), which does the actual copying,
    after that page has its own in-page nav bar injected) - landing on the
    demo IS the real product, with date-switching (prev/next/±10) built
    into the page itself instead of a different screen you navigate away
    from.
    """
    return


if __name__ == "__main__":
    built = build()
    if built:
        build_index(built)
    else:
        print("Nothing built - all dates failed.")
        sys.exit(1)
