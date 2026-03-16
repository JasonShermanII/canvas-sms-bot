import requests
import smtplib
import os
from email.message import EmailMessage
from icalendar import Calendar
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

# --- SECURE CREDENTIALS (Reading from Environment Variables) ---
# We use a default empty string '' to prevent errors if the variable is missing
CALENDAR_URL = os.getenv('CANVAS_URL', '')
EMAIL_ADDRESS = os.getenv('SENDER_EMAIL', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER', '')

TEXT_GATEWAY = f"{PHONE_NUMBER}@tmomail.net"
FLORIDA_TIME = ZoneInfo("America/New_York")

FLORIDA_TIME = ZoneInfo("America/New_York")

print("Fetching calendar data from Canvas...")
response = requests.get(CALENDAR_URL)

if response.status_code == 200:
    cal = Calendar.from_ical(response.text)

    now = datetime.now(FLORIDA_TIME)
    next_week = now + timedelta(days=7)

    assignment_count = 0
    # This is the bucket we will toss our text message into
    text_message_body = "🎓 UPCOMING ASSIGNMENTS:\n\n"

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

                # Custom Zoom Filter!
                if "COP3503C" in assignment_name and "04:00 PM" in formatted_date:
                    text_message_body += f"💻 Zoom: {assignment_name}\n⏰ {formatted_date}\n\n"
                else:
                    text_message_body += f"📝 {assignment_name}\n⏰ {formatted_date}\n\n"

    if assignment_count == 0:
        text_message_body = "🎉 No assignments due in the next 7 days! Go relax."

    print(f"Found {assignment_count} items. Sending text message to phone...")

    # --- 2. SENDING THE TEXT MESSAGE ---
    try:
        # Create the email/text message object
        msg = EmailMessage()
        msg.set_content(text_message_body)
        msg['Subject'] = 'Canvas' # T-Mobile usually puts the subject in parentheses in the text
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TEXT_GATEWAY

        # Log into Google's Server and send it
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Secures the connection
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit() # Hang up the connection

        print("✅ Text message successfully sent!")

    except Exception as e:
        print(f"❌ Failed to send text: {e}")

else:
    print(f"Failed to get data. Error code: {response.status_code}")