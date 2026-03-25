import sys
import os
import json
import re
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel
from ollama import Client
from sqlalchemy.orm import Session

# Add Course_Compass to path so we can reuse prompts/utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Course_Compass'))
from prompts import PROMPTS
from utils import strip_think_section

from database import get_db, create_tables, ChatHistory, QuizHistory, User, UserMemory
from auth import (
    get_current_user, get_optional_user, get_google_auth_url,
    exchange_code_for_google_user, create_access_token,
    FRONTEND_URL,
)

OLLAMA_MODEL = "coursecompass"

app = FastAPI(title="Course Compass API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    try:
        create_tables()
    except Exception as e:
        print(f"[DB] Warning: could not create tables – {e}")


def get_client() -> Client:
    return Client()


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class PlannerRequest(BaseModel):
    subjects: str
    grades: str = ""
    days: List[str] = []

class QuizRequest(BaseModel):
    subject: str
    topic: str = ""
    num_questions: int = 10
    duration: int = 60

class QuizFeedbackRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str
    subject: str

class NotesRequest(BaseModel):
    notes: str
    action: str  # clean | summarize | outline | flashcards

class RecommendRequest(BaseModel):
    topic: str
    level: str
    weekly_hours: str

class SaveChatRequest(BaseModel):
    role: str
    content: str

class SaveQuizRequest(BaseModel):
    subject: str
    topic: str = ""
    score: int
    total: int

class MemoryExtractRequest(BaseModel):
    user_message: str
    assistant_message: str

class MemoryUpsertRequest(BaseModel):
    updates: dict   # {key: value}


# ─── Streaming Helper ─────────────────────────────────────────────────────────

def stream_ollama_sse(messages_list: list, system_prompt: str, num_predict: int = 1200, temperature: float = 0.2):
    """Generator that yields SSE events from Ollama streaming."""
    client = get_client()
    formatted = [{"role": "system", "content": system_prompt}]
    for m in messages_list:
        formatted.append({"role": m["role"], "content": m["content"]})

    try:
        stream = client.chat(
            model=OLLAMA_MODEL,
            messages=formatted,
            stream=True,
            options={"num_predict": num_predict, "temperature": temperature, "num_ctx": 4096},
        )
        in_think = False
        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if not token:
                continue
            if "<think>" in token:
                in_think = True
            if "</think>" in token:
                in_think = False
                continue
            if in_think:
                continue
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

# ─── Memory Helpers ────────────────────────────────────────────────────────────

MEMORY_CATEGORIES = {
    "learning_style":       "style",
    "expertise_level":      "level",
    "prefers_concise":      "preference",
    "prefers_examples":     "preference",
    "prefers_code":         "preference",
    "communication_tone":   "style",
    "interests":            "behavior",
    "struggles":            "behavior",
}

MEMORY_EXTRACT_PROMPT = """You are a memory extractor for an AI study assistant.
Analyze the conversation exchange below and extract behavioral insights about the user as a learner.

Return ONLY a valid JSON object with these keys (include only those you are confident about):
- "learning_style": "step-by-step" | "conceptual" | "example-driven" | "analogy-based"
- "expertise_level": "beginner" | "intermediate" | "advanced"
- "prefers_concise": "true" | "false"
- "prefers_examples": "true" | "false"
- "prefers_code": "true" | "false"
- "communication_tone": "formal" | "casual"
- "interests": "comma, separated, topics the user is interested in"
- "struggles": "comma, separated, topics the user finds difficult"

Return {} if nothing meaningful can be inferred. Output ONLY the JSON — no explanation."""


def _get_memory_dict(user_id: int, db) -> dict:
    rows = db.query(UserMemory).filter(UserMemory.user_id == user_id).all()
    return {r.key_name: {"value": r.value, "category": r.category} for r in rows}


def _build_memory_system_prompt(memory: dict) -> str:
    base = PROMPTS.SYSTEM
    if not memory:
        return base

    lines = ["\n\n[PERSONALIZATION — tailor every response based on this learner profile:]"]

    label_map = {
        "learning_style":     "Learning style",
        "expertise_level":    "Expertise level",
        "prefers_concise":    "Prefers concise answers",
        "prefers_examples":   "Wants examples",
        "prefers_code":       "Wants code snippets",
        "communication_tone": "Tone preference",
        "interests":          "Topics of interest",
        "struggles":          "Finds difficult",
    }

    for key, meta in memory.items():
        val = meta["value"]
        label = label_map.get(key, key.replace("_", " ").title())
        if key == "prefers_concise":
            val = "Yes — keep answers short and focused" if val == "true" else "No — detailed explanations preferred"
        elif key == "prefers_examples":
            val = "Yes — always include examples" if val == "true" else "No"
        elif key == "prefers_code":
            val = "Yes — include code snippets where relevant" if val == "true" else "No"
        lines.append(f"- {label}: {val}")

    lines.append("Adapt vocabulary, depth, tone, and examples to match this profile.")
    return base + "\n".join(lines)


def _feature_memory_hint(memory: dict, keys: list) -> str:
    """Build a short memory hint string for non-chat features."""
    parts = []
    label_map = {
        "learning_style":     "learning style",
        "expertise_level":    "expertise level",
        "prefers_concise":    "prefers concise output",
        "prefers_examples":   "wants examples",
        "prefers_code":       "wants code",
        "communication_tone": "tone",
        "interests":          "interested in",
        "struggles":          "struggles with",
    }
    for key in keys:
        if key in memory:
            val = memory[key]["value"]
            if key == "prefers_concise" and val == "true":
                parts.append("keep output concise")
            elif key == "prefers_concise" and val == "false":
                parts.append("provide detailed output")
            elif key == "prefers_examples" and val == "true":
                parts.append("include real-world examples")
            elif key == "prefers_code" and val == "true":
                parts.append("include code snippets where relevant")
            else:
                parts.append(f"{label_map.get(key, key)}: {val}")
    if not parts:
        return ""
    return "\n[Learner profile — tailor this response: " + "; ".join(parts) + "]"


# ─── Auth Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/auth/google")
def google_login():
    return RedirectResponse(url=get_google_auth_url())


@app.get("/api/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    try:
        google_user = await exchange_code_for_google_user(code)
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")

    google_id = google_user.get("id")
    email     = google_user.get("email")
    name      = google_user.get("name")
    picture   = google_user.get("picture")

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = User(google_id=google_id, email=email, name=name, picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.name    = name
        user.picture = picture
        db.commit()

    token = create_access_token(user.id)
    return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token={token}")


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id":      current_user.id,
        "email":   current_user.email,
        "name":    current_user.name,
        "picture": current_user.picture,
    }


# ─── History Endpoints ────────────────────────────────────────────────────────

@app.post("/api/history/chat")
def save_chat(req: SaveChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = ChatHistory(user_id=current_user.id, role=req.role, content=req.content)
    db.add(msg)
    db.commit()
    return {"ok": True}


@app.get("/api/history/chat")
def get_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    return [
        {"role": r.role, "content": r.content, "timestamp": r.created_at.isoformat()}
        for r in rows
    ]


@app.post("/api/history/quiz")
def save_quiz(req: SaveQuizRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = QuizHistory(
        user_id=current_user.id,
        subject=req.subject,
        topic=req.topic,
        score=req.score,
        total=req.total,
    )
    db.add(result)
    db.commit()
    return {"ok": True}


@app.get("/api/history/quiz")
def get_quiz_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(QuizHistory)
        .filter(QuizHistory.user_id == current_user.id)
        .order_by(QuizHistory.created_at.desc())
        .all()
    )
    return [
        {
            "subject":    r.subject,
            "topic":      r.topic,
            "score":      r.score,
            "total":      r.total,
            "percentage": round(r.score / r.total * 100) if r.total else 0,
            "timestamp":  r.created_at.isoformat(),
        }
        for r in rows
    ]


# ─── Memory Endpoints ────────────────────────────────────────────────────────

@app.get("/api/memory")
def get_memory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(UserMemory).filter(UserMemory.user_id == current_user.id).all()
    return [
        {
            "key":      r.key_name,
            "category": r.category,
            "value":    r.value,
            "updated":  r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@app.delete("/api/memory/{key}")
def delete_memory(key: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserMemory).filter(
        UserMemory.user_id == current_user.id,
        UserMemory.key_name == key,
    ).delete()
    db.commit()
    return {"ok": True}


@app.delete("/api/memory")
def clear_memory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserMemory).filter(UserMemory.user_id == current_user.id).delete()
    db.commit()
    return {"ok": True}


@app.post("/api/memory/upsert")
def upsert_memory(
    req: MemoryUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Directly set memory key-value pairs (no LLM needed)."""
    for key, value in req.updates.items():
        if not isinstance(value, str) or not value.strip():
            continue
        category = MEMORY_CATEGORIES.get(key, "general")
        existing = db.query(UserMemory).filter(
            UserMemory.user_id == current_user.id,
            UserMemory.key_name == key,
        ).first()
        if existing:
            existing.value    = value.strip()
            existing.category = category
        else:
            db.add(UserMemory(
                user_id=current_user.id,
                key_name=key,
                category=category,
                value=value.strip(),
            ))
    db.commit()
    return {"ok": True}


@app.post("/api/memory/extract")
async def extract_memory(
    req: MemoryExtractRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run a lightweight LLM call to extract behavioral insights and upsert into user_memory."""
    prompt = (
        f"{MEMORY_EXTRACT_PROMPT}\n\n"
        f"User: {req.user_message[:800]}\n"
        f"Assistant: {req.assistant_message[:800]}"
    )
    try:
        client = get_client()
        resp = client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 256, "temperature": 0.1},
        )
        raw = strip_think_section(resp.get("message", {}).get("content", "")).strip()

        # Parse JSON — be lenient (model may wrap in backticks)
        raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
        insights: dict = json.loads(raw) if raw and raw != "{}" else {}
    except Exception:
        return {"ok": False, "extracted": {}}

    for key, value in insights.items():
        if not isinstance(value, str) or not value.strip():
            continue
        category = MEMORY_CATEGORIES.get(key, "general")
        existing = db.query(UserMemory).filter(
            UserMemory.user_id == current_user.id,
            UserMemory.key_name == key,
        ).first()
        if existing:
            existing.value    = value.strip()
            existing.category = category
        else:
            db.add(UserMemory(
                user_id=current_user.id,
                key_name=key,
                category=category,
                value=value.strip(),
            ))
    db.commit()
    return {"ok": True, "extracted": insights}


# ─── Activity Endpoint ────────────────────────────────────────────────────────

@app.get("/api/activity")
def get_activity(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import func
    since = datetime.utcnow() - timedelta(days=70)

    chat_rows = (
        db.query(func.date(ChatHistory.created_at).label("date"), func.count().label("cnt"))
        .filter(ChatHistory.user_id == current_user.id, ChatHistory.created_at >= since, ChatHistory.role == "user")
        .group_by(func.date(ChatHistory.created_at))
        .all()
    )
    quiz_rows = (
        db.query(func.date(QuizHistory.created_at).label("date"), func.count().label("cnt"))
        .filter(QuizHistory.user_id == current_user.id, QuizHistory.created_at >= since)
        .group_by(func.date(QuizHistory.created_at))
        .all()
    )

    activity: dict = {}
    for row in chat_rows:
        d = str(row.date)
        entry = activity.setdefault(d, {"count": 0, "types": set()})
        entry["count"] += row.cnt
        entry["types"].add("chat")
    for row in quiz_rows:
        d = str(row.date)
        entry = activity.setdefault(d, {"count": 0, "types": set()})
        entry["count"] += row.cnt
        entry["types"].add("quiz")

    return [{"date": d, "count": v["count"], "types": list(v["types"])} for d, v in activity.items()]


# ─── General Endpoints ────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.post("/api/chat")
async def chat(
    req: ChatRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    msgs = [{"role": m.role, "content": m.content} for m in req.messages if m.role != "system"]

    # Inject personalized system prompt if user is authenticated
    system_prompt = PROMPTS.SYSTEM
    if current_user:
        memory = _get_memory_dict(current_user.id, db)
        if memory:
            system_prompt = _build_memory_system_prompt(memory)

    def gen():
        yield from stream_ollama_sse(msgs, system_prompt, num_predict=900, temperature=0.3)

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/api/planner")
async def planner(
    req: PlannerRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    days_str = ", ".join(req.days) if req.days else "Monday to Saturday"
    user_msg = (
        f"Create a weekly study schedule.\n"
        f"Subjects: {req.subjects}\n"
        f"Grades/Performance: {req.grades or 'Not specified'}\n"
        f"Available days: {days_str}\n"
        "Output only the schedule with explicit time slots. Prioritize lower-grade subjects."
    )

    system_prompt = PROMPTS.PLANNER
    if current_user:
        memory = _get_memory_dict(current_user.id, db)
        hint   = _feature_memory_hint(memory, ["expertise_level", "learning_style", "struggles", "prefers_concise"])
        if hint:
            system_prompt = PROMPTS.PLANNER + hint

    def gen():
        yield from stream_ollama_sse([{"role": "user", "content": user_msg}], system_prompt, num_predict=1100, temperature=0.15)

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/api/quiz/generate")
async def quiz_generate(
    req: QuizRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    topic_part = f" on {req.topic}" if req.topic else ""
    user_msg = (
        f"Generate exactly {req.num_questions} MCQs about {req.subject}{topic_part}.\n"
        "Format each question exactly as:\n"
        "N. Question\nA. opt\nB. opt\nC. opt\nD. opt\n**Answer:** X\n\n"
        "Output ONLY the questions, nothing else."
    )
    num_predict = min(req.num_questions * 140, 1800)

    quiz_system = PROMPTS.QUIZ
    if current_user:
        memory = _get_memory_dict(current_user.id, db)
        hint   = _feature_memory_hint(memory, ["expertise_level", "struggles"])
        if hint:
            quiz_system = PROMPTS.QUIZ + hint

    try:
        client = get_client()
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": quiz_system},
                {"role": "user", "content": user_msg},
            ],
            options={"num_predict": num_predict, "temperature": 0.25, "num_ctx": 4096},
        )
        raw = response.get("message", {}).get("content", "")
        raw = strip_think_section(raw)
        questions = _parse_mcq(raw)
        return {"questions": questions, "raw": raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _parse_mcq(text: str) -> list:
    questions = []
    blocks = re.split(r'\n\s*\n', text.strip())
    if len(blocks) <= 1:
        blocks = re.split(r'\n(?=\d+[\.\)]\s)', '\n' + text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        q_match = re.match(r'^(\d+)[\.\)]\s+(.+)', lines[0])
        if not q_match:
            continue
        q_num = int(q_match.group(1))

        q_lines = [q_match.group(2)]
        i = 1
        while i < len(lines):
            line = lines[i]
            if re.match(r'^\(?[A-Da-d]\)?[\.\)]\s', line):
                break
            if re.search(r'[Aa]nswer', line):
                break
            q_lines.append(line)
            i += 1
        q_text = ' '.join(q_lines).strip()

        options: dict = {}
        answer = None
        for line in lines[i:]:
            opt = re.match(r'^\(?([A-Da-d])\)?[\.\)]\s+(.+)', line)
            if opt:
                options[opt.group(1).upper()] = opt.group(2).strip()
                continue
            ans = re.search(r'[Aa]nswer[^A-Da-d\n]*([A-Da-d])', line)
            if ans:
                answer = ans.group(1).upper()

        if q_text and len(options) >= 2 and answer:
            questions.append({"num": q_num, "question": q_text, "options": options, "answer": answer})
    return questions


@app.post("/api/quiz/feedback")
async def quiz_feedback(req: QuizFeedbackRequest):
    user_msg = (
        f"Question ({req.subject}): {req.question}\n"
        f"Student answered: {req.user_answer}\n"
        f"Correct answer: {req.correct_answer}\n\n"
        "Explain in 2-3 sentences why the correct answer is right."
    )
    try:
        client = get_client()
        resp = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful tutor. Give brief, clear explanations."},
                {"role": "user", "content": user_msg},
            ],
            options={"num_predict": 256, "temperature": 0.2},
        )
        feedback = strip_think_section(resp.get("message", {}).get("content", ""))
        return {"feedback": feedback.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notes")
async def notes(
    req: NotesRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    action_map = {
        "clean":      "Clean and format these notes with proper headings and bullet points:",
        "summarize":  "Summarize these notes into 4-5 key bullet points:",
        "outline":    "Create a nested hierarchical outline from these notes:",
        "flashcards": "Create exactly 5 flashcard Q&A pairs.\nFormat each as:\nQ: [question]\nA: [answer]\n---",
    }
    prefix   = action_map.get(req.action, action_map["clean"])
    user_msg = f"{prefix}\n\n{req.notes}"
    notes_tokens = 900 if req.action == "clean" else 600

    system_prompt = PROMPTS.NOTES
    if current_user:
        memory = _get_memory_dict(current_user.id, db)
        hint   = _feature_memory_hint(memory, ["learning_style", "expertise_level", "prefers_concise"])
        if hint:
            system_prompt = PROMPTS.NOTES + hint

    def gen():
        yield from stream_ollama_sse([{"role": "user", "content": user_msg}], system_prompt, num_predict=notes_tokens, temperature=0.15)

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/api/recommend")
async def recommend(
    req: RecommendRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    user_msg = (
        f"Create a detailed learning path for: {req.topic}\n"
        f"Current level: {req.level}\n"
        f"Weekly time commitment: {req.weekly_hours}\n"
        "Include weekly breakdown, resources with links, hands-on projects, quick start plan, and summary."
    )

    system_prompt = PROMPTS.RECOMMEND
    if current_user:
        memory = _get_memory_dict(current_user.id, db)
        hint   = _feature_memory_hint(memory, ["expertise_level", "interests", "struggles", "prefers_examples", "prefers_code"])
        if hint:
            system_prompt = PROMPTS.RECOMMEND + hint

    def gen():
        yield from stream_ollama_sse([{"role": "user", "content": user_msg}], system_prompt, num_predict=1400, temperature=0.25)

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)
