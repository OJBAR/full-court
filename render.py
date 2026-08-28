import html
import json
import re
from datetime import datetime, timedelta, timezone
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
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>FULL COURT - {display_date}</title>
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="assets/icon-180.png">
<meta name="theme-color" content="#EFEAD8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#2A2118" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Full Court">
<meta name="app-version" content="{app_version}">
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
  /* Android Chrome auto-boosts font size on narrow columns of text (its
     "font inflation" readability feature) independently of any CSS here -
     it was never caught in testing since this project was only ever
     checked on iOS Safari, which doesn't do this. That extra, uncontrolled
     boost stacks on top of our own deliberate --a11y-text-scale sizing,
     making text render bigger than any of our rem values actually say -
     exactly the "text too big, tables need scrolling, things get cut off"
     symptom. Disabling it makes our own sizing the only source of scale,
     on every browser. */
  html {{ -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }}
  html {{ font-size: calc(16px * var(--a11y-text-scale, 1)); }}
  /* Belt-and-suspenders alongside the viewport meta tag's user-scalable=no
     above - blocks double-tap-to-zoom too, which that meta tag alone
     doesn't cover on every browser. pan-y (not manipulation): manipulation
     still allows horizontal panning of the document itself, which on iOS
     was enough to let a swipe gesture (e.g. in the schedule tab - see
     initScheduleTab()) shift the whole page sideways for a moment before
     JS's own preventDefault took over, visibly jumping/truncating the
     sticky header. pan-y is stricter (vertical only) and still blocks
     double-tap-zoom the same way manipulation does. */
  html, body {{ touch-action: pan-y; }}
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
    padding-bottom: 9px;
    margin-bottom: 9px;
    border-bottom: 1px solid var(--border);
  }}
  .game-block:last-child {{ border-bottom: none; margin-bottom: 0; }}
  .game-row {{
    display: flex;
    /* Top-aligned, not centered: .team is taller than .score when a
       record is shown (name line + record line below it) - centering
       would line up .score against the midpoint of that whole two-line
       block instead of against just the team name, throwing the two out
       of alignment. Top-aligning keeps the name and score on the same
       line regardless, with the record simply continuing below. */
    align-items: flex-start;
    justify-content: center;
    padding-top: 8px;
    font-size: 0.9375rem;
    position: relative;
  }}
  .team {{ width: 4.5em; color: var(--text-muted); text-align: center; }}
  .team.winner {{ color: var(--text-heading); font-weight: 700; }}
  .team-record {{
    display: block;
    font-size: 0.5938rem;
    font-weight: 400;
    color: var(--text-muted);
  }}
  .score {{ width: 2.2em; text-align: center; color: var(--text-muted); font-variant-numeric: tabular-nums; }}
  .score.winner {{ color: var(--accent); font-weight: 700; }}
  /* A not-yet-played game's tip-off time ("19:30") is wider than a plain
     2-digit score - .score's fixed 2.2em would clip it. */
  .score.time {{ width: auto; min-width: 3.4em; }}
  .ot-tag {{
    /* Absolutely positioned off to the side, out of the flex flow, so it
       never shifts the row's true center - .game-row centers just the
       teams/score, same with or without overtime. */
    position: absolute;
    top: 50%;
    left: 2px;
    transform: translateY(-50%);
    padding: 2px 5px;
    border-radius: 999px;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 9px;
    font-weight: 700;
  }}
  .game-sub {{
    text-align: center;
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 6px;
  }}
  /* The game's own page on nba.com and its highlight video on GAMETIME
     HIGHLIGHTS, an unofficial third-party channel (see highlights.py) -
     either or both may be missing (the highlight especially, since it's
     often not up yet at brief time - see scheduler.py's two-pass design),
     so .game-links only renders the ones that exist, side by side. Both
     open in a real browser tab/app, out of the installed PWA. See
     initScheduleTab()'s gameUrl()/renderRichRow() - the schedule tab (see
     _build_schedule_html) is what builds these now, results are no longer
     a separate tab. */
  .game-links {{
    display: flex;
    justify-content: center;
    gap: 14px;
    margin-top: 6px;
  }}
  .game-link {{
    font-size: 0.7rem;
    color: var(--accent);
    text-decoration: none;
    padding: 3px 9px;
    border: 1px solid var(--accent);
    border-radius: 999px;
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
  /* Compact the Cup groups specifically (not the league standings, which
     already got a deliberate size bump elsewhere) so 3 groups per
     conference fit one app screen without needing to scroll to see the
     rest. */
  :root.tabs-mode .cup-group {{ margin-bottom: 6px; padding: 6px 8px 4px; }}
  :root.tabs-mode .cup-group .standing-row {{ padding: 5px 0; font-size: 0.8125rem; }}
  :root.tabs-mode .cup-group .standing-team {{ font-size: 0.75rem; }}

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
    align-items: center;
    justify-content: space-around;
    gap: 12px;
  }}
  .bracket-final {{ justify-content: center; }}
  /* The playoff bracket's strips and shared round-header track need every
     column to be exactly the same width (146px = a match's 128px plus a
     paired round's 16px padding + 2px border, which round 3's lone match
     doesn't have on its own) - otherwise the header track (label-only
     columns, sized to their text) and the two conference strips (some
     columns paired, some not) would drift out of sync as they pan
     together. Scoped to the playoff pager only, so it doesn't touch the
     Cup/Play-In brackets' own column sizing. */
  .bracket-pager .bracket-column,
  .cup-bracket-pager .bracket-column {{ width: 146px; }}
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
  /* Cup-specific: the Quarterfinal round's own pairs get the same 78px
     internal gap the Semifinal pair already uses, and the gap between the
     two conferences' own Quarterfinal blocks (.bracket-conf-block's
     margin-bottom, was a flat 18px) is widened to match that same 78px too
     - purely for visual breathing room/consistent spacing throughout the
     round (so tapping/swiping the Cup bracket isn't confined to a cramped
     block), per explicit feedback against a real screenshot. Both changes
     mean the Semifinal gap has to be recalculated the same way
     .bracket-pair-r2's own comment above derives 78 in the first place,
     just with this bracket's real, now-updated numbers: a Quarterfinal
     pair's own height is matchHeight(56) + 78px gap = 134px, and the two
     conferences' pairs are now stacked 134 + 78 (conf-block margin) + 134
     apart - so the Semifinal pair's two slots need gap = 56 + 78 + 78 =
     212 to land on those same two centers. Estimated the same way the
     original 78/78 pairing was (not visually re-verified against a live
     connector line render), same caveat as everywhere else this project
     derives bracket geometry by formula. */
  .cup-bracket-pager .bracket-pair:not(.bracket-pair-r2) {{ gap: 78px; }}
  .cup-bracket-pager .bracket-pair-r2 {{ gap: 212px; }}
  /* 66px, not 78 - .bracket-round (this conf-block's own parent) already
     has its own 12px flex gap between its two conf-block children, which
     stacks with this margin (measured directly: an attempted 78px margin
     rendered as a 90px real gap, exactly 78+12). Reduced by that same 12 so
     the actual on-screen gap comes out to 78, matching the within-pair
     gap above as intended. */
  .cup-bracket-pager .bracket-conf-block {{ margin-bottom: 66px; }}
  .cup-bracket-pager .bracket-conf-block:last-child {{ margin-bottom: 0; }}
  /* .bracket-pair::after's 25px stub is calibrated to reach the next
     round's box when that box is itself a .bracket-pair (which occupies a
     column's full 146px width, so the stub only needs to bridge the 24px
     track gap between columns). A round-2 pair always feeds a single,
     centered .bracket-final match instead (Conf. Finals / Cup
     Championship) - that box is 128px inside a 146px column, inset 9px
     from the column's own edge, so the plain 25px stub falls 8px short of
     actually touching it. +8px closes that gap to the same "touches with
     nothing left over" distance every other round's connector has. */
  .bracket-pair-r2::after {{ width: 33px; }}
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
  /* Shared "not decided yet, but not TBD either" look - used both for a
     series still being played (see _bracket_series_html/_finals_match_html)
     and for a known team waiting on a TBD opponent (see
     _bracket_projected_series_match_html and Cup's own
     _bracket_projected_match_html). Neither case means "lost" (the default
     muted color) or "decided winner" (bold) - plain heading color, no bold.
     font-style is reset explicitly since the TBD-projected cells wrap this
     in .bracket-match-tbd, whose italic would otherwise inherit down onto
     a team that's actually known. */
  .bracket-team.pending {{ color: var(--text-heading); font-weight: 400; font-style: normal; }}
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
  .bracket-match-tbd {{ opacity: 0.55; font-style: italic; }}
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
  /* The NBA Finals match is a real 4th track (see
     _bracket_nba_finals_track_html), not a separately-faded overlay - it
     has its own .strip-viewport, so it's clipped and only becomes visible
     by actually being panned into view, in lockstep with everything else
     (its .strip-track is picked up by the exact same ".strip-track"
     selector as every other track in initPlayoffBracketPager, so it needs
     no special-casing there at all). Its wrapper only needs a vertical
     position set, live, to span from the top edge of the West conference's
     Conf. Finals box to the bottom edge of the East one (positionFinals
     Connector() in initPlayoffBracketPager) - .bracket-final's own
     justify-content:center then lands the match at the true vertical
     middle between the two conferences, not squeezed into either one's own
     much shorter row height. The connecting line is the only thing still
     positioned separately (it can't live inside any single strip's own
     viewport, since it has to reach from one conference's box to the
     other's), sharing that same measured top/height, with its own left
     tracking those boxes' real right edge plus the same 16px gap
     .bracket-pair leaves before its own connecting line. Both pieces are
     folded into the same tracks[] array the pager already pans with
     setTracks(), so the exact same transform that moves the two conference
     strips moves them too - locked to the pan/drag the whole way, not just
     once settled. */
  .bracket-pager-strips {{ position: relative; }}
  .nba-finals-track-wrap {{
    position: absolute;
    left: 0;
    right: 0;
  }}
  /* The wrapper's own height is set live in px (positionFinalsConnector),
     but that alone doesn't make the match inside actually fill it - flex
     stretching only propagates from a parent that itself has a real
     height, and neither .strip-viewport nor .strip-track had one, so the
     match just sat at its own small natural size flush at the wrapper's
     top (i.e. level with the West conference's box) instead of being
     centered across the whole span. Chaining height:100% down through both
     lets .bracket-column's default stretch and .bracket-round's flex:1 do
     the rest, so .bracket-final's justify-content:center finally has the
     full span to center within. */
  .nba-finals-track-wrap .strip-viewport,
  .nba-finals-track-wrap .strip-track {{ height: 100%; }}
  .nba-finals-connector {{
    position: absolute;
    width: 2px;
    background: var(--text-muted);
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.3s ease;
    pointer-events: none;
  }}
  .bracket-pager[data-step="2"] .nba-finals-connector {{
    opacity: 1;
    visibility: visible;
  }}
  .nba-finals-connector::after {{
    content: "";
    position: absolute;
    top: 50%;
    left: 100%;
    width: 25px;
    height: 2px;
    margin-top: -1px;
    background: var(--text-muted);
  }}
  /* Play-In is just two stacked conference brackets with no pager, so it
     doesn't naturally use up the screen the way the paged brackets do. A
     fixed zoom overflowed narrower phones sideways - initFitToWidth() (JS)
     instead measures the real available width and computes a zoom that's
     guaranteed to fit, scaling everything (including its own layout
     footprint, unlike `transform`) so surrounding spacing reflows
     correctly without touching the fixed-pixel connector math inside
     .bracket-pair-captioned (it all scales together proportionally, so
     that math stays internally consistent regardless of the factor). */
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

  /* The season schedule tab's day nav (see initScheduleTab()) - reuses
     .pager-nav/.pager-arrow above for the arrows themselves, just needs its
     own label in between and a bit more breathing room above the list. */
  /* position:relative so .schedule-cal-toggle can sit off to the side via
     position:absolute, out of the flex flow entirely - otherwise it's a
     4th flex item alongside the arrows/label, pushing that centered trio
     visibly off-center instead of leaving it centered on its own. */
  .schedule-nav {{ margin-bottom: 8px; position: relative; }}
  /* Locks the day-pager row (label + arrows + calendar icon) to the top
     alongside the tab's own "לוח התוצאות" title bar, the same way every
     other tab's title stays put while its content scrolls underneath -
     without this, a day with enough games to need scrolling carried the
     pager row away with the list, so only the plain title bar (no arrows)
     stayed visible once you scrolled past it. --schedule-nav-top is set in
     JS (see fitToScreen()) to the title bar's own real measured height, so
     this sticks exactly below it instead of overlapping or leaving a gap.
     The translateZ/will-change pair forces this onto its own GPU
     compositing layer - the same fix used for the comprehensive demo's
     cd-nav bar - because a plain sticky/fixed element here visibly drifted
     sideways for a moment during the tab's own active touch-drag handling
     (the day-swipe gesture) without it. */
  :root.tabs-mode details.tab-section.app-screen-active > .details-body:has(> .schedule-tab) .schedule-nav {{
    position: sticky;
    top: var(--schedule-nav-top, 0px);
    z-index: 4;
    background: var(--bg);
    transform: translateZ(0);
    -webkit-transform: translateZ(0);
    will-change: transform;
  }}
  .schedule-date-label {{
    min-width: 9em;
    text-align: center;
    font-size: 0.9375rem;
    font-weight: 700;
    color: var(--text-heading);
  }}
  .schedule-cal-toggle {{
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg);
    font-size: 15px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  /* The global button:active {{ transform: scale(0.96) }} (see the a11y/tap-
     feedback rules below) would otherwise REPLACE this button's own resting
     transform (translateY(-50%), needed since it's position:absolute and
     vertically centered) instead of combining with it - losing the -50%
     mid-press made the icon visibly jump down by half its own height on
     every tap. Re-stated together here, at higher specificity (class +
     :active beats the plain button:active), so both apply at once. */
  .schedule-cal-toggle:active {{ transform: translateY(-50%) scale(0.96); }}
  /* Month-at-a-glance jump-to-date view (backlog item 7) - a plain grid,
     one cell per day of the currently-shown month, days outside that month
     left blank (not "bleeding" into neighboring months' numbers, to keep
     it uncluttered). Replaces .schedule-games while open; the day-nav row
     above it is reused as-is (same arrows, same label spot) rather than a
     second row of its own - see initScheduleTab()'s openCalendar()/
     changeMonth(). */
  .schedule-calendar-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 3px;
  }}
  .schedule-calendar-dow {{
    text-align: center;
    font-size: 0.625rem;
    color: var(--text-muted);
    padding-bottom: 2px;
  }}
  .schedule-calendar-day {{
    position: relative;
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    color: var(--text-body);
    border-radius: 6px;
    background: var(--card-bg);
    border: none;
    font-family: inherit;
    cursor: default;
  }}
  .schedule-calendar-day.empty {{ background: transparent; }}
  .schedule-calendar-day.has-games {{ cursor: pointer; color: var(--text-heading); font-weight: 700; }}
  .schedule-calendar-day.is-today {{ box-shadow: inset 0 0 0 1.5px var(--accent); }}
  .schedule-calendar-day .cal-count {{
    position: absolute;
    top: -3px;
    left: -3px;
    min-width: 14px;
    height: 14px;
    padding: 0 2px;
    border-radius: 999px;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 9px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  /* pan-y (not none): a day with many games still has to scroll vertically
     normally - only horizontal panning is taken over by initScheduleTab()'s
     own touch handling (swipe between days). Applied to .details-body too,
     not just .schedule-tab - that's what the swipe listener is actually
     attached to (see initScheduleTab()'s touchArea/fitToScreen()), and its
     own natural content height leaves empty space below a short day's list
     that .schedule-tab alone doesn't cover. Deliberately NOT applied to the
     summary/title bar above it (see initScheduleTab()'s comment on
     touchArea) - that has its own click-to-go-home handler, and giving it
     touch-action here too would still let a swipe starting near/on it
     interact with that handler. */
  .schedule-tab {{ touch-action: pan-y; }}
  .details-body:has(> .schedule-tab) {{ touch-action: pan-y; }}

  /* The playoff bracket's own pager (see initPlayoffBracketPager()) - a
     continuous per-conference strip panned by a JS-measured column width
     instead of the generic page-based .pager above, so the round shared
     between two adjacent stops never appears as two separate copies. */
  .strip-viewport {{ overflow: hidden; touch-action: pan-y; }}
  /* Constrained to exactly 2 columns' width (146px each + the 24px gap
     between them) and centered, instead of stretching to the full width
     of its container and leaving the visible columns pinned to one side
     with empty space on the other. */
  .bracket-pager .strip-viewport,
  .cup-bracket-pager .strip-viewport {{ max-width: 316px; margin: 0 auto; }}
  .strip-track {{
    display: flex;
    justify-content: flex-start;
    gap: 24px;
    padding: 4px 4px 12px;
    transition: transform 0.35s ease;
  }}
  /* The Cup pager's own viewport used to be scaled down by
     initFitToWidth()'s CSS zoom, then briefly switched to real native
     scrolling to dodge a real bug where a CSS transition on transform
     didn't work at all together with that zoom (confirmed directly on a
     real device). The zoom turned out to be unnecessary in the first
     place - this pager shares the exact same column width/viewport
     constraint as the playoff bracket's own pager, which was never zoomed
     and fits fine - and removing it removed the actual reason the
     transition-based approach didn't work here, so initCupBracketPager()
     is back to the same JS-transformed-track mechanism as the playoff
     bracket's own pager, no CSS overrides needed here beyond the shared
     .strip-viewport/.strip-track rules above. */

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
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }}
  .beta-note a {{ color: var(--accent); text-decoration: none; }}
  .manual-refresh-btn {{
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text-heading);
    border-radius: 999px;
    width: 22px;
    height: 22px;
    font-size: 12px;
    line-height: 1;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}

  /* App-like extras. Most of this section (splash screen, pull-to-refresh)
     is genuinely standalone-only - things a real installed app needs that a
     browser tab already has natively or doesn't need at all. The tabs-mode
     shell itself (below) is the one exception - it's phone-width-gated, not
     standalone-gated, specifically so a regular mobile browser visit looks
     like the app too (see initAppHome()) - that's what makes someone want
     to install it in the first place, not something worth hiding until
     after they already have. */
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

  /* App home (narrow viewport, see initAppHome()) - active in a regular
     mobile browser tab too, not just once installed. Only the
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
    /* pan-y: <main> is the real scroll container in tabs-mode (the sticky
       tab-title bar sticks to ITS scroll position) - without this, iOS
       Safari can still engage its own horizontal/elastic-bounce handling
       for a fraction of a touch gesture before a descendant's touch-action
       or preventDefault takes effect, which is enough to nudge <main>'s
       scroll position and visibly jump the sticky bar even during a swipe
       that's fully handled in JS (see initScheduleTab()). */
    touch-action: pan-y;
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
    min-height: 0;
    margin-top: 0;
    border: none;
    border-radius: 0;
    background: transparent;
    /* The base `details` rule below sets overflow:hidden for the little
       card's rounded corners - left as-is here, it clips this element's
       own content before <main>'s scroll ever sees the overflow, which is
       the actual reason content was getting cut off with no way to
       scroll to it (not the centering, that part was already fixed). */
    overflow: visible;
  }}
  :root.tabs-mode details.tab-section.app-screen-active > summary::after {{ content: "‹"; }}
  /* The tab's own title/back-arrow row stays pinned to the top of the
     scrollable area (<main>) instead of scrolling away with a long list
     of games - needs its own opaque background so scrolled-past content
     doesn't show through underneath it. */
  :root.tabs-mode details.tab-section.app-screen-active > summary {{
    position: sticky;
    top: 0;
    z-index: 5;
    background: var(--bg);
    /* Without this, summary is a flex item (its parent <details> is
       flex-direction:column) with the default flex-shrink:1 - if its
       sibling .details-body ever needs more room than <details> actually
       has (the schedule tab's own fitToScreen() forces a min-height on
       .details-body to reach empty space below a short day for swipe -
       see initScheduleTab()), the flex algorithm can shrink summary itself
       to make room, changing its real rendered height. flex-shrink:0 locks
       it to its natural height no matter what its sibling asks for. */
    flex-shrink: 0;
    /* Own GPU compositing layer - see .schedule-nav's sticky rule below for
       why (this same title bar visibly drifted sideways during the
       schedule tab's active touch-drag handling without it; harmless on
       every other tab, which has no touch-drag of its own running). */
    transform: translateZ(0);
    -webkit-transform: translateZ(0);
    will-change: transform;
  }}
  /* A full-screen tab's own content is centered as a block within the
     available height instead of pinned to the top with empty space below
     when it's shorter than the screen - the content itself (table rows,
     bracket, etc.) keeps its natural size, only its vertical position
     within the screen changes. No overflow/min-height here on purpose:
     <main> is still the one real scroll container (see below) - giving
     this element its own overflow:auto too, combined with a plain
     justify-content:center, is a known flex/scroll pitfall where content
     taller than the box gets clipped at the top with no way to scroll to
     it. "safe center" falls back to top-alignment instead of centering
     once content actually overflows, avoiding that trap. */
  :root.tabs-mode details.tab-section.app-screen-active > .details-body {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: safe center;
  }}
  /* The schedule tab opts out of the centering above: its own
     .details-body gets an explicit min-height in JS (see
     initScheduleTab()'s fitToScreen()) specifically so a swipe can reach
     the empty space below a short/empty day's list - but that same empty
     space then made "safe center" visibly float the content at a
     different vertical position depending on how many games that day
     has, instead of staying anchored right under the tab title like every
     other tab already does with its own naturally-short content. */
  :root.tabs-mode details.tab-section.app-screen-active > .details-body:has(> .schedule-tab) {{
    justify-content: flex-start;
  }}
  .app-home {{ display: none; }}
  /* Positioned like a vertical ruler from 0 (bottom of the home screen) to
     100 (the line under the header): the summary button's own center sits
     at 66.66 (=33.34 measured from the top) and the rest of the tabs'
     center sits at 33.33 (=66.67 from the top) - both are absolutely
     positioned against .app-home and centered on that exact point via
     translateY(-50%), regardless of each block's own natural height. */
  :root.tabs-mode .app-home {{
    display: block;
    position: relative;
    flex: 1;
    min-height: 0;
  }}
  :root.tabs-mode .app-home.hidden {{ display: none; }}
  .app-home-big-btn {{
    display: block;
    width: 100%;
    padding: 18px 16px;
    border-radius: 10px;
    border: none;
    background: var(--accent);
    color: var(--card-bg);
    font-size: 1.0625rem;
    font-weight: 700;
    text-align: center;
    cursor: pointer;
  }}
  :root.tabs-mode .app-home-big-btn {{
    position: absolute;
    left: 0;
    right: 0;
    top: 25.34%;
    transform: translateY(-50%);
  }}
  :root.tabs-mode .app-home-tabs-group {{
    position: absolute;
    left: 0;
    right: 0;
    top: 58.67%;
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
  }}
  /* The tabs no longer expand in place (opening one goes full-screen
     instead), so the +/- disclosure icon and off-center title from the
     old inline-accordion look no longer make sense here. */
  :root.tabs-mode .app-home-tabs-group summary {{
    justify-content: center;
    text-align: center;
  }}
  :root.tabs-mode .app-home-tabs-group summary::after {{ display: none; }}

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
  <script>
    // GitHub Pages serves every page with Cache-Control: max-age=600, so a
    // page opened again within 10 minutes of a new deploy can silently show
    // stale content - no error, just the old version, easy to mistake for a
    // broken push. This checks the CURRENT page's own URL again, bypassing
    // any cache (cache: "no-store" plus a cache-busting query param, belt
    // and suspenders), and compares its app-version meta tag against the
    // one already loaded - each dated brief page carries its own version
    // (set at render time), not one shared across the whole site, so a demo
    // page built yesterday is never considered "stale" just because some
    // other page was rebuilt today. A real mismatch means a newer build of
    // THIS exact page exists, so it reloads once, cache-busted - the
    // reloaded page runs this same check again and finds no mismatch (it
    // just fetched the true latest version), so this can't loop. Fails
    // completely silently (offline, blocked request, whatever) - never
    // blocks or breaks the page that's already showing.
    (function checkForNewVersion() {{
      var current = document.querySelector('meta[name="app-version"]');
      if (!current) return;
      fetch(location.pathname + "?_v=" + Date.now(), {{ cache: "no-store" }})
        .then(function(res) {{ return res.text(); }})
        .then(function(text) {{
          var match = text.match(/<meta name="app-version" content="([^"]*)"/);
          if (match && match[1] && match[1] !== current.content) {{
            location.href = location.pathname + "?_r=" + Date.now();
          }}
        }})
        .catch(function() {{}});
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
            <a class="a11y-link-btn" href="mailto:ojbar30@gmail.com?subject=%D7%A4%D7%A0%D7%99%D7%99%D7%94+%D7%9C%D7%90%D7%AA%D7%A8+FULL+COURT:+%D7%A0%D7%95%D7%A9%D7%90+%D7%94%D7%A4%D7%A0%D7%99%D7%99%D7%94&body=%D7%AA%D7%95%D7%9B%D7%9F%20%D7%94%D7%A4%D7%A0%D7%99%D7%94%3A%0A%0A%D7%A6%D7%99%D7%9C%D7%95%D7%9E%D7%99%20%D7%9E%D7%A1%D7%9A%3A%0A">ojbar30@gmail.com</a>
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

      <div class="beta-note">
        <span>גרסת בטא · <a href="demos.html">מעבר בין דמואים</a></span>
        <button type="button" class="manual-refresh-btn" onclick="manualRefresh()" aria-label="רענן את הדף">🔄</button>
      </div>
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

    (function initFitToWidth() {{
      // Scales an element to fill the real available width instead of a
      // fixed guess (which can overflow narrower phones sideways, or look
      // small on wider ones) - measures its true natural width at zoom:1,
      // then computes a zoom that's guaranteed to fit (capped so it never
      // gets absurdly large on a very narrow parent). Runs before the
      // pager init functions below so their own column-width measurements
      // already reflect the final zoomed size, not the pre-zoom one.
      function fit(el, maxScale) {{
        if (!el) return;
        el.style.zoom = 1;
        var parent = el.parentElement;
        if (!parent) return;
        var available = parent.clientWidth;
        var natural = el.scrollWidth;
        if (!natural || !available) return;
        var scale = Math.min(available / natural, maxScale);
        if (scale > 0.05) {{ el.style.zoom = scale; }}
      }}

      // The Cup bracket used to be scaled here too, but it shares the exact
      // same column width (146px) and viewport constraint (max-width:316px)
      // as the playoff bracket's own pager - which was never scaled and
      // fits fine - so there was never actually a real overflow reason for
      // it to be smaller. Removed entirely (not just left unused) since it
      // was also the whole source of a long chain of zoom-related pager
      // bugs (see initCupBracketPager()) - simplest fix once the real
      // problem (it never needed shrinking to begin with) was clear.
      fit(document.querySelector(".play-in-bracket"), 1.25);
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
      // The playoff bracket's pager: all 3 stops pan a continuous strip
      // per conference (see _bracket_strip_html) plus the shared
      // round-name header, all moving together by exactly one column's
      // real measured width, so a round shared between two adjacent
      // stops (e.g. Conf. Semis, visible at both stops) is the same
      // element throughout, never two overlapping copies mid-transition.
      // Stop 2 isn't special-cased at all - it just happens to land on
      // the West strip's 4th column, which is where the shared NBA
      // Finals match is embedded as real content, revealed by the same
      // pan as everything else. Only the connector line joining it to
      // both Conf. Finals boxes is positioned separately (see
      // positionFinalsConnector below), toggled by the data-step
      // attribute kept in sync here.
      var wrap = document.querySelector(".bracket-pager");
      if (!wrap) return;

      var step = parseInt(wrap.getAttribute("data-step"), 10) || 0;
      var maxStep = 2;
      var tracks = Array.prototype.slice.call(wrap.querySelectorAll(".strip-track"));
      var prevBtn = wrap.querySelector(".pager-prev");
      var nextBtn = wrap.querySelector(".pager-next");

      function unitShift() {{
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

      // The Finals track (see _bracket_nba_finals_track_html) is already
      // panned in perfect sync for free - it's just another ".strip-track"
      // the tracks[] query above already picked up. All that's left is
      // giving its wrapper a vertical position, and drawing the connecting
      // line, neither of which can be done from percentages alone: they
      // have to span exactly from the top edge of the West conference's
      // Conf. Finals box to the bottom edge of the East one, which varies
      // by phone/text size. The connector's left tracks those boxes' real
      // right edge plus the same 16px gap .bracket-pair leaves before its
      // own connecting line (same distance-0-into-the-next-box math as
      // every other round). It's converted from the just-measured
      // on-screen position back to the same untransformed reference frame
      // the real tracks use (current position + the shift already applied
      // = where it'd sit at step 0), then folded into the same tracks[]
      // array setTracks() already pans - from then on it gets the exact
      // same transform as everything else, every time setTracks() runs
      // (including mid-drag), never re-measured again unless the layout
      // itself changes (resize).
      function positionFinalsConnector() {{
        var connector = wrap.querySelector(".nba-finals-connector");
        var finalsWrap = wrap.querySelector(".nba-finals-track-wrap");
        var strips = wrap.querySelector(".bracket-pager-strips");
        var finalBoxes = wrap.querySelectorAll(".bracket-final-conf .bracket-match");
        if (!connector || !finalsWrap || !strips || finalBoxes.length < 2) return;
        var topBox = finalBoxes[0];
        var bottomBox = finalBoxes[finalBoxes.length - 1];
        var stripsRect = strips.getBoundingClientRect();
        var topRect = topBox.getBoundingClientRect();
        var bottomRect = bottomBox.getBoundingClientRect();
        if (!topRect.height || !bottomRect.height) return;
        var top = topRect.top - stripsRect.top;
        var height = bottomRect.bottom - topRect.top;
        finalsWrap.style.top = top + "px";
        finalsWrap.style.height = height + "px";
        var currentShift = step * unitShift();
        connector.style.top = top + "px";
        connector.style.height = height + "px";
        connector.style.left = (topRect.right - stripsRect.left + 16 + currentShift) + "px";
        connector.style.transform = "translateX(-" + currentShift + "px)";
        if (tracks.indexOf(connector) === -1) tracks.push(connector);
      }}

      function render(animate) {{
        wrap.setAttribute("data-step", step);
        setTracks(step * unitShift(), animate);
        prevBtn.disabled = step === 0;
        nextBtn.disabled = step === maxStep;
      }}

      function goTo(newStep) {{
        step = Math.max(0, Math.min(newStep, maxStep));
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
        if (startX === null) return;
        var dx = e.touches[0].clientX - startX;
        var dy = e.touches[0].clientY - startY;
        if (!dragging && Math.abs(dx) < Math.abs(dy)) return;
        dragging = true;
        var unit = unitShift();
        var target = Math.max(0, Math.min(step * unit - dx, maxStep * unit));
        setTracks(target, false);
        wrap.setAttribute("data-step", Math.round(target / (unit || 1)));
      }}, {{ passive: true }});

      wrap.addEventListener("touchend", function(e) {{
        if (!dragging) {{ startX = null; startY = null; return; }}
        var dx = e.changedTouches[0].clientX - startX;
        var threshold = 40;
        if (dx < -threshold) {{ goTo(step + 1); }}
        else if (dx > threshold) {{ goTo(step - 1); }}
        else {{ render(true); }}
        startX = null;
        startY = null;
        dragging = false;
      }});

      window.addEventListener("resize", function() {{ render(false); positionFinalsConnector(); }});
      render(false);
      positionFinalsConnector();
    }})();

    (function initCupBracketPager() {{
      // Same custom drag mechanism as the playoff bracket's own pager
      // (initPlayoffBracketPager, see there for the general shape) -
      // JS-tracked touchmove following the finger 1:1, one controlled CSS
      // transition (0.35s ease) to settle at the end. This pager tried
      // real native scrolling instead for a while, specifically to dodge
      // bugs from combining a CSS transition on transform with
      // initFitToWidth()'s CSS zoom (confirmed directly on a real device
      // that the combination silently didn't work at all) - but that zoom
      // turned out to be unnecessary in the first place (this pager uses
      // the exact same column width/viewport constraint as the playoff
      // bracket's, which was never zoomed and fits fine) and was removed
      // entirely, which removes the actual reason the transition-based
      // approach didn't work here. Back to the same mechanism as playoff,
      // now that the thing that broke it is gone. The column width (146)
      // and gap (24, see .strip-track/.bracket-column above) are used
      // directly rather than measured, since they're fixed, authored CSS
      // values, not something that varies per device.
      var wrap = document.querySelector(".cup-bracket-pager");
      if (!wrap) return;

      var tracks = Array.prototype.slice.call(wrap.querySelectorAll(".strip-track"));
      if (!tracks.length) return;

      var maxStep = 1;
      var step = parseInt(wrap.getAttribute("data-step"), 10) || 0;
      var prevBtn = wrap.querySelector(".pager-prev");
      var nextBtn = wrap.querySelector(".pager-next");

      function unitShift() {{
        return 146 + 24; // .bracket-column's width + .strip-track's gap
      }}

      function setTracks(px, animate) {{
        tracks.forEach(function(track) {{
          track.style.transition = animate ? "transform 0.35s ease" : "none";
          track.style.transform = "translateX(-" + px + "px)";
        }});
      }}

      function render(animate) {{
        setTracks(step * unitShift(), animate);
        prevBtn.disabled = step === 0;
        nextBtn.disabled = step === maxStep;
      }}

      function goTo(newStep) {{
        step = Math.max(0, Math.min(newStep, maxStep));
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
        if (startX === null) return;
        var dx = e.touches[0].clientX - startX;
        var dy = e.touches[0].clientY - startY;
        if (!dragging && Math.abs(dx) < Math.abs(dy)) return;
        dragging = true;
        var unit = unitShift();
        var target = Math.max(0, Math.min(step * unit - dx, maxStep * unit));
        setTracks(target, false);
      }}, {{ passive: true }});

      wrap.addEventListener("touchend", function(e) {{
        if (!dragging) {{ startX = null; startY = null; return; }}
        var dx = e.changedTouches[0].clientX - startX;
        var threshold = 40;
        if (dx < -threshold) {{ goTo(step + 1); }}
        else if (dx > threshold) {{ goTo(step - 1); }}
        else {{ render(true); }}
        startX = null;
        startY = null;
        dragging = false;
      }});

      window.addEventListener("resize", function() {{ render(false); }});
      // Transform doesn't have the "no-op while hidden" problem scrollTo()
      // had (it's just a style property, applies regardless of visibility)
      // - but centerVertically() below still needs a real, settled layout
      // to measure, so this stays for that. A native "toggle" listener
      // doesn't catch tabs-mode's own show/hide (its <details> stays
      // open="true" throughout, promoted via class changes instead - see
      // initAppHome()); IntersectionObserver didn't fire at all when
      // checked directly in this environment. A MutationObserver on the
      // class attribute did fire correctly, so that's what's used: on any
      // class change, re-run render()/centerVertically() if the element
      // now actually has real size (still nothing meaningful to measure
      // while it's hidden).
      // This bracket is short enough that it doesn't fill the tab's full
      // screen height, and .details-body's own flex-grow (which should
      // make justify-content:safe center vertically center it, the same
      // way every other tab already centers its own content) doesn't
      // actually stretch to the available height here specifically -
      // confirmed directly, not assumed: forcing flex-grow as high as 999
      // still left it at its own content height, something specific to
      // this <details>-based flex container that wasn't worth chasing
      // further. Centers it directly instead: measured space above the
      // pager (the summary bar) and below (the rest of the screen), pushed
      // down by half the difference.
      function centerVertically() {{
        if (!detailsEl) return;
        var content = wrap.querySelector(":scope > .cup-bracket-content");
        if (!content) return;
        var summary = detailsEl.querySelector(":scope > summary");
        var summaryHeight = summary ? summary.getBoundingClientRect().height : 0;
        // The round-name header (Quarterfinals/Semifinals/Championship) is
        // content's previous sibling - kept out of the centering entirely
        // (see _build_cup_bracket_html) so it stays locked directly under
        // the tab title at every step, rather than drifting up/down with
        // however tall the bracket happens to be at that step.
        var header = content.previousElementSibling;
        var headerHeight = header ? header.getBoundingClientRect().height : 0;
        var available = detailsEl.getBoundingClientRect().height - summaryHeight - headerHeight;
        var contentHeight = content.getBoundingClientRect().height;
        var offset = Math.max(0, (available - contentHeight) / 2);
        content.style.marginTop = offset + "px";
      }}

      var detailsEl = wrap.closest("details");
      if (detailsEl && window.MutationObserver) {{
        var classObserver = new MutationObserver(function() {{
          if (wrap.getBoundingClientRect().width > 0) {{
            render(false);
            centerVertically();
            // The tab's own reveal (showSection()) isn't instant - height
            // measured at the moment this class change first fires can
            // still reflect a mid-transition size, not the settled one, so
            // this is re-measured once more a beat later to catch it.
            setTimeout(centerVertically, 300);
          }}
        }});
        classObserver.observe(detailsEl, {{ attributes: true, attributeFilter: ["class"] }});
      }}
      window.addEventListener("resize", centerVertically);
      render(false);
      centerVertically();
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

    (function initAppHome() {{
      // Deliberately NOT gated on standalone (display-mode) - a first-time
      // visitor in a regular mobile browser tab is exactly who needs to see
      // this to want to install at all; gating the app-like UI behind
      // already being installed meant nobody ever saw the thing that would
      // have convinced them to install it. Narrow-viewport only (not
      // desktop) - this layout is phone-shaped, not a browser-chrome check.
      var narrow = window.matchMedia("(max-width: 480px)").matches;
      if (!narrow) return;

      var main = document.querySelector("main");
      var summaryDiv = main.querySelector(":scope > .summary");
      var sections = Array.prototype.slice.call(main.querySelectorAll(":scope > details.tab-section"));
      if (sections.length < 1) return;

      document.documentElement.classList.add("tabs-mode");

      var home = document.createElement("div");
      home.className = "app-home";

      // The rest of the tabs live inside their own grouped block, visually
      // separate from the summary button - one big highlighted tab plus a
      // shared group underneath, rather than a flat list of same-weight
      // rows.
      var tabsGroup = document.createElement("div");
      tabsGroup.className = "app-home-tabs-group";

      // Returning home always re-collects every section back into the
      // group (in their original order) and clears whichever one, if any,
      // was promoted to a full screen - safe to call unconditionally from
      // any state (header tap, the summary/a section's own back arrow).
      function showHome() {{
        home.classList.remove("hidden");
        if (summaryDiv) summaryDiv.classList.remove("app-screen-active");
        sections.forEach(function(section) {{
          section.classList.remove("app-screen-active");
          section.open = false;
          tabsGroup.appendChild(section);
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
        tabsGroup.appendChild(section);
      }});
      home.appendChild(tabsGroup);

      main.insertBefore(home, main.firstChild);
    }})();

    (function initScheduleTab() {{
      // The season schedule browser (see _build_schedule_html) - a single
      // flat game list embedded as JSON, grouped into Israel-calendar days
      // and paged entirely here in JS. "Today" is resolved to the real
      // viewer's today at render() time below, not baked in at page-
      // generation time, since the same static page keeps being viewed for
      // as long as it's the latest brief.
      var wrap = document.querySelector(".schedule-tab");
      if (!wrap) return;
      var dataEl = wrap.querySelector(".schedule-data");
      var games;
      try {{
        games = JSON.parse(dataEl.textContent);
      }} catch (e) {{
        return;
      }}
      var label = wrap.querySelector(".schedule-date-label");
      var gamesEl = wrap.querySelector(".schedule-games");
      var calEl = wrap.querySelector(".schedule-calendar");
      var calToggle = wrap.querySelector(".schedule-cal-toggle");
      // Named by screen position (left/right), not prev/next - the button
      // that goes to the previous day sits on the right (glyph '›'), the
      // one that goes to the next day sits on the left (glyph '‹'), by
      // request - the opposite of what the class names ("schedule-prev"/
      // "schedule-next", left as-is) would suggest.
      var leftBtn = wrap.querySelector(".schedule-prev");
      var rightBtn = wrap.querySelector(".schedule-next");
      var IL_TZ = "Asia/Jerusalem";
      var WEEKDAYS = ["יום ראשון", "יום שני", "יום שלישי", "יום רביעי", "יום חמישי", "יום שישי", "יום שבת"];
      var DOW_SHORT = ["א", "ב", "ג", "ד", "ה", "ו", "ש"];
      var MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"];

      function ilDateKey(isoUtc) {{
        return new Date(isoUtc).toLocaleDateString("en-CA", {{ timeZone: IL_TZ }});
      }}
      function ilTimeStr(isoUtc) {{
        return new Date(isoUtc).toLocaleTimeString("he-IL", {{
          timeZone: IL_TZ, hour: "2-digit", minute: "2-digit", hour12: false
        }});
      }}
      // "en-CA" gives a plain YYYY-MM-DD string directly, so day keys sort
      // correctly as plain strings with no separate date-parsing step.
      // data-simulated-today (demo fixtures only - see _build_schedule_html)
      // overrides the real live date, so an old demo still opens somewhere
      // inside its own frozen game data instead of always falling back to
      // "season's over" once real time has moved past it.
      function todayKey() {{
        return wrap.dataset.simulatedToday || new Date().toLocaleDateString("en-CA", {{ timeZone: IL_TZ }});
      }}
      function addDays(key, delta) {{
        var parts = key.split("-").map(Number);
        // Noon, not midnight - keeps this away from any DST-transition edge
        // where "midnight" itself doesn't exist or repeats in a local zone.
        var d = new Date(parts[0], parts[1] - 1, parts[2], 12);
        d.setDate(d.getDate() + delta);
        return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
      }}
      function formatLabel(key) {{
        var parts = key.split("-").map(Number);
        var d = new Date(parts[0], parts[1] - 1, parts[2], 12);
        return WEEKDAYS[d.getDay()] + ", " + String(parts[2]).padStart(2, "0") + "." + String(parts[1]).padStart(2, "0") + "." + parts[0];
      }}
      function gameUrl(g) {{
        return "https://www.nba.com/game/" + g.away_tricode.toLowerCase() + "-vs-" + g.home_tricode.toLowerCase() + "-" + g.game_id;
      }}

      // The "rich" row - same look as the old, now-removed results tab
      // (.team-record/.ot-tag/.game-sub/.game-links) - for a game this
      // brief actually fetched box scores/highlights for (see g.rich, set
      // by fetch.fetch_for_date's schedule-enrichment step). Mirrors that
      // Python code's logic exactly, just in JS since this renders client-
      // side on demand.
      function renderRichRow(g) {{
        var r = g.rich;
        var awayWon = g.is_final && g.away_score > g.home_score;
        var homeWon = g.is_final && g.home_score > g.away_score;
        // Season record next to the team code - not during Playoffs/Play-In,
        // where the series score / seed context (the caption below) is the
        // relevant number instead.
        var showRecord = !r.po_round && !r.is_play_in;
        function teamSpan(tricode, wins, losses, isWinner) {{
          var record = (showRecord && wins != null && losses != null)
            ? '<span class="team-record">' + wins + '-' + losses + '</span>' : '';
          return '<span class="team' + (isWinner ? " winner" : "") + '">' + tricode + record + '</span>';
        }}
        // g.is_final can be false with rich data still attached - the
        // comprehensive demo attaches next-game team records (see
        // enrich_full_history()'s next_date handling) to the single game
        // night right after its own simulated "today", where the real score
        // already exists in the underlying data (it's real history) but
        // showing it would spoil a game the viewer "hasn't gotten to yet".
        // Same score-vs-tipoff-time branch the plain (non-rich) row below
        // uses, so an unplayed rich row looks the same as an unplayed plain
        // one - only the extra record/context makes it "rich".
        var mid = g.is_final
          ? '<span class="score' + (awayWon ? " winner" : "") + '">' + g.away_score + '</span>' +
            '<span class="score">–</span>' +
            '<span class="score' + (homeWon ? " winner" : "") + '">' + g.home_score + '</span>'
          : '<span class="score time">' + ilTimeStr(g.tipoff_utc) + '</span>';
        var otCount = (r.period || 4) - 4;
        var otHtml = g.is_final && otCount > 0
          ? '<span class="ot-tag">' + (otCount === 1 ? "OT" : otCount + "OT") + '</span>' : '';
        var block = '<div class="game-row">' +
          teamSpan(g.away_tricode, r.away_wins, r.away_losses, awayWon) +
          mid +
          teamSpan(g.home_tricode, r.home_wins, r.home_losses, homeWon) +
          otHtml +
          '</div>';
        if (r.po_round) {{
          block += '<div class="game-sub">' + (r.series_game_number || "") + " · " + (r.series_text || "") + '</div>';
        }} else if (r.cup_subtype) {{
          block += '<div class="game-sub">NBA Cup · ' + (r.cup_sub_label || "") + '</div>';
        }} else if (r.is_play_in && r.series_text) {{
          block += '<div class="game-sub">Play-In · ' + r.series_text + '</div>';
        }}
        var links = '<a class="game-link" href="' + gameUrl(g) + '" target="_blank" rel="noopener">דף המשחק</a>';
        if (g.is_final && r.highlight_url) {{
          links += '<a class="game-link" href="' + r.highlight_url + '" target="_blank" rel="noopener">תקציר</a>';
        }}
        block += '<div class="game-links">' + links + '</div>';
        return '<div class="game-block">' + block + '</div>';
      }}

      var byDate = {{}};
      games.forEach(function(g) {{
        var key = ilDateKey(g.tipoff_utc);
        (byDate[key] = byDate[key] || []).push(g);
      }});
      var sortedKeys = Object.keys(byDate).sort();
      var minKey = sortedKeys[0];
      var maxKey = sortedKeys[sortedKeys.length - 1];

      function pickInitialKey() {{
        var today = todayKey();
        if (byDate[today] || !sortedKeys.length) return today;
        // No games today - default to the nearest upcoming gameday instead
        // of an empty screen.
        for (var i = 0; i < sortedKeys.length; i++) {{
          if (sortedKeys[i] > today) return sortedKeys[i];
        }}
        // No games left ahead either (the season's over) - fall back to the
        // most recent one so there's still something to look at.
        return maxKey;
      }}

      var currentKey = pickInitialKey();

      function render() {{
        label.textContent = formatLabel(currentKey);
        rightBtn.disabled = !!minKey && currentKey <= minKey; // yesterday
        leftBtn.disabled = !!maxKey && currentKey >= maxKey; // tomorrow

        var dayGames = (byDate[currentKey] || []).slice().sort(function(a, b) {{
          return a.tipoff_utc < b.tipoff_utc ? -1 : a.tipoff_utc > b.tipoff_utc ? 1 : 0;
        }});
        if (!dayGames.length) {{
          gamesEl.innerHTML = '<p dir="rtl" style="color:var(--text-muted); font-size:0.875rem; text-align:center;">אין משחקים ביום זה.</p>';
          return;
        }}
        gamesEl.innerHTML = dayGames.map(function(g) {{
          if (g.rich) return renderRichRow(g);
          var awayWon = g.is_final && g.away_score > g.home_score;
          var homeWon = g.is_final && g.home_score > g.away_score;
          var mid = g.is_final
            ? '<span class="score' + (awayWon ? " winner" : "") + '">' + g.away_score + '</span>' +
              '<span class="score">–</span>' +
              '<span class="score' + (homeWon ? " winner" : "") + '">' + g.home_score + '</span>'
            : '<span class="score time">' + ilTimeStr(g.tipoff_utc) + '</span>';
          return '<div class="game-block"><div class="game-row">' +
            '<span class="team' + (awayWon ? " winner" : "") + '">' + g.away_tricode + '</span>' +
            mid +
            '<span class="team' + (homeWon ? " winner" : "") + '">' + g.home_tricode + '</span>' +
            '</div><div class="game-links"><a class="game-link" href="' + gameUrl(g) + '" target="_blank" rel="noopener">דף המשחק</a></div></div>';
        }}).join("");
      }}

      // Same animated slide as a swipe (see swipeTo() below), not an
      // instant re-render - by request, so a button tap feels the same as
      // a swipe.
      // Guarded on calOpen (declared further down, but var-hoisted and
      // already set by the time either of these can actually fire from a
      // real click) - the day arrows have no reason to do anything while
      // the calendar is showing, by request.
      // Same two buttons, repurposed while the calendar is open (see
      // openCalendar()) - a month step instead of a day, same right=back/
      // left=forward convention, same animated feel (monthSwipeTo() mirrors
      // swipeTo()) so it reads as the same control either way.
      rightBtn.addEventListener("click", function() {{ if (calOpen) monthSwipeTo(-1); else swipeTo(-1); }});
      leftBtn.addEventListener("click", function() {{ if (calOpen) monthSwipeTo(1); else swipeTo(1); }});

      // Month-at-a-glance jump-to-date view (backlog item 7) - a plain grid
      // for whichever month currentKey is in when opened, days with games
      // marked by a small orange badge showing the count, tapping one jumps
      // straight there instead of stepping day by day. Bounded to the
      // real min/max months this season actually has data for, not a fixed
      // Oct-June range - a real season's data naturally falls in that
      // window anyway, and this way it's never wrong for an odd schedule.
      var calMonthKey = null; // "YYYY-MM", set when the calendar is opened
      var calOpen = false;

      function monthKeyOf(dayKey) {{ return dayKey.slice(0, 7); }}

      function clampMonthKey(mk) {{
        var lo = monthKeyOf(minKey), hi = monthKeyOf(maxKey);
        if (mk < lo) return lo;
        if (mk > hi) return hi;
        return mk;
      }}

      function shiftMonthKey(mk, delta) {{
        var parts = mk.split("-").map(Number);
        var d = new Date(parts[0], parts[1] - 1 + delta, 1);
        return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
      }}

      // No separate arrow row of its own (there was one at first - by
      // request, the calendar reuses the exact same nav-row arrows/label
      // instead of a second, redundant set): while open, leftBtn/rightBtn
      // step a month and the label shows "MONTH YEAR" - see changeMonth()/
      // openCalendar() below.
      function renderCalendar() {{
        var parts = calMonthKey.split("-").map(Number);
        var year = parts[0], month = parts[1]; // 1-indexed month
        var first = new Date(year, month - 1, 1);
        var daysInMonth = new Date(year, month, 0).getDate();
        // getDay() is 0=Sunday already matching DOW_SHORT's own order, and
        // the grid's first column (rightmost, dir=rtl) is Sunday too - no
        // day-of-week rotation needed for the leading blank cells.
        var leadingBlanks = first.getDay();
        var today = todayKey();

        label.textContent = MONTHS[month - 1] + " " + year;
        rightBtn.disabled = calMonthKey <= monthKeyOf(minKey);
        leftBtn.disabled = calMonthKey >= monthKeyOf(maxKey);

        var dow = DOW_SHORT.map(function(d) {{ return '<div class="schedule-calendar-dow">' + d + '</div>'; }}).join("");

        var cells = [];
        for (var i = 0; i < leadingBlanks; i++) {{
          cells.push('<div class="schedule-calendar-day empty"></div>');
        }}
        for (var day = 1; day <= daysInMonth; day++) {{
          var dayKey = year + "-" + String(month).padStart(2, "0") + "-" + String(day).padStart(2, "0");
          var count = (byDate[dayKey] || []).length;
          var cls = "schedule-calendar-day" + (count ? " has-games" : "") + (dayKey === today ? " is-today" : "");
          var badge = count ? '<span class="cal-count">' + count + '</span>' : "";
          cells.push('<button type="button" class="' + cls + '" data-day-key="' + dayKey + '"' +
            (count ? "" : " disabled") + '>' + day + badge + '</button>');
        }}

        calEl.innerHTML = '<div class="schedule-calendar-grid">' + dow + cells.join("") + '</div>';

        Array.prototype.forEach.call(calEl.querySelectorAll(".has-games"), function(cell) {{
          cell.addEventListener("click", function() {{
            currentKey = cell.dataset.dayKey;
            closeCalendar();
            render();
          }});
        }});
      }}

      // Single-step month change, shared by the top arrows and
      // monthSwipeTo() below (which just wraps this with the slide
      // animation) - direction 1 = next month, -1 = previous.
      function changeMonth(direction) {{
        var next = clampMonthKey(shiftMonthKey(calMonthKey, direction));
        if (next === calMonthKey) return false;
        calMonthKey = next;
        return true;
      }}

      function openCalendar() {{
        calMonthKey = clampMonthKey(monthKeyOf(currentKey));
        calOpen = true;
        gamesEl.hidden = true;
        calEl.hidden = false;
        renderCalendar();
      }}
      function closeCalendar() {{
        calOpen = false;
        calEl.hidden = true;
        gamesEl.hidden = false;
        render();
      }}
      calToggle.addEventListener("click", function() {{
        if (calOpen) closeCalendar(); else openCalendar();
      }});

      // Swipe, same spirit as the bracket pagers (initPlayoffBracketPager/
      // initCupBracketPager) - finger-follow during the drag, then either
      // commit to the next/prev day or snap back. Not the same mechanism
      // underneath, though: the brackets pan one continuous pre-built strip,
      // but here each day's list is a different height and is only built on
      // demand, so there's no adjacent panel to pan onto - instead the
      // current day's card slides out, the new day's content gets built,
      // and it slides in from the matching side. Same felt gesture, applied
      // to swapped content instead of a shared track.
      // Deliberately no preventDefault() here, and both touchmove/touchend
      // are {{ passive: true }} - matching the bracket pagers exactly (they
      // never had one either, and never had this problem). An earlier
      // version called preventDefault() on drag to suppress a theoretical
      // ghost-click on whatever the swipe started over; turned out to be
      // the actual cause of a real, repeatedly-confirmed bug instead (the
      // sticky tab title visibly jumping mid-swipe on iOS) - isolated by
      // finding the arrow buttons (same swipeTo() animation, no touch
      // events, no preventDefault) never jump, while every touch-based
      // variant did regardless of which element the listener was bound to.
      // touch-action:pan-y (see the .schedule-tab CSS) is what actually
      // blocks native horizontal panning; preventDefault was redundant
      // belt-and-suspenders that cost more than it protected against.
      // .details-body (not just .schedule-tab, and not the whole <details>
      // - that also contains the sticky summary, which has its own click-
      // to-go-home handler) is used so a swipe still reaches the empty
      // space below a short day's list; that needs its own real min-height
      // via fitToScreen() below since .details-body doesn't reliably
      // stretch to fill the screen here (same <details>-as-flex-child quirk
      // as the Cup bracket) despite its own CSS flex:1.
      // Right-to-left date order: swiping right (finger moves right, dx>0)
      // goes to the next day, swiping left goes to the previous - matching
      // how the day label itself reads (today on the right, moving right
      // steps forward), the opposite of a plain LTR carousel.
      var detailsEl = wrap.closest("details.tab-section");
      var touchArea = wrap.closest(".details-body") || wrap;

      function fitToScreen() {{
        if (!detailsEl) return;
        var summary = detailsEl.querySelector(":scope > summary");
        var summaryHeight = summary ? summary.getBoundingClientRect().height : 0;
        var available = detailsEl.getBoundingClientRect().height - summaryHeight;
        if (available > 0) touchArea.style.minHeight = available + "px";
        // .schedule-nav's own sticky top offset (see its CSS) - measured
        // instead of hardcoded, since the title bar's real height isn't a
        // fixed constant (font size / a11y zoom / RTL rendering can all
        // shift it slightly).
        wrap.style.setProperty("--schedule-nav-top", summaryHeight + "px");
      }}

      var startX = null;
      var startY = null;
      var dragging = false;

      touchArea.addEventListener("touchstart", function(e) {{
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        dragging = false;
      }}, {{ passive: true }});

      // No live 1:1 finger-follow during the drag itself (that's the one
      // remaining difference from a plain arrow-button tap, which never
      // jumps - narrowing it down after touch-area scope, touch-action, and
      // preventDefault all turned out not to be it). touchmove here only
      // tracks direction, exactly like the swipe detection already used for
      // the arrows; the actual animation is the same swipeTo() a button
      // click already triggers, fired once on touchend.
      touchArea.addEventListener("touchmove", function(e) {{
        if (startX === null) return;
        var dx = e.touches[0].clientX - startX;
        var dy = e.touches[0].clientY - startY;
        if (!dragging && Math.abs(dx) < Math.abs(dy)) return;
        dragging = true;
      }}, {{ passive: true }});

      touchArea.addEventListener("touchend", function(e) {{
        if (!dragging) {{ startX = null; startY = null; return; }}
        var dx = e.changedTouches[0].clientX - startX;
        var threshold = 40;
        startX = null;
        startY = null;
        dragging = false;

        // While the calendar is open, the exact same swipe here steps a
        // month instead of a day - the day-swipe/arrows only make sense
        // for the day list underneath, which isn't even visible right now.
        if (calOpen) {{
          if (dx >= threshold) {{ monthSwipeTo(1); }}
          else if (dx <= -threshold) {{ monthSwipeTo(-1); }}
          return;
        }}
        if (dx >= threshold) {{ swipeTo(1); }}
        else if (dx <= -threshold) {{ swipeTo(-1); }}
      }}, {{ passive: true }});

      // Same shape as swipeTo() (see below) but for a month step instead of
      // a day - direction 1 = next month, -1 = previous. Used for both the
      // swipe gesture and the (same, reused) top arrows while the calendar
      // is open, so a tap and a swipe feel identical - same visual language
      // as the day view.
      function monthSwipeTo(direction) {{
        if (!changeMonth(direction)) return;
        calEl.style.transition = "transform 0.2s ease, opacity 0.2s ease";
        calEl.style.transform = "translateX(" + (direction * 60) + "px)";
        calEl.style.opacity = "0";
        window.setTimeout(function() {{
          renderCalendar();
          calEl.style.transition = "none";
          calEl.style.transform = "translateX(" + (direction * -60) + "px)";
          calEl.style.opacity = "0";
          void calEl.offsetWidth;
          calEl.style.transition = "transform 0.2s ease, opacity 0.2s ease";
          calEl.style.transform = "translateX(0)";
          calEl.style.opacity = "1";
        }}, 200);
      }}

      // direction 1 = swiped right, toward the next day; -1 = swiped left,
      // toward the previous. The exit continues further the same way the
      // finger just dragged it (matching the live drag-follow above), and
      // the new content enters from the opposite side.
      function swipeTo(direction) {{
        currentKey = addDays(currentKey, direction);
        gamesEl.style.transition = "transform 0.2s ease, opacity 0.2s ease";
        gamesEl.style.transform = "translateX(" + (direction * 60) + "px)";
        gamesEl.style.opacity = "0";
        window.setTimeout(function() {{
          render();
          gamesEl.style.transition = "none";
          gamesEl.style.transform = "translateX(" + (direction * -60) + "px)";
          gamesEl.style.opacity = "0";
          void gamesEl.offsetWidth; // force reflow so the next line animates
          gamesEl.style.transition = "transform 0.2s ease, opacity 0.2s ease";
          gamesEl.style.transform = "translateX(0)";
          gamesEl.style.opacity = "1";
        }}, 200);
      }}

      window.addEventListener("resize", fitToScreen);
      // The tab starts hidden (0 height), same reason the Cup bracket
      // pager needs this same pattern - re-measure once tabs-mode actually
      // promotes this <details> to the active full-screen tab.
      if (detailsEl && window.MutationObserver) {{
        new MutationObserver(fitToScreen).observe(detailsEl, {{ attributes: true, attributeFilter: ["class"] }});
      }}

      render();
      fitToScreen();
    }})();

    function manualRefresh() {{
      // A plain location.reload() still respects GitHub Pages' HTTP cache -
      // iOS in standalone mode especially can keep serving a cached response
      // for several minutes without even asking the server. A cache-busting
      // query param makes this a URL the cache has never seen, forcing a
      // genuine fetch every time.
      location.href = location.pathname + "?_r=" + Date.now();
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


def _build_schedule_html(season_schedule: list[dict], simulated_today: str | None = None) -> str:
    """
    A day-by-day season schedule browser: past days show final scores,
    future days show the tip-off time - one flat game list (see
    fetch.get_season_schedule) embedded as JSON and grouped/paged entirely
    client-side (see initScheduleTab() below), since "today" has to resolve
    to the viewer's own real today, not the day this page happened to be
    generated on - the same static page keeps getting viewed for as long as
    it's the latest brief (see render.save()). Grouping by calendar day is
    done in Israel time in JS too (Intl's timeZone support), not US Eastern,
    so a westward-tipping game after local midnight correctly lands on the
    next Israel day instead of staying lumped in with the earlier one.
    A game this brief actually fetched box scores/highlights for (see
    fetch.fetch_for_date's schedule-enrichment step) carries a "rich"
    sub-object (OT count, highlight/series/cup info, real season records) -
    initScheduleTab()'s renderRichRow() renders those the same way the old,
    now-removed results tab did (.team-record/.ot-tag/.game-sub/.game-links).
    Every other day's games - the vast majority, since that level of detail
    is only ever fetched for the one night the brief covers - don't carry
    "rich" and fall back to the plain score-or-tip-off-time row.

    simulated_today (YYYY-MM-DD) is demo-only: real briefs never set it, so
    initScheduleTab() falls through to the viewer's real live date exactly
    as before. Demo fixtures - frozen at whatever date they were written
    for, forever - set it so the tab still opens on a date that's actually
    inside that fixture's own game data instead of the real, ever-advancing
    "today" (which would just fall back to "season's over" for every old
    demo the moment real time moves past its data).
    """
    if not season_schedule:
        return '<p dir="rtl" style="color:var(--text-muted); font-size:0.875rem;">לוח התוצאות לא זמין כרגע.</p>'

    # "</" could otherwise prematurely close this <script> tag if it ever
    # appeared inside a team name/city string.
    payload = json.dumps(season_schedule, ensure_ascii=False).replace("</", "<\\/")
    sim_attr = f' data-simulated-today="{html.escape(simulated_today)}"' if simulated_today else ""
    return (
        f'<div class="schedule-tab"{sim_attr}>'
        '<div class="pager-nav schedule-nav">'
        '<button type="button" class="pager-arrow schedule-prev" aria-label="יום הבא">‹</button>'
        '<div class="schedule-date-label" dir="rtl"></div>'
        '<button type="button" class="pager-arrow schedule-next" aria-label="יום קודם">›</button>'
        '<button type="button" class="schedule-cal-toggle" aria-label="לוח שנה">📅</button>'
        "</div>"
        '<div class="schedule-calendar" dir="rtl" hidden></div>'
        '<div class="schedule-games"></div>'
        f'<script type="application/json" class="schedule-data">{payload}</script>'
        "</div>"
    )


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
        # A series still being played has no loser yet - dimming both teams
        # muted-gray (the "lost" look) reads as if the whole series were
        # already decided against both of them. Only once is_over is true
        # does the muted color mean anything (this team actually lost);
        # until then both sides get the plain "pending" look instead - no
        # bold (that's still reserved for the real, decided winner), but not
        # grayed out either.
        if not series["is_over"]:
            cls = " pending"
        elif team["wins"] == max_wins:
            cls = " winner"
        else:
            cls = ""
        seed = team.get("seed")
        seed_html = f'<span class="bracket-seed">{seed}</span>' if seed else ""
        return (
            f'<div class="bracket-team{cls}">'
            f'<span class="bracket-team-label">{seed_html}<span>{html.escape(team["tricode"])}</span></span>'
            f'<span class="bracket-score">{team["wins"]}</span></div>'
        )

    return '<div class="bracket-match">' + "".join(_team(t) for t in ordered) + "</div>"


_ROUND1_BRACKET_HALF_BY_SEED = {1: "A", 8: "A", 4: "A", 5: "A", 2: "B", 7: "B", 3: "B", 6: "B"}


def _series_winner(series: dict | None) -> dict | None:
    """The winning team of a finished series, or None if it's missing/still live."""
    if not series or not series.get("is_over"):
        return None
    max_wins = max(t["wins"] for t in series["teams"])
    return next((t for t in series["teams"] if t["wins"] == max_wins), None)


def _bracket_projected_series_match_html(slots: list[dict | None]) -> str:
    """
    One bracket cell built from up to 2 already-known winners instead of a
    real series object - for the gap between a round finishing and the API
    actually creating a series for the round after it (that only happens
    once its games start being played). Shows whichever side(s) are
    already decided (seed + tricode, no score yet - the series hasn't
    started) against TBD for whichever side isn't, instead of leaving the
    whole cell blank until the very first tipoff of the next round.
    """
    def _slot(team: dict | None) -> str:
        if team is None:
            return '<div class="bracket-team"><span>TBD</span></div>'
        seed = team.get("seed")
        seed_html = f'<span class="bracket-seed">{seed}</span>' if seed else ""
        # Same "pending" look as a series still being played (see
        # _bracket_series_html) - a known team waiting on a TBD opponent
        # hasn't lost anything either, so it gets the plain look, not muted
        # gray, and not the italic this whole cell's TBD styling would
        # otherwise inherit down onto it.
        return (
            '<div class="bracket-team pending">'
            f'<span class="bracket-team-label">{seed_html}<span>{html.escape(team["tricode"])}</span></span>'
            "</div>"
        )

    return '<div class="bracket-match bracket-match-tbd">' + "".join(_slot(t) for t in slots) + "</div>"


def _bracket_next_round_cell(next_round_series: dict | None, feeders: list[dict | None]) -> str:
    """
    One bracket cell for a round that hasn't started yet: the real series
    if the API has already created one (games are actually being played),
    otherwise projected from whichever feeder series are already decided -
    a known winner shows up immediately against TBD (or against the other
    known winner, if both feeders finished before this round's own games
    began), rather than the whole cell staying blank TBD-vs-TBD until the
    next round's first tipoff.
    """
    if next_round_series is not None:
        return _bracket_series_html(next_round_series)
    winners = [_series_winner(f) for f in feeders]
    if any(winners):
        return _bracket_projected_series_match_html(winners)
    return _bracket_series_html(None)


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
    One conference's three playoff rounds (1st Round -> Conf. Semifinals ->
    Conf. Finals), each returned as bare .bracket-round/.bracket-final
    content (no .bracket-column wrapper, no round-name label) - the round
    name is shown once in a shared header above both conferences instead of
    repeated per column (see _bracket_round_header_track), so this only
    needs to produce the matches themselves.
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
    semis_cells = [
        _bracket_next_round_cell(semis_by_half.get(half), _pad_series(round1_by_half[half], 2))
        for half in ("A", "B")
    ]
    semis_pair = f'<div class="bracket-pair bracket-pair-r2">{"".join(semis_cells)}</div>'
    semis_slots = [semis_by_half.get("A"), semis_by_half.get("B")]

    final_column = _bracket_next_round_cell(finals[0] if finals else None, semis_slots)

    return {
        "1st Round": f'<div class="bracket-round">{"".join(round1_pairs)}</div>',
        "Conf. Semifinals": f'<div class="bracket-round">{semis_pair}</div>',
        "Conf. Finals": f'<div class="bracket-round bracket-final bracket-final-conf">{final_column}</div>',
    }


def _finals_match_html(series: dict | None, conf_by_team: dict, projected: dict | None = None) -> str:
    """
    Finals-specific version of _bracket_series_html: same look as every
    other bracket cell (seed badge, no conference-color badge), but ordered
    by conference (West on top, East below) to match the West/East block
    order on the page above it, instead of by seed - seeds aren't
    comparable across conferences, so sorting by them wouldn't reliably put
    the same conference on top from one Finals to the next.

    `projected` (a {"West": team|None, "East": team|None} dict of each
    conference's already-decided Conf. Finals winner, see _series_winner)
    fills the gap between a Conf. Finals ending and the API actually
    creating an NBA Finals series (which only happens once its games start)
    - a known conference champion shows up immediately instead of the cell
    staying TBD-vs-TBD until Game 1 tips off.
    """
    if series is None:
        west = projected.get("West") if projected else None
        east = projected.get("East") if projected else None
        if west or east:

            def _slot(team: dict | None) -> str:
                if team is None:
                    return '<div class="bracket-team"><span>TBD</span></div>'
                seed = team.get("seed")
                seed_html = f'<span class="bracket-seed">{seed}</span>' if seed else ""
                return (
                    '<div class="bracket-team pending">'
                    f'<span class="bracket-team-label">{seed_html}<span>{html.escape(team["tricode"])}</span></span>'
                    "</div>"
                )

            return '<div class="bracket-match bracket-match-tbd">' + _slot(west) + _slot(east) + "</div>"
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
        # See _bracket_series_html's identical reasoning: a series still in
        # progress has no loser yet, so neither side gets the muted "lost"
        # look until is_over actually says one of them did.
        if not series["is_over"]:
            cls = " pending"
        elif team["wins"] == max_wins:
            cls = " winner"
        else:
            cls = ""
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


def _bracket_round_header_track(labels: list[str]) -> str:
    """
    The round name shown once, shared above both conferences, instead of
    repeated per column inside each conference's own strip - this track
    carries no bracket content, just labels, but it's included as one more
    ".strip-track" so initPlayoffBracketPager() pans it in perfect sync
    with the two real conference strips (same measured column width).
    """
    cols = "".join(f'<div class="bracket-column"><h4 class="bracket-round-label">{html.escape(l)}</h4></div>' for l in labels)
    return f'<div class="strip-viewport"><div class="strip-track">{cols}</div></div>'


def _bracket_strip_html(conf_label: str, columns: dict[str, str]) -> str:
    """
    One conference's full Round 1 -> Conf. Semis -> Conf. Finals bracket as
    a single continuous strip - initPlayoffBracketPager() pans a fixed
    viewport across this strip by exactly one column's width at a time, so
    a round shared between two stops (e.g. Conf. Semis, visible at both
    stop 0 and stop 1) is the same element throughout, it just slides from
    the trailing position to the leading one. Only 3 real columns (this
    strip has nothing of its own for stop 2 - the shared NBA Finals match
    lives in its own separate track, see _bracket_nba_finals_track_html) -
    panning past the end of a 3-column track at stop 2 just reveals plain
    background on the right half of the viewport, which is exactly what's
    wanted there.
    """
    track_html = "".join(f'<div class="bracket-column">{columns[r]}</div>' for r in _PLAYOFF_ROUNDS[:3])
    return (
        '<div class="bracket-conf-block">'
        f'<h4 class="sr-only">{html.escape(conf_label)}</h4>'
        f'<div class="strip-viewport"><div class="strip-track">{track_html}</div></div>'
        "</div>"
    )


def _bracket_nba_finals_track_html(
    finals_series: dict | None, conf_by_team: dict, projected: dict | None = None
) -> str:
    """
    The NBA Finals match as its own independent track - not part of either
    conference's strip (the Finals combine both, so there's nothing
    conference-specific to show per side). It's panned by the exact same
    transform as every other track (all ".strip-track"s are picked up
    uniformly by initPlayoffBracketPager()) and clipped by its own
    .strip-viewport, so - same as every other round - it only ever becomes
    visible by actually being panned into view, never a moment before.
    Its wrapper (.nba-finals-track-wrap) is absolutely positioned to span
    the live-measured range between the two conferences' Conf. Finals boxes
    (see positionFinalsConnector), so centering the match within it lands
    it at the true vertical middle between them, not squeezed into either
    conference's own much shorter row height.
    """
    match = _finals_match_html(finals_series, conf_by_team, projected)
    empties = '<div class="bracket-column"></div>' * 3
    track_html = empties + f'<div class="bracket-column"><div class="bracket-round bracket-final">{match}</div></div>'
    return f'<div class="nba-finals-track-wrap"><div class="strip-viewport"><div class="strip-track">{track_html}</div></div></div>'


def _build_combined_playoff_bracket_html(playoff_series: list[dict], games: list[dict]) -> str:
    """
    A single bracket covering the whole playoffs (both conferences, no
    separate tab per conference or for the Finals) - only two adjacent
    rounds are shown at a time, since a full 4-round bracket is too wide for
    mobile. All 3 stops are one continuous pan across a strip per
    conference (see _bracket_strip_html) plus the shared round-name header
    and the shared NBA Finals track (see _bracket_nba_finals_track_html),
    every track moving together by the same measured column width - stop 2
    isn't special-cased, the two conference strips just run out of real
    columns and show blank space while the Finals track's own 4th column
    (its only real one) comes into view. Defaults to whichever stop is
    relevant tonight: if tonight's games span more than one round (e.g. a
    1st Round Game 7 and a Conf. Semifinals Game 1 on the same night), the
    earliest round wins, since that series isn't fully resolved
    league-wide yet.
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
    projected_finalists = {
        conf: _series_winner(
            next((s for s in playoff_series if s.get("conference") == conf and s.get("round") == "Conf. Finals"), None)
        )
        for conf in ("West", "East")
    }

    round_header = _bracket_round_header_track(_PLAYOFF_ROUNDS)
    west_strip = _bracket_strip_html("מערב", columns_by_conf["West"])
    east_strip = _bracket_strip_html("מזרח", columns_by_conf["East"])
    finals_track = _bracket_nba_finals_track_html(finals_series, conf_by_team, projected_finalists)
    finals_connector = '<div class="nba-finals-connector"></div>'

    # The content itself (and everything around it) is forced dir="ltr" (see
    # _details_block) since it's mostly seed numbers/English round names, so
    # the pager's arrows follow plain left-to-right pagination convention:
    # prev (‹) sits physically on the left, next (›) on the right - not
    # RTL-mirrored, since the ambient direction here already isn't RTL.
    return (
        f'<div class="bracket-pager" data-step="{start_step}">'
        f'<div class="bracket-pager-strips">{round_header}{west_strip}{east_strip}{finals_track}{finals_connector}</div>'
        f"{_finals_champion_line(finals_series)}"
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
def _bracket_projected_match_html(teams: list[dict | None]) -> str:
    """
    One bracket cell for a not-yet-played Cup knockout game, built from
    whichever feeders are already decided (e.g. a Quarterfinal winner) -
    shows a known side without a score against TBD for whichever side
    isn't decided yet, instead of leaving the whole cell TBD until both
    feeders are done.
    """
    def _slot(team: dict | None) -> str:
        if team is None:
            return '<div class="bracket-team"><span>TBD</span></div>'
        return f'<div class="bracket-team pending">{_bracket_team_name_html(team)}</div>'

    return '<div class="bracket-match bracket-match-projected">' + "".join(_slot(t) for t in teams) + "</div>"

def _build_cup_bracket_html(cup_bracket: list[dict]) -> str:
    """
    Renders the Cup knockout bracket as a connected tree (QF -> SF ->
    Championship), paged two rounds at a time like the playoff bracket
    (see initCupBracketPager()) - a shared round-name header pans in sync
    with a single strip (there's only one bracket here, not split by
    conference the way playoffs is, so no per-conference strips needed).
    Always shows the full shape (4 QF / 2 SF / 1 Final slots) even early in
    the knockout stage. Anything not played yet is either a TBD placeholder
    (no feeders decided yet) or a "projected" matchup, showing whichever
    side(s) are already decided (e.g. one or both Quarterfinal winners in a
    pair) against TBD for whichever side isn't, instead of waiting for
    every feeder to finish before showing anything.
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
    projected_sf_by_conf: dict[str, list[dict | None]] = {}
    for conf in ("West", "East"):
        conf_qf_games = qf_by_conf.get(conf, [])
        padded_qf_games = _pad_series(conf_qf_games, 2)
        # Wrapped in .bracket-conf-block (the same per-conference spacing
        # class the playoff bracket uses) purely for its vertical margin -
        # without it, West's and East's pairs sit directly stacked with
        # only .bracket-round's own small gap between them, so the whole
        # tree renders noticeably shorter than the playoff bracket's and
        # ends up looking like it's floating in half the screen instead of
        # filling it, even though both show the same 3 rounds.
        qf_pairs.append(
            '<div class="bracket-conf-block">'
            f'<div class="bracket-pair">'
            f'{"".join(_bracket_match_html(g) for g in padded_qf_games)}'
            "</div></div>"
        )
        qf_winners = [g["winner"] if g else None for g in padded_qf_games]
        if any(qf_winners):
            projected_sf_by_conf[conf] = qf_winners

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
        if any(final_teams):
            final_column = _bracket_projected_match_html(final_teams)
        else:
            final_column = _bracket_match_html(None)

    columns = [
        f'<div class="bracket-column"><div class="bracket-round">{"".join(qf_pairs)}</div></div>',
        f'<div class="bracket-column"><div class="bracket-round">{sf_pair}</div></div>',
        f'<div class="bracket-column"><div class="bracket-round bracket-final">{final_column}</div></div>',
    ]
    round_header = _bracket_round_header_track(["Quarterfinals", "Semifinals", "Championship"])
    # Defaults to whichever two rounds are relevant: once any Semifinal (or
    # the Championship itself) has a real result, show Semifinals+
    # Championship rather than starting back at Quarterfinals+Semifinals.
    start_step = 1 if (final or semifinals) else 0
    return (
        f'<div class="cup-bracket-pager" data-step="{start_step}">'
        f"{round_header}"
        # Everything below the round-name header - the actual bracket plus
        # its nav arrows - is wrapped separately so it (not the header) is
        # what gets vertically centered (see centerVertically() in
        # initCupBracketPager()): the header stays locked to a fixed
        # position right under the tab title regardless of step, only the
        # shorter-than-the-screen content below it shifts.
        '<div class="cup-bracket-content">'
        f'<div class="strip-viewport"><div class="strip-track">{"".join(columns)}</div></div>'
        '<div class="pager-nav">'
        '<button type="button" class="pager-arrow pager-prev" aria-label="הקודם">‹</button>'
        '<button type="button" class="pager-arrow pager-next" aria-label="הבא">›</button>'
        "</div></div></div>"
    )


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
    First, always: the season schedule browser (see _build_schedule_html) -
    this used to be a separate "results" tab plus a schedule tab at the end,
    but the schedule tab already shows results for any past day including
    the one this brief is about (it just resolves there by default, being
    the viewer's real "today" - see initScheduleTab()), so the two were
    merged into one. A day this brief actually fetched box scores/highlights
    for renders "rich" (OT tag, highlight link, series/cup caption - see
    renderRichRow() in JS); every other day in the schedule - which this
    brief never fetched that level of detail for - renders the plain
    score-or-tip-off-time version, same as before.
    Then, playoffs: the bracket tab (a single paged bracket covering both
    conferences and the Finals together - see
    _build_combined_playoff_bracket_html), plus the league standings tab
    last, for reference (seeding is already locked in by playoff time, but
    the final regular-season table is still worth being able to check).
    NBA Cup days (group stage or knockout): the regular league standings
    always show, since every Cup game except the Championship counts toward
    the regular season - plus a group-standings tab on group-stage days and
    a connected bracket tab on knockout days.
    Otherwise: standings only.
    """
    sections = [(
        "לוח התוצאות",
        _build_schedule_html(data.get("season_schedule", []), data.get("demo_today")),
    )]

    if data.get("is_playoffs"):
        playoff_series = data.get("playoff_series", [])
        sections += [
            ("בראקט הפלייאוף", _build_combined_playoff_bracket_html(playoff_series, data["games"])),
            ("טבלת הליגה", _build_standings_html(data["standings"])),
        ]
    else:
        standings_section = ("טבלת הליגה", _build_standings_html(data["standings"]))
        if data.get("is_cup_groups"):
            sections.append(
                ("בתי הגביע", _build_cup_group_standings_html(data.get("cup_group_standings", [])))
            )
        if data.get("is_cup_knockout"):
            sections.append(("בראקט הגביע", _build_cup_bracket_html(data.get("cup_bracket", []))))
        if data.get("is_play_in"):
            games = data.get("play_in_bracket", [])
            play_in_blocks = "".join(
                f'<div class="bracket-conf-block"><div class="bracket-conf-label">{label}</div>{_build_play_in_html(games, conf)}</div>'
                for conf, label in (("West", "מערב"), ("East", "מזרח"))
            )
            sections.append(("פלייאין", f'<div class="play-in-bracket">{play_in_blocks}</div>'))
        sections.append(standings_section)

    return "\n\n    ".join(_details_block(title, body_html) for title, body_html in sections)


def render(data: dict, summary: str) -> str:
    """Renders the daily brief as a self-contained, mobile-first HTML page (RTL, Hebrew)."""
    date_str = data["date"]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = date_obj.strftime("%d/%m/%Y")
    next_day = date_obj + timedelta(days=1)
    night_label = f"הלילה בין {_HEBREW_WEEKDAYS[date_obj.weekday()]} ל{_HEBREW_WEEKDAYS[next_day.weekday()]}"
    return TEMPLATE.format(
        display_date=display_date,
        page_date_label=f"{display_date}, {night_label}",
        app_version=datetime.now(timezone.utc).isoformat(),
        summary_html=_paragraphs_to_html(summary),
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
