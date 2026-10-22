import streamlit as st
import subprocess
import time
import os
import json
import sys


# ============================================================
# MUST BE FIRST STREAMLIT COMMAND
# ============================================================
st.set_page_config(
    page_title="AI-Powered Multi-Agent Helpdesk",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# CONSTANTS
# ============================================================
LOG_FILE = "output/logs/run.log"
FINAL_JSON = "output/final.json"
FINAL_MD = "output/final.md"
COORDINATOR_INPUT = "coordinator_input.txt"


# ============================================================
# START COORDINATOR ONLY ONCE
# ============================================================
@st.cache_resource
def start_coordinator():
    """
    Start coordinator backend once.
    Streamlit requirement: cannot run before set_page_config.
    """
    try:
        # output goes to output/logs/run.log; an unread PIPE would fill up
        # and block the coordinator
        proc = subprocess.Popen(
            [sys.executable, "coordinator/coordinator.py"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return proc
    except Exception as e:
        st.error(f"Failed to start coordinator: {e}")
        return None


# Start system
coordinator_process = start_coordinator()


# ============================================================
# UI – MAIN PAGE
# ============================================================
st.title("🤖 AI-Powered Multi-Agent Helpdesk")
st.markdown("Your multi-agent CrewAI + ADK + LangGraph workflow. ")


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ System Controls")

    if st.button("Restart Coordinator"):
        try:
            coordinator_process.kill()
        except:
            pass
        time.sleep(1)
        start_coordinator.clear()
        coordinator_process = start_coordinator()
        st.success("Coordinator restarted!")

    st.markdown("---")
    st.info("Coordinator runs in background. Logs & outputs refresh every 3 seconds.")


# ============================================================
# ISSUE INPUT
# ============================================================
st.subheader("📝 Submit a Support Ticket")

user_issue = st.text_area(
    "Describe the issue:",
    height=120,
    placeholder="Example: I am not able to login…"
)

if st.button("Submit Ticket", type="primary"):
    if not user_issue.strip():
        st.error("Please enter an issue!")
    else:
        with open(COORDINATOR_INPUT, "w", encoding="utf-8") as f:
            f.write(user_issue)
        st.success("Ticket sent to multi-agent system 🚀")
        st.toast("Agents are processing your ticket...")


# ============================================================
# LIVE LOG VIEWER
# ============================================================
def read_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "Log file not created yet."


@st.fragment(run_every=3)
def live_panels():
    st.subheader("🟢 Live System Logs")
    st.code(read_logs()[-20000:], language="bash")


    # ============================================================
    # FINAL OUTPUT – MARKDOWN
    # ============================================================
    st.subheader("📄 Final Output (Markdown)")

    output_md = st.empty()

    if os.path.exists(FINAL_MD):
        with open(FINAL_MD, "r", encoding="utf-8") as f:
            output_md.markdown(f.read())
    else:
        output_md.info("Final markdown output will appear here.")


    # ============================================================
    # FINAL OUTPUT – JSON
    # ============================================================
    st.subheader("📦 Final Output (JSON)")

    output_json = st.empty()

    if os.path.exists(FINAL_JSON):
        with open(FINAL_JSON, "r", encoding="utf-8") as f:
            output_json.json(json.load(f))
    else:
        output_json.info("Final JSON output will appear here.")


live_panels()
