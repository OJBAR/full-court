CLOSE_GAME_MARGIN = 5
STANDOUT_POINTS = 30
STANDOUT_REBOUNDS = 15
STANDOUT_ASSISTS = 15
TRIPLE_DOUBLE_CATEGORIES = ["points", "reboundsTotal", "assists", "steals", "blocks"]
TRIPLE_DOUBLE_THRESHOLD = 10
SURPRISE_RANK_GAP = 8
NOTABLE_STREAK_LENGTH = 3
SURPRISE_SEED_GAP = 3  # playoff mode: e.g. a #5 seed beating a #2 seed or worse


def _standings_by_team(standings: list[dict]) -> dict:
    """
    Maps TeamID -> standings row, adding our own 'OverallRank' (1 = best record)
    computed from WinPCT. The API's own LeagueRank field is unreliable (NaN for
    most teams as of this writing), so we don't use it.
    """
    ranked = sorted(standings, key=lambda row: row["WinPCT"], reverse=True)
    by_team = {}
    for rank, row in enumerate(ranked, start=1):
        by_team[row["TeamID"]] = {**row, "OverallRank": rank}
    return by_team


def find_close_or_ot_games(games: list[dict]) -> list[dict]:
    """Games decided by a small margin (<=5 pts) or that went to overtime."""
    storylines = []
    for game in games:
        line_score = game["line_score"]
        if len(line_score) != 2:
            continue
        team_a, team_b = line_score
        margin = abs(team_a["score"] - team_b["score"])
        is_ot = game["period"] > 4

        if margin <= CLOSE_GAME_MARGIN or is_ot:
            winner, loser = (
                (team_a, team_b) if team_a["score"] > team_b["score"] else (team_b, team_a)
            )
            storylines.append(
                {
                    "type": "close_game",
                    "matchup": game["matchup"],
                    "margin": margin,
                    "overtime": is_ot,
                    "winner": winner["teamTricode"],
                    "loser": loser["teamTricode"],
                    "final_score": f"{winner['teamTricode']} {winner['score']} - "
                    f"{loser['score']} {loser['teamTricode']}",
                }
            )
    return storylines


def find_standout_performances(games: list[dict]) -> list[dict]:
    """Players with 30+ points, a triple-double, or 15+ rebounds/assists."""
    storylines = []
    for game in games:
        for player in game["box_score"]:
            double_digit_categories = sum(
                1
                for category in TRIPLE_DOUBLE_CATEGORIES
                if player.get(category, 0) >= TRIPLE_DOUBLE_THRESHOLD
            )

            reasons = []
            if player.get("points", 0) >= STANDOUT_POINTS:
                reasons.append(f"{player['points']} points")
            if player.get("reboundsTotal", 0) >= STANDOUT_REBOUNDS:
                reasons.append(f"{player['reboundsTotal']} rebounds")
            if player.get("assists", 0) >= STANDOUT_ASSISTS:
                reasons.append(f"{player['assists']} assists")
            if double_digit_categories >= 3:
                reasons.append("triple-double")

            if reasons:
                storylines.append(
                    {
                        "type": "standout_performance",
                        "player": f"{player['firstName']} {player['familyName']}",
                        "team": player["teamTricode"],
                        "matchup": game["matchup"],
                        "reasons": reasons,
                        "line": f"{player['points']}p / {player['reboundsTotal']}r / "
                        f"{player['assists']}a",
                    }
                )
    return storylines


def find_surprises(games: list[dict], standings: list[dict]) -> list[dict]:
    """A team ranked well below its opponent (by league rank) won anyway."""
    by_team = _standings_by_team(standings)
    storylines = []
    for game in games:
        line_score = game["line_score"]
        if len(line_score) != 2:
            continue
        team_a, team_b = line_score
        winner, loser = (
            (team_a, team_b) if team_a["score"] > team_b["score"] else (team_b, team_a)
        )
        winner_standing = by_team.get(winner["teamId"])
        loser_standing = by_team.get(loser["teamId"])
        if not winner_standing or not loser_standing:
            continue

        rank_gap = winner_standing["OverallRank"] - loser_standing["OverallRank"]
        if rank_gap >= SURPRISE_RANK_GAP:
            storylines.append(
                {
                    "type": "surprise",
                    "matchup": game["matchup"],
                    "winner": winner["teamTricode"],
                    "winner_rank": winner_standing["OverallRank"],
                    "loser": loser["teamTricode"],
                    "loser_rank": loser_standing["OverallRank"],
                    "rank_gap": rank_gap,
                }
            )
    return storylines


