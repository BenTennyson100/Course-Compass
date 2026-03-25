import re
from typing import List, Dict

def strip_think_section(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

def strip_markdown_basic(text: str) -> str:
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"\*\*|\*|__|`+", "", text)
    text = re.sub(r"^\s*-\s*", "", text, flags=re.MULTILINE)
    return text.strip()

def clean_schedule_output(text: str) -> str:
    text = strip_think_section(text)
    lines = [ln.strip() for ln in text.splitlines()]
    filtered = []
    for ln in lines:
        if not ln:
            continue
        low = ln.lower()
        if any(token in low for token in ["<think", "</think", "i need to", "let's see", "okay", "let me", "so,"]):
            continue
        if re.match(r"^(okay|now,|so\b|let\b|i will|i can)\b", low):
            continue
        filtered.append(ln)
    return strip_markdown_basic("\n".join(filtered))

def safe_split_subjects(text: str) -> List[str]:
    return [s.strip() for s in re.split(r",|;", text) if s.strip()]

def parse_grades_input(text: str) -> Dict[str, float]:
    parts = re.split(r",|;", text)
    out: Dict[str, float] = {}
    for p in parts:
        if not p.strip():
            continue
        m = re.match(r"^\s*([A-Za-z &]+)\s*[:\-]?\s*(\d{1,3})\s*$", p.strip())
        if m:
            subj = m.group(1).strip()
            try:
                score = float(m.group(2))
                out[subj] = max(0.0, min(100.0, score))
            except ValueError:
                continue
    return out