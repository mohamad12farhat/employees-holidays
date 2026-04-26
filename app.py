import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, DB_PATH
from employee import employee_bp
from mail_utils import notify_employee_status_change

app = Flask(__name__)
app.secret_key = 'secret_key'

app.register_blueprint(employee_bp)

init_db()


@app.route('/')
def index():
    if session.get('admin'):
        return redirect(url_for('dashboard'))
    if session.get('user_id'):
        return redirect(url_for('employee.employee_dashboard'))
    return render_template('index.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password = ? AND role = ?',
            (username, password, 'admin')
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin'):
        flash('You must be logged in as admin to access that page.')
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'employee'")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leave_requests WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leave_requests WHERE status = 'approved'")
    approved_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leave_requests WHERE status = 'rejected'")
    rejected_count = cursor.fetchone()[0]

    cursor.execute('''
        SELECT lr.id, u.full_name, u.username, lr.start_date, lr.end_date,
               lr.leave_days, lr.reason, lr.status
        FROM leave_requests lr
        JOIN users u ON lr.user_id = u.id
        ORDER BY lr.id DESC
        LIMIT 5
    ''')
    recent_requests = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html',
        total_employees=total_employees,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        recent_requests=recent_requests
    )


@app.route('/admin/leave-requests')
def leave_requests():
    if not session.get('admin'):
        flash('You must be logged in as admin to access that page.')
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT lr.id, u.full_name, u.username, lr.start_date, lr.end_date,
               lr.leave_days, lr.reason, lr.status
        FROM leave_requests lr
        JOIN users u ON lr.user_id = u.id
        ORDER BY lr.id DESC
    ''')
    requests_list = cursor.fetchall()
    conn.close()
    return render_template('view-leave-requests.html', requests=requests_list)


@app.route('/admin/update-request-status/<int:request_id>', methods=['POST'])
def update_request_status(request_id):
    if not session.get('admin'):
        flash('You must be logged in as admin to access that page.')
        return redirect(url_for('login'))
    new_status = request.form.get('status')
    if new_status not in ('pending', 'approved', 'rejected'):
        flash('Invalid status.', 'danger')
        return redirect(url_for('leave_requests'))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('UPDATE leave_requests SET status = ? WHERE id = ?', (new_status, request_id))
    conn.commit()

    # Fetch request + employee details to send notification
    cursor.execute(
        '''SELECT lr.start_date, lr.end_date, lr.leave_days,
                  u.username AS email, u.full_name
           FROM leave_requests lr
           JOIN users u ON lr.user_id = u.id
           WHERE lr.id = ?''',
        (request_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row and new_status in ('approved', 'rejected'):
        try:
            notify_employee_status_change(
                employee_email=row['email'],
                full_name=row['full_name'] or row['email'],
                status=new_status,
                start_date=row['start_date'],
                end_date=row['end_date'],
                leave_days=row['leave_days'],
            )
        except Exception as e:
            app.logger.error('Email notification failed: %s', e)
            flash(f'Status updated but email notification failed: {e}', 'warning')

    flash(f'Request #{request_id} status updated to {new_status}.', 'success')
    return redirect(url_for('leave_requests'))


@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
