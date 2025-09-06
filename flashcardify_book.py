#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
flashcardify_book.py
Turn an entire PDF book into flashcards (front/back, cloze, cloze-input).

- Reads JSON template packs from templates/ (fb, cloze, cloze_input)
- Extracts: concepts/definitions, equations, examples, code snippets, key paragraphs
- Generates diverse cards (20-30 templates supported; here we ship 30)
- Optional Gemini pass for polishing prompts / MCQ distractors
- Outputs CSV: type, front, back, content, hint, tags, template_id

Env (optional):
  GEMINI_API_KEY=...   # if you want Gemini help

Usage:
  python flashcardify_book.py -i Book.pdf -o flashcards.csv --use-gemini
"""

import argparse
import csv
import json
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF
import nltk
from tqdm import tqdm

# keyphrase helpers
import yake
from keybert import KeyBERT

# Optional: Gemini
_HAVE_GEMINI = False
try:
    import google.generativeai as genai
    _HAVE_GEMINI = True
except Exception:
    _HAVE_GEMINI = False


# ----------------------- utilities -----------------------

def ensure_nltk():
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

def sent_tokenize(text: str) -> List[str]:
    ensure_nltk()
    try:
        return nltk.sent_tokenize(text)
    except Exception:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def wrap_code_block(code: str) -> str:
    return f"~CODE[python]\n{code.rstrip()}\n~"

def to_tags(*vals) -> str:
    tags = []
    for v in vals:
        if isinstance(v, list):
            tags += v
        elif v:
            tags.append(str(v))
    # keep 2-3 tags as requested; dedupe; lowercase-ish
    dedup = []
    for t in tags:
        t = t.strip()
        if not t: continue
        t = re.sub(r"\s+", "_", t.lower())
        if t not in dedup:
            dedup.append(t)
        if len(dedup) >= 3:
            break
    return ",".join(dedup) if dedup else ""

def safe_replace(template: str, values: Dict[str, str]) -> str:
    """Replace [[var]] placeholders without touching cloze carets."""
    def repl(m):
        key = m.group(1)
        return values.get(key, f"[[{key}]]")
    return re.sub(r"\[\[([a-zA-Z0-9_]+)\]\]", repl, template)

def score_paragraph_importance(p: str, key_terms: List[str]) -> float:
    hits = sum(1 for k in key_terms if k.lower() in p.lower())
    return hits + min(3, len(p) / 400.0)  # length bonus


# ----------------------- PDF parsing -----------------------

@dataclass
class Span:
    text: str
    size: float
    bold: bool

@dataclass
class Block:
    page: int
    text: str
    size_avg: float
    bold_any: bool

HEADING_PATTERN = re.compile(r"^(\d+(\.\d+){0,3}\s+.+|[A-Z][A-Za-z0-9 ,:;\-\(\)]+)$")
MATH_LINE = re.compile(
    r"(?:[=≅≈≃≤≥≡∝∼↦→←↔]+)|(?:[∑∏∫∂∇∞√⋅·×÷]+)|"
    r"(?:\\(frac|sum|prod|int|sqrt|alpha|beta|gamma|delta|lambda|pi|sigma|theta|phi|psi|mu|nu)\b)|"
    r"(?:\bargmax\b|\bargmin\b)|(?:\bsubject\s*to\b)|"
    r"(?:\bTheorem\b|\bLemma\b|\bCorollary\b|\bProposition\b|\bDefinition\b)",
    re.IGNORECASE
)

def extract_blocks(doc: fitz.Document) -> List[Block]:
    out = []
    for pno in range(len(doc)):
        page = doc[pno]
        data = page.get_text("dict")
        for b in data.get("blocks", []):
            if b.get("type", 0) != 0:
                continue
            spans, texts = [], []
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    t = span.get("text", "")
                    if not t.strip():
                        continue
                    size = float(span.get("size", 0))
                    flags = int(span.get("flags", 0))
                    bold = bool(flags & 2)
                    texts.append(t)
                    spans.append(Span(t, size, bold))
            if spans:
                avg = sum(s.size for s in spans) / len(spans)
                out.append(Block(page=pno+1, text="".join(texts).strip(), size_avg=avg, bold_any=any(s.bold for s in spans)))
    return out

def split_sections(blocks: List[Block]) -> List[Tuple[str, List[str]]]:
    """Return [(section_title, [paragraphs...]), ...]"""
    sizes = [b.size_avg for b in blocks]
    med = sorted(sizes)[len(sizes)//2] if sizes else 10
    sections = []
    cur_title = "Introduction"
    cur_paras: List[str] = []
    def is_heading(b: Block) -> bool:
        t = b.text.strip()
        if not t: return False
        numbered = bool(re.match(r"^(\d+(\.\d+)*|[Cc]hapter\s+\d+|[Ss]ection\s+\d+)", t))
        allcaps = (t.upper() == t) and (len(t) <= 80)
        return (b.size_avg >= med + 1.0) or (b.bold_any and len(t) <= 120) or numbered or allcaps
    for b in blocks:
        if is_heading(b):
            if cur_paras:
                sections.append((cur_title, cur_paras))
                cur_paras = []
            cur_title = b.text.strip()
        else:
            if b.text.strip():
                cur_paras.append(b.text.strip())
    if cur_paras:
        sections.append((cur_title, cur_paras))
    return sections


# ----------------------- content mining -----------------------

def extract_keyphrases(text: str, top_k: int = 20) -> List[str]:
    terms = set()
    try:
        y = yake.KeywordExtractor(lan="en", n=1, top=top_k)
        for kw, _ in y.extract_keywords(text):
            if 2 <= len(kw) <= 60:
                terms.add(kw.strip())
    except Exception:
        pass
    try:
        kb = KeyBERT()
        for phrase, _ in kb.extract_keywords(text, top_n=top_k, stop_words="english"):
            if 2 <= len(phrase) <= 60:
                terms.add(phrase.strip())
    except Exception:
        pass
    return list(sorted(terms))

def guess_def_pairs(paragraphs: List[str]) -> List[Tuple[str, str]]:
    """Heuristics: 'Term: def', 'Term — def', 'X is a|an|the ...' """
    pairs = []
    for p in paragraphs:
        # split to sentences
        for s in sent_tokenize(p):
            m = re.match(r"^\s*([A-Z][A-Za-z0-9_\- ]{2,40})\s*[:—-]\s+(.+)$", s)
            if m:
                term = m.group(1).strip()
                d = m.group(2).strip()
                if 4 <= len(d) <= 500:
                    pairs.append((term, d))
                    continue
            m2 = re.match(r"^\s*([A-Z][A-Za-z0-9_\- ]{2,40})\s+is\s+(.*)$", s)
            if m2:
                term, d = m2.group(1).strip(), m2.group(2).strip()
                if 4 <= len(d) <= 500:
                    pairs.append((term, d))
    return pairs

def extract_equations(paragraphs: List[str]) -> List[Tuple[str, str]]:
    eqs = []
    for i, p in enumerate(paragraphs):
        for line in p.splitlines():
            if MATH_LINE.search(line.strip()):
                # try to name from previous line if looks like a label
                name = ""
                if i > 0 and len(paragraphs[i-1]) < 120:
                    prev = paragraphs[i-1].strip()
                    if re.search(r"(Law|Rule|Identity|Equation|Theorem|Lemma|Corollary|Proposition)", prev, re.I):
                        name = prev
                eqs.append((name, line.strip()))
    # dedupe
    seen = set(); out = []
    for n, e in eqs:
        key = (n.lower(), e)
        if key not in seen:
            seen.add(key); out.append((n, e))
    return out

CODE_START = re.compile(r"^\s*(def |class |import |from |for |while |if |try:|with |print\(|#|@)")
def extract_code_snippets(paragraphs: List[str]) -> List[str]:
    """Heuristic: gather small code-ish blocks by consecutive 'code-like' lines."""
    blocks = []
    cur = []
    for p in paragraphs:
        for ln in p.splitlines():
            if CODE_START.search(ln) or ln.strip().endswith(":"):
                cur.append(ln)
            else:
                if cur:
                    blocks.append("\n".join(cur)); cur = []
        if cur:
            blocks.append("\n".join(cur)); cur = []
    # dedupe & keep modest size
    uniq = []
    for b in blocks:
        b = b.strip()
        if 10 <= len(b) <= 1200 and b not in uniq:
            uniq.append(b)
    return uniq

def pick_reader_paragraphs(paragraphs: List[str], key_terms: List[str], k: int = 20) -> List[str]:
    scored = [(score_paragraph_importance(p, key_terms), p) for p in paragraphs if len(p) > 200]
    scored.sort(reverse=True)
    return [p for _, p in scored[:k]]


# ----------------------- Gemini helpers (optional) -----------------------

def maybe_configure_gemini() -> bool:
    if not _HAVE_GEMINI:
        return False
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return False
    try:
        genai.configure(api_key=key)
        return True
    except Exception:
        return False

def gemini_make_mcq(concept: str, definition: str, n_opts: int = 4) -> Optional[Tuple[str, List[str], int, str]]:
    """Return (question, options, correct_index, rationale) or None."""
    if not maybe_configure_gemini():
        return None
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "Create a tight multiple-choice question to test understanding of a concept.\n"
            "Concept: " + concept + "\nDefinition: " + definition + "\n"
            "Output JSON with keys: question, options (array of " + str(n_opts) + "), correct, rationale."
        )
        resp = model.generate_content(prompt)
        txt = resp.text if hasattr(resp, "text") else ""
        m = re.search(r"\{[\s\S]+\}", txt)
        data = json.loads(m.group(0)) if m else json.loads(txt)
        q = data.get("question","").strip()
        opts = [o.strip() for o in data.get("options",[])][:n_opts]
        correct = int(data.get("correct", 0))
        rationale = data.get("rationale","").strip()
        if q and len(opts) == n_opts:
            return (q, opts, correct, rationale)
    except Exception:
        return None
    return None


# ----------------------- template loading -----------------------

def load_templates(dirpath: Path) -> Dict[str, List[dict]]:
    groups = {"fb": [], "cloze": [], "cloze_input": []}
    fpacks = {
        "fb": dirpath / "fb_templates.json",
        "cloze": dirpath / "cloze_templates.json",
        "cloze_input": dirpath / "cloze_input_templates.json"
    }
    for k, p in fpacks.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing template pack: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        groups[k] = data
    return groups


# ----------------------- card building -----------------------

def build_fb_card(tpl: dict, vals: Dict[str, str]) -> Dict[str, str]:
    front = safe_replace(tpl["render"]["front"], vals)
    back = safe_replace(tpl["render"]["back"], vals)
    hint = safe_replace(tpl["render"].get("hint",""), vals)
    tags = to_tags(vals.get("tags", []), tpl["render"].get("tag_rules", []))
    return {"type": "fb", "front": front, "back": back, "content": "", "hint": hint, "tags": tags, "template_id": tpl["id"]}

def build_cloze_card(tpl: dict, vals: Dict[str, str]) -> Dict[str, str]:
    content = safe_replace(tpl["render"]["content"], vals)
    hint = safe_replace(tpl["render"].get("hint",""), vals)
    tags = to_tags(vals.get("tags", []), tpl["render"].get("tag_rules", []))
    return {"type": "cloze", "front": "", "back": "", "content": content, "hint": hint, "tags": tags, "template_id": tpl["id"]}

def build_cin_card(tpl: dict, vals: Dict[str, str]) -> Dict[str, str]:
    content = safe_replace(tpl["render"]["content"], vals)
    hint = safe_replace(tpl["render"].get("hint",""), vals)
    tags = to_tags(vals.get("tags", []), tpl["render"].get("tag_rules", []))
    return {"type": "cloze_input", "front": "", "back": "", "content": content, "hint": hint, "tags": tags, "template_id": tpl["id"]}


# ----------------------- pipeline -----------------------

def make_cards_from_section(title: str, paras: List[str], tpls: Dict[str, List[dict]], use_gemini: bool) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    joined = "\n".join(paras)
    key_terms = extract_keyphrases(joined, top_k=20)

    # 1) Concepts & definitions
    defs = guess_def_pairs(paras)
    # (concept FB + cloze)
    for term, definition in defs[:50]:
        # FB concept (basic)
        tpl_fb = random.choice([t for t in tpls["fb"] if t["id"] in ("fb_concept_basic", "fb_concept_context")])
        ctx_sent = ""
        # choose one context sentence near definition if available
        for p in paras:
            if term in p and len(p) < 400:
                ctx_sent = p.strip(); break
        vals = {"term": term, "definition": definition, "context": ctx_sent, "tags": [title, "concept"]}
        cards.append(build_fb_card(tpl_fb, vals))

        # Cloze — hide term
        tpl_cz = next(t for t in tpls["cloze"] if t["id"] == "cloze_def_missing_term")
        cards.append(build_cloze_card(tpl_cz, {"term": term, "definition": definition, "tags": [title, "concept"]}))

        # Optional MCQ on concept (front/back with options in front, answer on back)
        if use_gemini:
            mcq = gemini_make_mcq(term, definition, n_opts=4)
            if mcq:
                q, opts, correct_idx, rationale = mcq
                front = q + "\n\n" + "\n".join([f"({chr(65+i)}) {opt}" for i, opt in enumerate(opts)])
                back = f"Answer: ({chr(65+correct_idx)}) {opts[correct_idx]}\n\nWhy: {rationale}"
                cards.append({
                    "type": "fb", "front": front, "back": back, "content": "",
                    "hint": "Eliminate distractors.", "tags": to_tags(title, "mcq", term),
                    "template_id": "fb_mcq_gemini"
                })

    # 2) Equations
    eqs = extract_equations(paras)[:40]
    for name, eq in eqs:
        # FB: equation name → formula
        tpl_fb = next(t for t in tpls["fb"] if t["id"] == "fb_equation_name")
        vals = {"equation_name": name or "This equation", "equation": eq, "tags": [title, "equation"]}
        cards.append(build_fb_card(tpl_fb, vals))

        # Cloze (symbol)
        tpl_cz = next(t for t in tpls["cloze"] if t["id"] == "cloze_equation_symbol")
        # pick a variable-like token to hide
        m = re.findall(r"[a-zA-Z]\\w{0,2}", eq)
        hide = m[0] if m else ""
        eq_clozed = eq.replace(hide, f"{{{{c1::{hide}}}}}", 1) if hide else f"{{{{c1::{eq}}}}}"
        cards.append(build_cloze_card(tpl_cz, {"equation_clozed": eq_clozed, "tags": [title, "equation"]}))

        # Cloze-input: require typing a key piece
        tpl_cin = next(t for t in tpls["cloze_input"] if t["id"] == "cin_equation_term")
        eq_cin = eq.replace(hide, f"{{{{cin1::{hide}}}}}", 1) if hide else f"{{{{cin1::{eq}}}}}"
        cards.append(build_cin_card(tpl_cin, {"equation_cin": eq_cin, "tags": [title, "equation"]}))

    # 3) Code snippets (if any)
    codes = extract_code_snippets(paras)[:25]
    for code in codes:
        # Cloze-input: remove a keyword/identifier
        tpl_cin = next(t for t in tpls["cloze_input"] if t["id"] == "cin_code_line")
        # pick token
        token = None
        toks = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code)
        if toks:
            token = random.choice(toks[:8])
        code_cin = code.replace(token, f"{{{{cin1::{token}}}}}", 1) if token else f"{{{{cin1::{code}}}}}"
        cards.append(build_cin_card(tpl_cin, {"code_cin": code_cin, "tags": [title, "code"]}))

        # Cloze (API arg)
        tpl_cz = next(t for t in tpls["cloze"] if t["id"] == "cloze_api_call")
        # hide '(' + argname
        arg = None
        m = re.search(r"([a-zA-Z_][A-Za-z0-9_]*)\s*=", code)
        if m:
            arg = m.group(1)
        api_clozed = code.replace(f"{arg}=", f"{{{{c1::{arg}}}}}=", 1) if arg else f"{{{{c1::{code}}}}}"
        cards.append(build_cloze_card(tpl_cz, {"api_clozed": api_clozed, "tags": [title, "api"]}))

    # 4) Reader paragraphs
    terms = extract_keyphrases(joined, top_k=30)
    readers = pick_reader_paragraphs(paras, terms, k=10)
    for para in readers:
        tpl_fb = next(t for t in tpls["fb"] if t["id"] == "fb_reader")
        cards.append(build_fb_card(tpl_fb, {"paragraph": para, "tags": [title, "reader"]}))

    # 5) Theorems (simple heuristic: sentences starting with Theorem/Lemma/…)
    theorems = []
    for p in paras:
        for s in sent_tokenize(p):
            if re.match(r"^(Theorem|Lemma|Corollary|Proposition)\\b", s):
                theorems.append(s)
    for s in theorems[:20]:
        name = s.split(":")[0].strip()
        tpl_fb = next(t for t in tpls["fb"] if t["id"] == "fb_theorem")
        cards.append(build_fb_card(tpl_fb, {"theorem_name": name, "statement": s, "tags": [title, "theorem"]}))

    return cards


# ----------------------- CSV writer -----------------------

CSV_FIELDS = ["type", "front", "back", "content", "hint", "tags", "template_id"]

def write_csv(path: Path, rows: List[Dict[str, str]]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            row = {k: r.get(k, "") for k in CSV_FIELDS}
            w.writerow(row)


# ----------------------- CLI -----------------------

def main():
    ap = argparse.ArgumentParser(description="Turn a PDF book into flashcards (fb/cloze/cloze_input).")
    ap.add_argument("-i", "--input", required=True, help="Path to PDF book")
    ap.add_argument("-o", "--output", default="flashcards.csv", help="Output CSV file")
    ap.add_argument("--templates", default="templates", help="Templates directory containing the three JSON files")
    ap.add_argument("--use-gemini", action="store_true", help="Use Gemini for MCQs/polish (set GEMINI_API_KEY env var)")
    args = ap.parse_args()

    tpl_dir = Path(args.templates).resolve()
    tpls = load_templates(tpl_dir)
    pdf = Path(args.input).resolve()
    if not pdf.exists():
        print(f"Input not found: {pdf}", file=sys.stderr); sys.exit(2)

    # Configure Gemini if requested
    use_gemini = bool(args.use_gemini and maybe_configure_gemini())

    doc = fitz.open(pdf)
    blocks = extract_blocks(doc)
    sections = split_sections(blocks)

    all_cards: List[Dict[str, str]] = []
    for title, paras in tqdm(sections, desc="Sections"):
        cards = make_cards_from_section(title, paras, tpls, use_gemini=use_gemini)
        all_cards.extend(cards)

    # Light dedupe by (type, front/content)
    seen = set()
    unique_cards = []
    for c in all_cards:
        key = (c["type"], (c["front"] or c["content"]).strip())
        if key not in seen and len((c["front"]+c["content"]).strip()) >= 8:
            seen.add(key)
            unique_cards.append(c)

    out = Path(args.output).resolve()
    write_csv(out, unique_cards)
    print(f"\nWrote {len(unique_cards)} cards → {out}")

if __name__ == "__main__":
    main()
