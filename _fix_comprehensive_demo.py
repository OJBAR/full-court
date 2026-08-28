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
    # Prefilled mailto body ("תוכן הפניה:" / "צילומי מסך:") - added to
    # render.py's TEMPLATE after these 212 pages were already built; these
    # don't need re-fetching for a plain string swap like this one.
    (
        'subject=%D7%A4%D7%A0%D7%99%D7%99%D7%94+%D7%9C%D7%90%D7%AA%D7%A8+FULL+COURT:+%D7%A0%D7%95%D7%A9%D7%90+%D7%94%D7%A4%D7%A0%D7%99%D7%99%D7%94"',
        'subject=%D7%A4%D7%A0%D7%99%D7%99%D7%94+%D7%9C%D7%90%D7%AA%D7%A8+FULL+COURT:+%D7%A0%D7%95%D7%A9%D7%90+%D7%94%D7%A4%D7%A0%D7%99%D7%99%D7%94&body=%D7%AA%D7%95%D7%9B%D7%9F%20%D7%94%D7%A4%D7%A0%D7%99%D7%94%3A%0A%0A%D7%A6%D7%99%D7%9C%D7%95%D7%9E%D7%99%20%D7%9E%D7%A1%D7%9A%3A%0A"',
    ),
]

_NAV_BLOCK = """<!-- cd-nav-start -->
<script type="application/json" id="cdDates">__DATES_JSON__</script>
<script>
(function() {
  // Appended straight to document.body (the codebase's own proven pattern
  // for an always-visible overlay control - see the old install banner)
  // and position:fixed, deliberately NOT placed in the normal document
  // flow inside .wrapper. Two earlier attempts (sticky, top of the page,
  // living inside .wrapper) came up invisible specifically in the
  // installed PWA - tabs-mode makes .wrapper a fixed-height 100dvh flex
  // column, and every position/sizing trick tried there still depended on
  // that flow one way or another. Fixed-at-the-viewport sidesteps all of
  // it - and moved to the bottom, by request.
  var css = document.createElement("style");
  css.textContent = [
    ".cd-nav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 999;",
    "  display: flex; align-items: center; justify-content: center; gap: 6px;",
    "  padding: 8px; padding-bottom: calc(8px + env(safe-area-inset-bottom));",
    "  background: var(--card-bg); border-top: 1px solid var(--border);",
    "  direction: rtl; flex-wrap: nowrap; }",
    ".cd-nav button { border: 1px solid var(--border); background: var(--bg); color: var(--text-heading);",
    "  border-radius: 999px; font-size: 13px; cursor: pointer; flex-shrink: 0;",
    "  padding: 5px 9px; font-family: inherit; }",
    ".cd-nav button:disabled { opacity: 0.35; cursor: default; }",
    ".cd-nav .cd-label { font-size: 12px; color: var(--text-muted); white-space: nowrap; padding: 0 4px; }"
  ].join("\\n");
  document.head.appendChild(css);

  var bar = document.createElement("div");
  bar.className = "cd-nav";
  bar.dir = "rtl";
  bar.innerHTML =
    '<button type="button" id="cdBack10" title="10 אחורה">«« 10</button>' +
    '<button type="button" id="cdPrev" title="יום קודם">‹</button>' +
    '<span class="cd-label" id="cdLabel"></span>' +
    '<button type="button" id="cdNext" title="יום הבא">›</button>' +
    '<button type="button" id="cdFwd10" title="10 קדימה">10 »»</button>';
  document.body.appendChild(bar);

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

    # Idempotent: strips any previously-injected block (by its HTML comment
    # markers) before adding the current one, so re-running this script
    # after editing the nav bar's own template actually updates already-
    # fixed pages instead of leaving their old copy in place.
    html = re.sub(r"<!-- cd-nav-start -->.*?<!-- cd-nav-end -->", "", html, flags=re.S)
    # Leftover from the first (sticky-top, static <style> block) version of
    # this bar - no longer produced, but strip it from pages fixed by that
    # earlier run so it doesn't linger as dead/conflicting CSS.
    html = re.sub(r"/\* cd-nav-css-start \*/.*?/\* cd-nav-css-end \*/", "", html, flags=re.S)

    nav_block = _NAV_BLOCK.replace("__DATES_JSON__", dates_json).replace("__DATE__", date_str)
    # Right before </body> - the script builds and appends its own bar to
    # document.body at runtime (see _NAV_BLOCK's own comment for why).
    html = html.replace("</body>", nav_block + "\n</body>", 1)

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
