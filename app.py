import streamlit as st
import pandas as pd
import smtplib
import time
import random
import io

from streamlit_quill import st_quill
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(page_title="Gmail Sender", page_icon="📧")

# -----------------------------------
# RESET SYSTEM (FIXED PROPERLY)
# -----------------------------------
if "reset" not in st.session_state:
    st.session_state.reset = False

def reset_app():
    st.session_state.reset = True

if st.session_state.reset:
    st.session_state.clear()
    st.session_state.reset = False
    st.rerun()

# -----------------------------------
# HEADER
# -----------------------------------
col1, col2 = st.columns([4, 1])

with col1:
    st.title("📧 Gmail Bulk Sender")

with col2:
    st.button("🔄 Reset App", on_click=reset_app)

# -----------------------------------
# LOGIN
# -----------------------------------
st.subheader("🔐 Login")

gmail = st.text_input("Gmail Address", key="gmail")
password = st.text_input("App Password", type="password", key="password")

# -----------------------------------
# EMAIL EDITOR
# -----------------------------------
subject = st.text_input("Subject", key="subject")

st.write("✍️ Write Email")

message = st_quill(
    html=True,
    key="editor"
)

# -----------------------------------
# FILE UPLOAD
# -----------------------------------
file = st.file_uploader("Upload CSV (email column only)", type=["csv"], key="file")

st.info("CSV format:\nemail\nabc@gmail.com")

# -----------------------------------
# SEND BUTTON
# -----------------------------------
if st.button("🚀 Send Emails"):

    if not gmail or not password:
        st.error("Enter Gmail credentials")
        st.stop()

    if file is None:
        st.error("Upload CSV")
        st.stop()

    # READ CSV SAFELY
    content = file.getvalue().decode("utf-8", errors="ignore")
    df = pd.read_csv(io.StringIO(content))

    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    df.columns = df.columns.str.strip().str.lower()

    if len(df.columns) != 1 or df.columns[0] != "email":
        st.error("CSV must contain ONLY email column")
        st.stop()

    emails = df["email"].dropna().astype(str).tolist()

    st.success(f"Total Emails: {len(emails)}")

    # SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(gmail, password)

    progress = st.progress(0)
    sent = 0

    for i, email in enumerate(emails):

        msg = MIMEMultipart()
        msg["From"] = gmail
        msg["To"] = email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "html"))

        try:
            server.sendmail(gmail, email, msg.as_string())
            st.success(f"Sent → {email}")
            sent += 1
        except:
            st.error(f"Failed → {email}")

        progress.progress((i + 1) / len(emails))

        if i < len(emails) - 1:
            time.sleep(random.randint(2, 3))

    server.quit()

    st.success(f"🎉 Done! Sent {sent}/{len(emails)} emails")

    # IMPORTANT: AUTO RESET BUTTON
    st.button("🔄 Start New Campaign", on_click=reset_app)
