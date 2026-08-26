import html
import re
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"

_HEBREW_WEEKDAYS = {
    0: "שני",
    1: "שלישי",
    2: "רביעי",
    3: "חמישי",
    4: "שישי",
    5: "שבת",
    6: "ראשון",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FULL COURT - {display_date}</title>
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="assets/icon-180.png">
<meta name="theme-color" content="#EFEAD8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#2A2118" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Full Court">
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
  :root[data-a11y-fontsize="large"] {{ --a11y-zoom: 1.15; }}
  :root[data-a11y-fontsize="xlarge"] {{ --a11y-zoom: 1.3; }}
  * {{ box-sizing: border-box; }}
  a:focus-visible,
  button:focus-visible,
  summary:focus-visible {{
    outline: 2px solid var(--accent);
    outline-offset: 2px;
    border-radius: 4px;
  }}
  .sr-only {{
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }}
  body {{
    font-family: "Segoe UI", "Rubik", Arial, sans-serif;
    background: var(--bg);
    color: var(--text-body);
    margin: 0;
    padding: 0;
  }}
  .wrapper {{
    max-width: 640px;
    margin: 0 auto;
    padding: 24px 16px 40px;
    position: relative;
    zoom: var(--a11y-zoom, 1);
  }}
  .theme-toggle,
  .a11y-toggle {{
    position: absolute;
    top: 24px;
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
  .theme-toggle {{ left: 16px; }}
  .a11y-toggle {{ right: 16px; }}
  .header {{
    text-align: center;
    padding-bottom: 20px;
    border-bottom: 2px solid var(--accent);
    margin-bottom: 20px;
  }}
  .logo-img {{
    height: 40px;
    width: auto;
    display: block;
    margin: 0 auto;
  }}
  .logo-dark {{ display: none; }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) .logo-light {{ display: none; }}
    :root:not([data-theme="light"]) .logo-dark {{ display: block; }}
  }}
  [data-theme="dark"] .logo-light {{ display: none; }}
  [data-theme="dark"] .logo-dark {{ display: block; }}
  .header h1 {{
    font-size: 14px;
    font-weight: 400;
    margin: 8px 0 0;
    color: var(--text-muted);
  }}
  .header .date {{
    color: var(--text-muted);
    font-size: 13px;
    margin-top: 6px;
  }}
  .summary {{
    font-size: 16px;
    line-height: 1.8;
  }}
  .summary p {{
    margin: 0 0 16px 0;
  }}
  details {{
    margin-top: 12px;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    background: var(--card-bg);
  }}
  summary {{
    list-style: none;
    cursor: pointer;
    padding: 14px 16px;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-heading);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  summary::-webkit-details-marker {{ display: none; }}
  summary::after {{
    content: "＋";
    color: var(--accent);
    font-size: 16px;
  }}
  details[open] summary::after {{ content: "－"; }}
  details[open] summary {{ border-bottom: 1px solid var(--border); }}
  .details-body {{ padding: 12px 16px 16px; }}

  .game-block {{
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }}
  .game-block:last-child {{ border-bottom: none; margin-bottom: 0; }}
  .game-row {{
    display: flex;
    align-items: center;
    justify-content: center;
    padding-top: 8px;
    font-size: 14px;
  }}
  .team {{ width: 4.5em; color: var(--text-muted); text-align: center; }}
  .team.winner {{ color: var(--text-heading); font-weight: 700; }}
  .team-record {{
    display: block;
    font-size: 9px;
    font-weight: 400;
    color: var(--text-muted);
  }}
  .score {{ width: 2.2em; text-align: center; color: var(--text-muted); font-variant-numeric: tabular-nums; }}
  .score.winner {{ color: var(--accent); font-weight: 700; }}
  .ot-tag {{
    margin-inline-start: 6px;
    padding: 1px 5px;
    border-radius: 999px;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 9px;
    font-weight: 700;
    vertical-align: middle;
  }}
  .game-sub {{
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 6px;
  }}

  .conferences {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
  }}
  @media (min-width: 480px) {{
    .conferences {{ grid-template-columns: 1fr 1fr; }}
  }}
  .conference h3 {{
    font-size: 13px;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 0 0 8px 0;
    text-align: center;
  }}
  .standings-block {{
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px;
    background: var(--bg);
  }}
  .standing-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    font-size: 13px;
    border-bottom: 1px solid var(--border);
  }}
  .standing-row:last-child {{ border-bottom: none; }}
  .standing-row.boundary {{ border-bottom: 1px dashed var(--accent); }}
  .standing-rank {{ color: var(--text-muted); width: 1.6em; flex-shrink: 0; }}
  .standing-team {{
    flex: 1;
    min-width: 0;
    color: var(--text-heading);
    white-space: nowrap;
    font-size: 12px;
  }}
  .standing-record {{ color: var(--text-muted); flex-shrink: 0; }}
  .standing-streak {{ width: 3em; text-align: right; flex-shrink: 0; font-variant-numeric: tabular-nums; }}
  .standing-streak.win {{ color: #4caf7d; }}
  .standing-streak.loss {{ color: #e05d5d; }}
  .standing-diff {{ width: 3em; text-align: right; flex-shrink: 0; font-variant-numeric: tabular-nums; color: var(--text-muted); }}
  .wildcard-badge {{
    display: inline-block;
    margin-left: 4px;
    padding: 1px 5px;
    border-radius: 999px;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 9px;
    font-weight: 700;
    vertical-align: middle;
  }}
  .wildcard-legend {{
    grid-column: 1 / -1;
    margin: 10px 2px 0;
    font-size: 11px;
    color: var(--text-muted);
    text-align: right;
  }}

  .cup-group {{
    margin-bottom: 10px;
    padding: 8px 10px 6px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--card-bg);
  }}
  .cup-group:last-child {{ margin-bottom: 0; }}
  .cup-group h4 {{
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 4px 0;
  }}

  .bracket {{
    display: flex;
    justify-content: safe center;
    gap: 24px;
    overflow-x: auto;
    padding: 4px 4px 12px;
  }}
  .bracket-column {{
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }}
  .bracket-round-label {{
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    text-align: center;
    margin: 0 0 10px 0;
  }}
  .bracket-round {{
    display: flex;
    flex: 1;
    flex-direction: column;
    justify-content: space-around;
    gap: 20px;
  }}
  .bracket-final {{ justify-content: center; }}
  .bracket-pair {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 16px;
    position: relative;
    padding-right: 16px;
    border-right: 2px solid var(--text-muted);
  }}
  .bracket-pair::after {{
    content: "";
    position: absolute;
    top: 50%;
    left: 100%;
    width: 25px;
    height: 2px;
    margin-top: -1px;
    background: var(--text-muted);
  }}
  .bracket-match {{
    width: 128px;
    flex-shrink: 0;
    padding: 6px 10px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
  }}
  .bracket-team {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    color: var(--text-muted);
    padding: 2px 0;
  }}
  .bracket-team.winner {{ color: var(--text-heading); font-weight: 700; }}
  .bracket-team-name {{
    display: flex;
    flex-direction: column;
    line-height: 1.3;
  }}
  .bracket-team-label {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }}
  .bracket-seed {{
    font-size: 10px;
    color: var(--text-muted);
    min-width: 1.2em;
    text-align: center;
    padding: 0 3px;
    border: 1px solid var(--border);
    border-radius: 4px;
  }}
  .conf-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 14px;
    height: 14px;
    border-radius: 3px;
    font-size: 9px;
    font-weight: 700;
    color: #fff;
  }}
  .conf-badge-east {{ background: #3b6fd6; }}
  .conf-badge-west {{ background: #c0392b; }}
  .bracket-record {{
    font-size: 9px;
    font-weight: 400;
    color: var(--text-muted);
  }}
  .bracket-score {{ font-variant-numeric: tabular-nums; }}
  .bracket-match-tbd {{ opacity: 0.55; border-style: dashed; font-style: italic; }}
  .bracket-match-wrap {{ width: 128px; flex-shrink: 0; }}
  .bracket-caption {{
    margin-top: 4px;
    font-size: 10px;
    line-height: 1.3;
    color: var(--text-muted);
    text-align: center;
    direction: rtl;
    /* Fixed height (~2 lines) regardless of actual caption length - the two
       Play-In captions in a pair are very different lengths ("מנצחת עולה
       לפלייאוף מהמקום ה-7" vs "מפסידה מודחת"), and without this the
       .bracket-pair's 50% connector midpoint drifts off from the true
       midpoint between the two match boxes whenever their wrap heights
       differ. */
    min-height: 2.6em;
  }}

  .a11y-overlay {{
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    z-index: 100;
  }}
  .a11y-overlay[hidden] {{ display: none; }}
  .a11y-panel {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    max-width: 320px;
    width: 100%;
  }}
  .a11y-panel-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }}
  .a11y-panel-header h2 {{
    font-size: 16px;
    color: var(--text-heading);
    margin: 0;
  }}
  .a11y-panel-close {{
    width: 30px;
    height: 30px;
    flex-shrink: 0;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text-heading);
    font-size: 14px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .a11y-field-label {{
    display: block;
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 8px;
  }}
  .a11y-fontsize-options {{
    display: flex;
    gap: 8px;
  }}
  .a11y-fontsize-btn {{
    flex: 1;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text-body);
    cursor: pointer;
  }}
  .a11y-fontsize-btn[aria-pressed="true"] {{
    border-color: var(--accent);
    color: var(--accent);
    font-weight: 700;
  }}
  .a11y-fontsize-btn.a11y-fontsize-sm {{ font-size: 14px; }}
  .a11y-fontsize-btn.a11y-fontsize-md {{ font-size: 19px; }}
  .a11y-fontsize-btn.a11y-fontsize-lg {{ font-size: 24px; }}
  .a11y-link-btn {{
    display: block;
    width: 100%;
    margin-top: 14px;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--accent);
    font-size: 13px;
    font-weight: 600;
    text-align: center;
    cursor: pointer;
  }}
  .email-row {{
    display: flex;
    align-items: stretch;
    gap: 8px;
  }}
  .email-row .a11y-link-btn {{ flex: 1; min-width: 0; }}
  .copy-email-btn {{
    flex-shrink: 0;
    width: 40px;
    margin-top: 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--accent);
    font-size: 15px;
    cursor: pointer;
  }}
  .a11y-statement-body {{
    font-size: 13px;
    line-height: 1.7;
    color: var(--text-body);
    max-height: 60vh;
    overflow-y: auto;
  }}
  .a11y-statement-body p {{ margin: 0 0 10px 0; }}
  .a11y-statement-body p:last-child {{ margin-bottom: 0; }}
  .a11y-statement-body ul {{ margin: 0 0 10px 0; padding-right: 20px; }}

  .footer {{
    margin-top: 28px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
  }}
  .footer a {{
    color: var(--accent);
    text-decoration: none;
  }}
  .footer a:hover {{ text-decoration: underline; }}
  .footer-link-btn {{
    color: var(--accent);
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    cursor: pointer;
    text-decoration: none;
  }}
  .footer-link-btn:hover {{ text-decoration: underline; }}
  .beta-note {{
    margin-top: 8px;
    font-size: 11px;
    color: var(--text-muted);
  }}
  .beta-note a {{ color: var(--accent); text-decoration: underline; }}
