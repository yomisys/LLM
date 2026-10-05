## Qwen/Qwen2.5-3B-Instruct (grader: lexical, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 67% | 0.42 | 17.0 | 20.0 | 0.75 | 1.00 | 80% |
| clean | ecerag | 48% | 0.42 | 12.3 | 10.0 | 0.78 | 1.00 | 80% |
| clean | ecerag_cr | 48% | 0.43 | 12.3 | 10.1 | 0.78 | 1.00 | 80% |
| irrelevant | baseline | 62% | 0.41 | 14.0 | 21.0 | 0.77 | 1.00 | 79% |
| irrelevant | ecerag | 44% | 0.41 | 10.0 | 9.8 | 0.80 | 1.00 | 79% |
| irrelevant | ecerag_cr | 45% | 0.42 | 10.4 | 10.0 | 0.80 | 1.00 | 79% |
| contradictory | baseline | 96% | 0.25 | 6.0 | 1.0 | 0.79 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 62% | 0.30 | 4.7 | 1.5 | 0.80 | – | 96% |
| counterfactual | baseline | 54% | 0.44 | 11.0 | 21.0 | 0.76 | 1.00 | 65% |
| counterfactual | ecerag | 43% | 0.41 | 8.1 | 10.3 | 0.79 | 1.00 | 65% |
| counterfactual | ecerag_cr | 46% | 0.43 | 9.2 | 10.4 | 0.77 | 1.00 | 73% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.42 / 67% | 0.41 / 62% | 0.25 / 96% | 0.44 / 54% |
| equal_RCAT | 0.19 / 27% | 0.26 / 28% | 0.09 / 47% | 0.18 / 28% |
| fit_RCAT | 0.18 / 28% | 0.26 / 29% | 0.04 / 44% | 0.30 / 31% |
| fit_RCATG | 0.42 / 48% | 0.41 / 44% | 0.21 / 71% | 0.41 / 43% |
| fit_RCATG_veto | 0.42 / 48% | 0.41 / 44% | 0.00 / 0% | 0.41 / 43% |
| main_minus_R | 0.43 / 51% | 0.45 / 49% | 0.00 / 0% | 0.42 / 45% |
| main_minus_C | 0.43 / 53% | 0.43 / 49% | 0.00 / 0% | 0.41 / 45% |
| main_minus_A | 0.43 / 50% | 0.41 / 46% | 0.00 / 0% | 0.42 / 44% |
| main_minus_T | 0.42 / 47% | 0.41 / 42% | 0.00 / 0% | 0.41 / 43% |
| main_minus_G | 0.18 / 28% | 0.26 / 29% | 0.00 / 0% | 0.30 / 31% |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.27, 0.57] | [0.26, 0.59] | [-0.06, 0.06] | 0.48 |
| irrelevant | [0.25, 0.58] | [0.24, 0.59] | [-0.07, 0.07] | 0.45 |
| contradictory | [0.08, 0.44] | – | – | nan |
| counterfactual | [0.26, 0.64] | [0.22, 0.62] | [-0.09, 0.04] | 0.16 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.41
- paper_S_equal_RCAT_test_split_only: 0.38
- cv_S_main_variant_out_of_fold: 0.54
- G_alone: 0.48
- random_ranking_expected: 0.62

### Risk-coverage AUC on the 40 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.23
- cv_S_main_variant_out_of_fold: 0.43
- G_alone: 0.45
- R_alone: 0.25
- C_alone: 0.22
- A_alone: 0.33
- T_alone: 0.28
- random_ranking_expected: 0.42
- paper_S_gain_over_random_ci95: [0.10, 0.27]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.75, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 70% | 0.43 |
| clean | ecerag | 33% | 0.29 |
| clean | ecerag_cr | 40% | 0.29 |
| irrelevant | baseline | 63% | 0.42 |
| irrelevant | ecerag | 34% | 0.29 |
| irrelevant | ecerag_cr | 41% | 0.29 |
| contradictory | baseline | 100% | 0.26 |
| contradictory | ecerag | 47% | 0.22 |
| contradictory | ecerag_cr | 53% | 0.20 |
| counterfactual | baseline | 61% | 0.40 |
| counterfactual | ecerag | 36% | 0.17 |
| counterfactual | ecerag_cr | 39% | 0.15 |

### Grader agreement (lexical vs judge): 76% on 123 answers; lexical-only correct 16, judge-only correct 13
