## Qwen/Qwen2.5-7B-Instruct (grader: judge, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 52% | 0.13 | 4.0 | 29.0 | 0.70 | 1.00 | 80% |
| clean | ecerag | 39% | 0.10 | 2.4 | 8.8 | 0.71 | 1.00 | 80% |
| clean | ecerag_cr | 41% | 0.12 | 3.0 | 8.9 | 0.72 | 1.00 | 78% |
| irrelevant | baseline | 58% | 0.16 | 5.0 | 23.0 | 0.74 | 1.00 | 79% |
| irrelevant | ecerag | 42% | 0.10 | 2.3 | 8.0 | 0.76 | 1.00 | 79% |
| irrelevant | ecerag_cr | 45% | 0.11 | 2.9 | 8.1 | 0.75 | 1.00 | 78% |
| contradictory | baseline | 88% | 0.14 | 3.0 | 3.0 | 0.71 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 36% | 0.06 | 0.6 | 1.1 | 0.76 | – | 92% |
| counterfactual | baseline | 54% | 0.36 | 9.0 | 21.0 | 0.69 | 1.00 | 65% |
| counterfactual | ecerag | 41% | 0.29 | 5.5 | 8.8 | 0.69 | 1.00 | 65% |
| counterfactual | ecerag_cr | 44% | 0.27 | 5.5 | 8.8 | 0.70 | 1.00 | 69% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.13 / 52% | 0.16 / 58% | 0.14 / 88% | 0.36 / 54% |
| equal_RCAT | 0.13 / 41% | 0.14 / 41% | 0.10 / 67% | 0.34 / 43% |
| fit_RCAT | 0.12 / 41% | 0.13 / 42% | 0.10 / 66% | 0.33 / 44% |
| fit_RCATG | 0.10 / 39% | 0.10 / 42% | 0.08 / 62% | 0.29 / 41% |
| fit_RCATG_veto | 0.10 / 39% | 0.10 / 42% | 0.00 / 0% | 0.29 / 41% |
| main_minus_R | 0.13 / 38% | 0.14 / 43% | 0.00 / 0% | 0.29 / 40% |
| main_minus_C | 0.08 / 37% | 0.10 / 41% | 0.00 / 0% | 0.25 / 40% |
| main_minus_A | 0.11 / 38% | 0.10 / 41% | 0.00 / 0% | 0.30 / 40% |
| main_minus_T | 0.10 / 39% | 0.10 / 42% | 0.00 / 0% | 0.29 / 41% |
| main_minus_G | 0.12 / 41% | 0.13 / 42% | 0.00 / 0% | 0.33 / 44% |

### Round 2: unconditional baseline vs ECERAG v2 (equal weights, conflict quarantine, merged CR)

| condition | system | coverage | selective risk | errors | self-declined | abstain recall |
|---|---|---|---|---|---|---|
| clean | baseline (refusal prompt) | 52% | 0.13 | 4.0 | 29.0 | 1.00 |
| clean | baseline (unconditional) | 100% | 0.43 | 26.0 | 0.0 | 0.00 |
| clean | evidence gate only (unconditional answers) | 83% | 0.38 | 18.9 | 0.0 | 0.28 |
| clean | ECERAG v2 | 41% | 0.13 | 3.1 | 14.8 | 1.00 |
| clean | ECERAG+CR v2 | 41% | 0.13 | 3.1 | 14.8 | 1.00 |
| irrelevant | baseline (refusal prompt) | 58% | 0.16 | 5.0 | 23.0 | 1.00 |
| irrelevant | baseline (unconditional) | 100% | 0.47 | 26.0 | 0.0 | 0.00 |
| irrelevant | evidence gate only (unconditional answers) | 86% | 0.45 | 21.1 | 0.0 | 0.23 |
| irrelevant | ECERAG v2 | 41% | 0.14 | 3.1 | 12.8 | 1.00 |
| irrelevant | ECERAG+CR v2 | 41% | 0.14 | 3.1 | 12.8 | 1.00 |
| contradictory | baseline (refusal prompt) | 88% | 0.14 | 3.0 | 3.0 | – |
| contradictory | baseline (unconditional) | 100% | 0.20 | 5.0 | 0.0 | – |
| contradictory | evidence gate only (unconditional answers) | 0% | 0.00 | 0.0 | 0.0 | – |
| contradictory | ECERAG v2 | 38% | 0.27 | 2.6 | 8.2 | – |
| contradictory | ECERAG+CR v2 | 38% | 0.27 | 2.6 | 8.9 | – |
| counterfactual | baseline (refusal prompt) | 54% | 0.36 | 9.0 | 21.0 | 1.00 |
| counterfactual | baseline (unconditional) | 100% | 0.63 | 29.0 | 0.0 | 0.00 |
| counterfactual | evidence gate only (unconditional answers) | 88% | 0.60 | 24.1 | 0.0 | 0.25 |
| counterfactual | ECERAG v2 | 43% | 0.34 | 6.8 | 12.2 | 1.00 |
| counterfactual | ECERAG+CR v2 | 43% | 0.34 | 6.8 | 12.2 | 1.00 |

