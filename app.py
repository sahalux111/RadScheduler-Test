from flask import Flask, render_template, request, redirect, session
import MySQLdb
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Import the database configuration
from config import db_config

# Connect to MySQL database (Hostinger)
def get_db_connection():
    return MySQLdb.connect(host=db_config['host'],
                           user=db_config['user'],
                           passwd=db_config['password'],
                           db=db_config['db'])

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to the database and fetch user
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT username, password, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        db.close()

        if user and user[1] == password:  # No password hashing, directly checking password
            session['username'] = user[0]
            session['role'] = user[2]
            return redirect('/dashboard')

    return render_template('login.html')

# Dashboard for all roles
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor()

    if session['role'] == 'doctor':
        # Fetch doctor-specific data (availability and breaks)
        cursor.execute("SELECT available_from, available_to FROM doctor_availability WHERE doctor_username = %s", (session['username'],))
        availability = cursor.fetchone()

        cursor.execute("SELECT break_from, break_to FROM doctor_breaks WHERE doctor_username = %s", (session['username'],))
        breaks = cursor.fetchall()

        db.close()
        return render_template('doctor_dashboard.html', availability=availability, breaks=breaks)

    elif session['role'] == 'admin':
        # Fetch all doctors' availability and breaks
        cursor.execute("SELECT doctor_username, available_from, available_to FROM doctor_availability")
        all_availability = cursor.fetchall()

        cursor.execute("SELECT doctor_username, break_from, break_to FROM doctor_breaks")
        all_breaks = cursor.fetchall()

        db.close()
        return render_template('admin_dashboard.html', all_availability=all_availability, all_breaks=all_breaks)

    elif session['role'] == 'qa_radiographer':
        # Fetch all doctors' availability
        cursor.execute("SELECT doctor_username, available_from, available_to FROM doctor_availability")
        all_availability = cursor.fetchall()
        db.close()

        # QA can view all doctor availability and update their own
        return render_template('qa_dashboard.html', all_availability=all_availability)

# Update availability for doctors or QA Radiographer
@app.route('/set_availability', methods=['POST'])
def set_availability():
    if 'username' not in session or session['role'] not in ['doctor', 'qa_radiographer']:
        return redirect('/login')

    available_from = request.form['available_from']
    available_to = request.form['available_to']

    db = get_db_connection()
    cursor = db.cursor()

    # Insert or update availability based on role
    cursor.execute("""
        INSERT INTO doctor_availability (doctor_username, available_from, available_to)
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE available_from=%s, available_to=%s
    """, (session['username'], available_from, available_to, available_from, available_to))

    db.commit()
    db.close()

    return redirect('/dashboard')

# Admin controls doctor availability and breaks
@app.route('/admin/update_schedule', methods=['POST'])
def update_schedule():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    doctor_username = request.form['doctor_username']
    available_from = request.form['available_from']
    available_to = request.form['available_to']

    db = get_db_connection()
    cursor = db.cursor()

    # Insert or update doctor's availability
    cursor.execute("""
        INSERT INTO doctor_availability (doctor_username, available_from, available_to)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE available_from=%s, available_to=%s
    """, (doctor_username, available_from, available_to, available_from, available_to))

    db.commit()
    db.close()

    return redirect('/dashboard')

# Admin controls doctor breaks
@app.route('/admin/update_break', methods=['POST'])
def update_break():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    doctor_username = request.form['doctor_username']
    break_from = request.form['break_from']
    break_to = request.form['break_to']

    db = get_db_connection()
    cursor = db.cursor()

    # Insert or update doctor's break
    cursor.execute("""
        INSERT INTO doctor_breaks (doctor_username, break_from, break_to)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE break_from=%s, break_to=%s
    """, (doctor_username, break_from, break_to, break_from, break_to))

    db.commit()
    db.close()

    return redirect('/dashboard')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
