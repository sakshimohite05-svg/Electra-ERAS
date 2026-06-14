from flask import Flask, render_template, request, redirect, session
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash
from email.message import EmailMessage
import smtplib
from datetime import datetime, timedelta
import secrets
from flask import render_template, request, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re
from flask import render_template
from functools import wraps
from flask import session, redirect, url_for

app = Flask(__name__)
app.secret_key = "electra_secret_key"

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_MYSQL_PASSWORD",
        database="electra"
    )

def login_required():
    return "username" in session

# ---------------- LANGUAGE TEXTS ----------------
LANGUAGES = {
    "en": {
        # NAVBAR
        "home": "Home",
        "dashboard": "Dashboard",
        "analysis": "Analysis",
        "electors": "Electors",
        "contact": "Contact",
        "feedback": "Feedback",
        "admin": "Admin" , 
        # HOME
        "home_title": "Election Related Analysis System",
        "home_desc": "A secure and efficient platform...",
        
        # DASHBOARD
        "total_electors": "Total Electors",
        "voted": "Voted",
        "not_voted": "Not Voted",
        "feedbacks": "Feedbacks",

        # SETTINGS
        "settings": "Account Settings",
        "language": "Language",
        "notifications": "Notifications",
        "save": "Save Settings"
    },

    "hi": {
        "home": "होम",
        "dashboard": "डैशबोर्ड",
        "analysis": "विश्लेषण",
        "electors": "मतदाता",
        "contact": "संपर्क",
        "feedback": "प्रतिक्रिया",
        "admin": "एडमिन" ,

        "home_title": "चुनाव विश्लेषण प्रणाली",
        "home_desc": "सुरक्षित और कुशल प्लेटफॉर्म...",

        "total_electors": "कुल मतदाता",
        "voted": "मतदान किया",
        "not_voted": "मतदान नहीं किया",
        "feedbacks": "प्रतिक्रियाएँ",

        "settings": "सेटिंग्स",
        "language": "भाषा",
        "notifications": "सूचनाएँ",
        "save": "सेव करें"
    },

    "mr": {
        "home": "मुख्यपृष्ठ",
        "dashboard": "डॅशबोर्ड",
        "analysis": "विश्लेषण",
        "electors": "मतदार",
        "contact": "संपर्क",
        "feedback": "अभिप्राय",
         "admin": "अॅडमिन" ,

        "home_title": "निवडणूक विश्लेषण प्रणाली",
        "home_desc": "सुरक्षित आणि कार्यक्षम प्रणाली...",

        "total_electors": "एकूण मतदार",
        "voted": "मत दिले",
        "not_voted": "मत दिले नाही",
        "feedbacks": "अभिप्राय",

        "settings": "सेटिंग्स",
        "language": "भाषा",
        "notifications": "सूचना",
        "save": "जतन करा"
    }
}

