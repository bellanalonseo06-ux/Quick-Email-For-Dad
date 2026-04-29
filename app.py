import streamlit as st
import pandas as pd
import smtplib
import time
import random
import os
import io

from streamlit_quill import st_quill
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------------
# SECRETS
# -----------------------------------
GMAIL = st.secrets["GMAIL_EMAIL"]
APP_PASSWORD = st.secrets["GMAIL_PASS"]

# -----------------------------------
# UI
# -----------------------------------
st.set_page_config(page_title="Gmail Style Sender", page_icon="📧")

st.title("📧 Gmail-Style Bulk Email Sender")

subject = st.text_input("Email Subject")

st.write("✍️ Write your email (Gmail-style editor below)")

# -----------------------------------
# RICH TEXT EDITOR (GMAIL STYLE)
# -----------------------------------
html_message = st_quill(
    placeholder="Write your email here...",
    html=True
)

file = st.file_uploader("Upload CSV (ONLY email column)", type=["csv"])

st.info("CSV format:\nemail\nabc@gmail.com")

# -----------------------------------
# SEND EMAILS
# -----------------------------------
if st.button("🚀 Send Emails"):

    if file is None:
        st.error("Upload CSV first")
        st.stop()

    if not subject:
        st.error("Enter subject")
        st.stop()

    if not html_message:
        st.error("Write email content")
        st.stop()

    # -------------------------------
    # SAFE CSV LOADING
    # -------------------------------
    content = file.getvalue().decode("utf-8", errors="ignore")
    df = pd.read_csv(io.StringIO(content))

    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    df.columns = df.columns.str.strip().str.lower()

    if len(df.columns) != 1 or df.columns[0] != "email":
        st.error("CSV must contain ONLY one column: email")
        st.stop()

    emails = df["email"].dropna().astype(str).str.strip().tolist()

    st.success(f"Total Emails: {len(emails)}")

    # SMTP setup
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

        # HTML email body (Gmail-style)
        msg.attach(MIMEText(html_message, "html"))

        try:
            server.sendmail(GMAIL, email, msg.as_string())
            st.success(f"Sent → {email}")
            sent += 1
        except:
            st.error(f"Failed → {email}")

        progress.progress((i + 1) / len(emails))

        # 20–30 sec delay
        if i < len(emails) - 1:
            time.sleep(random.randint(8, 10))

    server.quit()

    st.success(f"🎉 Done! Sent {sent}/{len(emails)} emails")