def find_streaks(games: list[dict], standings: list[dict]) -> list[dict]:
    """Teams (from last night's games) on a notable win or loss streak (>=3)."""
    by_team = _standings_by_team(standings)
    storylines = []
    seen_teams = set()
    for game in games:
        for team in game["line_score"]:
            team_id = team["teamId"]
            if team_id in seen_teams:
                continue
            seen_teams.add(team_id)

            standing = by_team.get(team_id)
            if not standing:
                continue
            streak_length = abs(int(standing.get("CurrentStreak", 0)))
            if streak_length >= NOTABLE_STREAK_LENGTH:
                storylines.append(
                    {
                        "type": "streak",
                        "team": team["teamTricode"],
                        "streak": standing.get("strCurrentStreak", ""),
                        "length": streak_length,
                        "matchup": game["matchup"],
                    }
                )
    return storylines


def all_game_results(games: list[dict]) -> list[dict]:
    """
    Final score for every game that was played, regardless of how notable it
    was. Used alongside the storyline detectors so the summary never silently
    skips a game just because nothing dramatic happened in it.
    """
    results = []
    for game in games:
        line_score = game["line_score"]
        if len(line_score) != 2:
            continue
        team_a, team_b = line_score
        winner, loser = (
            (team_a, team_b) if team_a["score"] > team_b["score"] else (team_b, team_a)
        )
        result = {
            "matchup": game["matchup"],
            "winner": winner["teamTricode"],
            "winner_score": winner["score"],
            "loser": loser["teamTricode"],
            "loser_score": loser["score"],
        }
        if game.get("po_round"):
            result["series_text"] = game.get("series_text", "")
            result["game_number"] = game.get("series_game_number", "")
        if game.get("cup_subtype"):
            result["cup_context"] = game.get("cup_sub_label", "")
        results.append(result)
    return results


def find_playoff_seed_upsets(games: list[dict]) -> list[dict]:
    """
    A team seeded clearly worse than its opponent won anyway (e.g. a #5 seed
    beating a #2 seed). Playoff seeds ride along on each game's line_score,
    so no cross-referencing with season-long standings is needed here.
    """
    storylines = []
    for game in games:
        line_score = game["line_score"]
        if len(line_score) != 2 or not game.get("po_round"):
            continue
        team_a, team_b = line_score
        winner, loser = (
            (team_a, team_b) if team_a["score"] > team_b["score"] else (team_b, team_a)
        )
        if "seed" not in winner or "seed" not in loser:
            continue
        seed_gap = winner["seed"] - loser["seed"]
        if seed_gap >= SURPRISE_SEED_GAP:
            storylines.append(
                {
                    "type": "playoff_upset",
                    "matchup": game["matchup"],
                    "winner": winner["teamTricode"],
                    "winner_seed": int(winner["seed"]),
                    "loser": loser["teamTricode"],
                    "loser_seed": int(loser["seed"]),
                }
            )
    return storylines


def find_series_developments(games: list[dict]) -> list[dict]:
    """
    Series-level context for last night's playoff games: a series being
    clinched, or a series now tied heading to a decisive game.
    """
    storylines = []
    for game in games:
        po_round = game.get("po_round")
        series_text = game.get("series_text", "")
        if not po_round or not series_text:
            continue
        if "wins" in series_text.lower():
            storylines.append(
                {
                    "type": "series_clinched",
                    "matchup": game["matchup"],
                    "round": po_round,
                    "series_text": series_text,
                    "game_number": game.get("series_game_number", ""),
                }
            )
        elif "tied" in series_text.lower():
            storylines.append(
                {
                    "type": "series_tied",
                    "matchup": game["matchup"],
                    "round": po_round,
                    "series_text": series_text,
                    "game_number": game.get("series_game_number", ""),
                }
            )
    return storylines


def find_cup_advancements(games: list[dict]) -> list[dict]:
    """
    NBA Cup knockout games are single-elimination - every one is simultaneously
    an elimination for the loser and an advancement for the winner.
    """
    storylines = []
    for game in games:
        if game.get("cup_subtype") != "in-season-knockout":
            continue
        line_score = game["line_score"]
        if len(line_score) != 2:
            continue
        team_a, team_b = line_score
        winner, loser = (
            (team_a, team_b) if team_a["score"] > team_b["score"] else (team_b, team_a)
        )
        storylines.append(
            {
                "type": "cup_advancement",
                "matchup": game["matchup"],
                "round": game.get("cup_sub_label", ""),
                "winner": winner["teamTricode"],
                "winner_score": winner["score"],
                "loser": loser["teamTricode"],
                "loser_score": loser["score"],
            }
        )
    return storylines


STAR_POWER_RANK_THRESHOLD = 30  # top 30 in the league by power rating counts as "a star"
WEAK_PERFORMANCE_RATIO = 0.5  # scoring at or below half of their own season average is notable


