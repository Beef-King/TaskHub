
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime, timedelta
from email_service import send_email
import sqlite3
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

load_dotenv()

print("SECRET_KEY =", os.getenv("SECRET_KEY"))
print("CLIENT_ID =", os.getenv("GOOGLE_CLIENT_ID"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# app.secret_key = "group5_secret_key"

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

github = oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={
        "scope": "read:user user:email"
    }
)

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("view_tasks"))
    return render_template("index.html")

@app.route("/signup", methods=["POST"])

def signup():

    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for("login"))

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Check if email already exists
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        connection.close()
        flash("Email already exists", "error")
        return redirect(url_for("login"))

    hashed_password = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users(first_name, last_name, email, password)
        VALUES (?, ?, ?, ?)
    """, (first_name, last_name, email, hashed_password))

    connection.commit()
    connection.close()

    flash("Account created successfully! Please sign in.", "success")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("view_tasks"))

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["first_name"] = user["first_name"]
            flash(f"Welcome back, {user['first_name']}!", "success")
            return redirect(url_for("view_tasks"))

        if not user:
            flash("No account found with that email — let's create one.", "error")
            return render_template("login.html", show_signup=True, signup_email=email)

        flash("Invalid email or password", "error")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/login/google")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/login/google/callback")
def google_callback():

    try:
        token = google.authorize_access_token()
        user_info = token["userinfo"]
    except Exception as e:
        print("Google OAuth Error:", e)
        flash("Google sign-in failed. Please try again.", "error")
        return redirect(url_for("login"))

    email = user_info["email"]
    first_name = user_info.get("given_name", "")
    last_name = user_info.get("family_name", "")
    google_id = user_info["sub"]

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    if user:

        cursor.execute("""
            UPDATE users
            SET google_id=?
            WHERE email=?
        """, (google_id, email))

        connection.commit()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

    else:

        password = generate_password_hash(os.urandom(24).hex())

        cursor.execute("""
            INSERT INTO users(
                first_name,
                last_name,
                email,
                password,
                auth_provider,
                google_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            first_name,
            last_name,
            email,
            password,
            "google",
            google_id
        ))

        connection.commit()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

    connection.close()

    session["user_id"] = user["id"]
    session["first_name"] = user["first_name"]

    flash(f"Welcome, {user['first_name']}!", "success")

    return redirect(url_for("view_tasks"))

