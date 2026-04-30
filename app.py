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
st.set_page_config(page_title="Gmail Bulk Sender", page_icon="📧")

st.title("📧 Gmail Bulk Sender (DAD)")

# -----------------------------------
# MULTI GMAIL INPUT (NEW FEATURE)
# -----------------------------------
st.subheader("🔐 Gmail Accounts (Multi Login Support)")

gmail_input = st.text_area(
    "Enter Gmail Accounts (one per line)",
    placeholder="example1@gmail.com\nexample2@gmail.com"
)

password = st.text_input("App Password (same for all accounts)", type="password")

# -----------------------------------
# EMAIL EDITOR
# -----------------------------------
subject = st.text_input("Subject")

st.write("✍️ Email Content")
html_message = st_quill(placeholder="Write email here...", html=True)

file = st.file_uploader("Upload CSV (ONLY email column)", type=["csv"])

# -----------------------------------
# RESUME SUPPORT
# -----------------------------------
if "last_index" not in st.session_state:
    st.session_state.last_index = 0

if "gmail_index" not in st.session_state:
    st.session_state.gmail_index = 0

# -----------------------------------
# SMTP CONNECT
# -----------------------------------
def connect_smtp(gmail, password):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(gmail, password)
    return server

# -----------------------------------
# START BUTTON
# -----------------------------------
if st.button("🚀 Start Sending"):

    # -------------------------
    # VALIDATION
    # -------------------------
    if not gmail_input or not password:
        st.error("Enter Gmail accounts and password")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    gmail_list = [g.strip() for g in gmail_input.split("\n") if g.strip()]

    if len(gmail_list) == 0:
        st.error("Add at least one Gmail account")
        st.stop()

    # -------------------------
    # READ CSV SAFE
    # -------------------------
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
    st.info(f"Using {len(gmail_list)} Gmail accounts (rotation enabled)")

    progress = st.progress(0)

    server = None
    sent = 0

    i = st.session_state.last_index

    # -----------------------------------
    # SEND LOOP
    # -----------------------------------
    while i < total:

        email = emails[i]

        # rotate Gmail accounts
        gmail = gmail_list[st.session_state.gmail_index]

        try:
            if server is None:
                server = connect_smtp(gmail, password)

            msg = MIMEMultipart()
            msg["From"] = gmail
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(MIMEText(html_message, "html"))

            server.sendmail(gmail, email, msg.as_string())

            st.success(f"Sent → {email} (via {gmail})")
            sent += 1

        except Exception:
            st.warning("Reconnecting SMTP...")

            try:
                server = connect_smtp(gmail, password)
                continue
            except:
                st.error("SMTP reconnect failed")
                break

        # update resume
        st.session_state.last_index = i + 1

        # rotate gmail account
        st.session_state.gmail_index = (
            st.session_state.gmail_index + 1
        ) % len(gmail_list)

        progress.progress((i + 1) / total)

        # 4–6 sec delay
        if i < total - 1:
            time.sleep(random.randint(4, 6))

        i += 1

    # -----------------------------------
    # CLOSE SMTP SAFELY
    # -----------------------------------
    try:
        if server:
            server.quit()
    except:
        pass

    st.success(f"🎉 Done! Sent {sent}/{total} emails")

    # reset resume
    st.session_state.last_index = 0
    st.session_state.gmail_index = 0
