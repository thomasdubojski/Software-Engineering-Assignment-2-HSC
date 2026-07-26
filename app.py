# importing required add-ons
from itsdangerous import URLSafeTimedSerializer
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from flask import session, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import flask_mail
import secrets
import os

# creating engine for site
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///assignment_logbook.db'
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False

# Email Configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True

app.config["MAIL_USERNAME"] = "bhc.assignment.tracker@gmail.com"
app.config["MAIL_PASSWORD"] = "ikdl ojhl nkbc hbqe"

app.config["MAIL_DEFAULT_SENDER"] = "bhc.assignment.tracker@gmail.com"

mail = flask_mail.Mail(app)

db = SQLAlchemy(app)

# =========================
# MODELS
# =========================

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    passwordhash = db.Column(db.String(255), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    created = db.Column(db.Date, default=datetime.utcnow)

    assignments = db.relationship("Assignments", backref='student', lazy=True)


class Assignments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    type = db.Column(db.String(100), nullable=True, index=True)
    course = db.Column(db.String(100), nullable=False, index=True)
    priority = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    due = db.Column(db.Date, nullable=False)
    due_time = db.Column(db.Time, nullable=True)
    created = db.Column(db.Date, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

    work_sessions = db.relationship(
        "WorkSession",
        backref="assignment",
        lazy=True,
        cascade="all, delete-orphan"
    )


class WorkSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.utcnow)


def calculate_priority(due_date):
    today = datetime.utcnow().date()
    days_left = (due_date - today).days

    if days_left <= 1:
        return 5
    elif days_left <= 3:
        return 4
    elif days_left <= 7:
        return 3
    elif days_left <= 14:
        return 2
    return 1


def total_minutes(assignment):
    return sum(s.duration for s in assignment.work_sessions)


def total_hours(assignment):
    return round(total_minutes(assignment) / 60, 2)

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    return render_template('base.html', page=page)

@app.route('/login', methods=['GET'])
def show_form_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.passwordhash, password):

        if not user.verified:
            flash("Please verify your email before logging in.", "error")
            return redirect(url_for("show_form_login"))
        
        session['user_id'] = user.user_id
        session['username'] = user.username
        return redirect(url_for('home'))

    flash("Invalid credentials.", "error")
    return redirect(url_for("show_form_login"))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/create-account', methods=['GET'])
def show_form_create_account():
    return render_template('create-account.html')


@app.route('/create-account', methods=['POST'])
def create_account():
    username = request.form['username'].strip()
    email = request.form['email'].strip().lower()
    password = request.form['password']

    if User.query.filter_by(username=username).first():
        flash("That username is already taken. Please choose another.", "error")
        return redirect(url_for('show_form_create_account'))

    if User.query.filter_by(email=email).first():
        flash("An account with that email already exists.", "error")
        return redirect(url_for('show_form_create_account'))

    new_user = User(
        username=username,
        email=email,
        passwordhash=generate_password_hash(password)
    )

    db.session.add(new_user)
    db.session.commit()

    send_verification_email(new_user)

    flash(
        "Account created! Check your email to verify your account.",
        "success"
    )

    return redirect(url_for('show_form_login'))

@app.route("/verify/<token>")
def verify_email(token):

    email = confirm_verification_token(token)

    if not email:
        return "Verification link expired or invalid", 400


    user = User.query.filter_by(
        email=email
    ).first()


    if not user:
        return "User not found", 404


    user.verified = True

    db.session.commit()


    flash(
        "Email verified successfully. You can now login.",
        "success"
    )


    return redirect(url_for("show_form_login"))


@app.route('/add-assignment', methods=['GET'])
def show_form_add_assignment():
    return render_template('add-assignment.html')


