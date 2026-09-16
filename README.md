# 오목 강화학습 챌린지 — 7일 프로젝트

강화학습(또는 자유롭게 다른 방법)으로 오목 에이전트를 학습시켜, 제공된 두 baseline
상대를 이기는 프로젝트입니다. 채점은 (1) 리포트에 기술된 **평가 방법**과
(2) 팀 간 **리그전 평균 승률** 두 축으로 진행합니다.

이 저장소는 [junxiaosong/AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku)
(MIT)의 게임 엔진, MCTS 구현, 사전학습 가중치를 기반으로 만든 강의용 fork입니다.

---

## 1. 게임 규칙

- 보드: **8 × 8**
- 승리 조건: 가로 / 세로 / 대각선으로 **5목** 완성
- 무승부: 보드가 다 찰 때까지 승자가 없으면 (최대 64수)
- 순서: 흑(Black) 선공

게임 엔진은 `game.py`에 있으며 수정할 필요 없습니다.

---

## 2. 제출물

| 파일                | 설명                                                                 |
|---------------------|----------------------------------------------------------------------|
| `student_agent.py`  | 학생 에이전트. `make_agent()` 정의 필수 (§4).                        |
| `train.py`          | 가중치를 만든 학습 스크립트. self-contained, 채점 시 실행되진 않음. |
| `training_log.txt`  | 학습 로그 (시작/종료 시각 포함).                                     |
| `report.md`         | 최대 3페이지. 접근 방식, 하이퍼파라미터, 실험, **평가 방법**, 결과.  |
| 가중치 파일          | 에이전트가 import 시 로드하는 파일 (총 **100 MB 이하**).            |

Zip으로 묶어 `gomoku_<학번>.zip` 형식으로 제출.

---

## 3. Baseline

두 개의 고정 상대. `baseline_bot.py`에 정의되어 있으며 **수정 금지**.

| Baseline    | 구성                                                                                             | 강도  |
|-------------|--------------------------------------------------------------------------------------------------|-------|
| `pure_mcts` | 랜덤 rollout 기반 MCTS, `n_playout = 1000`, `c_puct = 5`. 신경망 없음.                            | 약~중 |
| `alphazero` | 사전학습 정책·가치망(`best_policy_8_8_5.model`) + MCTS, `n_playout = 400`, `c_puct = 5`.          | 중~강 |

둘 다 MCTS 방문 횟수의 argmax 기반이라 사실상 결정적. `evaluate.py`가 매 게임 시드
고정으로 재현성 보장.

---

## 4. 에이전트 인터페이스

`student_agent.py`에 반드시 정의:

```python
def make_agent():
    return <플레이어 인스턴스>
```

인스턴스는 두 메서드 구현:

```python
class YourAgent:
    def set_player_ind(self, p: int) -> None:  # 매 게임 1회 호출, p ∈ {1, 2}
        ...
    def get_action(self, board) -> int:        # 합법 수 인덱스 반환
        ...
```

`board`는 `game.Board` 인스턴스. 주요 속성:

- `board.width`, `board.height` — 둘 다 8
- `board.n_in_row` — 5
- `board.availables` — 합법 수 인덱스 리스트
- `board.states` — `dict[move_index → player_id]`
- `board.last_move` — 마지막 수, 아직 없으면 `-1`
- `board.get_current_player()` — 1 또는 2
- `board.current_state()` — `(4, 8, 8)` numpy 배열, 현재 플레이어 관점:
    - 채널 0: 내 돌
    - 채널 1: 상대 돌
    - 채널 2: 마지막 수 위치
    - 채널 3: 내 차례면 전체 1, 아니면 전체 0
- `board.move_to_location(move)` → `[row, col]`
- `board.location_to_move([row, col])` → `move`

랜덤 플레이 스텁이 `student_agent.py`에 이미 있으니 이걸 대체하면 됩니다.

---

## 5. 평가

### 5.1 개발용 baseline eval

```bash
python evaluate.py --agent student_agent
```

- 총 100판: **50판 vs `pure_mcts`** + **50판 vs `alphazero`**
- 각 세트 내 색깔 교대: 흑 25판, 백 25판
- Seed 고정 → 두 번 실행해도 결과 동일

출력: baseline별 W/L/D + 승률, 그리고 전체 승률.

빠른 스모크 테스트:
```bash
python evaluate.py --agent student_agent --games 5     # 총 10판, 몇 초
```

