"""
The customer chat page, made with Streamlit.

Run it on your laptop with:  .venv/bin/streamlit run app.py
Settings (GOOGLE_API_KEY, GEMINI_MODEL, APP_PASSCODE, FAQ_SHEET_URL):
- on your laptop they come from the .env file
- online, they come from Streamlit's Secrets (Streamlit turns them into
  environment variables, so the same code works in both places)
"""

import asyncio
import hmac
import os
import uuid

import streamlit as st
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

# Read the .env file if it exists (on your laptop). Online there is none, which is fine.
load_dotenv()

# Imported after load_dotenv() because the agent needs GEMINI_MODEL when it loads.
from support_agent.agent import root_agent  # noqa: E402

APP_NAME = "support_agent"

st.set_page_config(page_title="DemoKart Support", page_icon="💬")
st.title("DemoKart Support")

# ---------- Step 1: the passcode ----------
passcode = os.environ.get("APP_PASSCODE", "")

if not st.session_state.get("unlocked"):
    if not passcode:
        # No passcode set: stay locked rather than open to everyone.
        st.error("This page is not set up yet (APP_PASSCODE is missing).")
        st.stop()
    typed = st.text_input("Enter the passcode to start chatting", type="password")
    if typed:
        if hmac.compare_digest(typed.encode(), passcode.encode()):
            st.session_state["unlocked"] = True
            st.rerun()
        else:
            st.error("Wrong passcode. Please try again.")
    st.stop()

# ---------- Step 2: one conversation per browser session ----------
if "runner" not in st.session_state:
    st.session_state["runner"] = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    st.session_state["user_id"] = str(uuid.uuid4())
    st.session_state["session_id"] = str(uuid.uuid4())
    st.session_state["messages"] = []  # the chat shown on screen
    # Create this visitor's conversation inside the runner.
    asyncio.run(
        st.session_state["runner"].session_service.create_session(
            app_name=APP_NAME,
            user_id=st.session_state["user_id"],
            session_id=st.session_state["session_id"],
        )
    )


async def ask_agent(text: str) -> str:
    """Send one message to the agent and return its reply."""
    message = types.Content(role="user", parts=[types.Part(text=text)])
    reply = ""
    async for event in st.session_state["runner"].run_async(
        user_id=st.session_state["user_id"],
        session_id=st.session_state["session_id"],
        new_message=message,
    ):
        # Only the agent's final answer is shown (not its tool calls).
        if event.is_final_response() and event.content and event.content.parts:
            reply += "".join(p.text or "" for p in event.content.parts)
    return reply


# ---------- Step 3: show the chat ----------
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])

if prompt := st.chat_input("Type your message"):
    st.session_state["messages"].append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Kavya is typing..."):
            try:
                answer = asyncio.run(ask_agent(prompt))
            except Exception:
                answer = "Sorry, something went wrong on our side. Please try again in a moment."
        st.markdown(answer or "Sorry, I could not answer that. Please try again.")
    st.session_state["messages"].append({"role": "assistant", "text": answer})
