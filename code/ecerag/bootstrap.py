"""Shared setup: load corpus/benchmark, build retriever, split calibration/test."""
import json
import random
from collections import defaultdict
from pathlib import Path

from .corpus import load_chunks, load_or_build_embeddings
from .retrieval import HybridRetriever

ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_PATH = ROOT / "data" / "benchmark.json"

CALIBRATION_FRACTION = 0.3
SPLIT_SEED = 7


def load_benchmark():
    return json.load(open(BENCHMARK_PATH, encoding="utf-8"))


def build_retriever():
    chunks = load_chunks()
    embeddings = load_or_build_embeddings(chunks)
    retriever = HybridRetriever(chunks, embeddings)
    chunks_by_doc = defaultdict(list)
    for c in chunks:
        chunks_by_doc[c["doc_id"]].append(c)
    return retriever, chunks, chunks_by_doc


def calibration_test_split(benchmark: list):
    by_type = defaultdict(list)
    for q in benchmark:
        by_type[q["type"]].append(q)
    rng = random.Random(SPLIT_SEED)
    calibration, test = [], []
    for qtype, items in by_type.items():
        items = list(items)
        rng.shuffle(items)
        k = max(1, round(len(items) * CALIBRATION_FRACTION))
        calibration.extend(items[:k])
        test.extend(items[k:])
    return calibration, test
