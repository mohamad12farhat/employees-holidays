import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

MAIL_SENDER   = os.environ['MAIL_SENDER']
MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
ADMIN_EMAIL   = os.environ['ADMIN_EMAIL']


def _send(to: str, subject: str, body: str) -> None:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = MAIL_SENDER
    msg['To']      = to
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls()
        server.login(MAIL_SENDER, MAIL_PASSWORD)
        server.sendmail(MAIL_SENDER, to, msg.as_string())


def notify_employee_status_change(
    employee_email: str,
    full_name: str,
    status: str,
    start_date: str,
    end_date: str,
    leave_days: int,
) -> None:
    color   = '#1e7d4f' if status == 'approved' else '#c0392b'
    label   = status.capitalize()
    subject = f'Your Leave Request has been {label}'
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
      <div style="background:#1e4d8c;padding:20px 24px;">
        <h2 style="color:white;margin:0;">Employee Holiday System</h2>
      </div>
      <div style="padding:28px 24px;">
        <p style="color:#333;">Hi <strong>{full_name}</strong>,</p>
        <p style="color:#333;">Your leave request has been
          <strong style="color:{color};">{label}</strong>.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f7f9fc;">
            <td style="padding:10px 14px;color:#555;font-size:13px;">Start Date</td>
            <td style="padding:10px 14px;color:#333;font-weight:600;">{start_date}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;color:#555;font-size:13px;">End Date</td>
            <td style="padding:10px 14px;color:#333;font-weight:600;">{end_date}</td>
          </tr>
          <tr style="background:#f7f9fc;">
            <td style="padding:10px 14px;color:#555;font-size:13px;">Working Days</td>
            <td style="padding:10px 14px;color:#333;font-weight:600;">{leave_days}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;color:#555;font-size:13px;">Status</td>
            <td style="padding:10px 14px;font-weight:600;color:{color};">{label}</td>
          </tr>
        </table>
        <p style="color:#888;font-size:12px;margin-top:24px;">
          &copy; 2026 Employee Holiday System
        </p>
      </div>
    </div>
    """
    _send(employee_email, subject, body)
