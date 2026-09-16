# -*- coding: utf-8 -*-
"""AI vs AI Gomoku viewer using tkinter.

Loads the pretrained AlphaZero-style policy/value net (numpy inference) and
lets two MCTS players play each other while the board updates in real time.
"""
from __future__ import print_function

import argparse
import pickle
import random
import threading
import tkinter as tk
from tkinter import font as tkfont

import numpy as np

from game import Board
from mcts_alphaZero import MCTSPlayer
from policy_value_net_numpy import PolicyValueNetNumpy


CELL = 60           # pixel size of one cell
MARGIN = 30         # margin around the board
STONE_R = 24        # stone radius
LAST_MOVE_R = 6     # last-move indicator radius


def load_policy(model_file, width, height):
    with open(model_file, "rb") as f:
        try:
            params = pickle.load(f)
        except UnicodeDecodeError:
            f.seek(0)
            params = pickle.load(f, encoding="bytes")
    return PolicyValueNetNumpy(width, height, params)


class GomokuGUI:
    def __init__(self, root, width, height, n_in_row, model_file, n_playout,
                 delay_ms, temp, random_opening, seed, start_player):
        self.width = width
        self.height = height
        self.n_in_row = n_in_row
        self.delay_ms = delay_ms
        self.temp = temp
        self.random_opening = random_opening
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.board = Board(width=width, height=height, n_in_row=n_in_row)
        self.board.init_board(start_player=start_player)

        policy = load_policy(model_file, width, height)
        self.player1 = MCTSPlayer(policy.policy_value_fn, c_puct=5, n_playout=n_playout)
        self.player2 = MCTSPlayer(policy.policy_value_fn, c_puct=5, n_playout=n_playout)
        self.player1.set_player_ind(1)
        self.player2.set_player_ind(2)
        self.players = {1: self.player1, 2: self.player2}

        self.root = root
        self.root.title("Gomoku AI vs AI (AlphaZero)")

        board_px_w = width * CELL + 2 * MARGIN
        board_px_h = height * CELL + 2 * MARGIN
        self.canvas = tk.Canvas(
            root, width=board_px_w, height=board_px_h, bg="#e8b56b", highlightthickness=0
        )
        self.canvas.pack(padx=8, pady=8)

        self.status_font = tkfont.Font(family="Helvetica", size=13)
        self.status_var = tk.StringVar(value="Loading...")
        tk.Label(root, textvariable=self.status_var, font=self.status_font).pack(pady=(0, 8))

        self.draw_grid()
        self.last_move = -1
        self.stones = {}  # move -> canvas item id
        self.thinking = False

        self.root.after(200, self.step)

    # ---------- drawing ----------
    def cell_center(self, row, col):
        x = MARGIN + col * CELL + CELL // 2
        y = MARGIN + (self.height - 1 - row) * CELL + CELL // 2
        return x, y

    def draw_grid(self):
        for i in range(self.height):
            y = MARGIN + i * CELL + CELL // 2
            self.canvas.create_line(
                MARGIN + CELL // 2,
                y,
                MARGIN + (self.width - 1) * CELL + CELL // 2,
                y,
                fill="#3b2712",
            )
        for j in range(self.width):
            x = MARGIN + j * CELL + CELL // 2
            self.canvas.create_line(
                x,
                MARGIN + CELL // 2,
                x,
                MARGIN + (self.height - 1) * CELL + CELL // 2,
                fill="#3b2712",
            )

    def draw_stone(self, move, player):
        row, col = self.board.move_to_location(move)
        x, y = self.cell_center(int(row), int(col))
        color = "#111" if player == 1 else "#f5f5f5"
        outline = "#000"
        item = self.canvas.create_oval(
            x - STONE_R, y - STONE_R, x + STONE_R, y + STONE_R, fill=color, outline=outline
        )
        self.stones[move] = item

        if self.last_move != -1 and self.last_move in self.stones:
            # remove previous highlight (if any)
            for tag in self.canvas.find_withtag("last_marker"):
                self.canvas.delete(tag)
        marker_color = "#f24" if player == 1 else "#f24"
        self.canvas.create_oval(
            x - LAST_MOVE_R,
            y - LAST_MOVE_R,
            x + LAST_MOVE_R,
            y + LAST_MOVE_R,
            fill=marker_color,
            outline="",
            tags="last_marker",
        )
        self.last_move = move

    # ---------- game loop ----------
    def step(self):
        if self.thinking:
            return
        end, winner = self.board.game_end()
        if end:
            if winner == -1:
                self.status_var.set("Game over — draw")
            else:
                who = "Black (P1)" if winner == 1 else "White (P2)"
                self.status_var.set(f"Game over — {who} wins")
            return

        current = self.board.get_current_player()
        who = "Black (P1)" if current == 1 else "White (P2)"
        move_count = len(self.board.states)
        self.status_var.set(f"Move {move_count + 1}: {who} thinking...")

        self.thinking = True

        def worker():
            player = self.players[current]
            move_num = len(self.board.states) + 1
            if move_num <= self.random_opening:
                move = random.choice(self.board.availables)
            else:
                move = player.get_action(self.board, temp=self.temp)

            def apply():
                self.board.do_move(move)
                self.draw_stone(move, current)
                self.thinking = False
                self.root.after(self.delay_ms, self.step)

            self.root.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="best_policy_8_8_5.model")
    ap.add_argument("--size", type=int, default=8, help="board width == height")
    ap.add_argument("--n-in-row", type=int, default=5)
    ap.add_argument("--playouts", type=int, default=400)
    ap.add_argument("--delay-ms", type=int, default=400)
    ap.add_argument("--temp", type=float, default=1.0,
                    help="MCTS softmax temperature over visit counts. "
                         "Lower = greedier (repeatable). Higher = more diverse. "
                         "AlphaZero self-play uses 1.0 for opening then ~0.")
    ap.add_argument("--random-opening", type=int, default=2,
                    help="Play the first N moves uniformly at random so games differ.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--start-player", type=int, default=1, choices=[0, 1],
                    help="0 = Black (P1) plays first, 1 = White (P2) plays first.")
    args = ap.parse_args()

    if args.size == 6 and args.model == "best_policy_8_8_5.model":
        args.model = "best_policy_6_6_4.model"
        args.n_in_row = 4

    root = tk.Tk()
    GomokuGUI(
        root,
        width=args.size,
        height=args.size,
        n_in_row=args.n_in_row,
        model_file=args.model,
        n_playout=args.playouts,
        delay_ms=args.delay_ms,
        temp=args.temp,
        random_opening=args.random_opening,
        seed=args.seed,
        start_player=args.start_player,
    )
    root.lift()
    root.attributes("-topmost", True)
    root.after(500, lambda: root.attributes("-topmost", False))
    root.mainloop()


if __name__ == "__main__":
    main()
