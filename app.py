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
# TITLE (UPDATED AS YOU REQUESTED)
# -----------------------------------
st.set_page_config(page_title="Gmail Bulk Sender", page_icon="📧")
st.title("📧 Gmail Bulk Sender (DAD)")

# -----------------------------------
# SESSION STATE FOR MULTI GMAILS
# -----------------------------------
if "gmail_accounts" not in st.session_state:
    st.session_state.gmail_accounts = []

# -----------------------------------
# ADD GMAIL ACCOUNT UI
# -----------------------------------
st.subheader("➕ Add Gmail Account")

new_gmail = st.text_input("Gmail Address (Add New)")
new_pass = st.text_input("App Password", type="password")

if st.button("➕ Add Gmail"):
    if new_gmail and new_pass:
        st.session_state.gmail_accounts.append({
            "gmail": new_gmail,
            "password": new_pass
        })
        st.success("Gmail Added!")
    else:
        st.warning("Please enter Gmail and Password")

# -----------------------------------
# SELECT GMAIL MANUALLY
# -----------------------------------
st.subheader("📂 Select Gmail Account")

if len(st.session_state.gmail_accounts) == 0:
    st.info("No Gmail accounts added yet.")
    selected_account = None
else:
    options = [acc["gmail"] for acc in st.session_state.gmail_accounts]
    selected_gmail = st.selectbox("Choose Gmail", options)

    selected_account = next(
        (acc for acc in st.session_state.gmail_accounts if acc["gmail"] == selected_gmail),
        None
    )

# -----------------------------------
# EMAIL EDITOR
# -----------------------------------
subject = st.text_input("Subject")

st.write("✍️ Email Content (Gmail-style editor)")
html_message = st_quill(placeholder="Write email here...", html=True)

file = st.file_uploader("Upload CSV (ONLY email column)", type=["csv"])

st.info("CSV format:\nemail\nabc@gmail.com")

# -----------------------------------
# SEND FUNCTION
# -----------------------------------
def connect_smtp(gmail, password):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(gmail, password)
    return server

# -----------------------------------
# SEND BUTTON
# -----------------------------------
if st.button("🚀 Start Sending"):

    if selected_account is None:
        st.error("Please add and select a Gmail account")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    gmail = selected_account["gmail"]
    password = selected_account["password"]

    # -----------------------------------
    # SAFE CSV LOAD
    # -----------------------------------
    content = file.getvalue().decode("utf-8", errors="ignore")
    df = pd.read_csv(io.StringIO(content))

    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    df.columns = df.columns.str.strip().str.lower()

    if len(df.columns) != 1 or df.columns[0] != "email":
        st.error("CSV must contain ONLY email column")
        st.stop()

    emails = df["email"].dropna().astype(str).str.strip().tolist()

    st.success(f"Total Emails: {len(emails)}")

    progress = st.progress(0)
    status = st.empty()

    server = None
    sent = 0

    # -----------------------------------
    # SEND LOOP
    # -----------------------------------
    for i, email in enumerate(emails):

        try:
            if server is None:
                server = connect_smtp(gmail, password)

            msg = MIMEMultipart()
            msg["From"] = gmail
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(MIMEText(html_message, "html"))

            server.sendmail(gmail, email, msg.as_string())

            st.success(f"Sent → {email}")
            sent += 1

        except Exception:
            st.warning(f"Reconnecting... {email}")
            try:
                server = connect_smtp(gmail, password)
                continue
            except:
                st.error("SMTP failed")
                break

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
