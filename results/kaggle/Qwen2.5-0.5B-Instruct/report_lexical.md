## Qwen/Qwen2.5-0.5B-Instruct (grader: lexical, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 68% | 0.59 | 24.0 | 19.0 | 0.78 | 0.56 | 80% |
| clean | ecerag | 49% | 0.56 | 16.4 | 9.6 | 0.81 | 0.79 | 80% |
| clean | ecerag_cr | 52% | 0.56 | 17.5 | 10.1 | 0.81 | 0.77 | 76% |
| irrelevant | baseline | 75% | 0.71 | 29.0 | 14.0 | 0.73 | 0.46 | 79% |
| irrelevant | ecerag | 48% | 0.67 | 17.6 | 9.7 | 0.77 | 0.84 | 79% |
| irrelevant | ecerag_cr | 51% | 0.65 | 18.3 | 9.8 | 0.76 | 0.82 | 76% |
| contradictory | baseline | 84% | 0.38 | 8.0 | 4.0 | 0.85 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 57% | 0.38 | 5.4 | 3.2 | 0.84 | – | 76% |
| counterfactual | baseline | 74% | 0.62 | 21.0 | 12.0 | 0.79 | 0.67 | 65% |
| counterfactual | ecerag | 57% | 0.64 | 16.6 | 8.9 | 0.84 | 0.83 | 65% |
| counterfactual | ecerag_cr | 59% | 0.63 | 17.4 | 9.2 | 0.83 | 0.83 | 64% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.59 / 68% | 0.71 / 75% | 0.38 / 84% | 0.62 / 74% |
| equal_RCAT | 0.60 / 57% | 0.72 / 62% | 0.38 / 73% | 0.65 / 63% |
| fit_RCAT | 0.48 / 35% | 0.62 / 39% | 0.30 / 46% | 0.63 / 52% |
| fit_RCATG | 0.56 / 49% | 0.67 / 48% | 0.33 / 63% | 0.64 / 57% |
| fit_RCATG_veto | 0.56 / 49% | 0.67 / 48% | 0.00 / 0% | 0.64 / 57% |
| main_minus_R | 0.53 / 48% | 0.67 / 47% | 0.00 / 0% | 0.62 / 58% |
| main_minus_C | 0.59 / 58% | 0.70 / 60% | 0.00 / 0% | 0.64 / 70% |
| main_minus_A | 0.56 / 49% | 0.67 / 48% | 0.00 / 0% | 0.64 / 57% |
| main_minus_T | 0.58 / 49% | 0.71 / 48% | 0.00 / 0% | 0.63 / 52% |
| main_minus_G | 0.48 / 35% | 0.62 / 39% | 0.00 / 0% | 0.63 / 52% |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.43, 0.73] | [0.39, 0.72] | [-0.09, 0.05] | 0.25 |
| irrelevant | [0.57, 0.84] | [0.50, 0.84] | [-0.11, 0.04] | 0.17 |
| contradictory | [0.18, 0.59] | – | – | nan |
| counterfactual | [0.45, 0.78] | [0.47, 0.80] | [-0.04, 0.10] | 0.70 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.62
- paper_S_equal_RCAT_test_split_only: 0.66
- cv_S_main_variant_out_of_fold: 0.63
- G_alone: 0.52
- random_ranking_expected: 0.72

### Risk-coverage AUC on the 41 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.46
- cv_S_main_variant_out_of_fold: 0.54
- G_alone: 0.45
- R_alone: 0.44
- C_alone: 0.46
- A_alone: 0.56
- T_alone: 0.59
- random_ranking_expected: 0.59
- paper_S_gain_over_random_ci95: [-0.02, 0.24]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.45, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 58% | 0.56 |
| clean | ecerag | 53% | 0.57 |
| clean | ecerag_cr | 58% | 0.56 |
| irrelevant | baseline | 71% | 0.69 |
| irrelevant | ecerag | 68% | 0.68 |
| irrelevant | ecerag_cr | 71% | 0.69 |
| contradictory | baseline | 84% | 0.38 |
| contradictory | ecerag | 84% | 0.38 |
| contradictory | ecerag_cr | 84% | 0.38 |
| counterfactual | baseline | 67% | 0.55 |
| counterfactual | ecerag | 67% | 0.55 |
| counterfactual | ecerag_cr | 67% | 0.55 |

### Grader agreement (lexical vs judge): 78% on 120 answers; lexical-only correct 19, judge-only correct 8