# ---------------- CONTEXT PROCESSOR ----------------
@app.context_processor
def inject_language():
    try:
        lang = session.get("language", "en")
        texts = LANGUAGES.get(lang, LANGUAGES["en"])

        return dict(t=texts)

    except Exception as e:
        print("Language error:", e)
        return dict(t=LANGUAGES["en"])

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/profile")
@login_required
def profile():
    username = session.get("username")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔹 USER INFO
    cursor.execute("""
        SELECT username, email, role
        FROM users
        WHERE username=%s
    """, (username,))
    user = cursor.fetchone()

    # 🔹 STEP 3 → ELECTOR INFO (ADD HERE 👇)
    cursor.execute("""
        SELECT name, region, status
        FROM electors
        WHERE name = %s
    """, (username,))
    elector = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("profile.html", user=user, elector=elector)

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # GET USER DATA
    cursor.execute(
        "SELECT * FROM users WHERE username=%s",
        (session['username'],)
    )
    user = cursor.fetchone()

    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']

        cursor.execute(
            "UPDATE users SET username=%s, email=%s WHERE username=%s",
            (new_username, new_email, session['username'])
        )
        conn.commit()

        # 🔥 IMPORTANT
        session['username'] = new_username

        cursor.close()
        conn.close()

        return redirect('/profile')

    cursor.close()
    conn.close()

    return render_template('edit_profile.html', user=user)
    
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    username = session.get("username")

    if request.method == "POST":
        current = request.form.get("current_password")
        new = request.form.get("new_password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and user["password"] == current:
            cursor.execute("""
                UPDATE users
                SET password=%s
                WHERE username=%s
            """, (new, username))
            conn.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Current password is incorrect!", "danger")

        cursor.close()
        conn.close()

    return render_template("change_password.html")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # ✅ Hardcoded Admin
        if username == "admin" and password == "admin123":
            session["username"] = "admin"
            session["role"] = "admin"
            return redirect(url_for("dashboard"))

        # ✅ Check normal users
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                       (username, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session["last_login"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
            session["username"] = user["username"]
            session["role"] = "user"
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)

@app.route("/delete-account", methods=["POST"])
def delete_account():
    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE username=%s", (username,))
    cursor.execute("DELETE FROM contact_messages WHERE name=%s", (username,))

    conn.commit()

    cursor.close()
    conn.close()

    session.clear()

    return redirect(url_for("login"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- FORGOT PASSWORD ----------------
import random
from flask import session

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        print("Entered Email:", email)

        cursor.execute("SELECT * FROM users WHERE LOWER(TRIM(email)) = LOWER(%s)", (email,))
        user = cursor.fetchone()

        # DEBUG PRINTS (KEEP BEFORE CLOSE)
        cursor.execute("SELECT username, email FROM users")
        users = cursor.fetchall()

        if not user:
            cursor.close()
            conn.close()
            return render_template("forgot_password.html", error="Email not found")

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        session["reset_email"] = email
        session["reset_otp"] = otp

        print("OTP is:", otp)

        # ✅ CLOSE ONLY AT END
        cursor.close()
        conn.close()

        return redirect("/verify-otp")

    return render_template("forgot_password.html")
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        if entered_otp == session.get("reset_otp"):
            return redirect("/reset-password")
        else:
            return "Invalid OTP"

    return render_template("verify_otp.html")

def get_user_language():
    if "language" in session:
        return session["language"]
    return "en"


@app.route("/admin/messages")
def admin_messages():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC")
    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin_messages.html", messages=messages)



# ---------------- RESET PASSWORD ----------------
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form["password"]
        email = session.get("reset_email")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (new_password, email)
        )

        conn.commit()
        cursor.close()
        conn.close()

        session.pop("reset_email", None)
        session.pop("reset_otp", None)

        return redirect("/login")

    return render_template("reset_password.html")



# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total electors
    cursor.execute("SELECT COUNT(*) AS total FROM electors")
    total_electors = cursor.fetchone()["total"]

    # Voted
    cursor.execute("SELECT COUNT(*) AS voted FROM electors WHERE status = 'Voted'")
    voted = cursor.fetchone()["voted"]

    # Not voted
    cursor.execute("SELECT COUNT(*) AS not_voted FROM electors WHERE status = 'Not Voted'")
    not_voted = cursor.fetchone()["not_voted"]

    # Feedbacks
    cursor.execute("SELECT COUNT(*) AS feedbacks FROM feedback")
    feedbacks = cursor.fetchone()["feedbacks"]
    print(session)
    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_electors=total_electors,
        voted=voted,
        not_voted=not_voted,
        feedbacks=feedbacks
    )

@app.route("/admin/add-elector", methods=["GET", "POST"])
def add_elector():
    if request.method == "POST":
        name = request.form.get("name")
        region = request.form.get("region")
        
        if not name or not region:
            flash("All fields are required!", "danger")
            return redirect(url_for("add_elector"))

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
            INSERT INTO electors (name, region, status)
             VALUES (%s, %s, 'Not Voted')
            """, (name, region))

            db.commit()
            cursor.close()
            db.close()

            flash("Elector added successfully!", "success")
            return redirect(url_for("admin_electors"))

        except Exception as e:
            print("ERROR:", e)
            flash("Something went wrong!", "danger")
            return redirect(url_for("add_elector"))

    return render_template("add_elector.html")

@app.route("/admin/edit-elector/<int:id>", methods=["GET", "POST"])
def edit_elector(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        region = request.form["region"]
        status = request.form["status"]

        cursor.execute(
            "UPDATE electors SET name=%s, region=%s, status=%s WHERE id=%s",
            (name, region, status, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/admin/electors")

    cursor.execute("SELECT * FROM electors WHERE id=%s", (id,))
    elector = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_elector.html", elector=elector)



@app.route("/admin/delete-elector/<int:id>")
def delete_elector(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM electors WHERE id=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin/electors")




# ---------------- SETTINGS ----------------
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    username = session.get("username")

    if request.method == 'POST':
        language = request.form.get('language')
        email_alerts = 1 if request.form.get('email_alerts') else 0
        sms_alerts = 1 if request.form.get('sms_alerts') else 0
        username = session.get("username")
        cursor.execute("""
    UPDATE users
    SET language=%s,
        email_alerts=%s,
        sms_alerts=%s
    WHERE username=%s
""", (language, email_alerts, sms_alerts, username))
        conn.commit()

        # update session instantly
        session['language'] = language


    # fetch latest settings
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    settings = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("settings.html", settings=settings)
# ---------------- CONTACT ----------------
@app.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # ===== VALIDATION =====
        if not name or not email or not message:
            flash("All fields are required!", "danger")
            return redirect(url_for("contact"))

        if len(message) < 10:
            flash("Message must be at least 10 characters!", "danger")
            return redirect(url_for("contact"))

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, email):
            flash("Invalid email format!", "danger")
            return redirect(url_for("contact"))

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
                (name, email, message)
            )

            db.commit()
            cursor.close()
            db.close()

            flash("Message sent successfully!", "success")

        except Exception as e:
            print(e)
            flash("Something went wrong!", "danger")

        return redirect(url_for("contact"))

    return render_template("contact.html")


# ================= FEEDBACK =================

@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # INSERT FEEDBACK
    if request.method == "POST":
        comment = request.form.get("feedback")

        if comment:
            cursor.execute(
                "INSERT INTO feedback (username, comment) VALUES (%s, %s)",
                (session["username"], comment)
            )
            conn.commit()

        return redirect(url_for("feedback"))

    # FETCH FEEDBACKS
    cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC")
    feedbacks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("feedback.html", feedbacks=feedbacks)


# ================= DELETE FEEDBACK =================


@app.route("/delete_feedback/<int:id>", methods=["POST"])
def delete_feedback(id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM feedback WHERE id=%s AND (username=%s OR %s='admin')",
        (id, session["username"], session["username"])
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("feedback"))

@app.route("/edit_voter/<int:voter_id>", methods=["GET", "POST"])
def edit_voter(voter_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        region = request.form["region"]
        status = request.form["status"]

        # Convert status to has_voted (1 or 0)
        if status == "Voted":
            has_voted = 1
        else:
            has_voted = 0

        cursor.execute("""
            UPDATE voters
            SET name=%s, region=%s, has_voted=%s
            WHERE id=%s
        """, (name, region, has_voted, voter_id))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("admin_electors"))

    # GET request
    cursor.execute("SELECT * FROM voters WHERE id=%s", (voter_id,))
    voter = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_voter.html", voter=voter)

@app.route("/add_voter", methods=["POST"])
def add_voter():
    name = request.form["name"]
    region = request.form["region"]
    status = request.form["status"]

    if status == "Voted":
        has_voted = 1
    else:
        has_voted = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO voters (name, region, has_voted)
        VALUES (%s, %s, %s)
    """, (name, region, has_voted))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_electors"))

@app.route("/analysis")
@login_required
def analysis():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # TOTAL
    cursor.execute("SELECT COUNT(*) AS total FROM electors")
    total = cursor.fetchone()["total"]

    # VOTED
    cursor.execute("SELECT COUNT(*) AS voted FROM electors WHERE status = 'Voted'")
    voted = cursor.fetchone()["voted"]

    # NOT VOTED
    cursor.execute("SELECT COUNT(*) AS not_voted FROM electors WHERE status = 'Not Voted'")
    not_voted = cursor.fetchone()["not_voted"]

    # REGION DATA ✅
    cursor.execute("""
        SELECT region, COUNT(*) AS count
        FROM electors
        GROUP BY region
    """)
    regions = cursor.fetchall()

    region_names = [r["region"] for r in regions]
    region_counts = [r["count"] for r in regions]

    # PARTY DATA ✅
    cursor.execute("""
        SELECT party, SUM(votes) AS total_votes
        FROM party_votes
        GROUP BY party
    """)
    party_data = cursor.fetchall()

    if not party_data:
        party_names = []
        party_votes = []
    else:
        party_names = [p["party"] for p in party_data]
        party_votes = [p["total_votes"] for p in party_data]

    cursor.close()
    conn.close()

    return render_template(
        "analysis.html",
        total=total,
        voted=voted,
        not_voted=not_voted,
        region_names=region_names,
        region_counts=region_counts,
        party_names=party_names,
        party_votes=party_votes
    )

@app.route('/analysis-data')
def analysis_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM voters")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS voted FROM voters WHERE has_voted = 1")
    voted = cursor.fetchone()['voted']

    not_voted = total - voted

    conn.close()

    return {
        "total": total,
        "voted": voted,
        "not_voted": not_voted
    }

