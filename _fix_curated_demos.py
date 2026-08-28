"""
Post-processes the 5 curated demo pages (output/{date}.html, built by
_build_curated_demos.py) so installing "as an app" from any one of them
opens THAT demo, not whichever page happened to render most recently.

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

An earlier version of this script also injected a fixed-bottom nav bar
(prev/next between the 5) here, mirroring the comprehensive dev demo - by
request, dropped again: moving between demos is meant to go through
Settings' own "מעבר בין דמואים" link (demos.html), not a second in-page
control. The strip-leftover-markers step below stays so re-running this on
an already-fixed (older) page cleans that bar out.

Deliberately does NOT touch the real manifest.json or any non-curated
output/*.html - only the 5 dates in CURATED_DATES ever get the
demos-manifest.json link.
"""
import re
from pathlib import Path

from render import OUTPUT_DIR

CURATED_DATES = [
    "2025-10-22",
    "2025-11-28",
    "2025-12-13",
    "2026-04-17",
    "2026-05-17",
]


def fix_file(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    html = html.replace('href="manifest.json"', 'href="demos-manifest.json"', 1)
    # Leftover from an earlier version of this script that injected a nav
    # bar here - stripped so a page fixed by that older run cleans up too.
    html = re.sub(r"<!-- curated-nav-start -->.*?<!-- curated-nav-end -->", "", html, flags=re.S)
    path.write_text(html, encoding="utf-8")


def main():
    print(f"Fixing {len(CURATED_DATES)} curated demo pages...")
    for date_str in CURATED_DATES:
        path = OUTPUT_DIR / f"{date_str}.html"
        if not path.exists():
            print(f"  MISSING {path} - run _build_curated_demos.py first. Skipping.")
            continue
        fix_file(path)
        print(f"  fixed {path.name}")
    print("Done.")


if __name__ == "__main__":
    main()
