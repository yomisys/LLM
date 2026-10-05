## Qwen/Qwen2.5-1.5B-Instruct (grader: lexical, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 87% | 0.52 | 27.0 | 8.0 | 0.78 | 0.38 | 80% |
| clean | ecerag | 29% | 0.26 | 4.8 | 0.6 | 0.88 | 0.89 | 80% |
| clean | ecerag_cr | 31% | 0.28 | 5.4 | 0.6 | 0.88 | 0.85 | 78% |
| irrelevant | baseline | 93% | 0.51 | 26.0 | 4.0 | 0.78 | 0.31 | 79% |
| irrelevant | ecerag | 29% | 0.23 | 4.0 | 0.4 | 0.88 | 0.95 | 79% |
| irrelevant | ecerag_cr | 32% | 0.25 | 4.6 | 0.4 | 0.88 | 0.90 | 77% |
| contradictory | baseline | 100% | 0.36 | 9.0 | 0.0 | 0.80 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 33% | 0.04 | 0.4 | 0.1 | 0.97 | – | 92% |
| counterfactual | baseline | 93% | 0.63 | 27.0 | 3.0 | 0.80 | 0.33 | 65% |
| counterfactual | ecerag | 26% | 0.28 | 3.8 | 0.2 | 0.93 | 0.97 | 65% |
| counterfactual | ecerag_cr | 32% | 0.32 | 5.0 | 0.2 | 0.92 | 0.97 | 76% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.52 / 87% | 0.51 / 93% | 0.36 / 100% | 0.63 / 93% |
| equal_RCAT | 0.29 / 32% | 0.25 / 31% | 0.11 / 42% | 0.40 / 35% |
| fit_RCAT | 0.23 / 28% | 0.19 / 25% | 0.08 / 39% | 0.31 / 29% |
| fit_RCATG | 0.26 / 29% | 0.23 / 29% | 0.28 / 44% | 0.28 / 26% |
| fit_RCATG_veto | 0.26 / 29% | 0.23 / 29% | 0.00 / 0% | 0.28 / 26% |
| main_minus_R | 0.30 / 32% | 0.31 / 34% | 0.00 / 0% | 0.35 / 30% |
| main_minus_C | 0.46 / 47% | 0.43 / 47% | 0.00 / 0% | 0.48 / 44% |
| main_minus_A | 0.24 / 28% | 0.23 / 28% | 0.00 / 0% | 0.26 / 25% |
| main_minus_T | 0.31 / 34% | 0.26 / 33% | 0.00 / 0% | 0.39 / 34% |
| main_minus_G | 0.23 / 28% | 0.19 / 25% | 0.00 / 0% | 0.31 / 29% |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.38, 0.65] | [0.11, 0.43] | [-0.40, -0.12] | 0.00 |
| irrelevant | [0.37, 0.65] | [0.08, 0.42] | [-0.43, -0.12] | 0.00 |
| contradictory | [0.16, 0.56] | – | – | nan |
| counterfactual | [0.48, 0.76] | [0.09, 0.54] | [-0.53, -0.14] | 0.00 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.38
- paper_S_equal_RCAT_test_split_only: 0.37
- cv_S_main_variant_out_of_fold: 0.45
- G_alone: 0.41
- random_ranking_expected: 0.58

### Risk-coverage AUC on the 52 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.33
- cv_S_main_variant_out_of_fold: 0.40
- G_alone: 0.39
- R_alone: 0.33
- C_alone: 0.29
- A_alone: 0.53
- T_alone: 0.39
- random_ranking_expected: 0.52
- paper_S_gain_over_random_ci95: [0.08, 0.27]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.8, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 84% | 0.53 |
| clean | ecerag | 28% | 0.25 |
| clean | ecerag_cr | 37% | 0.31 |
| irrelevant | baseline | 93% | 0.53 |
| irrelevant | ecerag | 29% | 0.25 |
| irrelevant | ecerag_cr | 37% | 0.27 |
| contradictory | baseline | 100% | 0.37 |
| contradictory | ecerag | 37% | 0.14 |
| contradictory | ecerag_cr | 42% | 0.25 |
| counterfactual | baseline | 94% | 0.61 |
| counterfactual | ecerag | 30% | 0.30 |
| counterfactual | ecerag_cr | 42% | 0.43 |

### Grader agreement (lexical vs judge): 82% on 146 answers; lexical-only correct 10, judge-only correct 17
