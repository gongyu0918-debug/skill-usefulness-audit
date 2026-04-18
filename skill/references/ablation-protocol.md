# Ablation Protocol

Use this protocol for every `general` skill.

## Goal

Measure whether the skill changes outcomes in a meaningful way.

High consistency between skill-on and skill-off runs means the skill adds little value.

## Sampling

Pick `5-20` historical tasks per skill.
Choose tasks where the skill should plausibly matter.
Prefer real user turns over synthetic prompts.

## Replay Method

For each case, run two isolated replays:

1. `with_skill`
2. `without_skill`

Keep these constant:

- same prompt
- same files and artifacts
- same model class when possible
- same tool permissions
- same success criteria

Use a fresh thread, subagent, or isolated run if the host supports it.

## Case Judgment

Record:

- `pass`: whether the run solved the task
- `score`: optional `0.0-1.0` quality score
- `tool_cost`: optional rough measure of tool calls, latency, or retries
- `verdict`: `better`, `same`, or `worse`
- `notes`: one short reason

## Normalized JSON Example

```json
[
  {
    "skill": "emotion-orchestrator",
    "case_id": "case-001",
    "with_skill": {"pass": true, "score": 0.92},
    "without_skill": {"pass": true, "score": 0.81},
    "verdict": "better",
    "notes": "with-skill run adapted reply style and avoided a follow-up correction"
  },
  {
    "skill": "tone-polisher",
    "case_id": "case-002",
    "with_skill": {"pass": true, "score": 0.84},
    "without_skill": {"pass": true, "score": 0.83},
    "verdict": "same",
    "notes": "final answer stayed materially equivalent"
  }
]
```

## Judgment Rule

Use `same` when the final answer, correctness, and workflow remain materially equivalent.
Use `better` when the skill improves correctness, speed, structure, or user-fit in a way the baseline did not.
Use `worse` when the skill adds friction, drift, or errors.

## Reporting

Feed the normalized ablation file into:

```bash
python scripts/skill_usefulness_audit.py audit --ablation-file ./ablation.json
```
