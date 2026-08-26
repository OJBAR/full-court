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
  :root[data-a11y-fontsize="large"] {{ --a11y-text-scale: 1.15; }}
  :root[data-a11y-fontsize="xlarge"] {{ --a11y-text-scale: 1.3; }}
  /* The accessibility font-size control scales root font-size (so only
     properties declared in rem below actually grow) instead of the old
     `zoom` on .wrapper, which scaled the entire layout - padding, borders,
     icons, everything - proportionally along with the text, and looked
     broken rather than just "bigger text". Fixed-size UI chrome (circular
     icon buttons, badges/pills, the bracket diagram - see its own comment
     below) stays in px on purpose so it doesn't distort at large sizes. */
  html {{ font-size: calc(16px * var(--a11y-text-scale, 1)); }}
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
  }}
  .settings-toggle {{
    position: absolute;
    top: 24px;
    right: 16px;
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
    font-size: 0.875rem;
    font-weight: 400;
    margin: 8px 0 0;
    color: var(--text-muted);
  }}
  .header .date {{
    color: var(--text-muted);
    font-size: 0.8125rem;
    margin-top: 6px;
  }}
  .summary {{
    font-size: 1rem;
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
    font-size: 0.9375rem;
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
    font-size: 0.875rem;
    position: relative;
  }}
  .team {{ width: 4.5em; color: var(--text-muted); text-align: center; }}
  .team.winner {{ color: var(--text-heading); font-weight: 700; }}
  .team-record {{
    display: block;
    font-size: 0.5625rem;
    font-weight: 400;
    color: var(--text-muted);
  }}
  .score {{ width: 2.2em; text-align: center; color: var(--text-muted); font-variant-numeric: tabular-nums; }}
  .score.winner {{ color: var(--accent); font-weight: 700; }}
  .ot-tag {{
    /* Absolutely positioned off to the side, out of the flex flow, so it
       never shifts the row's true center - .game-row centers just the
       teams/score, same with or without overtime. */
    position: absolute;
    top: 50%;
    left: 2px;
    transform: translateY(-50%);
    padding: 1px 5px;
    border-radius: 999px;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 9px;
    font-weight: 700;
  }}
  .game-sub {{
    text-align: center;
    font-size: 0.6875rem;
    color: var(--text-muted);
    margin-top: 6px;
  }}

  .conference h3 {{
    font-size: 0.8125rem;
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
    padding: 8px 0;
    font-size: 0.9375rem;
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
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.875rem;
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
    font-size: 0.6875rem;
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
    font-size: 0.6875rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 4px 0;
  }}

  /* Every font-size inside the bracket diagram (this section down through
     .bracket-conf-label/.pager-arrow) deliberately stays in px, not
     rem - the connector-line geometry between rounds is pixel-exact math
     tied to .bracket-match's real rendered height (see .bracket-pair-r2 and
     .bracket-pair-captioned below), and letting the text grow with the
     accessibility font-size setting would silently throw that math off
     again, the same bug that took real effort to track down and fix
     earlier. */
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
    gap: 12px;
  }}
  .bracket-final {{ justify-content: center; }}
  .bracket-pair {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 10px;
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
  /* A round-2 pair (Conf. Semifinals / Cup Semifinals) needs a bigger internal
     gap than a round-1 pair. Its two matches individually need to line up
     with the vertical centers of the two round-1 PAIRS feeding them, not just
     be evenly spaced within the column - round-1 pairs are already spread out
     by a match's height (56px) + round-1's own internal gap (10px) + the gap
     between pairs in a round (12px) = 78px between their centers, so the
     round-2 pair's own internal gap has to match that same 78px, not the
     plain 10px used one round earlier. Without this, a round-2 match's own
     center silently drifts away from the round-1 connector aimed at it (this
     is exactly why the connector looked disconnected - not a color/width
     issue, the target coordinate itself was off by ~38px in one demo).
     Coupled to bracket-match's real rendered height (56px) and the two gaps
     above - update this if any of those three ever change. */
  .bracket-pair-r2 {{ gap: 78px; }}
  /* Play-In's pair is the only one where each match has its own caption
     underneath it (see .bracket-caption) - that extra content below each
     match throws off the plain 50%-based connector (which naturally landed
     on the pair's overall midpoint, i.e. roughly between the two captions,
     not between the two actual score boxes). Here the connector is
     positioned with fixed pixels instead, tied to bracket-match's real
     height (56px, so a match's own center is 28px from its wrap's top) and
     bracket-match-wrap's real height (86px = 56 match + 4 caption margin +
     26 caption min-height) + this pair's own gap = 102px between the two
     matches' centers. Explicitly frozen at the original 16px gap (instead
     of inheriting .bracket-pair's, which is now smaller) so tightening the
     playoff/Cup bracket's spacing doesn't silently throw off this fixed-
     pixel math too. */
  .bracket-pair-captioned {{ border-right: none; gap: 16px; }}
  .bracket-pair-captioned::before {{
    content: "";
    position: absolute;
    top: 28px;
    right: 0;
    width: 2px;
    height: 102px;
    background: var(--text-muted);
  }}
  .bracket-pair-captioned::after {{ top: 79px; }}
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

  .bracket-conf-block {{ margin-bottom: 18px; }}
  .bracket-conf-block:last-child {{ margin-bottom: 0; }}
  .bracket-conf-label {{
    font-size: 11px;
    font-weight: 700;
    color: var(--text-muted);
    text-align: center;
    direction: rtl;
    margin: 0 0 6px;
  }}
  .pager-viewport {{ overflow: hidden; touch-action: pan-y; }}
  .pager-track {{
    display: flex;
    transition: transform 0.3s ease;
  }}
  .pager-page {{ flex: 0 0 100%; min-width: 0; }}
  .pager-nav {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-top: 4px;
  }}
  .pager-arrow {{
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text-heading);
    font-size: 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .pager-arrow:disabled {{ opacity: 0.35; cursor: default; }}

  /* The playoff bracket's own pager (see initPlayoffBracketPager()) - a
     continuous per-conference strip panned by a JS-measured column width
     instead of the generic page-based .pager above, so the round shared
     between two adjacent stops never appears as two separate copies. */
  .strip-viewport {{ overflow: hidden; touch-action: pan-y; }}
  .strip-track {{
    display: flex;
    justify-content: flex-start;
    gap: 24px;
    padding: 4px 4px 12px;
    transition: transform 0.35s ease;
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
    font-size: 1rem;
    color: var(--text-heading);
    margin: 0;
  }}
  .a11y-panel-close,
  .a11y-panel-back {{
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
  .a11y-panel-back {{ font-size: 18px; }}
  .a11y-field-label {{
    display: block;
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin-bottom: 8px;
  }}
  .settings-theme-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    font-size: 0.8125rem;
    color: var(--text-body);
  }}
  .settings-theme-btn {{
    width: 36px;
    height: 36px;
    flex-shrink: 0;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text-heading);
    font-size: 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .settings-about-text {{
    font-size: 0.8125rem;
    color: var(--text-body);
    margin: 0 0 4px;
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
    font-size: 0.8125rem;
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
    font-size: 0.8125rem;
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
    font-size: 0.75rem;
  }}
  .footer a {{
    color: var(--accent);
    text-decoration: none;
  }}
  .beta-note {{
    margin-top: 8px;
    font-size: 0.6875rem;
    color: var(--text-muted);
  }}
  .beta-note a {{ color: var(--accent); text-decoration: none; }}

  /* App-like extras: only active when installed to the home screen
     (display-mode: standalone) - a normal browser tab never sees any of
     this, on phone or desktop. */
  .splash-screen {{
    position: fixed;
    inset: 0;
    background: var(--bg);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 200;
    transition: opacity 0.3s ease;
  }}
  .splash-screen.visible {{ display: flex; }}
  .splash-screen.fade-out {{ opacity: 0; }}
  .splash-screen .logo-img {{ height: 84px; }}

  /* App home (standalone + narrow viewport, see initAppHome()). Only the
     main summary text is a separate "screen" (behind the big button + back
     button) - every other section (results/standings/brackets/etc.) stays
     a normal accordion, inline on the home screen itself, just enforced to
     only one open at a time (see the "toggle" listener in the JS). */
  /* Removes the iOS rubber-band bounce that happens even when there's
     nothing to actually scroll (a big part of what makes a PWA feel like a
     browser tab instead of an app) - real scrolling still works fine when a
     screen's content is genuinely taller than the viewport, this only kills
     the overshoot-past-the-edge effect. */
  :root.tabs-mode html,
  :root.tabs-mode body {{ overscroll-behavior: none; }}
  /* No text selection in app mode - long-press highlighting a word/score
     reads as a website, not an app. Buttons/links stay clickable either
     way, this only blocks selecting/highlighting text. */
  :root.tabs-mode * {{
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
  }}
  /* The page shell itself is pinned to exactly one screen's height and
     never scrolls - only the active screen's own content area (inside
     <main>) scrolls, and only when it's genuinely taller than the
     available space. This is also why the footer (contact/beta links)
     is hidden here - there's no page-level scroll left to reach it by. */
  :root.tabs-mode html,
  :root.tabs-mode body {{
    height: 100%;
    overflow: hidden;
  }}
  :root.tabs-mode .wrapper {{
    height: 100dvh;
    padding-bottom: env(safe-area-inset-bottom);
    display: flex;
    flex-direction: column;
  }}
  /* Compact app-mode header: logo moves to the top-left (row-reverse puts
     the first-markup child, the logo, at the ltr "end" which is the left
     edge under RTL), with the title/date beside it instead of stacked
     centered below - frees up real vertical room for the summary screen,
     which otherwise easily needs its own scroll on a long night. The
     splash screen's closing animation lands wherever .header .logo-img
     actually is (computed live, see animateSplashAway()), so it follows
     the logo here automatically. */
  :root.tabs-mode .header {{
    flex-shrink: 0;
    cursor: pointer;
    display: flex;
    flex-direction: row-reverse;
    align-items: center;
    gap: 10px;
    text-align: right;
    padding-bottom: 6px;
    margin-bottom: 6px;
  }}
  :root.tabs-mode .header .logo-img {{ height: 22px; margin: 0; }}
  /* The settings button is absolutely positioned against .wrapper, not
     .header, so shrinking the header left it too tall/low - it spilled
     past the header's bottom border instead of sitting inside it. Shrink
     and raise it to match the new compact header height. */
  :root.tabs-mode .settings-toggle {{
    width: 28px;
    height: 28px;
    top: 20px;
  }}
  /* Title and date both move out of the header entirely in app mode - just
     the logo remains, as compact as possible - the date reappears at the
     top of the summary screen instead (see .summary-date below). */
  :root.tabs-mode .header h1,
  :root.tabs-mode .header .date {{ display: none; }}
  .summary-date {{ display: none; }}
  :root.tabs-mode .summary-date {{
    display: block;
    color: var(--text-muted);
    font-size: 0.8125rem;
    margin-bottom: 10px;
  }}
  :root.tabs-mode main {{
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    display: flex;
    flex-direction: column;
  }}
  :root.tabs-mode .footer {{ display: none; }}
  :root.tabs-mode main > .summary {{
    display: none;
  }}
  :root.tabs-mode main > .summary.app-screen-active {{
    display: flex;
    flex-direction: column;
    flex: 1;
  }}
  /* A tab (results/standings/bracket/etc.) opened from the app home screen
     becomes its own full screen too, same as the summary - promoted to a
     direct child of <main> (see showSection() in initAppHome()), stripped
     of its little-card look, and its +/- toggle icon becomes a back
     arrow instead (clicking it returns home rather than collapsing it
     in place). */
  :root.tabs-mode main > details.tab-section.app-screen-active {{
    display: flex;
    flex-direction: column;
    flex: 1;
    margin-top: 0;
    border: none;
    border-radius: 0;
    background: transparent;
  }}
  :root.tabs-mode details.tab-section.app-screen-active > summary::after {{ content: "‹"; }}
  .app-home {{ display: none; }}
  :root.tabs-mode .app-home {{
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
  }}
  :root.tabs-mode .app-home.hidden {{ display: none; }}
  .app-home-big-btn {{
    display: block;
    width: 100%;
    flex-shrink: 0;
    padding: 40px 16px;
    margin: 4px 0 16px;
    border-radius: 16px;
    border: none;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 1.25rem;
    font-weight: 700;
    cursor: pointer;
  }}
  :root.tabs-mode .app-home details.tab-section {{ flex-shrink: 0; }}
  :root.tabs-mode .app-home details.tab-section:last-child {{ margin-bottom: 4px; }}
  :root.tabs-mode .app-home summary {{ padding: 22px 16px; font-size: 1.0625rem; }}
  .pull-refresh-indicator {{
    position: fixed;
    top: 16px;
    left: 50%;
    width: 36px;
    height: 36px;
    border-radius: 999px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    transform: translateX(-50%) translateY(0);
    opacity: 0;
    z-index: 150;
    pointer-events: none;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }}
  .pull-refresh-indicator svg {{ width: 18px; height: 18px; }}

  .install-banner {{
    display: none;
    flex-direction: column;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--card-bg);
    border-top: 1px solid var(--border);
    padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
    z-index: 150;
    gap: 8px;
  }}
  .install-banner.visible {{ display: flex; }}
  .install-banner-row {{ display: flex; align-items: center; gap: 10px; }}
  .install-banner-row img {{ width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0; }}
  .install-banner-text {{ flex: 1; min-width: 0; font-size: 0.75rem; color: var(--text-body); }}
  .install-banner-text strong {{ display: block; font-size: 0.8125rem; color: var(--text-heading); margin-bottom: 2px; }}
  .install-banner-action {{
    flex-shrink: 0;
    padding: 8px 14px;
    border-radius: 8px;
    border: none;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
  }}
  .install-banner-close {{
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    border: none;
    background: none;
    color: var(--text-muted);
    font-size: 16px;
    cursor: pointer;
  }}
  .install-banner-hint {{ font-size: 0.75rem; color: var(--text-muted); text-align: center; }}
  .install-banner-hint a {{ color: var(--accent); font-weight: 700; }}

  @media (prefers-reduced-motion: no-preference) {{
    .wrapper {{ animation: fc-fade-in 0.3s ease; }}
    @keyframes fc-fade-in {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    button:active, .app-home-big-btn:active, summary:active {{ transform: scale(0.96); }}
    button, .app-home-big-btn {{ transition: transform 0.1s ease; }}
  }}
</style>
</head>
<body>
  <div id="splash-screen" class="splash-screen">
    <img class="logo-img logo-light" src="assets/logo_light.png" alt="Full Court">
    <img class="logo-img logo-dark" src="assets/logo_dark.png" alt="Full Court">
  </div>
  <script>
    (function() {{
      var standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
      if (standalone) {{
        document.getElementById("splash-screen").classList.add("visible");
      }}
    }})();
  </script>
  <div class="wrapper">
    <button class="settings-toggle" id="settings-toggle" onclick="openSettingsPanel()" aria-haspopup="dialog" aria-expanded="false" aria-label="פתח הגדרות">⚙️</button>
    <header class="header">
      <img class="logo-img logo-light" src="assets/logo_light.png" alt="Full Court">
      <img class="logo-img logo-dark" src="assets/logo_dark.png" alt="Full Court">
      <div class="header-text">
        <h1>סיכום הלילה ב-NBA</h1>
        <div class="date">{page_date_label}</div>
      </div>
    </header>
    <main>
      <div class="summary">
        <div class="summary-date">{page_date_label}</div>
        {summary_html}
      </div>

      <details class="tab-section">
        <summary>{results_title}</summary>
        <div class="details-body">
          {results_html}
        </div>
      </details>

      {secondary_section_html}
    </main>

    <footer class="footer">
      made by Ofek Barel
    </footer>
  </div>

  <div class="a11y-overlay" id="settings-overlay" hidden onclick="if (event.target === this) closeSettingsOverlays()">
    <div class="a11y-panel" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <div class="a11y-panel-header">
        <h2 id="settings-title">הגדרות</h2>
        <button class="a11y-panel-close" onclick="closeSettingsOverlays()" aria-label="סגור הגדרות">✕</button>
      </div>

      <details class="settings-about">
        <summary>התאמות אישיות</summary>
        <div class="details-body">
          <div class="settings-theme-row">
            <span>מצב תצוגה</span>
            <button type="button" class="settings-theme-btn" id="settings-theme-btn" onclick="toggleTheme()" aria-label="החלף תצוגה בהירה/כהה">🌙</button>
          </div>
          <div class="a11y-field">
            <span class="a11y-field-label" id="a11y-fontsize-label">גודל טקסט</span>
            <div class="a11y-fontsize-options" role="group" aria-labelledby="a11y-fontsize-label">
              <button type="button" class="a11y-fontsize-btn a11y-fontsize-sm" data-fontsize="normal" aria-pressed="true" aria-label="גודל טקסט רגיל" onclick="setFontSize('normal')">א</button>
              <button type="button" class="a11y-fontsize-btn a11y-fontsize-md" data-fontsize="large" aria-pressed="false" aria-label="גודל טקסט גדול" onclick="setFontSize('large')">א</button>
              <button type="button" class="a11y-fontsize-btn a11y-fontsize-lg" data-fontsize="xlarge" aria-pressed="false" aria-label="גודל טקסט גדול מאוד" onclick="setFontSize('xlarge')">א</button>
            </div>
          </div>
        </div>
      </details>

      <details class="settings-about">
        <summary>יצירת קשר</summary>
        <div class="details-body">
          <p class="settings-about-text">יש הערה, באג, או הצעה לשיפור? אשמח לשמוע.</p>
          <a class="a11y-link-btn" href="https://github.com/OJBAR/full-court/issues/new" target="_blank" rel="noopener">GitHub Issues</a>
          <div class="email-row">
            <a class="a11y-link-btn" href="mailto:ojbar30@gmail.com?subject=%D7%A4%D7%A0%D7%99%D7%99%D7%94+%D7%9C%D7%90%D7%AA%D7%A8+FULL+COURT:+%D7%A0%D7%95%D7%A9%D7%90+%D7%94%D7%A4%D7%A0%D7%99%D7%99%D7%94">ojbar30@gmail.com</a>
            <button type="button" class="copy-email-btn" onclick="copyEmailAddress(this)" aria-label="העתק את כתובת המייל">📋</button>
          </div>
        </div>
      </details>

      <details class="settings-about">
        <summary>אודות</summary>
        <div class="details-body">
          <button type="button" class="a11y-link-btn" onclick="openA11yStatement()">הצהרת נגישות</button>
        </div>
      </details>

      <div class="beta-note">גרסת בטא · <a href="demos.html">מעבר בין דמואים</a></div>
    </div>
  </div>

  <div class="a11y-overlay" id="a11y-statement-overlay" hidden onclick="if (event.target === this) closeSettingsOverlays()">
    <div class="a11y-panel" role="dialog" aria-modal="true" aria-labelledby="a11y-statement-title">
      <div class="a11y-panel-header">
        <button class="a11y-panel-back" onclick="switchOverlay('settings-overlay')" aria-label="חזור להגדרות">‹</button>
        <h2 id="a11y-statement-title">הצהרת נגישות</h2>
        <button class="a11y-panel-close" onclick="closeSettingsOverlays()" aria-label="סגור הצהרת נגישות">✕</button>
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

    (function initPagers() {{
      // Generic horizontal pager: used for the playoff bracket (2 rounds at
      // a time) and for standings/Cup-groups (one conference at a time).
      // Pages slide via a CSS transform on the track (translateX in 100%
      // steps) instead of show/hide, so both the arrow buttons and swiping
      // animate the same smooth way. Ambient direction inside a bracket page
      // is forced ltr (see _details_block); standings pages aren't, but the
      // same left-to-right "next moves the track further left" logic still
      // reads fine either way since it's just a physical swipe direction.
      var pagers = document.querySelectorAll(".pager");
      pagers.forEach(function(pager) {{
        var viewport = pager.querySelector(".pager-viewport");
        var track = pager.querySelector(".pager-track");
        var pages = Array.prototype.slice.call(pager.querySelectorAll(".pager-page"));
        var prevBtn = pager.querySelector(".pager-prev");
        var nextBtn = pager.querySelector(".pager-next");
        var index = parseInt(pager.getAttribute("data-page"), 10) || 0;

        function render() {{
          track.style.transform = "translateX(" + (-index * 100) + "%)";
          prevBtn.disabled = index === 0;
          nextBtn.disabled = index === pages.length - 1;
        }}

        function goTo(newIndex) {{
          index = Math.max(0, Math.min(newIndex, pages.length - 1));
          render();
        }}

        prevBtn.addEventListener("click", function() {{ goTo(index - 1); }});
        nextBtn.addEventListener("click", function() {{ goTo(index + 1); }});

        var startX = null;
        var startY = null;
        var dragging = false;

        viewport.addEventListener("touchstart", function(e) {{
          startX = e.touches[0].clientX;
          startY = e.touches[0].clientY;
          dragging = false;
          track.style.transition = "none";
        }}, {{ passive: true }});

        viewport.addEventListener("touchmove", function(e) {{
          if (startX === null) return;
          var deltaX = e.touches[0].clientX - startX;
          var deltaY = e.touches[0].clientY - startY;
          if (!dragging && Math.abs(deltaX) < Math.abs(deltaY)) return;
          dragging = true;
          track.style.transform = "translateX(calc(" + (-index * 100) + "% + " + deltaX + "px))";
        }}, {{ passive: true }});

        viewport.addEventListener("touchend", function(e) {{
          track.style.transition = "transform 0.3s ease";
          if (dragging) {{
            var deltaX = e.changedTouches[0].clientX - startX;
            var threshold = 50;
            if (deltaX < -threshold) {{ goTo(index + 1); }}
            else if (deltaX > threshold) {{ goTo(index - 1); }}
            else {{ render(); }}
          }}
          startX = null;
          startY = null;
          dragging = false;
        }});

        render();
      }});
    }})();

    (function initPlayoffBracketPager() {{
      // The playoff bracket's pager: stops 0/1 pan a continuous strip per
      // conference (see _bracket_strip_html) by exactly one column's real
      // measured width, so the round shared between them never appears
      // twice mid-transition; stop 2 swaps to the separate Finals page,
      // since it isn't part of either conference's own strip.
      var wrap = document.querySelector(".bracket-pager");
      if (!wrap) return;

      var step = parseInt(wrap.getAttribute("data-step"), 10) || 0;
      var stripsEl = wrap.querySelector(".bracket-pager-strips");
      var finalsEl = wrap.querySelector(".bracket-pager-finals");
      var tracks = Array.prototype.slice.call(wrap.querySelectorAll(".strip-track"));
      var prevBtn = wrap.querySelector(".pager-prev");
      var nextBtn = wrap.querySelector(".pager-next");

      function maxShift() {{
        var track = tracks[0];
        var firstCol = track && track.children[0];
        if (!firstCol) return 0;
        var gap = parseFloat(getComputedStyle(track).gap || "0") || 0;
        return firstCol.getBoundingClientRect().width + gap;
      }}

      function setTracks(px, animate) {{
        tracks.forEach(function(track) {{
          track.style.transition = animate ? "transform 0.35s ease" : "none";
          track.style.transform = "translateX(-" + px + "px)";
        }});
      }}

      function render(animate) {{
        if (step < 2) {{
          stripsEl.hidden = false;
          finalsEl.hidden = true;
          setTracks(step === 1 ? maxShift() : 0, animate);
        }} else {{
          stripsEl.hidden = true;
          finalsEl.hidden = false;
        }}
        prevBtn.disabled = step === 0;
        nextBtn.disabled = step === 2;
      }}

      function goTo(newStep) {{
        step = Math.max(0, Math.min(newStep, 2));
        render(true);
      }}

      prevBtn.addEventListener("click", function() {{ goTo(step - 1); }});
      nextBtn.addEventListener("click", function() {{ goTo(step + 1); }});

      var startX = null;
      var startY = null;
      var dragging = false;

      wrap.addEventListener("touchstart", function(e) {{
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        dragging = false;
      }}, {{ passive: true }});

      wrap.addEventListener("touchmove", function(e) {{
        if (startX === null || step === 2) return;
        var dx = e.touches[0].clientX - startX;
        var dy = e.touches[0].clientY - startY;
        if (!dragging && Math.abs(dx) < Math.abs(dy)) return;
        dragging = true;
        var base = step === 1 ? maxShift() : 0;
        var target = Math.max(0, Math.min(base - dx, maxShift()));
        setTracks(target, false);
      }}, {{ passive: true }});

      wrap.addEventListener("touchend", function(e) {{
        if (startX === null) return;
        var dx = e.changedTouches[0].clientX - startX;
        var threshold = 40;
        if (dragging) {{
          if (dx < -threshold) {{ goTo(step + 1); }}
          else if (dx > threshold) {{ goTo(step - 1); }}
          else {{ render(true); }}
        }} else {{
          // No live drag preview on the Finals page (it isn't part of the
          // strip) - a plain swipe there still pages, just without a
          // dragged-along preview.
          if (dx < -threshold) {{ goTo(step + 1); }}
          else if (dx > threshold) {{ goTo(step - 1); }}
        }}
        startX = null;
        startY = null;
        dragging = false;
      }});

      window.addEventListener("resize", function() {{ render(false); }});
      render(false);
    }})();

    // Shared by the settings panel and the app-home tab list: an
    // exclusive-open accordion group (opening one closes any other) where
    // both the open and the close are height-animated instead of the
    // native <details> instant snap - intercepts the summary click so we
    // control the open/close timing ourselves.
    function makeExclusiveAccordion(sections) {{
      function animateOpen(section) {{
        var body = section.querySelector(":scope > .details-body");
        if (!body) {{ section.open = true; return; }}
        section.open = true;
        var target = body.scrollHeight;
        body.style.overflow = "hidden";
        body.style.maxHeight = "0px";
        body.getBoundingClientRect();
        body.style.transition = "max-height 0.25s ease";
        body.style.maxHeight = target + "px";
        body.addEventListener("transitionend", function done() {{
          body.style.maxHeight = "";
          body.style.overflow = "";
          body.style.transition = "";
          body.removeEventListener("transitionend", done);
        }});
      }}

      function animateClose(section) {{
        var body = section.querySelector(":scope > .details-body");
        if (!body) {{ section.open = false; return; }}
        body.style.overflow = "hidden";
        body.style.maxHeight = body.scrollHeight + "px";
        body.getBoundingClientRect();
        body.style.transition = "max-height 0.25s ease";
        body.style.maxHeight = "0px";
        body.addEventListener("transitionend", function done() {{
          section.open = false;
          body.style.maxHeight = "";
          body.style.overflow = "";
          body.style.transition = "";
          body.removeEventListener("transitionend", done);
        }});
      }}

      sections.forEach(function(section) {{
        var summary = section.querySelector(":scope > summary");
        summary.addEventListener("click", function(e) {{
          e.preventDefault();
          var wasOpen = section.open;
          sections.forEach(function(other) {{
            if (other !== section && other.open) animateClose(other);
          }});
          if (wasOpen) {{ animateClose(section); }} else {{ animateOpen(section); }}
        }});
      }});
    }}

    (function initSettingsAccordion() {{
      var sections = Array.prototype.slice.call(document.querySelectorAll("#settings-overlay details.settings-about"));
      makeExclusiveAccordion(sections);
    }})();

    var settingsLastFocused = null;
    var activeOverlayId = null;

    function switchOverlay(overlayId) {{
      if (activeOverlayId) {{
        document.getElementById(activeOverlayId).hidden = true;
      }}
      document.getElementById(overlayId).hidden = false;
      activeOverlayId = overlayId;
      var focusTarget = document.querySelector("#" + overlayId + " .a11y-panel-close");
      if (focusTarget) {{ focusTarget.focus(); }}
    }}

    function openSettingsPanel() {{
      settingsLastFocused = document.activeElement;
      document.getElementById("settings-toggle").setAttribute("aria-expanded", "true");
      document.querySelector(".wrapper").setAttribute("aria-hidden", "true");
      switchOverlay("settings-overlay");
      document.addEventListener("keydown", overlayKeydownHandler);
    }}

    function openA11yStatement() {{
      switchOverlay("a11y-statement-overlay");
    }}

    function closeSettingsOverlays() {{
      if (activeOverlayId) {{
        document.getElementById(activeOverlayId).hidden = true;
        activeOverlayId = null;
      }}
      document.getElementById("settings-toggle").setAttribute("aria-expanded", "false");
      document.querySelector(".wrapper").removeAttribute("aria-hidden");
      document.removeEventListener("keydown", overlayKeydownHandler);
      if (settingsLastFocused) {{ settingsLastFocused.focus(); }}
      settingsLastFocused = null;
    }}

    function overlayKeydownHandler(e) {{
      if (e.key === "Escape") {{
        closeSettingsOverlays();
        return;
      }}
      if (e.key === "Tab" && activeOverlayId) {{
        var focusable = document.querySelectorAll("#" + activeOverlayId + " button, #" + activeOverlayId + " a");
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

    function animateSplashAway(splash) {{
      // Moves the splash's own logo so it visually lands exactly on top of
      // the header's logo. The splash background stays fully opaque (no
      // fade) for the entire movement, then the whole splash is removed in
      // one instant the moment the movement finishes - the real header logo
      // was always there underneath, just fully hidden by the opaque
      // background the whole time, so there's a clean hand-off with zero
      // overlap instead of a cross-fade that can show both logos at once.
      var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      var visible = function(img) {{ return getComputedStyle(img).display !== "none"; }};
      var splashLogo = Array.prototype.filter.call(splash.querySelectorAll(".logo-img"), visible)[0];
      var headerLogo = Array.prototype.filter.call(document.querySelectorAll(".header .logo-img"), visible)[0];

      if (reducedMotion || !splashLogo || !headerLogo) {{
        splash.classList.add("fade-out");
        setTimeout(function() {{ splash.remove(); }}, 300);
        return;
      }}

      var splashRect = splashLogo.getBoundingClientRect();
      var headerRect = headerLogo.getBoundingClientRect();
      var scale = headerRect.height / splashRect.height;
      var deltaX = (headerRect.left + headerRect.width / 2) - (splashRect.left + splashRect.width / 2);
      var deltaY = (headerRect.top + headerRect.height / 2) - (splashRect.top + splashRect.height / 2);

      splashLogo.style.transition = "transform 0.5s ease";
      void splash.offsetWidth; // force reflow so the transition applies to the change below, not the initial state
      splashLogo.style.transform = "translate(" + deltaX + "px, " + deltaY + "px) scale(" + scale + ")";

      setTimeout(function() {{ splash.remove(); }}, 520);
    }}

    function dismissSplash() {{
      var splash = document.getElementById("splash-screen");
      if (!splash) return;
      if (splash.classList.contains("visible")) {{
        setTimeout(function() {{ animateSplashAway(splash); }}, 400);
      }} else {{
        splash.remove();
      }}
    }}
    // The "load" event may already have fired by the time this script runs
    // (e.g. on a fast connection/cache) - addEventListener("load", ...) would
    // then never call back, leaving the splash stuck forever. Check
    // readyState first and only wait for the event if it hasn't happened yet.
    // A hard timeout is also set regardless, as a safety net - dismissSplash()
    // is idempotent (a second call is a no-op once the element is gone), so
    // this can never show the splash twice or double-remove it, only
    // guarantee it can't get stuck forever if "load" never fires at all
    // (e.g. a slow/failed image request).
    if (document.readyState === "complete") {{
      dismissSplash();
    }} else {{
      window.addEventListener("load", dismissSplash);
    }}
    setTimeout(dismissSplash, 2500);

    (function initInstallBanner() {{
      var standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
      if (standalone) return;
      if (localStorage.getItem("nba-brief-install-dismissed")) return;

      var ua = navigator.userAgent;
      var isIOS = /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
      var isAndroid = /Android/.test(ua);
      if (!isIOS && !isAndroid) return; // desktop - not relevant

      var banner = document.createElement("div");
      banner.className = "install-banner";
      banner.setAttribute("role", "dialog");
      banner.setAttribute("aria-label", "התקנת האפליקציה");

      var row = document.createElement("div");
      row.className = "install-banner-row";

      var icon = document.createElement("img");
      icon.src = "assets/icon-192.png";
      icon.alt = "";

      var text = document.createElement("div");
      text.className = "install-banner-text";
      text.innerHTML = "<strong>הוסיפו את Full Court למסך הבית</strong>תצוגה מותאמת מובייל וגישה מהירה - ישר ממסך הבית";

      var actionBtn = document.createElement("button");
      actionBtn.type = "button";
      actionBtn.className = "install-banner-action";

      var closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.className = "install-banner-close";
      closeBtn.setAttribute("aria-label", "סגור");
      closeBtn.textContent = "✕";

      function dismiss() {{
        banner.classList.remove("visible");
        localStorage.setItem("nba-brief-install-dismissed", "1");
      }}
      closeBtn.onclick = dismiss;

      row.appendChild(icon);
      row.appendChild(text);
      row.appendChild(actionBtn);
      row.appendChild(closeBtn);
      banner.appendChild(row);

      // Only Safari's own "Add to Home Screen" produces a real standalone
      // web app on iOS - the same action from Chrome/Firefox/Edge on iOS
      // (all of which run on Safari's engine but aren't Safari itself) just
      // adds a plain bookmark that reopens inside that browser's own chrome.
      var isSafari = isIOS && !/CriOS|FxiOS|EdgiOS|OPiOS/.test(ua);

      if (isIOS && isSafari) {{
        // iOS has no programmatic install API at all - the only way is the
        // manual Share -> Add to Home Screen flow, so this just shows those
        // instructions rather than triggering anything itself.
        var hint = document.createElement("div");
        hint.className = "install-banner-hint";
        hint.hidden = true;
        hint.textContent = "לחצו על כפתור השיתוף למטה בספארי, ואז ״הוסף למסך הבית״.";
        actionBtn.textContent = "איך?";
        actionBtn.onclick = function() {{ hint.hidden = !hint.hidden; }};
        banner.appendChild(hint);
        banner.classList.add("visible");
      }} else if (isIOS && !isSafari) {{
        var hint = document.createElement("div");
        hint.className = "install-banner-hint";
        hint.hidden = true;
        var safariUrl = "x-safari-" + location.protocol + "//" + location.host + location.pathname + location.search;
        hint.innerHTML = 'ההוספה למסך הבית זמינה רק דרך ספארי. <a href="' + safariUrl + '">פתחו את הדף בספארי</a> ונסו שוב משם.';
        actionBtn.textContent = "איך?";
        actionBtn.onclick = function() {{ hint.hidden = !hint.hidden; }};
        banner.appendChild(hint);
        banner.classList.add("visible");
      }} else if (isAndroid) {{
        // Android/Chrome has a real install API - capture the browser's own
        // prompt event (this also suppresses Chrome's default mini-infobar)
        // and trigger it from our button instead, so both platforms share
        // one consistent banner even though the underlying mechanism differs.
        var deferredPrompt = null;
        actionBtn.textContent = "התקנה";
        window.addEventListener("beforeinstallprompt", function(e) {{
          e.preventDefault();
          deferredPrompt = e;
          banner.classList.add("visible");
        }});
        actionBtn.onclick = function() {{
          if (!deferredPrompt) return;
          deferredPrompt.prompt();
          deferredPrompt.userChoice.then(function() {{ dismiss(); }});
        }};
      }}

      document.body.appendChild(banner);
    }})();

    (function initPullToRefresh() {{
      // Regular browser tabs already have a native pull-to-refresh gesture -
      // this is only needed because iOS disables that gesture once the PWA
      // runs in standalone mode (the same platform limitation the old
      // visible refresh button worked around).
      var standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
      if (!standalone) return;

      var startY = null;
      var currentPull = 0;
      var threshold = 70;

      var indicator = document.createElement("div");
      indicator.className = "pull-refresh-indicator";
      indicator.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M12 19l-6-6M12 19l6-6"/></svg>';
      document.body.appendChild(indicator);

      function setPull(px) {{
        indicator.style.opacity = Math.min(px / threshold, 1);
        indicator.style.transform = "translateX(-50%) translateY(" + px + "px) rotate(" + (px * 3) + "deg)";
      }}

      function atTop() {{
        // In tabs-mode the page shell itself no longer scrolls (see the CSS)
        // - <main> is the actual scrollable region there - so "at the top"
        // has to be checked against main.scrollTop, not window.scrollY.
        var main = document.querySelector("main");
        if (document.documentElement.classList.contains("tabs-mode") && main) {{
          return main.scrollTop === 0;
        }}
        return window.scrollY === 0;
      }}

      document.addEventListener("touchstart", function(e) {{
        startY = atTop() ? e.touches[0].clientY : null;
        currentPull = 0;
        indicator.style.transition = "none";
      }}, {{ passive: true }});

      document.addEventListener("touchmove", function(e) {{
        if (startY === null) return;
        var delta = e.touches[0].clientY - startY;
        currentPull = Math.max(0, Math.min(delta, threshold * 1.5));
        setPull(currentPull);
      }}, {{ passive: true }});

      document.addEventListener("touchend", function() {{
        indicator.style.transition = "transform 0.25s ease, opacity 0.25s ease";
        if (currentPull >= threshold) {{
          // A plain location.reload() still respects GitHub Pages' HTTP
          // cache - iOS in standalone mode can keep serving a cached
          // response for several minutes without even asking the server.
          // A cache-busting query param makes this a URL the cache has
          // never seen, forcing a genuine fetch every time.
          var url = location.pathname + "?_r=" + Date.now();
          location.href = url;
        }} else {{
          indicator.style.opacity = 0;
          indicator.style.transform = "translateX(-50%) translateY(0)";
        }}
        startY = null;
        currentPull = 0;
      }}, {{ passive: true }});
    }})();

    (function initAppHome() {{
      var standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
      var narrow = window.matchMedia("(max-width: 480px)").matches;
      if (!standalone || !narrow) return;

      var main = document.querySelector("main");
      var summaryDiv = main.querySelector(":scope > .summary");
      var sections = Array.prototype.slice.call(main.querySelectorAll(":scope > details.tab-section"));
      if (sections.length < 1) return;

      document.documentElement.classList.add("tabs-mode");

      var home = document.createElement("div");
      home.className = "app-home";

      // Returning home always re-collects every section back into the home
      // list (in their original order) and clears whichever one, if any,
      // was promoted to a full screen - safe to call unconditionally from
      // any state (header tap, the summary/a section's own back arrow).
      function showHome() {{
        home.classList.remove("hidden");
        if (summaryDiv) summaryDiv.classList.remove("app-screen-active");
        sections.forEach(function(section) {{
          section.classList.remove("app-screen-active");
          section.open = false;
          home.appendChild(section);
        }});
      }}
      function showSummary() {{
        home.classList.add("hidden");
        if (summaryDiv) summaryDiv.classList.add("app-screen-active");
        main.scrollIntoView({{ behavior: "smooth", block: "start" }});
      }}
      // Opening a tab from the home list promotes it to a full screen of
      // its own (same treatment as the summary) instead of expanding it
      // inline - moved out of .app-home to a direct child of <main> so
      // .app-home's display:none doesn't hide it along with the rest of
      // the home list.
      function showSection(section) {{
        home.classList.add("hidden");
        section.open = true;
        section.classList.add("app-screen-active");
        main.insertBefore(section, main.firstChild);
        main.scrollIntoView({{ behavior: "smooth", block: "start" }});
      }}
      // Listens on the whole header, not just the logo <img> itself, so it
      // always fires regardless of exactly where within the logo area the
      // tap lands, rather than requiring a precise hit on the image.
      document.querySelector(".header").addEventListener("click", showHome);

      if (summaryDiv) {{
        var bigBtn = document.createElement("button");
        bigBtn.type = "button";
        bigBtn.className = "app-home-big-btn";
        bigBtn.textContent = "סיכום הלילה";
        bigBtn.onclick = showSummary;
        home.appendChild(bigBtn);
        summaryDiv.addEventListener("click", showHome); // tapping the summary itself also returns home
      }}

      sections.forEach(function(section) {{
        var summary = section.querySelector(":scope > summary");
        summary.addEventListener("click", function(e) {{
          e.preventDefault();
          if (section.classList.contains("app-screen-active")) {{
            showHome();
          }} else {{
            showSection(section);
          }}
        }});
        home.appendChild(section);
      }});

      main.insertBefore(home, main.firstChild);
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
      document.getElementById("settings-theme-btn").textContent = isDark ? "☀" : "🌙";
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
        return '<p style="color:var(--text-muted); font-size:0.875rem;">אין משחקים ללילה הזה.</p>'

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
        return '<p style="color:var(--text-muted); font-size:0.875rem;">אין נתוני טבלה זמינים.</p>'

    conferences: dict[str, list[dict]] = {}
    for team in standings:
        conferences.setdefault(team["Conference"], []).append(team)

    names = {"East": "מזרח", "West": "מערב"}
    pages = []
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
        pages.append(
            f'<div class="conference standings-block"><h3>{names.get(conf_key, conf_key)}</h3>'
            + "\n          ".join(rows)
            + "</div>"
        )
    return _build_pager_html(pages)


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


def _conference_bracket_columns(playoff_series: list[dict], conference: str) -> dict[str, str]:
    """
    One conference's three playoff-round columns (1st Round -> Conf.
    Semifinals -> Conf. Finals), each returned separately (keyed by round
    name) so a caller can combine any two adjacent rounds onto one page
    instead of always showing the full three-round bracket at once.
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
    semis_pair = f'<div class="bracket-pair bracket-pair-r2">{"".join(_bracket_series_html(s) for s in semis_slots)}</div>'

    final_column = _bracket_series_html(finals[0] if finals else None)

    return {
        "1st Round": _bracket_column_html("1st Round", f'<div class="bracket-round">{"".join(round1_pairs)}</div>'),
        "Conf. Semifinals": _bracket_column_html("Conf. Semifinals", f'<div class="bracket-round">{semis_pair}</div>'),
        "Conf. Finals": _bracket_column_html("Conf. Finals", f'<div class="bracket-round bracket-final">{final_column}</div>'),
    }


def _finals_match_html(series: dict | None, conf_by_team: dict) -> str:
    """
    Finals-specific version of _bracket_series_html: same look as every
    other bracket cell (seed badge, no conference-color badge), but ordered
    by conference (West on top, East below) to match the West/East block
    order on the page above it, instead of by seed - seeds aren't
    comparable across conferences, so sorting by them wouldn't reliably put
    the same conference on top from one Finals to the next.
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
    conf_order = {"West": 0, "East": 1}
    ordered = sorted(teams, key=lambda t: conf_order.get(conf_by_team.get(t["team_id"]), 99))
    max_wins = max(t["wins"] for t in teams)

    def _team(team: dict) -> str:
        cls = " winner" if series["is_over"] and team["wins"] == max_wins else ""
        seed = team.get("seed")
        seed_html = f'<span class="bracket-seed">{seed}</span>' if seed else ""
        return (
            f'<div class="bracket-team{cls}">'
            f'<span class="bracket-team-label">{seed_html}<span>{html.escape(team["tricode"])}</span></span>'
            f'<span class="bracket-score">{team["wins"]}</span></div>'
        )

    return '<div class="bracket-match">' + "".join(_team(t) for t in ordered) + "</div>"


def _finals_champion_line(series: dict | None) -> str:
    if series and series["is_over"]:
        champion = series["teams"][0]
        return f'<p class="game-sub" dir="rtl">{html.escape(champion["tricode"])} אלופת ה-NBA!</p>'
    return ""


_PLAYOFF_ROUNDS = ["1st Round", "Conf. Semifinals", "Conf. Finals", "NBA Finals"]


def _build_pager_html(pages: list[str], start_page: int = 0) -> str:
    """
    Generic horizontal pager (one page visible at a time, arrows + swipe,
    sliding transform) - shared by the playoff bracket (2 rounds at a time)
    and standings/Cup-group tables (one conference at a time). See
    initPagers() for the JS driving it.
    """
    pages_html = "".join(f'<div class="pager-page">{page_html}</div>' for page_html in pages)
    return (
        f'<div class="pager" data-page="{start_page}">'
        '<div class="pager-viewport">'
        f'<div class="pager-track">{pages_html}</div>'
        "</div>"
        '<div class="pager-nav">'
        '<button type="button" class="pager-arrow pager-prev" aria-label="הקודם">‹</button>'
        '<button type="button" class="pager-arrow pager-next" aria-label="הבא">›</button>'
        "</div></div>"
    )


def _bracket_conf_block(conf_label: str, columns_html: str) -> str:
    return (
        '<div class="bracket-conf-block">'
        f'<div class="bracket-conf-label">{html.escape(conf_label)}</div>'
        f'<div class="bracket">{columns_html}</div>'
        "</div>"
    )


def _bracket_strip_html(conf_label: str, columns: dict[str, str]) -> str:
    """
    One conference's full Round 1 -> Conf. Semis -> Conf. Finals bracket as
    a single continuous strip (all 3 columns, always in the DOM together),
    instead of splitting it across separate pages. initPlayoffBracketPager()
    pans a fixed viewport across this strip by exactly one column's width
    at a time, so a round shared between two "stops" (e.g. Conf. Semis,
    visible at both stop 0 and stop 1) is the same element throughout - it
    just slides from the trailing position to the leading one, instead of
    two independent copies appearing to overlap mid-transition the way two
    separate pages sliding past each other would.
    """
    track_html = columns["1st Round"] + columns["Conf. Semifinals"] + columns["Conf. Finals"]
    return (
        '<div class="bracket-conf-block">'
        f'<div class="bracket-conf-label">{html.escape(conf_label)}</div>'
        f'<div class="strip-viewport"><div class="strip-track">{track_html}</div></div>'
        "</div>"
    )


def _bracket_page_finals(
    columns_by_conf: dict[str, dict[str, str]], finals_series: dict | None, conf_by_team: dict
) -> str:
    """
    The Conf. Finals -> NBA Finals page: same stacked-block format as every
    other page (one block per conference, plus a third block for the Finals
    itself) instead of a special side-flanking layout - keeps the whole
    pager visually consistent from page to page.
    """
    west_col = columns_by_conf["West"].get("Conf. Finals", "")
    east_col = columns_by_conf["East"].get("Conf. Finals", "")
    finals_col = _bracket_column_html(
        "NBA Finals", f'<div class="bracket-round bracket-final">{_finals_match_html(finals_series, conf_by_team)}</div>'
    )
    blocks = "".join(
        _bracket_conf_block(label, col) for label, col in (("מערב", west_col), ("מזרח", east_col), ("גמר", finals_col))
    )
    return blocks + _finals_champion_line(finals_series)


def _build_combined_playoff_bracket_html(playoff_series: list[dict], games: list[dict]) -> str:
    """
    A single bracket covering the whole playoffs (both conferences, no
    separate tab per conference or for the Finals) - only two adjacent
    rounds are shown at a time, since a full 4-round bracket is too wide for
    mobile. Stops 0 and 1 (1st Round<->Conf. Semis<->Conf. Finals) are a pan
    across one continuous strip per conference (see _bracket_strip_html) -
    stop 2 (the Finals) is a separate composed page, since it's not part of
    either conference's own strip. Defaults to whichever stop is relevant
    tonight: if tonight's games span more than one round (e.g. a 1st Round
    Game 7 and a Conf. Semifinals Game 1 on the same night), the earliest
    round wins, since that series isn't fully resolved league-wide yet.
    """
    round_index = {r: i for i, r in enumerate(_PLAYOFF_ROUNDS)}
    current_indices = [round_index[g["po_round"]] for g in games if g.get("po_round") in round_index]
    current_round = min(current_indices) if current_indices else 0
    start_step = min(current_round, 2)

    columns_by_conf = {conf: _conference_bracket_columns(playoff_series, conf) for conf in ("West", "East")}
    finals_series = next((s for s in playoff_series if s.get("round") == "NBA Finals"), None)
    conf_by_team = {
        t["team_id"]: s.get("conference")
        for s in playoff_series
        if s.get("round") != "NBA Finals"
        for t in s["teams"]
    }

    west_strip = _bracket_strip_html("מערב", columns_by_conf["West"])
    east_strip = _bracket_strip_html("מזרח", columns_by_conf["East"])
    finals_page = _bracket_page_finals(columns_by_conf, finals_series, conf_by_team)

    strips_hidden = " hidden" if start_step == 2 else ""
    finals_hidden = "" if start_step == 2 else " hidden"

    # The content itself (and everything around it) is forced dir="ltr" (see
    # _details_block) since it's mostly seed numbers/English round names, so
    # the pager's arrows follow plain left-to-right pagination convention:
    # prev (‹) sits physically on the left, next (›) on the right - not
    # RTL-mirrored, since the ambient direction here already isn't RTL.
    return (
        f'<div class="bracket-pager" data-step="{start_step}">'
        f'<div class="bracket-pager-strips"{strips_hidden}>{west_strip}{east_strip}</div>'
        f'<div class="bracket-pager-finals"{finals_hidden}>{finals_page}</div>'
        '<div class="pager-nav">'
        '<button type="button" class="pager-arrow pager-prev" aria-label="הקודם">‹</button>'
        '<button type="button" class="pager-arrow pager-next" aria-label="הבא">›</button>'
        "</div></div>"
    )


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
        '<div class="bracket-pair bracket-pair-captioned">'
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
    Play-In bracket for one conference - one page of the shared "פלייאין"
    pager (see _build_secondary_section), one conference at a time. The 3
    games are identified by their teams' seeds, not by date - the two
    conferences don't always play their games on the same nights, so date
    order alone doesn't
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
    sf_pair = f'<div class="bracket-pair bracket-pair-r2">{"".join(sf_matches_html)}</div>'

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
        return '<p style="color:var(--text-muted); font-size:0.875rem;">אין נתוני בתים זמינים.</p>'

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

    result = _build_pager_html(conf_blocks)
    if found_wildcard:
        # Shown outside/below the pager itself (not per-page) since either
        # conference's page can carry the WC badge - stays visible no matter
        # which one is currently showing, same as when both were always
        # visible together before.
        result += (
            '\n      <p class="wildcard-legend" dir="rtl">'
            "WC - הסגנית עם המאזן הטוב ביותר.</p>"
        )
    return result


def _details_block(title: str, inner_html: str) -> str:
    return (
        '<details class="tab-section">\n'
        f"      <summary>{title}</summary>\n"
        '      <div class="details-body" dir="ltr">\n'
        f"        {inner_html}\n"
        "      </div>\n"
        "    </details>"
    )


def _build_secondary_section(data: dict) -> str:
    """
    Playoffs: one tab, a single paged bracket covering both conferences and
    the Finals together (see _build_combined_playoff_bracket_html) - there's
    no regular-season standings concept during playoffs. NBA Cup days
    (group stage or knockout): the
    regular league standings always show first, since every Cup game except
    the Championship counts toward the regular season - plus a group-standings
    tab on group-stage days and a connected bracket tab on knockout days.
    Otherwise: standings only.
    """
    if data.get("is_playoffs"):
        playoff_series = data.get("playoff_series", [])
        sections = [("בראקט הפלייאוף", _build_combined_playoff_bracket_html(playoff_series, data["games"]))]
    else:
        standings_section = ("טבלת הליגה", _build_standings_html(data["standings"]))
        sections = []
        if data.get("is_cup_groups"):
            sections.append(
                ("בתי הגביע", _build_cup_group_standings_html(data.get("cup_group_standings", [])))
            )
        if data.get("is_cup_knockout"):
            sections.append(("בראקט הגביע", _build_cup_bracket_html(data.get("cup_bracket", []))))
        if data.get("is_play_in"):
            games = data.get("play_in_bracket", [])
            play_in_pages = [
                f'<div class="bracket-conf-block"><div class="bracket-conf-label">{label}</div>{_build_play_in_html(games, conf)}</div>'
                for conf, label in (("West", "מערב"), ("East", "מזרח"))
            ]
            sections.append(("פלייאין", _build_pager_html(play_in_pages)))
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
