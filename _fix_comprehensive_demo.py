"""
Post-processes the already-built output/comprehensive/{date}.html pages (no
re-fetching, no network calls - just string surgery on files that already
exist) to fix two things reported after the first version shipped:

1. Broken logo/favicon/manifest/demos-link: render.py's TEMPLATE always
   writes asset paths relative to output/ itself (e.g. "assets/logo_light.png")
   since that's where every real output/{date}.html lives - but these pages
   live one level deeper, in output/comprehensive/, so those same relative
   paths resolve to a comprehensive/assets/ that doesn't exist. Rewritten to
   "../assets/...", "../manifest.json", "../demos.html" here instead of in
   render.py itself, since render.py's own paths are correct for every real
   caller - this subdirectory placement is specific to this demo.

2. Inconvenient date switching: a persistent nav bar (prev/next single day,
   plus skip-10-game-nights forward/back) injected right into each page's
   own header, instead of only living on a separate picker home screen the
   user has to navigate back to. Uses the exact list of dates this demo
   actually built (order matters - "10 game nights" skips through games
   actually played, not 10 calendar days).
"""
import re
from pathlib import Path

from render import OUTPUT_DIR

COMPREHENSIVE_DIR = OUTPUT_DIR / "comprehensive"

_PATH_FIXES = [
    ('href="assets/', 'href="../assets/'),
    ('src="assets/', 'src="../assets/'),
    ('href="manifest.json"', 'href="../manifest.json"'),
    ('href="demos.html"', 'href="../demos.html"'),
    ('"assets/icon-192.png"', '"../assets/icon-192.png"'),
]

_NAV_CSS = """/* cd-nav-css-start */
  .cd-nav {
    position: sticky; top: 0; z-index: 200;
    display: flex; align-items: center; justify-content: center; gap: 6px;
    padding: 6px 8px; background: var(--card-bg); border-bottom: 1px solid var(--border);
    direction: rtl; flex-wrap: nowrap;
    /* In tabs-mode (see render.py) .wrapper is itself a fixed-height
       (100dvh) flex column, and .cd-nav sits in that flow as a sibling of
       .header/main - without this it's eligible to shrink like any other
       flex child (same class of bug already hit and fixed for the schedule
       tab's own sticky summary - see render.py's flex-shrink:0 on
       details.tab-section.app-screen-active > summary). Reported as
       invisible specifically in the installed PWA (tabs-mode's real
       target), consistent with that. */
    flex-shrink: 0;
  }
  .cd-nav button {
    border: 1px solid var(--border); background: var(--bg); color: var(--text-heading);
    border-radius: 999px; font-size: 13px; cursor: pointer; flex-shrink: 0;
    padding: 5px 9px; font-family: inherit;
  }
  .cd-nav button:disabled { opacity: 0.35; cursor: default; }
  .cd-nav .cd-label { font-size: 12px; color: var(--text-muted); white-space: nowrap; padding: 0 4px; }
  .cd-nav .cd-home {
    text-decoration: none; font-size: 15px; flex-shrink: 0;
    border: 1px solid var(--border); background: var(--bg); border-radius: 999px;
    width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  }
/* cd-nav-css-end */"""

