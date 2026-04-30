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
# UI
# -----------------------------------
st.set_page_config(page_title="Bulletproof Gmail Sender", page_icon="📧")
st.title("📧 Gmail Bulk Sender (DAD)")

# -----------------------------------
# LOGIN
# -----------------------------------
GMAIL = st.text_input("Gmail Address")
APP_PASSWORD = st.text_input("App Password", type="password")

subject = st.text_input("Subject")

st.write("✍️ Email Content (Gmail-style editor)")
html_message = st_quill(placeholder="Write email here...", html=True)

file = st.file_uploader("Upload CSV (ONLY email column)", type=["csv"])

# -----------------------------------
# RESUME STATE
# -----------------------------------
if "last_index" not in st.session_state:
    st.session_state.last_index = 0

# -----------------------------------
# SAFE SMTP CONNECT FUNCTION
# -----------------------------------
def connect_smtp():
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(GMAIL, APP_PASSWORD)
    return server

# -----------------------------------
# START BUTTON
# -----------------------------------
if st.button("🚀 Start Sending"):

    if not GMAIL or not APP_PASSWORD:
        st.error("Enter Gmail and App Password")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    # -----------------------------------
    # READ CSV SAFE
    # -----------------------------------
    content = file.getvalue().decode("utf-8", errors="ignore")
    df = pd.read_csv(io.StringIO(content))

    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    df.columns = df.columns.str.strip().str.lower()

    if len(df.columns) != 1 or df.columns[0] != "email":
        st.error("CSV must contain ONLY email column")
        st.stop()

    emails = df["email"].dropna().astype(str).str.strip().tolist()

    total = len(emails)
    st.success(f"Total Emails: {total}")

    progress = st.progress(0)
    status = st.empty()

    server = None
    sent = 0

    i = st.session_state.last_index

    # -----------------------------------
    # MAIN LOOP (RESUME SUPPORT)
    # -----------------------------------
    while i < total:

        email = emails[i]

        try:
            # reconnect if needed
            if server is None:
                server = connect_smtp()

            msg = MIMEMultipart()
            msg["From"] = GMAIL
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(MIMEText(html_message, "html"))

            server.sendmail(GMAIL, email, msg.as_string())

            st.success(f"Sent → {email}")
            sent += 1

        except Exception as e:
            st.warning(f"Reconnecting... {email}")
            try:
                server = connect_smtp()
                continue
            except:
                st.error("SMTP reconnect failed")
                break

        # update resume index
        st.session_state.last_index = i + 1

        progress.progress((i + 1) / total)

        # 4–6 sec delay (your request)
        if i < total - 1:
            time.sleep(random.randint(4, 6))

        i += 1

    # -----------------------------------
    # SAFE CLOSE
    # -----------------------------------
    try:
        if server:
            server.quit()
    except:
        pass

    st.success(f"🎉 Done! Sent {sent} emails")

    # reset resume
    st.session_state.last_index = 0