@app.route("/login/github")
def github_login():
    redirect_uri = url_for("github_callback", _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route("/login/github/callback")
def github_callback():

    try:
        token = github.authorize_access_token()

        # Unlike Google, GitHub's profile endpoint doesn't include email
        # by default (it may be private), so we fetch it separately.
        profile_response = github.get("user", token=token)
        profile_response.raise_for_status()
        profile = profile_response.json()

        emails_response = github.get("user/emails", token=token)
        emails_response.raise_for_status()
        emails = emails_response.json()

    except Exception as e:
        print("GitHub OAuth Error:", e)
        flash("GitHub sign-in failed. Please try again.", "error")
        return redirect(url_for("login"))

    # Prefer the verified primary email; fall back to any verified email.
    email = None
    for entry in emails:
        if entry.get("primary") and entry.get("verified"):
            email = entry["email"]
            break
    if not email:
        for entry in emails:
            if entry.get("verified"):
                email = entry["email"]
                break

    if not email:
        flash("Your GitHub account has no verified email. Please add one on GitHub and try again.", "error")
        return redirect(url_for("login"))

    github_id = str(profile["id"])
    full_name = (profile.get("name") or profile.get("login") or "").strip()
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else profile.get("login", "")
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    if user:

        cursor.execute("""
            UPDATE users
            SET github_id=?
            WHERE email=?
        """, (github_id, email))

        connection.commit()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

    else:

        password = generate_password_hash(os.urandom(24).hex())

        cursor.execute("""
            INSERT INTO users(
                first_name,
                last_name,
                email,
                password,
                auth_provider,
                github_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            first_name,
            last_name,
            email,
            password,
            "github",
            github_id
        ))

        connection.commit()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

    connection.close()

    session["user_id"] = user["id"]
    session["first_name"] = user["first_name"]

    flash(f"Welcome, {user['first_name']}!", "success")

    return redirect(url_for("view_tasks"))

@app.route("/forgot_password", methods=["POST"])
def forgot_password():

    email = request.form["email"]

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    if not user:
        connection.close()
        flash("No account found with that email.", "error")
        return redirect(url_for("login"))

    otp = str(random.randint(100000, 999999))

    expiry = (
        datetime.now() + timedelta(minutes=10)
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE users
        SET otp_code=?, otp_expiry=?
        WHERE email=?
    """, (
        otp,
        expiry,
        email
    ))

    connection.commit()
    connection.close()

    subject = "TaskHub Password Reset Code"

    body = f"""
Hello,

Your TaskHub password reset verification code is:

{otp}

This code expires in 10 minutes.

If you didn't request a password reset, you can safely ignore this email.

TaskHub Team
"""

    send_email(email, subject, body)

    flash("A verification code has been sent to your email.", "success")

    return render_template(
    "login.html",
    show_otp=True,
    email=email
)

@app.route("/verify_otp", methods=["POST"])
def verify_otp():

    email = request.form["email"]
    otp = request.form["otp"]

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    connection.close()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("login"))

    if user["otp_code"] != otp:
        flash("Invalid OTP", "error")
        return redirect(url_for("login"))

    if datetime.now() > datetime.strptime(user["otp_expiry"], "%Y-%m-%d %H:%M:%S"):
        flash("OTP expired", "error")
        return redirect(url_for("login"))

    return redirect(url_for("reset_password", email=email))

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    if request.method == "GET":
        email = request.args.get("email")
        return render_template(
            "login.html",
            show_reset=True,
            email=email
        )

    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return render_template(
            "login.html",
            show_reset=True,
            email=email
        )

    hashed_password = generate_password_hash(password)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE users
        SET password=?, otp_code=NULL, otp_expiry=NULL
        WHERE email=?
        """,
        (hashed_password, email)
    )

    connection.commit()
    connection.close()

    flash("Password reset successfully! Please sign in.", "success")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/create", methods=["GET", "POST"])
def create_task():

    if "user_id" not in session:
            return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        # print("Form data received:", request.form)  # Debugging line
        
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        priority = request.form["priority"]
        due_date = request.form.get("due_date")
        recurrence = request.form.get("recurrence") or None
 
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, category, priority, due_date, user_id, recurrence) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, description, category, priority, due_date, user_id, recurrence)
        )
        connection.commit()
        connection.close()
 
        return redirect(url_for("view_tasks"))
 
    return render_template("create_task.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/schedule")
def schedule_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("schedule.html")

#send everything from here down to Beef_King

@app.route("/tasks")
def view_tasks():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
    "SELECT * FROM tasks WHERE user_id=?",
    (session["user_id"],)
)
    tasks = cursor.fetchall()


    connection.close()

    return render_template("view_task.html", tasks=tasks)

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM tasks WHERE user_id=?", (session["user_id"],))
    tasks = [dict(task) for task in cursor.fetchall()]

    connection.close()
    return jsonify(tasks), 200

@app.route("/api/tasks/<int:id>", methods=["GET"])
def api_get_task(id):
    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id=? AND user_id=?", (id, session["user_id"]))
    task = cursor.fetchone()

    connection.close()

    if task:
        return jsonify(dict(task)), 200

    return jsonify({"message": "Task not found"}), 404




@app.route("/api/tasks", methods=["POST"])
def api_create_task():

    data = request.get_json()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO tasks
        (title, description, category, priority, due_date, status, user_id, recurrence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["title"],
        data["description"],
        data["category"],
        data["priority"],
        data["due_date"],
        "Pending",
        session["user_id"],
        data.get("recurrence")
    ))

    connection.commit()

    task_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "message": "Task created successfully",
        "id": task_id
    }), 201

@app.route("/api/tasks/<int:id>", methods=["PUT"])
def api_update_task(id):

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE tasks
    SET
        title=?,
        description=?,
        category=?,
        priority=?,
        due_date=?,
        recurrence=?
    WHERE id=? AND user_id=?
""", (
    data["title"],
    data["description"],
    data["category"],
    data["priority"],
    data["due_date"],
    data.get("recurrence"),
    id,
    session["user_id"]
))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Task updated successfully"
    }), 200

@app.route("/api/tasks/<int:id>", methods=["DELETE"])
def api_delete_task(id):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Task deleted successfully"
    }), 200

