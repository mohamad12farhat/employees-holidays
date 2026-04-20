import sqlite3
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from holidays import get_lebanon_holidays
from database import DB_PATH

employee_bp = Blueprint('employee', __name__)

ANNUAL_LEAVE_DAYS = 15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def count_working_days(start_date_str, end_date_str):
    """Count Mon–Fri days between start and end (inclusive) excluding Lebanese public holidays."""
    start = date.fromisoformat(start_date_str)
    end   = date.fromisoformat(end_date_str)
    # Cache holidays per year in case the range spans two years
    holiday_cache = {}
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0=Mon … 4=Fri
            yr = current.year
            if yr not in holiday_cache:
                holiday_cache[yr] = get_lebanon_holidays(yr)
            if current.strftime('%Y-%m-%d') not in holiday_cache[yr]:
                count += 1
        current += timedelta(days=1)
    return count


def get_remaining_days(user_id, year):
    """Return how many leave days the employee still has for the given year."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT COALESCE(SUM(leave_days), 0)
           FROM leave_requests
           WHERE user_id = ?
             AND strftime('%Y', start_date) = ?
             AND status IN ('pending', 'approved')''',
        (user_id, str(year))
    )
    used = cursor.fetchone()[0]
    conn.close()
    return ANNUAL_LEAVE_DAYS - used


def check_date_overlap(user_id, start_str, end_str):
    """
    Returns (has_approved_conflict: bool, has_pending_conflict: bool).
    Checks whether any OTHER employee has a request whose date range
    overlaps [start_str, end_str].
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT status FROM leave_requests
           WHERE user_id != ?
             AND status IN ('approved', 'pending')
             AND start_date <= ?
             AND end_date   >= ?''',
        (user_id, end_str, start_str)
    )
    rows = cursor.fetchall()
    conn.close()
    statuses = {r[0] for r in rows}
    return ('approved' in statuses), ('pending' in statuses)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@employee_bp.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
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
            conn = sqlite3.connect(DB_PATH)
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


@employee_bp.route('/employee/request-leave', methods=['GET', 'POST'])
def request_leave():
    if not session.get('employee_id'):
        flash('You must be logged in to access that page.')
        return redirect(url_for('employee.employee_login'))

    user_id = session['employee_id']
    today   = date.today()

    if request.method == 'POST':
        start_str = request.form.get('start_date', '').strip()
        end_str   = request.form.get('end_date', '').strip()
        reason    = request.form.get('reason', '').strip() or None

        # --- Basic validation ---
        if not start_str or not end_str:
            flash('Please select both a start date and an end date.', 'danger')
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=get_remaining_days(user_id, today.year))

        start = date.fromisoformat(start_str)
        end   = date.fromisoformat(end_str)

        if start < today:
            flash('Start date cannot be in the past.', 'danger')
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=get_remaining_days(user_id, today.year))

        if end < start:
            flash('End date cannot be before the start date.', 'danger')
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=get_remaining_days(user_id, today.year))

        # --- Working days calculation ---
        leave_days = count_working_days(start_str, end_str)

        if leave_days == 0:
            flash('Your selected range contains no working days (all weekends or public holidays).', 'danger')
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=get_remaining_days(user_id, today.year))

        # --- Cross-employee overlap check ---
        approved_conflict, pending_conflict = check_date_overlap(user_id, start_str, end_str)

        if approved_conflict:
            flash(
                'These dates overlap with an already-approved leave request from another employee. '
                'Please choose different dates.',
                'danger'
            )
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=get_remaining_days(user_id, today.year))

        if pending_conflict and not request.form.get('confirmed'):
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=get_remaining_days(user_id, today.year),
                                   pending_conflict=True,
                                   form_data={
                                       'start_date': start_str,
                                       'end_date':   end_str,
                                       'reason':     reason or '',
                                   })

        # --- Quota check (based on the year of start_date) ---
        year      = start.year
        remaining = get_remaining_days(user_id, year)

        if leave_days > remaining:
            flash(
                f'Not enough leave days. You have {remaining} day(s) left '
                f'but this request requires {leave_days}.',
                'danger'
            )
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=remaining)

        # --- Overlap check ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id FROM leave_requests
               WHERE user_id = ?
                 AND status IN ('pending', 'approved')
                 AND start_date <= ?
                 AND end_date >= ?''',
            (user_id, end_str, start_str)
        )
        if cursor.fetchone():
            conn.close()
            flash('You already have a leave request that overlaps with these dates.', 'danger')
            return render_template('request_leave.html',
                                   username=session.get('employee_username'),
                                   remaining=get_remaining_days(user_id, year))

        # --- Save to DB ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO leave_requests (user_id, start_date, end_date, reason, leave_days, status)
               VALUES (?, ?, ?, ?, ?, 'pending')''',
            (user_id, start_str, end_str, reason, leave_days)
        )
        conn.commit()
        conn.close()

        flash(
            f'Leave request submitted! {leave_days} day(s) of leave requested. '
            f'You have {remaining - leave_days} day(s) remaining for {year}.',
            'success'
        )
        return redirect(url_for('employee.request_leave'))

    # GET — pass remaining days to template
    remaining = get_remaining_days(user_id, today.year)
    return render_template('request_leave.html',
                           username=session.get('employee_username'),
                           remaining=remaining)


@employee_bp.route('/employee/view-requests')
def view_requests():
    if not session.get('employee_id'):
        flash('You must be logged in to access that page.')
        return redirect(url_for('employee.employee_login'))
    user_id = session['employee_id']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, start_date, end_date, leave_days, reason, status
           FROM leave_requests
           WHERE user_id = ?
           ORDER BY id DESC''',
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    requests_list = [
        {'id': r[0], 'start_date': r[1], 'end_date': r[2],
         'leave_days': r[3], 'reason': r[4] or '—', 'status': r[5]}
        for r in rows
    ]
    return render_template('view_requests.html',
                           username=session.get('employee_username'),
                           requests=requests_list)


@employee_bp.route('/employee/logout')
def employee_logout():
    session.pop('employee_id', None)
    session.pop('employee_email', None)
    session.pop('employee_username', None)
    return redirect(url_for('employee.employee_login'))
