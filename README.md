# AI Harness Engineering Template

> 한국어 · [English](./README.en.md)

AI 에이전트가 자율적으로 일하되, 안전하게 통제할 수 있는 환경을 만드는 템플릿.
**Harness(구조적 가드레일) + Ouroboros(명세 기반 개발) + 3-Tier Layered Architecture**를 통합.

> "프롬프트는 부탁이고, 하네스는 강제다."
> "프롬프팅을 멈추고, 명세부터 시작하라."

---

## README 읽는 법

이 README는 두 부분으로 나뉩니다.

- 앞부분은 이 fork에서 추가한 Trace / Replay Test / 결과 저장 구조를 설명합니다.
- `Releases` 이후는 원본 `ai-harness-template`의 상세 설명을 유지한 영역입니다.

전체를 다 읽기 어렵다면 [SUMMARY.md](./SUMMARY.md)를 먼저 보세요. 팀원에게 공유할 때는 `SUMMARY.md`로 큰 그림을 잡고, 실제 설치나 검증이 필요할 때 이 README의 해당 챕터를 보면 됩니다.

### 30초 요약

이 레포는 원본 하네스의 workflow 의미를 바꾸지 않고, 관측 가능성만 추가한 버전입니다.

- 각 단계는 `[Harness Trace]`와 `[Spec Evidence]`로 어떤 command/reference/agent 파일과 Rule ID를 근거로 판단했는지 보여줍니다.
- Runtime Trace는 가능한 경우 실제 선택/로딩된 파일을 `.harness/trace`에 기록합니다.
- `/replay-test`는 전체 우로보로스 루프를 다시 돌리지 않고 특정 단계만 fixture로 검증합니다.
- replay 결과는 `tests/results/runs`, `tests/results/latest`, `tests/results/baseline` 구조로 관리합니다.
- 빈 프로젝트에서는 이 템플릿 폴더에서 바로 작업하는 것이 아니라 `./init.sh <target-project>`로 설치한 뒤 대상 프로젝트에서 `claude`를 실행합니다.

### 챕터별 목차

