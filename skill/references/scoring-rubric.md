# Scoring Rubric

Score every skill on a `0.0-10.0` scale.

## Formula

`total_score = usage_score + uniqueness_score + impact_score`

- `usage_score`: `0.0-3.0`
- `uniqueness_score`: `0.0-3.0`
- `impact_score`: `0.0-4.0`

## 1. Usage Score (`0.0-3.0`)

Use direct invocation counts when available.
Use transcript mentions only as fallback evidence.

Buckets:

- `0.0`: `0` calls
- `1.0`: `1-2` calls
- `2.0`: `3-9` calls
- `3.0`: `10+` calls

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

When ablation is missing, use a temporary neutral score of `2.0` and mark the report as incomplete.

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

## Verdict Bands

- `8.0-10.0`: keep
- `6.0-7.9`: keep, optional narrowing
- `4.5-5.9`: review, merge when overlap stays high
- `3.0-4.4`: merge or delete candidate
- `0.0-2.9`: strong delete candidate

## Delete Recommendation Rules

### General skills

Recommend deletion when either condition holds:

- `total_score < 3.0`
- `total_score < 4.5` and highest overlap `>= 0.65` and calls `<= 1`

### API and tool skills

Recommend deletion only when all conditions hold:

- `total_score < 4.0`
- calls `== 0`
- highest overlap `>= 0.75`

Prefer merge or scope narrowing over deletion when a low-scoring skill still exposes a distinct host integration.
