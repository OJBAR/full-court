"""
Temporary browsing page listing every demo brief currently in output/, since
it's NBA offseason right now (no real content to publish) but we still want
to verify the whole Pages/PWA publish chain works end-to-end. Once the real
season starts and scheduler.py is producing genuine nightly briefs, this page
stops being useful and can just be deleted (index.html - the PWA's actual
start_url - always shows the single latest real brief, unaffected by this).

Classifies each demo into exactly one of the six day-types (regular / cup
groups / cup knockout / playoffs / NBA Finals / Play-In) from the underlying
fixture's real data flags - not by scraping the rendered HTML's tab labels,
since a page can have several tabs (e.g. Finals days show both a Finals tab
and the two conference brackets).
"""
import json
from pathlib import Path

REPO_DIR = Path(__file__).parent
OUTPUT_DIR = REPO_DIR / "output"

FIXTURES = [
    "demo_fixture.json",
    "demo_regular_new_fixture.json",
    "demo_cup_groups_fixture.json",
    "demo_cup_groups_new_fixture.json",
    "demo_cup_knockout_fixture.json",
    "demo_cup_final_fixture.json",
    "demo_playoffs_fixture.json",
    "demo_playoffs_round2_fixture.json",
    "demo_playoffs_conf_finals_fixture.json",
    "demo_finals_fixture.json",
    "demo_play_in_fixture.json",
]


def classify(data: dict) -> str:
    if data.get("is_playoffs"):
        if any(s.get("round") == "NBA Finals" for s in data.get("playoff_series", [])):
            return "גמר NBA"
        return "פלייאוף"
    if data.get("is_cup_knockout"):
        return "גביע (נוקאאוט)"
    if data.get("is_cup_groups"):
        return "גביע (בתים)"
    if data.get("is_play_in"):
        return "פלייאין"
    return "יום רגיל"


rows = []
for fixture_name in FIXTURES:
    with open(REPO_DIR / fixture_name, encoding="utf-8") as f:
        fixture = json.load(f)
    data = fixture["data"]
    date_str = data["date"]
    if not (OUTPUT_DIR / f"{date_str}.html").exists():
        continue
    rows.append((date_str, classify(data)))

rows.sort()  # earliest to latest

items_html = "\n".join(
    f'<li><a href="{date}.html">{date}</a><span class="tabs"> - {category}</span></li>'
    for date, category in rows
)

# Same theme-variable system as render.py's TEMPLATE (light palette on :root,
# dark overrides via prefers-color-scheme + a manual data-theme toggle), so
# this temporary page matches the real site's look instead of being hardcoded
# to one look.
page = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Full Court - דמואים (זמני)</title>
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
    :root:not([data-theme="light"]) {{
      --bg: #2A2118;
      --card-bg: #241C14;
      --border: #453626;
      --accent: #E08A3E;
      --text-heading: #F0E6D6;
      --text-body: #D8C9AF;
      --text-muted: #8C7C64;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #2A2118;
    --card-bg: #241C14;
    --border: #453626;
    --accent: #E08A3E;
    --text-heading: #F0E6D6;
    --text-body: #D8C9AF;
    --text-muted: #8C7C64;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: "Segoe UI", "Rubik", Arial, sans-serif;
    background: var(--bg);
    color: var(--text-body);
    margin: 0;
    padding: 24px 16px;
  }}
  .theme-toggle {{
    position: absolute;
    top: 24px;
    left: 16px;
    width: 36px;
    height: 36px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--card-bg);
    color: var(--text-heading);
    font-size: 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
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
  <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" aria-label="החלף תצוגה בהירה/כהה">🌙</button>
  <h1>דמואים זמינים (זמני)</h1>
  <p class="note">דף זמני לבדיקת פרסום בלבד - זה offseason, אין עדיין תוכן אמיתי. ייעלם כשהעונה תתחיל.</p>
  <ul>
    {items_html}
  </ul>
  <script>
    (function() {{
      var saved = localStorage.getItem("nba-brief-theme");
      if (saved) {{ document.documentElement.setAttribute("data-theme", saved); }}
      updateToggleIcon();
    }})();
    function toggleTheme() {{
      var current = document.documentElement.getAttribute("data-theme");
      var systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      var isDark = current ? current === "dark" : systemDark;
      var next = isDark ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("nba-brief-theme", next);
      updateToggleIcon();
    }}
    function updateToggleIcon() {{
      var current = document.documentElement.getAttribute("data-theme");
      var systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      var isDark = current ? current === "dark" : systemDark;
      document.getElementById("theme-toggle").textContent = isDark ? "☀" : "🌙";
    }}
  </script>
</body>
</html>
"""

(OUTPUT_DIR / "demos.html").write_text(page, encoding="utf-8")
print(f"Saved output/demos.html with {len(rows)} entries.")
