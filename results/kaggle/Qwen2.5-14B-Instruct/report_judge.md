## Qwen/Qwen2.5-14B-Instruct (grader: judge, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 63% | 0.11 | 4.0 | 22.0 | 0.70 | 1.00 | 80% |
| clean | ecerag | 63% | 0.11 | 4.0 | 20.9 | 0.70 | 1.00 | 80% |
| clean | ecerag_cr | 63% | 0.11 | 4.0 | 20.9 | 0.70 | 1.00 | 79% |
| irrelevant | baseline | 62% | 0.03 | 1.0 | 21.0 | 0.73 | 1.00 | 79% |
| irrelevant | ecerag | 61% | 0.03 | 1.0 | 20.9 | 0.73 | 1.00 | 79% |
| irrelevant | ecerag_cr | 61% | 0.03 | 1.0 | 20.9 | 0.73 | 1.00 | 78% |
| contradictory | baseline | 88% | 0.05 | 1.0 | 3.0 | 0.74 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 64% | 0.29 | 4.6 | 3.0 | 0.76 | – | 96% |
| counterfactual | baseline | 54% | 0.24 | 6.0 | 21.0 | 0.70 | 1.00 | 65% |
| counterfactual | ecerag | 54% | 0.24 | 6.0 | 20.7 | 0.70 | 1.00 | 65% |
| counterfactual | ecerag_cr | 54% | 0.24 | 6.0 | 20.7 | 0.70 | 1.00 | 65% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.11 / 63% | 0.03 / 62% | 0.05 / 88% | 0.24 / 54% |
| equal_RCAT | 0.11 / 63% | 0.03 / 62% | 0.05 / 88% | 0.24 / 54% |
| fit_RCAT | 0.11 / 63% | 0.03 / 62% | 0.05 / 88% | 0.24 / 54% |
| fit_RCATG | 0.11 / 63% | 0.03 / 61% | 0.05 / 87% | 0.24 / 54% |
| fit_RCATG_veto | 0.11 / 63% | 0.03 / 61% | 0.00 / 0% | 0.24 / 54% |
| main_minus_R | 0.11 / 63% | 0.03 / 62% | 0.00 / 0% | 0.24 / 54% |
| main_minus_C | 0.11 / 63% | 0.03 / 62% | 0.00 / 0% | 0.24 / 54% |
| main_minus_A | 0.11 / 63% | 0.03 / 61% | 0.00 / 0% | 0.24 / 54% |
| main_minus_T | 0.11 / 63% | 0.03 / 61% | 0.00 / 0% | 0.24 / 54% |
| main_minus_G | 0.11 / 63% | 0.03 / 62% | 0.00 / 0% | 0.24 / 54% |

### Round 2: unconditional baseline vs ECERAG v2 (equal weights, conflict quarantine, merged CR)

| condition | system | coverage | selective risk | errors | self-declined | abstain recall |
|---|---|---|---|---|---|---|
| clean | baseline (refusal prompt) | 63% | 0.11 | 4.0 | 22.0 | 1.00 |
| clean | baseline (unconditional) | 100% | 0.40 | 24.0 | 0.0 | 0.00 |
| clean | evidence gate only (unconditional answers) | 91% | 0.39 | 21.3 | 0.0 | 0.14 |
| clean | ECERAG v2 | 63% | 0.11 | 4.0 | 22.0 | 1.00 |
| clean | ECERAG+CR v2 | 63% | 0.11 | 4.0 | 22.0 | 1.00 |
| irrelevant | baseline (refusal prompt) | 62% | 0.03 | 1.0 | 21.0 | 1.00 |
| irrelevant | baseline (unconditional) | 100% | 0.38 | 21.0 | 0.0 | 0.00 |
| irrelevant | evidence gate only (unconditional answers) | 92% | 0.38 | 19.1 | 0.0 | 0.10 |
| irrelevant | ECERAG v2 | 62% | 0.03 | 1.0 | 21.0 | 1.00 |
| irrelevant | ECERAG+CR v2 | 62% | 0.03 | 1.0 | 21.0 | 1.00 |
| contradictory | baseline (refusal prompt) | 88% | 0.05 | 1.0 | 3.0 | – |
| contradictory | baseline (unconditional) | 100% | 0.12 | 3.0 | 0.0 | – |
| contradictory | evidence gate only (unconditional answers) | 0% | 0.00 | 0.0 | 0.0 | – |
| contradictory | ECERAG v2 | 28% | 0.14 | 1.0 | 18.0 | – |
| contradictory | ECERAG+CR v2 | 28% | 0.14 | 1.0 | 18.0 | – |
| counterfactual | baseline (refusal prompt) | 54% | 0.24 | 6.0 | 21.0 | 1.00 |
| counterfactual | baseline (unconditional) | 100% | 0.48 | 22.0 | 0.0 | 0.00 |
| counterfactual | evidence gate only (unconditional answers) | 92% | 0.46 | 19.4 | 0.0 | 0.09 |
| counterfactual | ECERAG v2 | 54% | 0.24 | 6.0 | 21.0 | 1.00 |
| counterfactual | ECERAG+CR v2 | 54% | 0.24 | 6.0 | 21.0 | 1.00 |