</style>
</head>
<body>
  <div class="wrapper">
    <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" aria-label="החלף תצוגה בהירה/כהה">🌙</button>
    <button class="a11y-toggle" id="a11y-toggle" onclick="openA11yPanel()" aria-haspopup="dialog" aria-expanded="false" aria-label="פתח הגדרות נגישות">♿</button>
    <header class="header">
      <img class="logo-img logo-light" src="assets/logo_light.png" alt="Full Court">
      <img class="logo-img logo-dark" src="assets/logo_dark.png" alt="Full Court">
      <h1>סיכום הלילה ב-NBA</h1>
      <div class="date">{page_date_label}</div>
    </header>
    <main>
      <div class="summary">
        {summary_html}
      </div>

      <details>
        <summary>{results_title}</summary>
        <div class="details-body">
          {results_html}
        </div>
      </details>

      {secondary_section_html}
    </main>

    <footer class="footer">
      made by Ofek Barel · <button type="button" class="footer-link-btn" onclick="openContactOverlay()">יצירת קשר</button>
      <div class="beta-note">גרסת בטא · <a href="demos.html">מעבר בין דמואים</a></div>
    </footer>
  </div>

  <div class="a11y-overlay" id="contact-overlay" hidden onclick="if (event.target === this) closeContactOverlay()">
    <div class="a11y-panel" role="dialog" aria-modal="true" aria-labelledby="contact-title">
      <div class="a11y-panel-header">
        <h2 id="contact-title">יצירת קשר</h2>
        <button class="a11y-panel-close" onclick="closeContactOverlay()" aria-label="סגור יצירת קשר">✕</button>
      </div>
      <div class="a11y-statement-body" dir="rtl">
        <p>יש הערה, באג, או הצעה לשיפור? אשמח לשמוע.</p>
        <a class="a11y-link-btn" href="https://github.com/OJBAR/full-court/issues/new" target="_blank" rel="noopener">GitHub Issues</a>
        <div class="email-row">
          <a class="a11y-link-btn" href="https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=ojbar30@gmail.com&amp;su=%D7%A4%D7%A0%D7%99%D7%94+%D7%9C%D7%90%D7%AA%D7%A8+FULL+COURT-+(%D7%A0%D7%95%D7%A9%D7%90+%D7%94%D7%A4%D7%A0%D7%99%D7%94)&amp;body=%D7%AA%D7%95%D7%9B%D7%9F+%D7%94%D7%9E%D7%99%D7%99%D7%9C" target="_blank" rel="noopener">ojbar30@gmail.com</a>
          <button type="button" class="copy-email-btn" onclick="copyEmailAddress(this)" aria-label="העתק את כתובת המייל">📋</button>
        </div>
      </div>
    </div>
  </div>

  <div class="a11y-overlay" id="a11y-overlay" hidden onclick="if (event.target === this) closeA11yOverlays()">
    <div class="a11y-panel" role="dialog" aria-modal="true" aria-labelledby="a11y-panel-title">
      <div class="a11y-panel-header">
        <h2 id="a11y-panel-title">נגישות</h2>
        <button class="a11y-panel-close" onclick="closeA11yOverlays()" aria-label="סגור הגדרות נגישות">✕</button>
      </div>
      <div class="a11y-field">
        <span class="a11y-field-label" id="a11y-fontsize-label">גודל טקסט</span>
        <div class="a11y-fontsize-options" role="group" aria-labelledby="a11y-fontsize-label">
          <button type="button" class="a11y-fontsize-btn a11y-fontsize-sm" data-fontsize="normal" aria-pressed="true" aria-label="גודל טקסט רגיל" onclick="setFontSize('normal')">א</button>
          <button type="button" class="a11y-fontsize-btn a11y-fontsize-md" data-fontsize="large" aria-pressed="false" aria-label="גודל טקסט גדול" onclick="setFontSize('large')">א</button>
          <button type="button" class="a11y-fontsize-btn a11y-fontsize-lg" data-fontsize="xlarge" aria-pressed="false" aria-label="גודל טקסט גדול מאוד" onclick="setFontSize('xlarge')">א</button>
        </div>
      </div>
      <button type="button" class="a11y-link-btn" onclick="openA11yStatement()">הצהרת נגישות</button>
    </div>
  </div>

  <div class="a11y-overlay" id="a11y-statement-overlay" hidden onclick="if (event.target === this) closeA11yOverlays()">
    <div class="a11y-panel" role="dialog" aria-modal="true" aria-labelledby="a11y-statement-title">
      <div class="a11y-panel-header">
        <h2 id="a11y-statement-title">הצהרת נגישות</h2>
        <button class="a11y-panel-close" onclick="closeA11yOverlays()" aria-label="סגור הצהרת נגישות">✕</button>
      </div>
      <div class="a11y-statement-body" dir="rtl">
        <p>
          Full Court הוא ניוזלטר יומי שמסכם את ליל המשחקים ב-NBA. נעשה מאמץ להנגיש
          אותו לכלל הקוראים, כולל אנשים עם מוגבלות:
        </p>
        <ul>
          <li>מבנה סמנטי (landmarks) המאפשר ניווט נוח בעזרת קוראי מסך.</li>
          <li>אפשרות להגדלת גודל הטקסט בשלוש רמות, מהפאנל הזה.</li>
          <li>ניגודיות צבעים מותאמת במצב בהיר וכהה</li>
          <li>ניווט מקלדת מלא, כולל סימון מיקוד ברור ופאנלים הנסגרים ב-Escape.</li>
        </ul>
        <p>
          ההתאמות נעשו מתוך שאיפה לעמוד בהנחיות WCAG 2.1 ברמה AA. נתקלת בבעיית נגישות
          או יש לך הצעה לשיפור? אפשר לפנות אלינו (ראו פרטים בתחתית העמוד) ונשתדל לטפל
          בכך בהקדם.
        </p>
      </div>
    </div>
  </div>
  <script>
    (function() {{
      var saved = localStorage.getItem("nba-brief-theme");
      if (saved) {{
        document.documentElement.setAttribute("data-theme", saved);
      }}
      updateToggleIcon();
    }})();

    (function() {{
      var savedFontSize = localStorage.getItem("nba-brief-fontsize");
      if (savedFontSize) {{
        applyFontSize(savedFontSize);
      }}
    }})();

    var a11yLastFocused = null;
    var a11yActiveOverlayId = null;

    function switchA11yOverlay(overlayId) {{
      if (a11yActiveOverlayId) {{
        document.getElementById(a11yActiveOverlayId).hidden = true;
      }}
      document.getElementById(overlayId).hidden = false;
      a11yActiveOverlayId = overlayId;
      var focusTarget = document.querySelector("#" + overlayId + " .a11y-panel-close");
      if (focusTarget) {{ focusTarget.focus(); }}
    }}

    function openA11yPanel() {{
      a11yLastFocused = document.activeElement;
      document.getElementById("a11y-toggle").setAttribute("aria-expanded", "true");
      document.querySelector(".wrapper").setAttribute("aria-hidden", "true");
      switchA11yOverlay("a11y-overlay");
      document.addEventListener("keydown", a11yKeydownHandler);
    }}

    function openA11yStatement() {{
      switchA11yOverlay("a11y-statement-overlay");
    }}

    function closeA11yOverlays() {{
      if (a11yActiveOverlayId) {{
        document.getElementById(a11yActiveOverlayId).hidden = true;
        a11yActiveOverlayId = null;
      }}
      document.getElementById("a11y-toggle").setAttribute("aria-expanded", "false");
      document.querySelector(".wrapper").removeAttribute("aria-hidden");
      document.removeEventListener("keydown", a11yKeydownHandler);
      if (a11yLastFocused) {{ a11yLastFocused.focus(); }}
      a11yLastFocused = null;
    }}

    function a11yKeydownHandler(e) {{
      if (e.key === "Escape") {{
        closeA11yOverlays();
        return;
      }}
      if (e.key === "Tab" && a11yActiveOverlayId) {{
        var focusable = document.querySelectorAll("#" + a11yActiveOverlayId + " button");
        var first = focusable[0];
        var last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {{
          e.preventDefault();
          last.focus();
        }} else if (!e.shiftKey && document.activeElement === last) {{
          e.preventDefault();
          first.focus();
        }}
      }}
    }}

    function setFontSize(size) {{
      applyFontSize(size);
      localStorage.setItem("nba-brief-fontsize", size);
    }}

    function applyFontSize(size) {{
      if (size === "normal") {{
        document.documentElement.removeAttribute("data-a11y-fontsize");
      }} else {{
        document.documentElement.setAttribute("data-a11y-fontsize", size);
      }}
      var buttons = document.querySelectorAll(".a11y-fontsize-btn");
      buttons.forEach(function(btn) {{
        btn.setAttribute("aria-pressed", btn.getAttribute("data-fontsize") === size ? "true" : "false");
      }});
    }}

    function copyEmailAddress(btn) {{
      var original = btn.textContent;
      navigator.clipboard.writeText("ojbar30@gmail.com").then(function() {{
        btn.textContent = "✓";
        setTimeout(function() {{ btn.textContent = original; }}, 1500);
      }}).catch(function() {{}});
    }}

    var contactLastFocused = null;

    function openContactOverlay() {{
      contactLastFocused = document.activeElement;
      document.querySelector(".wrapper").setAttribute("aria-hidden", "true");
      document.getElementById("contact-overlay").hidden = false;
      document.querySelector("#contact-overlay .a11y-panel-close").focus();
      document.addEventListener("keydown", contactKeydownHandler);
    }}

    function closeContactOverlay() {{
      document.getElementById("contact-overlay").hidden = true;
      document.querySelector(".wrapper").removeAttribute("aria-hidden");
      document.removeEventListener("keydown", contactKeydownHandler);
      if (contactLastFocused) {{ contactLastFocused.focus(); }}
      contactLastFocused = null;
    }}

    function contactKeydownHandler(e) {{
      if (e.key === "Escape") {{
        closeContactOverlay();
        return;
      }}
      if (e.key === "Tab") {{
        var focusable = document.querySelectorAll("#contact-overlay button, #contact-overlay a");
        var first = focusable[0];
        var last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {{
          e.preventDefault();
          last.focus();
        }} else if (!e.shiftKey && document.activeElement === last) {{
          e.preventDefault();
          first.focus();
        }}
      }}
    }}

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

