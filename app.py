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
# MULTI-GMAIL INPUT
# -----------------------------------
st.subheader("🔐 Gmail Accounts (Multi-Login Support)")

gmail_accounts_input = st.text_area(
    "Enter Gmail accounts (one per line)",
    placeholder="gmail1@gmail.com\ngmail2@gmail.com\ngmail3@gmail.com"
)

APP_PASSWORD = st.text_input("App Password (same for all accounts)", type="password")

# -----------------------------------
# EMAIL EDITOR
# -----------------------------------
subject = st.text_input("Email Subject")

st.write("✍️ Gmail Style Email Editor")

html_message = st_quill(
    placeholder="Write your email here...",
    html=True
)

file = st.file_uploader("Upload CSV (ONLY email column)", type=["csv"])

st.info("CSV format:\nemail\nabc@gmail.com\nxyz@yahoo.com")

# -----------------------------------
# SMTP CONNECT FUNCTION
# -----------------------------------
def connect_smtp(account):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(account, APP_PASSWORD)
    return server

# -----------------------------------
# START BUTTON
# -----------------------------------
if st.button("🚀 Start Sending Emails"):

    # VALIDATION
    if not gmail_accounts_input:
        st.error("Enter at least one Gmail account")
        st.stop()

    if not APP_PASSWORD:
        st.error("Enter App Password")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    if not subject or not html_message:
        st.error("Subject and email content required")
        st.stop()

    # -----------------------------------
    # PROCESS GMAIL ACCOUNTS
    # -----------------------------------
    accounts = [
        g.strip() for g in gmail_accounts_input.split("\n") if g.strip()
    ]

    if len(accounts) == 0:
        st.error("No valid Gmail accounts found")
        st.stop()

    account_index = 0

    # -----------------------------------
    # SAFE CSV READ
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

    # -----------------------------------
    # PROGRESS
    # -----------------------------------
    progress = st.progress(0)
    status = st.empty()

    server = None
    sent = 0

    # -----------------------------------
    # MAIN LOOP
    # -----------------------------------
    for i, email in enumerate(emails):

        current_account = accounts[account_index % len(accounts)]

        try:
            # reconnect if needed
            if server is None:
                server = connect_smtp(current_account)

            msg = MIMEMultipart()
            msg["From"] = current_account
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(MIMEText(html_message, "html"))

            server.sendmail(current_account, email, msg.as_string())

            st.success(f"Sent → {email} via {current_account}")
            sent += 1

        except Exception as e:
            st.warning(f"Reconnecting account → {current_account}")
            try:
                server = connect_smtp(current_account)
                continue
            except:
                st.error(f"Account failed: {current_account}")
                continue

        # update rotation
        account_index += 1

        progress.progress((i + 1) / len(emails))

        # 4–6 sec delay (your requirement)
        if i < len(emails) - 1:
            time.sleep(random.randint(4, 6))

    # -----------------------------------
    # SAFE CLOSE
    # -----------------------------------
    try:
        if server:
            server.quit()
    except:
        pass

    st.success(f"🎉 Done! Sent {sent}/{len(emails)} emails")
