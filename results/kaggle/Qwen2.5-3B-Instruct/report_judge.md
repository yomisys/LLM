## Qwen/Qwen2.5-3B-Instruct (grader: judge, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 67% | 0.35 | 14.0 | 20.0 | 0.75 | 1.00 | 80% |
| clean | ecerag | 47% | 0.32 | 9.2 | 8.8 | 0.78 | 1.00 | 80% |
| clean | ecerag_cr | 48% | 0.32 | 9.3 | 9.2 | 0.78 | 1.00 | 82% |
| irrelevant | baseline | 62% | 0.44 | 15.0 | 21.0 | 0.77 | 1.00 | 79% |
| irrelevant | ecerag | 47% | 0.43 | 11.2 | 8.8 | 0.81 | 1.00 | 79% |
| irrelevant | ecerag_cr | 49% | 0.42 | 11.6 | 9.4 | 0.80 | 1.00 | 82% |
| contradictory | baseline | 96% | 0.46 | 11.0 | 1.0 | 0.79 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 59% | 0.21 | 3.1 | 1.2 | 0.81 | – | 97% |
| counterfactual | baseline | 54% | 0.44 | 11.0 | 21.0 | 0.76 | 1.00 | 65% |
| counterfactual | ecerag | 45% | 0.38 | 8.0 | 10.4 | 0.78 | 1.00 | 65% |
| counterfactual | ecerag_cr | 49% | 0.36 | 8.3 | 10.8 | 0.77 | 1.00 | 71% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.35 / 67% | 0.44 / 62% | 0.46 / 96% | 0.44 / 54% |
| equal_RCAT | 0.37 / 62% | 0.45 / 57% | 0.46 / 91% | 0.44 / 52% |
| fit_RCAT | 0.33 / 45% | 0.39 / 46% | 0.33 / 62% | 0.41 / 46% |
| fit_RCATG | 0.32 / 47% | 0.43 / 47% | 0.31 / 72% | 0.38 / 45% |
| fit_RCATG_veto | 0.32 / 47% | 0.43 / 47% | 0.00 / 0% | 0.38 / 45% |
| main_minus_R | 0.33 / 47% | 0.43 / 44% | 0.00 / 0% | 0.36 / 45% |
| main_minus_C | 0.38 / 56% | 0.47 / 52% | 0.00 / 0% | 0.43 / 47% |
| main_minus_A | 0.33 / 48% | 0.44 / 48% | 0.00 / 0% | 0.38 / 45% |
| main_minus_T | 0.34 / 48% | 0.42 / 44% | 0.00 / 0% | 0.36 / 41% |
| main_minus_G | 0.33 / 45% | 0.39 / 46% | 0.00 / 0% | 0.41 / 46% |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.20, 0.50] | [0.17, 0.49] | [-0.09, 0.04] | 0.21 |
| irrelevant | [0.28, 0.60] | [0.26, 0.61] | [-0.07, 0.06] | 0.37 |
| contradictory | [0.26, 0.65] | – | – | nan |
| counterfactual | [0.25, 0.65] | [0.19, 0.59] | [-0.12, -0.01] | 0.01 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.41
- paper_S_equal_RCAT_test_split_only: 0.40
- cv_S_main_variant_out_of_fold: 0.41
- G_alone: 0.30
- random_ranking_expected: 0.57

### Risk-coverage AUC on the 40 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.23
- cv_S_main_variant_out_of_fold: 0.26
- G_alone: 0.21
- R_alone: 0.24
- C_alone: 0.21
- A_alone: 0.35
- T_alone: 0.23
- random_ranking_expected: 0.35
- paper_S_gain_over_random_ci95: [0.02, 0.20]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.45, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 70% | 0.40 |
| clean | ecerag | 67% | 0.41 |
| clean | ecerag_cr | 67% | 0.41 |
| irrelevant | baseline | 63% | 0.50 |
| irrelevant | ecerag | 63% | 0.50 |
| irrelevant | ecerag_cr | 63% | 0.50 |
| contradictory | baseline | 100% | 0.53 |
| contradictory | ecerag | 100% | 0.53 |
| contradictory | ecerag_cr | 100% | 0.53 |
| counterfactual | baseline | 61% | 0.40 |
| counterfactual | ecerag | 61% | 0.40 |
| counterfactual | ecerag_cr | 61% | 0.40 |

### Grader agreement (lexical vs judge): 76% on 123 answers; lexical-only correct 16, judge-only correct 13
