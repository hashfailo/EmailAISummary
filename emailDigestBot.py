from email.header import decode_header
import os
import email
import imaplib
from itertools import chain
import base64
import re
import time
from dotenv import load_dotenv
import random
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta, timezone
import email.utils
import smtplib
from email.mime.text import MIMEText

def is_recent_email(msg):
    raw_date = msg["Date"]
    parsed_date = email.utils.parsedate_to_datetime(raw_date)

    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
    else:
        parsed_date = parsed_date.astimezone(timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - parsed_date

    print(f"[DEBUG] Email Date: {parsed_date} | Now: {now} | Age (seconds): {diff.total_seconds()}")

    return diff < timedelta(days=1)

def extract_body(msg):
    email_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                email_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                break

        if not email_body:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    soup = BeautifulSoup(html_body, "html.parser")
                    email_body = soup.get_text()
                    break
    else:
        email_body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
    return email_body

def summarize_text(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {os.getenv('HG_TOKEN')}"}

    # Trim input to avoid token limit issues
    trimmed_text = " ".join(text.split()[:500])

    response = requests.post(API_URL, headers=headers, json={"inputs": trimmed_text})
    
    if response.status_code == 200:
        return response.json()[0]["summary_text"]
    else:
        return f"Error: {response.status_code}, {response.text}"
def decode_subject(subject):
    decoded_parts = decode_header(subject)
    return ''.join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in decoded_parts
    )

def format_digest(summarized_emails):
    digest = "🗞️ *Your Email Digest for the Past 24 Hours*\n\n"
    for email in summarized_emails:
        digest += f"From: {email['from']}\n"
        digest += f"Subject: {email['subject']}\n"
        digest += f"Summary: {email['summary']}\n"
        digest += "-"*50 + "\n"
    return digest


def send_email(recipient, subject, body):
    sender_email = EMAIL_USERNAME
    password = EMAIL_PASSWORD

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = subject

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, msg.as_string())

def main():
    load_dotenv()

    imap_ssl_host = "imap.gmail.com"
    imap_port = 993
    global EMAIL_USERNAME
    global EMAIL_PASSWORD
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    mail = imaplib.IMAP4_SSL(imap_ssl_host)
    mail.login(EMAIL_USERNAME, EMAIL_PASSWORD)

    mail.select("inbox")
    print("--Connected to inbox")
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()[-100:]  # Limit to last 100 unread emails

    summarized_emails = []
    print("--getting last 24 hours emails")
    max_check = 100
    recent_ids = list(reversed(email_ids))  # Already sliced above

    stop_checking = False
    for idx, email_id in enumerate(recent_ids, start=1):
        if stop_checking:
            break
        print(f"Processing email {idx} of {len(email_ids)}...")
        _, msg_data = mail.fetch(email_id, "(RFC822)")
        # Get the raw email bytes from the msg_data
        raw_email = next((part[1] for part in msg_data if isinstance(part, tuple)), None)

        if raw_email is None:
            continue

        msg = email.message_from_bytes(raw_email)
        print(f"[DEBUG] Processing email subject: {msg['Subject']} | From: {msg['From']}")

        if not is_recent_email(msg):
            stop_checking = True
            break

        subject = decode_subject(msg["Subject"] or "(No Subject)")
        sender = msg["From"] or "(Unknown)"
        email_body = extract_body(msg)

        if not email_body.strip():
            continue  # Skip empty bodies

        summary = summarize_text(email_body)

        summarized_emails.append({
            "subject": subject,
            "from": sender,
            "summary": summary
        })

    if summarized_emails:
        print("--formatting email")
        digest_body = format_digest(summarized_emails)
        print("--sending email")
        send_email("rhinosheshu@gmail.com", "📰 Your Daily Email Digest", digest_body)
        print("--email sent successfully")
    else:
        print("--No recent emails to summarize.")

if __name__ == "__main__":
    main()