_NAV_HTML_TEMPLATE = """<!-- cd-nav-start -->
<div class="cd-nav" dir="rtl">
  <a class="cd-home" href="../demos.html" title="כל הדמואים">🏠</a>
  <button type="button" id="cdBack10" title="10 אחורה">«« 10</button>
  <button type="button" id="cdPrev" title="יום קודם">‹</button>
  <span class="cd-label" id="cdLabel"></span>
  <button type="button" id="cdNext" title="יום הבא">›</button>
  <button type="button" id="cdFwd10" title="10 קדימה">10 »»</button>
</div>
<script type="application/json" id="cdDates">__DATES_JSON__</script>
<script>
(function() {
  var dates = JSON.parse(document.getElementById("cdDates").textContent);
  var here = "__DATE__";
  var idx = dates.indexOf(here);
  var label = document.getElementById("cdLabel");
  var back10 = document.getElementById("cdBack10");
  var prev = document.getElementById("cdPrev");
  var next = document.getElementById("cdNext");
  var fwd10 = document.getElementById("cdFwd10");

  function fmt(d) {
    var p = d.split("-");
    return p[2] + "." + p[1] + "." + p[0];
  }
  function go(newIdx) {
    newIdx = Math.max(0, Math.min(newIdx, dates.length - 1));
    if (newIdx === idx) return;
    location.href = dates[newIdx] + ".html";
  }
  if (idx === -1) { if (label) label.textContent = here; }
  else {
    label.textContent = fmt(dates[idx]) + " (" + (idx + 1) + "/" + dates.length + ")";
    prev.disabled = idx === 0;
    next.disabled = idx === dates.length - 1;
    back10.disabled = idx === 0;
    fwd10.disabled = idx === dates.length - 1;
    prev.addEventListener("click", function() { go(idx - 1); });
    next.addEventListener("click", function() { go(idx + 1); });
    back10.addEventListener("click", function() { go(idx - 10); });
    fwd10.addEventListener("click", function() { go(idx + 10); });
  }
})();
</script>
<!-- cd-nav-end -->"""


def real_built_dates() -> list[str]:
    dates = sorted(p.stem for p in COMPREHENSIVE_DIR.glob("*.html") if p.stem != "index")
    return dates


def fix_file(path: Path, date_str: str, dates_json: str) -> None:
    html = path.read_text(encoding="utf-8")

    for old, new in _PATH_FIXES:
        html = html.replace(old, new)

    # The "לוח התוצאות" tab inside the page itself defaults to the real
    # viewer's live today (see render.py's initScheduleTab()) - correct for
    # a real brief, wrong here: viewing 2025-11-28's page in real August
    # 2026 would otherwise show that tab defaulting to "season's over"
    # instead of actually opening on 2025-11-28, breaking "if I'd opened
    # the app on this date last season." Same data-simulated-today override
    # mechanism the hand-authored demo fixtures already use (see
    # render._build_schedule_html's simulated_today param) - injected
    # directly into the already-rendered HTML here instead of re-fetching.
    html = html.replace(
        '<div class="schedule-tab">',
        f'<div class="schedule-tab" data-simulated-today="{date_str}">',
        1,
    )

    # Idempotent: strips any previously-injected block (by its HTML/CSS
    # comment markers) before adding the current one, so re-running this
    # script after editing the nav bar's own template actually updates
    # already-fixed pages instead of leaving their old copy in place.
    html = re.sub(r"<!-- cd-nav-start -->.*?<!-- cd-nav-end -->", "", html, flags=re.S)
    html = re.sub(r"/\* cd-nav-css-start \*/.*?/\* cd-nav-css-end \*/", "", html, flags=re.S)

    nav_html = _NAV_HTML_TEMPLATE.replace("__DATES_JSON__", dates_json).replace("__DATE__", date_str)
    # Right after <div class="wrapper"> - top of the visible page, above
    # the header, so it's always the first thing on screen regardless of
    # scroll position (position:sticky handles staying there after).
    html = html.replace('<div class="wrapper">', '<div class="wrapper">' + nav_html, 1)
    html = html.replace("</style>", _NAV_CSS + "</style>", 1)

    path.write_text(html, encoding="utf-8")


def main():
    dates = real_built_dates()
    import json

    dates_json = json.dumps(dates).replace("</", "<\\/")
    print(f"Fixing {len(dates)} pages...")
    for date_str in dates:
        fix_file(COMPREHENSIVE_DIR / f"{date_str}.html", date_str, dates_json)

    # index.html is just a copy of the latest real date's own (now-fixed)
    # page - not a separate bespoke picker - so landing on the demo IS the
    # real product, nav bar and all. Copied last, after fixes, so it picks
    # up everything above.
    latest = dates[-1]
    latest_html = (COMPREHENSIVE_DIR / f"{latest}.html").read_text(encoding="utf-8")
    (COMPREHENSIVE_DIR / "index.html").write_text(latest_html, encoding="utf-8")
    print(f"index.html copied from {latest}.html")
    print("Done.")


if __name__ == "__main__":
    main()
