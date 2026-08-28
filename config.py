from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

US_EASTERN = ZoneInfo("America/New_York")
# The schedule tab's own client-side day grouping (render.py's
# initScheduleTab()/ilDateKey()) buckets games by ISRAEL calendar day, not
# US Eastern - correct for the viewer ("future days show tip-off time in
# Israel time"), but a US-Eastern date string like the one
# last_night_game_date() returns is NOT automatically the same calendar day
# in Israel (a game tipping off late evening ET already lands on the NEXT
# Israel calendar day). Anything that feeds a date into that tab's own
# "today" bucket (see _generate_comprehensive_demo.py's demo_today) needs
# this zone, not US_EASTERN, or it opens on a day whose bucket doesn't
# actually contain the games it's supposed to.
ISRAEL = ZoneInfo("Asia/Jerusalem")


def last_night_game_date(now: datetime | None = None) -> str:
    """
    Returns the US Eastern calendar date (YYYY-MM-DD) of the most recently
    completed NBA game day. zoneinfo gives the correct current time in New
    York directly, regardless of what timezone the machine running this is
    set to, so no separate Israel-time step is needed.
    """
    now_eastern = now.astimezone(US_EASTERN) if now else datetime.now(US_EASTERN)
    yesterday_eastern = now_eastern - timedelta(days=1)
    return yesterday_eastern.strftime("%Y-%m-%d")


def season_string_for(date_str: str) -> str:
    """
    Converts a YYYY-MM-DD date into the NBA season string it belongs to
    (e.g. "2025-26"). The NBA season starts in October and runs through
    June of the following year.
    """
    year, month, _ = (int(part) for part in date_str.split("-"))
    start_year = year if month >= 10 else year - 1
    return f"{start_year}-{str(start_year + 1)[2:]}"