_MARKDOWN_HEADER_RE = re.compile(r"^#{1,6}\s*", re.MULTILINE)
_MARKDOWN_BOLD_ITALIC_RE = re.compile(r"(\*\*\*|\*\*|\*|__|_)")


def _strip_markdown(text: str) -> str:
    """
    Safety net: the model is instructed to never use Markdown, but it doesn't
    always comply. Strips headers/bold/italic markers before they hit HTML,
    so a stray '#' or '**' never shows up as a literal character on the page.
    """
    text = _MARKDOWN_HEADER_RE.sub("", text)
    text = _MARKDOWN_BOLD_ITALIC_RE.sub("", text)
    return text


def _paragraphs_to_html(summary: str) -> str:
    summary = _strip_markdown(summary)
    paragraphs = [p.strip() for p in summary.split("\n") if p.strip()]
    return "\n      ".join(f"<p>{html.escape(p)}</p>" for p in paragraphs)


def _build_results_html(games: list[dict], standings: list[dict]) -> str:
    if not games:
        return '<p style="color:var(--text-muted); font-size:14px;">אין משחקים ללילה הזה.</p>'

    standings_by_team_id = {s["TeamID"]: s for s in standings}
    rows = []
    for game in games:
        line_score = game["line_score"]
        if len(line_score) != 2:
            continue
        team_a, team_b = line_score
        a_wins = team_a["score"] > team_b["score"]
        is_play_in_game = game["game_id"].startswith("005")
        is_cup_knockout_game = game.get("cup_subtype") == "in-season-knockout"
        # Season record next to the team code - not during playoffs or Play-In,
        # where the series score / seed context (shown in the caption below) is
        # the relevant number instead, not the season record.
        show_record = not game.get("po_round") and not is_play_in_game

        def _team_span(team: dict, is_winner: bool) -> str:
            if show_record and is_cup_knockout_game:
                # Cup knockout games report "wins"/"losses" scoped to the
                # knockout stage itself (e.g. 1-0 for a Championship-game
                # team), not the real season record - look the real record up
                # from standings instead.
                standing = standings_by_team_id.get(team["teamId"])
                wins = standing["WINS"] if standing else None
                losses = standing["LOSSES"] if standing else None
            elif show_record:
                wins = team.get("wins")
                losses = team.get("losses")
            else:
                wins = losses = None
            record = (
                f'<span class="team-record">{wins}-{losses}</span>'
                if wins is not None and losses is not None
                else ""
            )
            return (
                f'<span class="team{" winner" if is_winner else ""}">'
                f'{html.escape(team["teamTricode"])}{record}</span>'
            )

        period = game.get("period", 4)
        ot_count = period - 4
        ot_html = (
            f'<span class="ot-tag">{"OT" if ot_count == 1 else f"{ot_count}OT"}</span>'
            if ot_count > 0
            else ""
        )
        block = (
            '<div class="game-row">'
            f'{_team_span(team_a, a_wins)}'
            f'<span class="score{" winner" if a_wins else ""}">{team_a["score"]}</span>'
            f'<span class="score">–</span>'
            f'<span class="score{"" if a_wins else " winner"}">{team_b["score"]}</span>'
            f'{_team_span(team_b, not a_wins)}'
            f'{ot_html}'
            "</div>"
        )
        if game.get("po_round"):
            game_number = html.escape(str(game.get("series_game_number", "")))
            series_text = html.escape(str(game.get("series_text", "")))
            block += f'<div class="game-sub">{game_number} · {series_text}</div>'
        elif game.get("cup_subtype"):
            cup_sub_label = html.escape(str(game.get("cup_sub_label", "")))
            block += f'<div class="game-sub">NBA Cup · {cup_sub_label}</div>'
        elif game["game_id"].startswith("005") and game.get("series_text"):
            block += f'<div class="game-sub">Play-In · {html.escape(str(game["series_text"]))}</div>'
        rows.append(f'<div class="game-block">{block}</div>')
    return "\n        ".join(rows)


