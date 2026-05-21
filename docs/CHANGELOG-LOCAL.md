# Local Change Log

이 파일은 외부망에서 작업한 변경분을 집에서 개인 GitHub 레포에 커밋할 때 참고하기 위한 간단 이력입니다.

## v3 후보 - Trace 신뢰도 및 누락 방지 개선

### 1. 사용자 출력 한국어화

- 변경: `[Harness Trace]`, `[Spec Evidence]`, `Trace Verification` 등 사용자-facing trace 문구를 `[하네스 추적]`, `[명세 근거]`, `Trace 검증` 중심으로 정리했습니다.
- 이유: 팀원이 하네스 trace를 처음 봐도 의미를 바로 이해할 수 있게 하기 위해서입니다.
- 기대 효과: trace 로그와 README 설명의 용어가 맞춰져 온보딩이 쉬워집니다.

### 2. `[하네스 추적]` 양식에 `산출물` 추가

- 변경: 필수 출력 양식에 `산출물:` 항목을 추가했습니다.
- 이유: 각 단계에서 무엇이 생성됐는지 trace와 함께 확인하기 위해서입니다.
- 기대 효과: trace가 단순 설명이 아니라 실제 workflow 결과와 연결됩니다.

### 3. 명세 근거 출력 조건 완화 유지

- 변경: 명시적으로 적용한 `file_path#RULE-ID` 근거가 있을 때만 `[명세 근거]`를 출력하도록 유지했습니다.
- 이유: 근거가 없는데 억지로 `No explicit spec rule found.`를 반복 출력하면 오히려 노이즈가 되기 때문입니다.
- 기대 효과: 실제 근거가 있는 경우만 evidence로 남아 trace 품질이 좋아집니다.

### 4. finalizer에 `PASS / WARNING / FAIL`과 이유 추가

- 변경: `trace/finalize-runtime-trace.py`가 `trace_status`, `trace_reasons.pass`, `trace_reasons.warning`, `trace_reasons.failure`를 저장하고 콘솔에도 이유를 출력하도록 개선했습니다.
- 이유: loaded 누락이나 evidence 불일치가 났을 때 왜 실패했는지 바로 알기 위해서입니다.
- 기대 효과: trace 실패 원인을 사람이 다시 추적하는 시간이 줄어듭니다.

### 5. optional selected 파일은 `WARNING`으로 분리

- 변경: required loaded 누락은 `FAIL`, optional selected 파일의 loaded 미기록은 `WARNING`으로 분리했습니다.
- 이유: selected에 있었지만 실제 참고하지 않았을 수 있는 파일까지 무조건 실패로 단정하지 않기 위해서입니다.
- 기대 효과: trace 검증이 더 정직해지고, 과도한 FAIL을 줄입니다.

### 6. `--expect-step`으로 이전 trace 오사용 방지

- 변경: finalizer에 `--expect-step <step>` 옵션을 추가하고 각 command가 자기 step을 넘기도록 했습니다.
- 이유: `/run` 실행 중 이전 `/seed`나 `/evaluate` trace를 잘못 검증하는 상황을 막기 위해서입니다.
- 기대 효과: 현재 command의 Runtime Trace가 없거나 다른 단계 trace를 잡으면 `FAIL`로 드러납니다.

### 7. trace 누락 방지 지시 강화

- 변경: `CLAUDE.md`, `templates/CLAUDE.md.hbs`, 각 Ouroboros command에 Runtime Trace 시작, 현재 command loaded 기록, final trace gate 실행을 preflight/postflight gate로 명시했습니다.
- 이유: Claude가 trace 시작이나 finalizer 실행을 빠뜨리는 경우를 줄이기 위해서입니다.
- 기대 효과: md 기반 하네스 안에서 가능한 수준의 강제성이 높아집니다.

### 8. trace 한계 문서화

- 변경: README와 `trace/README.md`에 loaded가 OS read hook이 아니며, loaded 없음만으로 실제 미열람과 기록 누락을 구분할 수 없다고 명시했습니다.
- 이유: trace 신뢰도를 과장하지 않기 위해서입니다.
- 기대 효과: 팀이 trace를 감사 가능한 외부 증거로 쓰되, 한계도 함께 이해할 수 있습니다.

### 9. replay 결과 trace에 상태와 이유 포함

- 변경: replay runner가 `trace_status`와 `trace_reasons`를 actual trace markdown에 포함하도록 했습니다.
- 이유: replay 결과에서도 왜 PASS/WARNING/FAIL이 났는지 함께 보이게 하기 위해서입니다.
- 기대 효과: replay artifact만 봐도 trace 검증 상태를 파악할 수 있습니다.

## 추천 커밋 메시지

```text
feat: improve runtime trace verification and Korean trace output
```

또는 조금 더 나누면:

```text
feat: add trace status reasons and step verification
docs: clarify trace reliability and limitations
```
