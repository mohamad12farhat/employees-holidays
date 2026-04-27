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


def notify_employee_deactivated(
    employee_email: str,
    full_name: str,
    reason: str,
) -> None:
    subject = 'Your account has been deactivated'
    reason_row = f"""
          <tr>
            <td style="padding:10px 14px;color:#555;font-size:13px;">Reason</td>
            <td style="padding:10px 14px;color:#333;">{reason}</td>
          </tr>
    """ if reason else ''
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
      <div style="background:#1e4d8c;padding:20px 24px;">
        <h2 style="color:white;margin:0;">Employee Holiday System</h2>
      </div>
      <div style="padding:28px 24px;">
        <p style="color:#333;">Hi <strong>{full_name}</strong>,</p>
        <p style="color:#333;">Your account has been
          <strong style="color:#c0392b;">deactivated</strong> by the admin.
          You will not be able to log in until your account is reactivated.
        </p>
        {f'<table style="width:100%;border-collapse:collapse;margin:20px 0;">{reason_row}</table>' if reason else ''}
        <p style="color:#555;font-size:13px;margin-top:16px;">
          If you believe this is a mistake, please contact your administrator.
        </p>
        <p style="color:#888;font-size:12px;margin-top:24px;">
          &copy; 2026 Employee Holiday System
        </p>
      </div>
    </div>
    """
    _send(employee_email, subject, body)


def notify_employee_reactivated(
    employee_email: str,
    full_name: str,
) -> None:
    subject = 'Your account has been reactivated'
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
      <div style="background:#1e4d8c;padding:20px 24px;">
        <h2 style="color:white;margin:0;">Employee Holiday System</h2>
      </div>
      <div style="padding:28px 24px;">
        <p style="color:#333;">Hi <strong>{full_name}</strong>,</p>
        <p style="color:#333;">Your account has been
          <strong style="color:#1e7d4f;">reactivated</strong> by the admin.
          You can now log in as normal.
        </p>
        <p style="color:#888;font-size:12px;margin-top:24px;">
          &copy; 2026 Employee Holiday System
        </p>
      </div>
    </div>
    """
    _send(employee_email, subject, body)


def notify_admin_new_request(
    full_name: str,
    employee_email: str,
    start_date: str,
    end_date: str,
    leave_days: int,
    reason: str,
) -> None:
    subject = f'New Leave Request from {full_name}'
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
      <div style="background:#1e4d8c;padding:20px 24px;">
        <h2 style="color:white;margin:0;">Employee Holiday System</h2>
      </div>
      <div style="padding:28px 24px;">
        <p style="color:#333;">A new leave request has been submitted and is awaiting your review.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f7f9fc;">
            <td style="padding:10px 14px;color:#555;font-size:13px;">Employee</td>
            <td style="padding:10px 14px;color:#333;font-weight:600;">{full_name}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;color:#555;font-size:13px;">Email</td>
            <td style="padding:10px 14px;color:#333;font-weight:600;">{employee_email}</td>
          </tr>
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
            <td style="padding:10px 14px;color:#555;font-size:13px;">Reason</td>
            <td style="padding:10px 14px;color:#333;">{reason or '—'}</td>
          </tr>
        </table>
        <p style="color:#888;font-size:12px;margin-top:24px;">
          &copy; 2026 Employee Holiday System
        </p>
      </div>
    </div>
    """
    _send(ADMIN_EMAIL, subject, body)
