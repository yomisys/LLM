# ECERAG paper: plain-English summary and recommendations

## Part 1: The paper in plain English

### The problem
Companies use AI chatbots that answer questions by first looking things up in their
documents (RAG, retrieval-augmented generation). This helps, but the chatbot still
answers confidently even when the documents it found are wrong, contradictory, or out of
date. In a bank, a law firm or an engineering team, a confident wrong answer can do real
damage.

### The idea (ECERAG)
Before answering, the system checks how good its evidence is. It scores the evidence on
four things:

- **Relevance:** do the documents actually match the question?
- **Coverage:** do they mention the key terms in the question?
- **Agreement:** do they agree with each other, or contradict each other?
- **Trust/recency:** are they current, or an old superseded version?

If the score is high, it answers. If it's middling, it asks the user to clarify. If it's
low, it says "I don't know." This is the "retrieve, assess, decide" idea.

### How it was tested
- 60 questions written from real public documents: Apple's annual reports for two years,
  a US government AI risk framework, a web security standard, and an old and a new
  version of the HTTP specification.
- 16 of the questions have no answer in the documents, to see whether the system knows
  when to stay quiet.
- The documents were deliberately sabotaged three ways: adding irrelevant pages,
  inserting a copy with a changed number, and swapping in an outdated version.
- Five AI models were tested, from very small (0.5B parameters) to fairly large (14B).
- Two graders were used: a keyword checker and a second AI acting as judge.

### What was found
1. **Allowing the system to decline cuts errors by about two-thirds.** A chatbot forced
   to always answer was wrong about 40% of the time; with ECERAG it was wrong about
   11–13% of the time on the questions it chose to answer.
2. **But the main credit goes to the AI's own judgment, not the evidence score.** Simply
   telling the model "answer only from the documents, and say NOT_SUPPORTED if they
   don't contain the answer" achieves nearly all of that improvement. Medium and large
   models (3B and up) correctly refused every unanswerable question this way.
3. **The evidence score alone helps only a little.** Used by itself to block answers, it
   removes a few more errors, and only in some cases. It catches just 9–33% of the
   unanswerable questions, because a trick question can still pull up documents that
   look relevant.
4. **The score is still a useful confidence meter.** Among the answers the system gave,
   a low score reliably points to the wrong ones. That makes it good for flagging
   answers for human review, even if it isn't a reliable gatekeeper.
5. **Bigger models make far fewer mistakes.** The smallest model was wrong about 63% of
   the time and the 14B model about 11%. This explains why the original small
   experiment showed no benefit: the tiny model's own mistakes swamped everything else.
6. **Contradictions are easy to detect, hard to fix.** The system spotted every planted
   contradiction. But removing the conflicting passages often removed the answer too.

### The takeaway
"Check before you answer" works. The best single safeguard is a capable model told to
answer only from the documents and to refuse otherwise. Evidence scoring is a useful
extra layer for ranking confidence and flagging risky answers, rather than the main
defence.

### Honest limits the paper states
It's a small test (60 questions, six documents). Grading is automatic and hasn't yet
been checked by people. All the models come from one family (Qwen). The sabotage was
artificial, so real-world mess may behave differently.

---

## Part 2: How to improve the paper and the results

### Quick fixes for the camera-ready (days)
1. **Run the human evaluation.** This is the biggest credibility gap. Two people label
   the 100-answer sheet
   (`results/kaggle/Qwen2.5-14B-Instruct/human_eval_sheet.csv`, about an hour each). It
   tells us which grader to trust and turns a stated limitation into a result.
2. **Report confidence intervals on Table I**, not only in Table II, so readers can see
   the uncertainty everywhere.
3. **Merge the `kaggle-experiment` branch into `main`** so the code link in the paper
   leads straight to the right code.

### Stronger results (1–2 weeks, more Kaggle runs)
4. **More questions.** 60 is the main reason many intervals are wide. Going to 150–200
   would make the small gate effects either clearly real or clearly absent. Candidates
   can be drafted from the documents, with every gold answer verified by hand.
5. **More realistic unanswerable questions.** Ours were written by us and may be too easy
   to refuse. Collect real questions from colleagues, or use near-miss questions such as
   a fiscal year that's one off.
6. **Another model family.** Add Llama 3.1 8B or Mistral 7B. It answers the obvious
   objection that the results might be Qwen-specific.
7. **A frontier model** such as GPT-4o or Claude, run on a small subset. It shows whether
   the pattern holds at the scale enterprises actually use.

### A better method (the research direction)
8. **Use the score to fix the evidence, not just to refuse.** When the score is low,
   retrieve again for the missing piece. Over-refusal was mostly multi-hop questions
   where one of the two needed figures wasn't retrieved; retrieving once per document or
   year would likely recover many of them.
9. **Make the outdated-document check smarter.** Outdated evidence was the hardest
   condition (24% errors even at 14B). Flag the case where a newer version of the same
   document exists but wasn't retrieved, then fetch it.
10. **Handle contradictions by choosing a side.** Instead of dropping both conflicting
    passages, keep the one from the more trusted or more recent source, or show both
    figures to the user.
11. **Combine the two signals into one decision.** Self-refusal catches unanswerable
    questions; the evidence score ranks answer quality. A combined rule (refuse if the
    model refuses, *or* if the score is very low) might beat either alone. This is cheap
    to test on the existing data, with no new runs.

### Writing improvements
12. **Tighten the title.** "Hallucination-resistant" now overstates the gate's role. A
    title closer to the finding, such as "When Does Evidence Scoring Help Enterprise
    RAG?", would be more accurate, but title changes may not be allowed at the
    camera-ready stage.
13. **Add one worked example** showing a question, its evidence, the score and each
    system's answer. Reviewers liked the RFC example in the original.

### Recommendation
- **Before submitting:** items 1, 3 and 11.
- **For a journal version later:** items 4–10.