이 결과는 리포트에서 개발 진행과 ablation 근거로 사용. 모든 학생이 동일한 채점
기준을 갖게 하는 공통 지표입니다.

### 5.2 리그 eval (채점 이벤트)

```bash
python league.py --teams team_A team_B team_C ...  --games 20
```

전 팀 라운드로빈, 색깔 교대. 헤드투헤드 승률 매트릭스와 최종 순위표(점수 =
`W + 0.5 * D`, 상대별 평균 승률) 출력.

**마감 후 조교가 전체 제출물로 한 번의 canonical 리그전을 돌립니다. 이 리그에서의
평균 승률이 리그 점수입니다.**

---

## 6. 채점

두 축의 홀리스틱 채점:

1. **평가 방법론** — 에이전트 강도를 어떻게 측정했는지. `report.md`에 기술.
   합리적 ablation, 명확한 표, 시도한/안 한 것에 대한 정직한 서술,
   `evaluate.py` 수치를 공통 기준으로 활용했는지 등을 봄.
2. **리그 승률** — 조교가 마감 후 전 제출물을 한 번의 리그로 돌린 결과의 평균 승률
   (§5.2).

**고정된 승률 컷은 없습니다.** 리그 승률이 다소 낮더라도 리포트에서 엔지니어링
사고를 잘 드러내면, 리그 승률만 높고 분석 없는 제출물보다 높게 평가될 수 있습니다.

---

## 7. 컴퓨트 제약

학습 wall-clock 합계 ≤ **4시간** (본인 머신 또는 Colab 무료 런타임).
`training_log.txt`에 시작/종료 시각 명시.

**평가 시 시간 제한: 게임당 300초 (5분), 누적.** 체스 sudden-death 방식입니다.
`evaluate.py`와 `league.py`가 `get_action()` 안에서 소비된 wall-clock을 누적해
300초 초과 시 그 게임은 몰수패로 기록. 시간은 매 게임 리셋.

실질적으로 8×8에서 최대 32수까지 두므로 평균 **~9초/수** 예산. MCTS 몇백 playouts
굴리기엔 충분.

가중치 파일 크기: **총 100 MB 이하**.

---

## 8. 접근 방법 (모두 유효)

1. **AlphaZero 스타일 self-play** — MCTS + 정책·가치망 self-play 학습. 상한이 가장
   높지만 컴퓨트 소모 큼. `policy_value_net_pytorch.py`와 `train.py`가 출발점.
2. **DQN / Double DQN** — 4×8×8 보드 텐서 기반 가치 학습 딥 RL.
3. **PPO / A2C + self-play** — 정책 그래디언트 + 주기적 상대 스냅샷.
4. **Behavior cloning + MCTS** — pretrained baseline이 둔 게임을 지도학습으로
   imitate → 추론 시 MCTS를 씌움.
5. **Rule-based prior + 신경망 가치평가** — 위협 감지(open 3, open 4, block) 등
   하드코딩 + 학습된 가치망.

자유롭게 조합 가능.

**실용적 힌트**: 학습된 네트워크만으로(추론 시 탐색 없이) `alphazero` baseline을
이기기는 매우 어렵습니다 — baseline은 매 수마다 400번 MCTS 시뮬레이션을 굴리기
때문. **학습된 네트워크에 추론 시 MCTS를 씌우는 것이 사실상 필수**입니다. 같은
네트워크로 MCTS 유/무만 바꿔도 승률이 30% 이상 벌어집니다. 게임당 300초 예산을
MCTS에 안배하세요.

또한 8×8 self-play는 초반 20~30분이 대부분 replay buffer 채우기에 소진되고
실질적 학습은 그 이후 시작됩니다. 제공된 `best_policy_8_8_5.model`을 warm-start로
사용(허용)하는 게 cold-start 부담을 크게 줄이는 방법입니다.

---

## 9. 로컬 환경 세팅

```bash
git clone <레포-URL> gomoku
cd gomoku
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy
# PyTorch 학습을 쓸 경우:
pip install torch
# baseline과 eval은 numpy만 있으면 됨. 가중치는 레포에 이미 포함.
```

동작 확인:
```bash
python evaluate.py --games 2      # ~10초, 랜덤 스텁이라 짐
```

---

## 10. Google Colab

무료 CPU 런타임으로 baseline eval과 리그 eval 모두 가능. GPU는 학습에만 필요.

### 10.1 세팅 (한 셀)
```python
!git clone <레포-URL> /content/gomoku
%cd /content/gomoku
!pip install -q numpy torch
```

