import streamlit as st
from ollama_client import get_ollama_client
from ui import chat_tab, planner_tab, progress_tab, quiz_tab, notes_tab

def main():
    st.set_page_config(page_title="Course Compass", layout="wide")
    st.title("Course Compass")
    st.caption("Your Personal Study & Skills Assistant")
    st.markdown("---")

    try:
        _ = get_ollama_client()
    except Exception as e:
        st.error(f"Ollama client initialization error: {e}")
        st.stop()

    tab_names = ["Chat", "Study Planner", "Progress Chart", "Quiz Generator", "Note Taker"]
    tabs = st.tabs(tab_names)

    # IMPORTANT: keep each tab isolated in its own fragment
    with tabs[0]:
        chat_tab()

    with tabs[1]:
        planner_tab()

    with tabs[2]:
        progress_tab()

    with tabs[3]:
        quiz_tab()

    with tabs[4]:
        notes_tab()

if __name__ == "__main__":
    main()