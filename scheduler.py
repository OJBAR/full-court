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

Two-pass highlight links: GAMETIME HIGHLIGHTS (see highlights.py) doesn't
always have every game's video up yet by the time the brief ships (the
later games of the night especially) - so once the brief is sent, if any
game is still missing a link, its fetched data + written summary are
stashed in pending/{date}.json (untracked, never published - see
.gitignore) and this same check() re-checks it on later runs. Once at
least SECOND_PASS_MINUTES has passed since the first pass, it retries the
lookup for whatever's still missing, re-renders/re-saves/re-pushes the
same file if anything new turned up, and deletes the pending file either
way - one retry only, never an unbounded loop. This second pass never
re-fetches game data or re-calls Claude - only highlight_url values change.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from config import last_night_game_date
from fetch import get_games_for_date, fetch_for_date, highlight_url_for_game
from storylines import find_storylines
from summarize import summarize
from render import save, OUTPUT_DIR

REPO_DIR = Path(__file__).parent
# Deliberately outside output/ - _publish_to_github only `git add output`, so
# this never gets committed/pushed (it's internal bookkeeping between this
# script's own runs, not part of the site). See .gitignore.
PENDING_DIR = REPO_DIR / "pending"

ISRAEL = ZoneInfo("Asia/Jerusalem")

FIRST_CHECK_MINUTES = 150       # 2:30 after the last game's scheduled start
FLOOR_HOUR_IL = 5
FLOOR_MINUTE_IL = 30
SAFETY_CEILING_MINUTES = 360    # 6h past the first check - force-send past this
SECOND_PASS_MINUTES = 120       # how long after the brief ships to retry missing highlight links, once

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


def _pending_path(date_str: str) -> Path:
    return PENDING_DIR / f"{date_str}.json"


def _try_second_pass(target_date: str, pending_path: Path, now: datetime) -> bool:
    """
    One retry, some time after the brief already shipped, for whichever
    games didn't have a highlight link yet on the first pass (see
    highlights.py - often the later games of the night, since GAMETIME
    HIGHLIGHTS/the game itself may simply not be posted yet at first-pass
    time). Reuses the exact same fetched data and Claude-written summary
    from the first pass (persisted to `pending_path`) rather than re-fetching
    or re-summarizing - this pass only ever adds highlight_url values and
    re-renders/re-saves/re-pushes the same file, it never touches the text.
    Whatever's still missing after this one retry stays missing for good -
    no unbounded retry loop, and the pending file is removed either way so
    this only ever runs once per date.
    """
    state = json.loads(pending_path.read_text(encoding="utf-8"))
    run1_at = datetime.fromisoformat(state["run1_at"])
    if now < run1_at + timedelta(minutes=SECOND_PASS_MINUTES):
        print(f"Second pass for {target_date} not due yet (ran first pass at {run1_at.isoformat()}).")
        return False

    data = state["data"]
    changed = False
    for game in data["games"]:
        if game.get("highlight_url"):
            continue
        try:
            url = highlight_url_for_game(game["matchup"], game["line_score"], target_date)
        except Exception as e:
            print(f"Warning: second-pass highlight lookup failed for {game['game_id']} ({e}).")
            url = None
        if url:
            game["highlight_url"] = url
            changed = True

    if changed:
        saved_path = save(data, state["summary"])
        print(f"Second pass: updated {saved_path} with newly available highlight link(s).")
        _publish_to_github(saved_path)
    else:
        print(f"Second pass for {target_date}: still nothing new.")

    pending_path.unlink()
    return changed


def check(now: datetime | None = None) -> bool:
    """
    Runs the full pipeline for last night's games if it's ready, and returns
    True if it did. Returns False (no side effects) if it's not time yet.
    """
    now = now or datetime.now(timezone.utc)
    target_date = last_night_game_date(now)

    output_path = OUTPUT_DIR / f"{target_date}.html"
    pending_path = _pending_path(target_date)
    if output_path.exists():
        if pending_path.exists():
            return _try_second_pass(target_date, pending_path, now)
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

    missing = [g["game_id"] for g in data["games"] if not g.get("highlight_url")]
    if missing:
        PENDING_DIR.mkdir(exist_ok=True)
        pending_path.write_text(
            json.dumps({"data": data, "summary": summary, "run1_at": now.isoformat()}),
            encoding="utf-8",
        )
        print(
            f"{len(missing)} game(s) still missing a highlight link - "
            f"will retry once in ~{SECOND_PASS_MINUTES} min."
        )
    return True


if __name__ == "__main__":
    ran = check()
    sys.exit(0 if ran or "--strict" not in sys.argv else 1)
