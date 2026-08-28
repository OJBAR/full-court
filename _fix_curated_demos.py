"""
Post-processes the 5 curated demo pages (output/{date}.html, built by
_build_curated_demos.py) so installing "as an app" from any one of them
behaves the way the comprehensive dev demo already does - a dedicated PWA
identity + an in-page way to reach the other 4, instead of only demos.html.

Why these 5 need their own manifest at all (same root cause diagnosed for
the comprehensive demo, see _fix_comprehensive_demo.py's own docstring): a
PWA's installed icon always opens whatever its manifest.json's start_url
says, REGARDLESS of which page you tapped "Add to Home Screen" from. These
5 pages sit at the same output/{date}.html path real daily briefs will
someday use, and so far all share output/manifest.json - whose start_url
("./") always resolves to output/index.html, which render.save() overwrites
on every single run (curated demo or real brief alike). Installing "from"
any specific demo still only ever opens whichever page was rendered most
recently - not a bug exactly (this IS the real product's intended
behavior - the icon should always show the latest real brief once
scheduler.py is actually running), but useless for "install this one demo
as its own thing", which is what the user actually wants here.

demos-manifest.json (a new, separate file, NOT touched by anything real-
product-related) fixes the identity: start_url is pinned to the first
curated date, so the installed icon always lands somewhere real and stable.
The injected nav bar (same fixed-bottom-pill pattern the comprehensive demo
already proved out) is what makes the OTHER 4 reachable from there without
detouring back to demos.html on every visit.

Deliberately does NOT touch the real manifest.json or any non-curated
output/*.html - only the 5 dates in CURATED_DATES ever get the
demos-manifest.json link + nav bar. Unlike the dev nav bar
(_fix_comprehensive_demo.py), this one does NOT disable the splash-logo
animation - the whole point of the curated demos is to look exactly like
the real product, splash included.
"""
import json
from pathlib import Path

from render import OUTPUT_DIR

CURATED_DATES = [
    "2025-10-22",
    "2025-11-28",
    "2025-12-13",
    "2026-04-17",
    "2026-05-17",
]

_NAV_BLOCK = """<!-- curated-nav-start -->
<script type="application/json" id="curatedDates">__DATES_JSON__</script>
<script>
(function() {
  var css = document.createElement("style");
  css.textContent = [
    ".curated-nav { position: fixed; left: 0; right: 0; bottom: calc(14px + env(safe-area-inset-bottom)); z-index: 999;",
    "  display: flex; align-items: center; justify-content: center; gap: 6px;",
    "  padding: 8px; border-radius: 999px; margin: 0 12px;",
    "  background: var(--card-bg); border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.15);",
    "  direction: rtl; flex-wrap: nowrap;",
    "  transform: translateZ(0); -webkit-transform: translateZ(0); will-change: transform; }",
    ".curated-nav button { border: 1px solid var(--border); background: var(--bg); color: var(--text-heading);",
    "  border-radius: 999px; font-size: 13px; cursor: pointer; flex-shrink: 0;",
    "  padding: 5px 9px; font-family: inherit; }",
    ".curated-nav button:disabled { opacity: 0.35; cursor: default; }",
  ].join("\\n");
  document.head.appendChild(css);

  // No date label here (see the fix script's own comment) - the app
  // already shows the date itself (header / settings), so a second one
  // in this bar was redundant. Just the two arrows to move between demos.
  var bar = document.createElement("div");
  bar.className = "curated-nav";
  bar.dir = "rtl";
  bar.innerHTML =
    '<button type="button" id="curatedPrev" title="דמו קודם">‹</button>' +
    '<button type="button" id="curatedNext" title="דמו הבא">›</button>';
  document.body.appendChild(bar);

  var dates = JSON.parse(document.getElementById("curatedDates").textContent);
  var here = "__DATE__";
  var idx = dates.indexOf(here);
  var prev = document.getElementById("curatedPrev");
  var next = document.getElementById("curatedNext");

  function go(newIdx) {
    newIdx = Math.max(0, Math.min(newIdx, dates.length - 1));
    if (newIdx === idx) return;
    location.href = dates[newIdx] + ".html";
  }
  if (idx !== -1) {
    prev.disabled = idx === 0;
    next.disabled = idx === dates.length - 1;
    prev.addEventListener("click", function() { go(idx - 1); });
    next.addEventListener("click", function() { go(idx + 1); });
  }
})();
</script>
<!-- curated-nav-end -->"""


def fix_file(path: Path, date_str: str, dates_json: str) -> None:
    html = path.read_text(encoding="utf-8")

    html = html.replace('href="manifest.json"', 'href="demos-manifest.json"', 1)

    # Idempotent, same reasoning as _fix_comprehensive_demo.py's own marker
    # strip-then-reinsert: safe to re-run after editing the nav bar itself.
    import re

    html = re.sub(r"<!-- curated-nav-start -->.*?<!-- curated-nav-end -->", "", html, flags=re.S)

    nav_block = _NAV_BLOCK.replace("__DATES_JSON__", dates_json).replace("__DATE__", date_str)
    html = html.replace("</body>", nav_block + "\n</body>", 1)

    path.write_text(html, encoding="utf-8")


def main():
    dates_json = json.dumps(CURATED_DATES).replace("</", "<\\/")
    print(f"Fixing {len(CURATED_DATES)} curated demo pages...")
    for date_str in CURATED_DATES:
        path = OUTPUT_DIR / f"{date_str}.html"
        if not path.exists():
            print(f"  MISSING {path} - run _build_curated_demos.py first. Skipping.")
            continue
        fix_file(path, date_str, dates_json)
        print(f"  fixed {path.name}")
    print("Done.")


if __name__ == "__main__":
    main()
