"""Local open-weight LM generator used for grounded answer generation and query rewriting.

Runs on CPU (float32) or GPU (float16/bfloat16, sharded across all visible GPUs via
device_map="auto", so a 7B model fits on Kaggle's 2x T4). Configure with:
  ECERAG_GENERATOR_MODEL  HF model id (default Qwen/Qwen2.5-1.5B-Instruct)
  ECERAG_LOAD_4BIT=1      load in 4-bit via bitsandbytes (for 14B+ models on T4s)
"""
import os

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .arithmetic import arithmetic_hint

MODEL_NAME = os.environ.get("ECERAG_GENERATOR_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

_loaded = {}


def load_model(name: str):
    if name not in _loaded:
        tok = AutoTokenizer.from_pretrained(name)
        kwargs = {}
        if torch.cuda.is_available():
            kwargs["device_map"] = "auto"
            if os.environ.get("ECERAG_LOAD_4BIT") == "1":
                from transformers import BitsAndBytesConfig
                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_type="nf4")
            else:
                # T4/P100 have no fast bf16; fp16 is the right choice there
                kwargs["torch_dtype"] = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        else:
            kwargs["torch_dtype"] = torch.float32
        model = AutoModelForCausalLM.from_pretrained(name, **kwargs)
        model.eval()
        _loaded[name] = (tok, model)
    return _loaded[name]


def chat(messages: list, max_new_tokens: int = 120, model_name: str = MODEL_NAME) -> str:
    tok, model = load_model(model_name)
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            top_k=None,
            pad_token_id=tok.eos_token_id,
        )
    gen_ids = out[0][inputs["input_ids"].shape[1]:]
    return tok.decode(gen_ids, skip_special_tokens=True).strip()


_chat = chat  # backward-compatible alias


def format_evidence(evidence: list) -> str:
    lines = []
    for e in evidence:
        lines.append(f"[{e['doc_id']}] {e['text']}")
    return "\n\n".join(lines)


ANSWER_SYSTEM = (
    "You are an enterprise QA assistant. Answer the question using ONLY the evidence "
    "passages provided. Lead with the exact specific value, fact, or entity the question "
    "asks for (a number, name, date, or yes/no) -- do not substitute a related figure. "
    "Then, if useful, add one short supporting clause. Be concise (1-3 sentences total). "
    "Every factual claim must be traceable to a passage; cite the source using its "
    "bracketed tag, e.g. [doc_id]. If a line tagged [computed] is present, it has already "
    "done any required arithmetic correctly -- restate its result rather than recalculating "
    "it yourself. "
    "If the evidence does not actually contain the specific answer, say exactly: "
    "\"NOT_SUPPORTED: the evidence does not contain this information.\""
)


def generate_answer(query: str, evidence: list, max_new_tokens: int = 75) -> str:
    evidence_text = format_evidence(evidence)
    hint = arithmetic_hint(query, evidence)
    if hint:
        evidence_text = f"[computed] {hint}\n\n{evidence_text}"
    messages = [
        {"role": "system", "content": ANSWER_SYSTEM},
        {"role": "user", "content": f"Evidence:\n{evidence_text}\n\nQuestion: {query}"},
    ]
    return chat(messages, max_new_tokens=max_new_tokens)


REWRITE_SYSTEM = (
    "You rewrite search queries for a retrieval system. Given the original question and the "
    "best evidence found so far (which was insufficient), produce ONE improved search query "
    "that adds specific missing terms (e.g. fiscal year, document name, section). "
    "Reply with only the rewritten query, no explanation."
)


def rewrite_query(query: str, evidence_so_far: list, max_new_tokens: int = 48) -> str:
    messages = [
        {"role": "system", "content": REWRITE_SYSTEM},
        {"role": "user", "content": (
            f"Original question: {query}\n\n"
            f"Best evidence found so far:\n{format_evidence(evidence_so_far[:3])}\n\n"
            "Rewritten query:"
        )},
    ]
    out = chat(messages, max_new_tokens=max_new_tokens)
    return out.splitlines()[0].strip().strip('"') if out else query
