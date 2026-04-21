# Scoring Rubric

Score each skill with one local 10-point score and three side signals.

## Core Outputs

- `local_score = usage_score + uniqueness_score + impact_score`
- `usage_score`: `0.0-3.0`
- `uniqueness_score`: `0.0-3.0`
- `impact_score`: `0.0-4.0`
- `confidence_score`: `0.0-1.0`
- `community_prior_score`: `0.0-1.0`
- `risk_level`: `none / low / medium / high`

Keep `community_prior_score` and `risk_level` separate from `local_score`.
Use them to shape review priority and final action.

## 1. Usage Score (`0.0-3.0`)

Prefer direct host usage logs.
Use transcript mentions only as weaker fallback evidence.

### Input Fields

- `calls`
- `recent_30d_calls`
- `recent_90d_calls`
- `last_used_at`
- `active_days`
- `usage_source`
- `evidence_weight`

### Base Usage Strength

- When `recent_30d_calls` exists:
  - `0.0`: `0`
  - `1.0`: `1-2`
  - `2.0`: `3-7`
  - `3.0`: `8+`
- When only `recent_90d_calls` exists:
  - `0.0`: `0`
  - `0.75`: `1-2`
  - `1.5`: `3-9`
  - `2.5`: `10+`
- When only total `calls` exists:
  - `0.0`: `0`
  - `1.0`: `1-2`
  - `2.0`: `3-9`
  - `3.0`: `10+`

### Recency Adjustments

- add `0.5` when `last_used_at <= 7 days`
- add `0.25` when `last_used_at <= 30 days`
- subtract `0.5` when `last_used_at > 180 days`
- add `0.25` when `active_days >= 10`
- add `0.10` when `active_days >= 3`

### Evidence Weight

- `1.00`: direct usage file
- `0.45`: transcript-history fallback
- `0.00`: missing usage evidence

Clamp the final usage score to `0.0-3.0`.

## 2. Uniqueness Score (`0.0-3.0`)

Measure the highest functional-overlap similarity against any other installed skill.
Use description, headings, and resource names as the comparison surface.

Buckets:

- `0.0`: highest overlap `>= 0.85`
- `1.0`: highest overlap `0.65-0.84`
- `2.0`: highest overlap `0.40-0.64`
- `3.0`: highest overlap `< 0.40`

## 3. Impact Score (`0.0-4.0`)

### General skills

Use ablation on historical conversations.
Compute:

- `consistency_rate`: skill-on and skill-off produce materially equivalent outcomes
- `better_rate`: skill-on clearly improves the result
- `worse_rate`: skill-on clearly harms the result

Base score from consistency:

- `0.0`: `consistency_rate >= 0.85`
- `1.0`: `0.70-0.84`
- `2.0`: `0.55-0.69`
- `3.0`: `0.35-0.54`
- `4.0`: `< 0.35`

Adjustments:

- add `1.0` when `better_rate - worse_rate >= 0.30`
- subtract `1.0` when `worse_rate > better_rate`
- clamp the final impact score to `0.0-4.0`

When ablation is missing, use a temporary neutral score of `2.0` and lower confidence.

### API and tool skills

Skip history ablation.
Use protected-capability scoring instead:

- start at `2.0`
- add `1.0` when the skill ships executable scripts or hard capability resources
- add `0.5` when highest overlap `< 0.35`
- add `0.5` when calls `>= 3`
- subtract `1.0` when highest overlap `>= 0.75`
- subtract `0.5` when calls are `0`
- clamp the final impact score to `0.0-4.0`

## 4. Confidence Score (`0.0-1.0`)

Confidence describes evidence quality, not usefulness.

Add:

- `0.35` for direct usage files
- `0.15` for history fallback
- `0.20` when recent usage fields exist
- `0.10` when only total direct calls exist
- `0.25` for protected `api/tool` classification
- `0.25` for `general` skills with `>= 5` ablation cases
- `0.15` for `general` skills with `1-4` ablation cases
- `0.10` when overlap comparison has peers
- `0.05` when only one skill exists in scope
- `0.10` when community metadata exists

Clamp the final confidence score to `0.0-1.0`.

## 5. Community Prior Score (`0.0-1.0`)

Treat community data as external prior, not a local verdict.

Weighted components:

- `0.35`: normalized rating
- `0.25`: current installs or downloads
- `0.20`: trending metric
- `0.10`: stars
- `0.10`: maintenance freshness from `last_updated`

Use it to rank review priority and benchmark replacements.

## 6. Risk Level

Run static scans against runnable scripts and resource files.

Typical flags:

- `curl-pipe-shell`
- `dynamic-exec`
- `protected-path-access`
- `persistence-hook`
- `external-post`
- `shell-exec`
- `network-download`
- `base64-payload`

Risk levels:

- `none`: `0.0`
- `low`: `0.0 < score < 2.0`
- `medium`: `2.0-3.9`
- `high`: `4.0+`

## Verdict Bands

- `8.0-10.0`: keep
- `6.0-7.9`: keep, narrow when overlap stays high
- `4.5-5.9`: review
- `3.0-4.4`: merge or delete candidate
- `0.0-2.9`: strong delete candidate

## Action Rules

- `high risk`: `quarantine-review`
- `medium risk + strong local score`: `keep-review-risk`
- `low confidence + weak local score`: `observe-30d`
- `low local score + high overlap`: `merge-delete`
- `very low local score`: `delete`
- `low local score + strong community prior`: `review-vs-community`

Community data shapes review order.
Risk level shapes safety action.
Local score stays the main usefulness judgment.