def _build_standings_html(standings: list[dict]) -> str:
    if not standings:
        return '<p style="color:var(--text-muted); font-size:14px;">אין נתוני טבלה זמינים.</p>'

    conferences: dict[str, list[dict]] = {}
    for team in standings:
        conferences.setdefault(team["Conference"], []).append(team)

    names = {"East": "מזרח", "West": "מערב"}
    blocks = []
    for conf_key in ["West", "East"]:
        if conf_key not in conferences:
            continue
        teams = sorted(conferences[conf_key], key=lambda t: int(t["PlayoffRank"]))
        rows = []
        for team in teams:
            rank = int(team["PlayoffRank"])
            streak = str(team.get("strCurrentStreak", "")).strip()
            streak_class = "win" if streak.startswith("W") else "loss" if streak.startswith("L") else ""
            boundary_class = " boundary" if rank in (6, 10) else ""
            rows.append(
                f'<div class="standing-row{boundary_class}">'
                f'<span class="standing-rank">{rank}</span>'
                f'<span class="standing-team">{html.escape(team["TeamCity"])} {html.escape(team["TeamName"])}</span>'
                f'<span class="standing-record">{team["WINS"]}-{team["LOSSES"]}</span>'
                f'<span class="standing-streak {streak_class}">{html.escape(streak)}</span>'
                "</div>"
            )
        blocks.append(
            f'<div class="conference standings-block"><h3>{names.get(conf_key, conf_key)}</h3>'
            + "\n          ".join(rows)
            + "</div>"
        )
    return "\n      ".join(blocks)