def find_injury_notes(games: list[dict], injuries: list[dict]) -> list[dict]:
    """
    Notable players marked "Out" on ESPN's current injury report, on teams
    that played tonight. This is a live snapshot (not date-specific) - see
    get_injuries() in fetch.py - so it reflects the report as of this
    morning, not necessarily the exact moment of the game.
    """
    storylines = []
    for game in games:
        line_score = game["line_score"]
        if len(line_score) != 2:
            continue
        team_names = {f"{team['teamCity']} {team['teamName']}" for team in line_score}
        for injury in injuries:
            if injury["team"] in team_names and injury["status"] == "Out":
                storylines.append(
                    {
                        "type": "player_out",
                        "matchup": game["matchup"],
                        "team": injury["team"],
                        "player": injury["player_name"],
                        "comment": injury["comment"],
                    }
                )
    return storylines


def find_star_weak_performances(games: list[dict], power_ratings: dict[str, dict]) -> list[dict]:
    """
    A top-30 player (by season power rating - see get_player_power_ratings()
    in fetch.py) who scored well below their own season average tonight - a
    data-grounded way to flag "a star had a quiet night" without needing to
    know who's a star from general knowledge, and relative to that specific
    player's normal level rather than one flat cutoff for everyone.

    The rank/rating are only ever used here to decide who qualifies as "a
    star" - they're intentionally left out of the returned storyline, since
    they're an internal signal, not something meant to appear in the brief.
    """
    storylines = []
    for game in games:
        for player in game["box_score"]:
            full_name = f"{player['firstName']} {player['familyName']}"
            rating_info = power_ratings.get(full_name)
            if not rating_info or rating_info["rank"] > STAR_POWER_RANK_THRESHOLD:
                continue
            if not player.get("minutes"):
                continue
            avg_points = rating_info["avg_points"]
            if avg_points <= 0:
                continue
            if player.get("points", 0) <= avg_points * WEAK_PERFORMANCE_RATIO:
                storylines.append(
                    {
                        "type": "star_weak_performance",
                        "player": full_name,
                        "team": player["teamTricode"],
                        "matchup": game["matchup"],
                        "season_avg_points": round(avg_points, 1),
                        "line": f"{player['points']}p / {player['reboundsTotal']}r / "
                        f"{player['assists']}a",
                    }
                )
    return storylines


def find_play_in_context(games: list[dict]) -> list[dict]:
    """
    Play-In Tournament context for tonight's games: which of the three game
    types this is (7-vs-8 opener, 9-vs-10 loser-out, or the decider for the
    8 seed) and who's advancing/eliminated - without this, a Play-In game
    reads to the model like an ordinary regular-season game with no stakes.
    """
    storylines = []
    for game in games:
        if not game["game_id"].startswith("005"):
            continue
        line_score = game["line_score"]
        if len(line_score) != 2:
            continue
        team_a, team_b = line_score
        seeds = {t.get("seed") for t in line_score}
        winner, loser = (
            (team_a, team_b) if team_a["score"] > team_b["score"] else (team_b, team_a)
        )
        if seeds == {7, 8}:
            game_type = "seven_vs_eight"
        elif seeds == {9, 10}:
            game_type = "nine_vs_ten"
        else:
            game_type = "decider"
        storylines.append(
            {
                "type": "play_in_context",
                "matchup": game["matchup"],
                "game_type": game_type,
                "winner": winner["teamTricode"],
                "loser": loser["teamTricode"],
            }
        )
    return storylines


def find_storylines(data: dict) -> dict:
    """Runs all storyline detectors over a fetch.py-shaped data dict."""
    games = data["games"]
    injuries = data.get("injuries", [])
    power_ratings = data.get("player_power_ratings", {})

    if data.get("is_playoffs"):
        return {
            "close_or_ot_games": find_close_or_ot_games(games),
            "standout_performances": find_standout_performances(games),
            "playoff_upsets": find_playoff_seed_upsets(games),
            "series_developments": find_series_developments(games),
            "injury_notes": find_injury_notes(games, injuries),
            "star_weak_performances": find_star_weak_performances(games, power_ratings),
        }

    standings = data["standings"]
    storylines = {
        "close_or_ot_games": find_close_or_ot_games(games),
        "standout_performances": find_standout_performances(games),
        "surprises": find_surprises(games, standings),
        "streaks": find_streaks(games, standings),
        "injury_notes": find_injury_notes(games, injuries),
        "star_weak_performances": find_star_weak_performances(games, power_ratings),
    }
    if data.get("is_cup_knockout"):
        storylines["cup_advancements"] = find_cup_advancements(games)
    if data.get("is_play_in"):
        storylines["play_in_context"] = find_play_in_context(games)
    return storylines
