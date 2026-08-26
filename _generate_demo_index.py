"""
Temporary browsing page listing every demo brief currently in output/, since
it's NBA offseason right now (no real content to publish) but we still want
to verify the whole Pages/PWA publish chain works end-to-end. Once the real
season starts and scheduler.py is producing genuine nightly briefs, this page
stops being useful and can just be deleted (index.html - the PWA's actual
start_url - always shows the single latest real brief, unaffected by this).
"""
import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>")

rows = []
for path in sorted(OUTPUT_DIR.glob("????-??-??.html")):
    date_str = path.stem
    html = path.read_text(encoding="utf-8")
    tabs = SUMMARY_RE.findall(html)
    tabs_label = " · ".join(tabs) if tabs else ""
    rows.append((date_str, tabs_label))

rows.sort(reverse=True)

items_html = "\n".join(
    f'<li><a href="{date}.html">{date}</a>'
    + (f'<span class="tabs"> - {tabs}</span>' if tabs else "")
    + "</li>"
    for date, tabs in rows
)

page = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Full Court - דמואים (זמני)</title>
<style>
  body {{ font-family: "Segoe UI", "Rubik", Arial, sans-serif; background: #2A2118; color: #D8C9AF; margin: 0; padding: 24px 16px; }}
  h1 {{ font-size: 18px; color: #F0E6D6; }}
  p.note {{ color: #8C7C64; font-size: 13px; }}
  ul {{ list-style: none; padding: 0; max-width: 480px; margin: 20px auto 0; }}
  li {{ border: 1px solid #453626; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; }}
  a {{ color: #E08A3E; text-decoration: none; font-weight: 700; }}
  a:hover {{ text-decoration: underline; }}
  .tabs {{ color: #8C7C64; font-size: 12px; font-weight: 400; }}
</style>
</head>
<body>
  <h1>דמואים זמינים (זמני)</h1>
  <p class="note">דף זמני לבדיקת פרסום בלבד - זה offseason, אין עדיין תוכן אמיתי. ייעלם כשהעונה תתחיל.</p>
  <ul>
    {items_html}
  </ul>
</body>
</html>
"""

(OUTPUT_DIR / "demos.html").write_text(page, encoding="utf-8")
print(f"Saved output/demos.html with {len(rows)} entries.")