@app.route('/add-assignment', methods=['POST'])
def add_assignment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignmentName = request.form.get('assignment_type', '').strip()
    courseName = request.form.get('course', '').strip()
    notes = request.form.get('assignmentNotes', '').strip()
    dueTime = request.form.get('due_time', '').strip()
    dueDate = request.form.get('due_date', '').strip()

    if not assignmentName or not courseName or not dueDate:
        flash("Missing Required Fields.", "error")
        return redirect(url_for('show_form_add_assignment'))

    due_date_obj = datetime.strptime(dueDate, "%Y-%m-%d").date()

    # AUTO PRIORITY CALCULATION
    priority_value = calculate_priority(due_date_obj)

    new_assignment = Assignments(
        user_id=session['user_id'],
        type=assignmentName,
        course=courseName,
        priority=priority_value,
        notes=notes,
        due=due_date_obj,
        due_time=datetime.strptime(dueTime, "%H:%M").time()
        if dueTime else None
    )

    db.session.add(new_assignment)
    db.session.commit()

    flash("Assignment added successfully!", "success")
    return redirect(url_for('home'))

@app.route("/calendar")
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignments = Assignments.query.filter_by(
        user_id=session['user_id']
    ).all()

    data = []

    for a in assignments:
        data.append({
            "id": a.id,
            "eventType": "assignment",
            "title": a.course,
            "subject": a.course,
            "type": a.type,
            "start": (datetime.combine(a.due, a.due_time).isoformat()
                if a.due_time
                else a.due.strftime("%Y-%m-%d")
            ),
            "priority": a.priority,
            "notes": a.notes,
            "overdue": a.due < datetime.utcnow().date() if a.due else False
        })

    sessions = WorkSession.query.join(
        Assignments,
        WorkSession.assignment_id == Assignments.id
    ).filter(
        Assignments.user_id == session["user_id"]
    ).all()

    for s in sessions:
        data.append({
            "id": f"session-{s.id}",
            "eventType": "session",
            "title": "Study Session",
            "assignment": s.assignment.course,
            "start": s.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": s.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration": s.duration,
            "notes": s.notes or ""
        })

    return render_template(
        "calendar.html",
        assignments=data
    )

@app.route("/assignment-dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignments = Assignments.query.filter_by(
        user_id=session['user_id']
    ).all()

    data = [{
        "id": a.id,
        "title": a.course + " Assignment",
        "subject": a.course,
        "type": a.type,
        "dueDate": a.due.strftime("%Y-%m-%d") if a.due else "",
        "priority": a.priority,
        "notes": a.notes or "",
        "completed": a.completed,
        "hours": total_hours(a),
        "minutes": total_minutes(a),
        "sessions": len(a.work_sessions),
        "overdue": a.due < datetime.utcnow().date() if a.due else False
    } for a in assignments]

    return render_template("assignment-dashboard.html", assignments=data)


@app.route('/complete-assignment/<int:id>', methods=['POST'])
def complete_assignment(id):
    if 'user_id' not in session:
        return jsonify({"success": False}), 401

    assignment = Assignments.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    assignment.completed = True
    db.session.commit()

    return jsonify({"success": True})



@app.route("/delete-assignment/<int:id>", methods=["POST"])
def delete_assignment(id):
    if 'user_id' not in session:
        return jsonify({"success": False}), 401

    assignment = Assignments.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(assignment)
    db.session.commit()

    return jsonify({"success": True})

