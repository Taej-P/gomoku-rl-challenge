# 오목 강화학습 챌린지

강화학습(또는 원하는 다른 방법)으로 오목 에이전트를 만들어 사전학습된 baseline 상대를
이겨보는 **개인 프로젝트**입니다. 참여자끼리 리그전으로 승률을 겨루는 이벤트로
마무리됩니다.

기반: [junxiaosong/AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku) (MIT)
의 게임 엔진과 사전학습 가중치.

---

## 게임 규칙

- 8×8 보드, **5목** (가로 / 세로 / 대각선 아무 방향)
- 흑이 선공, 최대 64수까지. 판이 다 차기 전까지는 승자가 없으면 게임 계속됨.
- 게임 엔진은 `game.py`에 있고 손댈 필요 없음.

---

## 제출물

**본인이 학습한 가중치 파일 하나**만 제출 (제출 방법은 별도 공지). 총 크기 100 MB 이하.

네트워크 구조는 `policy_value_net_pytorch.py`의 `Net` 클래스를 그대로 사용해 주세요.
평가는 이 구조로 가중치를 로드해서 진행합니다.

평가와 리그전 결과는 취합 후 별도로 공지합니다.

---

## 상대 (Baseline)

두 개의 고정 상대가 있습니다. `baseline_bot.py`에 정의되어 있고 **수정 금지**.

- **`pure_mcts`** — 신경망 없는 고전 MCTS. `n_playout = 1000`. 약~중 강도.
- **`alphazero`** — 사전학습 정책·가치망(`best_policy_8_8_5.model`)에 MCTS를 붙인 상대.
  `n_playout = 400`. 중~강 강도.

둘 다 결정적으로 두므로 재현성 있음.

---

## 에이전트 인터페이스

`student_agent.py`에 다음 함수가 반드시 있어야 합니다.

```python
def make_agent():
    return <플레이어 인스턴스>
```

인스턴스는 아래 두 메서드를 구현.

```python
class YourAgent:
    def set_player_ind(self, p):   # p = 1 (흑) 또는 2 (백). 매 게임 1회 호출됨
        ...
    def get_action(self, board):   # 합법 수 하나의 인덱스를 반환
        ...
```

`board`는 `game.Board` 인스턴스. 자주 쓸 것들:

- `board.availables` — 지금 둘 수 있는 수 인덱스 리스트
- `board.states` — `{수 인덱스: 플레이어 id}` 딕셔너리
- `board.last_move` — 마지막 수, 시작 상태면 `-1`
- `board.get_current_player()` — 1 또는 2
- `board.current_state()` — `(4, 8, 8)` numpy 배열. 현재 플레이어 관점에서
  (내 돌 / 상대 돌 / 마지막 수 위치 / 내 차례 표시)
- `board.move_to_location(move)`, `board.location_to_move([r, c])` — 인덱스 ↔ 좌표

랜덤 플레이 스텁이 파일에 이미 들어있으니, 그걸 참고해서 본인 코드로 대체하면 됩니다.

---

## 평가

### 개발용 (자기 로컬에서)

```bash
python evaluate.py --agent student_agent
```

총 100판 — 50판은 `pure_mcts`, 50판은 `alphazero`를 상대로 붙입니다. 각 세트 안에서
흑 25 / 백 25로 색깔 교대. Seed 고정이라 두 번 돌려도 같은 결과가 나옵니다.

빠르게 파이프라인만 확인하고 싶다면:
```bash
python evaluate.py --agent student_agent --games 5
```

### 리그전 (마감 후)

제출된 가중치들로 라운드로빈 리그전이 돌아가고, 헤드투헤드 승률 매트릭스와 최종 순위표
(점수 = 승 + 0.5·무, 상대별 평균 승률)가 나옵니다. 결과는 별도 공지.

---

## 시간 제약

- **학습 총 wall-clock ≤ 4시간** (본인 머신이든 Colab 무료 런타임이든).
- **평가 시 게임당 300초 (5분) 누적**. 체스식 sudden-death 방식.
  `evaluate.py`와 `league.py`가 `get_action()` 안에서 소비한 wall-clock을 누적해서
  300초 넘으면 그 게임 몰수패로 처리합니다. 게임마다 리셋.
- **가중치 총 크기 ≤ 100 MB**.

8×8에서 최대 32수까지 두므로 평균 약 9초/수. MCTS 몇백 playouts 굴리기에 충분한 예산.

---

## 어떤 방법이든 OK

- **AlphaZero 스타일 self-play** — MCTS + 정책·가치망 self-play. 상한 가장 높지만
  컴퓨트를 가장 많이 씀. `policy_value_net_pytorch.py`와 `train.py`가 출발점.
- **DQN, Double DQN** — 4×8×8 텐서 위에서 가치 학습.
- **PPO, A2C + self-play** — 정책 그래디언트 + 주기적 상대 스냅샷.
- **Behavior cloning + MCTS** — pretrained baseline이 둔 게임을 imitate → 추론 시
  MCTS를 씌움.
- **Rule-based prior + 가치 네트워크** — 위협 감지(open 3, open 4, block) 하드코딩 +
  학습된 가치망.

조합해서 써도 됩니다.

---

## 로컬 세팅

```bash
git clone <레포-URL> gomoku
cd gomoku
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy
# 학습에 PyTorch 쓸 거면
pip install torch
```

동작 확인:
```bash
python evaluate.py --games 2
```

랜덤 스텁이라 지긴 하지만 파이프라인이 도는지는 확인됩니다.

---

## Colab에서 하려면

무료 CPU 런타임으로 baseline eval 실행 가능. GPU는 학습에만 필요합니다.

### 세팅
```python
!git clone <레포-URL> /content/gomoku
%cd /content/gomoku
!pip install -q numpy torch
```

### 에이전트 편집
파일 브라우저에서 `student_agent.py`를 직접 편집하거나:
```python
%%writefile student_agent.py
# 여기에 본인 에이전트 코드
```

### 평가
```python
!python evaluate.py --agent student_agent
```

### GPU 학습
Runtime → Change runtime type → T4 GPU 선택. `train.py` 안에서:
```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
```

Colab 무료 세션은 ~12시간까지 붙지만 언제든 끊길 수 있어서 몇 분마다 체크포인트를
저장해 두는 습관 권장.

---

## 되는 것 / 안 되는 것

**되는 것**
- 아무 Python 라이브러리 (PyTorch, JAX, TensorFlow, numpy, sklearn, ...)
- `best_policy_8_8_5.model`을 imitation, self-play 스파링, warm-start 초기값 등으로 활용
- 학습 목적으로 레포 내 파일 자유롭게 읽고 수정 (아래 금지 파일 제외)

**안 되는 것**
- `baseline_bot.py`, `evaluate.py`, `league.py` 수정 — 평가는 원본으로 돌아감
- 추론 시점에 `baseline_bot.make_baseline(...)` 호출해서 상대 판단을 훔쳐보기
- 평가 중 외부 네트워크 접근
- 제공된 pretrained 가중치를 그대로 제출 (본인 학습 결과여야 함)

---

## 크레딧

게임 엔진, MCTS 구현, pretrained 가중치는
[junxiaosong/AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku)
(MIT License)에서 가져왔습니다. `baseline_bot.py`, `evaluate.py`, `league.py`,
그리고 이 문서는 챌린지용으로 새로 만든 것입니다.