def _pad_series(series_list: list[dict], count: int) -> list[dict | None]:
    padded = list(series_list[:count])
    while len(padded) < count:
        padded.append(None)
    return padded


def _bracket_series_html(series: dict | None) -> str:
    """One bracket cell for a playoff series: current W-L, or a TBD placeholder
    if the matchup isn't determined yet (a feeder series hasn't finished)."""
    if series is None:
        return (
            '<div class="bracket-match bracket-match-tbd">'
            '<div class="bracket-team"><span>TBD</span></div>'
            '<div class="bracket-team"><span>TBD</span></div>'
            "</div>"
        )
    teams = series["teams"]
    if len(teams) != 2:
        return _bracket_series_html(None)
    # Home-court advantage always belongs to the better (lower-numbered) seed
    # in a playoff series, regardless of who's currently leading in games -
    # display them on top for that reason, not by win count.
    ordered = sorted(teams, key=lambda t: t.get("seed") if t.get("seed") is not None else 99)
    max_wins = max(t["wins"] for t in teams)

    def _team(team: dict) -> str:
        is_winner = series["is_over"] and team["wins"] == max_wins
        cls = " winner" if is_winner else ""
        seed = team.get("seed")
        seed_html = f'<span class="bracket-seed">{seed}</span>' if seed else ""
        return (
            f'<div class="bracket-team{cls}">'
            f'<span class="bracket-team-label">{seed_html}<span>{html.escape(team["tricode"])}</span></span>'
            f'<span class="bracket-score">{team["wins"]}</span></div>'
        )

    return '<div class="bracket-match">' + "".join(_team(t) for t in ordered) + "</div>"


_ROUND1_BRACKET_HALF_BY_SEED = {1: "A", 8: "A", 4: "A", 5: "A", 2: "B", 7: "B", 3: "B", 6: "B"}


def _bracket_half_for_series(series: dict) -> str | None:
    """
    Which half of the conference bracket a series belongs to, from its
    teams' seeds - real NBA bracket structure (1v8 and 4v5 meet in the
    "top half"; 2v7 and 3v6 in the "bottom half"), not an arbitrary
    grouping, so the Conf. Semifinals column shows who's actually playing
    whom. A team's seed stays the same as it advances, so this works for
    Conf. Semifinals series too, not just 1st Round.
    """
    for team in series["teams"]:
        half = _ROUND1_BRACKET_HALF_BY_SEED.get(team.get("seed"))
        if half:
            return half
    return None


def _build_conference_bracket_html(playoff_series: list[dict], conference: str) -> str:
    """
    One conference's playoff bracket: 1st Round (4 series, in the 2 seed-based
    pairs described above) -> Conf. Semifinals (2 series, 1 pair) -> Conf.
    Finals (1 series). Same shape as the Cup bracket, so it reuses the same
    CSS and TBD-placeholder handling for anything not decided/started yet.
    """
    conf_series = [s for s in playoff_series if s.get("conference") == conference]
    round1 = [s for s in conf_series if s.get("round") == "1st Round"]
    semis = [s for s in conf_series if s.get("round") == "Conf. Semifinals"]
    finals = [s for s in conf_series if s.get("round") == "Conf. Finals"]

    round1_by_half: dict[str, list[dict]] = {"A": [], "B": []}
    for series in round1:
        half = _bracket_half_for_series(series)
        if half:
            round1_by_half[half].append(series)

    round1_pairs = [
        f'<div class="bracket-pair">'
        f'{"".join(_bracket_series_html(s) for s in _pad_series(round1_by_half[half], 2))}'
        "</div>"
        for half in ("A", "B")
    ]

    semis_by_half: dict[str, dict] = {}
    for series in semis:
        half = _bracket_half_for_series(series)
        if half:
            semis_by_half[half] = series
    semis_slots = [semis_by_half.get("A"), semis_by_half.get("B")]
    semis_pair = f'<div class="bracket-pair">{"".join(_bracket_series_html(s) for s in semis_slots)}</div>'

    final_column = _bracket_series_html(finals[0] if finals else None)

    columns = [
        _bracket_column_html("1st Round", f'<div class="bracket-round">{"".join(round1_pairs)}</div>'),
        _bracket_column_html("Conf. Semifinals", f'<div class="bracket-round">{semis_pair}</div>'),
        _bracket_column_html("Conf. Finals", f'<div class="bracket-round bracket-final">{final_column}</div>'),
    ]
    return f'<div class="bracket">{"".join(columns)}</div>'


