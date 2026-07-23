# importing required add-ons
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from flask import session
from flask import flash
from flask import abort
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os

# creating engine for site
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")

app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///assignment_logbook.db'
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False

db= SQLAlchemy(app) 

# creating db schema
# users table
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    passwordhash = db.Column(db.String(255), nullable=False)
    created = db.Column(db.Date, default=datetime.utcnow)

    assignments = db.relationship("Assignments", backref='student', lazy=True)

# assignments table
class Assignments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    type = db.Column(db.String(100), nullable=True, index=True)
    course = db.Column(db.String(100), nullable=False, index=True)
    priority = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    due = db.Column(db.Date, nullable=True)
    created = db.Column(db.Date, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

    work_sessions = db.relationship(
        "WorkSession",
        backref="assignment",
        lazy=True,
        cascade="all, delete-orphan"
    )


# work sessions table
class WorkSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.utcnow)

#Priority calculation function
def calculate_priority(due_date):
    today = datetime.utcnow().date()
    days_left = (due_date - today).days

    if days_left <= 1:
        return 5  # Critical
    elif days_left <= 3:
        return 4  # High
    elif days_left <= 7:
        return 3  # Medium
    elif days_left <= 14:
        return 2  # Low
    else:
        return 1  # Very Low
    
def total_minutes(assignment):
    return sum(
        session.duration
        for session in assignment.work_sessions
    )

def total_hours(assignment):
    return round(total_minutes(assignment) / 60, 2)

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    return render_template('base.html', page=page)

# defining login route
@app.route('/login', methods=['GET'])
def show_form_login():
    return render_template('login.html')

# defining login form
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    # authenticating user
    if user and check_password_hash(user.passwordhash, password):
        session['user_id'] = user.user_id
        session['username'] = user.username

        return redirect(url_for('home'))
    else:
        return "Invalid credentials", 401
    
# defining logout function
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# defining create account route
@app.route('/create-account', methods=['GET'])
def show_form_create_account():
    return render_template('create-account.html')

# defining create account form
@app.route('/create-account', methods=['POST'])
def create_account():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    hashedPassword = generate_password_hash(password)

    new_user = User(
        username=username,
        email=email,
        passwordhash=hashedPassword
    )

    db.session.add(new_user)
    db.session.commit()
    
    return redirect(url_for('home'))

# defining add assignment page route
@app.route('/add-assignment', methods=['GET'])
def show_form_add_assignment():
    return render_template('add-assignment.html')

# defining add assignment form  
@app.route('/add-assignment', methods=['POST'])
def add_assignment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    assignmentName = request.form.get('assignment_type', '').strip()
    courseName = request.form.get('course', '').strip()
    notes = request.form.get('assignmentNotes', '').strip()
    dueDate = request.form.get('due_date', '').strip()

    # required fields validation (REMOVED priority check)
    if not assignmentName or not courseName or not dueDate:
        flash("Missing Required Fields.", "error")
        return redirect(url_for('show_form_add_assignment'))

    # convert date
    due_date_obj = datetime.strptime(dueDate, "%Y-%m-%d").date()

    # AUTO PRIORITY CALCULATION
    priority_value = calculate_priority(due_date_obj)

    new_assignment = Assignments(
        user_id=session['user_id'],
        type=assignmentName,
        course=courseName,
        priority=priority_value,
        notes=notes,
        due=due_date_obj
    )

    db.session.add(new_assignment)
    db.session.commit()

    flash("Assignment added successfully!", "success")
    return redirect(url_for('home'))

@app.route('/calendar')
def assignment_calendar():
    assignments = Assignments.query.filter_by(
        user_id=session['user_id']
    ).all()

    data = [
    {
        "id": a.id,
        "title": a.course,
        "subject": a.course,
        "type": a.type,
        "dueDate": a.due.strftime("%Y-%m-%d") if a.due else "",
        "priority": a.priority,
        "notes": a.notes,
        "overdue": a.due < datetime.utcnow().date() if a.due else False
    }
    for a in assignments
    ]

    return render_template("calendar.html", assignments=data)

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

    assignment = Assignments.query.get_or_404(id)

    assignment.completed = True

    db.session.commit()

    return jsonify({"success": True})

@app.route("/assignment/<int:id>")
def assignment_history(id):

    assignment = Assignments.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    sessions = WorkSession.query.filter_by(
        assignment_id=id
    ).order_by(
        WorkSession.start_time.desc()
    ).all()

    return render_template(
        "assignment-history.html",
        assignment=assignment,
        sessions=sessions,
        total=total_hours(assignment)
    )

@app.route("/study-statistics")
def study_statistics():

    assignments = Assignments.query.filter_by(
        user_id=session["user_id"]
    ).all()

    total = sum(
        total_minutes(a)
        for a in assignments
    )

    sessions = sum(
        len(a.work_sessions)
        for a in assignments
    )

    return render_template(
        "study-statistics.html",
        assignments=assignments,
        total_hours=round(total/60,2),
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

    return render_template(
        "log-work.html",
        assignment=assignment
    )

@app.route("/log-work/<int:assignment_id>", methods=["POST"])
def log_work(assignment_id):

    start = request.form.get("start")
    end = request.form.get("end")

    # convert times
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    duration = int((end_dt - start_dt).total_seconds() / 60)

    session_entry = WorkSession(
        assignment_id=assignment_id,
        start_time=start_dt,
        end_time=end_dt,
        duration=duration,
        notes=request.form.get("notes", "")
    )

    db.session.add(session_entry)
    db.session.commit()

    return redirect(url_for("assignment_history", id=assignment_id))

@app.route("/export-calendar/<int:assignment_id>")
def export_calendar(assignment_id):

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # Creates tables if they don't exist
    app.run(debug=True)