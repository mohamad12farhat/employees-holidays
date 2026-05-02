# Employee Leave Management System

A web-based leave management system built with Flask, allowing employees to request leave and admins to manage and track requests.

## Features

**Employee**
- Register and log in with email and password
- Request leave with automatic working-day calculation (weekends and Lebanese public holidays excluded)
- View personal leave history and remaining balance (15 days/year, carry-over included)
- Receive an email notification when their leave request is approved or rejected
- View a monthly **team leave calendar** showing all approved leaves across the team, with prev/next month navigation, today highlighted, and color-coded indicators for own vs colleague leaves
- **Edit pending requests** — modify the dates and/or reason of a pending leave request before it is reviewed; full validation (quota, overlap, conflict checks) is re-applied on save

**Admin**
- Dashboard with live stats — total employees, pending, approved, and rejected requests
- View and manage all leave requests (approve / reject)
- See employee full name and email on each request
- Receive an email notification when an employee submits a new leave request
- Manage employees — view the full employee list with leave usage, total allocation, and carry-over days per year
- **Automatic year-end reset** — on January 1st at midnight, unused days (up to 5) carry over to the new year automatically; new-year total is capped at 20 days
- New employees joining mid-year receive a pro-rated allocation based on their join month
- Deactivate an employee account (with an optional reason) — employee receives an email notification
- Reactivate an employee account — employee receives an email notification
- Deactivated employees are blocked from logging in
- **Add leave manually** — log a leave on behalf of any employee (e.g. a sick day reported by phone); the leave is saved as approved instantly, the employee's balance is deducted, and they receive an email notification with the dates and an optional admin note

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, vanilla CSS

## How to Run

```bash
# Install dependencies
pip install flask flask-mail python-dotenv apscheduler

# Create a .env file with your email credentials
# (copy the example below and fill in your values)

# Run the app
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

**Default admin credentials:**
- Username: `admin`
- Password: `123`

## Email Setup

Create a `.env` file in the project root with the following:

```
MAIL_SENDER=your-gmail@gmail.com
MAIL_PASSWORD=your-16-char-app-password
ADMIN_EMAIL=admin-inbox@gmail.com
```

- `MAIL_SENDER` — the Gmail account used to send notifications
- `MAIL_PASSWORD` — a Gmail App Password (Google Account → Security → 2-Step Verification → App Passwords)
- `ADMIN_EMAIL` — the inbox where new leave request alerts are delivered

> The `.env` file is git-ignored and should never be committed.
