import requests
import smtplib
import os
from email.message import EmailMessage
from icalendar import Calendar
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

# --- 1. SECURE CREDENTIALS ---
# If the cloud fails to pass the secret, it defaults to a blank string to prevent crashes
CALENDAR_URL = os.getenv('CANVAS_URL', '')
EMAIL_ADDRESS = os.getenv('SENDER_EMAIL', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER', '')

# T-Mobile Gateway
TEXT_GATEWAY = f"{PHONE_NUMBER}@tmomail.net"
FLORIDA_TIME = ZoneInfo("America/New_York")

def main():
    print("Fetching calendar data from Canvas...")
    response = requests.get(CALENDAR_URL)

    if response.status_code == 200:
        cal = Calendar.from_ical(response.text)
        now = datetime.now(FLORIDA_TIME)
        next_week = now + timedelta(days=7)

        assignment_count = 0

        # --- UI FORMATTING ---
        now_str = now.strftime("%A, %b %d")
        text_message_body = f"🚀 CANVAS DAILY BRIEFING\n📅 {now_str}\n"
        text_message_body += "─" * 15 + "\n\n"

        # Temporary bucket for the assignments so we can count them first
        assignments_text = ""

        for component in cal.walk():
            if component.name == "VEVENT":
                assignment_name = component.get('summary')
                raw_due_date = component.get('dtstart').dt

                is_due_soon = False
                formatted_date = ""

                if isinstance(raw_due_date, datetime):
                    local_time = raw_due_date.astimezone(FLORIDA_TIME)
                    if now <= local_time <= next_week:
                        is_due_soon = True
                        formatted_date = local_time.strftime("%b %d at %I:%M %p")

                elif isinstance(raw_due_date, date):
                    if now.date() <= raw_due_date <= next_week.date():
                        is_due_soon = True
                        formatted_date = raw_due_date.strftime("%b %d (All Day)")

                if is_due_soon:
                    assignment_count += 1
                    # Your Custom Zoom Filter
                    if "COP3503C" in assignment_name and "04:00 PM" in formatted_date:
                        assignments_text += f"💻 [ZOOM] {assignment_name}\n⏰ {formatted_date}\n\n"
                    else:
                        assignments_text += f"📝 {assignment_name}\n⏰ {formatted_date}\n\n"

        # Combine the header and the assignments
        if assignment_count == 0:
            text_message_body += "✅ You're all caught up! No assignments due in the next 7 days.\n"
        else:
            text_message_body += f"🔔 You have {assignment_count} items coming up:\n\n" + assignments_text

        text_message_body += "─" * 15 + "\nHave a great day, Jason!"

        # --- 2. SENDING THE TEXT ---
        try:
            msg = EmailMessage()
            msg.set_content(text_message_body)
            msg['Subject'] = 'Canvas'
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = TEXT_GATEWAY

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            print("✅ Text message successfully sent!")
        except Exception as e:
            print(f"❌ Failed to send text: {e}")

    else:
        print(f"Failed to get data. Error code: {response.status_code}")

# This ensures the script only runs if we call it directly
if __name__ == "__main__":
    main()