import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, DB_PATH
from employee import employee_bp

app = Flask(__name__)
app.secret_key = 'secret_key'

app.register_blueprint(employee_bp)

init_db()


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
    return render_template('dashboard.html')


@app.route('/admin/leave-requests')
def leave_requests():
    if not session.get('admin'):
        flash('You must be logged in as admin to access that page.')
        return redirect(url_for('login'))
    return render_template('view-leave-requests.html')


@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
