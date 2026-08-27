import json
import time

import pandas as pd
import requests
from nba_api.stats.endpoints import (
    scoreboardv3,
    boxscoretraditionalv3,
    leaguestandingsv3,
    leaguegamefinder,
    scheduleleaguev2,
    leaguedashplayerstats,
)

from config import last_night_game_date, season_string_for
from highlights import find_highlight_url

# Being polite to stats.nba.com's unofficial API: small delay between calls.
REQUEST_DELAY_SECONDS = 1.0

# Unofficial, undocumented, free, no API key - same spirit as nba_api itself.
ESPN_INJURIES_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"


def _dataframe_for(endpoint_result, dataset_name: str) -> pd.DataFrame:
    """Pulls a specific named result set (e.g. 'GameHeader') out of an nba_api response."""
    names = list(endpoint_result.expected_data.keys())
    index = names.index(dataset_name)
    return endpoint_result.get_data_frames()[index]


def get_games_for_date(date_str: str) -> pd.DataFrame:
    """
    Returns one row per game played on the given US Eastern date (YYYY-MM-DD),
    including final scores, via ScoreboardV3's GameHeader + LineScore data.
    """
    result = scoreboardv3.ScoreboardV3(game_date=date_str)
    game_header = _dataframe_for(result, "GameHeader")
    line_score = _dataframe_for(result, "LineScore")
    return game_header, line_score


def get_box_score(game_id: str) -> pd.DataFrame:
    """Returns per-player stats (points, rebounds, assists, etc.) for one game."""
    result = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    return _dataframe_for(result, "PlayerStats")


def get_standings(season: str) -> pd.DataFrame:
    """Returns current league standings (rank, record, streak) for a season, e.g. '2025-26'."""
    result = leaguestandingsv3.LeagueStandingsV3(season=season)
    return _dataframe_for(result, "Standings")


def get_playoff_series(as_of_date: str) -> list[dict]:
    """
    Reconstructs the current state of every NBA playoff series active as of
    the given date, by replaying every playoff game up to that date (there's
    no single endpoint that returns "the current bracket" directly).
    """
    season = season_string_for(as_of_date)
    result = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable="Playoffs",
        league_id_nullable="00",
    )
    games_df = result.get_data_frames()[0]
    games_df = games_df[games_df["GAME_DATE"] <= as_of_date]
    if games_df.empty:
        return []

    by_game_id: dict[str, list] = {}
    for _, row in games_df.iterrows():
        by_game_id.setdefault(row["GAME_ID"], []).append(row)

    series_by_pair: dict[frozenset, dict] = {}
    for game_id, rows in by_game_id.items():
        if len(rows) != 2:
            continue
        team_a, team_b = rows
        pair = frozenset({team_a["TEAM_ID"], team_b["TEAM_ID"]})
        series = series_by_pair.setdefault(
            pair,
            {"wins": {}, "team_info": {}, "last_game_date": None, "last_game_id": None},
        )
        for row in (team_a, team_b):
            team_id = row["TEAM_ID"]
            series["wins"][team_id] = series["wins"].get(team_id, 0) + (
                1 if row["WL"] == "W" else 0
            )
            series["team_info"][team_id] = row["TEAM_ABBREVIATION"]
        game_date = team_a["GAME_DATE"]
        if series["last_game_date"] is None or game_date > series["last_game_date"]:
            series["last_game_date"] = game_date
            series["last_game_id"] = game_id

    # Round/conference labels (and each team's playoff seed) live on
    # ScoreboardV3, keyed by game date. Only fetch the (small number of)
    # distinct dates we actually need.
    dates_needed = sorted({s["last_game_date"] for s in series_by_pair.values()})
    game_meta: dict[str, dict] = {}
    for game_date in dates_needed:
        game_header, line_score = get_games_for_date(game_date)
        seeds_for_date = {row["teamId"]: row["seed"] for _, row in line_score.iterrows()}
        for _, game in game_header.iterrows():
            game_meta[game["gameId"]] = {
                "round": game["poRoundDesc"],
                "conference": game["seriesConference"],
                "seeds": seeds_for_date,
            }
        time.sleep(REQUEST_DELAY_SECONDS)

    series_list = []
    for series in series_by_pair.values():
        team_ids = sorted(series["wins"], key=lambda t: -series["wins"][t])
        meta = game_meta.get(series["last_game_id"], {})
        seeds = meta.get("seeds", {})
        series_list.append(
            {
                "teams": [
                    {
                        "team_id": t,
                        "tricode": series["team_info"][t],
                        "wins": series["wins"][t],
                        "seed": int(seeds[t]) if seeds.get(t) else None,
                    }
                    for t in team_ids
                ],
                "round": meta.get("round", ""),
                "conference": meta.get("conference", ""),
                "is_over": max(series["wins"].values()) >= 4,
            }
        )
    return series_list


