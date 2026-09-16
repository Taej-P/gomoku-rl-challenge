# -*- coding: utf-8 -*-
"""Deterministic evaluation harness for the Gomoku RL assignment.

Runs a fixed number of games against two baselines and reports per-baseline
plus overall win rate. Total default: 100 games (50 per baseline).

Usage:
    python evaluate.py                          # default agent module "student_agent"
    python evaluate.py --agent student_agent
    python evaluate.py --agent-path ./team_x/student_agent.py
    python evaluate.py --games 10               # quick smoke test (20 games total)

Determinism:
    Before every single game, we reseed both python `random` and `numpy.random`
    from a game-specific seed derived from --seed. This means two identical
    runs of `evaluate.py` produce identical results even when the agent or the
    baselines call random.*/np.random.*.
"""
from __future__ import print_function

import argparse
import importlib
import importlib.util
import os
import random
import sys
import time

import numpy as np

from game import Board, Game
from baseline_bot import BASELINE_NAMES, BOARD_SIZE, N_IN_ROW, make_baseline

STUDENT_TIME_BUDGET_S = 300.0  # per game, cumulative across all student moves


def _seed_all(seed):
    random.seed(seed)
    np.random.seed(seed & 0xFFFFFFFF)


def _load_agent_factory(module_name=None, module_path=None):
    """Return a callable make_agent() from either a module name or a file path."""
    if module_path:
        module_path = os.path.abspath(module_path)
        spec = importlib.util.spec_from_file_location("student_agent_loaded", module_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    else:
        if module_name is None:
            raise ValueError("Provide either --agent or --agent-path.")
        mod = importlib.import_module(module_name)
    if not hasattr(mod, "make_agent"):
        raise AttributeError(
            "Module {} must define make_agent().".format(module_name or module_path)
        )
    return mod.make_agent


def _play_one_game(student, baseline, student_is_black, time_budget_s=STUDENT_TIME_BUDGET_S):
    """Run one game with a cumulative wall-clock budget on the student side.
    If the student's total time in get_action() exceeds time_budget_s, the
    game is forfeited (recorded as a loss). Returns (outcome, time_used_s).
    Outcome is one of: "win", "loss", "loss_time", "draw".
    """
    board = Board(width=BOARD_SIZE, height=BOARD_SIZE, n_in_row=N_IN_ROW)
    board.init_board(start_player=0)
    if student_is_black:
        p1, p2 = student, baseline
        student_id = 1
    else:
        p1, p2 = baseline, student
        student_id = 2
    p1.set_player_ind(1)
    p2.set_player_ind(2)
    players = {1: p1, 2: p2}
    student_time = 0.0

    while True:
        current = board.get_current_player()
        player = players[current]
        if current == student_id:
            if student_time >= time_budget_s:
                return "loss_time", student_time
            t0 = time.perf_counter()
            move = player.get_action(board)
            student_time += time.perf_counter() - t0
            if student_time > time_budget_s:
                # last move ran over — still forfeit
                return "loss_time", student_time
        else:
            move = player.get_action(board)
        board.do_move(move)
        end, winner = board.game_end()
        if end:
            if winner == -1:
                return "draw", student_time
            return ("win" if winner == student_id else "loss"), student_time


def run_matchup(factory, baseline_name, n_games, seed_base, verbose=True):
    """Play `n_games` games against a named baseline. Colors alternate:
    the first half of games has the student as Black."""
    wins = losses = time_losses = draws = 0
    per_color = {"black": [0, 0, 0, 0], "white": [0, 0, 0, 0]}  # [w, l, d, time_loss]
    total_student_time = 0.0
    n_black = n_games // 2

    for i in range(n_games):
        _seed_all(seed_base + i)
        student = factory()
        baseline = make_baseline(baseline_name)
        student_is_black = i < n_black

        result, t_used = _play_one_game(student, baseline, student_is_black)
        total_student_time += t_used
        color_bucket = per_color["black" if student_is_black else "white"]
        if result == "win":
            wins += 1
            color_bucket[0] += 1
        elif result == "loss":
            losses += 1
            color_bucket[1] += 1
        elif result == "loss_time":
            losses += 1
            time_losses += 1
            color_bucket[1] += 1
            color_bucket[3] += 1
        else:
            draws += 1
            color_bucket[2] += 1

        if verbose and (i + 1) % max(1, n_games // 10) == 0:
            print(
                "  [{}/{}]  W {}  L {}  D {}   (time_forfeits {})".format(
                    i + 1, n_games, wins, losses, draws, time_losses
                )
            )

    return {
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "time_losses": time_losses,
        "per_color": per_color,
        "n_games": n_games,
        "total_student_time": total_student_time,
    }


def print_matchup_summary(name, result, elapsed):
    n = result["n_games"]
    w = result["wins"]
    l = result["losses"]
    d = result["draws"]
    tl = result["time_losses"]
    wr = 100.0 * w / n if n else 0.0
    b = result["per_color"]["black"]
    wt = result["per_color"]["white"]
    avg_t = result["total_student_time"] / n if n else 0.0
    print(
        "  {:>10} : {:>3}W / {:>3}L / {:>3}D   win-rate {:5.1f}%   "
        "(as Black {}W-{}L-{}D | as White {}W-{}L-{}D)   "
        "avg student time {:.1f}s/game, time_forfeits {}   [{:.1f}s wall]".format(
            name, w, l, d, wr,
            b[0], b[1], b[2], wt[0], wt[1], wt[2],
            avg_t, tl, elapsed
        )
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="student_agent",
                    help="Python module name to import (must expose make_agent()).")
    ap.add_argument("--agent-path", default=None,
                    help="Path to a student_agent.py file. Overrides --agent.")
    ap.add_argument("--games", type=int, default=50,
                    help="Games per baseline. Total games = 2 * games. Default 50 -> 100 total.")
    ap.add_argument("--seed", type=int, default=20260916,
                    help="Base seed for reproducible evaluation.")
    args = ap.parse_args()

    factory = _load_agent_factory(args.agent, args.agent_path)

    print("Gomoku evaluation")
    print("  board          : {}x{}, {}-in-a-row".format(BOARD_SIZE, BOARD_SIZE, N_IN_ROW))
    print("  games/baseline : {}  (total {})".format(args.games, 2 * args.games))
    print("  agent          : {}".format(args.agent_path or args.agent))
    print("  seed           : {}".format(args.seed))
    print("  time budget    : {:.0f}s per game (student side)".format(STUDENT_TIME_BUDGET_S))
    print("")

    t_total = time.time()
    results = {}
    for idx, name in enumerate(BASELINE_NAMES):
        print("vs {} ...".format(name))
        t0 = time.time()
        result = run_matchup(factory, name, args.games, args.seed + 1000 * idx)
        elapsed = time.time() - t0
        results[name] = result
        print_matchup_summary(name, result, elapsed)
        print("")

    total_w = sum(r["wins"] for r in results.values())
    total_l = sum(r["losses"] for r in results.values())
    total_d = sum(r["draws"] for r in results.values())
    total_n = sum(r["n_games"] for r in results.values())
    print("=" * 60)
    print(
        "TOTAL : {}W / {}L / {}D   overall win-rate {:.1f}%   "
        "[{:.1f}s total]".format(
            total_w, total_l, total_d,
            100.0 * total_w / total_n if total_n else 0.0,
            time.time() - t_total,
        )
    )


if __name__ == "__main__":
    main()
