from utils.timezone import to_myt
import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config.settings import SMTP_EMAIL, SMTP_PASSWORD

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def send_reminder_email(
    to_email: str,
    task_title: str,
    start_time: datetime,
    description: str | None = None,
    location: str | None = None,
) -> bool:
    """
    Send a styled HTML reminder email for an upcoming task.
    Returns True on success, False on failure.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — skipping email reminder.")
        return False

    # Format the time for display (MYT, UTC+8)
    if hasattr(start_time, "strftime"):
        # MongoDB stores naive UTC — mark as UTC first, then convert to MYT
        from zoneinfo import ZoneInfo
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=ZoneInfo("UTC"))
        start_time = start_time.astimezone(ZoneInfo("Asia/Kuala_Lumpur"))
        time_display = start_time.strftime("%I:%M %p")
        date_display = start_time.strftime("%A, %B %d, %Y")
    else:
        time_display = str(start_time)
        date_display = ""

    subject = f"⏰ Reminder: {task_title} starts soon!"

    # Build HTML body
    desc_block = ""
    if description:
        desc_block = f"""
        <tr>
          <td style="padding:8px 0 0;color:#94a3b8;font-size:13px;">
            <strong style="color:#e2e8f0;">Notes:</strong> {description}
          </td>
        </tr>
        """

    location_block = ""
    if location:
        location_block = f"""
        <tr>
          <td style="padding:4px 0 0;color:#94a3b8;font-size:13px;">
            <strong style="color:#e2e8f0;">📍 Location:</strong> {location}
          </td>
        </tr>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#0f1117;font-family:'Segoe UI',Roboto,Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1117;padding:32px 16px;">
        <tr>
          <td align="center">
            <table width="520" cellpadding="0" cellspacing="0" style="background:#1a1d27;border-radius:16px;border:1px solid #2a2d3a;overflow:hidden;">
              <!-- Header -->
              <tr>
                <td style="background:linear-gradient(135deg,#06b6d4,#8b5cf6);padding:28px 32px;">
                  <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:700;">⏰ Upcoming Task Reminder</h1>
                  <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">Your task is starting in ~10 minutes</p>
                </td>
              </tr>
              <!-- Body -->
              <tr>
                <td style="padding:28px 32px;">
                  <h2 style="margin:0 0 16px;color:#f1f5f9;font-size:22px;font-weight:700;">{task_title}</h2>
                  <table cellpadding="0" cellspacing="0" style="width:100%;">
                    <tr>
                      <td style="padding:0;color:#94a3b8;font-size:13px;">
                        <strong style="color:#e2e8f0;">🕐 Time:</strong> {time_display}
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:4px 0 0;color:#94a3b8;font-size:13px;">
                        <strong style="color:#e2e8f0;">📅 Date:</strong> {date_display}
                      </td>
                    </tr>
                    {location_block}
                    {desc_block}
                  </table>
                </td>
              </tr>
              <!-- Footer -->
              <tr>
                <td style="padding:16px 32px 24px;border-top:1px solid #2a2d3a;">
                  <p style="margin:0;color:#64748b;font-size:11px;text-align:center;">
                    Sent by CogniPlan — Plan smarter, live better.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"CogniPlan <{SMTP_EMAIL}>"
    msg["To"] = to_email

    # Plain-text fallback
    plain_text = (
        f"Reminder: {task_title}\n"
        f"Time: {time_display}\n"
        f"Date: {date_display}\n"
    )
    if location:
        plain_text += f"Location: {location}\n"
    if description:
        plain_text += f"Notes: {description}\n"

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        logger.info(f"✅ Reminder email sent to {to_email} for task '{task_title}'")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send reminder email to {to_email}: {e}")
        return False
