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
# TITLE (UPDATED AS REQUESTED)
# -----------------------------------
st.set_page_config(page_title="Gmail Bulk Sender", page_icon="📧")
st.title("📧 Gmail Bulk Sender (DAD)")

# -----------------------------------
# MULTI GMAIL ACCOUNTS (USER SELECT)
# -----------------------------------
st.subheader("🔐 Select Gmail Account")

accounts = {
    "Account 1": "",
    "Account 2": "",
    "Account 3": ""
}

selected_account = st.selectbox("Choose Gmail Account", list(accounts.keys()))

# User inputs credentials for selected account
GMAIL = st.text_input(f"Gmail for {selected_account}")
APP_PASSWORD = st.text_input(f"App Password for {selected_account}", type="password")

# -----------------------------------
# EMAIL INPUTS
# -----------------------------------
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
# SMTP CONNECT
# -----------------------------------
def connect_smtp():
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(GMAIL, APP_PASSWORD)
    return server

# -----------------------------------
# START SENDING
# -----------------------------------
if st.button("🚀 Start Sending"):

    if not GMAIL or not APP_PASSWORD:
        st.error("Please enter Gmail and App Password")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    if not subject or not html_message:
        st.error("Fill subject and email content")
        st.stop()

    # -----------------------------------
    # SAFE CSV LOAD
    # -----------------------------------
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

    server = None
    sent = 0

    i = st.session_state.last_index

    # -----------------------------------
    # SEND LOOP (RESUME + MULTI ACCOUNT SAFE)
    # -----------------------------------
    while i < len(emails):

        email = emails[i]

        try:
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

        except Exception:
            st.warning(f"Reconnecting SMTP for → {email}")
            try:
                server = connect_smtp()
                continue
            except:
                st.error("SMTP reconnect failed")
                break

        # update resume
        st.session_state.last_index = i + 1

        progress.progress((i + 1) / len(emails))

        # 4–6 sec delay (as requested earlier)
        if i < len(emails) - 1:
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
