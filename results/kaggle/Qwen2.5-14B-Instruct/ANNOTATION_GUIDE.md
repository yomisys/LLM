
# ECERAG Human Evaluation: Annotation Guide

This guide is for labelling `human_eval_sheet.csv` (100 answered items from the
Qwen2.5-14B-Instruct run: 28 clean, 27 irrelevant, 23 outdated (labelled
"counterfactual" in the item IDs), 22 contradictory). Results are scored with
`code/human_eval.py score`.

## Setup

- **Two annotators work independently.** Each saves their own copy of the sheet as
  `annot_A.csv` and `annot_B.csv`, and they don't discuss items until both are
  finished.
- **Don't edit the `item_id` column.** Put exactly `1` or `0` in `correct`,
  `faithful` and `citation_ok`. The script skips any row where one of those cells is
  blank or holds anything else.
- **Use only what's in the sheet.** Don't open the source documents or look anything
  up. Each label has its own reference point:

| Label         | Judge against                             | Ignore                                    |
|---------------|-------------------------------------------|-------------------------------------------|
| `correct`     | the **gold answer** (and the question)    | the evidence                              |
| `faithful`    | the **evidence** column only              | the gold answer and your own knowledge    |
| `citation_ok` | the `[doc_id]` tags against the evidence  | the gold answer                           |

Because these are separate judgments, one answer can be faithful but incorrect: for
example, it correctly repeats an outdated or altered number from the evidence. That
case matters for the paper, so label it carefully.

## 1. `correct`: does the answer give the asked-for fact?

**Label 1 if all of these hold:**

- Every part the question asks for is answered correctly. For example, "What was X,
  and did it increase?" needs both the value and the direction.
- Numbers match the gold within normal rounding or a change of units:
  "$383.3 billion" = "$383,285 million", and "2%" = "1.9%" only if the gold rounds
  it that way.
- The fiscal year, entity, units and version (current vs. obsolete RFC) are the right
  ones.

**Label 0 if any of these apply:**

- Any part that was asked for is wrong or missing. Partly correct still counts as 0;
  write `PARTIAL` in notes.
- It gives the wrong year or version: a value from the superseded 10-K or from
  RFC 2616 when the current one was asked for. Write `STALE` in notes.
- It repeats the altered number planted in the contradictory evidence. Write
  `ALTERED` in notes.
- It hedges between candidates ("either $X or $Y") or gives a range that only happens
  to include the gold.
- It adds an extra claim about the thing asked for that is false. Extra details that
  are correct or irrelevant are fine.
- The question is unanswerable (the gold column says `UNANSWERABLE`) and the answer
  states a value or accepts a false premise.

**Unanswerable special case:** if the answer clearly declines or corrects the premise
without saying `NOT_SUPPORTED` (e.g., "The filing does not report this figure"),
label 1 and write `SOFT-REFUSAL` in notes. That tells us how often the automatic
refusal check misses a real refusal.

**If you think the gold answer is wrong,** still label against the gold and write
`GOLD?` plus a reason in notes. We'll adjudicate these separately.

## 2. `faithful`: is every claim backed by the evidence shown?

**Label 1** if every factual claim in the answer can be found in, or directly
calculated from, the evidence column. The following are allowed:

- Paraphrase and unit conversion.
- Simple arithmetic on numbers in the evidence.
- Any value in the `[computed]` line, which counts as evidence.

**Label 0** if:

- Any claim is missing from the evidence, even if you know it's true. Knowledge from
  outside the evidence counts as unfaithful.
- Any claim contradicts the evidence, or a calculation from evidence numbers is wrong.
- The answer combines passages in a way they don't support, e.g., treating a FY2022
  figure as FY2023.

Remember: an answer that repeats an outdated or altered number that really is in the
evidence is **faithful = 1** (and correct = 0).

## 3. `citation_ok`: do the `[doc]` tags support the answer?

Tags name documents, not individual passages, so a tag is valid if *any* passage from
that document in the evidence supports the claim.

**Label 1 if all of these hold:**

- The answer has at least one tag.
- The main answer (the value or entity asked for) has a tag next to it.
- Every tag points to a document whose passages support the claim it's attached to.

**Label 0** if there are no tags at all, if a tag points to a document that doesn't
support its claim, or if the main answer has no tag.

## Notes column codes

Use these codes so the reasons can be counted afterwards: `PARTIAL`, `STALE`,
`ALTERED`, `SOFT-REFUSAL`, `GOLD?`, `UNSURE`. Add a few words of explanation if
helpful. Use `UNSURE` sparingly, and always give a 0 or 1 anyway.

## Worked example (Q006, clean evidence)

- **Question:** What were Apple's Greater China net sales in FY2023, and did they
  increase or decrease from FY2022?
- **Gold answer:** $72,559 million, a 2% decrease from $74,200 million.
- **Answer:** "$72,559 million; it decreased from fiscal 2022."

| Label         | Value | Why                                                            |
|---------------|-------|----------------------------------------------------------------|
| `correct`     | 1     | Both parts asked for are right. The 2% figure wasn't asked for. |
| `faithful`    | 1     | Both claims are in the FY2023 passage.                         |
| `citation_ok` | 0     | The answer has no `[doc]` tag.                                 |

## Process and time

1. **Practice round (about 10 minutes).** Both annotators label 5–10 items exported
   from the **7B** run
   (`python code/human_eval.py export results/kaggle/Qwen2.5-7B-Instruct --n 10`),
   then compare and settle disagreements against this rubric. Don't practise on the
   14B sheet, because that would inflate the agreement score.
2. **Main round (about 1 hour each).** Each annotator labels all 100 items
   independently. If you change your understanding of a rule partway through, recheck
   the earlier items.
3. **Scoring:**
   `python code/human_eval.py score results/kaggle/Qwen2.5-14B-Instruct annot_A.csv annot_B.csv`.
   This reports inter-annotator Cohen's kappa for each label and how well each
   automatic grader agrees with the humans. With two annotators, the script counts an
   item as correct only when both said 1. Aim for kappa ≥ 0.6 on `correct`. If it
   comes out lower, adjudicate the disagreements and report both the raw and the
   adjudicated figures.
