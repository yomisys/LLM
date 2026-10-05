## Qwen/Qwen2.5-14B-Instruct (grader: lexical, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 63% | 0.26 | 10.0 | 22.0 | 0.70 | 1.00 | 80% |
| clean | ecerag | 34% | 0.22 | 4.7 | 3.8 | 0.77 | 1.00 | 80% |
| clean | ecerag_cr | 36% | 0.22 | 4.8 | 3.9 | 0.77 | 1.00 | 80% |
| irrelevant | baseline | 62% | 0.21 | 7.0 | 21.0 | 0.73 | 1.00 | 79% |
| irrelevant | ecerag | 31% | 0.19 | 3.3 | 3.7 | 0.76 | 1.00 | 79% |
| irrelevant | ecerag_cr | 33% | 0.18 | 3.5 | 3.9 | 0.76 | 1.00 | 80% |
| contradictory | baseline | 88% | 0.14 | 3.0 | 3.0 | 0.74 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 25% | 0.01 | 0.1 | 0.5 | 0.84 | – | 97% |
| counterfactual | baseline | 54% | 0.24 | 6.0 | 21.0 | 0.70 | 1.00 | 65% |
| counterfactual | ecerag | 33% | 0.18 | 2.9 | 4.2 | 0.72 | 1.00 | 65% |
| counterfactual | ecerag_cr | 38% | 0.19 | 3.5 | 4.2 | 0.72 | 1.00 | 76% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.26 / 63% | 0.21 / 62% | 0.14 / 88% | 0.24 / 54% |
| equal_RCAT | 0.30 / 53% | 0.23 / 50% | 0.14 / 73% | 0.26 / 47% |
| fit_RCAT | 0.25 / 50% | 0.20 / 46% | 0.13 / 70% | 0.27 / 44% |
| fit_RCATG | 0.22 / 34% | 0.19 / 31% | 0.09 / 45% | 0.18 / 33% |
| fit_RCATG_veto | 0.22 / 34% | 0.19 / 31% | 0.00 / 0% | 0.18 / 33% |
| main_minus_R | 0.29 / 51% | 0.23 / 48% | 0.00 / 0% | 0.26 / 43% |
| main_minus_C | 0.31 / 48% | 0.25 / 45% | 0.00 / 0% | 0.25 / 42% |
| main_minus_A | 0.21 / 33% | 0.16 / 30% | 0.00 / 0% | 0.16 / 31% |
| main_minus_T | 0.17 / 31% | 0.13 / 28% | 0.00 / 0% | 0.13 / 32% |
| main_minus_G | 0.25 / 50% | 0.20 / 46% | 0.00 / 0% | 0.27 / 44% |

### Round 2: unconditional baseline vs ECERAG v2 (equal weights, conflict quarantine, merged CR)

| condition | system | coverage | selective risk | errors | self-declined | abstain recall |
|---|---|---|---|---|---|---|
| clean | baseline (refusal prompt) | 63% | 0.26 | 10.0 | 22.0 | 1.00 |
| clean | baseline (unconditional) | 100% | 0.47 | 28.0 | 0.0 | 0.00 |
| clean | evidence gate only (unconditional answers) | 91% | 0.46 | 24.9 | 0.0 | 0.16 |
| clean | ECERAG v2 | 53% | 0.30 | 9.3 | 14.9 | 1.00 |
| clean | ECERAG+CR v2 | 53% | 0.30 | 9.3 | 14.9 | 1.00 |
| irrelevant | baseline (refusal prompt) | 62% | 0.21 | 7.0 | 21.0 | 1.00 |
| irrelevant | baseline (unconditional) | 100% | 0.40 | 22.0 | 0.0 | 0.00 |
| irrelevant | evidence gate only (unconditional answers) | 92% | 0.40 | 20.4 | 0.0 | 0.11 |
| irrelevant | ECERAG v2 | 50% | 0.23 | 6.2 | 14.2 | 1.00 |
| irrelevant | ECERAG+CR v2 | 50% | 0.23 | 6.2 | 14.2 | 1.00 |
| contradictory | baseline (refusal prompt) | 88% | 0.14 | 3.0 | 3.0 | – |
| contradictory | baseline (unconditional) | 100% | 0.12 | 3.0 | 0.0 | – |
| contradictory | evidence gate only (unconditional answers) | 0% | 0.00 | 0.0 | 0.0 | – |
| contradictory | ECERAG v2 | 25% | 0.08 | 0.6 | 14.2 | – |
| contradictory | ECERAG+CR v2 | 25% | 0.08 | 0.6 | 14.2 | – |
| counterfactual | baseline (refusal prompt) | 54% | 0.24 | 6.0 | 21.0 | 1.00 |
| counterfactual | baseline (unconditional) | 100% | 0.46 | 21.0 | 0.0 | 0.00 |
| counterfactual | evidence gate only (unconditional answers) | 93% | 0.46 | 19.8 | 0.0 | 0.10 |
| counterfactual | ECERAG v2 | 47% | 0.26 | 5.5 | 14.9 | 1.00 |
| counterfactual | ECERAG+CR v2 | 47% | 0.26 | 5.5 | 14.9 | 1.00 |