def _finals_match_html(series: dict | None, conf_by_team: dict) -> str:
    """
    Finals-specific version of _bracket_series_html: shows a colored W/E
    conference badge instead of a seed number, since the two teams' seeds
    (1-8 independently within each conference) aren't a meaningful basis for
    comparison across conferences the way they are within a single bracket -
    knowing which conference each team is from is the more useful signal here.
    """
    if series is None:
        return (
            '<div class="bracket-match bracket-match-tbd">'
            '<div class="bracket-team"><span>TBD</span></div>'
            '<div class="bracket-team"><span>TBD</span></div>'
            "</div>"
        )
    teams = series["teams"]
    if len(teams) != 2:
        return _finals_match_html(None, conf_by_team)
    max_wins = max(t["wins"] for t in teams)

    def _team(team: dict) -> str:
        cls = " winner" if series["is_over"] and team["wins"] == max_wins else ""
        conf = conf_by_team.get(team["team_id"])
        badge_html = (
            f'<span class="conf-badge conf-badge-{conf.lower()}">{conf[0]}</span>' if conf else ""
        )
        return (
            f'<div class="bracket-team{cls}">'
            f'<span class="bracket-team-label">{badge_html}<span>{html.escape(team["tricode"])}</span></span>'
            f'<span class="bracket-score">{team["wins"]}</span></div>'
        )

    return '<div class="bracket-match">' + "".join(_team(t) for t in teams) + "</div>"


def _build_finals_html(playoff_series: list[dict]) -> str:
    """
    The NBA Finals series (East champion vs West champion) - unlike the two
    conference brackets, this has no "conference" of its own in the data
    (seriesConference is blank for Finals games), so it's pulled out by round
    name instead and shown as a single standalone match card. Each Finals
    team's conference (for the W/E badge) is looked up from whichever other
    series it appeared in earlier in the same bracket data - the Finals
    series itself doesn't carry that field.
    """
    finals = [s for s in playoff_series if s.get("round") == "NBA Finals"]
    series = finals[0] if finals else None
    conf_by_team = {
        t["team_id"]: s.get("conference")
        for s in playoff_series
        if s.get("round") != "NBA Finals"
        for t in s["teams"]
    }
    result = f'<div class="bracket"><div class="bracket-column">{_finals_match_html(series, conf_by_team)}</div></div>'
    if series and series["is_over"]:
        champion = series["teams"][0]
        result += f'<p class="game-sub" dir="rtl">{html.escape(champion["tricode"])} אלופת ה-NBA!</p>'
    return result


def _play_in_bracket_match_html(game: dict | None, caption: str) -> str:
    """
    One Play-In game as a bracket cell (reuses .bracket-match, same as the
    playoff/Cup brackets), with a caption below explaining what the result
    means - necessary because Play-In isn't a clean single-elimination shape
    like the rest of the bracket UI: the 7-vs-8 game's WINNER is done (locked
    into the 7 seed, plays no further Play-In games) while its LOSER is the
    one who continues into the decider - the opposite of a normal bracket
    advancement, so it needs to be spelled out rather than left to the shape
    of the lines to imply.
    """
    if game is None:
        match_html = (
            '<div class="bracket-match bracket-match-tbd">'
            '<div class="bracket-team"><span>TBD</span></div>'
            '<div class="bracket-team"><span>TBD</span></div>'
            "</div>"
        )
    else:
        line_score = game["line_score"]
        # Lower seed on top, same convention as the playoff conference brackets.
        ordered = sorted(line_score, key=lambda t: t.get("seed") if t.get("seed") is not None else 99)
        max_score = max(t["score"] for t in line_score)

        def _team(team: dict) -> str:
            cls = " winner" if team["score"] == max_score else ""
            seed = team.get("seed")
            seed_html = f'<span class="bracket-seed">{seed}</span>' if seed else ""
            return (
                f'<div class="bracket-team{cls}">'
                f'<span class="bracket-team-label">{seed_html}<span>{html.escape(team["teamTricode"])}</span></span>'
                f'<span class="bracket-score">{team["score"]}</span></div>'
            )

        match_html = '<div class="bracket-match">' + "".join(_team(t) for t in ordered) + "</div>"
    return (
        '<div class="bracket-match-wrap">'
        f"{match_html}"
        f'<div class="bracket-caption">{html.escape(caption)}</div>'
        "</div>"
    )


def _build_play_in_conference_bracket_html(conf_games: list[dict]) -> str:
    """
    One conference's Play-In bracket: 7-vs-8 and 9-vs-10 side by side (round
    1), feeding into a single decider game for the conference's final 8 seed
    (round 2) - visually a bracket, even though the real advancement logic
    is asymmetric (see _play_in_bracket_match_html) rather than "both
    winners meet", unlike every other bracket in this app.
    """
    seven_eight = nine_ten = decider = None
    for game in conf_games:
        seeds = {t.get("seed") for t in game["line_score"]}
        if seeds == {7, 8}:
            seven_eight = game
        elif seeds == {9, 10}:
            nine_ten = game
        else:
            decider = game

    round1_pair = (
        '<div class="bracket-pair">'
        f'{_play_in_bracket_match_html(seven_eight, "המנצחת עולה לפלייאוף מהמקום ה-7")}'
        f'{_play_in_bracket_match_html(nine_ten, "המפסידה מודחת")}'
        "</div>"
    )
    decider_cell = _play_in_bracket_match_html(decider, "המנצחת עולה לפלייאוף מהמקום ה-8")

    columns = [
        f'<div class="bracket-column"><div class="bracket-round">{round1_pair}</div></div>',
        f'<div class="bracket-column"><div class="bracket-round bracket-final">{decider_cell}</div></div>',
    ]
    return f'<div class="bracket">{"".join(columns)}</div>'