def get_cup_bracket(as_of_date: str) -> list[dict]:
    """
    Returns every completed Emirates NBA Cup knockout game (Quarterfinal,
    Semifinal, Championship) up to the given date, with round + final score.
    Cup knockout games are single-elimination (no multi-game series), so each
    one is a self-contained result - no reconstruction across games needed,
    unlike get_playoff_series().
    """
    season = season_string_for(as_of_date)
    result = scheduleleaguev2.ScheduleLeagueV2(season=season)
    schedule_df = _dataframe_for(result, "SeasonGames")

    knockout = schedule_df[schedule_df["gameSubtype"] == "in-season-knockout"].copy()
    knockout["date_str"] = pd.to_datetime(knockout["gameDate"]).dt.strftime("%Y-%m-%d")
    knockout = knockout[knockout["date_str"] <= as_of_date]
    if knockout.empty:
        return []

    dates_needed = sorted(knockout["date_str"].unique())
    games_by_id: dict[str, dict] = {}
    for game_date in dates_needed:
        game_header, line_score = get_games_for_date(game_date)
        for _, game in game_header.iterrows():
            if game["gameSubtype"] != "in-season-knockout":
                continue
            teams = line_score[line_score["gameId"] == game["gameId"]].to_dict(
                orient="records"
            )
            if len(teams) != 2:
                continue
            team_a, team_b = teams
            winner, loser = (
                (team_a, team_b) if team_a["score"] > team_b["score"] else (team_b, team_a)
            )
            games_by_id[game["gameId"]] = {
                "round": game["gameSubLabel"],
                "winner": {
                    "tricode": winner["teamTricode"],
                    "score": winner["score"],
                    "wins": winner["wins"],
                    "losses": winner["losses"],
                },
                "loser": {
                    "tricode": loser["teamTricode"],
                    "score": loser["score"],
                    "wins": loser["wins"],
                    "losses": loser["losses"],
                },
            }
        time.sleep(REQUEST_DELAY_SECONDS)

    return list(games_by_id.values())


def get_play_in_bracket(as_of_date: str) -> list[dict]:
    """
    Returns every Play-In Tournament game played this season up to the given
    date - not just the games from a single night. Needed because the daily
    brief only fetches that one date's games by default, so on the deciding
    night (game 3), the earlier 7-vs-8/9-vs-10 games from a few nights before
    would otherwise show as TBD even though they're long since final.

    Play-In games aren't tagged with their own gameSubtype or season_type
    the way Cup/Playoff games are - the only reliable identifier is the
    "005" gameId prefix - so this follows the same "filter the full season
    schedule, then fetch line scores for just the relevant dates" approach
    as get_cup_bracket(), rather than the single LeagueGameFinder call
    get_playoff_series() gets to use with season_type_nullable="Playoffs".
    """
    season = season_string_for(as_of_date)
    result = scheduleleaguev2.ScheduleLeagueV2(season=season)
    schedule_df = _dataframe_for(result, "SeasonGames")

    play_in = schedule_df[schedule_df["gameId"].str.startswith("005")].copy()
    play_in["date_str"] = pd.to_datetime(play_in["gameDate"]).dt.strftime("%Y-%m-%d")
    play_in = play_in[play_in["date_str"] <= as_of_date]
    if play_in.empty:
        return []

    dates_needed = sorted(play_in["date_str"].unique())
    games_by_id: dict[str, dict] = {}
    for game_date in dates_needed:
        game_header, line_score = get_games_for_date(game_date)
        for _, game in game_header.iterrows():
            if not game["gameId"].startswith("005"):
                continue
            teams = line_score[line_score["gameId"] == game["gameId"]].to_dict(
                orient="records"
            )
            if len(teams) != 2:
                continue
            games_by_id[game["gameId"]] = {
                "game_id": game["gameId"],
                "series_conference": game["seriesConference"],
                "line_score": teams,
            }
        time.sleep(REQUEST_DELAY_SECONDS)

    return list(games_by_id.values())


