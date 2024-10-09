
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pytz
from models import db, User, Availability, Break, Notes

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

# Indian Standard Time timezone setup
IST = pytz.timezone('Asia/Kolkata')

# Home route - redirect to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Take the password directly from input without hashing.
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'qa':
                return redirect(url_for('qa_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

# Dashboard for doctors
@app.route('/dashboard')
def dashboard():
    user = get_logged_in_user()
    if user.role not in ['doctor']:
        return redirect(url_for('login'))
    
    availability = Availability.query.filter_by(user_id=user.id).all()
    breaks = Break.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, availability=availability, breaks=breaks)

# QA Radiographer Dashboard
@app.route('/qa_dashboard')
def qa_dashboard():
    user = get_logged_in_user()
    if user.role != 'qa':
        return redirect(url_for('login'))
    
    doctors_availability = Availability.query.all()
    return render_template('qa_dashboard.html', user=user, doctors_availability=doctors_availability)

# Admin control panel
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    user = get_logged_in_user()
    if user.role != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update schedules or manage notes
        pass
    
    doctors = User.query.filter_by(role='doctor').all()
    qas = User.query.filter_by(role='qa').all()
    return render_template('admin_dashboard.html', doctors=doctors, qas=qas)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def get_logged_in_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
