"""
Builds the "comprehensive demo" (דמו כולל): real fetched data for EVERY real
game night of the 2025-26 season, so picking any date answers "if I'd opened
the app on this date last season, this is what it would have looked like."
No Claude summary call (the expensive/slow-and-irrelevant-here part) - a
fixed filler paragraph stands in for it instead.

Three things beyond a plain fetch_for_date() per date, all "as of this page's
own date", not "as of whenever this script happened to run":

1. Standings: LeagueStandingsV3 (fetch.get_standings) has NO as-of-date
   support - it's always the CURRENT table. fetch.compute_standings_as_of()
   recomputes real win/loss/streak/rank from season_schedule's own final
   scores instead.
2. Cup/Playoff brackets: already correctly as_of_date-filtered by design
   (fetch.get_cup_bracket/get_playoff_series) - fetch_for_date() already
   gets these right, nothing extra needed here.
3. Highlights on every past day in the schedule tab, not just the page's
   own night: a global, once-ever highlight lookup for every real game this
   season (_HIGHLIGHT_CACHE_PATH, keyed by game_id - a game only needs
   looking up once, shared across every later page that shows it), applied
   to every real season_schedule entry up to each page's own date
   (enrich_full_history()). No OT tag on these (would need a box-score call
   per historical game - not worth it just for that; render.py already
   treats a missing period as "no OT tag"), and no team-record badge either
   (would need each team's win/loss *at that specific game's own moment*,
   not just as of the page's date - a real reconstruction is possible but
   not implemented here; showing the page-date's end-state record next to
   an old game would look wrong, not just incomplete).

Written to output/comprehensive/ (a dedicated subdirectory, NOT
output/{date}.html) specifically because some of these real dates collide
with existing demo fixtures' own dates (e.g. 2025-11-28 is also
demo_cup_groups_new's date) - writing there would silently overwrite them.

Not part of the regular demo-regeneration pipeline (kept separate from
demo.py etc.) since it does real, slow, live nba_api/ESPN calls instead of
loading a frozen fixture - re-run manually only when needed.

Each date's raw fetched data (box scores/etc. - the expensive per-date
fetch_for_date() call) is cached to _comprehensive_cache/{date}.json
(gitignored - local only, not published) the first time it's fetched, and
the shared highlight lookup cached separately in
_comprehensive_cache/_highlights.json. Every run of this script re-renders
EVERY date (fetching per-date data only for whatever isn't cached yet, and
looking up only whatever games aren't in the highlight cache yet) and always
recomputes standings/full-history-enrichment fresh (both are pure local
computation, no API calls) - so a render.py template change, or a change to
either of those two computations, reaches every page with a cheap re-render
pass instead of a fresh multi-hour fetch. The first version of this script
learned the caching lesson the hard way: it skipped already-built HTML
entirely, so a later render.py change (the calendar view) silently never
showed up here.
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
from nba_api.stats.endpoints import scheduleleaguev2

from fetch import (
    fetch_for_date,
    get_season_schedule,
    get_standings,
    compute_standings_as_of,
    _dataframe_for,
)
from highlights import find_highlight_url
from config import US_EASTERN
from render import render, OUTPUT_DIR

COMPREHENSIVE_DIR = OUTPUT_DIR / "comprehensive"
DATA_CACHE_DIR = Path(__file__).parent / "_comprehensive_cache"
HIGHLIGHT_CACHE_PATH = DATA_CACHE_DIR / "_highlights.json"
SEASON = "2025-26"


def _json_default(o):
    # DataFrame .to_dict(orient="records") output can carry numpy scalar
    # types (int64/float64/bool_) - not natively JSON-serializable, and a
    # blanket str() fallback would silently turn e.g. a real int into the
    # *string* "27" once read back, which could quietly break comparisons
    # downstream. numpy scalars all expose .item() to convert back to a
    # native Python type properly; str() is still the last-resort fallback
    # for anything else genuinely exotic.
    if hasattr(o, "item"):
        return o.item()
    return str(o)

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


_ET_DATE_CACHE: dict[str, str] = {}


def _et_date(tipoff_utc: str) -> str:
    if tipoff_utc not in _ET_DATE_CACHE:
        dt = datetime.fromisoformat(tipoff_utc.replace("Z", "+00:00"))
        _ET_DATE_CACHE[tipoff_utc] = dt.astimezone(US_EASTERN).strftime("%Y-%m-%d")
    return _ET_DATE_CACHE[tipoff_utc]


def load_highlight_cache() -> dict:
    if HIGHLIGHT_CACHE_PATH.exists():
        return json.loads(HIGHLIGHT_CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def build_highlight_cache(base_schedule: list[dict]) -> dict:
    """
    One highlight lookup per real completed game, ever - shared across every
    page that later shows that game, instead of a lookup per (page, game)
    pair. Saved incrementally (every 10 lookups) so an interrupted run
    doesn't lose progress already made.
    """
    cache = load_highlight_cache()
    finals = [g for g in base_schedule if g["is_final"]]
    missing = [g for g in finals if g["game_id"] not in cache]
    if not missing:
        return cache
    print(f"Highlight cache: {len(finals) - len(missing)}/{len(finals)} already cached, looking up {len(missing)} more...")
    for i, g in enumerate(missing):
        try:
            url = find_highlight_url(g["home_team"], g["away_team"], _et_date(g["tipoff_utc"]))
        except Exception as e:
            print(f"  highlight lookup failed for {g['game_id']}: {e}")
            url = None
        cache[g["game_id"]] = url
        if (i + 1) % 10 == 0 or i + 1 == len(missing):
            HIGHLIGHT_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print(f"  [{i + 1}/{len(missing)}] highlights looked up")
        time.sleep(0.5)
    return cache


def enrich_full_history(season_schedule: list[dict], date_str: str, highlight_cache: dict) -> None:
    """
    Attaches "rich" to every FINAL game up to and including date_str that
    doesn't already have it - the page's own night already got the full
    treatment (OT tag, real per-game win/loss) from fetch_for_date()'s own
    _enrich_schedule_with_rich_data. See the module docstring for why these
    get no OT tag and no team-record badge.
    """
    for entry in season_schedule:
        if "rich" in entry or not entry.get("is_final"):
            continue
        if _et_date(entry["tipoff_utc"]) > date_str:
            continue
        entry["rich"] = {
            "period": None,
            "highlight_url": highlight_cache.get(entry["game_id"]),
            "po_round": entry.get("po_round"),
            "series_text": entry.get("series_text"),
            "series_game_number": entry.get("series_game_number"),
            "cup_subtype": entry.get("cup_subtype"),
            "cup_sub_label": entry.get("cup_sub_label"),
            "is_play_in": entry.get("is_play_in"),
            "away_wins": None,
            "away_losses": None,
            "home_wins": None,
            "home_losses": None,
        }


def build():
    COMPREHENSIVE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dates = real_game_dates()
    print(f"{len(dates)} real game nights found for {SEASON}.")

    # All fetched/computed once, reused for every date below (see module
    # docstring) - none of this needs redoing per date.
    base_schedule = get_season_schedule(dates[-1])
    print(f"Base season schedule fetched once: {len(base_schedule)} games.")
    standings_meta = get_standings(SEASON)
    highlight_cache = build_highlight_cache(base_schedule)

    built = []
    for i, date_str in enumerate(dates):
        cache_path = DATA_CACHE_DIR / f"{date_str}.json"
        if cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            print(f"[{i + 1}/{len(dates)}] Fetching real data for {date_str}...")
            try:
                data = fetch_for_date(date_str, season_schedule=base_schedule)  # include_highlights defaults True
                # See _fix_comprehensive_demo.py's fix_file() comment - the
                # "לוח התוצאות" tab needs to open on this page's own date,
                # not whatever the real viewer's live "today" happens to be.
                data["demo_today"] = date_str
            except Exception as e:
                print(f"  FAILED: {e} - skipping this date.")
                continue
            cache_path.write_text(json.dumps(data, ensure_ascii=False, default=_json_default), encoding="utf-8")
            time.sleep(0.5)

        # Both pure local computation (no API calls) - always redone fresh
        # from the freshest base_schedule/highlight_cache/standings_meta,
        # even for an already-cached date, so a fix to either computation
        # reaches every page on the next run without re-fetching anything.
        data["standings"] = compute_standings_as_of(date_str, base_schedule, standings_meta)
        enrich_full_history(data["season_schedule"], date_str, highlight_cache)

        html = render(data, FILLER_SUMMARY)
        (COMPREHENSIVE_DIR / f"{date_str}.html").write_text(html, encoding="utf-8")
        built.append(date_str)

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
