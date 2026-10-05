## Qwen/Qwen2.5-1.5B-Instruct (grader: judge, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 87% | 0.48 | 25.0 | 8.0 | 0.78 | 0.38 | 80% |
| clean | ecerag | 29% | 0.15 | 2.8 | 0.1 | 0.88 | 0.93 | 80% |
| clean | ecerag_cr | 32% | 0.19 | 3.6 | 0.1 | 0.88 | 0.88 | 77% |
| irrelevant | baseline | 93% | 0.43 | 22.0 | 4.0 | 0.78 | 0.31 | 79% |
| irrelevant | ecerag | 29% | 0.10 | 1.6 | 0.1 | 0.88 | 0.99 | 79% |
| irrelevant | ecerag_cr | 32% | 0.14 | 2.5 | 0.1 | 0.88 | 0.92 | 77% |
| contradictory | baseline | 100% | 0.28 | 7.0 | 0.0 | 0.80 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 35% | 0.00 | 0.1 | 0.0 | 0.96 | – | 92% |
| counterfactual | baseline | 93% | 0.65 | 28.0 | 3.0 | 0.80 | 0.33 | 65% |
| counterfactual | ecerag | 28% | 0.22 | 3.0 | 0.1 | 0.94 | 1.00 | 65% |
| counterfactual | ecerag_cr | 33% | 0.25 | 3.8 | 0.2 | 0.93 | 1.00 | 76% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.48 / 87% | 0.43 / 93% | 0.28 / 100% | 0.65 / 93% |
| equal_RCAT | 0.19 / 30% | 0.15 / 28% | 0.06 / 40% | 0.36 / 32% |
| fit_RCAT | 0.12 / 26% | 0.06 / 24% | 0.03 / 33% | 0.32 / 30% |
| fit_RCATG | 0.15 / 29% | 0.10 / 29% | 0.26 / 46% | 0.22 / 28% |
| fit_RCATG_veto | 0.15 / 29% | 0.10 / 29% | 0.00 / 0% | 0.22 / 28% |
| main_minus_R | 0.19 / 30% | 0.12 / 29% | 0.00 / 0% | 0.25 / 28% |
| main_minus_C | 0.25 / 35% | 0.16 / 32% | 0.00 / 0% | 0.34 / 35% |
| main_minus_A | 0.17 / 28% | 0.10 / 28% | 0.00 / 0% | 0.22 / 28% |
| main_minus_T | 0.14 / 30% | 0.08 / 29% | 0.00 / 0% | 0.20 / 29% |
| main_minus_G | 0.12 / 26% | 0.06 / 24% | 0.00 / 0% | 0.32 / 30% |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.35, 0.62] | [0.02, 0.32] | [-0.49, -0.18] | 0.00 |
| irrelevant | [0.29, 0.56] | [0.01, 0.25] | [-0.47, -0.18] | 0.00 |
| contradictory | [0.12, 0.48] | – | – | nan |
| counterfactual | [0.50, 0.79] | [0.05, 0.46] | [-0.59, -0.25] | 0.00 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.35
- paper_S_equal_RCAT_test_split_only: 0.33
- cv_S_main_variant_out_of_fold: 0.39
- G_alone: 0.32
- random_ranking_expected: 0.55

### Risk-coverage AUC on the 52 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.30
- cv_S_main_variant_out_of_fold: 0.34
- G_alone: 0.29
- R_alone: 0.28
- C_alone: 0.26
- A_alone: 0.45
- T_alone: 0.39
- random_ranking_expected: 0.48
- paper_S_gain_over_random_ci95: [0.09, 0.26]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.8, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 84% | 0.47 |
| clean | ecerag | 28% | 0.17 |
| clean | ecerag_cr | 37% | 0.31 |
| irrelevant | baseline | 93% | 0.42 |
| irrelevant | ecerag | 29% | 0.08 |
| irrelevant | ecerag_cr | 37% | 0.20 |
| contradictory | baseline | 100% | 0.26 |
| contradictory | ecerag | 37% | 0.14 |
| contradictory | ecerag_cr | 42% | 0.25 |
| counterfactual | baseline | 94% | 0.61 |
| counterfactual | ecerag | 30% | 0.30 |
| counterfactual | ecerag_cr | 42% | 0.36 |

### Grader agreement (lexical vs judge): 82% on 146 answers; lexical-only correct 10, judge-only correct 17
