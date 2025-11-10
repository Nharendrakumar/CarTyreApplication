import streamlit as st
from agent import get_agent_executor
from database import save_appointment, is_after_hours
import json
import os
import logging
import pandas as pd
import sqlite3

# Setup logging for debugging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load cached prices if available
CACHE_FILE = "price_cache.json"
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        price_cache = json.load(f)
else:
    price_cache = {}

# Streamlit app
st.title("XXX Tyres Chatbot")

# Sidebar for status and export
with st.sidebar:
    st.header("App Status")
    st.text("Ollama Model: llama3")
    if os.path.exists('app.log'):
        with open('app.log', 'r') as log_file:
            st.text_area("Recent Logs", log_file.read(), height=100)
    
    # Extra Feature: Export appointments to CSV
    st.header("Export Appointments")
    if st.button("Download CSV"):
        conn = sqlite3.connect("appointments.db")
        df = pd.read_sql_query("SELECT * FROM appointments", conn)
        conn.close()
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download appointments.csv",
            data=csv,
            file_name="appointments.csv",
            mime="text/csv"
        )

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Define fallback function
def simple_price_response(user_input):
    return "🛞 Estimated price for your tyre request is between $100 - $300 per tyre. Please visit our store or provide more details for accuracy."

# User input
if user_input := st.chat_input("Enter car details (e.g., Make: Toyota, Model: Camry, Year: 2023, Size: 19-inch, Zip: 90210)"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get agent response with fallback
    try:
        agent_executor = get_agent_executor()
        response = agent_executor.invoke({"input": user_input})["output"]
        logging.info(f"✅ Agent success: {user_input}")
    except Exception as e:
        # ✅ FALLBACK: Direct mock response (works instantly)
        response = simple_price_response(user_input)
        logging.warning(f"Agent failed, using fallback: {str(e)}")

    # Remove after-hours field temporarily for testing
    # if is_after_hours():
    #     response += "\n\n⏰ After hours - will call you tomorrow!"
    #     contact = st.text_input("Enter phone/email:", key="contact_input")
    #     if contact:
    #         zip_code = "90210"  # Default or parse from input
    #         time = "Tomorrow 10 AM"  # Placeholder
    #         save_appointment(contact, zip_code, time)
    #         response += "\n✅ Appointment scheduled!"
    #         logging.info("Appointment scheduled during after-hours")

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
