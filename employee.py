import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

employee_bp = Blueprint('employee', __name__)


@employee_bp.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password = ? AND role = ?',
            (email, password, 'employee')
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            session['employee_id'] = user[0]
            session['employee_email'] = email
            session['employee_username'] = email.split('@')[0]
            return redirect(url_for('employee.employee_dashboard'))
        else:
            error = 'Invalid email or password.'
    return render_template('employee_login.html', error=error)


@employee_bp.route('/employee/register', methods=['GET', 'POST'])
def employee_register():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            error = 'Passwords do not match.'
        else:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (email,))
            existing = cursor.fetchone()
            if existing:
                error = 'An account with this email already exists.'
                conn.close()
            else:
                cursor.execute(
                    'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                    (email, password, 'employee')
                )
                conn.commit()
                conn.close()
                return redirect(url_for('employee.employee_login'))

    return render_template('employee_register.html', error=error, success=success)


@employee_bp.route('/employee/dashboard')
def employee_dashboard():
    if not session.get('employee_id'):
        flash('You must be logged in to access that page.')
        return redirect(url_for('employee.employee_login'))
    return render_template('employee_dashboard.html', username=session.get('employee_username'))


@employee_bp.route('/employee/request-leave')
def request_leave():
    if not session.get('employee_id'):
        flash('You must be logged in to access that page.')
        return redirect(url_for('employee.employee_login'))
    return render_template('request_leave.html', username=session.get('employee_username'))


@employee_bp.route('/employee/view-requests')
def view_requests():
    if not session.get('employee_id'):
        flash('You must be logged in to access that page.')
        return redirect(url_for('employee.employee_login'))
    return render_template('view_requests.html', username=session.get('employee_username'))


@employee_bp.route('/employee/logout')
def employee_logout():
    session.pop('employee_id', None)
    session.pop('employee_email', None)
    session.pop('employee_username', None)
    return redirect(url_for('employee.employee_login'))