| condition | unconditional | ECERAG v2 | v2 − unconditional | P(v2 not better) |
|---|---|---|---|---|
| clean | [0.33, 0.60] | [0.15, 0.46] | [-0.32, -0.02] | 0.01 |
| irrelevant | [0.27, 0.53] | [0.09, 0.38] | [-0.32, -0.02] | 0.01 |
| contradictory | [0.00, 0.24] | [0.00, 0.28] | [-0.24, 0.17] | 0.34 |
| counterfactual | [0.33, 0.59] | [0.10, 0.45] | [-0.36, -0.06] | 0.00 |

| condition | unconditional | gate only | gate − unconditional | P(gate not better) |
|---|---|---|---|---|
| clean | [0.33, 0.60] | [0.33, 0.59] | [-0.04, 0.02] | 0.29 |
| irrelevant | [0.27, 0.53] | [0.27, 0.53] | [-0.02, 0.03] | 0.59 |
| contradictory | [0.00, 0.24] | – | – | nan |
| counterfactual | [0.33, 0.59] | [0.32, 0.61] | [-0.02, 0.03] | 0.58 |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.13, 0.42] | [0.09, 0.38] | [-0.12, 0.05] | 0.18 |
| irrelevant | [0.08, 0.35] | [0.05, 0.35] | [-0.11, 0.07] | 0.32 |
| contradictory | [0.00, 0.30] | – | – | nan |
| counterfactual | [0.09, 0.42] | [0.05, 0.35] | [-0.15, 0.02] | 0.08 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.33
- paper_S_equal_RCAT_test_split_only: 0.33
- cv_S_main_variant_out_of_fold: 0.33
- G_alone: 0.29
- random_ranking_expected: 0.53

### Risk-coverage AUC on the 38 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.13
- cv_S_main_variant_out_of_fold: 0.18
- G_alone: 0.22
- R_alone: 0.15
- C_alone: 0.14
- A_alone: 0.25
- T_alone: 0.16
- random_ranking_expected: 0.26
- paper_S_gain_over_random_ci95: [0.05, 0.22]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.8, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 67% | 0.31 |
| clean | ecerag | 26% | 0.18 |
| clean | ecerag_cr | 28% | 0.17 |
| irrelevant | baseline | 63% | 0.23 |
| irrelevant | ecerag | 27% | 0.18 |
| irrelevant | ecerag_cr | 29% | 0.17 |
| contradictory | baseline | 89% | 0.18 |
| contradictory | ecerag | 37% | 0.00 |
| contradictory | ecerag_cr | 42% | 0.00 |
| counterfactual | baseline | 61% | 0.30 |
| counterfactual | ecerag | 30% | 0.10 |
| counterfactual | ecerag_cr | 36% | 0.17 |

### Grader agreement (lexical vs judge): 82% on 119 answers; lexical-only correct 4, judge-only correct 18
