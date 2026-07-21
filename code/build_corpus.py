"""
Build the ECERAG experiment corpus: extract clean text from raw source
documents (SEC 10-K filings, NIST AI RMF, OWASP Top 10, IETF RFCs),
chunk into retrieval passages, and write data/corpus/chunks.jsonl.

Each chunk record:
{
  "chunk_id": str,
  "doc_id": str,          # e.g. "apple_10k_fy2023"
  "doc_title": str,
  "doc_type": str,        # financial | regulatory | technical_standard
  "doc_version_date": str,  # ISO date the document version is "as of"
  "text": str
}
"""
import json
import re
from pathlib import Path

import fitz  # pymupdf
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "corpus" / "raw"
OUT = ROOT / "data" / "corpus" / "chunks.jsonl"

CHUNK_WORDS = 220
CHUNK_OVERLAP = 40


def clean_ws(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_htm(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return clean_ws(text)


def extract_pdf(path: Path) -> str:
    doc = fitz.open(str(path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return clean_ws(text)


def extract_txt(path: Path) -> str:
    return clean_ws(path.read_text(encoding="utf-8", errors="ignore"))


def chunk_text(text: str, chunk_words=CHUNK_WORDS, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_words])
        if len(chunk.split()) >= 30:  # drop tiny trailing fragments
            chunks.append(chunk)
        i += chunk_words - overlap
    return chunks


DOCS = [
    dict(
        doc_id="apple_10k_fy2023",
        doc_title="Apple Inc. Form 10-K (Fiscal Year 2023, filed 2023-11-03)",
        doc_type="financial",
        doc_version_date="2023-11-03",
        path=RAW / "apple_10k_fy2023.htm",
        extractor=extract_htm,
    ),
    dict(
        doc_id="apple_10k_fy2022",
        doc_title="Apple Inc. Form 10-K (Fiscal Year 2022, filed 2022-10-28)",
        doc_type="financial",
        doc_version_date="2022-10-28",
        path=RAW / "apple_10k_fy2022.htm",
        extractor=extract_htm,
    ),
    dict(
        doc_id="nist_ai_rmf",
        doc_title="NIST AI Risk Management Framework (AI 100-1), January 2023",
        doc_type="regulatory",
        doc_version_date="2023-01-26",
        path=RAW / "nist_ai_rmf.pdf",
        extractor=extract_pdf,
    ),
    dict(
        doc_id="owasp_top10_2021",
        doc_title="OWASP Top 10:2021 Web Application Security Risks",
        doc_type="technical_standard",
        doc_version_date="2021-09-24",
        path=RAW / "owasp_top10_2021_combined.md",
        extractor=extract_txt,
    ),
    dict(
        doc_id="rfc2616_http11",
        doc_title="RFC 2616: Hypertext Transfer Protocol -- HTTP/1.1 (obsolete)",
        doc_type="technical_standard",
        doc_version_date="1999-06-01",
        path=RAW / "rfc2616_http11_1999.txt",
        extractor=extract_txt,
    ),
    dict(
        doc_id="rfc9110_http_semantics",
        doc_title="RFC 9110: HTTP Semantics (current, obsoletes RFC 2616 HTTP/1.1 semantics)",
        doc_type="technical_standard",
        doc_version_date="2022-06-01",
        path=RAW / "rfc9110_http_semantics_2022.txt",
        extractor=extract_txt,
    ),
]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for doc in DOCS:
            text = doc["extractor"](doc["path"])
            chunks = chunk_text(text)
            print(f"{doc['doc_id']}: {len(text.split())} words -> {len(chunks)} chunks")
            for idx, chunk in enumerate(chunks):
                rec = {
                    "chunk_id": f"{doc['doc_id']}__{idx:04d}",
                    "doc_id": doc["doc_id"],
                    "doc_title": doc["doc_title"],
                    "doc_type": doc["doc_type"],
                    "doc_version_date": doc["doc_version_date"],
                    "text": chunk,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total += 1
    print(f"\nWrote {total} chunks to {OUT}")


if __name__ == "__main__":
    main()