| 챕터 | 언제 읽나 | 링크 |
|------|-----------|------|
| 요약본 | 처음 보는 팀원에게 빠르게 설명할 때 | [SUMMARY.md](./SUMMARY.md) |
| 만든 이유 | 왜 이 fork가 필요한지 이해할 때 | [이 레포를 만든 이유](#이-레포를-만든-이유-trace-가능한-ai-harness) |
| Step 1 | Harness Trace / Spec Evidence / Runtime Trace가 무엇인지 볼 때 | [Step 1. Harness Trace / Spec Evidence 추가](#step-1-harness-trace--spec-evidence-추가) |
| Step 2 | `/replay-test`가 왜 필요하고 어떻게 검증하는지 볼 때 | [Step 2. Replay Test 구조 추가](#step-2-replay-test-구조-추가) |
| Step 3 | replay 결과가 어디에 저장되는지 볼 때 | [Step 3. Replay Test 결과 자동 저장](#step-3-replay-test-결과-자동-저장) |
| 팀 사용 순서 | 팀 운영 흐름을 정할 때 | [팀에서 사용하는 순서](#팀에서-사용하는-순서) |
| 빈 프로젝트 적용 | 새 프로젝트에 하네스를 설치할 때 | [빈 프로젝트에서 바로 쓰는 간단 매뉴얼](#빈-프로젝트에서-바로-쓰는-간단-매뉴얼) |
| 원본 하네스 상세 | 원본 기능, 설치 옵션, 게이트, 에이전트를 볼 때 | [Releases](#releases) 이후 |

### 추천 읽기 순서

처음 보는 팀원은 `SUMMARY.md` → `빈 프로젝트에서 바로 쓰는 간단 매뉴얼` → `팀에서 사용하는 순서`만 먼저 읽어도 됩니다.

하네스 설계를 담당하는 사람은 `Step 1` → `Step 2` → `Step 3` → `Replay Test 사용법` → `claude_mediated` lineage 설명까지 확인하는 것을 권장합니다.

## 이 레포를 만든 이유: Trace 가능한 AI Harness

이 레포는 원본 [`studioKjm/ai-harness-template`](https://github.com/studioKjm/ai-harness-template)을 기반으로 만든 팀용 커스터마이징 버전입니다.

원본 하네스의 핵심은 그대로 유지했습니다. AI가 바로 코딩하지 않고 `/interview`, `/seed`, `/trd`, `/decompose`, `/run`, `/evaluate`, `/evolve` 흐름을 따르도록 하는 구조는 바꾸지 않았습니다. 이 fork의 목적은 그 흐름 위에 “AI가 어떤 파일과 어떤 규칙을 근거로 판단했는지”를 사람이 확인할 수 있는 관측 가능성(observability)을 추가하는 것입니다.

쉽게 말하면 원본 하네스가 “AI가 지켜야 할 작업 절차”라면, 이 레포는 그 절차를 지키는 과정에서 “무엇을 보고 그렇게 판단했는지”를 남기는 버전입니다.

### 우리가 해결하려는 문제

AI 협업에서 팀원이 가장 답답해하는 지점은 보통 결과 자체보다 근거입니다.

- AI가 어떤 command 문서를 기준으로 실행했는가?
- 최신 seed spec, TRD, task 파일을 실제로 반영했는가?
- 어떤 agent persona가 판단에 영향을 줬는가?
- 어떤 Rule ID가 현재 판단에 적용됐는가?
- 명시 규칙이 없는데 AI가 임의로 근거를 만든 것은 아닌가?
- Trace 기능을 고친 뒤 전체 우로보로스 루프를 매번 다시 돌리지 않고 빠르게 검증할 수 있는가?

이 레포는 위 질문에 답하기 위해 세 단계로 커스터마이징했습니다.

| Step | 커밋 | 목적 | 결과 |
|------|------|------|------|
| Step 1 | `0529027 Add harness trace observability` | Harness Trace / Spec Evidence / Runtime Trace 추가 | AI 판단 근거를 Rule ID와 파일 경로로 추적 |
| Step 2 | `21ceeb0 Add replay test harness` | 전체 루프 없이 단계별 fixture replay 테스트 추가 | `/replay-test`로 특정 단계만 빠르게 검증 |
| Step 3 | `f9c918c Persist replay test results` | replay 결과를 파일로 자동 저장 | `tests/results`에 실행 이력, 최신 결과, baseline 구조 저장 |

중요한 제한은 계속 지켰습니다.

- 기존 command/spec/agent/evaluate 문서의 의미는 바꾸지 않았습니다.
- 기존 워크플로우 단계와 에이전트 역할, 검증 기준은 유지했습니다.
- 기존 규칙을 삭제하거나 요약본으로 대체하지 않았습니다.
- 추가한 것은 관측, 테스트, 결과 저장 레이어입니다.

---

## Step 1. Harness Trace / Spec Evidence 추가

### 왜 했나

원본 하네스는 명세 기반 workflow와 gate가 잘 잡혀 있지만, AI가 각 단계에서 어떤 문서와 어떤 규칙을 근거로 판단했는지 사용자에게 설명하는 구조는 약했습니다. 그래서 “하네스 기준에 따랐다”가 아니라 “어떤 파일의 어떤 Rule ID를 근거로 따랐다”를 출력하도록 만들었습니다.

### 실행 결과

각 주요 단계는 다음 형태의 trace를 출력하도록 설계됐습니다.

```text
[Harness Trace]
Current Step:
Request Type:
Applied Command Files:
Applied Reference Files:
Applied Agent Files:
Key Rules Applied:
Next Step:
```

판단 근거는 다음처럼 출력합니다.

```text
[Spec Evidence]
1. <file_path>#<rule_id>
   Rule: "<existing rule sentence or short summary>"
   Applied because: <why this rule applies now>
```

명시 규칙이 없으면 근거를 꾸며내지 않고 다음처럼 출력합니다.

```text
[Spec Evidence]
No explicit spec rule found.
Recommendation:
- Suggest which file should receive a new explicit rule for this situation.
```

### AS-IS / TO-BE: `templates/CLAUDE.md.hbs`

이 파일은 하네스를 다른 프로젝트에 설치할 때 생성될 `CLAUDE.md`의 원본 템플릿입니다.

AS-IS:

```markdown
### Before Starting Work
1. Read `ARCHITECTURE_INVARIANTS.md`
2. Check `docs/adr.yaml` for relevant architectural decisions
3. For new features: run `/interview` to clarify scope first
4. Understand the scope of changes
```

TO-BE:

````markdown
### Harness Trace & Spec Evidence

Trace is observability only. It must not change command semantics, specification content, agent roles, or gate criteria.

**Trace types**
- **AI-facing Trace**: explanation shown to the user at major workflow steps.
- **Runtime Trace**: execution log written by `.harness/trace/record-runtime-trace.sh` from selected command/reference/agent files.

**Required user output**

```text
[Harness Trace]
Current Step:
Request Type:
Applied Command Files:
Applied Reference Files:
Applied Agent Files:
Key Rules Applied:
Next Step:
```
````

차이:

- 원본의 “작업 전 읽어야 할 문서” 규칙은 유지했습니다.
- 그 앞에 Trace 출력 의무와 Runtime Trace 우선 원칙을 추가했습니다.
- 세부 업무 규칙을 `CLAUDE.md`에 몰아넣지 않고, 기존 command/agent/reference 파일을 계속 근거로 삼게 했습니다.

### AS-IS / TO-BE: `commands/run.md`

AS-IS:

```markdown
### Phase 0: State Audit (FIRST STEP)

1. **Read latest seed** from `.harness/ouroboros/seeds/seed-v*.yaml`
```

TO-BE:

```markdown
## Trace Metadata

- Rule ID: `RULE-RUN-001`
- Runtime Trace: run `.harness/trace/record-runtime-trace.sh --step run --request-type implementation --summary "<user request summary>"` before Phase 0 when the script exists.
- AI-facing Trace: use `.harness/trace/latest-runtime-trace.json` when available; otherwise list only files actually read.

### Phase 0: State Audit (FIRST STEP)

`RULE-RUN-001`

1. **Read latest seed** from `.harness/ouroboros/seeds/seed-v*.yaml`
```

차이:

- `/run`의 실행 의미는 바꾸지 않았습니다.
- 기존 “latest seed를 읽는다”는 규칙에 식별자만 붙였습니다.
- Runtime Trace 스크립트가 실제 선택 파일과 Rule ID를 기록할 수 있게 했습니다.

### AS-IS / TO-BE: `init.sh`

AS-IS:

```bash
success "Ouroboros templates installed"

# ─── Step 8.5: Install methodology plugin system ─────────────────
header "Step 8.5: Installing methodology plugin system"
```

TO-BE:

```bash
success "Ouroboros templates installed"

# Install Runtime Trace tools (observability only)
if [ -d "$HARNESS_DIR/trace" ]; then
  mkdir -p "$TARGET/.harness/trace"
  cp "$HARNESS_DIR/trace/"* "$TARGET/.harness/trace/" 2>/dev/null || true
  chmod +x "$TARGET/.harness/trace/"*.sh 2>/dev/null || true
  success "Runtime Trace tools installed"
fi

# ─── Step 8.5: Installing methodology plugin system
header "Step 8.5: Installing methodology plugin system"
```

차이:

- 설치 흐름은 유지했습니다.
- 추가로 `.harness/trace/record-runtime-trace.sh`가 설치되게 했습니다.
- 이 스크립트는 판단을 바꾸지 않고 실행 로그만 남깁니다.

### Step 1 산출물

- `trace/README.md`
- `trace/record-runtime-trace.sh`
- `templates/CLAUDE.md.hbs` Trace 섹션
- `commands/interview.md`, `commands/seed.md`, `commands/trd.md`, `commands/decompose.md`, `commands/run.md`, `commands/evaluate.md`, `commands/evolve.md`의 Rule ID / Trace Metadata
- 일부 core agent 문서의 persona Rule ID

---

## Step 2. Replay Test 구조 추가

### 왜 했나

Trace 기능을 추가하면 다음 문제가 생깁니다. 작은 규칙 하나를 바꿨는지 확인하려고 매번 `/interview → /seed → /trd → /decompose → /run → /evaluate` 전체를 실행하면 너무 느립니다.

그래서 특정 단계의 직전 산출물 fixture만 넣고 target step 하나를 replay해서 검증하는 `/replay-test` 구조를 추가했습니다.

`/replay-test`는 실제 개발 명령이 아닙니다. 개발 산출물을 만들지 않고, trace와 output이 기대대로 나왔는지 검사하는 테스트 명령입니다.

### `/run` 같은 command는 무엇이 실행하나

중요한 점이 있습니다. 이 레포 안에 `/run`을 직접 실행하는 bash/python dispatcher는 없습니다.

```text
commands/run.md              # 원본 slash command 지시문
        ↓ init.sh가 복사
.claude/commands/run.md      # 설치된 프로젝트의 slash command
        ↓ 사용자가 Claude Code에서 /run 입력
Claude Code                  # markdown 지시문을 읽고 수행하는 실제 runtime
```

즉 `commands/*.md`는 실행 파일이 아니라 Claude Code가 읽는 작업 지시문입니다. 그래서 replay도 “Python이 `/decompose`를 직접 실행한다”가 아니라, “Claude Code 세션이 target command md와 fixture를 읽어 replay 산출물을 새로 만들고, Python runner가 그 actual 결과를 검증한다”가 정확한 표현입니다.

### 신뢰도 기준

Replay에는 세 가지 수준이 있습니다.

| 모드 | 의미 | 신뢰도 |
|------|------|--------|
| `captured` | 이미 저장된 `actual_trace` / `actual_output` 파일을 검증 | 낮음~중간 |
| `claude_mediated` | 현재 Claude Code 세션이 target command md와 fixture로 actual 결과를 새로 생성 | 중간~높음 |
| `claude_cli` | 향후 Claude CLI/API로 비대화 실행 | 가장 높음, 추후 확장 대상 |

하네스 설계 검증에는 최소 `claude_mediated`를 권장합니다. `captured`는 빠른 assertion 확인이나 문서 예시에 적합합니다.

### Replay Test 사용법: 처음 보는 사람을 위한 흐름

Replay Test는 “전체 우로보로스 workflow를 다시 실행하지 않고, 특정 단계 하나만 fixture로 재현해 검증하는 절차”입니다.

핵심 입력과 출력은 다음과 같습니다.

| 구분 | 위치 | 의미 |
|------|------|------|
| Test case | `tests/cases/*.yaml` | 어떤 단계(`/decompose`, `/evaluate` 등)를 어떤 fixture와 기대값으로 검증할지 정의 |
| Input fixtures | `tests/fixtures/**` | 해당 단계 직전까지 이미 만들어졌다고 가정하는 입력 산출물 |
| Expected values | case YAML의 `expected_trace`, `expected_output` | 반드시 포함되어야 할 Rule ID, 문구, 금지 패턴 |
| Actual trace | `tests/results/runs/<run_id>/actual_trace.md` | replay 실행 중 실제 생성된 Harness Trace / Spec Evidence |
| Actual output | `tests/results/runs/<run_id>/actual_output.md` | replay 실행 중 실제 생성된 target step 산출물 |
| Result artifacts | `tests/results/runs/<run_id>/` | 검증 결과, trace, output, diff, summary, lineage |

#### 1. 빠른 assertion 확인: `captured` 모드

이미 저장된 actual trace/output 샘플을 검증할 때 사용합니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml
```

이 모드는 빠릅니다. 다만 `tests/expected/**`에 있는 캡처 파일을 actual로 읽을 수 있으므로, 하네스 설계 검증의 최종 근거로는 약합니다. 문서 예시나 assertion 로직 확인에 적합합니다.

#### 2. 실제 command md 기반 replay: `claude_mediated` 모드

하네스 설계를 검증하려면 이 흐름을 사용합니다.

먼저 replay run을 준비합니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml \
  --execution-mode claude_mediated \
  --prepare-replay
```

이 명령은 실행 결과를 검증하지 않고, 다음 파일들을 먼저 만듭니다.

```text
tests/results/runs/<run_id>/
  replay_prompt.md   # Claude Code가 실제 replay를 수행할 때 읽는 지시문
  lineage.yaml       # command/fixture/case의 초기 lineage
  workspace/         # replay-only scratch 공간
```

그 다음 Claude Code 세션에서 `replay_prompt.md`를 읽고 그대로 수행합니다.

```text
1. target command file을 읽는다. 예: commands/decompose.md
2. input fixture를 읽는다. 예: tests/fixtures/seed/*.yaml, tests/fixtures/trd/*.md
3. target command 지시문을 fixture 상태에만 적용한다.
4. production 파일은 수정하지 않는다.
5. actual_trace.md와 actual_output.md를 새로 작성한다.
```

생성되어야 하는 실제 산출물은 다음입니다.

```text
tests/results/runs/<run_id>/
  actual_trace.md    # 실제 Harness Trace + Spec Evidence
  actual_output.md   # 실제 target step output
```

마지막으로 actual artifact를 검증합니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml \
  --execution-mode claude_mediated \
  --run-dir tests/results/runs/<run_id>
```

이때 runner는 `tests/expected/**`를 actual로 대신 쓰지 않습니다. `actual_trace.md`, `actual_output.md`가 없으면 실패합니다.

#### 3. 결과를 확인하는 위치

검증이 끝나면 다음 파일을 보면 됩니다.

```text
tests/results/runs/<run_id>/summary.md          # 사람이 읽는 요약
tests/results/runs/<run_id>/replay_result.yaml  # 구조화된 PASS/FAIL 결과
tests/results/runs/<run_id>/diff.md             # expected와 actual 차이
tests/results/runs/<run_id>/lineage.yaml        # 산출물 출처와 이전 단계 lineage
```

가장 최근 결과만 보고 싶으면:

```text
tests/results/latest/<test_id>/summary.md
tests/results/latest/<test_id>/replay_result.yaml
```

기준 결과로 승격하려면 명시적으로 실행합니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml \
  --execution-mode claude_mediated \
  --run-dir tests/results/runs/<run_id> \
  --promote-baseline
```

baseline은 자동 갱신되지 않습니다. 팀 리뷰를 거친 “기준으로 삼을 만한 결과”만 baseline으로 올리는 것을 의도했습니다.

### 실행 결과

다음처럼 특정 단계만 빠르게 검증할 수 있습니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml
python3 tests/replay/replay_runner.py /evaluate data_pipeline_missing_quality
```

실제 command md 기반 replay를 준비하려면:

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml \
  --execution-mode claude_mediated \
  --prepare-replay
```

이 명령은 `tests/results/runs/<run_id>/replay_prompt.md`와 `lineage.yaml`을 만듭니다. Claude Code 세션에서 `replay_prompt.md`를 읽고 target command file과 fixture를 적용해 `actual_trace.md`, `actual_output.md`를 새로 작성한 뒤, 다음 명령으로 검증합니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml \
  --execution-mode claude_mediated \
  --run-dir tests/results/runs/<run_id>
```

예시 결과:

```text
[Replay Test Result]
Test ID: TEST-DECOMP-DP-CDC-001
Target Step: /decompose
Case: data_pipeline_cdc

[Harness Trace Check]
PASS - RULE-DECOMP-DP-001
PASS - RULE-DP-001
PASS - RULE-DP-003
PASS - RULE-DP-CDC-001

[Output Check]
PASS - CDC 변경순서 기준 확인
PASS - Raw CDC 적재
PASS - Quality validation

Result: PASS
```

### AS-IS / TO-BE: command 구조

AS-IS:

```text
commands/
  interview.md
  seed.md
  trd.md
  decompose.md
  run.md
  evaluate.md
  evolve.md
```

TO-BE:

```text
commands/
  interview.md
  seed.md
  trd.md
  decompose.md
  run.md
  evaluate.md
  evolve.md
  replay-test.md
```

`commands/replay-test.md` 핵심 내용:

```markdown
# /replay-test — Stage Replay Test

`/replay-test` is a verification command, not a development command.

It must not:
- create or modify production feature artifacts
- replace `/interview`, `/seed`, `/trd`, `/decompose`, `/run`, `/evaluate`, or `/evolve`
- change existing Harness Trace / Spec Evidence behavior
- introduce a separate `/trace` command
```

차이:

- 기존 workflow command는 바꾸지 않았습니다.
- `/trace` 같은 별도 추적 명령도 만들지 않았습니다.
- 오직 테스트용 `/replay-test`만 추가했습니다.

### AS-IS / TO-BE: 테스트 디렉터리

AS-IS:

```text
# tests 디렉터리 없음
```

TO-BE:

```text
tests/
  fixtures/
    interview/
    seed/
    trd/
    decompose/
    run_outputs/
  expected/
    traces/
    outputs/
    interview/
  cases/
    test_interview_single_turn.yaml
    test_interview_multi_turn.yaml
    test_seed_data_pipeline_cdc.yaml
    test_decompose_data_pipeline_cdc.yaml
    test_evaluate_missing_quality.yaml
  replay/
    replay_runner.py
    trace_assert.py
    output_assert.py
```

차이:

- 전체 E2E를 돌리지 않아도 단계별 fixture로 검증할 수 있습니다.
- `/interview`는 이전 산출물이 없으므로 사용자 요청과 turns fixture를 사용합니다.
- `/evaluate` replay에서 `PASS`는 산출물이 좋다는 뜻이 아니라, 기대한 실패를 평가기가 정확히 감지했다는 뜻입니다.

### AS-IS / TO-BE: `tests/replay/replay_runner.py`

AS-IS:

```text
# replay runner 없음
```

TO-BE:

```python
case_path = resolve_case(args.target_or_path, args.case)
case_data = load_case(case_path)

trace_path = resolve_path(case_data.get("actual_trace") or case_data.get("captured_trace"))
if trace_path:
    trace = load_trace(trace_path)
    results.extend(check_trace(trace, case_data.get("expected_trace", {}) or {}))

if output:
    results.extend(check_output(output, case_data.get("expected_output", {}) or {}))
```

차이:

- YAML case를 읽습니다.
- expected trace와 actual trace를 비교합니다.
- expected output과 actual output을 비교합니다.
- 금지 패턴이 output에 포함됐는지도 확인합니다.
- `claude_mediated` 모드에서는 `tests/expected/**`를 actual로 대신 쓰지 못하게 막습니다.

### Step 2 산출물

- `commands/replay-test.md`
- `tests/replay/replay_runner.py`
- `tests/replay/trace_assert.py`
- `tests/replay/output_assert.py`
- `tests/cases/*.yaml`
- `tests/fixtures/**`
- `tests/expected/**`

---

## Step 3. Replay Test 결과 자동 저장

### 왜 했나

Step 2의 replay test는 콘솔에서 PASS/FAIL을 볼 수 있었지만, 실행 결과가 화면에만 남으면 팀 리뷰나 회귀 비교에 쓰기 어렵습니다. 그래서 각 실행 결과를 파일로 저장하도록 바꿨습니다.

### 실행 결과

replay test를 실행하면 콘솔 출력과 함께 artifact 경로가 표시됩니다.

```text
[Replay Artifacts]
replay_result: tests/results/runs/20260519T091123Z_TEST-DECOMP-DP-CDC-001/replay_result.yaml
actual_trace: tests/results/runs/20260519T091123Z_TEST-DECOMP-DP-CDC-001/actual_trace.md
actual_output: tests/results/runs/20260519T091123Z_TEST-DECOMP-DP-CDC-001/actual_output.md
diff: tests/results/runs/20260519T091123Z_TEST-DECOMP-DP-CDC-001/diff.md
summary: tests/results/runs/20260519T091123Z_TEST-DECOMP-DP-CDC-001/summary.md
latest_dir: tests/results/latest/TEST-DECOMP-DP-CDC-001
```

저장 구조:

```text
tests/results/
  runs/
    <timestamp>_<test_id>/
      replay_result.yaml
      actual_trace.md
      actual_output.md
      diff.md
      summary.md
  latest/
    <test_id>/
      replay_result.yaml
      actual_trace.md
      actual_output.md
      diff.md
      summary.md
  baseline/
    <test_id>/
      replay_result.yaml
      actual_trace.md
      actual_output.md
```

`runs`는 실행 이력을 누적합니다. `latest`는 test_id별 최신 결과를 갱신합니다. `baseline`은 자동으로 갱신하지 않습니다. 사용자가 명시적으로 baseline 승격을 요청할 때만 갱신합니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml --promote-baseline
```

각 실행은 lineage도 함께 남깁니다.

```yaml
lineage:
  execution_mode: claude_mediated
  target_step: /decompose
  target_command_file: commands/decompose.md
  target_command_sha256: "..."
  command_git_commit: "..."
  case_file: tests/cases/test_decompose_data_pipeline_cdc.yaml
  case_sha256: "..."
  input_fixtures:
    - path: tests/fixtures/seed/data_pipeline_cdc_seed.yaml
      sha256: "..."
      source_step: /seed
      source_run_id: external_fixture
  actual_output_sha256: "..."
  actual_trace_sha256: "..."
  model_or_executor: Claude Code session
  generated_at: "..."
```

이 lineage 덕분에 replay 산출물이 어떤 command 파일, 어떤 fixture, 어떤 git commit, 어떤 실행 모드에서 나왔는지 추적할 수 있습니다.

### AS-IS / TO-BE: `replay_runner.py` 결과 처리

AS-IS:

```python
print(render(case_data, results))
return 0 if all(item["status"] == "PASS" for item in results) else 1
```

TO-BE:

```python
artifacts = write_artifacts(
    case_data=case_data,
    trace=trace,
    output=output,
    results=results,
    expected_output_path=output_path,
    promote_baseline=args.promote_baseline,
)

report = render(case_data, results)
lines = [report, "", "[Replay Artifacts]"]
for key, path in artifacts.items():
    lines.append(f"{key}: {path}")
print("\n".join(lines))
```

차이:

- 콘솔 출력만 하던 runner가 결과 파일을 저장합니다.
- 실행별 이력과 최신 결과를 동시에 관리합니다.
- baseline은 `--promote-baseline`을 줄 때만 갱신합니다.

### AS-IS / TO-BE: `replay_result.yaml`

AS-IS:

```text
# 파일 없음
```

TO-BE:

```yaml
test_id: TEST-DECOMP-DP-CDC-001
target_step: /decompose
case: data_pipeline_cdc
run_id: 20260519T091123Z_TEST-DECOMP-DP-CDC-001
timestamp: 20260519T091123Z
status: PASS
input_fixtures:
  - tests/fixtures/seed/data_pipeline_cdc_seed.yaml
  - tests/fixtures/trd/data_pipeline_cdc_trd.md
expected_trace:
  must_include_rule_ids:
    - RULE-DECOMP-DP-001
actual_rule_ids:
  - RULE-DECOMP-001
  - RULE-DECOMP-DP-001
trace_assertions:
  -
    section: Harness Trace Check
    status: PASS
    item: RULE-DECOMP-DP-001
result_artifact_paths:
  replay_result: tests/results/runs/<run_id>/replay_result.yaml
  actual_trace: tests/results/runs/<run_id>/actual_trace.md
  actual_output: tests/results/runs/<run_id>/actual_output.md
  diff: tests/results/runs/<run_id>/diff.md
  summary: tests/results/runs/<run_id>/summary.md
  lineage: tests/results/runs/<run_id>/lineage.yaml
```

차이:

- 실행 결과를 사람이 읽을 수 있는 YAML로 남깁니다.
- 어떤 Rule ID가 실제로 잡혔는지 기록합니다.
- trace, output, diff, summary 파일 경로를 함께 남깁니다.

### AS-IS / TO-BE: `tests/results/.gitignore`

AS-IS:

```text
# tests/results 구조 없음
```

TO-BE:

```gitignore
runs/
latest/

# Baselines are intentional review artifacts. Commit them only when promoted.
!baseline/
!baseline/**/
```

차이:

- 실행할 때마다 쌓이는 `runs`와 `latest`는 기본적으로 git에 올리지 않습니다.
- baseline은 의도적으로 승격했을 때만 리뷰 artifact로 관리할 수 있게 했습니다.

### Step 3 산출물

- `tests/results/.gitignore`
- `tests/replay/replay_runner.py` 결과 저장 로직
- `commands/replay-test.md` artifact 저장 안내
- README의 `tests/results` 구조 안내

---

## 팀에서 사용하는 순서

1. 새 프로젝트에 하네스를 설치합니다.
2. 기존처럼 `/interview`, `/seed`, `/trd`, `/decompose`, `/run`, `/evaluate`를 사용합니다.
3. 각 단계에서 `[Harness Trace]`와 `[Spec Evidence]`를 확인합니다.
4. 규칙이나 trace를 바꿨다면 전체 루프 대신 `/replay-test`로 필요한 단계만 검증합니다.
5. 테스트 결과는 `tests/results/latest/<test_id>/summary.md`와 `replay_result.yaml`에서 확인합니다.
6. 기준 결과로 삼고 싶을 때만 `--promote-baseline`을 사용합니다.

이 fork의 목표는 AI를 더 많이 믿게 만드는 것이 아닙니다. AI의 판단을 사람이 검토할 수 있게 만들고, 그 검토 구조가 계속 깨지지 않는지 빠르게 확인하는 것입니다.

## 빈 프로젝트에서 바로 쓰는 간단 매뉴얼

이 레포는 “작업할 프로젝트 자체”가 아니라, 다른 프로젝트에 Claude Code용 하네스를 설치하는 템플릿입니다. 따라서 빈 프로젝트에서 사용하려면 먼저 `init.sh`로 하네스를 설치해야 합니다.

### 1. 템플릿 압축 해제

```bash
tar -xzf ai-harness-template-trace-fork.tar.gz
cd ai-harness-template
```

### 2. 빈 프로젝트 준비

```bash
mkdir ../my-empty-project
cd ../my-empty-project
git init
```

이미 사용 중인 프로젝트가 있다면 새 폴더를 만들 필요 없이 그 프로젝트 경로를 사용하면 됩니다.

### 3. 하네스 설치

```bash
cd ../ai-harness-template
./init.sh ../my-empty-project
```

설치가 끝나면 대상 프로젝트에 다음 파일들이 생깁니다.

```text
my-empty-project/
  CLAUDE.md
  ARCHITECTURE_INVARIANTS.md
  .claude/commands/
  .claude/agents/
  .harness/
```

Claude Code의 `/interview`, `/seed`, `/run` 같은 slash command는 템플릿의 `commands/*.md`를 직접 실행하는 것이 아니라, 설치된 프로젝트의 `.claude/commands/*.md`를 읽고 동작합니다.

### 4. Claude Code 실행

```bash
cd ../my-empty-project
claude
```

Claude Code 안에서 다음 순서로 사용합니다.

```text
/interview  # 요구사항 인터뷰
/seed       # seed spec 생성
/trd        # 기술 설계 정리
/decompose  # 구현 task 분해
/run        # task 실행
/evaluate   # 결과 평가
/evolve     # 규칙 개선 필요 시 반영
```

각 단계 결과에는 `[Harness Trace]`와 `[Spec Evidence]`가 함께 출력되어야 합니다. 이 출력으로 Claude가 어떤 command/reference/agent 파일과 Rule ID를 근거로 판단했는지 확인합니다.

### 5. Replay Test 사용

특정 단계만 다시 검증하고 싶을 때는 `/replay-test`를 사용합니다. 이 명령은 실제 기능 개발 명령이 아니라, fixture와 기대값을 비교하는 검증 명령입니다.

```text
/replay-test decompose data_pipeline_cdc
/replay-test evaluate data_pipeline_missing_quality
```

Python runner를 직접 실행해 빠르게 확인할 수도 있습니다.

```bash
python3 tests/replay/replay_runner.py tests/cases/test_decompose_data_pipeline_cdc.yaml
```

실행 결과는 화면에만 남지 않고 다음 위치에 저장됩니다.

```text
tests/results/runs/<timestamp>_<test_id>/
tests/results/latest/<test_id>/
```

`summary.md`는 사람이 읽는 요약이고, `replay_result.yaml`은 자동화와 리뷰에 사용할 수 있는 구조화 결과입니다. 실제 command md 기반 신뢰도를 확인하려면 `claude_mediated` 모드를 사용하고, 생성된 `lineage.yaml`에서 어떤 command 파일과 fixture에서 산출물이 나왔는지 확인합니다.

## Releases

> **권장 설치: `v2.6.0` (최신 안정).** 모든 릴리즈가 `stable` 상태이며, 메서드 번들은 `/methodology` 커맨드로 선택 활성화합니다.

| 버전 | 날짜 | 상태 | 주요 변경 |
|------|------|------|----------|
| [**v2.6.0**](https://github.com/studioKjm/ai-harness-template/releases/tag/v2.6.0) | 2026-05-15 | `stable` ⭐ **권장** | **Isolated AI Security Gate** — 코딩 에이전트와 완전히 분리된 보안 전용 에이전트. 확증 편향 없이 취약점 탐지. claude CLI(Pro/Max) 우선, ANTHROPIC_API_KEY 폴백. critical/high 발견 시 커밋 차단. (NON-BREAKING) |
| [**v2.5.3**](https://github.com/studioKjm/ai-harness-template/releases/tag/v2.5.3) | 2026-05-06 | `stable` | **Workflow Gate Fix** — AI가 `/seed` 후 `/trd`·`/decompose`를 건너뛰고 `/run`으로 직행하던 구조적 버그 수정. CLAUDE.md 워크플로우 다이어그램, seed 완료 메시지, /run Prerequisites 3곳 동시 수정. (NON-BREAKING) |
| [**v2.5.2**](https://github.com/studioKjm/ai-harness-template/releases/tag/v2.5.2) | 2026-05-04 | `stable` | **AI Behavioral Baseline** — Karpathy 4원칙을 `CLAUDE.md`에 통합. 메서드 선택과 무관하게 항상 적용. `check-surgical-changes` opt-in 게이트 추가. (NON-BREAKING) |
| [**v2.5.0**](https://github.com/studioKjm/ai-harness-template/releases/tag/v2.5.0) | 2026-05-01 | `stable` | **메서드 16종 완성** — ddd-lite·bdd·shape-up 포함 총 16종 번들 확정. `/install` 마법사에서 Lean/Dev/Domain/Full 선택 설치 지원. (NON-BREAKING) |
| [**v2.2.0**](https://github.com/studioKjm/ai-harness-template/releases/tag/v2.2.0) | 2026-04-29 | `stable` | **Methodology Plugin System** — 하네스 코어 고정, 개발 방법론 플러그인 분리. `/methodology compose <a> <b>` 다중 활성화. (NON-BREAKING) |
| [**v2.1.0**](https://github.com/studioKjm/ai-harness-template/releases/tag/v2.1.0) | 2026-04-19 | `stable` | **Pair Mode** — AC complexity 기반 선택적 활성화, Navigator를 persistent background agent로 전환 (SendMessage 양방향 통신), Test Designer worktree 격리, Mixed Mode (direct+pair 혼합), 자동 /review 체크포인트. PairCoder(ASE 2024) + AgentCoder 논문 기반. |
| [**v2.0.0**](https://github.com/studioKjm/ai-harness-template/releases/tag/v2.0.0) | 2026-04-12 | `stable` | **Unified layout** — `.ouroboros/`를 `.harness/ouroboros/`로 통합. opt-in 게이트 4종 분리. (BREAKING) |
| [**v1.0.0**](https://github.com/studioKjm/ai-harness-template/releases/tag/v1.0.0) | 2026-04-12 | `stable` | 최초 릴리즈 — 11 게이트, 10 커맨드, 9 에이전트, 3-Tier 아키텍처 강제. |

**메서드 번들 도입 가이드:**
- 16종 번들 모두 `stable`. `/methodology list`로 확인, `/methodology use <name>`으로 활성화.
- 코어 7개 게이트는 항상 강제. 메서드별 추가 게이트는 활성화 시에만 적용.
- 처음 도입은 `Lean(ouroboros)` 또는 `Dev(ouroboros + bdd + tdd-strict + exploration)` 번들 권장.

## 데모 영상

**1분 요약**

https://github.com/user-attachments/assets/87a778e3-1fee-451e-9e18-f0cda740e7da

**풀버전 (5분)** — [![YouTube](https://img.shields.io/badge/YouTube-%EC%B2%AB%EB%B2%88%EC%A7%B8%20%EB%B3%B4%EA%B8%B0-red?logo=youtube)](https://youtu.be/bMjHYh0FZZI)

[![AI Harness Engineering Template 데모](https://img.youtube.com/vi/bMjHYh0FZZI/maxresdefault.jpg)](https://youtu.be/bMjHYh0FZZI)


---

## 목차

- [시스템 전체 구조](#시스템-전체-구조)
- [Quick Start](#quick-start)
- [Methodology System (v0.1)](#methodology-system-v01)
- [하네스 6가지 구성요소](#하네스-6가지-구성요소)
- [Ouroboros 워크플로우](#ouroboros-워크플로우)
- [12개 게이트](#12개-게이트)
- [AI Security Gate](#ai-security-gate)
- [3-Tier Layered Architecture](#3-tier-layered-architecture)
- [11개 에이전트 페르소나 + Orchestration](#11개-에이전트-페르소나)
- [Lite vs Pro 비교](#lite-vs-pro)
- [Pro 버전 상세](#pro-버전-상세)
- [설치 상세](#설치-상세)
- [디렉토리 구조](#디렉토리-구조)
- [데이터 흐름](#데이터-흐름)
- [Examples](#examples)
- [Acknowledgments](#acknowledgments--inspirations)

---

## 시스템 전체 구조

```
┌───────────────────────────────────────────────────────────────────┐
│  OUROBOROS (명세 기반 개발 루프)                                    │
│  /interview → /seed → /trd → /decompose → /run → /evaluate       │
│       ↑                                                │          │
│       └──────── /evolve (수렴까지 반복) ────────────────┘          │
└───────────────────────────────────────────────────────────────────┘
                          ↕ (강제됨)
┌───────────────────────────────────────────────────────────────────┐
│  HARNESS GATES (12개 구조적 가드레일)                               │
│  boundaries | layers | secrets | security | structure | spec       │
│  | complexity | deps | mutation | performance | ai-antipatterns    │
│  | security-ai                                                      │
└───────────────────────────────────────────────────────────────────┘
                          ↕ (학습됨)
┌───────────────────────────────────────────────────────────────────┐
│  FEEDBACK LOOP (자기 강화)                                         │
│  위반 감지 → 분류 → 규칙 추가 → 게이트 반영 → 시스템 강건화          │
└───────────────────────────────────────────────────────────────────┘
```

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| 명세가 먼저 | 코딩 전에 인터뷰 → 시드 스펙 확정 |
| 구조적 강제 | 규칙은 가이드라인이 아닌 게이트(차단)로 강제 |
| 불변 명세 | 시드 스펙은 수정 불가, 변경은 새 버전 생성 |
| 자기 강화 | 위반 → 규칙 진화 → 시스템이 점점 강건해짐 |
| 3-tier 아키텍처 | Presentation / Logic / Data 레이어 분리 필수 |
| 점진적 채택 | 전부 쓸 필요 없이 개별 컴포넌트 선택 가능 |
| 메서드 플러그인 | 하네스 코어는 고정, 개발 방법론은 사용자 선택·조합 |

---

## Methodology System (v0.1)

> 하네스 코어는 **고정**. 메서드는 **플러그인**으로 사용자가 선택·조합. **번들 16종**.

### 어떤 방법론을 골라야 하나?

#### 결정 트리

```
지금 뭐 하려는 중이세요?
│
├─ 🆕 0→1 (신규 프로젝트)
│   ├─ 단순 시작 ──────────────────────► ouroboros (기본)
│   ├─ 스토리·AC 정리 필요 ────────────► ouroboros + bmad-lite
│   ├─ 가설 먼저 검증하고 싶음 ─────────► lean-mvp (단독 또는 추가)
│   └─ 큰 아키텍처 결정 ─────────────► ouroboros + bmad-lite + rfc-driven
│
├─ 🔧 1→N (기존 확장)
│   ├─ 기능 추가 (시드 진화) ──────────► ouroboros + living-spec [+ bmad-lite]
│   ├─ 함수 시그니처 변경 ─────────────► + parallel-change
│   ├─ 모듈/시스템 교체 ──────────────► + strangler-fig
│   ├─ 복잡한 리팩터링 (의존성 불명확) ──► + mikado-method
│   └─ 클라이언트 레거시 인수 ─────────► strangler-fig (단독 가능)
│
├─ ❓ 미지수
│   ├─ 라이브러리 검증 / PoC ──────────► exploration (어느 조합에든 추가)
│   └─ 기능 효과 검증 (A/B 대신) ───────► lean-mvp (가설 기반 측정)
│
├─ 🧪 품질
│   └─ 테스트 우선 엄격 강제 ──────────► tdd-strict (blocking gate)
│
├─ 🏛 도메인 설계
│   ├─ 경계 모호, 용어 혼재 ────────────► ddd-lite
│   └─ 비즈니스 언어로 시나리오 ─────────► bdd [+ tdd-strict]
│
├─ 🎯 계획·스코프
│   └─ Appetite 기반 사이클 ─────────────► shape-up [+ lean-mvp]
│
├─ 🛡 운영·신뢰성
│   ├─ 결제·인증·민감 정보 다룸 ──────► + threat-model-lite
│   ├─ 메트릭·SLO 설계 필요 ──────────► + observability-first
│   └─ 장애 발생 ────────────────────► + incident-review
│
└─ 🐛 단순 버그 수정 ─────────────────► (메서드 불필요, 게이트만 작동)
```

#### 상황별 추천 매트릭스

| 상황 | 추천 조합 | 왜 |
|-----|---------|----|
| **개인 사이드 프로젝트** | `ouroboros` 또는 `exploration` 단독 | 무겁지 않고 명확 |
| **신규 외주 SaaS MVP** | `ouroboros + bmad-lite` | 명세 + 스토리 양쪽 강제 |
| **외주 SaaS 보안 강화** | `+ threat-model-lite + observability-first` | 결제·인증·PII 안전망 |
| **외주 SaaS 유지보수** | `ouroboros + bmad-lite + living-spec + incident-review` | 진화 + 장애 학습 |
| **레거시 인수 + 점진 개편** | `strangler-fig + parallel-change [+ ouroboros]` | 모듈+함수 양쪽 안전 |
| **큰 아키텍처 결정** | `+ rfc-driven` | 합의 + 페이퍼 트레일 |
| **신규 라이브러리·인프라 검증** | `exploration` (단독 또는 추가) | 샌드박스 자유 실험 |
| **혼자 / 1인 외주 운영자** | `ouroboros` (단순) → 필요 시 추가 | 페르소나 분리는 오버킬 |
| **6명 이상 팀 풀 BMAD** | (이 템플릿 X) → [BMAD-METHOD 본가](https://github.com/bmadcode/BMAD-METHOD) | bmad-lite는 의도적 축소판 |

#### 안티패턴 (이건 쓰지 마세요)

| 상황 | 잘못된 선택 | 올바른 선택 |
|-----|----------|----------|
| 단순 버그 수정 | `bmad-lite` (스토리 강제) | 메서드 없이 수정 (게이트만 작동) |
| "한 번만 빠르게 짜보자" | `ouroboros` (인터뷰 통과 필요) | `exploration` (timebox 스파이크) |
| 외부 라이브러리 PoC | `parallel-change` (오버킬) | `exploration` |
| 시드 없는데 스토리부터 | `bmad-lite` (prereq 차단) | `ouroboros` 먼저 → `bmad-lite` 추가 |
| DB 마이그레이션 그냥 진행 | `ouroboros`만 | `+ parallel-change` 필수 |
| 모듈 단위 마이그레이션 | `parallel-change` (함수 단위라 부족) | `strangler-fig` (모듈 단위 + facade) |
| 코드 후 RFC 작성 | `rfc-driven` 사후 | ADR로 충분 (`docs/adr.yaml`) |
| 메트릭 사후 추가 | `observability-first` 사후 | 새 기능부터 적용 |
| Slack에서 "고쳤다"로 종료 | (메서드 없음) | `incident-review` 활용 |

### 16종 메서드 한눈에

| 메서드 | 적용 단계 | 한 줄 요약 |
|-------|---------|----------|
| 🐍 **ouroboros** | 0→1 (기본) | 명세 우선 — Ambiguity ≤ 0.2까지 인터뷰 |
| 🔄 **living-spec** | 1→N | 시드 진화 — 두 버전 의미적 diff + 태스크 마이그레이션 |
| ⫶ **parallel-change** | 1→N | 호환 깨는 변경 (함수 단위) — Expand → Migrate → Contract |
| 🎭 **bmad-lite** | 0→1, 1→N | 페르소나(analyst/ux-designer/pm-strict) + 스토리 분해 |
| 🔭 **exploration** | 모든 단계 | 시간 박스 스파이크 — 샌드박스 게이트 완화 |
| 🌿 **strangler-fig** | 1→N | 모듈·시스템 단위 교체 — facade 라우팅 + 4-state |
| 🚨 **incident-review** | 운영 | blameless postmortem — 5-state + action items + 패턴 분석 |
| 🛡 **threat-model-lite** | 모든 단계 | STRIDE 위협 모델링 — security-reviewer 페르소나 |
| 📊 **observability-first** | 0→1, 1→N | 메트릭·로그·트레이스·SLO를 설계 산출물로 |
| 📜 **rfc-driven** | 모든 단계 | 큰 변경은 코드 전 RFC — 5-state + LOC 임계값 게이트 |
| 🔴 **tdd-strict** | 모든 단계 | Red→Green→Refactor — 테스트 우선을 git 히스토리 게이트로 강제 |
| 🧪 **lean-mvp** | 0→1, 1→N | Build→Measure→Learn — 가설 기반 MVP 검증, pivot or persist |
| 🎋 **mikado-method** | 1→N | Goal→try→revert→prerequisites — 트리 기반 점진적 리팩터링 |
| 🏛️ **ddd-lite** | 0→1, 1→N | Bounded Context + Aggregate + Ubiquitous Language — 경계 게이트 강제 |
| 🎭 **bdd** | 모든 단계 | Given/When/Then 시나리오 — 비즈니스·개발 언어 연결, tdd-strict 짝꿍 |
| 🎯 **shape-up** | 0→1, 1→N | Appetite + Pitch + Betting Table — 고정 시간·가변 범위 (Basecamp) |

### 활성화 명령

```bash
/methodology list                                            # 메서드 목록 (16종)
/methodology current                                         # 현재 활성 메서드
/methodology use ouroboros                                   # 단일 활성화
/methodology compose ouroboros bmad-lite                     # 다중 조합
/methodology compose ouroboros bmad-lite living-spec         # 외주 SaaS 유지보수
/methodology compose ouroboros bmad-lite threat-model-lite observability-first  # 보안 강화 SaaS
/methodology compose strangler-fig parallel-change           # 레거시 인수 + 점진 교체
/methodology info <name>                                     # 메서드 상세
/methodology deactivate <name>                               # 비활성화
```

### 더 자세히

- 메서드 비교표·조합 매트릭스: [`docs/methodology-catalog.md`](./docs/methodology-catalog.md)
- 시스템 구조·매니페스트 스키마·사용자 정의 방법: [`docs/methodology-guide.md`](./docs/methodology-guide.md)
- 각 메서드 상세 README: [`methodologies/<name>/README.md`](./methodologies/)

---

## Quick Start

어떤 방식으로 설치하든 `/install` 마법사를 사용할 수 있습니다.

### 옵션 A: 설치 마법사 (권장)

```bash
git clone https://github.com/studioKjm/ai-harness-template.git
```

Claude Code에서 **클론한 하네스 디렉토리**를 열고:

```
/install /path/to/your-project
```

대화형 마법사가 단계별 질문을 통해 최적의 설정을 안내합니다:

```
① 구성 선택        Full(Pair Mode 포함) / Minimal(제외)  ← v2.5.3 기준
② 트랙 선택        Lite (bash only) / Pro (Python)
③ 권한 프리셋      Strict / Standard / Permissive
④ Pair Mode       Auto / Always On / Off  (Full 구성만)
⑤ 게이트 구성      기본 7개 + opt-in 선택
⑥ 메서드 번들      Lean / Dev / Domain / Full  (16종 중 선택)
⑦ Git Hooks       설치 / 스킵
⑧ CI/CD           GitHub Actions 설치 / 스킵
⑨ 스택 감지        자동 / 수동 선택
```

설치 완료 후에는 대상 프로젝트에서도 `/install`을 실행할 수 있습니다 (재설치·설정 변경 시 사용).

### 옵션 B: 원라인 설치

마법사 없이 CLI 플래그로 직접 설치합니다:

```bash
# Stable + Lite (기본값)
./ai-harness-template/init.sh /path/to/your-project --yes

# Experimental + Pair Mode Auto
./ai-harness-template/init.sh /path/to/your-project --yes \
  --version experimental --pair-mode auto

# Pro 추가 설치
./ai-harness-template/pro/install.sh /path/to/your-project
```

<details>
<summary>init.sh 전체 옵션 보기</summary>

| 플래그 | 값 | 기본값 | 설명 |
|--------|-----|--------|------|
| `--yes`, `-y` | - | - | 모든 확인 스킵 |
| `--preset` | strict / standard / permissive | standard | 권한 프리셋 |
| `--version` | stable / experimental | stable | 설치 버전 |
| `--pair-mode` | auto / on / off | off | Pair Mode 설정 (experimental만) |
| `--gates` | +complexity,+performance,+ai-antipatterns,+security-ai | - | opt-in 게이트 추가 |
| `--no-hooks` | - | - | Git pre-commit hook 스킵 |
| `--no-ci` | - | - | GitHub Actions 스킵 |
| `--stack` | auto / nextjs-django / python / nodejs ... | auto | 스택 감지 방식 |
| `--name` | 문자열 | 디렉토리명 | 프로젝트 이름 |

</details>

### 옵션 C: Claude Code 플러그인

```
/plugin marketplace add studioKjm/ai-harness-template
/plugin install harness@studioKjm-harness
```

플러그인 설치 후 `/install`로 마법사를 실행할 수 있습니다.
커맨드/에이전트만 필요하면 이 방법으로 충분하고, 게이트·훅·템플릿까지 원하면 마법사가 나머지를 안내합니다.

---

## 하네스 6가지 구성요소

| # | 구성요소 | 설명 | 구현물 |
|---|---------|------|--------|
| 1 | **규칙 전달** (CLAUDE.md) | AI가 읽는 컨텍스트 파일 | `CLAUDE.md.hbs`, `ARCHITECTURE_INVARIANTS.md.hbs`, `code-convention.yaml` |
| 2 | **위험 차단** (Permissions) | AI 접근 범위 제한 | `boundaries/presets/` (strict/standard/permissive) |
| 3 | **자동 검증** (Hooks) | 편집/커밋 시 자동 실행 | `pre-commit-gate.sh`, `post-edit-lint.sh`, Pro hooks |
| 4 | **테스트 도구** (MCP) | 외부 에이전트에서 게이트 호출 | `mcp/server.py` — 11개 게이트 + 시드/인터뷰/감사 도구 |
| 5 | **AI 분리** (Subagent) | 작업별 에이전트 위임 | `/seed`, `/run`, `/evaluate`, `/evolve`에 명시적 subagent 패턴 |
| 6 | **진화 원칙** (메타 원칙) | 실패 → 규칙 추가 → 진화 | `evolve-rules.md`, `/evolve` 커맨드, 수렴 판정 |

---

## Ouroboros 워크플로우

```
/interview    →    /seed    →    /trd     →   /decompose  →    /run    →    /evaluate    →    /evolve
 (명세 확정)    (스펙 생성)    (기술 설계)    (태스크 분해)     (구현)      (검증)           (진화)
      ↑                                                                                      │
      └────────────────────────── ontology 수렴까지 반복 ─────────────────────────────────────┘
```

### 12개 커맨드

| Command | Description | Agent | Subagent |
|---------|-------------|-------|----------|
| `/interview` | 소크라테스 인터뷰 (숨겨진 가정 발견) | Interviewer | - |
| `/seed` | 불변 시드 스펙 생성 | Seed Architect | Ontologist (도메인 추출) |
| `/trd` | 3-tier 기반 기술 설계서 (논의 먼저 → 설계) | Executor | - |
| `/decompose` | 원자적 태스크 분해 + 레이어별 검증 | Decomposer | - |
| `/run` | Double Diamond 실행 (D→L→P 순서) | Executor | Explore (병렬 탐색) |
| `/evaluate` | 3단계 검증 (Mechanical→Semantic→Judgment) | Evaluator | Gate Runner (기계적 검증) |
| `/evolve` | 진화 루프 (수렴까지) | Evolver | Contrarian+Simplifier+Researcher (병렬 분석) |
| `/rollback` | Saga 패턴 롤백 (stash/checkout/branch) | Rollback Guardian | - |
| `/unstuck` | 막혔을 때 5 에이전트 다각도 돌파 | 5 Agents | - |
| `/pm` | PRD 자동 생성 | PM | - |

### /interview — 소크라테스식 인터뷰

4개 차원 추적으로 모호성을 수치화:

| 차원 | 비중 | 목표 질문 |
|------|------|----------|
| Goal Clarity | 40% | 무엇을 만들고 싶은가? 누구를 위한 것인가? |
| Constraint Clarity | 30% | 절대 하면 안 되는 것은? 기술 스택 제약은? |
| Success Criteria | 30% | 완료를 어떻게 판단하나? 엣지 케이스는? |
| Context Clarity | 15% | 기존 코드 구조는? 영향 범위는? (brownfield만) |

> Greenfield: G(40%) + C(30%) + S(30%) = 100%.
> Brownfield: G(35%) + C(25%) + S(25%) + X(15%) = 100% (자동 재조정).

**게이트**: `ambiguity = 1.0 - Σ(clarity_i × weight_i)` ≤ 0.2 이어야 `/seed` 진행 가능

### /seed — 불변 명세

시드 스펙 구조:
```yaml
version: 1
goal: { summary, detail, non_goals }
constraints: { must, must_not, should }
acceptance_criteria: [{ id, description, verification, priority }]
ontology:
  entities: [{ name, fields, relationships }]
  actions: [{ name, actor, input, output, side_effects }]
architecture:
  pattern: "3-tier-layered"
  layers: { presentation, logic, data }
  layer_communication: { presentation_to_logic, logic_to_data, data_format }
scope: { mvp, future }
tech_decisions: [{ decision, reason, alternatives }]
```

**불변 원칙**: seed-v1.yaml 생성 후 수정 불가. 변경은 seed-v2.yaml로.

### /trd — 기술 설계서

바로 설계서를 작성하지 않는다. **논의 먼저**:

```
Phase 1: 탐색 (문서/코드 파악) → Phase 2: 큰 그림 (P/L/D별)
→ Phase 3: 논의점 (resource/impact 설명) → Phase 4: 최종 설계서
→ Phase 5: 레이어별 테스트 설계
```

### /decompose — 원자적 태스크 분해

각 AC를 레이어 단위로 분해하고 의존성 순서를 결정:
```
AC-001: "사용자가 검색하면 매물을 보여준다"
  → T-001 [Data]: 검색 쿼리 레포지토리 + 테스트
  → T-002 [Logic]: 필터링 서비스 + 테스트
  → T-003 [Present]: 검색 API 엔드포인트 + 테스트
```

### /run — Double Diamond (레이어 기반)

| Phase | 활동 |
|-------|------|
| Discover | 시드 재확인, 코드베이스 탐색 (subagent 병렬) |
| Define | 범위 확정, 구현 순서, 테스트 전략 |
| **Design** | **레이어 영향 분석 → 레이어별 설계 → DTO 계약 → 테스트 전략** |
| **Deliver** | **Data → Logic → Presentation 순서, 모듈마다 즉시 테스트** |

### /evaluate — 3단계 검증

```
Stage 1 Mechanical: 게이트 + lint + build + tests
Stage 2 Semantic:   AC 준수 + 목표 정합 + 레이어 컴플라이언스 + 온톨로지 드리프트
Stage 3 Judgment:   코드 품질 + 엣지 케이스 (선택적)
```

### /evolve — 진화 루프

`Wonder → Reflect → Re-seed`. 수렴 판정: 온톨로지 유사도 ≥ 0.95 → 완료.

---

## 12개 게이트

### 차단 게이트 (위반 시 커밋/CI 차단)

| 게이트 | 검사 대상 |
|--------|----------|
| `check-boundaries.sh` | `boundaries.yaml` 기반 금지 import 패턴 |
| `check-layers.sh` | 3-tier 레이어 분리 (P→D 스킵, L→P 역참조) |
| `check-secrets.sh` | 35+ 시크릿 패턴 (AWS, GitHub, Stripe, JWT, Firebase 등) |
| `check-security.sh` | SAST 정적 보안 분석 (Semgrep/Bandit + 11개 내장 패턴) |
| `check-structure.sh` | 파일 배치 규칙 (.env, SQL migrations) |
| `check-spec.sh` | 시드 스펙 필수 필드 완성도 |
| `check-deps.sh` | npm/pip/go/cargo audit 의존성 취약점 |
| `check-mutation.sh` | 뮤테이션 테스트 점수 (mutmut/Stryker) |

### 경고 게이트 (차단하지 않음, 리뷰 권장)

| 게이트 | 검사 대상 |
|--------|----------|
| `check-complexity.sh` | 함수 길이(80L), 파라미터(5개), 파일 길이(500L), 중첩(5단계) |
| `check-performance.sh` | 파일 크기, 의존성 수, 빌드 출력, import 깊이 |
| `check-ai-antipatterns.sh` | 환각 API, 과잉 추상화, 네이밍 드리프트, 미사용 import |

### Opt-in 차단 게이트 (활성화 시 critical/high 발견 → 커밋 차단)

| 게이트 | 검사 대상 |
|--------|----------|
| `check-security-ai.sh` | 격리된 AI 보안 분석 — 코딩 에이전트와 완전히 분리된 신선한 Claude 세션으로 의미적 취약점 탐지. critical/high 발견 시 커밋 차단. `HARNESS_ENABLE_AI_SECURITY=1`로 활성화. |

### 실행 시점

```
git commit  → pre-commit hook → 자동 실행
CI push/PR  → .github/workflows/harness-gates.yaml
수동        → .harness/detect-violations.sh
MCP         → harness mcp-serve (외부 에이전트에서 호출)
```

---

## AI Security Gate

> v2.6.0에서 추가된 opt-in 차단 게이트. 코딩 에이전트와 **완전히 격리된** 신선한 Claude 세션으로 취약점을 탐지한다.

### 왜 격리가 필요한가?

코딩 에이전트는 자신이 작성한 코드의 의도를 안다 — "이렇게 짠 이유가 있다"는 확증 편향이 생긴다.
AI Security Gate는 해당 컨텍스트를 **완전히 차단**한 독립 프로세스가 코드만 보고 취약점을 찾는다.

```
코딩 에이전트 (확증 편향 있음)
    ↕ 완전 격리 (컨텍스트 공유 없음)
보안 에이전트 (신선한 Claude 세션 · 적대적 페르소나)
    → 결과: findings.json (팀 공유)
```

### 설치

**옵션 1: `/install` 마법사 (권장)**

```
/install /path/to/your-project
```

Phase 2 게이트 선택에서 `+ AI Security (격리된 보안 분석)`을 체크한다.

**옵션 2: CLI 플래그**

```bash
./init.sh /path/to/your-project --yes --gates +security-ai
```

설치 후 생성되는 파일:

```
.harness/
├── gates/check-security-ai.sh      # 게이트 스크립트
└── security/
    ├── findings.json               # 누적 취약점 (git 커밋 권장)
    ├── dismissed.txt               # 기각된 오탐 (git 커밋 권장)
    └── dismiss-finding.sh          # 기각 헬퍼
```

### 사용법

**수동 실행**

```bash
# 변경된 파일만 스캔 (빠름)
bash .harness/gates/check-security-ai.sh .

# 전체 코드베이스 스캔
bash .harness/gates/check-security-ai.sh . --full-scan

# 결과를 마크다운으로 내보내기
bash .harness/gates/check-security-ai.sh . --export=markdown
```

**pre-commit hook 자동 실행**

```bash
# 환경 변수로 활성화 (비활성화가 기본값)
export HARNESS_ENABLE_AI_SECURITY=1
git commit -m "..."   # 커밋 시 자동 실행
```

**결과 확인**

```bash
cat .harness/security/findings.json
```

```json
{
  "findings": [
    {
      "id": "SEC-001",
      "severity": "critical",
      "title": "SQL Injection in search endpoint",
      "file": "src/api/search.py",
      "line": 42,
      "description": "..."
    }
  ]
}
```

**오탐 기각**

```bash
bash .harness/security/dismiss-finding.sh SEC-001 "파라미터 바인딩으로 이미 처리됨"
```

기각 이유는 `dismissed.txt`에 기록되며 다음 스캔에서 자동으로 제외된다.

### GitHub Actions CI 연동

`check-security-ai.sh`는 **claude CLI 세션**을 사용하므로 클라우드 runner와 직접 연동하려면 `ANTHROPIC_API_KEY`가 필요하다. 구독(Pro/Max)을 그대로 쓰려면 Option A(self-hosted runner)를 권장한다.

**Option A — Self-hosted runner (Pro/Max 구독, API 키 불필요)**

자신의 Mac을 GitHub Actions runner로 등록:

```
GitHub repo → Settings → Actions → Runners → New self-hosted runner
```

`.github/workflows/harness-gates.yaml`에서 아래 주석 해제:

```yaml
ai-security-gate:
  name: AI Security Gate (Isolated Agent)
  runs-on: self-hosted          # claude CLI가 설치된 로컬 머신
  needs: default-gates
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - name: AI Security Analysis
      run: bash .harness/gates/check-security-ai.sh . --full-scan
      # claude -p는 로컬 Pro/Max 세션을 사용 — ANTHROPIC_API_KEY 불필요
```

**Option B — GitHub-hosted runner (ANTHROPIC_API_KEY 사용)**

```
Settings → Secrets and variables → Actions → New secret
Name: ANTHROPIC_API_KEY
```

`.github/workflows/harness-gates.yaml`에서 Option B 블록 주석 해제:

```yaml
ai-security-gate:
  name: AI Security Gate (Isolated Agent)
  runs-on: ubuntu-latest
  needs: default-gates
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - name: AI Security Analysis
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
          echo "::warning::ANTHROPIC_API_KEY not set — skipping."
          exit 0
        fi
        bash .harness/gates/check-security-ai.sh . --full-scan
```

비용: ~$0.01–0.10 / 스캔 (claude-opus-4-7, 최대 50파일 / 80KB)

### 취약점 생명주기

```
발견 (findings.json)
    ↓
코드 수정 → 재스캔 → 자동 해소
    또는
오탐 기각 → dismiss-finding.sh → dismissed.txt
```

`findings.json`과 `dismissed.txt`는 팀 공유를 위해 **git에 커밋 권장**.
`SECURITY_REPORT.md` (--export=markdown 결과물)는 `.gitignore`에 포함되어 있어 커밋되지 않는다.

---

## 3-Tier Layered Architecture

### 레이어 정의

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Presentation    │────→│     Logic        │────→│      Data        │
│  (사용자 소통)    │     │  (비즈니스 규칙)   │     │  (데이터 소통)    │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ UI, HTTP 경계     │     │ 알고리즘, 검증    │     │ DB 조작          │
│ 입력 검증         │     │ 트랜잭션 관리     │     │ 외부 API 호출    │
│ 응답 포맷팅       │     │ 서비스 조율       │     │ 캐싱             │
└──────────────────┘     └──────────────────┘     └──────────────────┘

  ✅ Presentation → Logic → Data (순방향만 허용)
  ❌ Presentation → Data (레이어 스킵 금지)
  ❌ Logic → Presentation (역참조 금지)
  ❌ Data → Logic (역참조 금지)
```

### 스택별 매핑

| Layer | Next.js | NestJS | FastAPI | Django |
|-------|---------|--------|---------|--------|
| **Presentation** | pages, Components | Controllers, DTOs | Routes, Pydantic | Views, Templates |
| **Logic** | services, Server Actions | Services, Domain | Services | Models/Managers |
| **Data** | Prisma Client, repos | TypeORM, Repositories | SQLAlchemy, repos | Django ORM |

### 레이어별 테스트

| Layer | 테스트 유형 | 원칙 |
|-------|-----------|------|
| **Logic** | 단위 테스트 | 순수 비즈니스 로직, mock은 경계에서만 |
| **Data** | 통합 테스트 | 실제 DB/외부 서비스 |
| **Presentation** | E2E/API | UI 렌더링, 라우팅 |

**핵심**: 구현과 테스트를 함께 작성. 일괄 작성 금지. mock으로 접착제 코드를 테스트하지 않는다.

---

## 11개 에이전트 페르소나

### 코어 (4개)

| Agent | Role | When |
|-------|------|------|
| **Interviewer** | 질문만 한다 (답 금지) | `/interview` |
| **Ontologist** | 도메인 모델 추출 | `/seed` (subagent) |
| **Seed Architect** | 스펙 결정화 | `/seed` |
| **Evaluator** | 3단계 검증 | `/evaluate` |

### 확장 (5개)

| Agent | Perspective | When |
|-------|------------|------|
| **Contrarian** | "만약 반대라면?" | `/unstuck`, `/evolve` |
| **Simplifier** | "제거할 건 없나?" | `/unstuck`, `/evolve` |
| **Researcher** | "증거는?" | `/unstuck`, `/evolve` |
| **Architect** | "구조가 원인인가?" | `/unstuck` |
| **Hacker** | "우회로는?" | `/unstuck` |

### Pair Mode (2개) — v2.1.0

| Agent | Role | Lifecycle | When |
|-------|------|-----------|------|
| **Navigator** | 플랜 3개 생성, 최적 선택, 결과 검토 | Background (SendMessage) | `/run` Pair Mode (medium/high AC) |
| **Test Designer** | AC 기반 독립 테스트 설계 (구현 코드 미참조) | One-shot (worktree 격리) | `/run` Pair Mode (high AC) |

### Pair Mode 작동 방식

```
seed spec의 AC complexity에 따라 자동 판단:

  low complexity   → Direct 구현 (기존 방식)
  medium complexity → Navigator 플랜 + Driver 구현
  high complexity  → Navigator + Driver + Test Designer (worktree 격리)

Mixed Mode: low를 먼저 구현 → medium/high를 Pair로 구현
```

```
Driver(메인 에이전트)
  │
  ├─ spawn Navigator (background, persistent)
  │   ├─ SendMessage: "AC-001 플랜 요청" → Navigator 응답: 3 plans
  │   ├─ Driver 구현
  │   ├─ SendMessage: "결과 보고" → Navigator 응답: Pass/Retry/Switch
  │   └─ 반복 (최대 5회 왕복)
  │
  └─ spawn Test Designer (worktree, one-shot)
      └─ seed spec + AC만으로 독립 테스트 작성 (src/ 접근 불가)
```

### Orchestration Topology (`agents/topology.yaml`)

| 패턴 | 설명 | 사용 |
|------|------|------|
| **Pipeline** | 순차 실행 (출력→입력) | `/interview` → `/seed` |
| **Fan-out** | 병렬 실행 + 결과 병합 | `/evolve` (3 subagent 동시) |
| **Expert Pool** | 전문가 풀 전원 투입 | `/unstuck` (5 관점) |
| **Producer-Reviewer** | 생산-검증 분리 | `/run` → `/evaluate` |
| **Navigator-Driver** | 짝프로그래밍 (양방향 통신) | `/run` Pair Mode |

---

## Lite vs Pro

### 어느 쪽을 써야 하나?

**Lite로 시작하라.** Lite만으로도 가치의 80%를 얻는다.

**Pro로 업그레이드해야 할 시점** — 아래 중 2개 이상 해당:
- 팀이 3명 이상이고 협업 세션이 길어진다
- 프로젝트가 3개월 이상 지속될 예정이다
- 게이트 실행 내역과 감사 로그를 추적해야 한다
- 다른 AI 도구(Cursor, Cline 등)에서도 같은 게이트를 쓰고 싶다 (MCP)
- CI에서 객관적 점수(ambiguity, drift)를 수치로 남겨야 한다

**Pro가 과할 때** — Lite로 충분:
- 솔로 개발
- 프로토타입/해커톤
- 한 달 이내 단기 프로젝트
- 게이트 + 커맨드 + 에이전트만 필요

### 기능 비교

| | **Lite** | **Pro** |
|---|---|---|
| 의존성 | bash only (제로 의존성) | Python 3.11+ |
| 설치 | `./init.sh` | `./pro/install.sh` |
| 11개 게이트 | O | O |
| 10개 슬래시 커맨드 | O (AI 기반) | O (AI + 엔진) |
| 11 에이전트 페르소나 | O | O |
| 실제 모호성 점수 계산 | - | O |
| 온톨로지 유사도 추적 | - | O |
| 3단계 자동 평가 | - | O |
| 세션 영속성 (SQLite) | - | O |
| 드리프트 모니터링 훅 | - | O |
| 테스트 스캐폴드 생성 | - | O |
| 감사 로그 | - | O |
| Agent Observability | - | O |
| MCP 서버 | - | O |
| CLI (`harness` 커맨드) | - | O |

---

## Pro 버전 상세

### 아키텍처

```
pro/src/harness_pro/
├── cli.py                  # Typer CLI (12개 커맨드)
├── interview/engine.py     # 인터뷰 + 명확도 자동 점수화
├── scoring/ambiguity.py    # 모호성 가중 수식 계산
├── ontology/extractor.py   # 엔티티/관계/액션 추출 + 유사도
├── evaluation/pipeline.py  # 3단계 자동 평가 + 감사 로그
├── persistence/store.py    # SQLite EventStore (sessions, events, audit_log)
├── drift/monitor.py        # 시드 대비 드리프트 측정
├── testing/scaffold.py     # AC → 테스트 스캐폴드 생성
├── observability/tracer.py # Agent 의사결정 트레이싱
└── mcp/server.py           # MCP 서버 (게이트를 도구로 노출)
```

### CLI 커맨드

```bash
harness interview "topic"         # 인터뷰 시작, 모호성 점수 반환
harness seed                      # 최신 인터뷰 → 시드 생성
harness score                     # 현재 모호성 점수 표시
harness evaluate                  # 3단계 검증 실행
harness drift <file>              # 시드 대비 드리프트 측정
harness status                    # 세션 상태 표시
harness audit [--summary]         # 감사 로그 조회
harness trace [--recent N]        # Agent observability 트레이스 조회
harness test-scaffold --stack ts  # AC → 테스트 스캐폴드 생성
harness mcp-serve                 # MCP 서버 시작 (stdio/sse)
```

### MCP 서버

외부 AI 에이전트에서 하네스 기능을 MCP 도구로 호출:

```bash
pip install ai-harness-pro[mcp]
harness mcp-serve  # Claude Code, Cursor 등에서 연결
```

**제공 도구**: 11개 게이트 (`check_boundaries`, `check_layers`, ...) + `get_seed_spec` + `get_interview` + `get_ambiguity_score` + `get_trace` + `get_audit_log` + `run_all_gates`

**제공 리소스**: `harness://architecture-invariants`, `harness://code-conventions`, `harness://boundary-rules`

### Pro Hooks

| Hook | 트리거 | 역할 |
|------|--------|------|
| `keyword-detector.py` | UserPromptSubmit | 커맨드 키워드 감지 → CLI 라우팅 |
| `drift-monitor.py` | PostToolUse(Edit/Write) | 편집 후 자동 드리프트 측정 |
| `session-start.py` | SessionStart | 세션 초기화, EventStore 연결 |

---

## 설치 상세

### init.sh 실행 과정 (12 Steps)

```
./init.sh /path/to/project
    │
    ├─ [사전 검증] 디렉토리 존재/쓰기 권한/소스 파일 무결성
    ├─ [Step 1]  스택 감지 (lib/detect-stack.sh)
    ├─ [Step 2]  권한 프리셋 선택 (strict/standard/permissive)
    ├─ [Step 3]  프로젝트 이름 입력
    ├─ [Step 4]  CLAUDE.md 생성 (스택별 조건부)
    ├─ [Step 5]  ARCHITECTURE_INVARIANTS.md 생성
    ├─ [Step 6]  docs/ 생성 (code-convention, adr)
    ├─ [Step 7]  .claude/settings.local.json 설치
    ├─ [Step 8]  커맨드(10개) & 에이전트(9개) 복사
    ├─ [Step 9]  게이트(11개) & 규칙 설치
    ├─ [Step 10] pre-commit hook 설치
    ├─ [Step 11] GitHub Actions 워크플로우 (선택)
    └─ [Step 12] .gitignore 업데이트
```

### 지원 스택 (자동 감지)

| 카테고리 | 감지 대상 |
|----------|----------|
| **Node.js** | Next.js, NestJS, React, Vue, Nuxt, Svelte, SvelteKit, Remix, Astro, Express, Fastify, Hono |
| **Python** | FastAPI, Django, Flask |
| **Go** | Go, Gin, Chi |
| **Rust** | Rust, Actix, Axum |
| **Java/Kotlin** | Spring, Gradle, Maven |
| **ORM/DB** | Prisma, Alembic, Drizzle |
| **모노레포** | pnpm-workspace, Turborepo, Lerna |
| **인프라** | Docker, GitHub Actions |
| **패키지 매니저** | npm, yarn, pnpm, bun, pip, poetry, uv, pipenv, go, cargo, maven/gradle |

### 권한 프리셋

| Preset | 대상 | 차단 |
|--------|------|------|
| **strict** | 프로덕션/클라이언트 | rm -rf, DROP TABLE, sudo, git reset --hard |
| **standard** (기본) | 일반 개발 | rm -rf /, force push, sudo rm |
| **permissive** | 프로토타이핑 | rm -rf /, main force push |

### 문서 우선순위

```
1. ARCHITECTURE_INVARIANTS.md  (최상위 — 모든 것에 우선)
2. docs/adr.yaml              (아키텍처 결정 기록)
3. CLAUDE.md                   (AI 에이전트 컨텍스트)
4. docs/code-convention.yaml   (코딩 컨벤션)
```

---

## 디렉토리 구조

### 설치된 프로젝트

```
my-project/
├── CLAUDE.md                        # AI 에이전트 컨텍스트 (자동 생성)
├── ARCHITECTURE_INVARIANTS.md       # 절대 불변 규칙 (3-tier invariant 포함)
├── docs/
│   ├── code-convention.yaml         # 코딩 컨벤션 (LAYER + 스택별 규칙)
│   ├── adr.yaml                     # 아키텍처 결정 기록
│   └── TRD.md                       # 기술 설계서 (/trd 커맨드로 생성됨)
├── .claude/
│   ├── settings.local.json          # 권한 프리셋
│   ├── commands/                    # 슬래시 커맨드 (10개)
│   │   ├── interview.md, seed.md, trd.md, decompose.md, run.md
│   │   ├── evaluate.md, evolve.md, rollback.md, unstuck.md, pm.md
│   └── agents/                      # 에이전트 (9개 + topology)
│       ├── interviewer.md ... hacker.md
│       └── topology.yaml            # 에이전트 협업 패턴
├── .harness/
│   ├── gates/                       # 게이트 스크립트 (기본 7 + opt-in 5)
│   │   ├── check-boundaries.sh      check-layers.sh
│   │   ├── check-secrets.sh         check-security.sh
│   │   ├── check-structure.sh       check-spec.sh
│   │   ├── check-deps.sh
│   │   ├── check-security-ai.sh     # opt-in: 격리된 AI 보안 분석
│   │   ├── GATES.md                  # 기본/옵션 게이트 설명
│   │   └── rules/
│   │       ├── boundaries.yaml      # 의존성 + 레이어 규칙
│   │       └── structure.yaml       # 파일 배치 규칙
│   ├── security/                    # AI 보안 게이트 결과물 (check-security-ai 활성화 시)
│   │   ├── findings.json            # 누적 취약점 (팀 공유 — git 커밋 권장)
│   │   ├── dismissed.txt            # 기각된 오탐 목록 (팀 공유 — git 커밋 권장)
│   │   └── dismiss-finding.sh       # 기각 헬퍼
│   ├── hooks/
│   │   ├── post-edit-lint.sh        # 편집 후 자동 린트
│   │   └── pre-commit-gate.sh       # 커밋 전 게이트
│   ├── detect-violations.sh         # 전체 게이트 통합 실행
│   └── ouroboros/                   # Ouroboros 워크스페이스 (v2)
│       ├── seeds/seed-v*.yaml       # 불변 시드 스펙 (버전별)
│       ├── interviews/*.yaml        # 인터뷰 기록
│       ├── evaluations/*.yaml       # 평가 결과
│       ├── templates/seed-spec.yaml
│       ├── scoring/ambiguity-checklist.yaml
│       └── session.db               # Pro: SQLite EventStore
└── .github/
    └── workflows/harness-gates.yaml  # CI 워크플로우 (선택)
```

---

## 데이터 흐름

### 전체 워크플로우

```
[사용자 요구]
    ▼
/interview ── 질문 → 답변 → 차원별 명확도 → ambiguity ≤ 0.2 통과
    ▼
/seed ─────── 인터뷰 → 온톨로지 추출 (subagent) → 불변 명세
    ▼
/trd ──────── 논의 먼저 → 레이어별 설계 → docs/TRD.md
    ▼
/decompose ── AC → 원자적 태스크 (레이어별, 의존성 순서)
    ▼
/run ──────── Double Diamond: Discover → Define → Design → Deliver
              구현 순서: Data → Logic → Presentation
              모듈마다 즉시 테스트 작성
    ▼
게이트 자동 실행 ── layers + boundaries + secrets + security
    ▼
/evaluate ──── Stage 1 (Mechanical) → Stage 2 (Semantic) → Stage 3 (Judgment)
    ▼
├── PASS → git commit → pre-commit 게이트 → push → CI
└── FAIL → /evolve → Wonder → Reflect → Re-seed → 반복
```

### 게이트 실행 흐름

```
git commit -m "..."
    ↓
.git/hooks/pre-commit → .harness/hooks/pre-commit-gate.sh
    ↓
┌─ check-secrets.sh --staged (35+ 패턴)
├─ check-boundaries.sh (boundaries.yaml)
└─ check-structure.sh (.env, SQL 위치)
    ↓
ANY FAIL → 커밋 차단 | ALL PASS → 커밋 허용
```

### 피드백 루프

```
위반 발생 → detect-violations.sh
    → 분류 (규칙 부재 | 불명확 | 게이트 미비 | 오탐)
    → 규칙 추가 (boundaries.yaml / code-convention.yaml / adr.yaml)
    → 게이트 반영 → 검증 → 시스템 강건화
```

---

## Examples

`examples/` 디렉토리에 스택별 설정 예시:

- `examples/nextjs-fastapi/` — Next.js + FastAPI
- `examples/nextjs-nestjs/` — Next.js + NestJS
- `examples/nextjs-django/` — Next.js + Django
- `examples/python-only/` — Python standalone

---

## Acknowledgments & Inspirations

- [vibemafiaclub/mafia-codereview-harness](https://github.com/vibemafiaclub/mafia-codereview-harness) — Early reference for code review pipeline structure and convention categorization approach (our conventions are independently authored)
- [greatSumini/gpters-lecture](https://github.com/greatSumini/gpters-lecture-260323) — 3-tier layered architecture prompting patterns
- [Q00/ouroboros](https://github.com/Q00/ouroboros) — Ouroboros specification-first development concepts
- Peter Steinberger (OpenClaw) — Planning-first development philosophy
- Addy Osmani — Harness Engineering concept
- "Human steers, Agent executes" — OpenAI

## License

MIT