| condition | unconditional | ECERAG v2 | v2 − unconditional | P(v2 not better) |
|---|---|---|---|---|
| clean | [0.28, 0.53] | [0.02, 0.21] | [-0.42, -0.17] | 0.00 |
| irrelevant | [0.27, 0.51] | [0.00, 0.10] | [-0.49, -0.22] | 0.00 |
| contradictory | [0.00, 0.24] | [0.00, 0.50] | [-0.24, 0.38] | 0.53 |
| counterfactual | [0.33, 0.63] | [0.08, 0.43] | [-0.40, -0.09] | 0.00 |

| condition | unconditional | gate only | gate − unconditional | P(gate not better) |
|---|---|---|---|---|
| clean | [0.28, 0.53] | [0.27, 0.53] | [-0.04, 0.02] | 0.29 |
| irrelevant | [0.27, 0.51] | [0.26, 0.51] | [-0.02, 0.02] | 0.29 |
| contradictory | [0.00, 0.24] | – | – | nan |
| counterfactual | [0.33, 0.63] | [0.31, 0.60] | [-0.05, -0.00] | 0.01 |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.02, 0.21] | [0.03, 0.22] | [0.00, 0.00] | 1.00 |
| irrelevant | [0.00, 0.10] | [0.00, 0.10] | [0.00, 0.00] | 1.00 |
| contradictory | [0.00, 0.14] | – | – | nan |
| counterfactual | [0.08, 0.43] | [0.08, 0.43] | [-0.01, 0.00] | 0.24 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.26
- paper_S_equal_RCAT_test_split_only: 0.21
- cv_S_main_variant_out_of_fold: 0.25
- G_alone: 0.15
- random_ranking_expected: 0.43

### Risk-coverage AUC on the 38 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.05
- cv_S_main_variant_out_of_fold: 0.08
- G_alone: 0.07
- R_alone: 0.05
- C_alone: 0.05
- A_alone: 0.05
- T_alone: 0.05
- random_ranking_expected: 0.11
- paper_S_gain_over_random_ci95: [0.00, 0.12]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.8, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 67% | 0.10 |
| clean | ecerag | 26% | 0.00 |
| clean | ecerag_cr | 28% | 0.00 |
| irrelevant | baseline | 63% | 0.04 |
| irrelevant | ecerag | 27% | 0.00 |
| irrelevant | ecerag_cr | 29% | 0.00 |
| contradictory | baseline | 89% | 0.00 |
| contradictory | ecerag | 37% | 0.00 |
| contradictory | ecerag_cr | 42% | 0.00 |
| counterfactual | baseline | 61% | 0.20 |
| counterfactual | ecerag | 30% | 0.00 |
| counterfactual | ecerag_cr | 36% | 0.00 |

### Grader agreement (lexical vs judge): 82% on 119 answers; lexical-only correct 4, judge-only correct 18
