# Generator-scale sweep (cross-validated, main variant)

| generator | grader | clean: baseline risk / cov | clean: ECERAG risk / cov | clean: ECERAG+CR risk / cov | contradictory: base → ECERAG risk | counterfactual: base → ECERAG risk | RC-AUC paper S → fitted S |
|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | judge | 0.63 / 68% | 0.40 / 29% | 0.42 / 33% | 0.52 → 0.00 | 0.74 → 0.68 | 0.63 → 0.57 |
| Qwen/Qwen2.5-1.5B-Instruct | judge | 0.48 / 87% | 0.15 / 29% | 0.19 / 32% | 0.28 → 0.00 | 0.65 → 0.22 | 0.35 → 0.39 |
| Qwen/Qwen2.5-3B-Instruct | judge | 0.35 / 67% | 0.32 / 47% | 0.32 / 48% | 0.46 → 0.00 | 0.44 → 0.38 | 0.41 → 0.41 |
| Qwen/Qwen2.5-7B-Instruct | judge | 0.13 / 52% | 0.10 / 39% | 0.12 / 41% | 0.14 → 0.00 | 0.36 → 0.29 | 0.31 → 0.28 |
| Qwen/Qwen2.5-14B-Instruct | judge | 0.11 / 63% | 0.11 / 63% | 0.11 / 63% | 0.05 → 0.00 | 0.24 → 0.24 | 0.26 → 0.25 |
