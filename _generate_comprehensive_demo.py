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
    The comprehensive demo's own home screen: a real day-by-day browser (the
    same shape as the real brief's own "לוח התוצאות" tab - arrows + swipe,
    one date at a time), front and center rather than buried in a tab, so
    switching between real dates from last season feels like the product
    itself. Unlike the schedule tab, this only steps through dates that were
    actually built here (a dense but not perfectly continuous run - a
    handful of real dates can fail/be skipped), not a calendar.
    """
    built_sorted = sorted(built)
    entries = [
        {"date": d, "display": datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")}
        for d in built_sorted
    ]
    import json as _json
    payload = _json.dumps(entries, ensure_ascii=False).replace("</", "<\\/")
    show_dots = len(entries) <= 20
    dots_html = '<div class="dots" id="dots"></div>' if show_dots else ""

    page = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Full Court - דמו כולל</title>
<style>
  :root {{
    --bg: #EFEAD8;
    --card-bg: #E4DDC5;
    --border: #DAD2B8;
    --accent: #A67C1E;
    --text-heading: #2E2A1E;
    --text-body: #4A4530;
    --text-muted: #93876A;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #2A2118;
      --card-bg: #241C14;
      --border: #453626;
      --accent: #E08A3E;
      --text-heading: #F0E6D6;
      --text-body: #D8C9AF;
      --text-muted: #8C7C64;
    }}
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ touch-action: pan-y; }}
  body {{
    font-family: "Segoe UI", "Rubik", Arial, sans-serif;
    background: var(--bg);
    color: var(--text-body);
    margin: 0;
    padding: 24px 16px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  h1 {{ font-size: 18px; color: var(--text-heading); text-align: center; margin-bottom: 4px; }}
  p.note {{ color: var(--text-muted); font-size: 13px; text-align: center; max-width: 480px; margin: 0 auto 20px; }}
  .picker {{ max-width: 420px; margin: 0 auto; width: 100%; flex: 1; display: flex; flex-direction: column; justify-content: center; }}
  .nav {{ display: flex; align-items: center; justify-content: center; gap: 16px; }}
  .arrow {{
    width: 40px; height: 40px; flex-shrink: 0;
    border-radius: 999px; border: 1px solid var(--border); background: var(--card-bg);
    color: var(--text-heading); font-size: 20px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
  }}
  .arrow:disabled {{ opacity: 0.35; cursor: default; }}
  .card {{ flex: 1; text-align: center; padding: 4px 8px; }}
  .card .date {{ font-size: 1.5rem; font-weight: 700; color: var(--text-heading); }}
  .card .count {{ font-size: 0.8125rem; color: var(--text-muted); margin-top: 4px; }}
  .open-btn {{
    display: inline-block;
    margin-top: 24px;
    padding: 12px 28px;
    border-radius: 999px;
    background: var(--accent);
    color: var(--card-bg);
    font-weight: 700;
    text-decoration: none;
  }}
  .dots {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 6px; margin-top: 20px; }}
  .dot {{ width: 7px; height: 7px; border-radius: 999px; background: var(--border); }}
  .dot.active {{ background: var(--accent); }}
  .jump-row {{ display: flex; justify-content: center; margin-top: 16px; }}
  .jump-row input {{
    font-family: inherit; font-size: 0.9375rem; padding: 6px 10px;
    border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text-heading);
  }}
</style>
</head>
<body>
  <h1>דמו כולל - נתונים אמיתיים</h1>
  <p class="note">כל תאריך כאן הוא ברייף אמיתי מהעונה שעברה - תוצאות, טבלה, בראקטים
    וקישורים אמיתיים - כולל תקצירי וידאו. רק פסקת הסיכום היא טקסט פילר קבוע.</p>
  <div class="picker" id="picker">
    <div class="nav">
      <button type="button" class="arrow" id="prevBtn" aria-label="תאריך קודם">‹</button>
      <div class="card">
        <div class="date" id="dateLabel"></div>
        <div class="count" id="countLabel"></div>
        <a class="open-btn" id="openBtn" href="#">פתח את הברייף</a>
      </div>
      <button type="button" class="arrow" id="nextBtn" aria-label="תאריך הבא">›</button>
    </div>
    {dots_html}
    <div class="jump-row">
      <input type="date" id="jumpInput" aria-label="קפוץ לתאריך">
    </div>
  </div>
  <script type="application/json" id="datesData">{payload}</script>
  <script>
    (function() {{
      var dates = JSON.parse(document.getElementById("datesData").textContent);
      var idx = dates.length - 1; // start on the latest real date
      var picker = document.getElementById("picker");
      var dateLabel = document.getElementById("dateLabel");
      var countLabel = document.getElementById("countLabel");
      var openBtn = document.getElementById("openBtn");
      var prevBtn = document.getElementById("prevBtn");
      var nextBtn = document.getElementById("nextBtn");
      var dotsEl = document.getElementById("dots");
      var jumpInput = document.getElementById("jumpInput");

      if (dotsEl) {{
        dates.forEach(function() {{
          var d = document.createElement("span");
          d.className = "dot";
          dotsEl.appendChild(d);
        }});
      }}

      function render() {{
        var d = dates[idx];
        dateLabel.textContent = d.display;
        countLabel.textContent = (idx + 1) + " מתוך " + dates.length;
        openBtn.href = d.date + ".html";
        prevBtn.disabled = idx === 0;
        nextBtn.disabled = idx === dates.length - 1;
        jumpInput.value = d.date;
        if (dotsEl) {{
          Array.prototype.forEach.call(dotsEl.children, function(dot, i) {{
            dot.classList.toggle("active", i === idx);
          }});
        }}
      }}

      prevBtn.addEventListener("click", function() {{ if (idx > 0) {{ idx--; render(); }} }});
      nextBtn.addEventListener("click", function() {{ if (idx < dates.length - 1) {{ idx++; render(); }} }});

      jumpInput.addEventListener("change", function() {{
        var target = jumpInput.value;
        var found = -1;
        for (var i = 0; i < dates.length; i++) {{
          if (dates[i].date >= target) {{ found = i; break; }}
        }}
        if (found === -1) found = dates.length - 1;
        idx = found;
        render();
      }});

      // Swipe, same shape as the real brief's schedule tab - no
      // preventDefault, passive throughout.
      var startX = null, startY = null, dragging = false;
      picker.addEventListener("touchstart", function(e) {{
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        dragging = false;
      }}, {{ passive: true }});
      picker.addEventListener("touchmove", function(e) {{
        if (startX === null) return;
        var dx = e.touches[0].clientX - startX;
        var dy = e.touches[0].clientY - startY;
        if (!dragging && Math.abs(dx) < Math.abs(dy)) return;
        dragging = true;
      }}, {{ passive: true }});
      picker.addEventListener("touchend", function(e) {{
        if (!dragging) {{ startX = null; return; }}
        var dx = e.changedTouches[0].clientX - startX;
        var threshold = 40;
        startX = null;
        dragging = false;
        if (dx >= threshold && idx > 0) {{ idx--; render(); }}
        else if (dx <= -threshold && idx < dates.length - 1) {{ idx++; render(); }}
      }}, {{ passive: true }});

      render();
    }})();
  </script>
</body>
</html>
"""
    index_path = COMPREHENSIVE_DIR / "index.html"
    index_path.write_text(page, encoding="utf-8")
    print(f"Saved {index_path} with {len(built)} entries.")


if __name__ == "__main__":
    built = build()
    if built:
        build_index(built)
    else:
        print("Nothing built - all dates failed.")
        sys.exit(1)
