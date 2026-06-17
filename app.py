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
    priority = request.form.get('priority', '').strip()
    notes = request.form.get('assignmentNotes', '').strip()
    dueDate = request.form.get('due_date', '').strip()

    # required fields validation
    if not assignmentName or not courseName or not priority or not dueDate:
        flash("Missing Required Fields.", "error")
        return redirect(url_for('show_form_add_assignment'))

    new_assignment = Assignments(
        user_id=session['user_id'],
        type=assignmentName,
        course=courseName,
        priority=int(priority),
        notes=notes,
        due=datetime.strptime(dueDate, "%Y-%m-%d").date()
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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # Creates tables if they don't exist
    app.run(debug=True)