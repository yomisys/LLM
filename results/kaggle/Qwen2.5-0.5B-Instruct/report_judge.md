## Qwen/Qwen2.5-0.5B-Instruct (grader: judge, n=60)

### Cross-validated (all questions out-of-fold, mean of 20x5-fold)

| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |
|---|---|---|---|---|---|---|---|---|
| clean | baseline | 68% | 0.63 | 26.0 | 19.0 | 0.78 | 0.56 | 80% |
| clean | ecerag | 29% | 0.40 | 6.8 | 1.8 | 0.87 | 0.93 | 80% |
| clean | ecerag_cr | 33% | 0.42 | 8.3 | 1.9 | 0.86 | 0.93 | 73% |
| irrelevant | baseline | 75% | 0.76 | 31.0 | 14.0 | 0.73 | 0.46 | 79% |
| irrelevant | ecerag | 26% | 0.43 | 6.1 | 2.6 | 0.84 | 0.98 | 79% |
| irrelevant | ecerag_cr | 31% | 0.46 | 7.9 | 2.7 | 0.83 | 0.98 | 72% |
| contradictory | baseline | 84% | 0.52 | 11.0 | 4.0 | 0.85 | – | 100% |
| contradictory | ecerag | 0% | 0.00 | 0.0 | 0.0 | – | – | 100% |
| contradictory | ecerag_cr | 25% | 0.40 | 2.5 | 0.0 | 0.93 | – | 82% |
| counterfactual | baseline | 74% | 0.74 | 25.0 | 12.0 | 0.79 | 0.67 | 65% |
| counterfactual | ecerag | 34% | 0.68 | 10.8 | 2.6 | 0.89 | 0.98 | 65% |
| counterfactual | ecerag_cr | 38% | 0.70 | 12.4 | 2.6 | 0.86 | 0.98 | 64% |

### Ablation (ECERAG selective risk / coverage, clean and perturbed)

| variant | clean | irrelevant | contradictory | counterfactual |
|---|---|---|---|---|
| baseline | 0.63 / 68% | 0.76 / 75% | 0.52 / 84% | 0.74 / 74% |
| equal_RCAT | 0.62 / 52% | 0.78 / 56% | 0.52 / 72% | 0.70 / 58% |
| fit_RCAT | 0.35 / 25% | 0.55 / 27% | 0.31 / 41% | 0.71 / 41% |
| fit_RCATG | 0.40 / 29% | 0.43 / 26% | 0.36 / 45% | 0.68 / 34% |
| fit_RCATG_veto | 0.40 / 29% | 0.43 / 26% | 0.00 / 0% | 0.68 / 34% |
| main_minus_R | 0.42 / 33% | 0.47 / 28% | 0.00 / 0% | 0.62 / 38% |
| main_minus_C | 0.43 / 29% | 0.37 / 23% | 0.00 / 0% | 0.64 / 32% |
| main_minus_A | 0.40 / 29% | 0.42 / 26% | 0.00 / 0% | 0.67 / 33% |
| main_minus_T | 0.38 / 29% | 0.49 / 26% | 0.00 / 0% | 0.62 / 29% |
| main_minus_G | 0.35 / 25% | 0.55 / 27% | 0.00 / 0% | 0.71 / 41% |

### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)

| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |
|---|---|---|---|---|
| clean | [0.48, 0.78] | [0.18, 0.64] | [-0.41, -0.07] | 0.00 |
| irrelevant | [0.62, 0.89] | [0.21, 0.69] | [-0.50, -0.16] | 0.00 |
| contradictory | [0.32, 0.74] | – | – | nan |
| counterfactual | [0.58, 0.88] | [0.43, 0.91] | [-0.22, 0.10] | 0.23 |

### Risk-coverage AUC (lower is better)

- paper_S_equal_RCAT: 0.63
- paper_S_equal_RCAT_test_split_only: 0.67
- cv_S_main_variant_out_of_fold: 0.57
- G_alone: 0.50
- random_ranking_expected: 0.75

### Risk-coverage AUC on the 41 questions the generator answered (no credit for ranking its own refusals)

- paper_S_equal_RCAT: 0.47
- cv_S_main_variant_out_of_fold: 0.47
- G_alone: 0.40
- R_alone: 0.44
- C_alone: 0.49
- A_alone: 0.57
- T_alone: 0.57
- random_ranking_expected: 0.63
- paper_S_gain_over_random_ci95: [0.02, 0.27]

### Paper protocol (fixed split: 17 calibration / 43 test, tau_A=0.45, tau_C=0.2)

| condition | system | coverage | selective risk |
|---|---|---|---|
| clean | baseline | 58% | 0.60 |
| clean | ecerag | 53% | 0.57 |
| clean | ecerag_cr | 58% | 0.60 |
| irrelevant | baseline | 71% | 0.72 |
| irrelevant | ecerag | 68% | 0.71 |
| irrelevant | ecerag_cr | 71% | 0.72 |
| contradictory | baseline | 84% | 0.56 |
| contradictory | ecerag | 84% | 0.56 |
| contradictory | ecerag_cr | 84% | 0.56 |
| counterfactual | baseline | 67% | 0.64 |
| counterfactual | ecerag | 67% | 0.64 |
| counterfactual | ecerag_cr | 67% | 0.64 |

### Grader agreement (lexical vs judge): 78% on 120 answers; lexical-only correct 19, judge-only correct 8