def get_cup_group_standings(as_of_date: str) -> list[dict]:
    """
    Computes each team's win-loss record and point differential within
    Emirates NBA Cup group-stage play only (gameSubtype == "in-season"), up
    to the given date - not the regular-season record. Point differential is
    the key tiebreaker for who advances out of each group.
    """
    season = season_string_for(as_of_date)
    result = scheduleleaguev2.ScheduleLeagueV2(season=season)
    schedule_df = _dataframe_for(result, "SeasonGames")

    group_games = schedule_df[schedule_df["gameSubtype"] == "in-season"].copy()
    group_games["date_str"] = pd.to_datetime(group_games["gameDate"]).dt.strftime("%Y-%m-%d")
    group_games = group_games[group_games["date_str"] <= as_of_date]
    if group_games.empty:
        return []

    dates_needed = sorted(group_games["date_str"].unique())
    records: dict[str, dict] = {}
    for game_date in dates_needed:
        game_header, line_score = get_games_for_date(game_date)
        for _, game in game_header.iterrows():
            if game["gameSubtype"] != "in-season":
                continue
            teams = line_score[line_score["gameId"] == game["gameId"]].to_dict(
                orient="records"
            )
            if len(teams) != 2:
                continue
            team_a, team_b = teams
            group_label = game["gameSubLabel"]
            for team, opponent in ((team_a, team_b), (team_b, team_a)):
                record = records.setdefault(
                    team["teamId"],
                    {
                        "tricode": team["teamTricode"],
                        "name": f"{team['teamCity']} {team['teamName']}",
                        "group": group_label,
                        "wins": 0,
                        "losses": 0,
                        "point_diff": 0,
                    },
                )
                record["point_diff"] += team["score"] - opponent["score"]
                if team["score"] > opponent["score"]:
                    record["wins"] += 1
                else:
                    record["losses"] += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return list(records.values())