### 10.2 에이전트 개발
Colab 파일 브라우저에서 `student_agent.py` 직접 편집하거나 `%%writefile`:
```python
%%writefile student_agent.py
# 당신의 에이전트 코드
```

### 10.3 Baseline eval
```python
!python evaluate.py --agent student_agent
```
빠른 반복:
```python
!python evaluate.py --agent student_agent --games 5
```

### 10.4 리그전 (조교용)
팀별 `student_agent.py`를 `/content/teams/<팀명>/`에 업로드 후:
```python
!python league.py --teams teams/*  --games 20
```

### 10.5 Colab GPU 학습
Runtime → Change runtime type → T4 GPU. `train.py`에서:
```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
```
학습 wall-clock은 4시간 예산 내. Colab 무료 세션은 ~12시간까지 가능. 연결 끊김
대비해 몇 분마다 체크포인트 저장 권장.

---

## 11. 규칙

**허용**
- 어떤 Python 라이브러리든 (PyTorch, JAX, TensorFlow, numpy, scikit-learn, ...)
- 제공된 `best_policy_8_8_5.model`을 imitation learning, self-play 스파링 상대,
  또는 warm-start 초기값으로 사용
- 학습 목적으로 레포 내 파일을 자유롭게 읽고 수정 (아래 금지 파일 제외)

**금지**
- `baseline_bot.py`, `evaluate.py`, `league.py` 수정 (조교는 원본 사용)
- 추론 시 `baseline_bot.make_baseline(...)` 호출로 상대의 판단을 오라클처럼 이용
- 평가 시 네트워크 접속 (외부 서비스 호출 금지)
- 사전학습 가중치를 그대로 제출 — `training_log.txt`에 실제 학습 흔적이 있어야 함

---

## 12. FAQ

**Q: 평가는 어떻게 랜덤화되나요?**
A: 랜덤화하지 않습니다. `evaluate.py`는 매 게임 시작 시 `--seed + <game_index>`로
Python `random`과 `numpy.random`을 재시드하므로, 에이전트가 확률적이더라도 동일한
실행은 동일한 결과를 냅니다.

**Q: 초반에 시간을 몰아쓰고 후반은 빠르게 둬도 되나요?**
A: 네. 300초 예산은 게임 전체 누적입니다. 오프닝/미드게임에서 30초 이상 생각하고
엔드게임은 빨리 두는 방식 OK.

**Q: 가중치 로딩, JIT 컴파일 같은 무거운 초기화는 어디서 해야 하나요?**
A: `make_agent()` 안 또는 모듈 import 시점에서. 게임 시계는 그 이후에 시작하고
`get_action()` 안의 시간만 카운트됩니다.

**Q: `alphazero` baseline이 실제로 어떻게 두는지 보고 싶어요.**
A: 뷰어 사용:
```bash
python ai_vs_ai_gui.py --size 8 --playouts 400
```

**Q: 왜 8×8 5목인가요? 정식 15×15는?**
A: 학습을 며칠이 아니라 시간 단위로 끝낼 수 있게 하기 위해. 8×8은 선공 프리미엄이
결정적이지 않을 정도로 복잡하면서도, 4시간 학습으로 baseline을 이길 여지가
있을 정도로 관리 가능합니다.

---

## 13. 권장 타임라인

| Day | 마일스톤                                                                 |
|-----|--------------------------------------------------------------------------|
| 1   | 환경 세팅. 랜덤 스텁으로 `evaluate.py` 확인. 접근 방법 결정.            |
| 2   | 프로토타입: 작은 정책망 self-play 또는 간단한 baseline.                |
| 3   | 첫 실제 학습. `pure_mcts`에 가끔이라도 승리.                             |
| 4   | 반복 개선. `pure_mcts` 승률 올림. `alphazero` 공략 시작.                |
| 5   | 학습 확장. Ablation (네트워크 크기, playouts, self-play 게임 수).       |
| 6   | 리포트 작성. 최종 학습.                                                  |
| 7   | 최종 `evaluate.py` 실행, 제출 zip 패키징.                                |

---

## 14. 크레딧

게임 엔진, MCTS 구현, 사전학습 가중치는
[junxiaosong/AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku)
(MIT License)에서 가져왔습니다. 강의 스캐폴딩 (`baseline_bot.py`,
`evaluate.py`, `league.py`, 이 문서)은 강의 자료입니다.