@app.route("/party-analysis")
def party_analysis():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT region, party, SUM(votes) AS total_votes
        FROM party_votes
        GROUP BY region, party
    """)

    data = cursor.fetchall()

    print("DATA:", data)  # debug

# ✅ SAFE WINNER LOGIC
    if data:
        winner = max(data, key=lambda x: x["total_votes"])
    else:
        winner = None

    cursor.close()
    conn.close()

    return render_template(
    "party_analysis.html",
    data=data,
    winner=winner
)

@app.route("/electors")
def electors():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    name = request.args.get("name")
    region = request.args.get("region")
    status = request.args.get("status")

    query = "SELECT * FROM electors WHERE 1=1"
    values = []

    if name:
        query += " AND name LIKE %s"
        values.append("%" + name + "%")

    if region:
        query += " AND region LIKE %s"
        values.append("%" + region + "%")

    if status:
        query += " AND status = %s"
        values.append(status)

    cursor.execute(query, values)
    electors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("electors.html", electors=electors)

@app.route("/view_contacts")
def view_contacts():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
        messages = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template("view_contacts.html", messages=messages)

    except Exception as e:
        print(e)
        flash("Unable to load contact messages!", "danger")
        return redirect(url_for("admin_electors"))

@app.route("/delete_contact/<int:id>")
def delete_contact(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("DELETE FROM contact_messages WHERE id = %s", (id,))
        db.commit()

        cursor.close()
        db.close()

        flash("Message deleted successfully!", "success")

    except Exception as e:
        print(e)
        flash("Unable to delete message!", "danger")

    return redirect(url_for("view_contacts"))


@app.route("/admin")
def admin_redirect():
    if session.get("role") != "admin":
        return redirect("/login")

    return redirect("/admin/electors")

@app.route("/admin/electors")
def admin_electors():

    status = request.args.get("status")
    name = request.args.get("name")
    region = request.args.get("region")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM electors WHERE 1=1"
    params = []

    if status and status != "All":
        query += " AND status = %s"
        params.append(status)

    if name and name.strip() != "":
        query += " AND name LIKE %s"
        params.append(f"%{name}%")

    if region and region.strip() != "":
        query += " AND region LIKE %s"
        params.append(f"%{region}%")

    query += " ORDER BY id DESC"

    cursor.execute(query, tuple(params))
    electors = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("admin_electors.html", electors=electors)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 🔍 Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return render_template("register.html", error="Username already exists. Try another one.")

        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'user')",
            (username, email, password)
        )
    
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")



# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
