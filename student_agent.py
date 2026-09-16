# -*- coding: utf-8 -*-
"""Student submission stub — REPLACE THIS FILE with your own agent.

Required interface:

    def make_agent():
        return <your player>

The returned player must implement:

    set_player_ind(p: int) -> None      # called once per game, p in {1, 2}
    get_action(board) -> int            # return a legal move index

Where `board` is a game.Board instance. Useful members:

    board.width, board.height          # both 8 for this assignment
    board.n_in_row                     # 5
    board.availables                   # list of legal move indices
    board.states                       # dict move_index -> player_id (1 or 2)
    board.last_move                    # int, or -1 if no move played yet
    board.get_current_player()         # 1 or 2
    board.current_state()              # numpy array shape (4, 8, 8),
                                       # from the current player's perspective:
                                       #   channel 0 = my stones
                                       #   channel 1 = opponent stones
                                       #   channel 2 = last-move indicator
                                       #   channel 3 = all 1s if my turn else 0s
    board.move_to_location(move)       # move -> [row, col]
    board.location_to_move([r, c])     # [row, col] -> move

Constraints (enforced or checked by evaluate.py / league.py):
  * <= 5 seconds of wall-clock per get_action() call
  * <= 100 MB of weight files loaded at import time
  * no network access at eval time
  * no calls into baseline_bot.py from your agent

The stub below plays uniformly at random. It exists only to document the
interface — you are expected to replace it entirely.
"""
from __future__ import print_function

import random


class RandomAgent(object):
    """Plays a legal move uniformly at random. Weakest possible opponent."""

    def __init__(self):
        self.player = None

    def set_player_ind(self, p):
        self.player = p

    def get_action(self, board):
        return random.choice(board.availables)


def make_agent():
    """Entry point required by evaluate.py and league.py."""
    return RandomAgent()