def _build_play_in_html(games: list[dict], conference: str) -> str:
    """
    Play-In bracket for one conference (its own tab - "פלייאין מזרח"/"פלייאין
    מערב" - same as the two playoff conference-bracket tabs). The 3 games are
    identified by their teams' seeds, not by date - the two conferences don't
    always play their games on the same nights, so date order alone doesn't
    tell you which game is which. {7,8} is the opener, {9,10} is the loser-out
    game, and the mismatched pair (e.g. {7,9} or {8,10}) is the decider for
    the conference's final 8 seed.
    """
    conf_games = [
        g
        for g in games
        if g["game_id"].startswith("005") and g.get("series_conference") == conference
    ]
    return _build_play_in_conference_bracket_html(conf_games)


def _bracket_column_html(label: str, round_html: str) -> str:
    return f'<div class="bracket-column"><h4 class="bracket-round-label">{html.escape(label)}</h4>{round_html}</div>'


def _cup_conference_from_round(round_name: str) -> str:
    for conf in ("West", "East"):
        if round_name.startswith(conf):
            return conf
    return ""


def _bracket_team_name_html(team: dict) -> str:
    return f'<span class="bracket-team-name">{html.escape(team["tricode"])}</span>'


def _bracket_match_html(game: dict | None) -> str:
    """One bracket cell for a Cup knockout game, or a TBD placeholder if that
    matchup isn't decided yet (a feeder game hasn't been played)."""
    if game is None:
        return (
            '<div class="bracket-match bracket-match-tbd">'
            '<div class="bracket-team"><span>TBD</span></div>'
            '<div class="bracket-team"><span>TBD</span></div>'
            "</div>"
        )
    winner, loser = game["winner"], game["loser"]
    return (
        '<div class="bracket-match">'
        f'<div class="bracket-team winner">{_bracket_team_name_html(winner)}'
        f'<span class="bracket-score">{winner["score"]}</span></div>'
        f'<div class="bracket-team">{_bracket_team_name_html(loser)}'
        f'<span class="bracket-score">{loser["score"]}</span></div>'
        "</div>"
    )
def _bracket_projected_match_html(teams: list[dict]) -> str:
    """Both participants of a not-yet-played match are already known (e.g.
    both Quarterfinal winners in a pair) - show the matchup without a score."""
    return (
        '<div class="bracket-match bracket-match-projected">'
        + "".join(
            f'<div class="bracket-team">{_bracket_team_name_html(team)}</div>'
            for team in teams
        )
        + "</div>"
    )

def _build_cup_bracket_html(cup_bracket: list[dict]) -> str:
    """
    Renders the Cup knockout bracket as a connected tree (QF -> SF ->
    Championship) - only 7 games total, so this fits. Always shows the full
    shape (4 QF / 2 SF / 1 Final slots) even early in the knockout stage.
    Anything not played yet is either a TBD placeholder (participants still
    unknown) or a "projected" matchup (both participants known - e.g. both
    Quarterfinal winners in a pair - but that game hasn't been played yet).
    """
    quarterfinals = [g for g in cup_bracket if "Quarterfinal" in g.get("round", "")]
    semifinals = [g for g in cup_bracket if "Semifinal" in g.get("round", "")]
    final = [g for g in cup_bracket if "Championship" in g.get("round", "")]

    qf_by_conf: dict[str, list[dict]] = {}
    for game in quarterfinals:
        qf_by_conf.setdefault(_cup_conference_from_round(game["round"]), []).append(game)
    sf_by_conf: dict[str, list[dict]] = {}
    for game in semifinals:
        sf_by_conf.setdefault(_cup_conference_from_round(game["round"]), []).append(game)

    qf_pairs = []
    projected_sf_by_conf: dict[str, list[dict]] = {}
    for conf in ("West", "East"):
        conf_qf_games = qf_by_conf.get(conf, [])
        qf_pairs.append(
            f'<div class="bracket-pair">'
            f'{"".join(_bracket_match_html(g) for g in _pad_series(conf_qf_games, 2))}'
            "</div>"
        )
        if len(conf_qf_games) == 2:
            projected_sf_by_conf[conf] = [g["winner"] for g in conf_qf_games]

    sf_matches_html = []
    known_sf_winner_by_conf: dict[str, dict | None] = {}
    for conf in ("West", "East"):
        real_sf_games = sf_by_conf.get(conf, [])
        if real_sf_games:
            game = real_sf_games[0]
            sf_matches_html.append(_bracket_match_html(game))
            known_sf_winner_by_conf[conf] = game["winner"]
        elif conf in projected_sf_by_conf:
            sf_matches_html.append(_bracket_projected_match_html(projected_sf_by_conf[conf]))
        else:
            sf_matches_html.append(_bracket_match_html(None))
    sf_pair = f'<div class="bracket-pair">{"".join(sf_matches_html)}</div>'

    if final:
        final_column = _bracket_match_html(final[0])
    else:
        final_teams = [known_sf_winner_by_conf.get(conf) for conf in ("West", "East")]
        if all(final_teams):
            final_column = _bracket_projected_match_html(final_teams)
        else:
            final_column = _bracket_match_html(None)

    columns = [
        _bracket_column_html("Quarterfinals", f'<div class="bracket-round">{"".join(qf_pairs)}</div>'),
        _bracket_column_html("Semifinals", f'<div class="bracket-round">{sf_pair}</div>'),
        _bracket_column_html("Championship", f'<div class="bracket-round bracket-final">{final_column}</div>'),
    ]
    return f'<div class="bracket">{"".join(columns)}</div>'


