from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from threading import Timer
from datetime import datetime, timedelta
import pytz
from config import db_config

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure database connection
def get_db_connection():
    connection = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        db=db_config['db'],
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Convert UTC to IST
def utc_to_ist(utc_dt):
    ist_tz = pytz.timezone('Asia/Kolkata')
    return utc_dt.astimezone(ist_tz)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if session['role'] == 'doctor':
        cursor.execute("SELECT * FROM availability WHERE doctor_id=(SELECT id FROM users WHERE username=%s)", (session['username'],))
        availability = cursor.fetchall()
        return render_template('dashboard.html', availability=availability)
    else:
        # For admin or QA roles, show all doctors' availability
        cursor.execute("SELECT * FROM availability")
        all_availability = cursor.fetchall()
        return render_template('admin_panel.html', availability=all_availability)

# Availability management route for doctors
@app.route('/set_availability', methods=['GET', 'POST'])
def set_availability():
    if 'username' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))

    if request.method == 'POST':
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO availability (doctor_id, start_time, end_time) VALUES ((SELECT id FROM users WHERE username=%s), %s, %s)", 
                       (session['username'], start_time, end_time))
        conn.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('availability.html')

# Admin can add notes for doctors
@app.route('/add_note', methods=['POST'])
def add_note():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    doctor_id = request.form['doctor_id']
    note = request.form['note']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (doctor_id, note) VALUES (%s, %s)", (doctor_id, note))
    conn.commit()
    
    return redirect(url_for('dashboard'))

# Log out
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Function to periodically ping the app
def ping_app():
    Timer(15, ping_app).start()

# Start periodic ping
ping_app()

if __name__ == '__main__':
    app.run(debug=True)
