import random

APP_BASE_URL = "https://beefking7.pythonanywhere.com"

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

MOTIVATIONAL_QUOTES = [
    "Discipline is choosing between what you want now and what you want most.",
    "Small daily actions compound into big results.",
    "The best time to start was earlier. The next best time is now.",
    "Progress is progress, no matter how small.",
    "You don't have to see the whole staircase, just take the first step.",
    "Consistency beats intensity over time.",
    "Every completed task is a vote for the person you're becoming.",
    "Done today is better than perfect someday.",
    "Momentum starts with one small win.",
    "Future you is counting on today you.",
    "Showing up is half the battle — you're already here.",
    "A little progress each day adds up to big results.",
]


def get_quote():
    return random.choice(MOTIVATIONAL_QUOTES)


def schedule_occurs_today(schedule_row, today_str, today_dow):
    """
    Mirrors the frontend's scheduleOccursOn logic:
    - must be Active
    - must have started (start_date <= today)
    - daily routines always count
    - weekly routines count only on their matching day_of_week
    """
    if schedule_row["status"] != "Active":
        return False

    if schedule_row["start_date"] and schedule_row["start_date"] > today_str:
        return False

    if schedule_row["recurrence"] == "daily":
        return True

    if schedule_row["recurrence"] == "weekly":
        return schedule_row["day_of_week"] == today_dow

    return False