def _build_cup_group_standings_html(cup_group_standings: list[dict]) -> str:
    """
    Cup group-stage standings: win-loss and point differential within group
    play only (not the season record), grouped as Group A/B/C per conference,
    with a boundary line between 1st and 2nd place (only 1st advances directly).
    Also marks the "Wild Card" - the best-record runner-up across a conference's
    3 groups, since that team advances to the knockout too, alongside the
    3 group winners.
    """
    if not cup_group_standings:
        return '<p style="color:var(--text-muted); font-size:14px;">אין נתוני בתים זמינים.</p>'

    conferences: dict[str, dict[str, list[dict]]] = {}
    for team in cup_group_standings:
        group_label = team.get("group", "")
        conf = "West" if group_label.startswith("West") else "East" if group_label.startswith("East") else ""
        conferences.setdefault(conf, {}).setdefault(group_label, []).append(team)

    names = {"East": "מזרח", "West": "מערב"}
    conf_blocks = []
    found_wildcard = False
    for conf_key in ["West", "East"]:
        if conf_key not in conferences:
            continue

        ranked_groups: dict[str, list[dict]] = {}
        runners_up = []
        for group_label, teams in conferences[conf_key].items():
            ranked = sorted(teams, key=lambda t: (-t["wins"], -t["point_diff"]))
            ranked_groups[group_label] = ranked
            if len(ranked) >= 2:
                runners_up.append(ranked[1])

        wildcard_tricode = None
        if runners_up:
            wildcard_tricode = max(runners_up, key=lambda t: (t["wins"], t["point_diff"]))["tricode"]
            found_wildcard = True

        group_blocks = []
        for group_label in sorted(ranked_groups):
            rows = []
            for rank, team in enumerate(ranked_groups[group_label], start=1):
                boundary_class = " boundary" if rank == 1 else ""
                diff = team["point_diff"]
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                badge = (
                    ' <span class="wildcard-badge">WC</span>'
                    if team["tricode"] == wildcard_tricode
                    else ""
                )
                rows.append(
                    f'<div class="standing-row{boundary_class}">'
                    f'<span class="standing-team">{html.escape(team["name"])}{badge}</span>'
                    f'<span class="standing-record">{team["wins"]}-{team["losses"]}</span>'
                    f'<span class="standing-diff">{diff_str}</span>'
                    "</div>"
                )
            group_name = group_label.split()[-1] if group_label else ""
            group_blocks.append(
                f'<div class="cup-group"><h4>Group {html.escape(group_name)}</h4>'
                + "\n            ".join(rows)
                + "</div>"
            )
        conf_blocks.append(
            f'<div class="conference standings-block"><h3>{names.get(conf_key, conf_key)}</h3>'
            + "\n          ".join(group_blocks)
            + "</div>"
        )

    result = "\n      ".join(conf_blocks)
    if found_wildcard:
        result += (
            '\n      <p class="wildcard-legend" dir="rtl">'
            "WC - הסגנית הכי טובה בכל אזור, עולה לשלב הנוקאאוט</p>"
        )
    return result


def _details_block(title: str, inner_html: str) -> str:
    return (
        "<details>\n"
        f"      <summary>{title}</summary>\n"
        '      <div class="details-body" dir="ltr">\n'
        f"        {inner_html}\n"
        "      </div>\n"
        "    </details>"
    )


def _build_secondary_section(data: dict) -> str:
    """
    Playoffs: two tabs, one connected bracket per conference (1st Round ->
    Conf. Semifinals -> Conf. Finals) - there's no regular-season standings
    concept during playoffs. NBA Cup days (group stage or knockout): the
    regular league standings always show first, since every Cup game except
    the Championship counts toward the regular season - plus a group-standings
    tab on group-stage days and a connected bracket tab on knockout days.
    Otherwise: standings only.
    """
    if data.get("is_playoffs"):
        playoff_series = data.get("playoff_series", [])
        sections = []
        if any(s.get("round") == "NBA Finals" for s in playoff_series):
            sections.append(("גמר ה-NBA", _build_finals_html(playoff_series)))
        sections.append(("בראקט מערב", _build_conference_bracket_html(playoff_series, "West")))
        sections.append(("בראקט מזרח", _build_conference_bracket_html(playoff_series, "East")))
    else:
        standings_section = (
            "טבלת הליגה",
            f'<div class="conferences">{_build_standings_html(data["standings"])}</div>',
        )
        sections = []
        if data.get("is_cup_groups"):
            sections.append(
                (
                    "בתי הגביע",
                    f'<div class="conferences">{_build_cup_group_standings_html(data.get("cup_group_standings", []))}</div>',
                )
            )
        if data.get("is_cup_knockout"):
            sections.append(("בראקט הגביע", _build_cup_bracket_html(data.get("cup_bracket", []))))
        if data.get("is_play_in"):
            games = data.get("play_in_bracket", [])
            sections.append(("פלייאין מערב", _build_play_in_html(games, "West")))
            sections.append(("פלייאין מזרח", _build_play_in_html(games, "East")))
        sections.append(standings_section)

    return "\n\n    ".join(_details_block(title, body_html) for title, body_html in sections)


def render(data: dict, summary: str) -> str:
    """Renders the daily brief as a self-contained, mobile-first HTML page (RTL, Hebrew)."""
    date_str = data["date"]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = date_obj.strftime("%d/%m/%Y")
    next_day = date_obj + timedelta(days=1)
    night_label = f"הלילה בין {_HEBREW_WEEKDAYS[date_obj.weekday()]} ל{_HEBREW_WEEKDAYS[next_day.weekday()]}"
    results_title = "תוצאת המשחק" if len(data["games"]) == 1 else "כל תוצאות הלילה"
    return TEMPLATE.format(
        display_date=display_date,
        page_date_label=f"{display_date}, {night_label}",
        summary_html=_paragraphs_to_html(summary),
        results_title=results_title,
        results_html=_build_results_html(data["games"], data["standings"]),
        secondary_section_html=_build_secondary_section(data),
    )


def save(data: dict, summary: str) -> Path:
    """
    Renders and writes the brief to output/YYYY-MM-DD.html, and also copies it
    to output/index.html - a stable URL that always shows the latest brief,
    which is what the PWA (manifest.json's start_url) and any bookmark/home
    screen icon actually point to, instead of a new address every day.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    html = render(data, summary)
    output_path = OUTPUT_DIR / f"{data['date']}.html"
    output_path.write_text(html, encoding="utf-8")
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    from fetch import fetch_for_date
    from storylines import find_storylines
    from summarize import summarize

    data = fetch_for_date("2025-12-25")
    detected_storylines = find_storylines(data)
    summary_text = summarize(data, detected_storylines)
    output_path = save(data, summary_text)
    print(f"Saved to {output_path}")
