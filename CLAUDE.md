# CLAUDE.md — AI Harness Template

This is the harness template repository itself.

## Project Overview

AI 에이전트 하네스 엔지니어링 + Ouroboros(명세 기반 개발) 통합 오픈소스 템플릿.
두 가지 버전: Lite(bash only) / Pro(Python enhanced).

## Rules

1. **Lite는 외부 의존성 없음** — bash/sed/grep만 사용. commands/agents는 마크다운
2. **Pro는 Python 3.11+** — pydantic, pyyaml, aiosqlite, rich, typer
3. **민감 데이터 제로** — API 키, JWT, DB URL, 비즈니스 로직 절대 포함 금지
4. **스택 자동 감지** — init.sh가 프로젝트 타입을 알아서 판단
5. **점진적 채택** — 전부 쓸 필요 없이 개별 컴포넌트 선택 가능

## Harness Trace & Spec Evidence

이 레포는 기존 하네스 동작을 유지합니다. trace metadata를 추가하더라도 기존 command/spec/agent/evaluation 규칙을 삭제, 재작성, 요약 대체하지 마세요.

### Trace 종류

- **AI-facing Trace**: 주요 workflow 단계에서 사용자에게 보여주는 설명용 trace입니다.
- **Runtime Trace**: selected, loaded, applied evidence 기록을 `.harness/trace` 아래에 남기는 실행 로그입니다. 가능하면 `.harness/trace/latest-runtime-trace-final.json`을 우선 사용하고, 없으면 `.harness/trace/latest-runtime-trace.json`을 사용하세요.

### Runtime 신뢰도 수준

- `selected`: router가 선택한 command/reference/agent 파일입니다.
- `loaded`: `.harness/trace/mark-loaded-file.sh --path <file>`로 읽었다고 명시 기록한 파일입니다.
- `applied`: Spec Evidence에서 인용되고 `python3 .harness/trace/finalize-runtime-trace.py --evidence-file <file>`로 검증된 Rule ID입니다.

Rule ID가 loaded 파일 또는 finalized runtime trace에 없으면 runtime-verified라고 설명하지 마세요.

### 라우팅 원칙

workflow step 기준으로 selected 파일을 식별하세요.
- command files: `commands/<step>.md` 또는 설치된 `.claude/commands/<step>.md`
- reference files: 해당 단계와 관련된 seed spec, TRD, task file, architecture invariant, gate rule file
- agent files: 해당 단계에서 호출된 `agents/*.md`, methodology persona, 또는 설치된 `.claude/agents/*.md`

### 필수 사용자 출력

각 주요 단계에서 아래 형식으로 출력하세요.

```text
[Harness Trace]
Current Step:
Request Type:
Applied Command Files:
Applied Reference Files:
Applied Agent Files:
Key Rules Applied:
Trace Confidence:
Trace Verification:
Next Step:
```

명시적으로 적용한 `file_path#RULE-ID` 근거가 있을 때만 아래 형식의 `[Spec Evidence]`를 출력하세요. 근거가 없으면 `[Spec Evidence]` 블록과 `No explicit spec rule found.` 문구를 강제로 출력하지 마세요.

```text
[Spec Evidence]
1. <file_path>#<rule_id>
   Rule: "<기존 규칙 문장 또는 짧은 요약>"
   Applied because: <이 규칙이 현재 작업에 적용되는 이유>
```

부모 Rule ID와 더 구체적인 하위 Rule ID가 함께 있으면, 넓은 부모 ID만 인용하지 말고 `RULE-EVAL-PERSONA-001-02`처럼 현재 판단에 가장 구체적으로 적용되는 하위 Rule ID를 인용하세요.

Runtime Trace 도구가 있으면, Spec Evidence를 출력한 경우에만 그 블록을 `.harness/trace/current-spec-evidence.md`에 저장하고 아래 명령을 실행하세요.

```bash
python3 .harness/trace/finalize-runtime-trace.py \
  --evidence-file .harness/trace/current-spec-evidence.md \
  --require-loaded-selected command \
  --policy .harness/trace/trace-policy.json \
  --require-policy
```

Spec Evidence를 출력하지 않은 경우에는 `--evidence-file` 없이 아래 명령을 실행하세요.

```bash
python3 .harness/trace/finalize-runtime-trace.py \
  --require-loaded-selected command \
  --policy .harness/trace/trace-policy.json \
  --require-policy
```

finalized trace가 성공한 경우에만 검증된 trace로 사용하세요. 실패하면 누락된 loaded 파일 또는 불일치한 evidence와 함께 `Trace Verification: FAIL`을 출력하고, runtime verification이 된 것처럼 말하지 마세요. finalized trace가 없으면 runtime verification을 암시하지 말고 사용 가능한 confidence level(`selected_only` 또는 `loaded_files_recorded`)을 명시하세요.

## Structure

- `init.sh` — Lite 설치 스크립트 (Harness + Ouroboros commands/agents + methodology dispatcher)
- `lib/` — 공유 유틸리티 (detect-stack, render-template, colors, **methodology.sh**)
- `templates/` — 프로젝트에 복사할 템플릿 파일
- `gates/` — CI/CD 게이트 스크립트 (check-boundaries, check-secrets, check-spec)
- `boundaries/` — Claude Code 권한 프리셋 + hooks
- `commands/` — Ouroboros 슬래시 커맨드 (interview, seed, run, evaluate, evolve, unstuck, pm) + `/methodology`
- `agents/` — 11개 에이전트 페르소나 정의
- `ouroboros/` — 시드 스펙 템플릿, 모호성 체크리스트
- `methodology/` — 플러그인 시스템 (스키마, 레지스트리, 상태 템플릿)
- `methodologies/` — 번들 메서드 플러그인 13종 (ouroboros, living-spec, parallel-change, bmad-lite, exploration, strangler-fig, incident-review, threat-model-lite, observability-first, rfc-driven, tdd-strict, lean-mvp, mikado-method)
- `feedback/` — 피드백 루프 도구
- `examples/` — 스택별 예시
- `pro/` — Pro 버전 (Python 엔진, CLI, hooks)
- `docs/` — 가이드 (methodology-guide.md, methodology-catalog.md, CODEBASE-GUIDE.md)

## Methodology System

하네스 코어는 **고정**. 메서드는 **플러그인**으로 사용자가 선택·조합.

```bash
/methodology list                           # 사용 가능한 메서드
/methodology use ouroboros                  # 단일 활성화
/methodology compose ouroboros bmad-lite    # 다중 조합
```

번들 16종:
- 0→1 / 1→N: ouroboros (default) · living-spec · parallel-change · bmad-lite · lean-mvp · ddd-lite · shape-up
- 모든 단계: exploration · threat-model-lite · rfc-driven · tdd-strict · bdd
- 운영 / 시스템: strangler-fig · incident-review · observability-first
- 리팩터링: mikado-method

자세한 내용은 `docs/methodology-guide.md`, `docs/methodology-catalog.md`.