def get_injuries() -> list[dict]:
    """
    Current NBA injury report (ESPN, unofficial but free/no-key - nba_api has
    no equivalent). This is a live snapshot as of whenever it's called, not
    tied to a specific date, so it reflects "as of this morning" rather than
    the exact moment of last night's games - close enough in practice since
    injury statuses usually persist for days/weeks, not hours.
    """
    response = requests.get(ESPN_INJURIES_URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    injuries = []
    for team in data.get("injuries", []):
        for entry in team.get("injuries", []):
            athlete = entry.get("athlete", {})
            injuries.append(
                {
                    "player_name": athlete.get("displayName", ""),
                    "team": team.get("displayName", ""),
                    "status": entry.get("status", ""),
                    "comment": entry.get("shortComment", ""),
                }
            )
    return injuries


def get_player_power_ratings(season: str) -> dict[str, dict]:
    """
    Per-player season "power rating" - the same formula ESPN's Season Leaders
    page (espn.com/nba/seasonleaders) uses to produce a single combined
    ranking instead of separate points/rebounds/assists leaderboards:
    PTS + REB + 1.4*AST + STL + 1.4*BLK - .7*TOV + FGM + .5*FG3M
    - .8*(FGA-FGM) + .25*FTM - .8*(FTA-FTM)
    Computed locally from nba_api's own per-game season stats (the formula
    itself is public) rather than depending on ESPN for this too - nba_api is
    already the project's trusted core source. The rank is used internally
    (storylines.py) to decide who counts as a "star" - it's never meant to be
    shown to the reader, just a signal for what's worth highlighting.
    Returns {player_name: {"rating", "rank", "avg_points"}}.
    """
    result = leaguedashplayerstats.LeagueDashPlayerStats(season=season, per_mode_detailed="PerGame")
    df = result.get_data_frames()[0]

    df["POWER_RATING"] = (
        df["PTS"] + df["REB"] + 1.4 * df["AST"] + df["STL"] + 1.4 * df["BLK"]
        - 0.7 * df["TOV"] + df["FGM"] + 0.5 * df["FG3M"]
        - 0.8 * (df["FGA"] - df["FGM"]) + 0.25 * df["FTM"]
        - 0.8 * (df["FTA"] - df["FTM"])
    )
    df = df.sort_values("POWER_RATING", ascending=False).reset_index(drop=True)

    return {
        row["PLAYER_NAME"]: {
            "rating": round(row["POWER_RATING"], 1),
            "rank": i + 1,
            "avg_points": row["PTS"],
        }
        for i, row in df.iterrows()
    }


def highlight_url_for_game(game_code: str, line_score_rows: list[dict], date_str: str) -> str | None:
    """
    Derives the two teams' full names from this game's own line_score rows
    (already fetched, no extra request) and the away/home order from
    game_code (ScoreboardV3's "YYYYMMDD/AWAYHOME" gameCode field) to look up
    this exact game's highlight video (see highlights.py). Public (not
    fetch.py-internal) since scheduler.py's second pass needs to redo this
    same lookup later for whichever games missed it on the first pass,
    without re-fetching anything else from nba_api.
    """
    codes = game_code.split("/")[-1] if "/" in game_code else ""
    if len(codes) != 6:
        return None
    away_tricode, home_tricode = codes[:3], codes[3:]
    by_tricode = {row["teamTricode"]: row for row in line_score_rows}
    home_row, away_row = by_tricode.get(home_tricode), by_tricode.get(away_tricode)
    if not home_row or not away_row:
        return None
    home_name = f"{home_row['teamCity']} {home_row['teamName']}"
    away_name = f"{away_row['teamCity']} {away_row['teamName']}"
    return find_highlight_url(home_name, away_name, date_str)


def fetch_for_date(date_str: str) -> dict:
    """
    Fetches all games for a given US Eastern date, their box scores, and current
    league standings. Returns a plain dict, ready to be dumped as JSON.
    """
    game_header, line_score = get_games_for_date(date_str)

    games = []
    for _, game in game_header.iterrows():
        game_id = game["gameId"]
        box_score = get_box_score(game_id)
        time.sleep(REQUEST_DELAY_SECONDS)

        game_line_score = line_score[line_score["gameId"] == game_id].to_dict(orient="records")

        # Unofficial, best-effort (see highlights.py) - a game whose highlight
        # isn't up yet just gets None here, not an error; scheduler.py's
        # second pass retries whatever's still missing a couple hours later.
        try:
            highlight_url = highlight_url_for_game(game["gameCode"], game_line_score, date_str)
        except Exception as e:
            print(f"Warning: highlight lookup failed for {game_id} ({e}) - continuing without it.")
            highlight_url = None
        time.sleep(REQUEST_DELAY_SECONDS)

        games.append(
            {
                "game_id": game_id,
                "matchup": game["gameCode"],
                "status": game["gameStatusText"],
                "period": int(game["period"]),
                "line_score": game_line_score,
                "box_score": box_score.to_dict(orient="records"),
                "po_round": game["poRoundDesc"],
                "series_conference": game["seriesConference"],
                "series_text": game["seriesText"],
                "series_game_number": game["seriesGameNumber"],
                "cup_subtype": game["gameSubtype"],
                "cup_sub_label": game["gameSubLabel"],
                "highlight_url": highlight_url,
            }
        )

    standings = get_standings(season_string_for(date_str))
    time.sleep(REQUEST_DELAY_SECONDS)

    is_playoffs = any(g["po_round"] for g in games)
    playoff_series = get_playoff_series(date_str) if is_playoffs else []

    is_cup_knockout = any(g["cup_subtype"] == "in-season-knockout" for g in games)
    cup_bracket = get_cup_bracket(date_str) if is_cup_knockout else []

    is_cup_groups = any(g["cup_subtype"] == "in-season" for g in games)
    cup_group_standings = get_cup_group_standings(date_str) if is_cup_groups else []

    # Play-In games (gameId prefix "005") aren't tagged via poRoundDesc the way
    # Playoffs/Finals games are - is_playoffs stays False for them, since the
    # Play-In isn't officially "Playoffs". Detected by game_id prefix instead.
    is_play_in = any(g["game_id"].startswith("005") for g in games)
    play_in_bracket = get_play_in_bracket(date_str) if is_play_in else []

    # Both unofficial/undocumented on top of everything above - degrade
    # gracefully (empty results) rather than failing the whole brief if
    # ESPN or this particular nba_api endpoint has a bad day.
    try:
        injuries = get_injuries()
    except Exception as e:
        print(f"Warning: could not fetch injuries ({e}) - continuing without them.")
        injuries = []
    try:
        power_ratings = get_player_power_ratings(season_string_for(date_str))
    except Exception as e:
        print(f"Warning: could not fetch player power ratings ({e}) - continuing without them.")
        power_ratings = {}

    return {
        "date": date_str,
        "games": games,
        "standings": standings.to_dict(orient="records"),
        "is_playoffs": is_playoffs,
        "playoff_series": playoff_series,
        "is_cup_knockout": is_cup_knockout,
        "cup_bracket": cup_bracket,
        "is_cup_groups": is_cup_groups,
        "cup_group_standings": cup_group_standings,
        "is_play_in": is_play_in,
        "play_in_bracket": play_in_bracket,
        "injuries": injuries,
        "player_power_ratings": power_ratings,
    }


def fetch_last_night(now=None) -> dict:
    """Fetches last night's games (from the Israeli reader's perspective)."""
    return fetch_for_date(last_night_game_date(now))


if __name__ == "__main__":
    data = fetch_last_night()
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
