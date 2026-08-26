"""
Dynamic morning-run gate. Meant to be triggered every ~20 minutes (e.g. via
Windows Task Scheduler) through the evening/night window - each run is a
short, stateless check: "is last night's brief ready to send yet?" If not,
it exits quietly and the next scheduled trigger tries again.

Design (see CLAUDE.md backlog item 7 for the full discussion):
- First check at (last game's scheduled start) + 2:30.
- No fixed "second check" special case after that - Task Scheduler's own
  20-minute re-trigger cadence IS the polling interval, so this script never
  sleeps or loops internally.
- No guessing at game duration: every check reads the live gameStatusText
  for each game. Postponed/cancelled games are excluded immediately rather
  than waited on.
- Never delivers before 05:30 Israel time, even if everything is Final earlier.
- A generous 6-hour safety ceiling (past the first-check time) forces a send
  even if some game's status never resolves, flagging it instead of hanging
  forever - this only protects against a genuinely stuck/unrecognized status;
  a real postponement is detected immediately, not via this ceiling.
- If there were no games at all on the target date (offseason, All-Star break,
  a rare true off day), it does NOT run - no brief is generated for a night
  with nothing to report on.
"""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from config import last_night_game_date
from fetch import get_games_for_date, fetch_for_date
from storylines import find_storylines
from summarize import summarize
from render import save, OUTPUT_DIR

REPO_DIR = Path(__file__).parent

ISRAEL = ZoneInfo("Asia/Jerusalem")

FIRST_CHECK_MINUTES = 150       # 2:30 after the last game's scheduled start
FLOOR_HOUR_IL = 5
FLOOR_MINUTE_IL = 30
SAFETY_CEILING_MINUTES = 360    # 6h past the first check - force-send past this

_POSTPONED_KEYWORDS = ("ppd", "postponed", "cancel", "suspended")


def _game_status(status_text: str) -> str:
    """Classifies one game's status text as 'final', 'postponed', or 'pending'."""
    text = str(status_text).lower()
    if "final" in text:
        return "final"
    if any(keyword in text for keyword in _POSTPONED_KEYWORDS):
        return "postponed"
    return "pending"


def _publish_to_github(saved_path: Path) -> None:
    """
    Commits and pushes the freshly generated output/ (the new dated brief,
    plus the refreshed index.html) to GitHub, so the "Deploy Brief to Pages"
    workflow picks it up and republishes the live site. GitHub Actions can't
    run the fetch pipeline itself (stats.nba.com blocks cloud IPs) - this is
    the other half of that split: generate at home, publish from home too.
    A failed push is only logged, not raised - the brief was already saved
    locally successfully by this point, which matters more than the publish
    step succeeding on any single run (the next run will just push it too).
    """
    try:
        subprocess.run(["git", "add", "output"], cwd=REPO_DIR, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Daily brief: {saved_path.stem}"],
            cwd=REPO_DIR,
            check=True,
        )
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        print("Published to GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: could not publish to GitHub ({e}) - brief was still saved locally.")


def check(now: datetime | None = None) -> bool:
    """
    Runs the full pipeline for last night's games if it's ready, and returns
    True if it did. Returns False (no side effects) if it's not time yet.
    """
    now = now or datetime.now(timezone.utc)
    target_date = last_night_game_date(now)

    output_path = OUTPUT_DIR / f"{target_date}.html"
    if output_path.exists():
        print(f"{target_date} already has a brief ({output_path}) - nothing to do.")
        return False

    game_header, _ = get_games_for_date(target_date)
    if game_header.empty:
        print(f"No games on {target_date} - nothing to brief. Not running.")
        return False

    last_start_utc = (
        game_header["gameTimeUTC"]
        .apply(lambda t: datetime.fromisoformat(str(t).replace("Z", "+00:00")))
        .max()
    )
    first_check = last_start_utc + timedelta(minutes=FIRST_CHECK_MINUTES)
    if now < first_check:
        print(f"Too early - first check is at {first_check.isoformat()} (now {now.isoformat()}).")
        return False

    statuses = [_game_status(s) for s in game_header["gameStatusText"]]
    pending = [s for s in statuses if s == "pending"]
    minutes_past_first_check = (now - first_check).total_seconds() / 60

    if pending and minutes_past_first_check < SAFETY_CEILING_MINUTES:
        print(f"{len(pending)} game(s) still not Final/Postponed - trying again next cycle.")
        return False

    if pending:
        print(
            f"Safety ceiling reached ({SAFETY_CEILING_MINUTES} min past first check) "
            f"with {len(pending)} game(s) still unresolved - sending anyway."
        )

    now_il = now.astimezone(ISRAEL)
    floor_il = now_il.replace(hour=FLOOR_HOUR_IL, minute=FLOOR_MINUTE_IL, second=0, microsecond=0)
    if now_il < floor_il:
        print(f"Before the {FLOOR_HOUR_IL:02d}:{FLOOR_MINUTE_IL:02d} Israel-time floor - waiting.")
        return False

    print(f"Ready. Running the pipeline for {target_date}...")
    data = fetch_for_date(target_date)
    storylines = find_storylines(data)
    summary = summarize(data, storylines)
    saved_path = save(data, summary)
    print(f"Saved to: {saved_path}")
    _publish_to_github(saved_path)
    return True


if __name__ == "__main__":
    ran = check()
    sys.exit(0 if ran or "--strict" not in sys.argv else 1)
