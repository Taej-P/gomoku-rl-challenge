# Gomoku RL Challenge — 7-Day Project

Train an agent to play Gomoku and beat the provided baseline opponents. You
may use any technique you like; reinforcement learning is recommended but not
required. Your grade is based on **how you evaluated your agent** (in the
report) plus **your average win rate in the inter-team league**.

---

## 1. Game

- Board: **8 × 8**
- Win condition: **5 in a row** (horizontal, vertical, or either diagonal)
- Draw only if the board fills without a winner (max 64 moves per game)
- Standard turn order — Black plays first

The engine lives in `game.py` (from
[junxiaosong/AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku),
MIT). You do not need to modify it.

---

## 2. Deliverable

A single Python module that follows the agent interface below (§4).

You will submit:

| File                | Description                                                        |
|---------------------|--------------------------------------------------------------------|
| `student_agent.py`  | Your agent. Must import cleanly and define `make_agent()`.         |
| `train.py`          | Script you used to produce your weights. Self-contained; not run at eval. |
| `training_log.txt`  | Timestamped log of your training run (start/end times visible).    |
| `report.md`         | Max 3 pages. Approach, hyperparameters, ablations, **evaluation methodology**, final results. |
| Weight files        | Whatever your agent loads at import time (`≤ 100 MB total`).       |

Zip and submit as `gomoku_<studentid>.zip`.

---

## 3. Baselines

Two fixed opponents. Both are defined in `baseline_bot.py` and **must not be
modified**.

| Baseline    | Configuration                                                                | Strength     |
|-------------|------------------------------------------------------------------------------|--------------|
| `pure_mcts` | Classical MCTS with uniform-random rollouts, `n_playout = 1000`, `c_puct = 5`. No neural network. | weak-medium  |
| `alphazero` | Pretrained AlphaZero policy/value net (`best_policy_8_8_5.model`) + MCTS, `n_playout = 400`, `c_puct = 5`. | medium-strong |

Both baselines are effectively deterministic (greedy w.r.t. MCTS visit counts).
Reproducibility across runs is guaranteed by seed-per-game in `evaluate.py`.

---

## 4. Agent Interface

`student_agent.py` must define:

```python
def make_agent():
    return <your player instance>
```

Your player must implement two methods:

```python
class YourAgent:
    def set_player_ind(self, p: int) -> None:  # p in {1, 2}. Called once per game.
        ...
    def get_action(self, board) -> int:        # returns a legal move index.
        ...
```

`board` is a `game.Board` instance. Useful members:

- `board.width`, `board.height` — both 8
- `board.n_in_row` — 5
- `board.availables` — list of legal move indices
- `board.states` — `dict[move_index -> player_id]`
- `board.last_move` — last move played, or `-1`
- `board.get_current_player()` — 1 or 2
- `board.current_state()` — `numpy` array shape `(4, 8, 8)` from the current
  player's view:
    - channel 0: my stones
    - channel 1: opponent stones
    - channel 2: last-move indicator
    - channel 3: all 1s if it is my turn, else 0s
- `board.move_to_location(move)` → `[row, col]`
- `board.location_to_move([row, col])` → `move`

A **random-play stub** lives in `student_agent.py`. Replace it with your agent.

---

## 5. Evaluation

### 5.1 Baseline eval (for your own development)

```bash
python evaluate.py --agent student_agent
```

- 100 total games: **50 vs `pure_mcts`** + **50 vs `alphazero`**
- Within each set, colors alternate: 25 games as Black, 25 as White
- Seed is fixed. Two runs of `evaluate.py` produce identical results.

Output: per-baseline W/L/D and win rate, plus overall win rate.

Quick smoke test during development:
```bash
python evaluate.py --agent student_agent --games 5     # 10 games total, ~seconds
```

Use this eval in your report to describe your development progress and
ablation results. It is the shared reference all students report against.

### 5.2 League eval (the graded event)

```bash
python league.py --teams team_A team_B team_C ...  --games 20
```

Round-robin between every pair of teams. Colors alternate. Reports a
head-to-head win-rate matrix and a final standings table (points =
`W + 0.5 * D`, average win rate across opponents).

**The instructor will run one canonical league across all submissions after
the deadline. Your average win rate in that league is your league score.**

---

## 6. Grading

Grading is holistic, based on two things:

1. **Your evaluation methodology** — how you set up experiments to measure
   your agent's strength. Reported in `report.md`. Look for: sensible
   ablations, clear tables, honest acknowledgement of what you did and did
   not try, use of `evaluate.py` numbers as a shared reference.
2. **Your league win rate** — average win rate across all opponents in the
   instructor-run inter-team league (§5.2).

There are **no fixed win-rate tiers**. A well-designed but modestly-scoring
agent, with a report that shows real engineering thought, can outscore a
higher-league-WR agent submitted without analysis.

---

## 7. Compute Constraint

Total training wall-clock ≤ **4 hours** on your own machine or a free Colab
runtime. Include start/end timestamps in `training_log.txt`.

**Inference time control at evaluation: 5 minutes (300 seconds) per game,
cumulative across all of your moves in that game.** This is a chess-style
sudden-death budget. `evaluate.py` and `league.py` accumulate the wall-clock
time spent inside your `get_action()` calls; if the total exceeds 300 seconds
during a game, that game is forfeited (recorded as a loss). Time resets at
the start of each game.

Practical implication: on an 8×8 board you play at most 32 moves per game, so
the budget averages **~9 seconds per move** — plenty for MCTS with a few
hundred playouts.

Model weights on disk: **≤ 100 MB total**.

---

## 8. Approaches (all valid)

