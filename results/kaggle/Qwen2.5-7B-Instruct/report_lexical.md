## Qwen/Qwen2.5-7B-Instruct (grader: lexical, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 52% | 0.26 | 8.0 | 29.0 | 0.70 | 1.00 | 80% |
| clean | ecerag | 30% | 0.18 | 3.3 | 4.8 | 0.71 | 1.00 | 80% |
| clean | ecerag_cr | 32% | 0.21 | 4.1 | 5.0 | 0.71 | 1.00 | 76% |
| irrelevant | baseline | 58% | 0.25 | 8.0 | 23.0 | 0.74 | 1.00 | 79% |
| irrelevant | ecerag | 30% | 0.16 | 2.6 | 4.0 | 0.75 | 1.00 | 79% |
| irrelevant | ecerag_cr | 33% | 0.20 | 3.7 | 4.2 | 0.75 | 1.00 | 75% |
| contradictory | baseline | 88% | 0.05 | 1.0 | 3.0 | 0.71 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 25% | 0.15 | 0.9 | 0.5 | 0.78 | – | 92% |
| counterfactual | baseline | 54% | 0.40 | 10.0 | 21.0 | 0.69 | 1.00 | 65% |
| counterfactual | ecerag | 31% | 0.16 | 2.3 | 5.4 | 0.70 | 1.00 | 65% |
| counterfactual | ecerag_cr | 34% | 0.20 | 3.2 | 5.6 | 0.71 | 1.00 | 68% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.26 / 52% | 0.25 / 58% | 0.05 / 88% | 0.40 / 54% |
| equal_RCAT | 0.23 / 34% | 0.20 / 35% | 0.07 / 54% | 0.24 / 35% |
| fit_RCAT | 0.20 / 32% | 0.18 / 33% | 0.06 / 50% | 0.23 / 34% |
| fit_RCATG | 0.18 / 30% | 0.16 / 30% | 0.07 / 51% | 0.16 / 31% |
| fit_RCATG_veto | 0.18 / 30% | 0.16 / 30% | 0.00 / 0% | 0.16 / 31% |
| main_minus_R | 0.23 / 34% | 0.24 / 34% | 0.00 / 0% | 0.24 / 32% |
| main_minus_C | 0.23 / 35% | 0.22 / 36% | 0.00 / 0% | 0.28 / 37% |
| main_minus_A | 0.18 / 31% | 0.16 / 31% | 0.00 / 0% | 0.17 / 32% |
| main_minus_T | 0.18 / 31% | 0.16 / 30% | 0.00 / 0% | 0.15 / 32% |
| main_minus_G | 0.20 / 32% | 0.18 / 33% | 0.00 / 0% | 0.23 / 34% |

### Round 2: unconditional baseline vs ECERAG v2 (equal weights, conflict quarantine, merged CR)

| condition | system | coverage | selective risk | errors | self-declined | abstain recall |
|---|---|---|---|---|---|---|
| clean | baseline (refusal prompt) | 52% | 0.26 | 8.0 | 29.0 | 1.00 |
| clean | baseline (unconditional) | 100% | 0.52 | 31.0 | 0.0 | 0.00 |
| clean | evidence gate only (unconditional answers) | 74% | 0.51 | 22.7 | 0.0 | 0.33 |
| clean | ECERAG v2 | 34% | 0.23 | 4.7 | 9.8 | 1.00 |
| clean | ECERAG+CR v2 | 34% | 0.23 | 4.7 | 9.9 | 1.00 |
| irrelevant | baseline (refusal prompt) | 58% | 0.25 | 8.0 | 23.0 | 1.00 |
| irrelevant | baseline (unconditional) | 100% | 0.51 | 28.0 | 0.0 | 0.00 |
| irrelevant | evidence gate only (unconditional answers) | 74% | 0.50 | 20.6 | 0.0 | 0.32 |
| irrelevant | ECERAG v2 | 35% | 0.20 | 4.0 | 6.8 | 1.00 |
| irrelevant | ECERAG+CR v2 | 35% | 0.20 | 4.0 | 6.8 | 1.00 |
| contradictory | baseline (refusal prompt) | 88% | 0.05 | 1.0 | 3.0 | – |
| contradictory | baseline (unconditional) | 100% | 0.24 | 6.0 | 0.0 | – |
| contradictory | evidence gate only (unconditional answers) | 0% | 0.00 | 0.0 | 0.0 | – |
| contradictory | ECERAG v2 | 33% | 0.28 | 2.4 | 6.7 | – |
| contradictory | ECERAG+CR v2 | 33% | 0.28 | 2.4 | 7.1 | – |
| counterfactual | baseline (refusal prompt) | 54% | 0.40 | 10.0 | 21.0 | 1.00 |
| counterfactual | baseline (unconditional) | 100% | 0.57 | 26.0 | 0.0 | 0.00 |
| counterfactual | evidence gate only (unconditional answers) | 77% | 0.54 | 19.2 | 0.0 | 0.29 |
| counterfactual | ECERAG v2 | 35% | 0.24 | 4.0 | 8.5 | 1.00 |
| counterfactual | ECERAG+CR v2 | 35% | 0.24 | 4.0 | 8.5 | 1.00 |

