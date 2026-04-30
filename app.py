import streamlit as st
import pandas as pd
import smtplib
import time
import random
import io

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(page_title="Bulletproof Email Sender", page_icon="📧")

st.title("📧 Bulletproof Gmail Sender v2")

# -----------------------------------
# LOGIN
# -----------------------------------
GMAIL = st.text_input("Gmail Address")
APP_PASSWORD = st.text_input("App Password", type="password")

# -----------------------------------
# EMAIL CONTENT
# -----------------------------------
subject = st.text_input("Subject")

message = st.text_area(
    "Email Message (HTML supported)",
    height=220,
    placeholder="Write your email..."
)

file = st.file_uploader("Upload CSV (ONLY email column)", type=["csv"])

st.info("CSV format: email column only")

# -----------------------------------
# SAFE SMTP CONNECT FUNCTION
# -----------------------------------
def connect_smtp():
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()
        server.login(GMAIL, APP_PASSWORD)
        return server
    except Exception as e:
        st.error(f"SMTP connection failed: {e}")
        return None

# -----------------------------------
# START SENDING
# -----------------------------------
if st.button("🚀 Start Sending"):

    if not GMAIL or not APP_PASSWORD:
        st.error("Enter Gmail credentials")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    # -------------------------------
    # SAFE CSV LOAD
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

    progress = st.progress(0)

    sent = 0
    failed = 0

    server = connect_smtp()

    # -----------------------------------
    # SEND LOOP (BULLETPROOF)
    # -----------------------------------
    for i, email in enumerate(emails):

        if not server:
            st.warning("Reconnecting SMTP...")
            server = connect_smtp()
            if not server:
                st.error("Failed to reconnect SMTP. Stopping.")
                break

        try:
            msg = MIMEMultipart()
            msg["From"] = GMAIL
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(MIMEText(message, "html"))

            server.sendmail(GMAIL, email, msg.as_string())

            st.success(f"Sent → {email}")
            sent += 1

        except Exception as e:
            st.error(f"Failed → {email}")
            failed += 1

            # try reconnect once if failure happens
            try:
                server.quit()
            except:
                pass

            server = connect_smtp()

        progress.progress((i + 1) / len(emails))

        # safe delay
        if i < len(emails) - 1:
            time.sleep(random.randint(4, 6))

    # -----------------------------------
    # SAFE CLEANUP (NO CRASH)
    # -----------------------------------
    try:
        if server:
            server.quit()
    except:
        pass

    st.success(f"""
    🎉 Completed!

    ✅ Sent: {sent}  
    ❌ Failed: {failed}  
    """)
