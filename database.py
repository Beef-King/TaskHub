import sqlite3

connection = sqlite3.connect("database.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    priority TEXT,
    due_date TEXT,
    status TEXT DEFAULT 'Pending',
    user_id INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT,
    auth_provider TEXT DEFAULT 'local',
    google_id TEXT,
    github_id TEXT,
    otp_code TEXT,
    otp_expiry TEXT
)
""")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN github_id TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN otp_code TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN otp_expiry TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN otp_code TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN otp_expiry TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("""
    ALTER TABLE tasks
    ADD COLUMN reminder_sent INTEGER DEFAULT 0
    """)
except sqlite3.OperationalError:
    pass
    pass

try:
    cursor.execute("""
    ALTER TABLE tasks
    ADD COLUMN user_id INTEGER
    """)
except sqlite3.OperationalError:
    pass
    pass

try:
    cursor.execute("""
    ALTER TABLE tasks
    ADD COLUMN recurrence TEXT
    """)
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    recurrence TEXT NOT NULL,
    day_of_week TEXT,
    start_date TEXT,
    status TEXT DEFAULT 'Active',
    evening_reminder_sent_date TEXT,
    morning_reminder_sent_date TEXT,
    duration_minutes INTEGER,
    user_id INTEGER
)
""")

try:
    cursor.execute("""
    ALTER TABLE schedules
    ADD COLUMN duration_minutes INTEGER
    """)
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedule_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    user_id INTEGER,
    UNIQUE(schedule_id, date)
)
""")

connection.commit()
connection.close()

#cursor.execute("DROP TABLE IF EXISTS users")

print("Database created successfully!")