@app.route("/assignment/<int:id>")
def assignment_history(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignment = Assignments.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    sessions = WorkSession.query.filter_by(
        assignment_id=id
    ).order_by(WorkSession.start_time.desc()).all()

    return render_template(
        "assignment-history.html",
        assignment=assignment,
        sessions=sessions,
        total=total_hours(assignment)
    )


@app.route("/study-statistics")
def study_statistics():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignments = Assignments.query.filter_by(
        user_id=session["user_id"]
    ).all()

    total = sum(total_minutes(a) for a in assignments)
    sessions = sum(len(a.work_sessions) for a in assignments)

    return render_template(
        "study-statistics.html",
        assignments=assignments,
        total_hours=round(total / 60, 2),
        total_sessions=sessions
    )

@app.route("/log-work/<int:assignment_id>", methods=["GET"])
def show_log_work(assignment_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignment = Assignments.query.filter_by(
        id=assignment_id,
        user_id=session["user_id"]
    ).first_or_404()

    return render_template("log-work.html", assignment=assignment)


@app.route("/log-work/<int:assignment_id>", methods=["POST"])
def log_work(assignment_id):

    start = datetime.fromisoformat(request.form.get("start"))
    end = datetime.fromisoformat(request.form.get("end"))

    duration = int((end - start).total_seconds() / 60)

    session_entry = WorkSession(
        user_id=session.get("user_id"),
        assignment_id=assignment_id,
        start_time=start,
        end_time=end,
        duration=duration,
        notes=request.form.get("notes", "")
    )

    db.session.add(session_entry)
    db.session.commit()

    return redirect(url_for("assignment_history", id=assignment_id))

@app.route("/export-calendar/<int:assignment_id>")
def export_calendar(assignment_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignment = Assignments.query.filter_by(
        id=assignment_id,
        user_id=session["user_id"]
    ).first_or_404()

    due = assignment.due.strftime("%Y%m%d")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Assignment Tracker//EN
BEGIN:VEVENT
UID:{assignment.id}@assignmenttracker
DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}
SUMMARY:{assignment.course} - {assignment.type}
DESCRIPTION:{assignment.notes or ""}
DTSTART;VALUE=DATE:{due}
DTEND;VALUE=DATE:{due}
END:VEVENT
END:VCALENDAR"""

    response = app.response_class(
        response=ics_content,
        mimetype="text/calendar"
    )

    response.headers["Content-Disposition"] = f"attachment; filename=assignment_{assignment.id}.ics"
    return response


@app.route("/google-calendar/<int:assignment_id>")
def google_calendar(assignment_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignment = Assignments.query.filter_by(
        id=assignment_id,
        user_id=session["user_id"]
    ).first_or_404()

    start = assignment.due.strftime("%Y%m%d")

    url = (
        "https://calendar.google.com/calendar/render?"
        "action=TEMPLATE"
        f"&text={assignment.course} - {assignment.type}"
        f"&dates={start}/{start}"
        f"&details={assignment.notes or ''}"
    )

    return redirect(url)


@app.route("/settings")
def settings():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template("settings.html", user=user)


@app.route("/test-email")
def test_email():

    msg = flask_mail.Message(
        subject="Assignment Centre Test",
        recipients=["bhc.assignment.tracker@gmail.com"]
    )

    msg.body = """
Congratulations!

Your Assignment Centre email system is working correctly.

This email was sent using Flask-Mail.
"""

    mail.send(msg)

    return "Email sent successfully!"

serializer = URLSafeTimedSerializer(app.secret_key)


def generate_verification_token(email):

    return serializer.dumps(
        email,
        salt="email-verification"
    )


def confirm_verification_token(token, expiration=3600):

    try:
        email = serializer.loads(
            token,
            salt="email-verification",
            max_age=expiration
        )

        return email

    except Exception:
        return None
    
def send_verification_email(user):

    token = generate_verification_token(user.email)

    link = url_for(
        "verify_email",
        token=token,
        _external=True
    )


    msg = flask_mail.Message(
        "Verify your Assignment Centre account",
        recipients=[user.email]
    )


    msg.body = f"""
Hi {user.username},

Welcome to Assignment Centre!

Please verify your email address by clicking this link:

{link}

This link expires in 1 hour.

Thanks,
Assignment Centre
"""


    mail.send(msg)

@app.route("/resend-verification")
def show_resend_verification():
    return render_template("resend-verification.html")

@app.route("/resend-verification", methods=["POST"])
def resend_verification():

    email = request.form["email"].strip().lower()

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("No account exists with that email.", "error")
        return redirect(url_for("show_resend_verification"))

    if user.verified:
        flash("This account has already been verified.", "success")
        return redirect(url_for("show_form_login"))

    send_verification_email(user)

    flash(
        "A new verification email has been sent.",
        "success"
    )

    return redirect(url_for("show_form_login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)