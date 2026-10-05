# Generator-scale sweep (cross-validated, main variant)

| generator | grader | clean: baseline risk / cov | clean: ECERAG risk / cov | clean: ECERAG+CR risk / cov | contradictory: base → ECERAG risk | counterfactual: base → ECERAG risk | RC-AUC paper S → fitted S |
|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | lexical | 0.59 / 68% | 0.56 / 49% | 0.56 / 52% | 0.38 → 0.00 | 0.62 → 0.64 | 0.62 → 0.63 |
| Qwen/Qwen2.5-1.5B-Instruct | lexical | 0.52 / 87% | 0.26 / 29% | 0.28 / 31% | 0.36 → 0.00 | 0.63 → 0.28 | 0.38 → 0.45 |
| Qwen/Qwen2.5-3B-Instruct | lexical | 0.42 / 67% | 0.42 / 48% | 0.43 / 48% | 0.25 → 0.00 | 0.44 → 0.41 | 0.41 → 0.54 |
| Qwen/Qwen2.5-7B-Instruct | lexical | 0.26 / 52% | 0.18 / 30% | 0.21 / 32% | 0.05 → 0.00 | 0.40 → 0.16 | 0.36 → 0.40 |
| Qwen/Qwen2.5-14B-Instruct | lexical | 0.26 / 63% | 0.22 / 34% | 0.22 / 36% | 0.14 → 0.00 | 0.24 → 0.18 | 0.33 → 0.33 |