| condition | unconditional | ECERAG v2 | v2 − unconditional | P(v2 not better) |
|---|---|---|---|---|
| clean | [0.40, 0.65] | [0.07, 0.41] | [-0.45, -0.14] | 0.00 |
| irrelevant | [0.38, 0.64] | [0.06, 0.38] | [-0.45, -0.16] | 0.00 |
| contradictory | [0.08, 0.40] | [0.00, 0.60] | [-0.21, 0.33] | 0.59 |
| counterfactual | [0.41, 0.70] | [0.08, 0.43] | [-0.50, -0.16] | 0.00 |

| condition | unconditional | gate only | gate − unconditional | P(gate not better) |
|---|---|---|---|---|
| clean | [0.40, 0.65] | [0.38, 0.64] | [-0.05, 0.04] | 0.39 |
| irrelevant | [0.38, 0.64] | [0.37, 0.64] | [-0.04, 0.03] | 0.35 |
| contradictory | [0.08, 0.40] | – | – | nan |
| counterfactual | [0.41, 0.70] | [0.39, 0.69] | [-0.06, 0.02] | 0.13 |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.10, 0.42] | [0.02, 0.35] | [-0.22, 0.04] | 0.09 |
| irrelevant | [0.11, 0.41] | [0.03, 0.33] | [-0.22, 0.03] | 0.07 |
| contradictory | [0.00, 0.14] | – | – | nan |
| counterfactual | [0.21, 0.59] | [0.03, 0.34] | [-0.40, -0.10] | 0.00 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.36
- paper_S_equal_RCAT_test_split_only: 0.36
- cv_S_main_variant_out_of_fold: 0.40
- G_alone: 0.38
- random_ranking_expected: 0.62

### Risk-coverage AUC on the 31 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.10
- cv_S_main_variant_out_of_fold: 0.20
- G_alone: 0.29
- R_alone: 0.12
- C_alone: 0.09
- A_alone: 0.25
- T_alone: 0.11
- random_ranking_expected: 0.26
- paper_S_gain_over_random_ci95: [0.06, 0.24]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.8, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 53% | 0.26 |
| clean | ecerag | 26% | 0.18 |
| clean | ecerag_cr | 28% | 0.17 |
| irrelevant | baseline | 61% | 0.24 |
| irrelevant | ecerag | 27% | 0.18 |
| irrelevant | ecerag_cr | 29% | 0.17 |
| contradictory | baseline | 89% | 0.06 |
| contradictory | ecerag | 37% | 0.00 |
| contradictory | ecerag_cr | 37% | 0.00 |
| counterfactual | baseline | 61% | 0.35 |
| counterfactual | ecerag | 30% | 0.10 |
| counterfactual | ecerag_cr | 30% | 0.10 |

### Grader agreement (lexical vs judge): 75% on 110 answers; lexical-only correct 11, judge-only correct 17
