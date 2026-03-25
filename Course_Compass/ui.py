# ui.py — ChatGPT-style UI using st.chat_message and safe streaming fallback
import time
import re
from typing import List, Dict, Optional
import pandas as pd
import streamlit as st
import asyncio

from utils import safe_split_subjects, parse_grades_input, strip_markdown_basic, strip_think_section
from ollama_client import query_llm, stream_chat_and_collect
from prompts import PROMPTS

# safe rerun helper (works across streamlit versions)
def _safe_rerun():
    """
    Try to trigger a script rerun in a way that works across Streamlit versions.
    If internal APIs are not available, return gracefully (no-op).
    """
    try:
        # Streamlit >= 1.18-ish internal API
        from streamlit.runtime.scriptrunner.script_runner import RerunException
        raise RerunException()
    except Exception:
        try:
            # Older Streamlit internal path
            from streamlit.script_runner import RerunException
            raise RerunException()
        except Exception:
            # Last resort: do nothing (the function will return, and the page will re-render on next interaction)
            return

# --- Styling (minor CSS) ---
st.markdown(
    """
    <style>
    .stApp .block-container { padding-top: 1.5rem; max-width: 1200px; }
    .chat-input { border-radius: 12px; }
    .streaming-indicator { color: #9ca3af; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

import json
from urllib.parse import quote_plus


# ----------------- Helper utilities -----------------

def _try_extract_json(text: str) -> Optional[dict]:
    """Try to find & parse the first JSON object in `text`. Returns dict or None."""
    json_match = re.search(r"(\{(?:.|\n)*\})", text)
    if json_match:
        candidate = json_match.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            fixed = re.sub(r",\s*}\b", "}", candidate)
            fixed = re.sub(r",\s*\]", "]", fixed)
            try:
                return json.loads(fixed)
            except Exception:
                return None
    return None


def _parse_sections_from_text(text: str):
    """Splits freeform text into (heading, content) sections.
    Returns list of (heading, content).
    """
    pattern = re.compile(
        r"(?m)^\s*(?:#{1,6}\s*)?(Week\s*\d+|Day\s*\d+|Resources|Projects|Quick[- ]?Start|Quick Start|Summary|Overview)\b[:\-]?\s*",
        flags=re.IGNORECASE,
    )
    parts = []
    last_pos = 0
    last_head = "Overview"
    matches = list(pattern.finditer(text))
    if not matches:
        return [("Overview", text.strip())]
    for m in matches:
        start = m.start()
        head = m.group(1).strip()
        if start != last_pos:
            content = text[last_pos:start].strip()
            if content:
                parts.append((last_head, content))
        last_head = head
        last_pos = m.end()
    tail = text[last_pos:].strip()
    if tail:
        parts.append((last_head, tail))
    normalized = []
    for h, c in parts:
        h_norm = h.title()
        normalized.append((h_norm, c.strip()))
    return normalized


def render_recommendation_structured(data: dict):
    """Render parsed recommendation dict in Streamlit with sections."""
    if overview := data.get("overview") or data.get("Overview"):
        st.markdown(f"**Overview**\n\n{overview}")

    weeks = data.get("weeks") or data.get("Weeks") or []
    if weeks:
        st.markdown("### Study Plan")
        for i, w in enumerate(weeks, start=1):
            if isinstance(w, dict):
                title = w.get("title") or f"Week {i}"
                body = w.get("content") or w.get("tasks") or ""
                st.markdown(f"**{title}**\n\n{body}")
            else:
                st.markdown(f"**Week {i}**\n\n{w}")

    resources = data.get("resources") or data.get("Resources") or []
    if resources:
        st.markdown("### Resources")
        for r in resources:
            if isinstance(r, dict):
                title = r.get("title") or r.get("name") or ""
                url = r.get("url") or r.get("link") or ""
                note = r.get("note") or r.get("desc") or ""
                if url:
                    st.markdown(f"- [{title or url}]({url}) — {note}")
                else:
                    st.markdown(f"- {title} — {note}")
            else:
                url_match = re.search(r"(https?://\S+)", str(r))
                if url_match:
                    url = url_match.group(1)
                    text_only = re.sub(rf"{re.escape(url)}", "", str(r)).strip()
                    st.markdown(f"- [{text_only or url}]({url})")
                else:
                    st.markdown(f"- {r}")

    projects = data.get("projects") or data.get("Projects") or []
    if projects:
        st.markdown("### Suggested Projects")
        for p in projects:
            if isinstance(p, dict):
                st.markdown(f"- **{p.get('title','Project')}** — {p.get('desc','')}")
            else:
                st.markdown(f"- {p}")

    quick = data.get("quick_start") or data.get("Quick Start") or data.get("quickstart")
    if quick:
        st.markdown("### Quick Start (2–4 weeks)")
        if isinstance(quick, list):
            for q in quick:
                st.markdown(f"- {q}")
        else:
            st.markdown(quick)

    if summary := data.get("summary") or data.get("Summary"):
        st.markdown("### Summary")
        st.markdown(summary)


# ----------------- Chat / UI logic -----------------

def _render_history():
    """Render the chat history using st.chat_message bubbles."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for entry in st.session_state.chat_history:
        role, text = entry[0], entry[1]
        with st.chat_message(role):
            st.markdown(text)


def _safe_stream_or_fallback(messages: List[Dict], placeholder, max_tokens: int = 1024) -> str:
    """Attempt to stream; if running inside an active event loop (Streamlit environment),
    fall back to non-streaming query to avoid asyncio.run conflicts.

    This keeps the UI robust across different hosting environments.
    """
    try:
        # If there is a running loop, get_running_loop() returns it (no exception).
        asyncio.get_running_loop()
        # We're inside an event loop (e.g., Streamlit's runtime). Streaming helper may try to
        # call asyncio.run which would fail — use synchronous query as a safe fallback.
        placeholder.markdown("*(stream unavailable in this environment; fetching full response...)*")
        return query_llm(messages, max_tokens=max_tokens)
    except RuntimeError:
        # No running loop — safe to perform our streaming helper which uses asyncio.run
        return stream_chat_and_collect(messages, placeholder, max_tokens=max_tokens)

@st.fragment
def chat_tab():
    # Initialize state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Render previous messages
    for role, msg, *_ in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    # Input box (only one!)
    user_msg = st.chat_input("Ask anything about studies, courses, skills...")

    if user_msg:
        # Add user message
        st.session_state.chat_history.append(("user", user_msg, time.time()))

        # Build messages to send to model
        recent = st.session_state.chat_history[-12:]
        messages = [{"role": "system", "content": PROMPTS.SYSTEM}]
        for r, t, *_ in recent:
            messages.append({"role": r, "content": t})

        # Start assistant message bubble
        with st.chat_message("assistant"):
            placeholder = st.empty()

            # Try streaming
            try:
                full = stream_chat_and_collect(
                    messages,
                    placeholder,
                    max_tokens=1024
                )
            except Exception as e:
                placeholder.markdown(f"*(stream failed — falling back)*")
                full = query_llm(messages)

        # Clean the output
        full = strip_think_section(full)
        full = strip_markdown_basic(full)

        # Save assistant message
        st.session_state.chat_history.append(("assistant", full, time.time()))

        # Refresh UI
        st.rerun()

# ---------- STUDY PLANNER TAB ----------
def planner_tab():
    st.header("🗓️ Create Study Plan")
    with st.form("planner_form"):
        subjects_str = st.text_input("Enter subjects (comma separated)", value="Math, Physics, Chemistry")
        grades_str = st.text_input("Enter your subjects and grades (e.g., Math: 70, Physics: 85)")
        include_weekdays = st.multiselect(
            "Days to include",
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        )
        submit = st.form_submit_button("Create Study Plan with Weekly Time Slots")
    if submit:
        subjects = safe_split_subjects(subjects_str)
        grades = parse_grades_input(grades_str)
        if not subjects:
            st.warning("Please enter at least one subject.")
            return
        grades_text = ", ".join([f"{s}: {int(g)}" for s, g in grades.items()]) if grades else "No grades provided"
        user_prompt = (
            f"The student studies these subjects: {', '.join(subjects)}.\n"
            f"Grades: {grades_text}.\n"
            f"Create a weekly study schedule across these days: {', '.join(include_weekdays)}."
        )
        messages = [
            {"role": "system", "content": PROMPTS.PLANNER},
            {"role": "user", "content": user_prompt},
        ]
        with st.spinner("Creating study plan..."):
            response = query_llm(messages, max_tokens=700)
        st.text_area("Study Plan", value=response, height=350)
        st.download_button("Download Plan (.txt)", response, file_name="study_plan.txt", mime="text/plain")


# ---------- PROGRESS TAB ----------
def progress_tab():
    st.header("📈 Visualize Subject Progress")
    st.write("Each term can have different subjects. Enter term details below:")
    if "terms" not in st.session_state:
        st.session_state.terms = []

    with st.form("progress_form"):
        n_terms = st.number_input("Number of terms to compare", min_value=2, max_value=6, value=3, step=1)
        term_entries = []
        for idx in range(int(n_terms)):
            st.markdown(f"**Term {idx+1}**")
            term_name = st.text_input(f"Term name {idx+1}", value=f"Term {idx+1}", key=f"term_name_{idx}")
            subjects = st.text_input(
                f"Subjects for {term_name} (comma separated)",
                value="Math, Physics, Chemistry" if idx == 0 else "",
                key=f"term_subjects_{idx}",
            )
            subj_list = safe_split_subjects(subjects)
            scores = {}
            for subj in subj_list:
                score = st.number_input(f"{subj} score for {term_name}", min_value=0, max_value=100, value=0, key=f"{term_name}_{subj}_score")
                scores[subj] = float(score)
            term_entries.append((term_name, scores))
        submit = st.form_submit_button("Show Progress Chart")

    if submit:
        data = {}
        terms_order = []
        for term_name, scores in term_entries:
            terms_order.append(term_name)
            data[term_name] = scores
        all_subjects = set()
        for d in data.values():
            all_subjects.update(d.keys())
        df = pd.DataFrame(index=terms_order, columns=sorted(all_subjects), dtype=float)
        for term in terms_order:
            scores = data.get(term, {})
            for subj in all_subjects:
                df.at[term, subj] = scores.get(subj, None)
        st.line_chart(df)
        st.dataframe(df.T, use_container_width=True)
        st.download_button("Download progress CSV", df.to_csv(), file_name="progress.csv", mime="text/csv")


# ---------- QUIZ TAB ----------
def quiz_tab():
    import time

    st.header("📝 Generate & Take a Multiple-Choice Quiz")

    # Safe rerun helper must be defined once in the module (see above).
    # Initialize session state variables
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = None
    if "generated_quiz_raw" not in st.session_state:
        st.session_state.generated_quiz_raw = None
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "quiz_start_time" not in st.session_state:
        st.session_state.quiz_start_time = None
    if "quiz_duration" not in st.session_state:
        st.session_state.quiz_duration = 0   # seconds

    # ---------------- FORM TO CREATE QUIZ -----------------
    with st.form("quiz_form"):
        subject = st.text_input("Subject (e.g., Biology, NLP, DSA)", key="quiz_subject")
        topic = st.text_input("Optional Topic", key="quiz_topic")
        num_questions = st.selectbox("Number of Questions", [5, 10, 15, 20], index=2)
        duration = st.selectbox("Quiz Timer (seconds)", [30, 60, 90, 120], index=1)

        submit = st.form_submit_button(f"Generate {num_questions} MCQs")

    # ---------------- GENERATE QUIZ -----------------
    if submit:
        if not subject.strip():
            st.warning("Please enter a subject.")
            return

        st.session_state.quiz_duration = int(duration)
        st.session_state.quiz_start_time = time.time()

        full_topic = f" on {topic.strip()}" if topic.strip() else ""
        user_prompt = (
            f"Generate {num_questions} multiple-choice questions for {subject.strip()}{full_topic}.\n"
            f"Format strictly as:\n\n"
            f"1. Question text\n"
            f"A) Option 1\nB) Option 2\nC) Option 3\nD) Option 4\n"
            f"**Answer:** C\n\n"
            f"No explanations. Only one correct answer."
        )

        messages = [
            {"role": "system", "content": PROMPTS.QUIZ},
            {"role": "user", "content": user_prompt},
        ]

        with st.spinner("Generating quiz..."):
            raw_quiz = query_llm(messages, max_tokens=1500)

        st.session_state.generated_quiz_raw = raw_quiz

        # Parse MCQs (flexible)
        q_pattern = re.compile(
            r"^\s*(\d+)\.\s*(.+?)\nA\)\s*(.+?)\nB\)\s*(.+?)\nC\)\s*(.+?)\nD\)\s*(.+?)\n\*\*Answer:\*\*\s*([A-D])",
            re.MULTILINE | re.DOTALL,
        )
        matches = q_pattern.findall(raw_quiz)

        questions = []
        if matches:
            for match in matches[:num_questions]:
                qnum, qtext, A, B, C, D, correct = match
                questions.append({
                    "num": int(qnum),
                    "question": qtext.strip(),
                    "options": {"A": A.strip(), "B": B.strip(), "C": C.strip(), "D": D.strip()},
                    "answer": correct.strip(),
                })
        else:
            # fallback: simpler split + best-effort extract
            parts = re.split(r"(?m)^\s*\d+\.\s+", raw_quiz)
            parts = [p.strip() for p in parts if p.strip()][:num_questions]
            for i, p in enumerate(parts):
                a_m = re.search(r"\*\*Answer:\*\*\s*([A-D])", p, re.IGNORECASE | re.DOTALL)
                ans = a_m.group(1).strip() if a_m else ""
                q_line = p.splitlines()[0] if p.splitlines() else p
                # attempt to extract options (best-effort)
                opts = {}
                for opt_label in ["A)", "B)", "C)", "D)"]:
                    m = re.search(rf"{re.escape(opt_label)}\s*(.+?)(?:\n|$)", p)
                    if m:
                        opts[opt_label[0]] = m.group(1).strip()
                # fall back to empty strings when not found
                for k in ["A", "B", "C", "D"]:
                    opts.setdefault(k, "")
                questions.append({
                    "num": i + 1,
                    "question": q_line.strip(),
                    "options": opts,
                    "answer": ans,
                })

        st.session_state.quiz_questions = questions
        st.session_state.user_answers = {}
        # trigger rerun safely so UI picks up new state immediately
        _safe_rerun()
        return

    # -------------------------------------------------------
    # ---------------- DISPLAY QUIZ + TIMER -----------------
    # -------------------------------------------------------
    if st.session_state.quiz_questions:
        # TIMER HANDLING (computed from stored start time)
        elapsed = int(time.time() - (st.session_state.quiz_start_time or 0))
        remaining = int(st.session_state.quiz_duration - elapsed)

        if remaining <= 0:
            st.error("⏰ Time’s up! Auto-submitting your quiz...")
            auto_submit = True
        else:
            st.markdown(f"### ⏳ Time Remaining: **{remaining} seconds**")
            # show simple progress as fraction (0.0-1.0)
            if st.session_state.quiz_duration > 0:
                progress_val = max(0.0, min(1.0, remaining / st.session_state.quiz_duration))
                st.progress(progress_val)

            auto_submit = False

        # DISPLAY QUESTIONS
        st.subheader("Your Quiz")
        for q in st.session_state.quiz_questions:
            st.markdown(f"**{q['num']}. {q['question']}**")
            # If options exist, show radio, else text input
            if q.get("options"):
                st.session_state.user_answers[q['num']] = st.radio(
                    "Select answer:",
                    ["A", "B", "C", "D"],
                    index=0,
                    key=f"radio_{q['num']}"
                )
            else:
                st.session_state.user_answers[q['num']] = st.text_input(
                    f"Your answer for Q{q['num']}",
                    key=f"qa_{q['num']}"
                )

        # Manual Submit Button
        submit_btn = st.button("Submit Quiz")
        if submit_btn or auto_submit:
            score = 0
            for q in st.session_state.quiz_questions:
                correct = q.get("answer", "").strip().upper()
                user = (st.session_state.user_answers.get(q["num"]) or "").strip().upper()
                if user and user == correct:
                    score += 1

            # Build feedback prompt for LLM if you want a verbose explanation
            feedback_prompt = f"User Score: {score}/{len(st.session_state.quiz_questions)}\n\n"
            feedback_prompt += "Provide short feedback for questions answered incorrectly:\n"
            for q in st.session_state.quiz_questions:
                feedback_prompt += (
                    f"Q{q['num']}: User answered '{st.session_state.user_answers.get(q['num'])}'. "
                    f"Correct is '{q.get('answer', '')}'. "
                    f"Question: {q['question']}\n"
                )

            grade_messages = [
                {"role": "system", "content": "Provide short helpful feedback per wrong question."},
                {"role": "user", "content": feedback_prompt},
            ]

            with st.spinner("Generating feedback..."):
                feedback = query_llm(grade_messages, max_tokens=800)

            st.markdown(f"## 🏆 Final Score: **{score}/{len(st.session_state.quiz_questions)}**")
            st.markdown("### 📝 Feedback")
            st.markdown(feedback)

            st.download_button(
                "Download Quiz & Feedback",
                f"Quiz:\n{st.session_state.generated_quiz_raw}\n\nFeedback:\n{feedback}",
                file_name="quiz_and_feedback.txt"
            )

            # Reset quiz state
            st.session_state.quiz_questions = None
            st.session_state.generated_quiz_raw = None
            st.session_state.user_answers = {}
            st.session_state.quiz_start_time = None
            st.session_state.quiz_duration = 0
            # no explicit rerun required; the app will rerun on next interaction
            return

# ---------- NOTES TAB ----------
def notes_tab():
    st.header("📓 Smart Note Taker")
    with st.form("notes_form"):
        raw_notes = st.text_area("Paste your raw lecture or reading notes here:", height=200)
        action = st.radio("Action", ["Clean & Format", "Summarize", "Outline", "Flashcards"])
        submit = st.form_submit_button("Process Notes")
    if submit and raw_notes.strip():
        messages = [{"role": "system", "content": PROMPTS.NOTES}]
        messages.append({"role": "user", "content": f"Action: {action}\n\n{raw_notes}"})
        with st.spinner("Processing notes..."):
            result = query_llm(messages, max_tokens=800)
        st.session_state.processed_notes = result

    if st.session_state.get("processed_notes"):
        st.subheader("Processed Notes")
        st.text_area("Result", st.session_state.processed_notes, height=300)
        st.download_button("📥 Download as .txt", st.session_state.processed_notes, file_name="course_compass_notes.txt", mime="text/plain")


# ---------- COURSE RECOMMENDER TAB ----------
def recommend_tab():
    st.header("🎯 Personalized Course Recommendations & Learning Path")
    topic = st.text_input(
        "Enter a topic you want to upskill in (e.g., NLP, Web Development, Data Science):",
        key="rec_topic",
    )
    level = st.selectbox("Select your current level:", ["Beginner", "Intermediate", "Advanced"], key="rec_level")
    time_commit = st.selectbox(
        "Weekly time commitment:", ["2-4 hours", "5-8 hours", "8-12 hours", "12+ hours"], key="rec_time"
    )
    submit = st.button("Generate Recommendations")

    if submit and topic.strip():
        user_prompt = (
            f"I want to upskill in {topic.strip()}. I am a {level} learner and can study {time_commit} weekly. "
            f"Please produce a practical learning path with timeline, recommended courses, estimated hours, "
            f"suggested projects, checkpoints, and key skills. Prefer a clean sectioned Markdown format with clear headings."
        )

        system_msg = (
            PROMPTS.RECOMMEND
            + "\n\nReturn in Markdown format with top-level sections:\n"
            + "- Overview\n- Week 1, Week 2, ... (each inside '###')\n"
            + "- Resources\n- Projects\n- Quick Start\n- Summary\n"
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ]

        with st.spinner("Generating personalized learning path..."):
            raw = query_llm(messages, max_tokens=1400)

        st.markdown("## 🧠 Learning Path Overview")

        sections = _parse_sections_from_text(raw)
        if not sections:
            st.markdown(raw)
            return

        for heading, content in sections:
            heading_clean = heading.strip().title()

            if re.match(r"^Week\s*\d+", heading_clean, re.IGNORECASE):
                with st.expander(f"📘 {heading_clean}", expanded=False):
                    st.markdown(content)
            elif "Overview" in heading_clean:
                st.markdown(f"### 🌟 {heading_clean}")
                st.markdown(content)
            elif any(k in heading_clean for k in ["Resource", "Material"]):
                st.markdown("### 🔗 Resources")
                lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
                for line in lines:
                    url_match = re.search(r"(https?://\S+)", line)
                    if url_match:
                        url = url_match.group(1)
                        text = re.sub(r"\(?.*https?://\S+\)?", "", line).strip(" -–:")
                        st.markdown(f"- [{text or url}]({url})")
                    else:
                        st.markdown(f"- {line}")
            elif "Project" in heading_clean:
                st.markdown("### 🧩 Projects")
                for ln in content.split("\n"):
                    if ln.strip():
                        st.markdown(f"- {ln.strip()}")
            elif "Quick" in heading_clean:
                st.markdown("### ⚡ Quick Start Plan")
                st.markdown(content)
            elif "Summary" in heading_clean:
                st.markdown("### 🔍 Summary")
                st.markdown(content)
            else:
                with st.expander(heading_clean, expanded=False):
                    st.markdown(content)

        st.divider()
        st.download_button(
            "💾 Download Full Plan (.txt)",
            raw,
            file_name=f"{topic.strip().replace(' ', '_')}_learning_plan.txt",
            mime="text/plain",
        )