import sqlite3
import sys
from datetime import datetime, timedelta

from email_service import send_email

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


def send_reminders(mode):
    """
    mode = 'evening' -> remind tonight about tomorrow's occurrence
    mode = 'morning' -> remind this morning about today's occurrence
    """

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    today_dow = WEEKDAYS[today.weekday()]
    tomorrow_dow = WEEKDAYS[tomorrow.weekday()]

    target_dow = tomorrow_dow if mode == "evening" else today_dow
    target_date_str = tomorrow_str if mode == "evening" else today_str
    target_label = "tomorrow" if mode == "evening" else "today"
    reminder_column = "evening_reminder_sent_date" if mode == "evening" else "morning_reminder_sent_date"

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT schedules.*, users.email
        FROM schedules
        JOIN users ON schedules.user_id = users.id
        WHERE schedules.status = 'Active'
    """)
    schedules = cursor.fetchall()

    emails_sent = 0

    for sched in schedules:

        # Skip schedules that haven't started yet
        if sched["start_date"] and sched["start_date"] > target_date_str:
            continue

        occurs_on_target_day = (
            sched["recurrence"] == "daily"
            or (sched["recurrence"] == "weekly" and sched["day_of_week"] == target_dow)
        )

        if not occurs_on_target_day:
            continue

        # Already reminded for this occurrence today? skip (prevents duplicate sends)
        if sched[reminder_column] == today_str:
            continue

        subject = f"\U0001F4C5 Schedule Reminder: {sched['title']}"

        body = f"""
Hello!

This is a reminder about your scheduled routine:

{sched['title']}

It's coming up {target_label}.

Log into TaskHub to view your schedule.

Have a productive day!

- TaskHub
"""

        send_email(sched["email"], subject, body)

        cursor.execute(
            f"UPDATE schedules SET {reminder_column} = ? WHERE id = ?",
            (today_str, sched["id"])
        )

        emails_sent += 1

    connection.commit()
    connection.close()

    return emails_sent


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else None

    if mode not in ("evening", "morning"):
        print("Usage: python schedule_reminder_job.py [evening|morning]")
        sys.exit(1)

    count = send_reminders(mode)
    print(f"Schedule reminder emails sent ({mode}): {count}")
