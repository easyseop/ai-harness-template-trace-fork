---
description: Replay one Ouroboros workflow step from fixtures and verify Harness Trace, Spec Evidence, and output expectations. Testing command only; never creates production development artifacts.
argument-hint: "<target_step> <case> | YAML block with target_step and case"
---

# /replay-test — Stage Replay Test

> 기존 Harness Trace / Spec Evidence 로직을 수정하지 않고, 특정 workflow 단계만 fixture 기반으로 재실행해 trace와 산출물을 검증한다.

## Scope

`/replay-test` is a verification command, not a development command.

## Command Runtime Reality

Ouroboros slash commands are Markdown instructions, not shell programs.

- Source command files live in `commands/*.md`.
- `init.sh` copies them to `.claude/commands/*.md`.
- Claude Code is the runtime that reads and performs a slash command when the user types `/run`, `/decompose`, etc.
- `tests/replay/replay_runner.py` is not the slash-command runtime. It prepares replay prompts, records lineage, and verifies actual replay artifacts.

Therefore, trusted stage replay must be explicit about how actual artifacts were produced.

It must not:
- create or modify production feature artifacts
- replace `/interview`, `/seed`, `/trd`, `/decompose`, `/run`, `/evaluate`, or `/evolve`
- change existing Harness Trace / Spec Evidence behavior
- introduce a separate `/trace` command

It may:
- read `tests/cases/*.yaml`
- read `tests/fixtures/**`
- run `tests/replay/replay_runner.py`
- write replay result artifacts under `tests/results/**`
- write replay-only captured output under `tests/expected/` or temporary replay scratch paths when explicitly needed

## Usage

Positional:

```text
/replay-test interview banking_message_customer_inquiry
/replay-test seed data_pipeline_cdc
/replay-test trd data_pipeline_cdc
/replay-test decompose data_pipeline_cdc
/replay-test evaluate data_pipeline_missing_quality
```

YAML block:

```yaml
target_step: /decompose
case: data_pipeline_cdc
```

## Instructions

1. Resolve the test case:
   - Positional form maps to `tests/cases/test_<step>_<case>.yaml`
   - YAML form uses `target_step` and `case`
   - If multiple matching files exist, ask the user to choose one
2. Read the case YAML completely.
3. Read every file listed in `input_fixtures`.
4. Replay only the requested `target_step` using those fixtures as the prior state.
5. Do not run the full Ouroboros workflow unless the case explicitly says `mode: e2e`.
6. Capture the step's Harness Trace, Spec Evidence, and output.
7. Run the assertions:

```bash
python3 tests/replay/replay_runner.py tests/cases/<case-file>.yaml
```

8. Confirm that artifacts were written under:
   - `tests/results/runs/<timestamp>_<test_id>/`
   - `tests/results/latest/<test_id>/`
9. Report using the required format and include artifact paths.

To explicitly promote the latest run as a baseline:

```bash
python3 tests/replay/replay_runner.py tests/cases/<case-file>.yaml --promote-baseline
```

Never update `tests/results/baseline/<test_id>/` unless the user explicitly requests baseline promotion.

## Execution Modes

### `captured`

Reads pre-captured `actual_trace` and `actual_output` from the case YAML and verifies them.

Use this for documentation examples, quick assertion checks, or imported historical artifacts.

### `claude_mediated`

Uses the current Claude Code session as the command runtime.

This is the preferred mode when validating harness design behavior without a separate Claude CLI runner.

Flow:

```bash
python3 tests/replay/replay_runner.py tests/cases/<case-file>.yaml \
  --execution-mode claude_mediated \
  --prepare-replay
```

Then:

1. Open the printed `replay_prompt.md`.
2. Read the target command file named in the prompt, such as `commands/decompose.md`.
3. Read the listed fixtures.
4. Apply the target command instructions to the fixture state only.
5. Write newly generated artifacts to the printed paths:
   - `actual_trace.md`
   - `actual_output.md`
6. Run:

```bash
python3 tests/replay/replay_runner.py tests/cases/<case-file>.yaml \
  --execution-mode claude_mediated \
  --run-dir tests/results/runs/<run_id>
```

In this mode, the runner refuses to fall back to `tests/expected/**` as actual output. Actual artifacts must be produced for the run.

### `claude_cli`

Reserved for a future non-interactive executor using Claude CLI/API. It should follow the same lineage contract as `claude_mediated`.

## Lineage

Every replay result records where its artifacts came from:

- execution mode
- target command file path and sha256
- git commit of the command file
- case file path and sha256
- input fixture paths and sha256
- inferred source step for each fixture
- parent result references when provided
- actual trace/output sha256
- model or executor label

This lineage is written to both `replay_result.yaml` and `lineage.yaml`.

## Fixture Inputs By Step

| Target Step | Fixture Inputs |
|-------------|----------------|
| `/interview` | user request and optional `turns` fixture |
| `/seed` | interview output fixture |
| `/trd` | seed output fixture |
| `/decompose` | seed output + TRD output fixture |
| `/run` | decomposed task fixture |
| `/evaluate` | run output fixture |
| `/evolve` | evaluation result fixture |

## Interview Replay Strategy

### Single-turn Interview Test

Use one user request fixture. Verify:
- `expected_request_type`
- `must_ask_about`
- `must_not_ask_about`
- `must_include_rule_ids`
- required Harness Trace fields

### Multi-turn Interview Replay Test

Use a fixture with the original request plus user answer turns. Verify:
- the interview continues with necessary questions at each turn
- the interview stops when ambiguity is low enough
- `interview_output.yaml` shape is present
- `ambiguity_score_lte` is satisfied

## Required Result Format

```text
[Replay Test Result]
Test ID:
Target Step:
Case:
Input Fixtures:

[Harness Trace Check]
PASS/FAIL - <rule_id>

[Output Check]
PASS/FAIL - <expected item>

[Forbidden Pattern Check]
PASS/FAIL - <forbidden item>

Result: PASS or FAIL

[Replay Artifacts]
replay_result: tests/results/runs/<run_id>/replay_result.yaml
actual_trace: tests/results/runs/<run_id>/actual_trace.md
actual_output: tests/results/runs/<run_id>/actual_output.md
diff: tests/results/runs/<run_id>/diff.md
summary: tests/results/runs/<run_id>/summary.md
lineage: tests/results/runs/<run_id>/lineage.yaml
latest_dir: tests/results/latest/<test_id>
```

## Evaluate Replay Semantics

For `/evaluate` replay tests, `Result: PASS` means the evaluator detected the expected result.

Example: if a case expects `status: FAIL`, Replay Test passes only when the captured evaluation output fails for the expected reasons.
