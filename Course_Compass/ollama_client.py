from typing import List, Dict
import streamlit as st
from ollama import Client

# phi3:3.8b-instruct
OLLAMA_MODEL = "coursecompass"

@st.cache_resource(show_spinner=False)
def get_ollama_client() -> Client:
    return Client()

def query_llm(messages: List[Dict], max_tokens: int = 1024, just_schedule: bool = False) -> str:
    client = get_ollama_client()
    try:
        resp = client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            stream=False,
            options={"num_predict": max_tokens, "temperature": 0.2},
        )
    except Exception as e:
        return f"(Model error: {e})"

    # Correct Ollama response format
    try:
        text = resp["choices"][0]["message"]["content"]
    except:
        text = resp.get("text") or resp.get("message", {}).get("content") or ""

    text = text.strip()

    if just_schedule:
        return text

    return text

def stream_chat_and_collect(messages, placeholder, max_tokens=1024):
    client = get_ollama_client()

    stream = client.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        stream=True,
        options={"num_predict": max_tokens, "temperature": 0.2},
    )

    final_text = ""
    visible_text = ""
    inside_think = False
    think_header_shown = False

    for chunk in stream:
        msg = chunk.get("message", {})
        token = msg.get("content", "")

        final_text += token

        # Detect think start
        if "<think>" in token:
            inside_think = True

            # Insert "Thinking..." header once
            if not think_header_shown:
                visible_text += (
                    "<div style='color:#9ca3af; font-style:italic;'>"
                    "🤔 <i>Thinking…</i>"
                    "</div>"
                )
                think_header_shown = True

            # fade the opening <think>
            token = token.replace("<think>", "<span style='color:#9ca3af; font-style:italic;'>")

        # Detect think end
        if "</think>" in token:
            inside_think = False
            # fade closing tag
            token = token.replace("</think>", "</span>")

        # If still inside a think block, fade + italicize
        if inside_think:
            token = f"<span style='color:#9ca3af; font-style:italic;'>{token}</span>"

        visible_text += token

        # Render while streaming
        placeholder.markdown(visible_text, unsafe_allow_html=True)

    return final_text.strip()