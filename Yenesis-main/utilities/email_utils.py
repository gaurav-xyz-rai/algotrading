# === utils/email_helper.py ===
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from config import EMAIL_PASSWORD

def send_email(subject, body, to_email, from_email, chart_path=None, attachments=None):
    """
    Send an email with optional inline chart and file attachments.

    Parameters:
        - subject (str): Email subject
        - body (str): Plain text email body
        - to_email (list[str]): List of recipient email addresses
        - from_email (str): Sender's email address
        - chart_path (str, optional): Path to image to embed in email
        - attachments (list[str], optional): List of file paths to attach
    """
    if isinstance(to_email, str):
        to_email = [to_email]

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ", ".join(to_email)

    msg.attach(MIMEText(body, 'plain'))

    # Attach inline chart if provided
    if chart_path:
        with open(chart_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<chart>')
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(chart_path))
            msg.attach(img)

    # Attach additional files
    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
            except Exception as e:
                print(f"Failed to attach {file_path}: {e}")

    # Send the email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(from_email, EMAIL_PASSWORD)
        server.send_message(msg)
