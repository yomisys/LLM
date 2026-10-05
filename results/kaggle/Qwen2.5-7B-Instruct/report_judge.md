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
| contradictory | ecerag_cr | 63% | 0.10 | 1.6 | 1.6 | 0.75 | – | 92% |
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