@app.route("/api/tasks/search", methods=["GET"])
def api_search_tasks():

    query = request.args.get("q", "")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE (title LIKE ? OR description LIKE ?) AND user_id=?
    """, (
        f"%{query}%",
        f"%{query}%",
        session["user_id"]
    ))

    tasks = [dict(task) for task in cursor.fetchall()]

    connection.close()

    return jsonify(tasks), 200

@app.route("/api/tasks/filter", methods=["GET"])
def api_filter_tasks():

    category = request.args.get("category")
    priority = request.args.get("priority")
    status = request.args.get("status")

    sql = "SELECT * FROM tasks WHERE user_id=?"
    values = [session["user_id"]]

    if category:
        sql += " AND category=?"
        values.append(category)

    if priority:
        sql += " AND priority=?"
        values.append(priority)

    if status:
        sql += " AND status=?"
        values.append(status)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(sql, values)

    tasks = [dict(task) for task in cursor.fetchall()]

    connection.close()

    return jsonify(tasks), 200

@app.route("/api/tasks/stats", methods=["GET"])
def api_task_stats():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='Pending'",
        (user_id,)
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='Completed'",
        (user_id,)
    )
    completed = cursor.fetchone()[0]

    cursor.execute(
        """SELECT COUNT(*) FROM tasks
           WHERE user_id=? AND status='Pending' AND DATE(due_date) < DATE('now')""",
        (user_id,)
    )
    overdue = cursor.fetchone()[0]

    cursor.execute(
        "SELECT category, COUNT(*) FROM tasks WHERE user_id=? GROUP BY category",
        (user_id,)
    )
    by_category = {row[0]: row[1] for row in cursor.fetchall()}

    connection.close()

    return jsonify({
        "pending": pending,
        "completed": completed,
        "overdue": overdue,
        "by_category": by_category
    }), 200

@app.route("/api/tasks/bulk-complete", methods=["POST"])
def api_bulk_complete():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    task_ids = data.get("ids", [])

    if not task_ids:
        return jsonify({"message": "No task IDs provided"}), 400

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    placeholders = ",".join("?" for _ in task_ids)

    cursor.execute(
        f"""UPDATE tasks SET status='Completed'
            WHERE id IN ({placeholders}) AND user_id=?""",
        (*task_ids, session["user_id"])
    )

    updated_count = cursor.rowcount
    connection.commit()
    connection.close()

    return jsonify({"updated": updated_count}), 200

@app.route("/api/tasks/sort", methods=["GET"])
def api_sort_tasks():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    sort_by = request.args.get("by", "due_date")

    allowed_columns = {
        "due_date": "due_date ASC",
        "priority": """CASE priority
                            WHEN 'High' THEN 1
                            WHEN 'Medium' THEN 2
                            WHEN 'Low' THEN 3
                       END ASC""",
        "title": "title ASC"
    }

    order_clause = allowed_columns.get(sort_by, "due_date ASC")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        f"SELECT * FROM tasks WHERE user_id=? ORDER BY {order_clause}",
        (session["user_id"],)
    )

    tasks = [dict(task) for task in cursor.fetchall()]

    connection.close()

    return jsonify(tasks), 200

@app.route("/api/tasks/overdue", methods=["GET"])
def api_overdue_tasks():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        """SELECT * FROM tasks
           WHERE user_id=? AND status='Pending' AND DATE(due_date) < DATE('now')
           ORDER BY due_date ASC""",
        (session["user_id"],)
    )

    tasks = [dict(task) for task in cursor.fetchall()]

    connection.close()

    return jsonify(tasks), 200

@app.route("/api/tasks/range", methods=["GET"])
def api_tasks_in_range():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    start = request.args.get("start")
    end = request.args.get("end")

    if not start or not end:
        return jsonify({"message": "start and end query params are required (YYYY-MM-DD)"}), 400

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        """SELECT * FROM tasks
           WHERE user_id=? AND DATE(due_date) BETWEEN DATE(?) AND DATE(?)
           ORDER BY due_date ASC""",
        (session["user_id"], start, end)
    )

    tasks = [dict(task) for task in cursor.fetchall()]

    connection.close()

    return jsonify(tasks), 200

# ---------- SCHEDULES (recurring routines, separate from one-off tasks) ----------

@app.route("/api/schedules", methods=["GET"])
def api_get_schedules():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM schedules WHERE user_id=?", (session["user_id"],))
    schedules = [dict(s) for s in cursor.fetchall()]

    connection.close()
    return jsonify(schedules), 200

@app.route("/api/schedules", methods=["POST"])
def api_create_schedule():

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    recurrence = data.get("recurrence")
    if recurrence not in ("daily", "weekly"):
        return jsonify({"message": "recurrence must be 'daily' or 'weekly'"}), 400

    day_of_week = data.get("day_of_week") if recurrence == "weekly" else None
    start_date = data.get("start_date") or datetime.now().strftime("%Y-%m-%d")
    duration_minutes = data.get("duration_minutes")
    if duration_minutes in ("", None):
        duration_minutes = None
    else:
        try:
            duration_minutes = int(duration_minutes)
        except (TypeError, ValueError):
            return jsonify({"message": "duration_minutes must be a number"}), 400

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO schedules
        (title, description, recurrence, day_of_week, start_date, status, duration_minutes, user_id)
        VALUES (?, ?, ?, ?, ?, 'Active', ?, ?)
    """, (
        data["title"],
        data.get("description"),
        recurrence,
        day_of_week,
        start_date,
        duration_minutes,
        session["user_id"]
    ))

    connection.commit()
    schedule_id = cursor.lastrowid
    connection.close()

    return jsonify({"message": "Schedule created successfully", "id": schedule_id}), 201

