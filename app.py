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

st.title("📧 Gmail Bulk Sender (Login Mode)")

# -----------------------------------
# LOGIN INPUTS (NEW)
# -----------------------------------
st.subheader("🔐 Login")

GMAIL = st.text_input("Enter Gmail Address")

APP_PASSWORD = st.text_input(
    "Enter Gmail App Password",
    type="password"
)

# -----------------------------------
# EMAIL EDITOR
# -----------------------------------
subject = st.text_input("Email Subject")

st.write("✍️ Write Email (Gmail-style editor)")

html_message = st_quill(
    placeholder="Write your email here...",
    html=True
)

# -----------------------------------
# CSV UPLOAD
# -----------------------------------
file = st.file_uploader("Upload CSV (ONLY email column)", type=["csv"])

st.info("CSV format:\nemail\nabc@gmail.com")

# -----------------------------------
# START BUTTON
# -----------------------------------
if st.button("🚀 Send Emails"):

    # VALIDATION
    if not GMAIL or not APP_PASSWORD:
        st.error("Please enter Gmail and App Password")
        st.stop()

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    if not subject or not html_message:
        st.error("Subject and email content required")
        st.stop()

    # -----------------------------------
    # READ CSV SAFELY
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
    # SMTP CONNECTION
    # -----------------------------------
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL, APP_PASSWORD)
    except:
        st.error("Login failed. Check Gmail or App Password.")
        st.stop()

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

        # 4-5 sec delay
        if i < len(emails) - 1:
            time.sleep(random.randint(4, 5))

    server.quit()

    st.success(f"🎉 Done! Sent {sent}/{len(emails)} emails")
