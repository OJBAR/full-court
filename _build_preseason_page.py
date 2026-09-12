"""
Builds the real output/index.html BEFORE the 2026-27 season has any actual
game night to summarize. Without this, the real "latest brief" pointer
stays stuck on whatever a demo build last happened to leave there (see
CLAUDE.md's own note on why that's a real operational risk) - the 5
curated demos moved to output/demos/ specifically so they never touch
index.html again, but that alone left index.html as stale leftover
content, not a real page.

NOT a fake brief: no summary text is invented, no Claude call - just the
real, live 2026-27 schedule (fetched from ScheduleLeagueV2, confirmed
already published as of 2026-09-12) so the schedule tab genuinely works
and shows real upcoming games, real (all 0-0) standings, and a plain
explanatory paragraph in place of a night's summary. scheduler.py's own
first real nightly run will overwrite this file exactly the same way it
overwrites any other night's brief, the morning after the season's first
game night actually happens - this script has no ongoing role after that.
"""
from datetime import datetime

from config import ISRAEL
from fetch import get_season_schedule, get_standings
from render import render, OUTPUT_DIR

SEASON_START = "2026-10-20"  # first real game night of the 2026-27 season, per the real schedule


def build():
    season_schedule = get_season_schedule(SEASON_START)
    standings_records = get_standings("2026-27").to_dict(orient="records")

    # LeagueStandingsV3 has no tricode column of its own - same join-on-
    # full-name pattern already used 3 other places in fetch.py (see
    # fetch_for_date's own comment on this exact join).
    tricode_by_fullname = {}
    for g in season_schedule:
        tricode_by_fullname[g["home_team"]] = g["home_tricode"]
        tricode_by_fullname[g["away_team"]] = g["away_tricode"]
    for row in standings_records:
        tricode = tricode_by_fullname.get(f"{row['TeamCity']} {row['TeamName']}")
        if tricode:
            row["Tricode"] = tricode

    today = datetime.now(ISRAEL).strftime("%Y-%m-%d")
    data = {
        "date": today,
        "games": [],
        "standings": standings_records,
        "season_schedule": season_schedule,
        "is_playoffs": False,
        "is_cup_knockout": False,
        "is_cup_groups": False,
        "is_play_in": False,
        # This page is ONLY ever saved to output/index.html, never also to
        # its own output/{date}.html the way a real brief's save() does -
        # og:url has to point at the actual root URL instead of claiming a
        # dated page that doesn't exist (see render()'s own comment on
        # this key).
        "og_url_path": "",
    }
    summary = (
        "עונת 2026-27 עוד לא התחילה - המשחק הראשון נפתח ב-20.10.2026. ברגע שהעונה "
        "תתחיל, הבריף הראשון יתפרסם כאן בבוקר שאחרי ליל המשחקים הראשון של העונה. "
        "אפשר כבר עכשיו לעיין בלוח המשחקים המלא של העונה למטה, בטאב \"לוח התוצאות\"."
    )

    html = render(data, summary)
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"Saved output/index.html - pre-season placeholder ({len(season_schedule)} games in the real schedule).")


if __name__ == "__main__":
    build()