| condition | unconditional | ECERAG v2 | v2 − unconditional | P(v2 not better) |
|---|---|---|---|---|
| clean | [0.30, 0.57] | [0.02, 0.27] | [-0.45, -0.16] | 0.00 |
| irrelevant | [0.35, 0.60] | [0.03, 0.27] | [-0.47, -0.21] | 0.00 |
| contradictory | [0.04, 0.36] | [0.01, 0.59] | [-0.20, 0.39] | 0.69 |
| counterfactual | [0.48, 0.76] | [0.15, 0.55] | [-0.47, -0.11] | 0.00 |

| condition | unconditional | gate only | gate − unconditional | P(gate not better) |
|---|---|---|---|---|
| clean | [0.30, 0.57] | [0.25, 0.51] | [-0.11, -0.01] | 0.01 |
| irrelevant | [0.35, 0.60] | [0.31, 0.58] | [-0.07, 0.01] | 0.09 |
| contradictory | [0.04, 0.36] | – | – | nan |
| counterfactual | [0.48, 0.76] | [0.45, 0.75] | [-0.07, -0.01] | 0.01 |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.03, 0.26] | [0.01, 0.23] | [-0.10, 0.03] | 0.23 |
| irrelevant | [0.03, 0.29] | [0.01, 0.22] | [-0.14, 0.01] | 0.06 |
| contradictory | [0.00, 0.29] | – | – | nan |
| counterfactual | [0.18, 0.56] | [0.12, 0.49] | [-0.18, 0.01] | 0.05 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.31
- paper_S_equal_RCAT_test_split_only: 0.27
- cv_S_main_variant_out_of_fold: 0.28
- G_alone: 0.22
- random_ranking_expected: 0.55

### Risk-coverage AUC on the 31 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.04
- cv_S_main_variant_out_of_fold: 0.04
- G_alone: 0.06
- R_alone: 0.04
- C_alone: 0.05
- A_alone: 0.09
- T_alone: 0.05
- random_ranking_expected: 0.13
- paper_S_gain_over_random_ci95: [0.01, 0.17]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.8, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 53% | 0.13 |
| clean | ecerag | 26% | 0.00 |
| clean | ecerag_cr | 28% | 0.00 |
| irrelevant | baseline | 61% | 0.16 |
| irrelevant | ecerag | 27% | 0.00 |
| irrelevant | ecerag_cr | 29% | 0.00 |
| contradictory | baseline | 89% | 0.12 |
| contradictory | ecerag | 37% | 0.00 |
| contradictory | ecerag_cr | 37% | 0.00 |
| counterfactual | baseline | 61% | 0.35 |
| counterfactual | ecerag | 30% | 0.20 |
| counterfactual | ecerag_cr | 30% | 0.20 |

### Grader agreement (lexical vs judge): 75% on 110 answers; lexical-only correct 11, judge-only correct 17
