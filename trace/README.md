# Harness Trace

Harness Trace adds observability without changing the harness workflow, command semantics, agent roles, or gate criteria.

## Trace Types

- **AI-facing Trace**: a concise explanation shown to the user by Claude.
- **Runtime Trace**: a JSONL execution log written by `.harness/trace/record-runtime-trace.sh` from the command/reference/agent files selected for the current workflow step.

AI-facing Trace should prefer `.harness/trace/latest-runtime-trace.json` when it exists. If no runtime trace exists, Claude may state the selected files it read, but must not invent rule IDs or evidence.

## Runtime Trace Schema

Each JSONL record contains:

```yaml
timestamp: ISO-8601 timestamp
workflow_step: interview | seed | trd | decompose | run | evaluate | evolve | review | other
request_type: user-provided request category
selected_command_files: list of command markdown files selected by the router
selected_reference_files: list of seed spec, TRD, task, architecture invariant, gate rule, or other reference files selected by the router
selected_agent_files: list of agent markdown files selected by the router, including methodology personas when invoked
loaded_rule_ids: Rule IDs found in the selected files
rule_source_paths: file paths that contain loaded Rule IDs
trace_id: runtime trace identifier
user_request_summary: short user request summary
```

## Rule ID Convention

Use stable IDs without rewriting rule meaning:

- `RULE-INTERVIEW-*`
- `RULE-SEED-*`
- `RULE-TRD-*`
- `RULE-DECOMP-*`
- `RULE-RUN-*`
- `RULE-EVAL-*`
- `RULE-EVOLVE-*`
- `RULE-APP-3TIER-*`
- `RULE-DP-*`
- `RULE-MSG-*`
- `RULE-SCA-*`

## Output Templates

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

```text
[Spec Evidence]
1. <file_path>#<rule_id>
   Rule: "<existing rule sentence or short summary>"
   Applied because: <why this rule applies now>
```

If no explicit rule applies:

```text
[Spec Evidence]
No explicit spec rule found.
Recommendation:
- Suggest which file should receive a new explicit rule for this situation.
```