1. **AlphaZero-style self-play** — MCTS + policy/value network trained by
   self-play. Highest ceiling but most compute-hungry. `policy_value_net_pytorch.py`
   and `train.py` in the repo give you a starting point.
2. **DQN / Double DQN** — value-based deep RL on the 4×8×8 board tensor.
3. **PPO or A2C with self-play** — policy gradient with a periodically-updated
   opponent snapshot.
4. **Behavior cloning + MCTS** — supervised imitation from games generated by
   the pretrained baseline, then wrap the learned policy with MCTS at inference.
5. **Rule-based prior + neural evaluation** — hand-coded threat detection
   (open 3, open 4, block) blended with a learned value net.

You are free to mix and match.

**Practical hint**: a learned policy/value net *without any test-time search*
has a hard time beating the `alphazero` baseline, because that baseline runs
400 MCTS simulations per move. Wrapping your learned net in an MCTS at
inference time is essentially required to reliably beat `alphazero`. The
same net, with vs. without MCTS at test time, can swing win rate by 30+
points. Budget your 5-minute per-game time for MCTS accordingly.

Also note: on 8×8, the first ~20–30 minutes of self-play mostly fill the
replay buffer and produce weak policies. Real learning kicks in after that.
Warm-starting from the pretrained `best_policy_8_8_5.model` (allowed) is a
cheap way to skip the cold-start period.

---

## 9. Local Environment Setup

```bash
git clone <course-repo-url> gomoku
cd gomoku
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy
# If you use PyTorch for training:
pip install torch
# Baseline & eval only need numpy. Baseline weights are already in the repo.
```

Verify:
```bash
python evaluate.py --games 2      # ~10 seconds, will lose (random agent stub)
```

---

## 10. Google Colab Workflow

Everything runs on a free Colab CPU runtime. A GPU runtime speeds up training
only — the baselines and evaluation do not need one.

### 10.1 Set up (one cell)

```python
!git clone <course-repo-url> /content/gomoku
%cd /content/gomoku
!pip install -q numpy torch
```

### 10.2 Develop your agent

Edit `student_agent.py` directly in the Colab file browser, or `%%writefile`:

```python
%%writefile student_agent.py
# your agent here
```

### 10.3 Baseline evaluation

```python
!python evaluate.py --agent student_agent
```

Runs in a few minutes on a Colab CPU. For quick iteration:

```python
!python evaluate.py --agent student_agent --games 5
```

### 10.4 League (instructor use)

Upload all teams' `student_agent.py` files into `/content/teams/<name>/`, then:

```python
!python league.py --teams teams/*  --games 20
```

### 10.5 Training on Colab GPU

Switch runtime to GPU (Runtime → Change runtime type → T4 GPU). Your
`train.py` should detect CUDA:

```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
```

Keep total training wall-clock within the 4-hour budget. Colab free sessions
last up to ~12 hours; if you need long runs, checkpoint every N minutes so a
disconnect doesn't cost you the run.

---

## 11. Rules

**Allowed**
- Any Python package (PyTorch, JAX, TensorFlow, numpy, scikit-learn, ...).
- Loading the provided `best_policy_8_8_5.model` for imitation learning, as a
  self-play sparring partner during training, or as a warm-start initializer.
- Reading and modifying any file in the repo *for your own training*, except
  the ones listed as frozen below.

**Not allowed**
- Modifying `baseline_bot.py`, `evaluate.py`, or `league.py`. The grader uses
  the originals.
- Querying `baseline_bot.make_baseline(...)` from your agent at inference time.
- Network access at eval time (no calls to online services).
- Submitting the pretrained baseline weights unchanged as your own agent.
  Your `training_log.txt` must show actual training took place.

---

## 12. FAQ

**Q: How is the evaluation randomized?**
A: It isn't. `evaluate.py` reseeds Python `random` and `numpy.random` at the
start of every game from `--seed + <game_index>`. If your agent is stochastic,
identical runs of `evaluate.py` will produce identical games.

**Q: Can I spend most of my time budget on early moves and play fast late?**
A: Yes. The 300-second budget is cumulative across the whole game, not per
move. Feel free to spend 30+ seconds thinking on opening/mid-game and play
end-game quickly.

**Q: Where should heavy setup (loading weights, JIT-compiling) go?**
A: In `make_agent()` or module import. `evaluate.py` builds the agent
*before* the game clock starts. Only time inside `get_action()` counts.

**Q: What does the `alphazero` baseline actually look like as an opponent?**
A: Try the AI-vs-AI visualizer:
```bash
python ai_vs_ai_gui.py --size 8 --playouts 400
```

**Q: Why 8×8 5-in-a-row instead of standard 15×15?**
A: To keep training in the range of hours, not days, on modest hardware. 8×8
is complex enough that first-move advantage isn't decisive, but small enough
that a 4-hour training run can plausibly beat both baselines.

---

## 13. Suggested Timeline

| Day | Milestone                                                                    |
|-----|------------------------------------------------------------------------------|
| 1   | Set up. Run `evaluate.py` with the stub. Pick an approach.                   |
| 2   | Prototype: small policy net trained by self-play, or a tabular baseline.     |
| 3   | First real training run. Beat `pure_mcts` at least occasionally.             |
| 4   | Iterate. Push win rate vs `pure_mcts` up. Start attacking `alphazero`.       |
| 5   | Scale up training. Ablations (net size, playouts, self-play games).          |
| 6   | Write the report. Final training run.                                        |
| 7   | Run final `evaluate.py`, package the submission zip.                         |

---

## 14. Acknowledgement

The Gomoku engine, MCTS implementations, and pretrained AlphaZero weights are
from [junxiaosong/AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku)
(MIT License). The assignment scaffolding (`baseline_bot.py`, `evaluate.py`,
`league.py`, this document) is course material.
