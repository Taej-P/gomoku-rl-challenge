# -*- coding: utf-8 -*-
"""Round-robin league between multiple team submissions.

Each team submits a directory containing student_agent.py.  This script pits
every team against every other team, alternating colors, and reports a summary
table plus per-team average win rate.

Usage:
    # by directory (student_agent.py must exist in each dir)
    python league.py --teams teamA teamB teamC --games 20

    # by explicit file path (name is inferred from parent dir)
    python league.py --files teamA/agent.py teamB/agent.py --games 20

    # with an alias:  name=path/to/agent.py
    python league.py --files "A=teamA/agent.py" "B=teamB/agent.py" --games 20

Determinism:
    Each game is seeded from --seed + hash(team_a, team_b, game_index) so two
    identical runs produce identical results.
"""
from __future__ import print_function

import argparse
import importlib.util
import os
import random
import sys
import time
from itertools import combinations

import numpy as np

from game import Board, Game
from baseline_bot import BOARD_SIZE, N_IN_ROW

TIME_BUDGET_S = 300.0  # per team per game, cumulative


def _seed_all(seed):
    random.seed(seed)
    np.random.seed(seed & 0xFFFFFFFF)


def _resolve_team_entries(dirs, files):
    """Return list of (team_name, absolute_path_to_student_agent.py)."""
    entries = []
    for d in dirs or []:
        d = os.path.abspath(d)
        candidate = os.path.join(d, "student_agent.py")
        if not os.path.isfile(candidate):
            raise FileNotFoundError(
                "Expected {} in team dir {}".format("student_agent.py", d)
            )
        entries.append((os.path.basename(d.rstrip(os.sep)), candidate))
    for spec in files or []:
        if "=" in spec:
            name, path = spec.split("=", 1)
        else:
            path = spec
            name = os.path.basename(os.path.dirname(os.path.abspath(path))) or os.path.basename(path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError("Not a file: {}".format(path))
        entries.append((name, path))
    # de-duplicate names
    seen = {}
    unique = []
    for name, path in entries:
        if name in seen:
            seen[name] += 1
            name = "{}#{}".format(name, seen[name])
        else:
            seen[name] = 1
        unique.append((name, path))
    return unique


def _load_factory(module_path, load_key):
    spec = importlib.util.spec_from_file_location(load_key, module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[load_key] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, "make_agent"):
        raise AttributeError(
            "{} does not define make_agent().".format(module_path)
        )
    return mod.make_agent


def _play_one_game(black_factory, white_factory, time_budget_s=TIME_BUDGET_S):
    """Both sides share the same time budget. Return (winner, over_id) where
    winner in {1,2,-1} and over_id is the player id that ran out of time (or 0).
    A time-out becomes an automatic loss for that side."""
    board = Board(width=BOARD_SIZE, height=BOARD_SIZE, n_in_row=N_IN_ROW)
    board.init_board(start_player=0)
    b, w = black_factory(), white_factory()
    b.set_player_ind(1)
    w.set_player_ind(2)
    players = {1: b, 2: w}
    used = {1: 0.0, 2: 0.0}

    while True:
        cur = board.get_current_player()
        if used[cur] >= time_budget_s:
            return (2 if cur == 1 else 1), cur
        t0 = time.perf_counter()
        move = players[cur].get_action(board)
        used[cur] += time.perf_counter() - t0
        if used[cur] > time_budget_s:
            return (2 if cur == 1 else 1), cur
        board.do_move(move)
        end, winner = board.game_end()
        if end:
            return winner, 0


def run_pair(name_a, fac_a, name_b, fac_b, n_games, base_seed):
    """Play `n_games` between two teams, alternating who plays Black.
    Return (a_wins, b_wins, draws, a_timeouts, b_timeouts)."""
    a_wins = b_wins = draws = 0
    a_timeouts = b_timeouts = 0
    for g in range(n_games):
        seed = (base_seed + hash((name_a, name_b, g))) & 0xFFFFFFFF
        _seed_all(seed)
        a_is_black = (g % 2 == 0)
        if a_is_black:
            winner, over_id = _play_one_game(fac_a, fac_b)
            if over_id == 1:
                a_timeouts += 1
            elif over_id == 2:
                b_timeouts += 1
            if winner == 1:
                a_wins += 1
            elif winner == 2:
                b_wins += 1
            else:
                draws += 1
        else:
            winner, over_id = _play_one_game(fac_b, fac_a)
            if over_id == 1:
                b_timeouts += 1
            elif over_id == 2:
                a_timeouts += 1
            if winner == 1:
                b_wins += 1
            elif winner == 2:
                a_wins += 1
            else:
                draws += 1
    return a_wins, b_wins, draws, a_timeouts, b_timeouts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teams", nargs="+", default=None,
                    help="Team directories (each must contain student_agent.py).")
    ap.add_argument("--files", nargs="+", default=None,
                    help="Agent files. Format: PATH or NAME=PATH.")
    ap.add_argument("--games", type=int, default=20,
                    help="Games per pair. Colors alternate every game.")
    ap.add_argument("--seed", type=int, default=20260916)
    args = ap.parse_args()

    if not args.teams and not args.files:
        ap.error("Provide at least one of --teams or --files.")

    entries = _resolve_team_entries(args.teams, args.files)
    if len(entries) < 2:
        ap.error("Need at least 2 teams for a league.")

    # Load each team's make_agent
    print("Loading {} teams...".format(len(entries)))
    factories = {}
    for name, path in entries:
        print("  {:>16}  <- {}".format(name, path))
        factories[name] = _load_factory(path, "league_" + name)
    print("")

    names = [n for n, _ in entries]
    n_teams = len(names)
    n_pairs = n_teams * (n_teams - 1) // 2
    total_games = n_pairs * args.games
    print(
        "League: {} teams, {} pairs, {} games/pair -> {} total games\n".format(
            n_teams, n_pairs, args.games, total_games
        )
    )

    # Score table: wins/losses/draws for each team
    scores = {n: {"W": 0, "L": 0, "D": 0, "opponents": 0} for n in names}
    matrix = {n: {m: None for m in names} for n in names}  # (wr_percent, wins, games)

    timeout_counts = {n: 0 for n in names}
    t_total = time.time()
    for a, b in combinations(names, 2):
        t0 = time.time()
        aw, bw, dr, a_to, b_to = run_pair(a, factories[a], b, factories[b], args.games, args.seed)
        wr_a = 100.0 * (aw + 0.5 * dr) / args.games
        wr_b = 100.0 * (bw + 0.5 * dr) / args.games
        matrix[a][b] = (wr_a, aw, args.games)
        matrix[b][a] = (wr_b, bw, args.games)
        scores[a]["W"] += aw
        scores[a]["L"] += bw
        scores[a]["D"] += dr
        scores[a]["opponents"] += 1
        scores[b]["W"] += bw
        scores[b]["L"] += aw
        scores[b]["D"] += dr
        scores[b]["opponents"] += 1
        timeout_counts[a] += a_to
        timeout_counts[b] += b_to
        extra = ""
        if a_to or b_to:
            extra = "  (timeouts: {} {}, {} {})".format(a, a_to, b, b_to)
        print(
            "  {:>12} vs {:<12}  {:>3}-{:<3}  (draws {}){}   [{:.1f}s]".format(
                a, b, aw, bw, dr, extra, time.time() - t0
            )
        )

    print("\nHead-to-head win-rate matrix (% score, includes draws as 0.5):")
    col_w = 8
    header = " " * 14 + "".join("{:>{}s}".format(n[:col_w - 1], col_w) for n in names)
    print(header)
    for row in names:
        cells = []
        for col in names:
            if row == col:
                cells.append("{:>{}s}".format("--", col_w))
            else:
                wr, w, g = matrix[row][col]
                cells.append("{:>{}s}".format("{:.0f}%".format(wr), col_w))
        print("{:>13s} ".format(row) + "".join(cells))

    print("\nFinal standings (avg win rate across opponents):")
    ranking = []
    for n in names:
        s = scores[n]
        total = s["W"] + s["L"] + s["D"]
        pts = s["W"] + 0.5 * s["D"]
        avg_wr = 100.0 * pts / total if total else 0.0
        ranking.append((avg_wr, n, s, timeout_counts[n]))
    ranking.sort(reverse=True)
    print("  rank  team                avg_WR    W    L    D   timeouts")
    for i, (wr, n, s, to) in enumerate(ranking, 1):
        print("  {:>3}.  {:<18} {:>6.1f}%  {:>4} {:>4} {:>4}   {:>4}".format(
            i, n, wr, s["W"], s["L"], s["D"], to
        ))

    print("\nTotal elapsed: {:.1f}s".format(time.time() - t_total))


if __name__ == "__main__":
    main()
