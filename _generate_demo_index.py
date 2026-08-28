"""
The 5-demo "beta" browsing page linked from every real page's footer
("גרסת בטא · מעבר בין דמואים"). Replaces the old 11-demo lineup (a mix of
real data and entirely fabricated playoff/cup/Play-In scenarios) - all 5 of
these are real 2025-26 season data with a real Claude-written summary, built
by _build_curated_demos.py (see that file's own docstring for exactly which
5 dates and why). This script only builds the browsing/index page itself,
reading each date's already-rendered output/{date}.html for its metadata -
run _build_curated_demos.py first if any of these 5 pages don't exist yet.
"""
from pathlib import Path

REPO_DIR = Path(__file__).parent
OUTPUT_DIR = REPO_DIR / "output"

# Keep in sync with _build_curated_demos.py's own CURATED_DATES - mirrored
# here (not imported) since this script only needs the date+label pairs,
# not any of that module's heavier real-data-fetching imports.
CURATED = [
    ("2025-10-22", "יום רגיל"),
    ("2025-11-28", "גביע (בתים)"),
    ("2025-12-13", "גביע (נוקאאוט)"),
    ("2026-04-17", "פלייאין"),
    ("2026-05-17", "פלייאוף"),
]


rows = []
for date_str, category in CURATED:
    if not (OUTPUT_DIR / f"{date_str}.html").exists():
        continue
    rows.append((date_str, category))

items_html = "\n".join(
    f'<li><a href="{date}.html">{date}</a><span class="tabs"> - {category}</span></li>'
    for date, category in rows
)

# Same theme-variable system as render.py's TEMPLATE (light palette on :root,
# dark overrides via prefers-color-scheme + a manual data-theme toggle), so
# this page matches the real site's look instead of being hardcoded to one.
page = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Full Court - דמואים</title>
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
  body {{
    font-family: "Segoe UI", "Rubik", Arial, sans-serif;
    background: var(--bg);
    color: var(--text-body);
    margin: 0;
    padding: 24px 16px;
  }}
  h1 {{ font-size: 18px; color: var(--text-heading); text-align: center; }}
  p.note {{ color: var(--text-muted); font-size: 13px; text-align: center; }}
  ul {{ list-style: none; padding: 0; max-width: 480px; margin: 20px auto 0; }}
  li {{
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 8px;
    background: var(--card-bg);
  }}
  a {{ color: var(--accent); text-decoration: none; font-weight: 700; }}
  .tabs {{ color: var(--text-muted); font-size: 12px; font-weight: 400; }}
</style>
</head>
<body>
  <h1>דמואים</h1>
  <p class="note">5 לילות אמיתיים מהעונה שעברה - נתונים וסיכומים אמיתיים, אחד לכל סוג יום.</p>
  <ul>
    {items_html}
  </ul>
</body>
</html>
"""

(OUTPUT_DIR / "demos.html").write_text(page, encoding="utf-8")
print(f"Saved output/demos.html with {len(rows)} entries.")
