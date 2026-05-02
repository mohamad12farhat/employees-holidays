import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, DB_PATH
from employee import employee_bp
from mail_utils import (notify_employee_status_change, notify_employee_deactivated,
                        notify_employee_reactivated, notify_employee_admin_logged_leave,
                        notify_employee_low_balance)

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
        '''SELECT lr.user_id, lr.start_date, lr.end_date, lr.leave_days,
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

    if row and new_status == 'approved':
        from employee import get_remaining_days
        year = int(row['start_date'][:4])
        remaining = get_remaining_days(row['user_id'], year)
        if 0 <= remaining <= 5:
            try:
                notify_employee_low_balance(
                    employee_email=row['email'],
                    full_name=row['full_name'] or row['email'],
                    remaining_days=remaining,
                )
            except Exception as e:
                app.logger.error('Low balance email failed: %s', e)

    flash(f'Request #{request_id} status updated to {new_status}.', 'success')
    return redirect(url_for('leave_requests'))


@app.route('/admin/employees')
def manage_employees():
    if not session.get('admin'):
        flash('You must be logged in as admin to access that page.')
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    current_year = str(date.today().year)
    cursor.execute('''
        SELECT u.id, u.username, u.full_name, u.is_active,
               COALESCE(lb.total_days, 15) AS total_days,
               COALESCE(lb.carry_over_days, 0) AS carry_over_days,
               COALESCE(SUM(
                   CASE WHEN lr.status IN ('pending', 'approved')
                        AND strftime('%Y', lr.start_date) = ?
                   THEN lr.leave_days ELSE 0 END
               ), 0) AS days_used
        FROM users u
        LEFT JOIN leave_balance lb ON lb.user_id = u.id AND lb.year = ?
        LEFT JOIN leave_requests lr ON lr.user_id = u.id
        WHERE u.role = 'employee'
        GROUP BY u.id
        ORDER BY u.full_name
    ''', (current_year, int(current_year)))
    employees = cursor.fetchall()
    conn.close()
    return render_template('admin_employees.html', employees=employees, current_year=int(current_year))


@app.route('/admin/employees/<int:emp_id>/toggle-status', methods=['POST'])
def toggle_employee_status(emp_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    reason = request.form.get('reason', '').strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT is_active, username, full_name FROM users WHERE id = ? AND role = "employee"',
        (emp_id,)
    )
    row = cursor.fetchone()
    if row:
        new_status = 0 if row[0] else 1
        cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, emp_id))
        conn.commit()
        emp_email = row[1]
        emp_name  = row[2] or row[1]
        label = 'reactivated' if new_status else 'deactivated'
        flash(f'Employee account {label} successfully.', 'success')
        try:
            if new_status == 0:
                notify_employee_deactivated(emp_email, emp_name, reason)
            else:
                notify_employee_reactivated(emp_email, emp_name)
        except Exception as e:
            app.logger.error('Email notification failed: %s', e)
            flash(f'Account {label} but email notification failed: {e}', 'warning')
    else:
        flash('Employee not found.', 'danger')
    conn.close()
    return redirect(url_for('manage_employees'))



@app.route('/admin/add-leave', methods=['GET', 'POST'])
def admin_add_leave():
    if not session.get('admin'):
        flash('You must be logged in as admin to access that page.')
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, full_name FROM users WHERE role = 'employee' AND is_active = 1 ORDER BY full_name"
    )
    employees = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        emp_id    = request.form.get('employee_id', '').strip()
        start_str = request.form.get('start_date', '').strip()
        end_str   = request.form.get('end_date', '').strip()
        note      = request.form.get('note', '').strip() or None

        if not emp_id or not start_str or not end_str:
            flash('Employee, start date, and end date are all required.', 'danger')
            return render_template('admin_add_leave.html', employees=employees)

        try:
            emp_id = int(emp_id)
            start  = date.fromisoformat(start_str)
            end    = date.fromisoformat(end_str)
        except (ValueError, TypeError):
            flash('Invalid input.', 'danger')
            return render_template('admin_add_leave.html', employees=employees)

        if end < start:
            flash('End date cannot be before the start date.', 'danger')
            return render_template('admin_add_leave.html', employees=employees)

        from employee import count_working_days, get_remaining_days
        leave_days = count_working_days(start_str, end_str)

        if leave_days == 0:
            flash('The selected range contains no working days (all weekends or public holidays).', 'danger')
            return render_template('admin_add_leave.html', employees=employees)

        year      = start.year
        remaining = get_remaining_days(emp_id, year)

        if leave_days > remaining:
            flash(
                f'Not enough leave days. The employee has {remaining} day(s) left '
                f'but this leave requires {leave_days}.',
                'danger'
            )
            return render_template('admin_add_leave.html', employees=employees)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verify employee exists
        cursor.execute('SELECT username, full_name FROM users WHERE id = ? AND role = "employee"', (emp_id,))
        emp_row = cursor.fetchone()
        if not emp_row:
            conn.close()
            flash('Employee not found.', 'danger')
            return render_template('admin_add_leave.html', employees=employees)

        cursor.execute(
            '''INSERT INTO leave_requests (user_id, start_date, end_date, reason, leave_days, status, logged_by_admin)
               VALUES (?, ?, ?, ?, ?, 'approved', 1)''',
            (emp_id, start_str, end_str, note, leave_days)
        )
        conn.commit()
        conn.close()

        try:
            notify_employee_admin_logged_leave(
                employee_email=emp_row['username'],
                full_name=emp_row['full_name'] or emp_row['username'],
                start_date=start_str,
                end_date=end_str,
                leave_days=leave_days,
                note=note or '',
            )
        except Exception as e:
            app.logger.error('Email notification failed: %s', e)
            flash(f'Leave logged but email notification failed: {e}', 'warning')

        new_remaining = remaining - leave_days
        if 0 <= new_remaining <= 5:
            try:
                notify_employee_low_balance(
                    employee_email=emp_row['username'],
                    full_name=emp_row['full_name'] or emp_row['username'],
                    remaining_days=new_remaining,
                )
            except Exception as e:
                app.logger.error('Low balance email failed: %s', e)

        flash(
            f'Leave logged successfully for {emp_row["full_name"] or emp_row["username"]} '
            f'({leave_days} day(s), {start_str} → {end_str}).',
            'success'
        )
        return redirect(url_for('admin_add_leave'))

    return render_template('admin_add_leave.html', employees=employees)


@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


def run_year_end_reset():
    """Runs automatically on Jan 1st: calculates carry-over and sets next-year balances."""
    current_year = date.today().year - 1  # it's Jan 1st, so we're resetting the previous year
    next_year = current_year + 1
    MAX_CARRY_OVER = 5
    MAX_TOTAL = 20
    ANNUAL_DAYS = 15

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE role = "employee" AND is_active = 1')
    employees = cursor.fetchall()

    for (emp_id,) in employees:
        cursor.execute(
            'SELECT total_days FROM leave_balance WHERE user_id = ? AND year = ?',
            (emp_id, current_year)
        )
        row = cursor.fetchone()
        total_days = row[0] if row else ANNUAL_DAYS

        cursor.execute(
            '''SELECT COALESCE(SUM(leave_days), 0) FROM leave_requests
               WHERE user_id = ? AND strftime('%Y', start_date) = ?
                 AND status IN ('pending', 'approved')''',
            (emp_id, str(current_year))
        )
        used = cursor.fetchone()[0]
        unused = max(0, total_days - used)
        carry_over = min(unused, MAX_CARRY_OVER)
        next_total = min(ANNUAL_DAYS + carry_over, MAX_TOTAL)

        cursor.execute(
            '''INSERT OR REPLACE INTO leave_balance (user_id, year, total_days, carry_over_days)
               VALUES (?, ?, ?, ?)''',
            (emp_id, next_year, next_total, carry_over)
        )

    conn.commit()
    conn.close()
    app.logger.info('Year-end reset complete: %d employee(s) updated for %d.', len(employees), next_year)


scheduler = BackgroundScheduler()
scheduler.add_job(run_year_end_reset, trigger='cron', month=1, day=1, hour=0, minute=1)
scheduler.start()


if __name__ == '__main__':
    app.run(debug=True)
