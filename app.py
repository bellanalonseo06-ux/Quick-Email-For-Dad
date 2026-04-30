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
st.set_page_config(page_title="Gmail Bulk Sender", page_icon="📧")

# -----------------------------------
# SAFE RESET FUNCTION (FIXED)
# -----------------------------------
def reset_app():
    keys_to_clear = [
        "gmail",
        "password",
        "subject",
        "editor",
        "file_uploaded"
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

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

GMAIL = st.text_input("Gmail Address", key="gmail")

APP_PASSWORD = st.text_input(
    "App Password",
    type="password",
    key="password"
)

# -----------------------------------
# EMAIL CONTENT
# -----------------------------------
subject = st.text_input("Email Subject", key="subject")

st.write("✍️ Write Email (Gmail-style editor)")

html_message = st_quill(
    placeholder="Write your email here...",
    html=True,
    key="editor"
)

# -----------------------------------
# FILE UPLOAD
# -----------------------------------
file = st.file_uploader(
    "Upload CSV (ONLY email column)",
    type=["csv"],
    key="file_uploaded"
)

st.info("CSV format:\nemail\nabc@gmail.com")

# -----------------------------------
# SEND BUTTON
# -----------------------------------
if st.button("🚀 Send Emails"):

    if not GMAIL or not APP_PASSWORD:
        st.error("Enter Gmail and App Password")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    if not subject or not html_message:
        st.error("Subject and message required")
        st.stop()

    try:
        # -----------------------------------
        # SAFE CSV READ
        # -----------------------------------
        content = file.getvalue().decode("utf-8", errors="ignore")
        df = pd.read_csv(io.StringIO(content))

        df = df.loc[:, ~df.columns.str.contains("Unnamed")]
        df.columns = df.columns.str.strip().str.lower()

        if len(df.columns) != 1 or df.columns[0] != "email":
            st.error("CSV must contain ONLY column: email")
            st.stop()

        emails = df["email"].dropna().astype(str).str.strip().tolist()

        st.success(f"Total Emails: {len(emails)}")

        # -----------------------------------
        # SMTP
        # -----------------------------------
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL, APP_PASSWORD)

        progress = st.progress(0)
        sent = 0

        # -----------------------------------
        # SEND LOOP
        # -----------------------------------
        for i, email in enumerate(emails):

            msg = MIMEMultipart()
            msg["From"] = GMAIL
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(MIMEText(html_message, "html"))

            try:
                server.sendmail(GMAIL, email, msg.as_string())
                st.success(f"Sent → {email}")
                sent += 1
            except:
                st.error(f"Failed → {email}")

            progress.progress((i + 1) / len(emails))

            if i < len(emails) - 1:
                time.sleep(random.randint(2, 3))

        server.quit()

        st.success(f"🎉 Done! Sent {sent}/{len(emails)} emails")

        # Optional reset button after completion
        st.button("🔄 Start New Campaign", on_click=reset_app)

    except Exception as e:
        st.error(f"Error: {str(e)}")