@app.route("/api/schedules/<int:id>", methods=["PUT"])
def api_update_schedule(id):

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    recurrence = data.get("recurrence")
    if recurrence not in ("daily", "weekly"):
        return jsonify({"message": "recurrence must be 'daily' or 'weekly'"}), 400

    day_of_week = data.get("day_of_week") if recurrence == "weekly" else None
    duration_minutes = data.get("duration_minutes")
    if duration_minutes in ("", None):
        duration_minutes = None
    else:
        try:
            duration_minutes = int(duration_minutes)
        except (TypeError, ValueError):
            return jsonify({"message": "duration_minutes must be a number"}), 400

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE schedules
        SET title=?, description=?, recurrence=?, day_of_week=?, start_date=?, duration_minutes=?
        WHERE id=? AND user_id=?
    """, (
        data["title"],
        data.get("description"),
        recurrence,
        day_of_week,
        data.get("start_date"),
        duration_minutes,
        id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return jsonify({"message": "Schedule updated successfully"}), 200

@app.route("/api/schedules/<int:id>", methods=["DELETE"])
def api_delete_schedule(id):

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM schedules WHERE id=? AND user_id=?", (id, session["user_id"]))

    connection.commit()
    connection.close()

    return jsonify({"message": "Schedule deleted successfully"}), 200

@app.route("/api/schedules/<int:id>/toggle", methods=["POST"])
def api_toggle_schedule(id):

    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT status FROM schedules WHERE id=? AND user_id=?", (id, session["user_id"]))
    schedule = cursor.fetchone()

    if not schedule:
        connection.close()
        return jsonify({"message": "Schedule not found"}), 404

    new_status = "Paused" if schedule["status"] == "Active" else "Active"

    cursor.execute(
        "UPDATE schedules SET status=? WHERE id=? AND user_id=?",
        (new_status, id, session["user_id"])
    )
    connection.commit()
    connection.close()

    return jsonify({"message": "Schedule updated", "status": new_status}), 200

@app.route("/complete/<int:id>", methods=["POST"])
def complete_task(id):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT status, title, description, category, priority, due_date, recurrence FROM tasks WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )

    task = cursor.fetchone()

    if task:
        current_status, title, description, category, priority, due_date, recurrence = task

        if current_status == "Pending":
            new_status = "Completed"
        else:
            new_status = "Pending"

        cursor.execute(
            "UPDATE tasks SET status=? WHERE id=? AND user_id=?",
            (new_status, id, session["user_id"])
        )

        # If this task just got completed and it's a recurring task,
        # create the next occurrence so it doesn't just disappear.
        if new_status == "Completed" and recurrence in ("daily", "weekly") and due_date:
            try:
                current_due = datetime.strptime(due_date, "%Y-%m-%d")
                delta = timedelta(days=1) if recurrence == "daily" else timedelta(days=7)
                next_due = (current_due + delta).strftime("%Y-%m-%d")

                cursor.execute("""
                    INSERT INTO tasks
                    (title, description, category, priority, due_date, status, user_id, recurrence, reminder_sent)
                    VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?, 0)
                """, (title, description, category, priority, next_due, session["user_id"], recurrence))
            except ValueError:
                # due_date wasn't in the expected format, skip auto-recurrence
                pass

        connection.commit()

    connection.close()

    return redirect(url_for("view_tasks"))

@app.route("/api/reminders" , methods=["POST"])
def api_reminders():

    secret = request.headers.get("X-SECRET-TOKEN")

    if secret != os.environ.get("REMINDER_SECRET"):
        return jsonify({"error": "Unauthorized"}), 401

    # your reminder code...

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT
            tasks.id,
            tasks.title,
            tasks.due_date,
            users.email
        FROM tasks
        JOIN users
        ON tasks.user_id = users.id
        WHERE
            tasks.status = 'Pending'
            AND tasks.reminder_sent = 0
            AND DATE(tasks.due_date) = ?
    """, (tomorrow,))

    reminders = cursor.fetchall()

    emails_sent = 0

    for reminder in reminders:

        subject = "⏰ Task Reminder"

        body = f"""
Hello!

This is a reminder that your task:

{reminder['title']}

is due tomorrow ({reminder['due_date']}).

Log into TaskHub to complete it.

Have a productive day!

- TaskHub
"""

        send_email(
            reminder["email"],
            subject,
            body
        )

        cursor.execute("""
            UPDATE tasks
            SET reminder_sent = 1
            WHERE id = ?
        """, (reminder["id"],))

        emails_sent += 1

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "emails_sent": emails_sent
    })


if __name__ == "__main__":
    app.run(debug=True)